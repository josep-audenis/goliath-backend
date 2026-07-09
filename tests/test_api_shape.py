"""Person A — API response-shape contract tests.

These assert the *serialized JSON* the endpoints return matches the field names
the frontend expects (web/src/lib/contract.ts). They hit the real routes through
an in-process ASGI client, so they exercise FastAPI's alias serialization — the
actual bytes the frontend receives.
"""

from __future__ import annotations

import asyncio

from app.schemas.contract import RunStatus
from tests.conftest import make_completed_run

OPP_STATUSES = {"hot", "warming", "neutral", "cooling", "not_hot"}
EVIDENCE_SOURCES = {"cala", "news", "web", "manual"}


async def test_get_run_uses_frontend_field_names(client):
    run = await make_completed_run()
    body = (await client.get(f"/api/runs/{run.runId}")).json()

    # Run.id (not runId)
    assert body["id"] == run.runId
    assert "runId" not in body
    for key in ("query", "status", "agents", "events", "opportunities"):
        assert key in body


async def test_agent_and_event_shape(client):
    run = await make_completed_run()
    body = (await client.get(f"/api/runs/{run.runId}")).json()

    for a in body["agents"]:
        assert a["name"]  # display name derived from role
        assert "voiceId" in a
        assert "voice" not in a

    assert body["events"]
    for e in body["events"]:
        assert e["id"] and e["timestamp"] and isinstance(e["text"], str) and e["text"]
        assert "ts" not in e and "payload" not in e


async def test_opportunity_shape_and_confidence_scale(client):
    run = await make_completed_run()
    body = (await client.get(f"/api/runs/{run.runId}")).json()

    opps = body["opportunities"]
    assert 3 <= len(opps) <= 5
    for o in opps:
        assert o["startupName"] and "name" not in o
        assert "location" in o and "geo" not in o
        assert o["summary"]
        assert 0 <= o["confidence"] <= 1, "confidence must serialize on a 0-1 scale"
        assert o["status"] in OPP_STATUSES
        for ev in o["evidence"]:
            assert ev["id"]
            assert ev["source"] in EVIDENCE_SOURCES


async def test_final_report_shape(client):
    run = await make_completed_run()
    body = (await client.get(f"/api/reports/{run.runId}")).json()

    for key in ("id", "runId", "title", "executiveSummary", "createdAt", "opportunities", "segments"):
        assert key in body, f"FinalReport missing {key}"
    assert body["id"] == f"report-{run.runId}"
    assert "query" not in body
    assert body["opportunities"][0]["startupName"]


async def test_report_summary_shape(client):
    run = await make_completed_run()
    summaries = (await client.get("/api/reports")).json()

    assert summaries
    s = next(x for x in summaries if x["runId"] == run.runId)
    for key in ("runId", "title", "query", "status", "createdAt", "opportunityCount", "topOpportunities"):
        assert key in s, f"ReportSummary missing {key}"
    assert s["status"] in {rs.value for rs in RunStatus}
    for top in s["topOpportunities"]:
        assert set(top.keys()) == {"id", "startupName", "goliathScore", "status"}


async def test_create_run_returns_id_and_completes(client):
    created = (await client.post("/api/runs", json={"query": "AI startups in Barcelona"})).json()
    assert "id" in created and created["query"]
    assert created["status"] in {rs.value for rs in RunStatus}

    run_id = created["id"]
    for _ in range(60):
        body = (await client.get(f"/api/runs/{run_id}")).json()
        if body["status"] in ("complete", "error"):
            break
        await asyncio.sleep(0.05)
    assert body["status"] == "complete"
    assert body["id"] == run_id


async def test_unknown_ids_return_404(client):
    assert (await client.get("/api/runs/nope")).status_code == 404
    assert (await client.get("/api/reports/nope")).status_code == 404
