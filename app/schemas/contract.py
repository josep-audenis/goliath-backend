"""
Frontend <-> backend contract.

The enums below are LOAD-BEARING: frontend animation and card rendering are
switch-statements over these exact values. Changing a value is a breaking change
requiring cross-team sign-off. See docs/llm-wiki/api-contract.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Load-bearing enums
# ---------------------------------------------------------------------------


class RunStatus(str, Enum):
    AWAITING_QUERY = "awaiting_query"
    PLANNING_AGENTS = "planning_agents"
    RESEARCHING = "researching"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    ERROR = "error"


class AgentStatus(str, Enum):
    PENDING = "pending"
    RESEARCHING = "researching"
    SPEAKING = "speaking"
    DONE = "done"
    ERROR = "error"


class RunEventType(str, Enum):
    ORCHESTRATOR_PLAN = "orchestrator.plan"
    AGENT_SPAWNED = "agent.spawned"
    AGENT_MESSAGE = "agent.message"
    AGENT_FINDING = "agent.finding"
    REPORT_SEGMENT_READY = "report.segment_ready"
    RUN_COMPLETE = "run.complete"


class OpportunityStatus(str, Enum):
    HOT = "hot"
    WARMING = "warming"
    NEUTRAL = "neutral"
    COOLING = "cooling"
    NOT_HOT = "not_hot"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceSource(str, Enum):
    CALA = "cala"
    NEWS = "news"
    WEB = "web"
    MANUAL = "manual"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Evidence(BaseModel):
    source: EvidenceSource
    title: str
    url: Optional[str] = None
    snippet: Optional[str] = None


class Opportunity(BaseModel):
    """A scored investment opportunity. The five scored fields must never be null."""

    id: str
    name: str
    goliathScore: float = Field(ge=0, le=100)
    status: OpportunityStatus
    confidence: float = Field(ge=0, le=100)
    riskLevel: RiskLevel
    scoreReason: str
    prediction: str  # one short, specific sentence
    sector: Optional[str] = None
    geo: Optional[str] = None
    stage: Optional[str] = None
    evidence: list[Evidence] = Field(default_factory=list)


class AgentPlan(BaseModel):
    """One planned/spawned research subagent."""

    id: str
    role: str
    purpose: str
    voice: Optional[str] = None  # ElevenLabs voice id / label
    status: AgentStatus = AgentStatus.PENDING
    findings: list[str] = Field(default_factory=list)


class RunEvent(BaseModel):
    type: RunEventType
    ts: datetime = Field(default_factory=_now)
    agentId: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class PresentationSegment(BaseModel):
    agentId: str
    script: str
    subtitle: str
    audioUrl: Optional[str] = None
    imageUrl: Optional[str] = None


class Report(BaseModel):
    runId: str
    query: str
    createdAt: datetime = Field(default_factory=_now)
    opportunities: list[Opportunity] = Field(default_factory=list)
    segments: list[PresentationSegment] = Field(default_factory=list)


class Run(BaseModel):
    runId: str
    query: str
    status: RunStatus = RunStatus.AWAITING_QUERY
    agents: list[AgentPlan] = Field(default_factory=list)
    opportunities: list[Opportunity] = Field(default_factory=list)
    segments: list[PresentationSegment] = Field(default_factory=list)
    events: list[RunEvent] = Field(default_factory=list)
    error: Optional[str] = None
    createdAt: datetime = Field(default_factory=_now)
    updatedAt: datetime = Field(default_factory=_now)


# ---- request/response wrappers ----


class CreateRunRequest(BaseModel):
    query: str
    geo: Optional[str] = None
    sector: Optional[str] = None


class ReportSummary(BaseModel):
    runId: str
    query: str
    createdAt: datetime
    opportunityCount: int
