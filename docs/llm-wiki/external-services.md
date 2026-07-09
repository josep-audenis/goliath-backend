# External Services

## Integrations
| Service | Purpose | Quirks | Limits | Source |
| --- | --- | --- | --- | --- |
| Cala AI | Structured startup + financial/company context (funding rounds, stage, traction) for research subagents | Exact available fields are `TBD` for the hackathon | `TBD` | overview/domain spec |
| News / web search | Market and current-heat signals for opportunity discovery | Specific provider not yet chosen (`TBD`) | `TBD` | domain spec |
| ElevenLabs | Text-to-speech for final report segments; each subagent can have a distinct voice | See ElevenLabs notes below | Voice IDs `TBD` | agents/voices spec |

## Credentials And Secrets
- Do not commit secrets.
- **All ElevenLabs and Cala calls go through the backend.** Frontend must never
  hold these keys — a hard constraint, not a preference.
- Document secret names and required scopes only when stable. Do not document
  secret values.

## ElevenLabs Notes
- Backend returns one `audioUrl` per `PresentationSegment`; frontend plays it
  when present and falls back to subtitle text when absent.
- Minimum demo target: at least **two distinct voices** working.
- Undecided (`TBD`): whether audio is one combined file, per-agent clips, or
  streamed; where audio files are stored/served from; whether subtitles need
  per-word/sentence timing or segment-level text is enough.

## Vendor Quirks
- `TBD`: Add validated behavior that differs from docs or common expectation as
  it is discovered during integration.

## Related
- [api-contract.md](api-contract.md)
- [domain.md](domain.md)
- [debugging.md](debugging.md)
- [performance.md](performance.md)
