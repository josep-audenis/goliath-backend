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
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, field_serializer


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Presentation helpers (derive the human-facing fields the frontend expects
# from the internal data the pipeline produces — Person A owns the mapping,
# Person B owns the underlying data).
# ---------------------------------------------------------------------------


def _display_name(role: str) -> str:
    """Slug role -> display name, e.g. 'market_mapper' -> 'Market Mapper'."""
    return (role or "").replace("_", " ").title() or "Analyst"


def _opportunity_summary(sector: Optional[str], stage: Optional[str], geo: Optional[str]) -> str:
    head = f"{stage} " if stage else ""
    where = f" in {geo}" if geo else ""
    return f"{head}{sector or 'startup'}{where}".strip().capitalize()


def _report_title(query: str, opportunities: list["Opportunity"]) -> str:
    loc = next((o.geo for o in opportunities if o.geo), None)
    sector = next((o.sector for o in opportunities if o.sector), None)
    if sector and loc:
        return f"{sector} investment opportunities — {loc}"
    if loc:
        return f"Investment opportunities — {loc}"
    return f"Investment opportunities: {query[:60]}"


def _executive_summary(opportunities: list["Opportunity"]) -> str:
    if not opportunities:
        return "No opportunities cleared the bar for this query."
    top = opportunities[0]
    rest = ", ".join(o.name for o in opportunities[1:3])
    tail = f" {rest} round out the shortlist." if rest else ""
    return f"{top.name} leads at {int(top.goliathScore)} ({top.status.value}): {top.scoreReason}{tail}"


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
    # `id` lets presentation segments reference specific evidence.
    id: str = Field(default_factory=lambda: f"evd-{uuid4().hex[:8]}")
    source: EvidenceSource
    title: str
    url: Optional[str] = None
    snippet: Optional[str] = None


class Opportunity(BaseModel):
    """A scored investment opportunity. The five scored fields must never be null.

    The pipeline constructs this by internal attribute names (`name`, `geo`); the
    serialized JSON uses the frontend names (`startupName`, `location`) via
    aliases, plus a derived `summary` and a 0-1 `confidence`.
    """

    id: str
    name: str = Field(serialization_alias="startupName")
    goliathScore: float = Field(ge=0, le=100)
    status: OpportunityStatus
    confidence: float = Field(ge=0, le=100)  # stored 0-100; serialized 0-1 (below)
    riskLevel: RiskLevel
    scoreReason: str
    prediction: str  # one short, specific sentence
    sector: Optional[str] = None
    geo: Optional[str] = Field(default=None, serialization_alias="location")
    stage: Optional[str] = None
    evidence: list[Evidence] = Field(default_factory=list)

    @computed_field
    @property
    def summary(self) -> str:
        return _opportunity_summary(self.sector, self.stage, self.geo)

    @field_serializer("confidence")
    def _confidence_0_1(self, v: float) -> float:
        # internal scale is 0-100; the frontend expects 0-1.
        return round(v / 100, 4) if v > 1 else round(v, 4)


class AgentPlan(BaseModel):
    """One planned/spawned research subagent."""

    id: str
    role: str
    purpose: str
    voice: Optional[str] = Field(default=None, serialization_alias="voiceId")  # ElevenLabs voice
    status: AgentStatus = AgentStatus.PENDING
    findings: list[str] = Field(default_factory=list, exclude=True)  # internal scratch

    @computed_field
    @property
    def name(self) -> str:
        return _display_name(self.role)


class RunEvent(BaseModel):
    # `payload` is the internal structured detail the pipeline emits; the frontend
    # consumes the derived `id`/`timestamp`/`title`/`text` instead.
    id: str = Field(default_factory=lambda: f"ev-{uuid4().hex[:8]}")
    type: RunEventType
    ts: datetime = Field(default_factory=_now, serialization_alias="timestamp")
    agentId: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict, exclude=True)

    @computed_field
    @property
    def title(self) -> Optional[str]:
        return {
            RunEventType.ORCHESTRATOR_PLAN: "Research plan ready",
            RunEventType.RUN_COMPLETE: "Run complete",
        }.get(self.type)

    @computed_field
    @property
    def text(self) -> str:
        p = self.payload or {}
        t = self.type
        if t == RunEventType.ORCHESTRATOR_PLAN:
            roles = ", ".join(_display_name(r) for r in p.get("roles", []))
            return f"Planned {p.get('agentCount', 0)} research agents: {roles}." if roles else "Research plan ready."
        if t == RunEventType.AGENT_SPAWNED:
            return f"{_display_name(p.get('role', ''))} joined the run."
        if t in (RunEventType.AGENT_FINDING, RunEventType.AGENT_MESSAGE):
            return p.get("text") or p.get("message") or "New finding."
        if t == RunEventType.REPORT_SEGMENT_READY:
            sub = p.get("subtitle") or ""
            return f"Segment ready: {sub}" if sub else "A presentation segment is ready."
        if t == RunEventType.RUN_COMPLETE:
            return f"Research complete. {p.get('opportunityCount', 0)} opportunities scored."
        return p.get("text", "")


class TranscriptWord(BaseModel):
    text: str
    startMs: int
    endMs: int


class PresentationSegment(BaseModel):
    id: str = Field(default_factory=lambda: f"seg-{uuid4().hex[:8]}")
    agentId: str
    script: str
    subtitle: str
    audioUrl: Optional[str] = None
    wordTimings: list[TranscriptWord] = Field(default_factory=list)
    imageUrl: Optional[str] = None
    evidenceIds: list[str] = Field(default_factory=list)
    durationMs: Optional[int] = None

    @computed_field
    @property
    def title(self) -> str:
        return _display_name(self.agentId.split("-", 2)[-1] if "-" in self.agentId else self.agentId)


class TranscriptSegment(BaseModel):
    agentId: str
    script: str
    subtitle: str
    audioUrl: Optional[str] = None
    durationMs: int
    timingSource: str = "estimated"
    wordTimings: list[TranscriptWord] = Field(default_factory=list)


class ReportTranscript(BaseModel):
    runId: str
    query: str
    segments: list[TranscriptSegment] = Field(default_factory=list)


class Report(BaseModel):
    """Final report. Serializes as the frontend `FinalReport` (adds `id`,
    `title`, `executiveSummary`)."""

    runId: str
    query: str = Field(exclude=True)  # internal; frontend FinalReport has no query
    createdAt: datetime = Field(default_factory=_now)
    opportunities: list[Opportunity] = Field(default_factory=list)
    segments: list[PresentationSegment] = Field(default_factory=list)

    @computed_field
    @property
    def id(self) -> str:
        return f"report-{self.runId}"

    @computed_field
    @property
    def title(self) -> str:
        return _report_title(self.query, self.opportunities)

    @computed_field
    @property
    def executiveSummary(self) -> str:
        return _executive_summary(self.opportunities)


class Run(BaseModel):
    runId: str = Field(serialization_alias="id")  # frontend expects `id`
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


class TopOpportunity(BaseModel):
    id: str
    startupName: str
    goliathScore: float
    status: OpportunityStatus


class ReportSummary(BaseModel):
    runId: str
    title: str
    query: str
    status: RunStatus
    createdAt: datetime
    opportunityCount: int
    topOpportunities: list[TopOpportunity] = Field(default_factory=list)
