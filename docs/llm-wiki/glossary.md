# Glossary

| Term | Meaning | Notes |
| --- | --- | --- |
| Goliath | The product: VC opportunity-intelligence tool that answers NL queries with a narrated multi-agent research report. | Not a trading/execution product. |
| Orchestrator | The user's "VC partner" agent; interprets the query, plans subagents, coordinates final synthesis. | Goes straight to planning, no clarification interview. |
| Subagent | A specialized research agent (market, company, funding, risk, heat) with a role, purpose, voice, and presentation segment. | Orchestrator decides how many to spawn (~4 demo target). |
| Goliath Score | Custom 0–100 opportunity score; explainable, not exact financial ROI. | Always paired with `scoreReason`. See [domain.md](domain.md). |
| Opportunity status (heat) | Compact label: `hot`, `warming`, `neutral`, `cooling`, `not_hot`. | Fixed enum; powers card labels. |
| Run | One end-to-end execution of a query through a `RunStatus` state machine. | Frontend animates off its status + events. |
| Presentation segment | One spoken chunk of the final report tied to a subagent, with script, subtitle, optional audio/image. | ElevenLabs `audioUrl` optional. |
| Word timings | Clip-relative per-word subtitle alignment for a presentation segment. | Contract field name: `wordTimings`. Frontend falls back to proportional timing when absent. |
| Cala AI | External source of structured startup/funding-round data. | See [external-services.md](external-services.md). |
| Graphifyy | Project knowledge graph used for code structure and architecture exploration. | Wiki should not duplicate Graphifyy output. |
| LLM Wiki | Human-maintained memory for rationale, domain knowledge, decisions, and pitfalls. | Explains why, not how. |
| TBD | Known gap awaiting validated information. | Prefer over invented facts. |

## Rules
- Add terms only when meaning is project-specific, overloaded, or non-obvious.
- Link terms to related wiki pages when useful.
