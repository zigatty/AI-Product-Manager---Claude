import json

import anthropic

from backend.config import settings

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def summarize(pipeline_result: dict) -> str:
    """Generate a strategic summary of a completed pipeline run.

    Args:
        pipeline_result: The full serialised PipelineRunResult dict.

    Returns:
        A concise markdown strategic summary.
    """
    stages = pipeline_result.get("stages", {})
    summary = pipeline_result.get("summary", {})
    errors = pipeline_result.get("errors", [])

    feedback_stage = stages.get("feedback", {}).get("output", {})
    prio_stage = stages.get("prioritization", {}).get("output", {})
    prd_stage = stages.get("prd", {}).get("output", {})
    ticket_stage = stages.get("tickets", {}).get("output", {})

    prompt = f"""You are a senior product manager reviewing an automated analysis pipeline.

## Pipeline Summary
- Feedback items analysed: {summary.get('total_feedback', 0)}
- Clusters found:          {summary.get('clusters_found', 0)}
- Opportunities ranked:    {summary.get('opportunities_ranked', 0)}
- PRDs generated:          {summary.get('prds_generated', 0)}
- Tickets created:         {summary.get('tickets_created', 0)}
- Errors:                  {len(errors)}

## Top Clusters
{json.dumps(feedback_stage.get('clusters', [])[:5], indent=2)}

## Ranked Opportunities
{json.dumps(prio_stage.get('opportunities', [])[:5], indent=2)}

## PRDs Generated
{json.dumps(prd_stage.get('prd_titles', []), indent=2)}

## Errors (if any)
{json.dumps(errors, indent=2)}

Write a concise strategic summary in this exact markdown format:

## What We Found
[2–3 sentences on the most important customer issues uncovered.]

## Top Opportunities
[Bullet list of the top 3 ranked opportunities with their priority and one-line rationale.]

## Actions Taken
[Bullet list summarising what was generated: clusters, PRDs, ticket counts.]

## Recommended Next Steps
[Bullet list of 2–3 concrete next actions for the team.]

Be direct and specific. No filler. Reference actual themes and opportunity titles from the data.
"""

    response = _client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()
