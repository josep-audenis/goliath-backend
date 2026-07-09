"""
Goliath multi-agent orchestrator.

Flow (drives the Run.status state machine the frontend animates off):

    planning_agents -> researching -> synthesizing -> complete   (error from any)

    Orchestrator (partner)
     ├─ market_mapper          → segments + demand
     ├─ company_scout          → candidate startups + traction
     ├─ current_opportunities  → heat status + predictions
     ├─ funding_analyst        → next-raise windows
     └─ risk_analyst           → risks + confidence calibration

Subagents may be real (LLM + Cala tools) or deterministic mocks — output shape is
identical either way. Every phase appends a RunEvent so a polling frontend can
reconstruct the timeline.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.agent import prompts, roster
from app.agent.runtime import SDK_AVAILABLE, llm_enabled, make_model, run_agent_json
from app.agent.tools import RESEARCH_TOOLS, company_scan_impl, market_scan_impl
from app.schemas.contract import (
    AgentPlan,
    AgentStatus,
    Evidence,
    EvidenceSource,
    Opportunity,
    OpportunityStatus,
    PresentationSegment,
    Report,
    RiskLevel,
    Run,
    RunEvent,
    RunEventType,
    RunStatus,
)
from app.services import tts
from app.store.run_store import store

log = logging.getLogger("app.agent.orchestrator")


# ---------------------------------------------------------------------------
# Event + status helpers
# ---------------------------------------------------------------------------


def _emit(run: Run, type_: RunEventType, agent_id: str | None = None, **payload: Any) -> None:
    run.events.append(RunEvent(type=type_, agentId=agent_id, payload=payload))
    store.put_run(run)


def _set_status(run: Run, status: RunStatus) -> None:
    run.status = status
    store.put_run(run)


def _set_agent(run: Run, agent: AgentPlan, status: AgentStatus) -> None:
    agent.status = status
    store.put_run(run)


# ---------------------------------------------------------------------------
# Phase 1 — plan
# ---------------------------------------------------------------------------


async def _plan(run: Run, geo: str | None, sector: str | None) -> list[AgentPlan]:
    _set_status(run, RunStatus.PLANNING_AGENTS)
    agents: list[AgentPlan] | None = None
    if llm_enabled():
        try:
            from agents import Agent  # type: ignore

            planner = Agent(name="Orchestrator", instructions=prompts.ORCHESTRATOR_PLAN_SYSTEM, model=make_model())
            out = await run_agent_json(planner, f"query={run.query}\ngeo={geo}\nsector={sector}")
            picked = out.get("agents") or []
            agents = [
                roster.make_agent_plan(a.get("role", "market_mapper"), i, a.get("purpose"), a.get("voice"))
                for i, a in enumerate(picked)
                if a.get("role") in roster.ROSTER
            ] or None
        except Exception:
            log.exception("planner failed — using default roster")
    if not agents:
        agents = roster.default_plan()

    run.agents = agents
    _emit(run, RunEventType.ORCHESTRATOR_PLAN, agentCount=len(agents), roles=[a.role for a in agents])
    return agents


# ---------------------------------------------------------------------------
# Phase 2 — research
# ---------------------------------------------------------------------------


async def _research(run: Run, geo: str | None, sector: str | None) -> dict[str, Any]:
    _set_status(run, RunStatus.RESEARCHING)

    async def _one(agent: AgentPlan) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        _set_agent(run, agent, AgentStatus.RESEARCHING)
        _emit(run, RunEventType.AGENT_SPAWNED, agent.id, role=agent.role)
        findings, comps, evid = await _run_subagent(agent, run.query, geo, sector)
        for f in findings:
            agent.findings.append(f)
            _emit(run, RunEventType.AGENT_FINDING, agent.id, text=f)
        _set_agent(run, agent, AgentStatus.DONE)
        return comps, evid

    # Subagents are independent — run them concurrently so their (slow, ~100s
    # each) Cala lookups overlap instead of serializing.
    results = await asyncio.gather(*(_one(a) for a in run.agents))

    companies: list[dict[str, Any]] = []
    evidence: list[dict[str, str]] = []
    for comps, evid in results:
        companies.extend(comps)
        evidence.extend(evid)

    # dedupe companies by name, keep highest score
    by_name: dict[str, dict[str, Any]] = {}
    for c in companies:
        name = c.get("name")
        if not name:
            continue
        if name not in by_name or c.get("goliathScore", 0) > by_name[name].get("goliathScore", 0):
            by_name[name] = c
    return {"companies": list(by_name.values()), "evidence": evidence}


async def _run_subagent(agent: AgentPlan, query: str, geo: str | None, sector: str | None):
    """Return (findings, companies, evidence). LLM path if enabled, else deterministic."""
    if llm_enabled():
        try:
            from agents import Agent  # type: ignore

            sub = Agent(
                name=agent.role,
                instructions=prompts.RESEARCH_AGENT_SYSTEM.format(role=agent.role, purpose=agent.purpose),
                model=make_model(),
                tools=RESEARCH_TOOLS,
            )
            out = await run_agent_json(sub, f"query={query}\ngeo={geo}\nsector={sector}")
            return (
                out.get("findings") or [],
                out.get("companies") or [],
                out.get("evidence") or [],
            )
        except Exception:
            log.exception("subagent %s failed — deterministic fallback", agent.role)

    # Deterministic fallback per role. Cala calls are sync + slow, so run them
    # off the event loop (to_thread) — under the concurrent gather in _research
    # this lets multiple agents' lookups overlap instead of blocking each other.
    if agent.role == "market_mapper":
        m = await asyncio.to_thread(market_scan_impl, query, geo, sector)
        return (m.get("findings") or [m["summary"]], [], m["evidence"])
    if agent.role in ("company_scout", "current_opportunities"):
        c = await asyncio.to_thread(company_scan_impl, query, geo, sector)
        names = ", ".join(x["name"] for x in c["companies"][:3])
        return ([f"Top candidates: {names}."], c["companies"], c["evidence"])
    if agent.role == "funding_analyst":
        return (["Several candidates likely re-raising within 6–9 months."], [], [])
    # risk_analyst
    return (["Key risks: execution, competitive density, funding-market timing."], [], [])


# ---------------------------------------------------------------------------
# Phase 3 — synthesis
# ---------------------------------------------------------------------------


def _to_opportunity(idx: int, c: dict[str, Any]) -> Opportunity:
    status = c.get("status", "warming")
    risk = c.get("riskLevel", "medium")
    return Opportunity(
        id=f"opp-{idx}",
        name=c.get("name", f"Opportunity {idx}"),
        goliathScore=float(c.get("goliathScore", 60)),
        status=OpportunityStatus(status) if status in OpportunityStatus._value2member_map_ else OpportunityStatus.WARMING,
        confidence=float(c.get("confidence", 55)),
        riskLevel=RiskLevel(risk) if risk in RiskLevel._value2member_map_ else RiskLevel.MEDIUM,
        scoreReason=c.get("scoreReason") or f"Strong traction signals in {c.get('sector', 'target sector')}.",
        prediction=c.get("prediction") or f"{c.get('name', 'This startup')} is positioned to raise within 9 months.",
        sector=c.get("sector"),
        geo=c.get("geo"),
        stage=c.get("stage"),
        evidence=[
            Evidence(
                source=EvidenceSource(e.get("source", "web")) if e.get("source") in EvidenceSource._value2member_map_ else EvidenceSource.WEB,
                title=e.get("title", "source"),
                url=e.get("url"),
            )
            for e in (c.get("evidence") or [])
        ],
    )


async def _synthesize(run: Run, gathered: dict[str, Any]) -> tuple[list[Opportunity], list[PresentationSegment]]:
    _set_status(run, RunStatus.SYNTHESIZING)

    companies = sorted(gathered["companies"], key=lambda c: c.get("goliathScore", 0), reverse=True)[:5]
    # attach shared evidence when a company carries none
    shared_ev = gathered["evidence"][:2]
    for c in companies:
        c.setdefault("evidence", shared_ev)
    opportunities = [_to_opportunity(i, c) for i, c in enumerate(companies)]

    # one segment per contributing agent
    segments: list[PresentationSegment] = []
    top = opportunities[0].name if opportunities else "the top candidate"
    for agent in run.agents:
        _set_agent(run, agent, AgentStatus.SPEAKING)
        script = _segment_script(agent, opportunities, top)
        seg = PresentationSegment(agentId=agent.id, script=script, subtitle=script[:120])
        segments.append(seg)
        _emit(run, RunEventType.REPORT_SEGMENT_READY, agent.id, subtitle=seg.subtitle)
        _set_agent(run, agent, AgentStatus.DONE)

    # optional LLM polish of segment scripts (best-effort)
    if llm_enabled():
        try:
            await _polish_segments(run, gathered, opportunities, segments)
        except Exception:
            log.exception("segment polish failed — keeping deterministic scripts")

    # best-effort TTS
    await tts.attach_audio(segments, run.agents)
    return opportunities, segments


def _segment_script(agent: AgentPlan, opps: list[Opportunity], top: str) -> str:
    role = agent.role
    if role == "market_mapper":
        return f"The market is heating up. Demand signals point to real momentum, and {top} sits right at the center."
    if role in ("company_scout", "current_opportunities"):
        hot = ", ".join(o.name for o in opps[:3]) or top
        return f"Our top candidates are {hot}. {top} shows the strongest traction of the set."
    if role == "funding_analyst":
        return f"{top} looks primed for its next raise, likely within the next six to nine months."
    return f"On risk: {top} carries manageable execution risk, with competitive density the main watch item."


async def _polish_segments(run: Run, gathered, opportunities, segments) -> None:
    from agents import Agent  # type: ignore

    agent_ids = [a.id for a in run.agents]
    synth = Agent(
        name="Synthesis",
        instructions=prompts.SYNTHESIS_SYSTEM.format(agent_ids=agent_ids),
        model=make_model(),
    )
    payload = {
        "query": run.query,
        "opportunities": [o.model_dump(mode="json") for o in opportunities],
        "findings": [f for a in run.agents for f in a.findings],
    }
    import json

    out = await run_agent_json(synth, json.dumps(payload))
    llm_segs = {s.get("agentId"): s for s in (out.get("segments") or []) if isinstance(s, dict)}
    for seg in segments:
        s = llm_segs.get(seg.agentId)
        if s and s.get("script"):
            seg.script = s["script"]
            seg.subtitle = s.get("subtitle") or seg.script[:120]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def run_pipeline(run_id: str, geo: str | None = None, sector: str | None = None) -> None:
    """Execute the full run. Mutates + persists the Run through the store."""
    run = store.get_run(run_id)
    if run is None:
        log.error("run_pipeline: unknown run %s", run_id)
        return
    log.info("run %s start | query=%r llm=%s cala_live=%s", run_id, run.query[:80], llm_enabled(), None)
    try:
        await _plan(run, geo, sector)
        gathered = await _research(run, geo, sector)
        opportunities, segments = await _synthesize(run, gathered)

        run.opportunities = opportunities
        run.segments = segments
        _set_status(run, RunStatus.COMPLETE)
        _emit(run, RunEventType.RUN_COMPLETE, opportunityCount=len(opportunities))

        store.put_report(
            Report(
                runId=run.runId,
                query=run.query,
                opportunities=opportunities,
                segments=segments,
            )
        )
        log.info("run %s complete | opportunities=%d segments=%d", run_id, len(opportunities), len(segments))
    except Exception as exc:
        log.exception("run %s failed", run_id)
        run.status = RunStatus.ERROR
        run.error = f"{type(exc).__name__}: {exc}"
        store.put_run(run)
