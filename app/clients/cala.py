"""
Cala data layer — one place for every Cala call.

Two transports, one purpose (structured entity/knowledge facts):
  - REST  (`CalaRestClient`)  : deterministic entity + knowledge_search lookups
    used by the research subagents' tool functions.
  - MCP   (`cala_mcp_server`) : open-ended `knowledge_search` exposed to an
    Agent for free-form narrative research.

Secrets stay backend-side (hard constraint, see external-services.md). When no
key is configured or `use_cala_mock` is on, callers should fall back to mocks —
this module raises `CalaUnavailable` rather than inventing data.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.core.config import settings

log = logging.getLogger("app.cala")


class CalaUnavailable(RuntimeError):
    """Raised when a live Cala call is requested but not possible/failed."""


# ---------------------------------------------------------------------------
# REST client
# ---------------------------------------------------------------------------


class CalaRestClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.base_url = (base_url or settings.cala_base_url).rstrip("/")
        self.api_key = api_key or settings.cala_api_key

    def _headers(self) -> dict[str, str]:
        return {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

    def _post(self, path: str, body: dict[str, Any], timeout: float = 120.0, retries: int = 3) -> dict[str, Any]:
        if not self.api_key:
            raise CalaUnavailable("no CALA_API_KEY configured")
        last: Optional[Exception] = None
        for attempt in range(retries):
            try:
                with httpx.Client(timeout=timeout) as c:
                    r = c.post(f"{self.base_url}{path}", headers=self._headers(), json=body)
                    r.raise_for_status()
                    return r.json()
            except httpx.HTTPError as e:
                # Cala is slow (100s+) and the connection resets intermittently
                # (WinError 10054 -> ReadError). httpx.HTTPError covers timeouts,
                # connect/read errors, and status errors — retry them all.
                last = e
                log.warning("Cala POST %s failed (%d/%d): %s: %s", path, attempt + 1, retries, type(e).__name__, e)
        raise CalaUnavailable(f"{type(last).__name__}: {last}" if last else "Cala POST failed")

    # ---- high-level lookups ----

    def knowledge_search(self, query: str, explainability: bool = True, return_entities: bool = True) -> dict[str, Any]:
        """Free-text structured search. Returns content + context + explainability + entities."""
        return self._post(
            "/knowledge/search",
            {"input": query, "explainability": explainability, "return_entities": return_entities},
        )

    def retrieve_entity(self, uuid: str, properties: list[str], relationships: dict[str, Any]) -> dict[str, Any]:
        return self._post(f"/entities/{uuid}", {"properties": properties, "relationships": relationships})


# ---------------------------------------------------------------------------
# Parsing helpers (shared by tool functions)
# ---------------------------------------------------------------------------


def extract_evidence(data: dict[str, Any], max_items: int = 8) -> list[dict[str, str]]:
    """
    Citable {title,url,source} rows from context[].origins[].

    Real shape: origin = {source:{name,url}, document:{name,url}, breadcrumb:[]}.
    Title comes from document.name (NOT .title), source from source.name.
    """
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for ctx in data.get("context") or []:
        for origin in ctx.get("origins") or []:
            doc = origin.get("document") or {}
            src = origin.get("source") or {}
            url = doc.get("url") or src.get("url")
            if not (isinstance(url, str) and url.startswith("http")) or url in seen:
                continue
            seen.add(url)
            out.append(
                {
                    "title": doc.get("name") or src.get("name") or url,
                    "url": url,
                    "source": src.get("name") or "cala",
                }
            )
            if len(out) >= max_items:
                return out
    return out


# Cala entity_types that could represent investable companies.
_COMPANY_TYPES = {"Company", "Organization"}

# Name patterns that mark an Organization as NOT an investable startup:
# investors, funds, universities, government, consortia, standards bodies, banks.
import re as _re

_NON_STARTUP_RE = _re.compile(
    r"\b("
    r"ventures?|capital|partners?|fund|funds|holdings?|group|"
    r"investors?|equity|asset management|angels?|"
    r"university|universitat|universidad|college|institute|institut|"
    r"foundation|fundaci|association|associaci|consortium|alliance|"
    r"international|national|federation|society|council|committee|"
    r"government|ministry|agency|authority|commission|"
    r"bank|banco|sabadell|"
    r"supercomputing|research cent|centre|center|centro|"
    r"incubator|accelerator|chamber"
    r")\b",
    _re.IGNORECASE,
)


# Well-known investors/funds whose names carry no generic keyword marker, so the
# regex above misses them. Matched case-insensitively on a normalized name.
_KNOWN_INVESTORS = {
    "atomico", "sequoia", "a16z", "andreessen horowitz", "accel", "index", "index ventures",
    "gic", "gic private limited", "temasek", "softbank", "tiger global", "coatue",
    "insight", "insight partners", "general catalyst", "greylock", "benchmark", "kleiner perkins",
    "lightspeed", "bessemer", "battery", "ivp", "founders fund", "khosla", "y combinator",
    "techstars", "500 startups", "eurazeo", "balderton", "northzone", "creandum", "point nine",
    "seedcamp", "kfund", "k fund", "nauta", "seaya", "kibo ventures", "jme", "adara",
    "elaia", "crane", "crane venture partners", "banco sabadell", "sabadell",
}


def _norm(name: str) -> str:
    return _re.sub(r"[^a-z0-9 ]", "", (name or "").lower()).strip()


def is_probable_startup(entity: dict[str, Any]) -> bool:
    """True if the entity looks like an investable startup (not an investor/institution)."""
    if not isinstance(entity, dict):
        return False
    if entity.get("entity_type") not in _COMPANY_TYPES:
        return False
    name = entity.get("name") or ""
    if _norm(name) in _KNOWN_INVESTORS:
        return False
    return not _NON_STARTUP_RE.search(name)


def extract_entities(
    data: dict[str, Any], company_only: bool = True, startups_only: bool = False
) -> list[dict[str, Any]]:
    """
    Typed entities: {id, name, entity_type, mentions}. No `properties` field.

    - company_only (default): keep Company/Organization types.
    - startups_only: additionally drop investors, funds, universities, gov,
      consortia, and standards bodies (name heuristic) and rank `Company` before
      `Organization` so real startups surface first.
    """
    ents = data.get("entities")
    if not isinstance(ents, list):
        return []
    if not company_only and not startups_only:
        return ents
    if startups_only:
        keep = [e for e in ents if is_probable_startup(e)]
        # Company type is a stronger startup signal than a bare Organization.
        return sorted(keep, key=lambda e: 0 if e.get("entity_type") == "Company" else 1)
    return [e for e in ents if isinstance(e, dict) and e.get("entity_type") in _COMPANY_TYPES]


def extract_claims(data: dict[str, Any], max_items: int = 8) -> list[str]:
    """One-sentence grounded claims from explainability[].content — ideal findings."""
    out: list[str] = []
    for exp in data.get("explainability") or []:
        c = exp.get("content") if isinstance(exp, dict) else None
        if isinstance(c, str) and c.strip():
            out.append(c.strip())
        if len(out) >= max_items:
            break
    return out


# ---------------------------------------------------------------------------
# MCP server factory (open-ended knowledge_search inside an Agent)
# ---------------------------------------------------------------------------


def cala_mcp_server() -> Any:
    """
    Build a per-request Cala MCP server object, or None if unavailable.

    NOTE: caching the connection across requests breaks the SDK's anyio task
    scopes — always create fresh and enter with `async with` per request.
    """
    if not settings.cala_mcp_api_key:
        return None
    try:
        from agents.mcp import MCPServerStreamableHttp, create_static_tool_filter  # type: ignore
    except Exception as e:  # pragma: no cover
        log.warning("openai-agents MCP unavailable: %s", e)
        return None

    return MCPServerStreamableHttp(
        params={
            "url": settings.cala_mcp_url,
            "headers": {"X-API-KEY": settings.cala_mcp_api_key},
            "timeout": 120.0,
            "sse_read_timeout": 300.0,
        },
        name="cala",
        cache_tools_list=True,
        client_session_timeout_seconds=120,
        tool_filter=create_static_tool_filter(allowed_tool_names=["knowledge_search"]),
    )


rest = CalaRestClient()
