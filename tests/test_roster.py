"""Roster — default plan + agent-plan construction."""

from __future__ import annotations

from app.agent import roster
from app.schemas.contract import AgentStatus


def test_default_plan_is_four_distinct_agents():
    plan = roster.default_plan()
    assert [a.role for a in plan] == roster.DEFAULT_ROLES
    assert len({a.id for a in plan}) == 4
    # distinct voices so the narrated presentation has multiple speakers
    assert len({a.voice for a in plan}) == 4
    assert all(a.status == AgentStatus.PENDING for a in plan)


def test_make_agent_plan_fills_role_defaults():
    a = roster.make_agent_plan("market_mapper", 0)
    purpose, voice = roster.ROSTER["market_mapper"]
    assert a.role == "market_mapper"
    assert a.purpose == purpose
    assert a.voice == voice
    assert a.id == "agent-0-market_mapper"


def test_make_agent_plan_overrides():
    a = roster.make_agent_plan("risk_analyst", 3, purpose="custom purpose", voice="Nova")
    assert a.purpose == "custom purpose"
    assert a.voice == "Nova"


def test_unknown_role_falls_back():
    a = roster.make_agent_plan("does_not_exist", 1)
    assert a.purpose == "Research the query."
    assert a.voice == "Aria"
