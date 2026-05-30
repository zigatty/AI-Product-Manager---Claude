from mcp.server.fastmcp import FastMCP

from mcp_servers.tools.feedback import search_feedback as _search, store_feedback as _store
from mcp_servers.tools.prd import create_prd as _create_prd
from mcp_servers.tools.tickets import create_ticket as _create_ticket, list_tickets as _list_tickets

mcp = FastMCP("AI Product Manager")


@mcp.tool()
def store_feedback(source: str, text: str, metadata: dict | None = None) -> dict:
    """Store a piece of raw customer feedback.

    Args:
        source:   Where the feedback came from (e.g. 'intercom', 'csv', 'manual').
        text:     The raw feedback text.
        metadata: Optional key/value pairs (user_id, plan, channel, etc.).

    Returns:
        The created feedback record with its assigned id.
    """
    return _store(source, text, metadata)


@mcp.tool()
def search_feedback(query: str, limit: int = 10) -> list[dict]:
    """Search stored customer feedback by keyword.

    Args:
        query: Keyword or phrase to search for (case-insensitive).
        limit: Maximum number of results to return (default 10).

    Returns:
        List of matching feedback records.
    """
    return _search(query, limit)


@mcp.tool()
def create_prd(
    opportunity_id: str,
    problem: str,
    solution: str,
    acceptance_criteria: list[str],
    metrics: list[str],
) -> dict:
    """Create a Product Requirements Document linked to an opportunity.

    Args:
        opportunity_id:      UUID of the parent opportunity.
        problem:             Clear problem statement.
        solution:            Proposed solution description.
        acceptance_criteria: List of conditions that define done.
        metrics:             List of success metrics to track.

    Returns:
        The created PRD record.
    """
    return _create_prd(opportunity_id, problem, solution, acceptance_criteria, metrics)


@mcp.tool()
def create_ticket(
    prd_id: str,
    title: str,
    description: str,
    priority: str,
    estimate: str,
) -> dict:
    """Create an engineering ticket linked to a PRD.

    Args:
        prd_id:      UUID of the parent PRD.
        title:       Short ticket title.
        description: Full ticket description with context and requirements.
        priority:    P1, P2, or P3.
        estimate:    Time estimate (e.g. '2 days', '1 week').

    Returns:
        The created ticket record.
    """
    return _create_ticket(prd_id, title, description, priority, estimate)


@mcp.tool()
def list_tickets(prd_id: str | None = None, status: str | None = None, limit: int = 20) -> list[dict]:
    """List engineering tickets with optional filters.

    Args:
        prd_id: Filter by parent PRD UUID (optional).
        status: Filter by status — 'open', 'in_progress', or 'done' (optional).
        limit:  Maximum number of results (default 20).

    Returns:
        List of matching ticket records.
    """
    return _list_tickets(prd_id, status, limit)


if __name__ == "__main__":
    mcp.run()
