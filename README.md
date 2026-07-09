# goliath-backend

Backend for **Goliath** — a VC opportunity-intelligence product. A natural-language
query spawns a crew of research subagents that return scored investment
opportunities plus a narrated presentation. See `docs/llm-wiki/` for rationale.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # optional — app runs deterministically with no keys
uvicorn app.main:app --reload
```

No LLM/Cala keys required to boot: subagents fall back to credible mock data with
identical output shape, so the full pipeline runs end-to-end.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/runs` | start a run from `{query, geo?, sector?}` |
| `GET` | `/api/runs/{runId}` | poll full run state (status machine + events) |
| `GET` | `/api/runs/{runId}/events` | SSE event stream (polling is an accepted fallback) |
| `GET` | `/api/reports` | list finished reports |
| `GET` | `/api/reports/{runId}` | one final report |
| `GET` | `/health` | provider/mock status |

## Layout

```
app/
  core/config.py          settings (LLM provider, Cala, ElevenLabs)
  schemas/contract.py     load-bearing enums + models (frontend contract)
  clients/cala.py         Cala data layer — REST client + MCP server factory
  agent/
    orchestrator.py       plan -> research -> synthesize state machine + events
    runtime.py            OpenAI Agents SDK model factory + JSON parsing
    roster.py             reference subagent roster + default plan
    prompts.py            orchestrator/research/synthesis prompts
    tools.py              research tools (live Cala -> mock fallback)
    mock_data.py          credible mock output
  services/tts.py         ElevenLabs (backend-side, best-effort)
  store/run_store.py      in-memory run/report store (swappable)
  api/routes/             runs, reports, health
```

The pipeline degrades gracefully: SDK/LLM absent -> deterministic crew; Cala
absent -> mock research; ElevenLabs absent -> segments carry no `audioUrl` and
the frontend uses subtitles.