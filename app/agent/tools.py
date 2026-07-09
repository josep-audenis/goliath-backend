"""
Research tools — the data-gathering layer subagents draw on.

Each function tries a live Cala REST call and falls back to credible mock data
when Cala is unavailable (no key / mock mode / error). Output shape is identical
either way, so the orchestrator and frontend never branch on real-vs-mock.

`@function_tool` wrappers expose the same functions to an Agent when the SDK is
present; the plain `*_impl` functions are what the deterministic orchestrator
calls directly.
"""

from __future__ import annotations

import logging
from typing import Any

from app.agent import mock_data
from app.clients.cala import CalaUnavailable, extract_claims, extract_entities, extract_evidence, rest
from app.core.config import settings

log = logging.getLogger("app.agent.tools")

try:
    from agents import function_tool  # type: ignore
except Exception:  # pragma: no cover

    def function_tool(*args, **kwargs):  # type: ignore
        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]

        def _wrap(fn):
            return fn

        return _wrap


# ---------------------------------------------------------------------------
# Market Mapper — segments + demand signals
# ---------------------------------------------------------------------------


def market_scan_impl(query: str, geo: str | None = None, sector: str | None = None) -> dict[str, Any]:
    if settings.cala_live:
        try:
            data = rest.knowledge_search(f"market segments and demand for {sector or 'startups'} in {geo or ''}: {query}")
            claims = extract_claims(data, max_items=4)
            return {
                "summary": claims[0] if claims else f"Market map for '{query}'.",
                "findings": claims,
                "evidence": extract_evidence(data),
                "mocked": False,
            }
        except CalaUnavailable as e:
            log.warning("market_scan live failed, mocking: %s", e)
    return {
        "summary": f"Market map for '{query}' — demand rising across target segments.",
        "findings": [f"Demand rising across {sector or 'target'} segments."],
        "evidence": mock_data.mock_evidence(sector or "target market"),
        "mocked": True,
    }


# ---------------------------------------------------------------------------
# Company Scout — candidate startups + traction
# ---------------------------------------------------------------------------


def company_scan_impl(query: str, geo: str | None = None, sector: str | None = None, n: int = 5) -> dict[str, Any]:
    if settings.cala_live:
        try:
            data = rest.knowledge_search(f"{sector or 'startups'} in {geo or ''} that raised funding: {query}")
            ents = extract_entities(data)  # already filtered to Company/Organization
            evidence = extract_evidence(data)
            companies = [
                {
                    "name": e.get("name") or "unknown",
                    "sector": sector,
                    "geo": geo,
                    "stage": None,  # Cala entities carry no stage field; enrich via funding_scan
                    "goliathScore": 60.0,
                    "status": "warming",
                    "confidence": 55.0,
                    "riskLevel": "medium",
                    "cala_entity_id": e.get("id"),
                }
                for e in ents[:n]
            ]
            # Surface a live-but-empty result explicitly instead of silently mocking:
            # empty companies with real claims still means the call worked.
            return {
                "companies": companies,
                "findings": extract_claims(data, max_items=6),
                "evidence": evidence,
                "mocked": False,
            }
        except CalaUnavailable as e:
            log.warning("company_scan live failed, mocking: %s", e)
    return {
        "companies": mock_data.mock_companies(query, geo, sector, n),
        "findings": [],
        "evidence": mock_data.mock_evidence(sector or "candidate companies"),
        "mocked": True,
    }


# ---------------------------------------------------------------------------
# Funding Analyst — round timing / next-raise window
# ---------------------------------------------------------------------------


def funding_scan_impl(company: str) -> dict[str, Any]:
    if settings.cala_live:
        try:
            data = rest.knowledge_search(f"{company} funding rounds latest raise investors")
            return {"company": company, "evidence": extract_evidence(data), "mocked": False}
        except CalaUnavailable as e:
            log.warning("funding_scan live failed, mocking: %s", e)
    return {
        "company": company,
        "note": "Likely re-raise window in the next 6–9 months based on last round timing.",
        "evidence": mock_data.mock_evidence(f"{company} funding"),
        "mocked": True,
    }


# ---- function_tool wrappers (Agent-facing) ----


@function_tool
def market_scan(query: str, geo: str | None = None, sector: str | None = None) -> dict[str, Any]:
    """Map market segments and demand signals for the query's geo/sector."""
    return market_scan_impl(query, geo, sector)


@function_tool
def company_scan(query: str, geo: str | None = None, sector: str | None = None) -> dict[str, Any]:
    """Find candidate startups with funding history and traction for the query."""
    return company_scan_impl(query, geo, sector)


@function_tool
def funding_scan(company: str) -> dict[str, Any]:
    """Look up a company's funding rounds and estimate its next-raise window."""
    return funding_scan_impl(company)


RESEARCH_TOOLS = [market_scan, company_scan, funding_scan]
