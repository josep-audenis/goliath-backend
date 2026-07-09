# goliath-backend

## Project Purpose
- Backend for **Goliath**, a VC opportunity-intelligence product.
- Owns a multi-agent research system: turns a natural-language VC query into
  scored investment opportunities and a narrated final report.
- Backend owners: Axel + Josep. Frontend (Felipe + Marc) renders/animates only
  what the backend returns. See `docs/llm-wiki/domain.md` and `api-contract.md`.

## Architecture Overview
- Source tree currently minimal.
- Use Graphifyy for current code structure when `graphify-out/graph.json` exists.
- Keep durable rationale in `docs/llm-wiki/` when it cannot be inferred from code.

## Graphifyy
- First choice for codebase questions:
  - `graphify query "<question>"`
  - `graphify path "<A>" "<B>"`
  - `graphify explain "<concept>"`
- Use `graphify-out/wiki/index.md` for broad navigation when present.
- Use `graphify-out/GRAPH_REPORT.md` only when focused queries do not give enough context.
- Run `graphify update .` after code changes when command exists.
- Dirty `graphify-out/` files are expected and not a failure.

## Long-Term Knowledge
- `docs/llm-wiki/` is organizational memory, not code documentation.
- Graphifyy explains how code works.
- LLM Wiki explains why choices exist.
- Add durable facts only:
  - architecture decisions and tradeoffs
  - business rules and domain assumptions
  - external service quirks
  - recurring pitfalls and debugging discoveries
  - performance constraints
  - future plans and known limitations
  - glossary terms with project-specific meaning
- Do not add generated code summaries, API references, class descriptions, function explanations, or file inventories.

## Decision Log Format
Use this format for lightweight ADRs:

```markdown
### ADR-YYYYMMDD-short-title

Decision: One sentence.
Context: Why decision was needed.
Alternatives considered: Option A, option B.
Why this choice: Main rationale.
Consequences: Positive and negative effects.
Date: YYYY-MM-DD.
Status: Proposed / Accepted / Deprecated / Superseded.
```

## Decisions

### ADR-20260709-llm-wiki-memory

Decision: Store long-term agent memory in `docs/llm-wiki/`, separate from Graphifyy-generated code knowledge.
Context: Future AI agents need durable rationale, domain assumptions, and pitfalls. Graphifyy already captures source structure and relationships.
Alternatives considered: Put everything in README; store generated architecture docs; use concise LLM Wiki.
Why this choice: Separates code understanding from organizational memory and avoids duplicating source-derived facts.
Consequences: Agents must decide whether knowledge is long-term before documenting it. Some pages start sparse until real project context is learned.
Date: 2026-07-09.
Status: Accepted.

## Build
- Current build command: TBD.

## Test
- Current test command: TBD.

## Coding Conventions
- Match existing style.
- Keep changes small and scoped.
- Add tests when behavior changes and test framework exists.
- Keep docs concise.

## Branch Strategy
- Default agent branch prefix: `codex/`.
- Keep branch names short and task-specific.
- Do not rewrite shared history unless user explicitly requests it.

## Definition Of Done
- Requested behavior implemented.
- Relevant tests run, or missing tests noted.
- `graphify update .` run after code changes when available.
- New durable knowledge added to `docs/llm-wiki/` only when useful.

## Common Commands
```powershell
graphify query "<question>"
graphify update .
git status --short
```

## AI Must Never
- Invent domain facts, commands, external contracts, or architecture decisions.
- Duplicate generated code knowledge.
- Treat dirty `graphify-out/` files as failure.
- Revert user changes without explicit instruction.
- Commit secrets or generated local artifacts.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
