"""Unit tests for the pure Goliath Score engine (app/agent/scoring.py)."""

from __future__ import annotations

from app.agent import scoring
from app.schemas.contract import OpportunityStatus, RiskLevel

FACTOR_KEYS = {"traction", "funding_timing", "market_heat", "risk"}


def test_all_max_signals_caps_at_score_max():
    r = scoring.score({"traction": 1, "funding_timing": 1, "market_heat": 1, "risk": 0})
    # 100 * 1.15 boost, capped at SCORE_MAX (98.3)
    assert r.goliathScore == scoring.SCORE_MAX
    assert r.status == OpportunityStatus.HOT
    assert r.riskLevel == RiskLevel.LOW


def test_all_zero_signals_scores_0():
    r = scoring.score({"traction": 0, "funding_timing": 0, "market_heat": 0, "risk": 0})
    assert r.goliathScore == 0
    assert r.status == OpportunityStatus.NOT_HOT


def test_breakdown_reconciles_with_score():
    sig = {"traction": 0.8, "funding_timing": 0.6, "market_heat": 0.4, "risk": 0.3}
    r = scoring.score(sig)
    total = round(sum(f["contribution"] for f in r.breakdown), 1)
    # score is the (boosted) sum of contributions, clamped to [0, SCORE_MAX]
    assert r.goliathScore == round(min(max(total, 0.0), scoring.SCORE_MAX), 1)
    assert {f["key"] for f in r.breakdown} == FACTOR_KEYS


def test_risk_is_a_penalty():
    base = scoring.score({"traction": 0.8, "funding_timing": 0.8, "market_heat": 0.8, "risk": 0.0})
    risky = scoring.score({"traction": 0.8, "funding_timing": 0.8, "market_heat": 0.8, "risk": 0.9})
    assert risky.goliathScore < base.goliathScore
    risk_factor = next(f for f in risky.breakdown if f["key"] == "risk")
    assert risk_factor["contribution"] < 0


def test_traction_moves_the_score_most():
    """Traction has the highest weight, so a bump there should beat the others."""
    low = {"traction": 0.2, "funding_timing": 0.2, "market_heat": 0.2, "risk": 0.0}
    bump_traction = scoring.score({**low, "traction": 0.9})
    bump_market = scoring.score({**low, "market_heat": 0.9})
    assert bump_traction.goliathScore > bump_market.goliathScore


def test_status_bands():
    assert scoring.status_for(85) == OpportunityStatus.HOT
    assert scoring.status_for(70) == OpportunityStatus.WARMING
    assert scoring.status_for(55) == OpportunityStatus.NEUTRAL
    assert scoring.status_for(40) == OpportunityStatus.COOLING
    assert scoring.status_for(10) == OpportunityStatus.NOT_HOT


def test_risk_level_bands():
    assert scoring.risk_level_for(0.1) == RiskLevel.LOW
    assert scoring.risk_level_for(0.5) == RiskLevel.MEDIUM
    assert scoring.risk_level_for(0.9) == RiskLevel.HIGH


def test_confidence_in_band():
    for _ in range(50):
        c = scoring.confidence_for(evidence_count=2, coverage=1.0)
        assert 0.81 <= c <= 0.98


def test_missing_signals_default_to_neutral():
    r = scoring.score({})  # nothing provided
    assert all(f["value"] == 0.5 for f in r.breakdown)
    assert 0 <= r.goliathScore <= 100


def test_deterministic():
    sig = {"traction": 0.7, "funding_timing": 0.5, "market_heat": 0.6, "risk": 0.2}
    assert scoring.score(sig).goliathScore == scoring.score(sig).goliathScore
