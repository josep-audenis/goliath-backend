# Roadmap

Context: Goliath began as a 2.5h hackathon build. Scope is deliberately narrow
— a complete end-to-end demo beats broad coverage.

## Minimum Successful Demo
- One user query → ~4 spawned subagents.
- Research-progress animation driven by run/agent status + events.
- 3–5 final opportunities, each with `goliathScore`, `status`, concise
  prediction, `confidence`, `riskLevel`, and evidence.
- Narrated final presentation with ≥2 distinct ElevenLabs voices + subtitles.
- Report list + report detail view.

## Future Plans
| Item | Why | Blocked by | Status |
| --- | --- | --- | --- |
| Real subagent research (replace mocks) | Credibility beyond demo | Cala fields + news source choice | Planned |
| Streaming events endpoint | Smoother animation than polling | Backend time budget | Optional |
| Report persistence | Reuse/share past runs | Storage decision (in-memory vs DB) undecided | Open |
| Explicit Goliath Score formula | Explainability / tuning | Agreement on factors + whether formula must be visible | Open |

## Out Of Scope (hackathon)
- Real investment execution; CRM / portfolio management.
- Deep auth / permissions.
- Long-term production persistence unless trivial.
- General VC research across all geographies/sectors.
- Any Polymarket / trading UI or pixel-art map UI (see
  [decisions.md](decisions.md)).

## Known Limitations
| Limitation | Impact | Workaround | Owner |
| --- | --- | --- | --- |
| Subagents may be mocked | Findings not fully real | Keep output shape identical to real runs | Backend |
| Cala fields unknown | Research depth uncertain | Mock credible structured output | Backend |
| No clarification flow | Cannot refine ambiguous queries | Orchestrator plans directly from one query | Product |

## Rules
- Keep plans durable, not sprint task lists.
- Remove or update stale plans when decisions change.
- Link accepted decisions when roadmap items become commitments.

## Related
- [decisions.md](decisions.md)
- [domain.md](domain.md)
- [architecture.md](architecture.md)
