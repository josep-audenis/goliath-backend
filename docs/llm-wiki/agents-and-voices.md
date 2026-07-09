# Agents And Voices

## Core Model
- Orchestrator is the user's VC partner.
- Orchestrator reads the query, decides needed subagents, and coordinates final synthesis.
- Subagents need role, purpose, research scope, distinct voice/personality, and final presentation segment.

## Demo Agent Roster
| Agent | Purpose | Voice | Output |
| --- | --- | --- | --- |
| Orchestrator / Partner | Interpret query, decide plan, coordinate final recommendation | Calm senior VC partner | Intro/conclusion if time allows |
| Market Mapper | Identify relevant AI/startup segments in target geography | Analytical and concise | Market map, demand signals, sector attractiveness |
| Company Scout | Find candidate startups and summarize funding, stage, traction | Energetic scout | Startup shortlist and evidence |
| Current Opportunities Agent | Classify opportunity heat and produce concise cards | Fast, current, decisive | Heat labels and concise predictions |
| Funding Analyst | Inspect rounds, timing, investors, likely next raise windows | Precise finance analyst | Round history and timing prediction |
| Risk Analyst | Identify risks, weak signals, competitive threats, data gaps | Skeptical partner | Risk assessment and confidence calibration |
| Synthesis / Investment Memo Agent | Turn findings into ranking and presentation segments | Polished presenter | Final report |

## Voice Rules
- ElevenLabs calls happen backend-side only.
- Backend returns one `audioUrl` per presentation segment.
- Backend should return clip-relative `wordTimings` when audio is generated.
- Each subagent may have distinct ElevenLabs voice ID.
- Frontend degrades to subtitles when audio is missing.
- Minimum demo target: at least two distinct voices working.

## Final Presentation Behavior
1. Orb enters or becomes active.
2. Agent name, role, and purpose appear.
3. Audio starts when present.
4. Subtitle words reveal at audio-aligned timestamps.
5. Frontend falls back to proportional text timing when `wordTimings` or audio is unavailable.
6. Supporting data, image, or evidence appears when available.
7. Next orb enters after segment completes.

## Related
- [api-contract.md](api-contract.md)
- [external-services.md](external-services.md)
- [domain.md](domain.md)
