"""Shared fixtures for the agent-brain (Axel-owned) tests.

Scope: these tests exercise only Axel's modules — `app/agent/*` — and reach the
run/report store through its public interface (never editing it). They run fully
offline: the fixture below strips any real keys from a local `.env` so
`llm_enabled()` is False and the deterministic mock pipeline is what's tested.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

from app.agent.orchestrator import run_pipeline
from app.core.config import settings
from app.schemas.contract import Run, RunStatus
from app.store.run_store import store


@pytest.fixture(autouse=True)
def deterministic_mode(monkeypatch):
    """Force the offline/mock pipeline regardless of keys present in .env."""
    for attr in ("groq_api_key", "openai_api_key", "hf_token", "cala_api_key", "cala_mcp_api_key", "elevenlabs_api_key"):
        monkeypatch.setattr(settings, attr, "", raising=False)
    monkeypatch.setattr(settings, "use_cala_mock", True, raising=False)
    yield


@pytest.fixture(autouse=True)
def clean_store():
    store._runs.clear()
    store._reports.clear()
    yield
    store._runs.clear()
    store._reports.clear()


async def make_completed_run(query: str = "AI startups in Barcelona", geo: str | None = None, sector: str | None = None) -> Run:
    """Drive the pipeline to completion deterministically and return the run."""
    run_id = uuid.uuid4().hex[:12]
    store.put_run(Run(runId=run_id, query=query, status=RunStatus.AWAITING_QUERY))
    await run_pipeline(run_id, geo=geo, sector=sector)
    return store.get_run(run_id)


@pytest_asyncio.fixture
async def completed_run() -> Run:
    return await make_completed_run()
