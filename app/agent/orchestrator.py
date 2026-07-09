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

from app.agent import prompts, roster, scoring
from app.agent.runtime import SDK_AVAILABLE, llm_enabled, make_model, run_agent_json
from app.agent.tools import (
    RESEARCH_TOOLS,
    company_scan_impl,
    funding_landscape_impl,
    market_scan_impl,
    risk_scan_impl,
)
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
    ScoreFactor,
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

    # The partner/presenter always leads the roster (frames + concludes the
    # briefing). It is backend-owned, not planner-chosen.
    agents = [roster.partner_agent()] + [a for a in agents if a.role != roster.PARTNER_ROLE]

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
    # Partner does not research — it presents in synthesis.
    if agent.role == roster.PARTNER_ROLE:
        return ([], [], [])
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
        findings = ([f"Top candidates: {names}."] if names else []) + (c.get("findings") or [])
        return (findings, c["companies"], c["evidence"])
    if agent.role == "funding_analyst":
        f = await asyncio.to_thread(funding_landscape_impl, query, geo, sector)
        return (f.get("findings") or [], [], f.get("evidence") or [])
    # risk_analyst
    r = await asyncio.to_thread(risk_scan_impl, query, geo, sector)
    return (r.get("findings") or [], [], r.get("evidence") or [])


# ---------------------------------------------------------------------------
# Phase 3 — synthesis
# ---------------------------------------------------------------------------


def _dedupe_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Unique evidence rows by url (fallback title), order preserved."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for e in items:
        key = e.get("url") or e.get("title")
        if key and key not in seen:
            seen.add(key)
            out.append(e)
    return out


def _score_company(c: dict[str, Any]) -> None:
    """Compute goliathScore + breakdown + status/riskLevel/confidence in place.

    Turns the four per-agent sub-signals into an explainable score. If a company
    predates this (no `signals`), scoring falls back to neutral 0.5 defaults.
    """
    res = scoring.score(
        c.get("signals") or {},
        evidence_count=len(c.get("evidence") or []),
        coverage=float(c.get("coverage", 1.0)),
    )
    c["goliathScore"] = res.goliathScore
    c["status"] = res.status.value
    c["riskLevel"] = res.riskLevel.value
    c["confidence"] = res.confidence
    c["scoreBreakdown"] = res.breakdown


def _to_opportunity(idx: int, c: dict[str, Any]) -> Opportunity:
    status = c.get("status", "warming")
    risk = c.get("riskLevel", "medium")
    return Opportunity(
        id=f"opp-{idx}",
        name=c.get("name", f"Opportunity {idx}"),
        goliathScore=float(c.get("goliathScore", 60)),
        status=OpportunityStatus(status) if status in OpportunityStatus._value2member_map_ else OpportunityStatus.WARMING,
        confidence=float(c.get("confidence", 0.6)),  # 0-1 scale
        riskLevel=RiskLevel(risk) if risk in RiskLevel._value2member_map_ else RiskLevel.MEDIUM,
        scoreReason=c.get("scoreReason") or _score_reason(c),
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
        scoreBreakdown=[ScoreFactor(**f) for f in (c.get("scoreBreakdown") or [])],
    )


def _score_reason(c: dict[str, Any]) -> str:
    """Explain the score from its strongest positive factor."""
    breakdown = [f for f in (c.get("scoreBreakdown") or []) if f.get("key") != "risk"]
    if breakdown:
        top = max(breakdown, key=lambda f: f.get("contribution", 0))
        return f"{top['label']} is the strongest driver ({top['contribution']:+.0f} pts) for this opportunity."
    return f"Strong traction signals in {c.get('sector', 'target sector')}."


