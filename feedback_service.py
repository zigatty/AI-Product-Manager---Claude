import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import feedback_agent
from backend.db.models import Feedback, FeedbackCluster


async def ingest(
    db: AsyncSession,
    source: str,
    raw_text: str,
    submitted_at: datetime | None,
    metadata: dict,
) -> Feedback:
    item = Feedback(
        source=source,
        raw_text=raw_text,
        submitted_at=submitted_at or datetime.utcnow(),
        metadata_=metadata,
    )
    db.add(item)
    await db.flush()
    return item


async def analyze(
    db: AsyncSession,
    feedback_ids: list[uuid.UUID] | None = None,
) -> dict:
    """Run the Feedback Agent over stored items and persist clusters.

    Args:
        db:           Async DB session.
        feedback_ids: Restrict analysis to these IDs; None means all.

    Returns:
        {
            clusters: [...],
            duplicates: [...],
            total_feedback: int,
            clusters_found: int,
        }
    """
    # ── 1. Fetch feedback ─────────────────────────────────────────────────────
    query = select(Feedback).order_by(Feedback.submitted_at)
    if feedback_ids:
        query = query.where(Feedback.id.in_(feedback_ids))

    result = await db.execute(query)
    items = result.scalars().all()

    if not items:
        return {"clusters": [], "duplicates": [], "total_feedback": 0, "clusters_found": 0}

    # ── 2. Prepare payload for Claude ─────────────────────────────────────────
    payload = [
        {
            "id": str(f.id),
            "source": f.source,
            "text": f.raw_text,
            "submitted_at": f.submitted_at.isoformat() if f.submitted_at else None,
        }
        for f in items
    ]

    # ── 3. Run agent ──────────────────────────────────────────────────────────
    agent_output = feedback_agent.run(payload)

    # ── 4. Persist clusters ───────────────────────────────────────────────────
    saved_clusters = []
    for c in agent_output.get("clusters", []):
        cluster = FeedbackCluster(
            theme=c["theme"],
            frequency_score=c.get("frequency_score", 0.0),
            summary=c["summary"],
            evidence=c.get("evidence", []),
        )
        db.add(cluster)
        saved_clusters.append((cluster, c.get("feedback_ids", [])))

    await db.flush()

    return {
        "clusters": [
            {
                "id": str(cl.id),
                "theme": cl.theme,
                "summary": cl.summary,
                "evidence": cl.evidence,
                "frequency_score": cl.frequency_score,
                "feedback_count": len(ids),
                "feedback_ids": ids,
            }
            for cl, ids in saved_clusters
        ],
        "duplicates": agent_output.get("duplicates", []),
        "total_feedback": len(items),
        "clusters_found": len(saved_clusters),
    }


async def get_clusters(db: AsyncSession) -> list[FeedbackCluster]:
    result = await db.execute(
        select(FeedbackCluster).order_by(FeedbackCluster.frequency_score.desc())
    )
    return result.scalars().all()
