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
