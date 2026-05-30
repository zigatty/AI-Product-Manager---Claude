import json
import pathlib
import re

import anthropic

from backend.config import settings

_PROMPT_PATH = pathlib.Path(__file__).parent.parent.parent / "agents" / "feedback_agent.md"

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _parse_json(text: str) -> dict:
    """Strip markdown fences then parse JSON."""
    text = re.sub(r"^```(?:json)?\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text.strip())
    return json.loads(text)


def run(feedback_items: list[dict]) -> dict:
    """Cluster feedback items and detect duplicates via Claude.

    Args:
        feedback_items: List of dicts with keys: id, source, text, submitted_at.

    Returns:
        {
            "clusters": [
                {
                    "theme": str,
                    "summary": str,
                    "evidence": [str, ...],
                    "frequency_score": float,
                    "feedback_ids": [str, ...]
                }
            ],
            "duplicates": [str, ...]   # feedback IDs that are near-duplicates
        }
    """
    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    user_message = f"""Analyze the following {len(feedback_items)} customer feedback items.

Feedback:
{json.dumps(feedback_items, indent=2)}

Return ONLY valid JSON — no prose, no markdown — using exactly this structure:
{{
  "clusters": [
    {{
      "theme": "short theme label",
      "summary": "one-sentence description of the grouped issue",
      "evidence": ["verbatim quote 1", "verbatim quote 2"],
      "frequency_score": 0.0,
      "feedback_ids": ["<uuid>", ...]
    }}
  ],
  "duplicates": ["<uuid of near-duplicate item>", ...]
}}

Rules:
- Group semantically similar feedback into the same cluster even if the wording differs.
- frequency_score = items in this cluster / total items (0.0 – 1.0).
- evidence must be direct quotes from the raw feedback text, max 3 per cluster.
- A duplicate is a feedback item whose meaning is already fully represented by another item in the same cluster. Keep one representative; mark the rest as duplicates.
- Every feedback ID must appear in exactly one cluster or in the duplicates list.
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
