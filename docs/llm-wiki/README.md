# LLM Wiki

Organizational memory for future AI agents and maintainers.

Graphifyy explains how code works. This wiki explains why choices exist.

## What Belongs Here
- Architectural decisions and tradeoffs.
- Design rationale and rejected alternatives.
- Business rules that are not obvious from code.
- Domain assumptions and vocabulary.
- Constraints from operations, security, compliance, data, or vendors.
- Recurring implementation patterns and pitfalls.
- Debugging discoveries worth remembering.
- External API quirks and integration gotchas.
- Performance limits, bottlenecks, and tuning notes.
- Future plans that guide near-term implementation.

## What Does Not Belong
- API reference.
- Code listings.
- Function, class, or file explanations.
- Endpoint inventories.
- Generated Graphifyy summaries.
- Facts that can be recovered by reading current source.

## Page Map
| Page | Use when |
| --- | --- |
| [architecture.md](architecture.md) | Rationale behind architecture boundaries, data flow, and constraints |
| [domain.md](domain.md) | Business concepts, assumptions, rules, and invariants |
| [api-contract.md](api-contract.md) | Frontend↔backend contract rationale, load-bearing enums, and field invariants |
| [decisions.md](decisions.md) | Lightweight ADR log |
| [conventions.md](conventions.md) | Durable project patterns not obvious from tooling |
| [debugging.md](debugging.md) | Root causes, symptoms, diagnostics, and fixes worth preserving |
| [performance.md](performance.md) | Bottlenecks, budgets, scaling limits, and measurement notes |
| [roadmap.md](roadmap.md) | Future work and known limitations |
| [glossary.md](glossary.md) | Project vocabulary and overloaded terms |
| [external-services.md](external-services.md) | Vendor contracts, quirks, limits, and credentials notes |
| [prompts.md](prompts.md) | Reusable prompts and agent workflows |

## When To Create New Pages
- Existing page would become too broad.
- Topic has independent lifecycle or owner.
- Topic will likely collect multiple long-term entries.

Prefer editing existing pages. Link related pages.

## Agent Workflow
1. Use Graphifyy for code structure.
2. Read [../../CLAUDE.md](../../CLAUDE.md).
3. Pick only relevant wiki pages from page map.
4. Make code changes.
5. Add wiki entry only if new durable knowledge was learned.

## Entry Quality Checklist
- Answers why, when, tradeoffs, alternatives, or limits.
- Concise enough for future agent to scan.
- Links related pages.
- Avoids code documentation.
- Marks unknown facts as `TBD` instead of guessing.
