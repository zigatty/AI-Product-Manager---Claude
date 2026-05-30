from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import (
    APIResponse,
    PipelineConfig,
    PipelineRunResultSchema,
    StageResultSchema,
)
from backend.db.database import get_db
from backend.db.models import Feedback, FeedbackCluster, Opportunity, PRD, Ticket
from backend.services import manager_service

router = APIRouter(prefix="/pipeline", tags=["Manager"])


@router.post("/run", response_model=APIResponse)
async def run_pipeline(
    config: PipelineConfig = PipelineConfig(),
    db: AsyncSession = Depends(get_db),
):
    """Run the full agent pipeline: Feedback → Prioritization → PRD → Tickets.

    Stages execute sequentially. If a stage fails, later stages are skipped
    and the run returns with status='partial'. Per-stage errors are collected
    without aborting the whole run where possible (e.g. one failed PRD does
    not prevent other PRDs from generating).
    """
    try:
        result = await manager_service.run_pipeline(
            db=db,
            feedback_ids=config.feedback_ids,
            prd_priorities=config.prd_priorities,
            force=config.force,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    result_dict = result.to_dict()

    return APIResponse(
        status="success",
        data=PipelineRunResultSchema(
            status=result_dict["status"],
            stages={
                k: StageResultSchema(**v)
                for k, v in result_dict["stages"].items()
            },
            summary=result_dict["summary"],
            errors=result_dict["errors"],
            strategic_summary=result_dict["strategic_summary"],
            total_duration_seconds=result_dict["total_duration_seconds"],
        ),
        message=_run_message(result_dict),
    )


@router.get("/status", response_model=APIResponse)
async def pipeline_status(db: AsyncSession = Depends(get_db)):
    """Return counts for each stage — a snapshot of the current pipeline state."""
    feedback_count  = await db.scalar(select(func.count()).select_from(Feedback)) or 0
    cluster_count   = await db.scalar(select(func.count()).select_from(FeedbackCluster)) or 0
    opp_count       = await db.scalar(select(func.count()).select_from(Opportunity)) or 0
    prd_count       = await db.scalar(select(func.count()).select_from(PRD)) or 0
    ticket_count    = await db.scalar(select(func.count()).select_from(Ticket)) or 0

    return APIResponse(
        status="success",
        data={
            "feedback_items": feedback_count,
            "clusters": cluster_count,
            "opportunities": opp_count,
            "prds": prd_count,
            "tickets": ticket_count,
        },
    )


def _run_message(result: dict) -> str:
    s = result["summary"]
    status = result["status"]
    return (
        f"Pipeline {status}: "
        f"{s.get('clusters_found', 0)} clusters, "
        f"{s.get('opportunities_ranked', 0)} opportunities, "
        f"{s.get('prds_generated', 0)} PRDs, "
        f"{s.get('tickets_created', 0)} tickets "
        f"({result['total_duration_seconds']:.1f}s)"
    )
