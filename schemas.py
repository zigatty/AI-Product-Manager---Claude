import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ── Shared ────────────────────────────────────────────────────────────────────

class APIResponse(BaseModel):
    status: str
    data: Any = None
    message: str = ""


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    source: str
    raw_text: str
    submitted_at: datetime | None = None
    metadata_: dict = {}


class FeedbackRead(BaseModel):
    id: uuid.UUID
    source: str
    raw_text: str
    submitted_at: datetime
    metadata_: dict
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Feedback Analysis ─────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    feedback_ids: list[uuid.UUID] | None = None  # None = analyze all


class ClusterResult(BaseModel):
    id: str
    theme: str
    summary: str
    evidence: list[str]
    frequency_score: float
    feedback_count: int
    feedback_ids: list[str]


class AnalyzeResult(BaseModel):
    clusters: list[ClusterResult]
    duplicates: list[str]
    total_feedback: int
    clusters_found: int


# ── Feedback Clusters ─────────────────────────────────────────────────────────

class ClusterRead(BaseModel):
    id: uuid.UUID
    theme: str
    frequency_score: float
    summary: str
    evidence: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Opportunities ─────────────────────────────────────────────────────────────

class PrioritizeRequest(BaseModel):
    cluster_ids: list[uuid.UUID] | None = None  # None = score all clusters
    force: bool = False                         # re-score already-scored clusters


class OpportunityResult(BaseModel):
    id: str
    cluster_id: str
    title: str
    customer_impact: float
    business_impact: float
    effort: float
    composite_score: float
    priority: str
    rationale: str | None
    status: str


class PrioritizeResult(BaseModel):
    opportunities: list[OpportunityResult]
    total_scored: int


class OpportunityRead(BaseModel):
    id: uuid.UUID
    cluster_id: uuid.UUID
    title: str
    customer_impact: float
    business_impact: float
    effort: float
    composite_score: float
    priority: str
    rationale: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── PRD ───────────────────────────────────────────────────────────────────────

class PRDStatusUpdate(BaseModel):
    status: str  # draft | review | approved


class PRDRead(BaseModel):
    id: uuid.UUID
    opportunity_id: uuid.UUID
    problem: str
    users_affected: str | None = None
    solution: str
    acceptance_criteria: list[str]
    metrics: list[str]
    markdown_content: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Pipeline ─────────────────────────────────────────────────────────────────

class PipelineConfig(BaseModel):
    feedback_ids: list[uuid.UUID] | None = None
    prd_priorities: list[str] = ["P1", "P2"]   # which priorities to generate PRDs for
    force: bool = False                         # re-score clusters that already have opportunities


class StageResultSchema(BaseModel):
    status: str                                 # completed | skipped | failed | partial
    output: dict = {}
    error: str | None = None
    duration_seconds: float = 0.0


class PipelineRunResultSchema(BaseModel):
    status: str                                 # completed | partial | failed
    stages: dict[str, StageResultSchema]
    summary: dict
    errors: list[str]
    strategic_summary: str
    total_duration_seconds: float


# ── Tickets ───────────────────────────────────────────────────────────────────

class TicketStatusUpdate(BaseModel):
    status: str  # open | in_progress | done


class TicketRead(BaseModel):
    id: uuid.UUID
    prd_id: uuid.UUID
    title: str
    description: str
    priority: str
    estimate: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketGenerateResult(BaseModel):
    tickets: list[TicketRead]
    total_created: int
    prd_id: uuid.UUID
