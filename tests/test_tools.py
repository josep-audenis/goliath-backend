"""Research tools — deterministic mock fallback path (Cala not live).

The `deterministic_mode` fixture clears the Cala key, so `settings.cala_live` is
False and every *_impl takes its mock branch.
"""

from __future__ import annotations

from app.agent import tools


def test_market_scan_returns_summary_and_evidence():
    out = tools.market_scan_impl("AI in Barcelona", geo="Barcelona", sector="AI")
    assert out["mocked"] is True
    assert out["summary"]
    assert out["evidence"]


def test_company_scan_returns_companies_and_evidence():
    out = tools.company_scan_impl("AI in Barcelona", geo="Barcelona", sector="AI", n=4)
    assert out["mocked"] is True
    assert len(out["companies"]) == 4
    assert out["evidence"]
    # companies carry the scored fields the synthesizer maps to Opportunity
    for c in out["companies"]:
        assert {"name", "goliathScore", "status", "confidence", "riskLevel"} <= set(c)


def test_funding_scan_returns_note():
    out = tools.funding_scan_impl("Nova Labs")
    assert out["mocked"] is True
    assert out["company"] == "Nova Labs"
    assert out["note"]


def test_function_tool_wrappers_exist():
    # SDK-facing wrappers should be registered for the agent path
    # (market, company, funding_scan, funding_landscape, risk_scan)
    assert len(tools.RESEARCH_TOOLS) == 5
