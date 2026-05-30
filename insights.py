from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import (
    APIResponse,
    ClusterRead,
    OpportunityRead,
    PrioritizeRequest,
    PrioritizeResult,
)
from backend.db.database import get_db
from backend.db.models import FeedbackCluster, Opportunity
from backend.services import prioritization_service

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("", response_model=APIResponse)
async def list_insights(db: AsyncSession = Depends(get_db)):
    """Summary view: all clusters and their ranked opportunities."""
    clusters = await db.execute(
        select(FeedbackCluster).order_by(FeedbackCluster.frequency_score.desc())
    )
    opportunities = await db.execute(
        select(Opportunity).order_by(Opportunity.priority, Opportunity.composite_score.desc())
    )
    return APIResponse(
        status="success",
        data={
            "clusters": [ClusterRead.model_validate(c) for c in clusters.scalars().all()],
            "opportunities": [OpportunityRead.model_validate(o) for o in opportunities.scalars().all()],
        },
    )


@router.post("/prioritize", response_model=APIResponse)
async def prioritize_opportunities(
    payload: PrioritizeRequest = PrioritizeRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Run Prioritization Agent: score clusters on impact + effort, assign P1/P2/P3."""
    try:
        result = await prioritization_service.prioritize(
            db=db,
            cluster_ids=payload.cluster_ids,
            force=payload.force,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return APIResponse(
        status="success",
        data=PrioritizeResult(**result),
        message=f"Scored {result['total_scored']} opportunities",
    )


@router.get("/opportunities", response_model=APIResponse)
async def list_opportunities(db: AsyncSession = Depends(get_db)):
    """Return all opportunities ranked by priority then composite score."""
    opps = await prioritization_service.get_ranked_opportunities(db)
    return APIResponse(
        status="success",
        data=[OpportunityRead.model_validate(o) for o in opps],
    )


@router.get("/opportunities/{opportunity_id}", response_model=APIResponse)
async def get_opportunity(opportunity_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return APIResponse(status="success", data=OpportunityRead.model_validate(opp))
