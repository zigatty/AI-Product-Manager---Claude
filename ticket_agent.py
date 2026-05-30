import json
import pathlib
import re

import anthropic

from backend.config import settings

_PROMPT_PATH = pathlib.Path(__file__).parent.parent.parent / "agents" / "ticket_agent.md"

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_PRIORITY_ORDER = {"P1": 0, "P2": 1, "P3": 2}


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text.strip())
    return json.loads(text)


def run(prd: dict, opportunity: dict) -> dict:
    """Decompose a PRD into atomic engineering tickets.

    Args:
        prd:         Dict with keys: problem, users_affected, solution,
                     acceptance_criteria (list), metrics (list), priority.
        opportunity: Dict with keys: title, priority, customer_impact,
                     business_impact, effort.

    Returns:
        {
            "tickets": [
                {
                    "title":       str,   # verb-first, ≤ 80 chars
                    "description": str,   # markdown with Context / Task / Acceptance
                    "priority":    str,   # P1 | P2 | P3
                    "estimate":    str,   # e.g. "2 days"
                }
            ]
        }
    """
    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    criteria_block = "\n".join(
        f"  {i + 1}. {c}" for i, c in enumerate(prd.get("acceptance_criteria", []))
    )
    metrics_block = "\n".join(
        f"  - {m}" for m in prd.get("metrics", [])
    )

    user_message = f"""Break down the following PRD into engineering tickets.

## Opportunity
Title:           {opportunity['title']}
Priority:        {opportunity['priority']}
Customer Impact: {opportunity['customer_impact']}/10
Business Impact: {opportunity['business_impact']}/10
Effort:          {opportunity['effort']}/10

## PRD
Problem:
{prd['problem']}

Users Affected:
{prd.get('users_affected', 'N/A')}

Proposed Solution:
{prd['solution']}

Acceptance Criteria:
{criteria_block}

Success Metrics:
{metrics_block}

## Instructions
Create one ticket per acceptance criterion plus any clearly necessary supporting
tasks (e.g. database migrations, test coverage, documentation).

Return ONLY valid JSON — no prose, no markdown — using exactly this structure:
{{
  "tickets": [
    {{
      "title":       "Verb-first title, ≤ 80 chars (e.g. Add OAuth callback error handling)",
      "description": "## Context\\n[Why this exists]\\n\\n## Task\\n[What to build/change — be specific]\\n\\n## Acceptance\\n[The criterion this satisfies]",
      "priority":    "P1 | P2 | P3",
      "estimate":    "e.g. 1 day | 3 days | 1 week | 2 weeks"
    }}
  ]
}}

Rules:
- Each ticket must be independently deliverable by a single engineer.
- title must start with an action verb (Add, Fix, Implement, Migrate, Write, etc.).
- priority inherits from the PRD ({prd['priority']}) unless a ticket is clearly lower risk.
- estimate must be a realistic range — not optimistic, not padded.
- description must use the three-section markdown template shown above.
- Do not create duplicate tickets for the same criterion.
"""

    response = _client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )

    result = _parse_json(response.content[0].text)

    # Sort: P1 first, then by position (preserve Claude's internal ordering per priority)
    result["tickets"].sort(key=lambda t: _PRIORITY_ORDER.get(t.get("priority", "P3"), 2))
    return result
