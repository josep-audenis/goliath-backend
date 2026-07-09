"""Mock research output — deterministic, query-derived, contract-valid."""

from __future__ import annotations

from app.agent import mock_data
from app.schemas.contract import EvidenceSource, OpportunityStatus, RiskLevel


def test_mock_companies_are_deterministic():
    a = mock_data.mock_companies("AI in Barcelona", None, None)
    b = mock_data.mock_companies("AI in Barcelona", None, None)
    assert a == b


def test_mock_companies_vary_by_query():
    a = mock_data.mock_companies("AI in Barcelona", None, None)
    b = mock_data.mock_companies("fintech in Berlin", None, None)
    assert [c["name"] for c in a] != [c["name"] for c in b]


def test_mock_companies_count_and_ranking():
    comps = mock_data.mock_companies("AI in Barcelona", None, None, n=5)
    assert len(comps) == 5
    scores = [c["goliathScore"] for c in comps]
    assert scores == sorted(scores, reverse=True)


def test_mock_company_fields_in_contract_range():
    for c in mock_data.mock_companies("AI in Barcelona", None, None):
        assert 55 <= c["goliathScore"] <= 95
        assert 0 <= c["confidence"] <= 100
        assert c["status"] in {s.value for s in OpportunityStatus}
        assert c["riskLevel"] in {r.value for r in RiskLevel}


def test_geo_sector_override():
    c = mock_data.mock_companies("q", geo="Lisbon", sector="climate tech", n=1)[0]
    assert c["geo"] == "Lisbon"
    assert c["sector"] == "climate tech"


def test_mock_evidence_shape():
    ev = mock_data.mock_evidence("AI infra")
    assert ev
    for e in ev:
        assert e["source"] in {s.value for s in EvidenceSource}
        assert e["title"] and e["url"].startswith("http")
