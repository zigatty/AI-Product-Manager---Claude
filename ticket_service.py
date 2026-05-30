import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import ticket_agent
from backend.db.models import Opportunity, PRD, Ticket


async def generate(db: AsyncSession, prd_id: uuid.UUID) -> list[Ticket]:
    """Run Ticket Agent against a PRD and persist the resulting tickets.

    Args:
        db:     Async DB session.
        prd_id: UUID of the source PRD.

    Returns:
        List of persisted Ticket instances, P1-first.

    Raises:
        ValueError: If the PRD or its opportunity cannot be found.
    """
    # ── 1. Load PRD ───────────────────────────────────────────────────────────
    prd_result = await db.execute(select(PRD).where(PRD.id == prd_id))
    prd = prd_result.scalar_one_or_none()
    if not prd:
        raise ValueError(f"PRD {prd_id} not found")

    # ── 2. Load parent opportunity for context ────────────────────────────────
    opp_result = await db.execute(
        select(Opportunity).where(Opportunity.id == prd.opportunity_id)
    )
    opp = opp_result.scalar_one_or_none()
    if not opp:
        raise ValueError(f"Opportunity {prd.opportunity_id} not found")

    # ── 3. Build payloads ─────────────────────────────────────────────────────
    prd_payload = {
        "problem": prd.problem,
        "users_affected": prd.users_affected,
        "solution": prd.solution,
        "acceptance_criteria": prd.acceptance_criteria,
        "metrics": prd.metrics,
        "priority": opp.priority,
    }
    opp_payload = {
        "title": opp.title,
        "priority": opp.priority,
        "customer_impact": opp.customer_impact,
        "business_impact": opp.business_impact,
        "effort": opp.effort,
    }

    # ── 4. Run agent ──────────────────────────────────────────────────────────
    agent_output = ticket_agent.run(prd_payload, opp_payload)

    # ── 5. Persist tickets ────────────────────────────────────────────────────
    saved = []
    for t in agent_output.get("tickets", []):
        ticket = Ticket(
            prd_id=prd.id,
            title=t["title"],
            description=t["description"],
            priority=t["priority"],
            estimate=t["estimate"],
            status="open",
        )
        db.add(ticket)
        saved.append(ticket)

    await db.flush()
    return saved


async def get(db: AsyncSession, ticket_id: uuid.UUID) -> Ticket | None:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    return result.scalar_one_or_none()


async def list_all(db: AsyncSession, prd_id: uuid.UUID | None = None) -> list[Ticket]:
    query = select(Ticket)
    if prd_id:
        query = query.where(Ticket.prd_id == prd_id)
    query = query.order_by(Ticket.priority, Ticket.created_at)
    result = await db.execute(query)
    return result.scalars().all()


async def update_status(db: AsyncSession, ticket_id: uuid.UUID, status: str) -> Ticket:
    ticket = await get(db, ticket_id)
    if not ticket:
        raise ValueError(f"Ticket {ticket_id} not found")
    ticket.status = status
    await db.flush()
    return ticket
