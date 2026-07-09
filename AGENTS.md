# Agent Instructions

## Style
- Respond terse like smart caveman.
- Keep technical substance.
- Drop filler, pleasantries, and hedging.
- Use normal grammar in code blocks, commit messages, PR text, and destructive-action warnings.

## First Reads
- Read `CLAUDE.md` before making changes.
- Read only relevant pages in `docs/llm-wiki/`, not whole wiki.
- Use Graphifyy for code structure before raw source browsing when `graphify-out/graph.json` exists:
  - `graphify query "<question>"`
  - `graphify path "<A>" "<B>"`
  - `graphify explain "<concept>"`

## Graphifyy Rules
- Graphifyy explains how code works.
- Do not duplicate Graphifyy output in docs.
- Dirty `graphify-out/` files are expected after hooks or incremental updates.
- Dirty graph files are not reason to skip Graphifyy.
- Skip Graphifyy only when task is about stale or incorrect graph output, or user explicitly says not to use it.
- If `graphify-out/wiki/index.md` exists, use it for broad navigation before raw source browsing.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` when command exists.

## Long-Term Knowledge
- `docs/llm-wiki/` is project memory.
- `CLAUDE.md` and `AGENTS.md` define agent operating rules.
- Add only durable knowledge that future agents cannot infer from code or Graphifyy:
  - architectural decisions
  - design rationale
  - business logic
  - assumptions
  - domain knowledge
  - constraints
  - recurring patterns
  - common pitfalls
  - debugging discoveries
  - implementation notes
  - future plans
  - glossary terms
  - external API quirks
  - performance considerations
- Do not add:
  - API docs
  - code listings
  - function explanations
  - class descriptions
  - file summaries

## Documentation Rules
- Keep documentation concise.
- Prefer bullets, tables, decision logs, and checklists.
- Every important fact should answer why, when, tradeoffs, alternatives, or known limitations.
- Prefer editing existing wiki pages over creating new files.
- Do not create scripts or git hooks for documentation maintenance unless user asks.
- Do not invent project facts. Mark unknowns as `TBD` with owner or discovery step.

## Change Discipline
- Keep changes scoped to user request.
- Preserve user changes in dirty worktrees.
- Do not run destructive git commands unless user explicitly asks.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
