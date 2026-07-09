"""
Reference subagent roster.

The orchestrator's planner (LLM) may pick a subset dynamically. When there is no
LLM key, `default_plan` provides a deterministic 4-agent plan so the pipeline
still runs end-to-end.
"""

from __future__ import annotations

from app.schemas.contract import AgentPlan

# role -> (purpose, distinct voice label)
ROSTER: dict[str, tuple[str, str]] = {
    "market_mapper": ("Map market segments and demand signals in the target geo/sector.", "Aria"),
    "company_scout": ("Surface candidate startups with funding history and traction.", "Roger"),
    "current_opportunities": ("Assign heat status and concise predictions per opportunity.", "Sarah"),
    "funding_analyst": ("Estimate round timing and likely next-raise windows.", "Charlie"),
    "risk_analyst": ("Surface risks, weak signals, and calibrate confidence.", "George"),
}

DEFAULT_ROLES = ["market_mapper", "company_scout", "current_opportunities", "risk_analyst"]


def make_agent_plan(role: str, idx: int, purpose: str | None = None, voice: str | None = None) -> AgentPlan:
    default_purpose, default_voice = ROSTER.get(role, ("Research the query.", "Aria"))
    return AgentPlan(
        id=f"agent-{idx}-{role}",
        role=role,
        purpose=purpose or default_purpose,
        voice=voice or default_voice,
    )


def default_plan() -> list[AgentPlan]:
    return [make_agent_plan(role, i) for i, role in enumerate(DEFAULT_ROLES)]
