# API Contract (Frontend ↔ Backend)

This page records the **agreed shape** the backend must produce and the
rationale behind it. It is a durable cross-team contract, not generated API
docs — it exists because separate frontend/backend ownership under a 2.5h
timebox makes schema drift the biggest risk. Keep source-of-truth types in code
(a shared `contract.ts` / model mirror); this page explains *why* the shape is
what it is and which parts are load-bearing.

Origin: proposed by frontend in `GoliathFrontend/llm-wiki/backend-contract.md`.
Simplify only by mutual agreement.

## Endpoints
Minimum surface:
- `POST /api/runs` — start a run from a query.
- `GET  /api/runs/:runId` — poll full run state.
- `GET  /api/reports` — list finished reports.
- `GET  /api/reports/:runId` — one final report.

Optional:
- `GET  /api/runs/:runId/events` — stream events.

Polling is an accepted substitute for streaming (see
[architecture.md](architecture.md)).

## Load-Bearing Enums (do not change unilaterally)
- `RunStatus`: `awaiting_query | planning_agents | researching | synthesizing | complete | error`
- `AgentPlan.status`: `pending | researching | speaking | done | error`
- `RunEvent.type`: `orchestrator.plan | agent.spawned | agent.message | agent.finding | report.segment_ready | run.complete`
- `Opportunity.status`: `hot | warming | neutral | cooling | not_hot`
- `Opportunity.riskLevel`: `low | medium | high`
- `Evidence.source`: `cala | news | web | manual`

Frontend animation and card rendering are switch-statements over these values.
Adding/removing a value is a breaking change requiring cross-team sign-off.

## Field Contracts That Must Not Regress
- Every `Opportunity` includes `goliathScore` (0–100), `status`, `confidence`,
  `riskLevel`, and `scoreReason`. Never omit these; use best-effort values for
  mocked subagents rather than nulls.
- `prediction` is one short, specific sentence.
- Each `PresentationSegment` references one `agentId`, carries `script` +
  `subtitle`, and MAY carry `audioUrl` / `imageUrl`. Missing `audioUrl` is
  valid — frontend falls back to subtitle text.
- `RunEvent` order/timestamps drive the animation timeline; emit events in
  causal order.

## Shape Reference
Full TypeScript types live in the frontend contract file and any backend model
mirror — see `backend-contract.md` in the frontend repo. Do not paste the type
listings here (that would be code documentation that drifts); keep this page to
rationale and the invariants above.

## Related
- [architecture.md](architecture.md)
- [domain.md](domain.md)
- [external-services.md](external-services.md)
- [decisions.md](decisions.md)
