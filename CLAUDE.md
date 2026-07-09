# goliath-backend

## Project Purpose
- Backend service for `goliath-backend`.
- Product/domain purpose: TBD.

## Architecture Overview
- Source tree currently minimal.
- Use Graphifyy for current code structure when `graphify-out/graph.json` exists.
- Keep rationale here only when it cannot be inferred from code.

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
- This file is organizational memory, not code documentation.
- Graphifyy explains how code works.
- This file explains why choices exist.
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

### ADR-20260709-root-memory-only

Decision: Store agent-facing long-term knowledge in `CLAUDE.md` and `AGENTS.md`, not a separate wiki system.
Context: Project needs durable AI guidance, but user wants no wiki update script and no git hook.
Alternatives considered: `docs/llm-wiki` directory, validator script, non-blocking pre-commit reminder.
Why this choice: Root prompt files are already read by agents and avoid extra maintenance surface.
Consequences: Less structure than a wiki, but lower overhead. Long entries must stay concise to avoid bloating startup context.
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
- New durable knowledge added here only when useful.

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
