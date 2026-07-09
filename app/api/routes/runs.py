"""Run endpoints — start a run, poll its state, optionally stream events."""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agent.orchestrator import run_pipeline
from app.schemas.contract import CreateRunRequest, Run, RunStatus
from app.store.run_store import store

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", response_model=Run)
async def create_run(req: CreateRunRequest) -> Run:
    run_id = uuid.uuid4().hex[:12]
    run = Run(runId=run_id, query=req.query, status=RunStatus.AWAITING_QUERY)
    store.put_run(run)
    # Fire-and-forget: pipeline drives the state machine; frontend polls this run.
    asyncio.create_task(run_pipeline(run_id, geo=req.geo, sector=req.sector))
    return run


@router.get("/{run_id}", response_model=Run)
async def get_run(run_id: str) -> Run:
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return run


@router.get("/{run_id}/events")
async def stream_events(run_id: str) -> StreamingResponse:
    """SSE stream of RunEvents. Polling GET /{run_id} is an accepted fallback."""
    if store.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="run not found")

    async def gen():
        sent = 0
        while True:
            run = store.get_run(run_id)
            if run is None:
                break
            events = run.events
            while sent < len(events):
                yield f"data: {events[sent].model_dump_json()}\n\n"
                sent += 1
            if run.status in (RunStatus.COMPLETE, RunStatus.ERROR):
                yield f"event: done\ndata: {json.dumps({'status': run.status.value})}\n\n"
                break
            await asyncio.sleep(0.4)

    return StreamingResponse(gen(), media_type="text/event-stream")