async def _synthesize(run: Run, gathered: dict[str, Any]) -> tuple[list[Opportunity], list[PresentationSegment]]:
    _set_status(run, RunStatus.SYNTHESIZING)

    # Score every candidate from its sub-signals, then rank and keep the top 5.
    companies = list(gathered["companies"])
    for c in companies:
        _score_company(c)
    companies = sorted(companies, key=lambda c: c.get("goliathScore", 0), reverse=True)[:5]

    # Distribute the whole evidence pool across the shown cards instead of pinning
    # the same 2 URLs to every one. Each gets its own rotating slice (up to 3),
    # deduped, so cards cite varied real sources. Any evidence a company already
    # carries is kept and takes precedence.
    pool = _dedupe_evidence(gathered.get("evidence") or [])
    per = 3
    for i, c in enumerate(companies):
        own = c.get("evidence") or []
        if pool:
            start = (i * per) % len(pool)
            share = [pool[(start + k) % len(pool)] for k in range(min(per, len(pool)))]
        else:
            share = []
        c["evidence"] = _dedupe_evidence(list(own) + share)[:per]
    opportunities = [_to_opportunity(i, c) for i, c in enumerate(companies)]

    # Ordered presentation: partner opens, each expert speaks at length from its
    # own findings, partner closes with the recommendation.
    partner = next((a for a in run.agents if a.role == roster.PARTNER_ROLE), None)
    experts = [a for a in run.agents if a.role != roster.PARTNER_ROLE]

    plan: list[tuple[AgentPlan, str]] = []
    if partner:
        plan.append((partner, _presenter_intro(run, opportunities, experts)))
    for agent in experts:
        plan.append((agent, _expert_script(agent, opportunities)))
    if partner:
        plan.append((partner, _presenter_outro(opportunities)))

    segments: list[PresentationSegment] = []
    for agent, script in plan:
        _set_agent(run, agent, AgentStatus.SPEAKING)
        seg = PresentationSegment(agentId=agent.id, script=script, subtitle=_subtitle(script))
        segments.append(seg)
        _emit(run, RunEventType.REPORT_SEGMENT_READY, agent.id, subtitle=seg.subtitle)
        _set_agent(run, agent, AgentStatus.DONE)

    # NOTE: LLM "polish" is intentionally disabled — it compressed segments back
    # into one-liners. The long-form scripts above are built from the real
    # findings and are what we want spoken. (_polish_segments kept for reference.)

    # best-effort TTS
    await tts.attach_audio(segments, run.agents)
    return opportunities, segments


# ---------------------------------------------------------------------------
# Narration. Scripts lead straight with substance (the UI already shows each
# agent's name + role, so no spoken self-introductions). Each script is capped
# to ~45s of speech (~110 words) so no orb monologues.
# ---------------------------------------------------------------------------

# Measured: eleven_v3 speaks dense, number-heavy sentences at ~95 wpm (not the
# textbook 150). 70 words ≈ 44s worst case — keeps every segment under ~45s.
MAX_SPEECH_WORDS = 70


def _sentence(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    return s if s[-1] in ".!?" else s + "."


def _fit_words(sentences: list[str], max_words: int = MAX_SPEECH_WORDS) -> str:
    """Join sentences up to a word budget, never cutting mid-sentence. Always keeps ≥1."""
    out: list[str] = []
    used = 0
    for s in sentences:
        s = _sentence(s)
        if not s:
            continue
        w = len(s.split())
        if out and used + w > max_words:
            break
        out.append(s)
        used += w
    return " ".join(out)


def _subtitle(script: str, n: int = 140) -> str:
    s = script.strip().replace("\n", " ")
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def _clean_findings(agent: AgentPlan, limit: int = 12) -> list[str]:
    """Agent findings as clean sentences, dropping internal 'Top candidates:' scaffolding."""
    out: list[str] = []
    seen: set[str] = set()
    for f in agent.findings:
        if not f or f.startswith("Top candidates:"):
            continue
        s = _sentence(f)
        if s and s not in seen:
            seen.add(s)
            out.append(s)
        if len(out) >= limit:
            break
    return out


def _expert_script(agent: AgentPlan, opps: list[Opportunity]) -> str:
    # Straight to the findings — no "As market mapper, I…" preamble.
    findings = _clean_findings(agent)
    if not findings:
        names = ", ".join(o.name for o in opps[:3]) or "the shortlist"
        return f"Signals around {names} are still thin, so treat this read as directional for now."
    return _fit_words(findings)


def _display(role: str) -> str:
    return (role or "").replace("_", " ").strip() or "an analyst"


def _presenter_intro(run: Run, opps: list[Opportunity], experts: list[AgentPlan]) -> str:
    top = opps[0] if opps else None
    lines = [f"The question on the table: {run.query.strip().rstrip('.')}."]
    lines.append(f"We pulled live market data and scored {len(opps)} opportunities.")
    if top:
        lines.append(
            f"{top.name} leads at a Goliath Score of {int(top.goliathScore)}, status {top.status.value}."
        )
        lines.append(_sentence(top.prediction))
    if len(opps) > 1:
        rest = ", ".join(o.name for o in opps[1:3])
        if rest:
            lines.append(f"{rest} round out the shortlist.")
    lines.append("Here is what the team found.")
    return _fit_words(lines)


def _presenter_outro(opps: list[Opportunity]) -> str:
    if not opps:
        return "Nothing cleared the bar this round, so the call is to wait and re-scan next quarter."
    top = opps[0]
    lines = [
        f"{top.name} is where the signal is strongest, scoring {int(top.goliathScore)} at {top.riskLevel.value} risk.",
        _sentence(top.scoreReason),
    ]
    if len(opps) > 1:
        runners = ", ".join(f"{o.name} ({int(o.goliathScore)})" for o in opps[1:3])
        if runners:
            lines.append(f"{runners} are the credible runners-up.")
    lines.append("Recommendation: take first meetings at the top of this list before the next funding window closes, and size each position to the risk it carries.")
    return _fit_words(lines)


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
