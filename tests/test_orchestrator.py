"""Orchestrator flow — plan -> research -> synthesize state machine + events.

Deterministic (no-LLM) path only. Asserts the invariants the frontend animates
off, but against the *current* contract (see app/schemas/contract.py).
"""

from __future__ import annotations

from app.schemas.contract import (
    AgentStatus,
    OpportunityStatus,
    RiskLevel,
    RunEventType,
    RunStatus,
)
from tests.conftest import make_completed_run


async def test_run_reaches_complete():
    run = await make_completed_run()
    assert run.status == RunStatus.COMPLETE
    assert run.error is None


async def test_default_crew_spawned_and_done():
    run = await make_completed_run()
    assert [a.role for a in run.agents] == [
        "market_mapper",
        "company_scout",
        "current_opportunities",
        "risk_analyst",
    ]
    assert all(a.status == AgentStatus.DONE for a in run.agents)


async def test_opportunity_count_in_demo_range():
    run = await make_completed_run()
    assert 3 <= len(run.opportunities) <= 5


async def test_opportunities_ranked_desc_and_valid():
    run = await make_completed_run()
    scores = [o.goliathScore for o in run.opportunities]
    assert scores == sorted(scores, reverse=True)
    for o in run.opportunities:
        # the five scored/narrative fields must never be null and stay in range
        assert 0 <= o.goliathScore <= 100
        assert 0 <= o.confidence <= 100  # current contract scale
        assert isinstance(o.status, OpportunityStatus)
        assert isinstance(o.riskLevel, RiskLevel)
        assert o.scoreReason and o.prediction


async def test_one_segment_per_agent():
    run = await make_completed_run()
    assert len(run.segments) == len(run.agents)
    assert {s.agentId for s in run.segments} == {a.id for a in run.agents}
    for s in run.segments:
        assert s.script and s.subtitle


async def test_event_causal_order():
    run = await make_completed_run()
    types = [e.type for e in run.events]
    assert types[0] == RunEventType.ORCHESTRATOR_PLAN
    assert types[-1] == RunEventType.RUN_COMPLETE

    spawned = [e for e in run.events if e.type == RunEventType.AGENT_SPAWNED]
    assert len(spawned) == len(run.agents)
    assert {e.agentId for e in spawned} == {a.id for a in run.agents}

    # every agent.spawned precedes run.complete
    complete_idx = types.index(RunEventType.RUN_COMPLETE)
    for i, e in enumerate(run.events):
        if e.type == RunEventType.AGENT_SPAWNED:
            assert i < complete_idx


async def test_plan_event_payload_describes_crew():
    run = await make_completed_run()
    plan_ev = next(e for e in run.events if e.type == RunEventType.ORCHESTRATOR_PLAN)
    assert plan_ev.payload.get("agentCount") == len(run.agents)
    assert plan_ev.payload.get("roles") == [a.role for a in run.agents]


async def test_report_persisted_and_matches_run():
    from app.store.run_store import store

    run = await make_completed_run()
    report = store.get_report(run.runId)
    assert report is not None
    assert report.query == run.query
    assert len(report.opportunities) == len(run.opportunities)
    assert len(report.segments) == len(run.segments)


async def test_geo_sector_flow_through_to_opportunities():
    run = await make_completed_run(query="fintech deals", geo="Berlin", sector="fintech")
    assert any(o.geo == "Berlin" for o in run.opportunities)
    assert any(o.sector == "fintech" for o in run.opportunities)


async def test_different_queries_differ():
    a = await make_completed_run("fintech startups in Berlin")
    b = await make_completed_run("climate tech in Lisbon")
    assert [o.name for o in a.opportunities] != [o.name for o in b.opportunities]
