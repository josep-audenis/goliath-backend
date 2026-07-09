"""
In-memory run/report store.

Persistence (in-memory vs DB) is deliberately undecided for the hackathon
(see docs/llm-wiki/roadmap.md). Everything the API reads goes through this
interface so storage stays swappable behind it.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Optional

from app.schemas.contract import (
    Report,
    ReportSummary,
    Run,
    RunEvent,
    RunStatus,
    TopOpportunity,
    _report_title,
)


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[str, Run] = {}
        self._reports: dict[str, Report] = {}
        self._lock = threading.RLock()

    # ---- runs ----
    def put_run(self, run: Run) -> None:
        with self._lock:
            run.updatedAt = datetime.now(timezone.utc)
            self._runs[run.runId] = run

    def get_run(self, run_id: str) -> Optional[Run]:
        with self._lock:
            return self._runs.get(run_id)

    def append_event(self, run_id: str, event: RunEvent) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if run is not None:
                run.events.append(event)
                run.updatedAt = datetime.now(timezone.utc)

    # ---- reports ----
    def put_report(self, report: Report) -> None:
        with self._lock:
            self._reports[report.runId] = report

    def get_report(self, run_id: str) -> Optional[Report]:
        with self._lock:
            return self._reports.get(run_id)

    def list_reports(self) -> list[ReportSummary]:
        with self._lock:
            items = [
                ReportSummary(
                    runId=r.runId,
                    title=_report_title(r.query, r.opportunities),
                    query=r.query,
                    # reports are only stored once a run completes.
                    status=RunStatus.COMPLETE,
                    createdAt=r.createdAt,
                    opportunityCount=len(r.opportunities),
                    topOpportunities=[
                        TopOpportunity(
                            id=o.id,
                            startupName=o.name,
                            goliathScore=o.goliathScore,
                            status=o.status,
                        )
                        for o in r.opportunities[:3]
                    ],
                )
                for r in self._reports.values()
            ]
        return sorted(items, key=lambda s: s.createdAt, reverse=True)


store = RunStore()
