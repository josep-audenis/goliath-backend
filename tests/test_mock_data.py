"""Mock research output — deterministic, query-derived, contract-valid."""

from __future__ import annotations

from app.agent import mock_data
from app.schemas.contract import EvidenceSource

SIGNAL_KEYS = {"traction", "funding_timing", "market_heat", "risk"}


def test_mock_companies_are_deterministic():
    a = mock_data.mock_companies("AI in Barcelona", None, None)
    b = mock_data.mock_companies("AI in Barcelona", None, None)
    assert a == b


def test_mock_companies_vary_by_query():
    a = mock_data.mock_companies("AI in Barcelona", None, None)
    b = mock_data.mock_companies("fintech in Berlin", None, None)
    assert [c["name"] for c in a] != [c["name"] for c in b]


def test_mock_companies_count():
    comps = mock_data.mock_companies("AI in Barcelona", None, None, n=5)
    assert len(comps) == 5


def test_mock_company_carries_signals_in_0_1():
    for c in mock_data.mock_companies("AI in Barcelona", None, None):
        assert set(c["signals"]) == SIGNAL_KEYS
        assert all(0 <= v <= 1 for v in c["signals"].values())
        assert c["coverage"] == 1.0


def test_market_heat_is_shared_per_sector():
    comps = mock_data.mock_companies("AI in Barcelona", None, sector="fintech", n=4)
    heats = {c["signals"]["market_heat"] for c in comps}
    assert len(heats) == 1  # same sector -> same market heat


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
