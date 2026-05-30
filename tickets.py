import uuid

from backend.db.models import Ticket
from mcp_servers.db import get_session


def create_ticket(
    prd_id: str,
    title: str,
    description: str,
    priority: str,
    estimate: str,
) -> dict:
    with get_session() as db:
        item = Ticket(
            prd_id=uuid.UUID(prd_id),
            title=title,
            description=description,
            priority=priority,
            estimate=estimate,
            status="open",
        )
        db.add(item)
        db.flush()
        return {
            "id": str(item.id),
            "prd_id": str(item.prd_id),
            "title": item.title,
            "description": item.description,
            "priority": item.priority,
            "estimate": item.estimate,
            "status": item.status,
            "created_at": str(item.created_at),
        }


def list_tickets(prd_id: str | None = None, status: str | None = None, limit: int = 20) -> list[dict]:
    with get_session() as db:
        q = db.query(Ticket)
        if prd_id:
            q = q.filter(Ticket.prd_id == uuid.UUID(prd_id))
        if status:
            q = q.filter(Ticket.status == status)
        items = q.order_by(Ticket.created_at.desc()).limit(limit).all()
        return [
            {
                "id": str(t.id),
                "prd_id": str(t.prd_id),
                "title": t.title,
                "description": t.description,
                "priority": t.priority,
                "estimate": t.estimate,
                "status": t.status,
                "created_at": str(t.created_at),
            }
            for t in items
        ]
