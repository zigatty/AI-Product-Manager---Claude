import time
import uuid
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import manager_agent
from backend.services import feedback_service, prioritization_service, prd_service, ticket_service


# ── Stage result ──────────────────────────────────────────────────────────────

@dataclass
class StageResult:
    status: str                        # completed | skipped | failed
    output: dict = field(default_factory=dict)
    error: str | None = None
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "duration_seconds": round(self.duration_seconds, 2),
        }


# ── Pipeline result ───────────────────────────────────────────────────────────

@dataclass
class PipelineRunResult:
    status: str = "completed"          # completed | partial | failed
    stages: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    strategic_summary: str = ""
    total_duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "stages": {k: v.to_dict() for k, v in self.stages.items()},
            "summary": self.summary,
            "errors": self.errors,
            "strategic_summary": self.strategic_summary,
            "total_duration_seconds": round(self.total_duration_seconds, 2),
        }


# ── Pipeline orchestrator ─────────────────────────────────────────────────────

async def run_pipeline(
    db: AsyncSession,
    feedback_ids: list[uuid.UUID] | None = None,
    prd_priorities: list[str] | None = None,
    force: bool = False,
) -> PipelineRunResult:
    """Coordinate Feedback → Prioritization → PRD → Ticket agents end-to-end.

    Args:
        db:              Async DB session.
        feedback_ids:    Restrict feedback analysis to these IDs; None = all.
        prd_priorities:  Generate PRDs only for these priorities (default: P1, P2).
        force:           Re-score clusters that already have opportunities.

    Returns:
        PipelineRunResult with per-stage output and a strategic summary.
    """
    if prd_priorities is None:
        prd_priorities = ["P1", "P2"]

    result = PipelineRunResult()
    pipeline_start = time.perf_counter()

    # ── Stage 1: Feedback Analysis ────────────────────────────────────────────
    t = time.perf_counter()
    try:
        feedback_out = await feedback_service.analyze(db, feedback_ids=feedback_ids)
        result.stages["feedback"] = StageResult(
            status="completed",
            output=feedback_out,
            duration_seconds=time.perf_counter() - t,
        )
        new_cluster_ids = [
            uuid.UUID(c["id"]) for c in feedback_out.get("clusters", [])
        ]
    except Exception as exc:
        result.stages["feedback"] = StageResult(
            status="failed",
            error=str(exc),
            duration_seconds=time.perf_counter() - t,
        )
        result.status = "partial"
        result.errors.append(f"[feedback] {exc}")
        result.total_duration_seconds = time.perf_counter() - pipeline_start
        return result

    if not new_cluster_ids:
        result.stages["prioritization"] = StageResult(status="skipped", output={"reason": "No clusters produced"})
        result.stages["prd"] = StageResult(status="skipped", output={"reason": "No clusters to prioritize"})
        result.stages["tickets"] = StageResult(status="skipped", output={"reason": "No PRDs to process"})
        result.status = "partial"
        result.total_duration_seconds = time.perf_counter() - pipeline_start
        return result

    # ── Stage 2: Prioritization ───────────────────────────────────────────────
    t = time.perf_counter()
    try:
        prio_out = await prioritization_service.prioritize(
            db, cluster_ids=new_cluster_ids, force=force
        )
        result.stages["prioritization"] = StageResult(
            status="completed",
            output=prio_out,
            duration_seconds=time.perf_counter() - t,
        )
        target_opps = [
            o for o in prio_out.get("opportunities", [])
            if o["priority"] in prd_priorities
        ]
    except Exception as exc:
        result.stages["prioritization"] = StageResult(
            status="failed",
            error=str(exc),
            duration_seconds=time.perf_counter() - t,
        )
        result.status = "partial"
        result.errors.append(f"[prioritization] {exc}")
        result.total_duration_seconds = time.perf_counter() - pipeline_start
        return result

    # ── Stage 3: PRD Generation (per opportunity) ─────────────────────────────
    t = time.perf_counter()
    generated_prds = []
    prd_errors = []

    for opp in target_opps:
        try:
            prd = await prd_service.generate(db, uuid.UUID(opp["id"]))
            generated_prds.append(prd)
        except Exception as exc:
            msg = f"PRD failed for '{opp['title']}': {exc}"
            prd_errors.append(msg)
            result.errors.append(f"[prd] {msg}")

    result.stages["prd"] = StageResult(
        status="completed" if generated_prds else ("failed" if not prd_errors else "partial"),
        output={
            "prds_generated": len(generated_prds),
            "prd_ids": [str(p.id) for p in generated_prds],
            "prd_titles": [p.problem[:80] for p in generated_prds],
            "errors": prd_errors,
        },
        duration_seconds=time.perf_counter() - t,
    )

    # ── Stage 4: Ticket Generation (per PRD) ─────────────────────────────────
    t = time.perf_counter()
    all_tickets = []
    ticket_errors = []

    for prd in generated_prds:
        try:
            tickets = await ticket_service.generate(db, prd.id)
            all_tickets.extend(tickets)
        except Exception as exc:
            msg = f"Tickets failed for PRD {prd.id}: {exc}"
            ticket_errors.append(msg)
            result.errors.append(f"[tickets] {msg}")

    result.stages["tickets"] = StageResult(
        status="completed" if all_tickets else ("failed" if not ticket_errors else "partial"),
        output={
            "tickets_created": len(all_tickets),
            "ticket_ids": [str(t.id) for t in all_tickets],
            "errors": ticket_errors,
        },
        duration_seconds=time.perf_counter() - t,
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    result.summary = {
        "total_feedback": feedback_out.get("total_feedback", 0),
        "clusters_found": feedback_out.get("clusters_found", 0),
        "opportunities_ranked": prio_out.get("total_scored", 0),
        "prds_generated": len(generated_prds),
        "tickets_created": len(all_tickets),
    }

    if result.errors:
        result.status = "partial"

    result.total_duration_seconds = time.perf_counter() - pipeline_start

    # ── Strategic summary (Claude) ────────────────────────────────────────────
    try:
        result.strategic_summary = manager_agent.summarize(result.to_dict())
    except Exception as exc:
        result.errors.append(f"[summary] {exc}")
        result.strategic_summary = "Strategic summary unavailable."

    return result
