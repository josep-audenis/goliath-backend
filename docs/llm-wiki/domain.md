# Domain Knowledge

## Purpose
- Preserve business concepts, assumptions, and rules that code cannot fully explain.

## What Goliath Is
Goliath helps **venture capital users** ask natural-language questions about
startups, funding rounds, markets, and investment opportunities. A query spawns
a tailored team of AI research agents; the output is a set of scored investment
opportunities presented as a narrated multi-agent report. It is an **opportunity
intelligence** product, not a trading or execution product.

## Business Rules
| Rule | Why | Known limits | Source |
| --- | --- | --- | --- |
| Every opportunity carries a `goliathScore` (0–100), `status`, `confidence`, `riskLevel`, and `scoreReason` | Frontend cards and ranking depend on these fields always being present | Score is explainable, not financially exact | frontend PRD |
| `status` is one of `hot`, `warming`, `neutral`, `cooling`, `not_hot` | Powers a "current opportunity heat" subagent and card labels | Fixed enum; do not add values without cross-team agreement | frontend PRD |
| Predictions are short and specific (1 sentence) | They render as concise card text and spoken subtitles | Avoid hedged, long-form predictions | frontend PRD |
| Orchestrator goes directly from query to subagent plan | 2.5h timebox dropped the 5-question clarification flow | No interactive clarification in the demo | overview |
| Every final report segment maps to one subagent and may have `audioUrl` | Presentation shows one orb speaking per segment | Degrade to subtitles if audio missing | agents/voices spec |

## Goliath Score
- Custom 0–100 opportunity score, **not** a guaranteed financial ROI.
- Meant to be **explainable, not mathematically perfect** — always ship a
  `scoreReason` string alongside the number.
- Candidate factors: market attractiveness, founder/company traction, funding
  timing, competitive density, strategic fit with the user's stated
  preferences, risk level, and evidence confidence.
- Open: whether a visible formula is required or a natural-language explanation
  suffices. See [open questions in roadmap.md](roadmap.md).

## Suggested Subagent Roster (demo target: ~4)
The orchestrator dynamically decides count; this is the reference set:
- **Orchestrator / Partner** — interprets query, plans, coordinates synthesis.
- **Market Mapper** — market segments and demand signals in the target geo.
- **Company Scout** — candidate startups, funding history, traction.
- **Current Opportunities Agent** — assigns `status` heat labels + predictions.
- **Funding Analyst** — round timing and likely next-raise window (Cala data).
- **Risk Analyst** — risks, weak signals, confidence calibration.
- **Synthesis / Memo Agent** — final ranking and presentation segments.

Each subagent needs: role, purpose, research scope, a distinct voice, and a
final presentation segment.

## Assumptions
- Data comes from **news sources + Cala AI**; Cala supplies structured startup
  and funding-round context. Exact Cala fields available are `TBD`.
- Demo geography/sector is narrow (e.g. Barcelona AI); Goliath is not expected
  to cover all geographies/sectors for the hackathon.

## Open Questions
- Which scoring factors matter most, and is a visible formula required?
- Which news/search source backs the research subagents?
- Exact Cala API fields for startup/funding-round data.

## Related
- [glossary.md](glossary.md)
- [api-contract.md](api-contract.md)
- [external-services.md](external-services.md)
- [roadmap.md](roadmap.md)
