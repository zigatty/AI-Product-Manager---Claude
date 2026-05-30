import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import prioritization_agent
from backend.db.models import FeedbackCluster, Opportunity

# ── Scoring ───────────────────────────────────────────────────────────────────
# composite = weighted sum of impact scores, discounted by effort
# frequency contributes 20 %, customer impact 35 %, business impact 35 %,
# then the whole thing is divided by effort so hard items rank lower.

_WEIGHT_CUSTOMER = 0.35
_WEIGHT_BUSINESS = 0.35
_WEIGHT_FREQUENCY = 0.30   # frequency_score is 0–1; scaled to 0–10 below

_P1_THRESHOLD = 5.5
_P2_THRESHOLD = 3.0


def _composite(customer: float, business: float, effort: float, frequency: float) -> float:
    raw = (
        customer * _WEIGHT_CUSTOMER
        + business * _WEIGHT_BUSINESS
        + (frequency * 10) * _WEIGHT_FREQUENCY
    )
    return round(raw / max(effort, 1.0), 3)


def _priority(score: float) -> str:
    if score >= _P1_THRESHOLD:
        return "P1"
    if score >= _P2_THRESHOLD:
        return "P2"
    return "P3"


# ── Service ───────────────────────────────────────────────────────────────────

async def prioritize(
    db: AsyncSession,
    cluster_ids: list[uuid.UUID] | None = None,
    force: bool = False,
) -> dict:
    """Run Prioritization Agent over clusters and persist opportunities.

    Args:
        db:          Async DB session.
        cluster_ids: Restrict to these cluster IDs; None means all.
        force:       Re-score clusters that already have opportunities.

    Returns:
        { opportunities: [...], total_scored: int }
    """
    # ── 1. Fetch clusters ─────────────────────────────────────────────────────
    query = select(FeedbackCluster).order_by(FeedbackCluster.frequency_score.desc())
    if cluster_ids:
        query = query.where(FeedbackCluster.id.in_(cluster_ids))

    result = await db.execute(query)
    clusters = result.scalars().all()

    if not clusters:
        return {"opportunities": [], "total_scored": 0}

    # ── 2. Skip already-scored clusters unless force=True ─────────────────────
    if not force:
        scored_ids = set()
        opp_result = await db.execute(select(Opportunity.cluster_id))
        for row in opp_result.scalars().all():
            scored_ids.add(row)
        clusters = [c for c in clusters if c.id not in scored_ids]

    if not clusters:
        return {"opportunities": [], "total_scored": 0, "message": "All clusters already scored. Use force=true to re-score."}

    # ── 3. Build payload for Claude ───────────────────────────────────────────
    payload = [
        {
            "cluster_id": str(c.id),
            "theme": c.theme,
            "summary": c.summary,
            "evidence": c.evidence,
            "frequency_score": c.frequency_score,
        }
        for c in clusters
    ]

    # ── 4. Run agent ──────────────────────────────────────────────────────────
    agent_output = prioritization_agent.run(payload)

    # ── 5. Build cluster lookup for frequency scores ──────────────────────────
    cluster_map = {str(c.id): c for c in clusters}

    # ── 6. Compute scores, assign priority, persist ───────────────────────────
    saved = []
    for item in agent_output.get("opportunities", []):
        cid = item["cluster_id"]
        cluster = cluster_map.get(cid)
        if not cluster:
            continue

        composite = _composite(
            customer=item["customer_impact"],
            business=item["business_impact"],
            effort=item["effort"],
            frequency=cluster.frequency_score,
        )

        opp = Opportunity(
            cluster_id=cluster.id,
            title=item["title"],
            customer_impact=item["customer_impact"],
            business_impact=item["business_impact"],
            effort=item["effort"],
            composite_score=composite,
            priority=_priority(composite),
            rationale=item.get("rationale"),
            status="new",
        )
        db.add(opp)
        saved.append(opp)

    await db.flush()

    # ── 7. Sort output: P1 first, then by composite score desc ───────────────
    priority_order = {"P1": 0, "P2": 1, "P3": 2}
    saved.sort(key=lambda o: (priority_order[o.priority], -o.composite_score))

    return {
        "opportunities": [_serialize(o) for o in saved],
        "total_scored": len(saved),
    }


async def get_ranked_opportunities(db: AsyncSession) -> list[Opportunity]:
    result = await db.execute(
        select(Opportunity).order_by(Opportunity.priority, Opportunity.composite_score.desc())
    )
    return result.scalars().all()


def _serialize(o: Opportunity) -> dict:
    return {
        "id": str(o.id),
        "cluster_id": str(o.cluster_id),
        "title": o.title,
        "customer_impact": o.customer_impact,
        "business_impact": o.business_impact,
        "effort": o.effort,
        "composite_score": o.composite_score,
        "priority": o.priority,
        "rationale": o.rationale,
        "status": o.status,
    }
