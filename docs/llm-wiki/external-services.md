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
- **One mp3 clip per `PresentationSegment`, not one combined file** (resolved
  2026-07-09). Backend returns a public or backend-proxied `audioUrl` per
  segment; frontend plays it when present and falls back to `script` subtitles
  timed by `durationMs` when absent.
- Backend should return clip-relative `wordTimings` when audio is generated.
  Preferred sources: ElevenLabs timestamped generation, or forced alignment of
  final audio against final `script`.
- `wordTimings` are exact-alignment data. Proportional timing is only fallback
  behavior when audio or alignment data is unavailable.
- Minimum demo target: at least **two distinct voices** working.
- Still `TBD`: exact storage/serving location for the mp3s.

## Vendor Quirks
- `TBD`: Add validated behavior that differs from docs or common expectation as
  it is discovered during integration.

## Related
- [api-contract.md](api-contract.md)
- [agents-and-voices.md](agents-and-voices.md)
- [domain.md](domain.md)
- [debugging.md](debugging.md)
- [performance.md](performance.md)
