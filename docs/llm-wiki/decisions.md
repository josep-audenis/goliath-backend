# Decision Log

Use this page for lightweight ADRs. Append newest decisions at top.

## ADR Format
```markdown
## ADR-YYYYMMDD-short-title

| Field | Value |
| --- | --- |
| Decision | One sentence |
| Date | YYYY-MM-DD |
| Status | Proposed / Accepted / Deprecated / Superseded |

### Context
- Why decision was needed.

### Alternatives Considered
| Option | Tradeoff |
| --- | --- |
| Option A | Tradeoff |

### Why This Choice
- Reason.

### Consequences
- Positive and negative effects.
```

## ADR-20260709-contract-ts-source-of-truth

| Field | Value |
| --- | --- |
| Decision | `web/src/lib/contract.ts` in the frontend repo is the canonical schema; backend mirrors it and validates against the frontend mock. ElevenLabs audio ships as one mp3 per segment. |
| Date | 2026-07-09 |
| Status | Accepted |

### Context
- Frontend is now a built Next.js app driven entirely by a TypeScript contract
  plus a mock, with automatic mock fallback when the backend is down.
- Backend needs a single unambiguous schema to target and a way to self-check.

### Alternatives Considered
| Option | Tradeoff |
| --- | --- |
| Wiki prose as the schema | Readable, but drifts from what frontend code actually parses |
| Backend defines its own schema | Autonomy, but guarantees drift and breaks the shared demo |
| Frontend `contract.ts` canonical + mock to validate against | Backend must track another repo's file, but zero drift and self-testable |

### Why This Choice
- The frontend already parses `contract.ts`; matching it is the only way to
  guarantee the demo works. The mock (`mock-run.ts`) gives backend a concrete
  fixture to diff responses against.

### Consequences
- Backend model changes must be reconciled with `contract.ts` and the wiki
  together. New hard transport requirements: CORS from `http://localhost:3000`,
  1–2s poll-friendly `GET /api/runs/:runId`, per-segment mp3 `audioUrl`s.

## ADR-20260709-vc-opportunity-intelligence-pivot

| Field | Value |
| --- | --- |
| Decision | Goliath is a VC opportunity-intelligence product; drop all Polymarket/trading and pixel-art-office directions. |
| Date | 2026-07-09 |
| Status | Accepted |

### Context
- Product pivoted away from prediction-market/trading framing.
- Target user is a VC asking about startups, funding rounds, and markets.

### Alternatives Considered
| Option | Tradeoff |
| --- | --- |
| Keep Polymarket/trading UI | Reuses prior work, but wrong audience and adds a trading surface out of scope |
| Pixel-art office metaphor | Fun, but heavy dependency and off-brand for a VC tool |
| Clean orb/node agent UI over a VC research backend | Requires new build, but matches audience and demo goal |

### Why This Choice
- Matches the VC audience and the narrated multi-agent demo moment.
- Removes scope (trading, pixel art) the timebox cannot afford.

### Consequences
- Backend focuses on opportunity discovery + scoring, not markets/trading.
- No trading or pixel-art code paths should be added.

## ADR-20260709-drop-clarification-flow

| Field | Value |
| --- | --- |
| Decision | Orchestrator plans subagents directly from the query; drop the 5-question clarification interview. |
| Date | 2026-07-09 |
| Status | Accepted |

### Context
- 2.5h timebox; the clarifying-question flow added latency and build cost.

### Alternatives Considered
| Option | Tradeoff |
| --- | --- |
| Keep 5-question interview | Better query refinement, but slower demo and more UI |
| Direct query → plan | Faster wow moment, but can't disambiguate vague queries |

### Why This Choice
- The demo's wow moment is fast spawning + narrated report, not refinement.

### Consequences
- No interactive clarification; vague queries handled by orchestrator defaults.

## ADR-20260709-status-driven-decoupling

| Field | Value |
| --- | --- |
| Decision | Frontend animates purely from `Run.status`, `AgentPlan.status`, and `RunEvent`; polling is an accepted alternative to streaming. |
| Date | 2026-07-09 |
| Status | Accepted |

### Context
- Separate frontend/backend ownership under a tight timebox; schema drift is the
  main risk. Streaming may be too slow to build.

### Alternatives Considered
| Option | Tradeoff |
| --- | --- |
| Frontend reads backend internals | Tight coupling, breaks parallel work |
| Streaming-only events | Smoothest animation, but risky to build in time |
| Status enums + events, polling fallback | Slightly less smooth, but robust and parallelizable |

### Why This Choice
- Lets both teams build against a stable contract; degrades gracefully.

### Consequences
- Backend must keep status enums + event `type` values stable (breaking to
  change). See [api-contract.md](api-contract.md).

## ADR-20260709-llm-wiki-memory

| Field | Value |
| --- | --- |
| Decision | Store long-term agent memory in concise Markdown wiki separate from Graphifyy-generated code knowledge. |
| Date | 2026-07-09 |
| Status | Accepted |

### Context
- Future AI agents need durable rationale, domain assumptions, and pitfalls.
- Graphifyy already captures source structure and relationships.
- Duplicating source-derived facts creates drift.

### Alternatives Considered
| Option | Tradeoff |
| --- | --- |
| Put everything in README | Easy to find, but bloats onboarding and mixes audiences |
| Store generated architecture docs | Broad coverage, but duplicates Graphifyy and gets stale |
| Use concise LLM Wiki | Requires maintenance, but preserves why-oriented knowledge |

### Why This Choice
- Separates code understanding from organizational memory.
- Encourages small updates only when new durable knowledge appears.
- Gives agents clear routing before editing.

### Consequences
- Agents must decide whether knowledge is long-term before documenting it.
- Some pages start sparse until real project context is learned.
