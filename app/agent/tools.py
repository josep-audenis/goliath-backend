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
from app.clients.cala import (
    CalaUnavailable,
    extract_claims,
    extract_entities,
    extract_evidence,
    is_probable_startup,
    rest,
)
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
# Multi-query helper — run several Cala searches concurrently, merge the
# claims/evidence/entities. This is what makes each research pass "extensive"
# instead of a single lookup.
# ---------------------------------------------------------------------------


def _multi_search(queries: list[str], claims_each: int = 4, ev_cap: int = 10) -> dict[str, Any]:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    raw: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(len(queries), 5)) as pool:
        futs = {pool.submit(rest.knowledge_search, q): q for q in queries}
        for fut in as_completed(futs):
            try:
                raw.append({"query": futs[fut], "data": fut.result()})
            except Exception as e:
                log.warning("multi_search query failed (%s): %s", futs[fut], e)

    findings: list[str] = []
    evidence: list[dict[str, str]] = []
    entities: list[dict[str, Any]] = []
    seen_ev: set[str] = set()
    for item in raw:
        d = item["data"]
        findings.extend(extract_claims(d, max_items=claims_each))
        for e in extract_evidence(d, max_items=ev_cap):
            if e["url"] not in seen_ev:
                seen_ev.add(e["url"])
                evidence.append(e)
        entities.extend(extract_entities(d))
    # de-dupe findings preserving order
    seen_f: set[str] = set()
    findings = [f for f in findings if not (f in seen_f or seen_f.add(f))]
    return {"queries": queries, "findings": findings, "evidence": evidence[:ev_cap], "entities": entities, "raw": raw}


# ---------------------------------------------------------------------------
# Market Mapper — segments + demand signals (multi-angle)
# ---------------------------------------------------------------------------


def market_scan_impl(query: str, geo: str | None = None, sector: str | None = None) -> dict[str, Any]:
    sec = sector or "startups"
    loc = geo or "Europe"
    if settings.cala_live:
        try:
            res = _multi_search(
                [
                    f"market segments and demand for {sec} in {loc}: {query}",
                    f"{sec} market growth rate and total addressable market in {loc}",
                    f"competitive density and leading {sec} companies in {loc}",
                ]
            )
            return {
                "summary": res["findings"][0] if res["findings"] else f"Market map for '{query}'.",
                "findings": res["findings"],
                "evidence": res["evidence"],
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


def company_scan_impl(query: str, geo: str | None = None, sector: str | None = None, n: int = 8) -> dict[str, Any]:
    sec = sector or "startups"
    loc = geo or "Europe"
    if settings.cala_live:
        try:
            res = _multi_search(
                [
                    f"{sec} in {loc} that raised funding: {query}",
                    f"fastest growing {sec} startups in {loc} with strong traction",
                    f"notable recently funded {sec} companies in {loc} and their investors",
                ],
                claims_each=5,
            )
            # de-dupe by name, keep only probable startups (drop investors,
            # universities, gov, consortia — see is_probable_startup).
            by_name: dict[str, dict[str, Any]] = {}
            for e in res["entities"]:
                nm = e.get("name")
                if nm and nm not in by_name and is_probable_startup(e):
                    by_name[nm] = e
            companies = [
                {
                    "name": e.get("name") or "unknown",
                    "sector": sector,
                    "geo": geo,
                    "stage": None,  # Cala entities carry no stage; enrich via funding_scan
                    "goliathScore": 60.0,
                    "status": "warming",
                    "confidence": 55.0,
                    "riskLevel": "medium",
                    "cala_entity_id": e.get("id"),
                }
                for e in list(by_name.values())[:n]
            ]
            return {
                "companies": companies,
                "findings": res["findings"],
                "evidence": res["evidence"],
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
# Risk Analyst — risks, weak signals, competitive threats
# ---------------------------------------------------------------------------


def risk_scan_impl(query: str, geo: str | None = None, sector: str | None = None) -> dict[str, Any]:
    sec = sector or "startups"
    loc = geo or "Europe"
    if settings.cala_live:
        try:
            res = _multi_search(
                [
                    f"risks and failures for {sec} startups in {loc}: {query}",
                    f"regulatory, funding-market and competitive threats to {sec} in {loc}",
                ]
            )
            return {"findings": res["findings"], "evidence": res["evidence"], "mocked": False}
        except CalaUnavailable as e:
            log.warning("risk_scan live failed, mocking: %s", e)
    return {
        "findings": ["Key risks: execution, competitive density, funding-market timing."],
        "evidence": [],
        "mocked": True,
    }


# ---------------------------------------------------------------------------
# Funding Analyst — round timing / next-raise window
# ---------------------------------------------------------------------------


def funding_landscape_impl(query: str, geo: str | None = None, sector: str | None = None) -> dict[str, Any]:
    """Broad funding-climate scan (not company-specific)."""
    sec = sector or "startups"
    loc = geo or "Europe"
    if settings.cala_live:
        try:
            res = _multi_search(
                [
                    f"recent funding rounds and round sizes for {sec} in {loc}: {query}",
                    f"most active investors and next-raise timing for {sec} in {loc}",
                ]
            )
            return {"findings": res["findings"], "evidence": res["evidence"], "mocked": False}
        except CalaUnavailable as e:
            log.warning("funding_landscape live failed, mocking: %s", e)
    return {
        "findings": ["Several candidates likely re-raising within 6–9 months."],
        "evidence": [],
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


@function_tool
def funding_landscape(query: str, geo: str | None = None, sector: str | None = None) -> dict[str, Any]:
    """Scan the broad funding climate: recent rounds, active investors, next-raise timing."""
    return funding_landscape_impl(query, geo, sector)


@function_tool
def risk_scan(query: str, geo: str | None = None, sector: str | None = None) -> dict[str, Any]:
    """Surface risks, weak signals, regulatory and competitive threats for the query."""
    return risk_scan_impl(query, geo, sector)


RESEARCH_TOOLS = [market_scan, company_scan, funding_scan, funding_landscape, risk_scan]
