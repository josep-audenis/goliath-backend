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

    def _post(self, path: str, body: dict[str, Any], timeout: float = 60.0, retries: int = 2) -> dict[str, Any]:
        if not self.api_key:
            raise CalaUnavailable("no CALA_API_KEY configured")
        last: Optional[Exception] = None
        for attempt in range(retries):
            try:
                with httpx.Client(timeout=timeout) as c:
                    r = c.post(f"{self.base_url}{path}", headers=self._headers(), json=body)
                    r.raise_for_status()
                    return r.json()
            except (httpx.ReadTimeout, httpx.HTTPStatusError) as e:
                last = e
                log.warning("Cala POST %s failed (%d/%d): %s", path, attempt + 1, retries, e)
        raise CalaUnavailable(str(last) if last else "Cala POST failed")

    # ---- high-level lookups ----

    def knowledge_search(self, query: str, explainability: bool = True, return_entities: bool = True) -> dict[str, Any]:
        """Free-text structured search. Returns context + explainability + entities."""
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
    """Pull citable {title,url,source} rows from knowledge_search context origins."""
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for ctx in data.get("context") or []:
        for origin in ctx.get("origins") or []:
            doc = origin.get("document") or {}
            url = doc.get("url") if isinstance(doc, dict) else None
            if not (url and isinstance(url, str) and url.startswith("http")) or url in seen:
                continue
            seen.add(url)
            out.append(
                {
                    "title": (doc.get("title") if isinstance(doc, dict) else None) or url,
                    "url": url,
                    "source": (origin.get("source") or {}).get("name") or "cala",
                }
            )
            if len(out) >= max_items:
                return out
    return out


def extract_entities(data: dict[str, Any]) -> list[dict[str, Any]]:
    ents = data.get("entities")
    return ents if isinstance(ents, list) else []


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
