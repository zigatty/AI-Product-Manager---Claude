import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(Text)
    raw_text: Mapped[str] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FeedbackCluster(Base):
    __tablename__ = "feedback_clusters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    theme: Mapped[str] = mapped_column(Text)
    frequency_score: Mapped[float] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="cluster")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("feedback_clusters.id"))
    title: Mapped[str] = mapped_column(Text)
    customer_impact: Mapped[float] = mapped_column(Float)
    business_impact: Mapped[float] = mapped_column(Float)
    effort: Mapped[float] = mapped_column(Float)
    composite_score: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[str] = mapped_column(String(10))
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cluster: Mapped["FeedbackCluster"] = relationship(back_populates="opportunities")
    prds: Mapped[list["PRD"]] = relationship(back_populates="opportunity")


class PRD(Base):
    __tablename__ = "prds"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("opportunities.id"))
    problem: Mapped[str] = mapped_column(Text)
    users_affected: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution: Mapped[str] = mapped_column(Text)
    acceptance_criteria: Mapped[list] = mapped_column(JSON, default=list)
    metrics: Mapped[list] = mapped_column(JSON, default=list)
    markdown_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    opportunity: Mapped["Opportunity"] = relationship(back_populates="prds")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="prd")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prd_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("prds.id"))
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10))
    estimate: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prd: Mapped["PRD"] = relationship(back_populates="tickets")
