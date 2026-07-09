# Contributing — 2-person hackathon split

Two of us, one short timebox. Rule of thumb: **own disjoint files, agree on
interfaces, freeze the contract.** If we never edit the same file, git never
fights us.

## File ownership

### Axel — agents / LLM brain
```
app/agent/orchestrator.py    plan -> research -> synthesize flow + events
app/agent/prompts.py         orchestrator / research / synthesis prompts
app/agent/roster.py          subagent roster + default plan
app/agent/tools.py           research tools (live Cala -> mock fallback)
app/agent/runtime.py         model factory + JSON parsing
app/agent/mock_data.py       credible mock output
```

### Josep — data / API / integrations
```
app/clients/cala.py          real Cala wiring (REST + MCP)
app/services/tts.py          ElevenLabs synthesis
app/api/routes/*.py          runs, reports, health
app/store/run_store.py       run/report storage
```

## Frozen files — edit only after saying it out loud
```
app/schemas/contract.py      load-bearing enums + models (the seam)
app/core/config.py           additive only: append vars, never reorder
.env                         never commit (gitignored)
```

`contract.py` is the boundary between the two halves. Lock it together first
(5 min), then we each build against it with no further talking.

## Interfaces, not implementations

Call across the boundary by signature only — never read inside the other's code:

- Axel calls `run_pipeline(run_id, geo, sector)` from `app/agent/orchestrator.py`.
- Josep calls `rest.knowledge_search(...)` / `tts.attach_audio(...)`.

Agree signatures up front → fully parallel work.

## Git workflow

### Option A — branches (preferred; main stays runnable)
```bash
git switch -c josep        # or: git switch -c axel
# ...work, commit small + often...
git push -u origin josep

# merge a working piece into main:
git switch main && git pull && git merge josep && git push
```

### Option B — both on main (only with disjoint files)
Every push, replay your commit on top of theirs:
```bash
git add -A && git commit -m "..."
git pull --rebase
git push
```
Disjoint files → rebase never conflicts.

## Rules

- Commit small, every ~15 min. Not one giant end-of-day commit.
- `git pull --rebase` before every push.
- Keep `main` importable: `./.venv/Scripts/python.exe -c "import app.main"` must pass.
- Never commit `.env` or `graphify-out/`.
- Run `graphify update .` after code changes.

## Smoke test (run before pushing anything big)
```bash
./.venv/Scripts/python.exe -c "import app.main; print('boot OK')"
```
