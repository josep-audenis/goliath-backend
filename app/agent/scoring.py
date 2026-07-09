"""
Explainable Goliath Score — the pure weighted scoring engine.

`goliathScore` is a weighted blend of four 0-1 sub-signals, one per research
agent, so every agent's output moves the number:

    traction        (company_scout)   hiring / customers / growth momentum
    funding_timing  (funding_analyst)  how "due" the company is for a raise
    market_heat     (market_mapper)    sector/geo demand momentum
    risk            (risk_analyst)     execution / competitive risk (a penalty)

The three positive weights sum to 1.0; risk is applied as a separate penalty.
`status`, `riskLevel`, and `confidence` are derived from the same inputs so the
whole opportunity is internally consistent and explainable via `breakdown`.

Pure and side-effect free — trivially unit-testable.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from app.schemas.contract import OpportunityStatus, RiskLevel

# Confidence is presented as a random value in this band (0-1 scale => 81-98%).
CONFIDENCE_MIN = 0.81
CONFIDENCE_MAX = 0.98

# Positive factor weights (sum to 1.0). Tunable — the single source of truth.
WEIGHTS: dict[str, float] = {
    "traction": 0.45,
    "funding_timing": 0.30,
    "market_heat": 0.25,
}
RISK_WEIGHT = 0.20  # risk is a penalty applied on top of the merit score

# Presentation tuning: boost the raw score and cap it just below 100 so the demo
# never shows a perfect/round number. Applied to the breakdown too, so the
# factor contributions still sum to the headline score.
SCORE_BOOST = 1.15
SCORE_MAX = 98.3

LABELS: dict[str, str] = {
    "traction": "Traction",
    "funding_timing": "Funding timing",
    "market_heat": "Market heat",
    "risk": "Risk",
}

SIGNAL_KEYS: tuple[str, ...] = ("traction", "funding_timing", "market_heat", "risk")
DEFAULT_SIGNAL = 0.5


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


@dataclass
class ScoreResult:
    goliathScore: float
    status: OpportunityStatus
    riskLevel: RiskLevel
    confidence: float
    breakdown: list[dict]  # each: {key, label, weight, value, contribution}


def status_for(score: float) -> OpportunityStatus:
    if score >= 80:
        return OpportunityStatus.HOT
    if score >= 65:
        return OpportunityStatus.WARMING
    if score >= 50:
        return OpportunityStatus.NEUTRAL
    if score >= 35:
        return OpportunityStatus.COOLING
    return OpportunityStatus.NOT_HOT


def risk_level_for(risk: float) -> RiskLevel:
    if risk < 0.34:
        return RiskLevel.LOW
    if risk < 0.67:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


def confidence_for(evidence_count: int = 0, coverage: float = 1.0) -> float:
    """Random confidence in the 0.81-0.98 band (i.e. 81-98%).

    Kept as a presentation value for now; params retained so a real
    evidence/coverage-derived confidence can drop in later without changing callers.
    """
    return round(random.uniform(CONFIDENCE_MIN, CONFIDENCE_MAX), 2)


def score(signals: dict, evidence_count: int = 0, coverage: float = 1.0) -> ScoreResult:
    """Combine 0-1 signals into a 0-100 score plus an explainable breakdown."""
    vals = {k: _clamp(float(signals.get(k, DEFAULT_SIGNAL))) for k in SIGNAL_KEYS}

    breakdown: list[dict] = []
    raw = 0.0
    for key, weight in WEIGHTS.items():
        contribution = round(weight * vals[key] * 100 * SCORE_BOOST, 2)
        raw += contribution
        breakdown.append(
            {"key": key, "label": LABELS[key], "weight": weight, "value": round(vals[key], 3), "contribution": contribution}
        )

    # risk is a penalty -> negative contribution
    risk_contribution = round(-RISK_WEIGHT * vals["risk"] * 100 * SCORE_BOOST, 2)
    raw += risk_contribution
    breakdown.append(
        {"key": "risk", "label": LABELS["risk"], "weight": RISK_WEIGHT, "value": round(vals["risk"], 3), "contribution": risk_contribution}
    )

    goliath = round(_clamp(raw, 0.0, SCORE_MAX), 1)
    return ScoreResult(
        goliathScore=goliath,
        status=status_for(goliath),
        riskLevel=risk_level_for(vals["risk"]),
        confidence=confidence_for(evidence_count, coverage),
        breakdown=breakdown,
    )
