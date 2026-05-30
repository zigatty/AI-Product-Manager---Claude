import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import prd_agent
from backend.db.models import FeedbackCluster, Opportunity, PRD


async def generate(db: AsyncSession, opportunity_id: uuid.UUID) -> PRD:
    """Generate and persist a PRD for the given opportunity.

    Args:
        db:               Async DB session.
        opportunity_id:   UUID of the target opportunity.

    Returns:
        The persisted PRD model instance.

    Raises:
        ValueError: If the opportunity or its cluster cannot be found.
    """
    # ── 1. Load opportunity ───────────────────────────────────────────────────
    opp_result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opp = opp_result.scalar_one_or_none()
    if not opp:
        raise ValueError(f"Opportunity {opportunity_id} not found")

    # ── 2. Load parent cluster for evidence + context ─────────────────────────
    cluster_result = await db.execute(
        select(FeedbackCluster).where(FeedbackCluster.id == opp.cluster_id)
    )
    cluster = cluster_result.scalar_one_or_none()
    if not cluster:
        raise ValueError(f"Cluster {opp.cluster_id} not found")

    # ── 3. Run PRD agent ──────────────────────────────────────────────────────
    opportunity_payload = {
        "title": opp.title,
        "priority": opp.priority,
        "customer_impact": opp.customer_impact,
        "business_impact": opp.business_impact,
        "effort": opp.effort,
        "rationale": opp.rationale,
    }
    cluster_payload = {
        "theme": cluster.theme,
        "summary": cluster.summary,
        "evidence": cluster.evidence,
        "frequency_score": cluster.frequency_score,
    }

    markdown = prd_agent.run(opportunity_payload, cluster_payload)

    # ── 4. Parse markdown into structured fields ──────────────────────────────
    parsed = prd_agent.parse(markdown)

    # ── 5. Persist ────────────────────────────────────────────────────────────
    prd = PRD(
        opportunity_id=opp.id,
        problem=parsed["problem"],
        users_affected=parsed["users_affected"],
        solution=parsed["solution"],
        acceptance_criteria=parsed["acceptance_criteria"],
        metrics=parsed["metrics"],
        markdown_content=markdown,
        status="draft",
    )
    db.add(prd)
    await db.flush()

    return prd


async def get(db: AsyncSession, prd_id: uuid.UUID) -> PRD | None:
    result = await db.execute(select(PRD).where(PRD.id == prd_id))
    return result.scalar_one_or_none()


async def list_all(db: AsyncSession) -> list[PRD]:
    result = await db.execute(select(PRD).order_by(PRD.created_at.desc()))
    return result.scalars().all()


async def update_status(db: AsyncSession, prd_id: uuid.UUID, status: str) -> PRD:
    prd = await get(db, prd_id)
    if not prd:
        raise ValueError(f"PRD {prd_id} not found")
    prd.status = status
    await db.flush()
    return prd
