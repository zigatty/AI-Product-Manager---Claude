import json
import pathlib
import re

import anthropic

from backend.config import settings

_PROMPT_PATH = pathlib.Path(__file__).parent.parent.parent / "agents" / "prioritization_agent.md"

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text.strip())
    return json.loads(text)


def run(clusters: list[dict]) -> dict:
    """Score and rank feedback clusters into prioritized opportunities.

    Args:
        clusters: List of dicts with keys:
                  cluster_id, theme, summary, evidence, frequency_score, feedback_count.

    Returns:
        {
            "opportunities": [
                {
                    "cluster_id": str,
                    "title": str,
                    "customer_impact": float,   # 0–10
                    "business_impact": float,   # 0–10
                    "effort": float,            # 0–10  (10 = hardest)
                    "rationale": str
                }
            ]
        }
    """
    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    user_message = f"""Score and rank the following {len(clusters)} feedback clusters as product opportunities.

Clusters:
{json.dumps(clusters, indent=2)}

Scoring guide:
- customer_impact (0–10): How severely does this affect users? 10 = blocks core workflow.
- business_impact (0–10): Revenue, retention, acquisition, or strategic value. 10 = critical.
- effort (0–10): Engineering complexity and time. 10 = multi-quarter, 1 = hours.

Return ONLY valid JSON — no prose, no markdown — using exactly this structure:
{{
  "opportunities": [
    {{
      "cluster_id": "<uuid>",
      "title": "action-oriented title (e.g. Fix OAuth login flow)",
      "customer_impact": 0.0,
      "business_impact": 0.0,
      "effort": 0.0,
      "rationale": "one or two sentences explaining why this score"
    }}
  ]
}}

Rules:
- Every cluster_id must appear exactly once.
- Scores are floats between 0.0 and 10.0.
- title must be specific and actionable, not a restatement of the theme.
- rationale must reference frequency_score and concrete evidence.
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

    return _parse_json(response.content[0].text)
