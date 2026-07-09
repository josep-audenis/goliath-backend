# Architecture Notes

## Purpose
- Capture architecture rationale that cannot be inferred from code.
- Keep current module/file structure in Graphifyy, not here.

## What This Backend Owns
`goliath-backend` is the backend for **Goliath**, a VC opportunity-intelligence
product. Backend (Axel + Josep) owns a **multi-agent research system** that
turns a natural-language VC query into scored investment opportunities plus a
narrated final report. Frontend (Felipe + Marc) only animates and renders what
the backend returns and must not need backend internals.

See [domain.md](domain.md) for what the product means and
[api-contract.md](api-contract.md) for the exact shape the frontend consumes.

## Core Flow (why it is shaped this way)
1. User submits a query (e.g. "startup investment opportunities in Barcelona
   related to AI").
2. **Orchestrator** interprets the query and produces a subagent plan directly
   — no clarifying-question interview (dropped for the 2.5h timebox; see
   [decisions.md](decisions.md)).
3. Subagents research (market, companies, funding, risk, current heat),
   emitting events as they go. They may be real or credibly mocked.
4. A synthesis step ranks opportunities and produces final report segments.
5. ElevenLabs audio is generated backend-side, one `audioUrl` per segment.

## Run Lifecycle
Backend exposes progress through a `Run.status` state machine so the frontend
can animate stages without knowing internals:

`awaiting_query -> planning_agents -> researching -> synthesizing -> complete`
(`error` reachable from any state).

Per-subagent `AgentPlan.status`:
`pending -> researching -> speaking -> done` (`error` possible).

Frontend drives all animation off these two enums plus the `RunEvent` stream.
Keeping the state machine and event `type` values stable is a hard cross-team
constraint.

## Streaming vs Polling
- Streaming events (`GET /api/runs/:runId/events`) is the nice-to-have.
- **Polling `GET /api/runs/:runId` is an accepted fallback** if streaming is too
  slow to build in the timebox. Frontend must tolerate either.

## Known Constraints
| Constraint | Why | Consequence | Status |
| --- | --- | --- | --- |
| Graphifyy owns code-structure knowledge | Avoid duplicate docs that drift | Wiki stores rationale only | Active |
| Frontend animates purely off `Run.status`, `AgentPlan.status`, `RunEvent` | Decouple teams under time pressure | Backend must keep the state machine + event types stable | Active |
| ElevenLabs / Cala secrets stay backend-side | Keys must not reach browser | Backend proxies all vendor calls, returns `audioUrl` | Active |
| Subagents may be mocked | 2.5h timebox; end-to-end demo beats data coverage | Output shape must be identical whether real or mocked | Active |

## Rationale Notes
- Prioritize a complete end-to-end demo over broad data coverage.
- Return credible structured output even when a subagent is a mock, so the
  frontend demo never blocks on real research.
- Persistence (in-memory vs stored reports) is undecided; treat report storage
  as swappable behind the report endpoints. See [roadmap.md](roadmap.md).

## Related
- [api-contract.md](api-contract.md)
- [domain.md](domain.md)
- [decisions.md](decisions.md)
- [external-services.md](external-services.md)
- [roadmap.md](roadmap.md)
