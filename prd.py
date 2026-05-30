import uuid

from backend.db.models import PRD
from mcp_servers.db import get_session


def create_prd(
    opportunity_id: str,
    problem: str,
    solution: str,
    acceptance_criteria: list[str],
    metrics: list[str],
) -> dict:
    with get_session() as db:
        item = PRD(
            opportunity_id=uuid.UUID(opportunity_id),
            problem=problem,
            solution=solution,
            acceptance_criteria=acceptance_criteria,
            metrics=metrics,
            status="draft",
        )
        db.add(item)
        db.flush()
        return {
            "id": str(item.id),
            "opportunity_id": str(item.opportunity_id),
            "problem": item.problem,
            "solution": item.solution,
            "acceptance_criteria": item.acceptance_criteria,
            "metrics": item.metrics,
            "status": item.status,
            "created_at": str(item.created_at),
        }
