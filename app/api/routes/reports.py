"""Report endpoints — list finished reports and fetch one."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.contract import Report, ReportSummary, ReportTranscript
from app.services.transcript import build_report_transcript
from app.store.run_store import store

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("", response_model=list[ReportSummary])
async def list_reports() -> list[ReportSummary]:
    return store.list_reports()


@router.get("/{run_id}", response_model=Report)
async def get_report(run_id: str) -> Report:
    report = store.get_report(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return report


@router.get("/{run_id}/transcript", response_model=ReportTranscript)
async def get_report_transcript(run_id: str) -> ReportTranscript:
    report = store.get_report(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return build_report_transcript(report)
