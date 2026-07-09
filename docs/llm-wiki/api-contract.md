# API Contract (Frontend ↔ Backend)

This page records the **agreed shape** the backend must produce and the
rationale behind it. It is a durable cross-team contract, not generated API
docs — it exists because separate frontend/backend ownership under a 2.5h
timebox makes schema drift the biggest risk. Keep source-of-truth types in code
(a shared `contract.ts` / model mirror); this page explains *why* the shape is
what it is and which parts are load-bearing.

**Canonical source of truth:** the TypeScript file `web/src/lib/contract.ts`
in the frontend repo (`marcvendrellf/GoliathFrontend`). The frontend's
`llm-wiki/backend-contract.md` mirrors it. When a field changes, it changes in
`contract.ts` **and** the wiki, and the team is told — no silent drift. Backend
can validate its JSON against the frontend mock in
`web/src/lib/mock/mock-run.ts` (the frontend `api.ts` serves that mock whenever
`NEXT_PUBLIC_API_BASE_URL` is unset, so the demo runs with no backend).

## Endpoints
Minimum surface (JSON over HTTP):
- `POST /api/runs` — body `{ query: string }` (`CreateRunRequest`) → `Run`.
- `GET  /api/runs/:runId` — poll full run state → `Run`.
- `GET  /api/reports` — list finished reports → `ReportSummary[]`.
- `GET  /api/reports/:runId` — one final report → `FinalReport`.

Optional:
- `GET  /api/runs/:runId/events` — SSE stream of `RunEvent`.

Polling is an accepted substitute for streaming (see
[architecture.md](architecture.md)).

## Dev Topology / Transport (hard requirements)
- Backend assumed at `http://localhost:8000`; frontend at `http://localhost:3000`.
- **Backend must allow CORS from `http://localhost:3000`.** New hard requirement.
- Frontend polls `GET /api/runs/:runId` **every 1–2s** until status is
  `complete` or `error`. Keep that endpoint cheap.
- On `complete`, frontend hands off to the reports views — `FinalReport` must be
  fetchable by the same `runId`.

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
- Every `Opportunity` includes `goliathScore` (0–100), `status`, `confidence`
  (**0–1**, not 0–100), `riskLevel`, and `scoreReason`. Never omit these; use
  best-effort values for mocked subagents rather than nulls.
- `prediction` is one short, specific sentence.
- Timestamps (`createdAt`/`updatedAt`) are ISO 8601 strings. `FinalReport` also
  carries `createdAt`.
- Each `PresentationSegment` references one `agentId`, carries `script` +
  `subtitle`, and MAY carry `audioUrl` / `wordTimings` / `imageUrl` /
  `durationMs`. `script` is the full spoken text and doubles as subtitles.
  Missing `audioUrl` is valid — frontend falls back to subtitles timed by
  `durationMs`.
- `wordTimings` is the shared contract name for per-word subtitle alignment.
  Timings are clip-relative milliseconds from the start of that segment's audio.
  Ordered `text` values should reconstruct displayed script. Use exact alignment
  when audio exists; frontend may fall back to proportional timing when missing.
- `PresentationSegment.evidenceIds` reference `Opportunity.evidence[].id`.
- `GET /api/reports` returns `ReportSummary[]`, a lighter shape than `Run`:
  `runId`, `title`, `query`, `status`, `createdAt`, `opportunityCount`, and
  `topOpportunities` (each just `id`, `startupName`, `goliathScore`, `status`).
- `RunEvent` order/timestamps drive the animation timeline; emit events in
  causal order. The **`agent.spawned` event per agent matters most** — it drives
  the spawn animation.

## Shape Reference
Do not paste the full type listings here (that would be code documentation that
drifts). The canonical types live in `web/src/lib/contract.ts` in the frontend
repo; mirror them in a backend model file. This page holds only rationale and
the invariants above.

## Related
- [architecture.md](architecture.md)
- [domain.md](domain.md)
- [external-services.md](external-services.md)
- [agents-and-voices.md](agents-and-voices.md)
- [decisions.md](decisions.md)
