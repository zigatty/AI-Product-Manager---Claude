import pathlib
import re

import anthropic

from backend.config import settings

_PROMPT_PATH = pathlib.Path(__file__).parent.parent.parent / "agents" / "prd_agent.md"

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

# ── Markdown template Claude must follow exactly ──────────────────────────────
_TEMPLATE = """\
# Problem
{problem}

# Users Affected
{users_affected}

# Proposed Solution
{solution}

# Acceptance Criteria
{acceptance_criteria}

# Success Metrics
{metrics}"""


def run(opportunity: dict, cluster: dict) -> str:
    """Generate a structured markdown PRD for an opportunity.

    Args:
        opportunity: Dict with keys: title, customer_impact, business_impact,
                     effort, priority, rationale.
        cluster:     Dict with keys: theme, summary, evidence, frequency_score.

    Returns:
        Full PRD as a markdown string.
    """
    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    user_message = f"""Generate a Product Requirements Document for the following opportunity.

## Opportunity
Title:            {opportunity['title']}
Priority:         {opportunity['priority']}
Customer Impact:  {opportunity['customer_impact']}/10
Business Impact:  {opportunity['business_impact']}/10
Effort:           {opportunity['effort']}/10
Rationale:        {opportunity.get('rationale', 'N/A')}

## Supporting Feedback
Theme:            {cluster['theme']}
Summary:          {cluster['summary']}
Frequency:        {round(cluster['frequency_score'] * 100)}% of all feedback
Evidence:
{chr(10).join(f'  - "{e}"' for e in cluster.get('evidence', []))}

## Output Format
Write the PRD using EXACTLY this markdown structure. Do not add extra headings or sections.

# Problem
[2–3 sentences. State the core problem clearly. Do not describe the solution here.]

# Users Affected
[Who experiences this problem. Include user segments, frequency, and severity of impact.]

# Proposed Solution
[Concrete description of what will be built or changed. Be specific about scope.]

# Acceptance Criteria
- [ ] [Testable condition 1]
- [ ] [Testable condition 2]
- [ ] [Testable condition 3]
(add as many as needed)

# Success Metrics
- [Metric name]: [target value and timeframe]
- [Metric name]: [target value and timeframe]
(add as many as needed)
"""

    response = _client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
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

    return response.content[0].text.strip()


# ── Markdown parser ───────────────────────────────────────────────────────────

def parse(markdown: str) -> dict:
    """Extract structured fields from the generated PRD markdown.

    Returns:
        {
            problem: str,
            users_affected: str,
            solution: str,
            acceptance_criteria: list[str],
            metrics: list[str],
        }
    """
    def _section(heading: str) -> str:
        pattern = rf"^#+\s+{re.escape(heading)}\s*\n(.*?)(?=^#+\s|\Z)"
        match = re.search(pattern, markdown, re.MULTILINE | re.DOTALL)
        return match.group(1).strip() if match else ""

    def _bullets(text: str) -> list[str]:
        results = []
        for line in text.splitlines():
            line = line.strip()
            # Matches "- [ ] text", "- text", "* text", "1. text"
            cleaned = re.sub(r"^(-\s*\[.\]\s*|-\s*|\*\s*|\d+\.\s*)", "", line).strip()
            if cleaned:
                results.append(cleaned)
        return results

    return {
        "problem": _section("Problem"),
        "users_affected": _section("Users Affected"),
        "solution": _section("Proposed Solution"),
        "acceptance_criteria": _bullets(_section("Acceptance Criteria")),
        "metrics": _bullets(_section("Success Metrics")),
    }
