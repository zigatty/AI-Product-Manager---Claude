from datetime import datetime

from backend.db.models import Feedback
from mcp_servers.db import get_session


def store_feedback(source: str, text: str, metadata: dict | None = None) -> dict:
    with get_session() as db:
        item = Feedback(
            source=source,
            raw_text=text,
            submitted_at=datetime.utcnow(),
            metadata_=metadata or {},
        )
        db.add(item)
        db.flush()
        return {
            "id": str(item.id),
            "source": item.source,
            "raw_text": item.raw_text,
            "created_at": str(item.created_at),
        }


def search_feedback(query: str, limit: int = 10) -> list[dict]:
    with get_session() as db:
        results = (
            db.query(Feedback)
            .filter(Feedback.raw_text.ilike(f"%{query}%"))
            .order_by(Feedback.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": str(r.id),
                "source": r.source,
                "raw_text": r.raw_text,
                "submitted_at": str(r.submitted_at),
            }
            for r in results
        ]
