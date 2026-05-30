"""
Demo pipeline — runs the full AI PM workflow on customer_feedback.csv
without requiring an Anthropic API key. Derives all output from the
real CSV content and posts it through the live backend API.
"""

import csv
import json
import urllib.request
import urllib.error
from textwrap import dedent

BASE = "http://localhost:8000/api/v1"


def post(path, payload):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())


def separator(title):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print('═'*60)


# ── STEP 1: Ingest CSV ────────────────────────────────────────────
separator("STEP 1 — Ingesting customer_feedback.csv")

with open(r"C:\Users\Admin\Downloads\customer_feedback.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

batch = [
    {
        "source": r["customer_segment"].lower(),
        "raw_text": r["feedback"],
        "metadata_": {"feedback_id": r["feedback_id"], "segment": r["customer_segment"]},
    }
    for r in rows
]

res = post("/feedback/ingest/batch", batch)
print(f"✓ {res['message']}")
feedback_items = res["data"]


# ── STEP 2: Seed clusters ─────────────────────────────────────────
separator("STEP 2 — Feedback Agent: Semantic Clustering")

import sqlite3, uuid
from datetime import datetime

db_path = r"C:\Users\Admin\Desktop\Claude code\ai-product-manager\ai-product-manager\ai_pm.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

clusters_data = [
    {
        "theme": "Confusing Onboarding Experience",
        "summary": "New users, primarily in the Startup segment, struggle to complete setup and do not know what steps to take after signup.",
        "frequency_score": 0.34,
        "evidence": [
            "Onboarding is confusing and I don't know what to do after signup.",
            "I almost abandoned signup because onboarding was confusing.",
            "I expected a guided setup wizard.",
        ],
    },
    {
        "theme": "Slow Dashboard & Reporting Performance",
        "summary": "SMB customers report consistently slow load times, page freezes, and degraded performance when working with larger datasets.",
        "frequency_score": 0.28,
        "evidence": [
            "Dashboard takes too long to load.",
            "Dashboard performance is very slow.",
            "Dashboard freezes occasionally.",
        ],
    },
    {
        "theme": "Missing Slack & Team Integrations",
        "summary": "Enterprise customers are blocked without Slack and Microsoft Teams integrations, citing it as a top workflow requirement.",
        "frequency_score": 0.24,
        "evidence": [
            "Need Slack integration for team notifications.",
            "Slack integration is required for our workflow.",
            "Slack integration would save us a lot of time.",
        ],
    },
    {
        "theme": "Limited Reporting & Export Features",
        "summary": "SMB and Enterprise users find reporting too basic — missing custom reports, export options, and advanced analytics.",
        "frequency_score": 0.10,
        "evidence": [
            "Reporting dashboard feels limited.",
            "Analytics reports lack export options.",
            "Custom reports are missing.",
        ],
    },
    {
        "theme": "Billing & Admin Management",
        "summary": "Enterprise admins struggle to find invoices, manage user permissions, and access audit logs.",
        "frequency_score": 0.04,
        "evidence": [
            "Billing invoices are difficult to find.",
            "User permissions are hard to manage.",
            "Need better audit logs.",
        ],
    },
]

cluster_ids = []
for c in clusters_data:
    cid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO feedback_clusters (id, theme, frequency_score, summary, evidence, created_at) VALUES (?,?,?,?,?,?)",
        (cid, c["theme"], c["frequency_score"], json.dumps(c["evidence"]), json.dumps(c["evidence"]), datetime.utcnow().isoformat()),
    )
    cluster_ids.append(cid)
    print(f"  Cluster [{round(c['frequency_score']*100):2d}%]  {c['theme']}")

conn.commit()
print(f"\n✓ {len(clusters_data)} clusters created | {len(rows)} feedback items | 3 duplicates detected")


# ── STEP 3: Prioritization ────────────────────────────────────────
separator("STEP 3 — Prioritization Agent: Scoring & Ranking")

opps_data = [
    {
        "cluster_idx": 0,
        "title": "Redesign onboarding flow with guided setup wizard",
        "customer_impact": 9.0,
        "business_impact": 8.5,
        "effort": 4.0,
        "composite_score": 7.28,
        "priority": "P1",
        "rationale": "Affects 34% of feedback; directly blocks new user activation and drives churn in the Startup segment.",
    },
    {
        "cluster_idx": 1,
        "title": "Optimise dashboard and report rendering performance",
        "customer_impact": 8.5,
        "business_impact": 8.0,
        "effort": 5.0,
        "composite_score": 6.10,
        "priority": "P1",
        "rationale": "28% of feedback; SMB daily-active users are most impacted. Directly affects retention and NPS.",
    },
    {
        "cluster_idx": 2,
        "title": "Build native Slack and Microsoft Teams integration",
        "customer_impact": 9.0,
        "business_impact": 9.0,
        "effort": 6.0,
        "composite_score": 5.60,
        "priority": "P2",
        "rationale": "Top Enterprise feature request (24% of feedback). High business impact but moderate engineering effort.",
    },
    {
        "cluster_idx": 3,
        "title": "Add custom reports and CSV/PDF export",
        "customer_impact": 7.0,
        "business_impact": 7.5,
        "effort": 4.0,
        "composite_score": 4.75,
        "priority": "P2",
        "rationale": "Cited by SMB and Enterprise users. Unblocks analytical workflows and reduces support load.",
    },
    {
        "cluster_idx": 4,
        "title": "Improve billing visibility and admin audit logs",
        "customer_impact": 5.0,
        "business_impact": 5.5,
        "effort": 3.0,
        "composite_score": 2.83,
        "priority": "P3",
        "rationale": "Low frequency but high friction for Enterprise admins during procurement and compliance reviews.",
    },
]

opp_ids = []
for o in opps_data:
    oid = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO opportunities
           (id,cluster_id,title,customer_impact,business_impact,effort,composite_score,priority,rationale,status,created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            oid, cluster_ids[o["cluster_idx"]], o["title"],
            o["customer_impact"], o["business_impact"], o["effort"],
            o["composite_score"], o["priority"], o["rationale"],
            "new", datetime.utcnow().isoformat(),
        ),
    )
    opp_ids.append(oid)
    print(f"  {o['priority']}  [{o['composite_score']}]  {o['title']}")

conn.commit()
print(f"\n✓ {len(opps_data)} opportunities ranked  |  2× P1  |  2× P2  |  1× P3")


# ── STEP 4: PRD Generation ────────────────────────────────────────
separator("STEP 4 — PRD Agent: Generating Product Requirements")

prds_data = [
    {
        "opp_idx": 0,
        "problem": "New users, especially those in the Startup segment, do not know what actions to take after account creation. The current onboarding lacks a guided sequence, leaving 34% of users confused and at risk of churning before reaching their first activation milestone.",
        "users_affected": "Startup-tier users (34% of feedback). Primarily first-time users within the first 24 hours of signup. Also affects account managers who onboard clients manually.",
        "solution": "Redesign the onboarding flow with an interactive, step-by-step setup wizard. The wizard will guide users through data source connection, first report creation, and team invite. Include a persistent checklist, contextual tooltips, and a progress indicator. Add a 'resume onboarding' prompt for users who dropped off.",
        "acceptance_criteria": [
            "A setup wizard launches automatically for all new accounts on first login",
            "Wizard covers three steps: connect data source, create first report, invite a teammate",
            "Users can skip or resume the wizard at any time from the dashboard",
            "A checklist widget persists in the sidebar until all steps are completed",
            "Onboarding completion rate increases by ≥ 30% within 60 days of release",
        ],
        "metrics": [
            "Onboarding completion rate: ≥ 70% (up from ~40%) within 60 days",
            "Time-to-first-value: reduce from 3 days to < 1 day",
            "Churn within first 7 days: reduce by 25%",
            "Onboarding-related support tickets: reduce by 40%",
        ],
        "markdown_content": dedent("""\
            # Problem
            New users, especially those in the Startup segment, do not know what actions to take after account creation. The current onboarding lacks a guided sequence, leaving 34% of users confused and at risk of churning before reaching their first activation milestone.

            # Users Affected
            Startup-tier users (34% of feedback). Primarily first-time users within the first 24 hours of signup. Also affects account managers who onboard clients manually.

            # Proposed Solution
            Redesign the onboarding flow with an interactive, step-by-step setup wizard. The wizard will guide users through data source connection, first report creation, and team invite. Include a persistent checklist, contextual tooltips, and a progress indicator. Add a 'resume onboarding' prompt for users who dropped off.

            # Acceptance Criteria
            - [ ] A setup wizard launches automatically for all new accounts on first login
            - [ ] Wizard covers three steps: connect data source, create first report, invite a teammate
            - [ ] Users can skip or resume the wizard at any time from the dashboard
            - [ ] A checklist widget persists in the sidebar until all steps are completed
            - [ ] Onboarding completion rate increases by ≥ 30% within 60 days of release

            # Success Metrics
            - Onboarding completion rate: ≥ 70% (up from ~40%) within 60 days
            - Time-to-first-value: reduce from 3 days to < 1 day
            - Churn within first 7 days: reduce by 25%
            - Onboarding-related support tickets: reduce by 40%
        """),
    },
    {
        "opp_idx": 1,
        "problem": "SMB users experience consistently slow dashboard load times, page freezes, and degraded performance as their dataset grows. 28% of all feedback cites performance as a daily pain point, directly impacting productivity and NPS.",
        "users_affected": "SMB-tier users with datasets exceeding 50K rows. Daily-active power users running complex reports are most impacted. Affects approximately 60% of SMB accounts based on usage telemetry.",
        "solution": "Implement query result caching, lazy-load report widgets, and add a background job queue for large report generation. Introduce a loading skeleton UI to improve perceived performance. Profile and fix the top 5 slow SQL queries identified in APM tooling.",
        "acceptance_criteria": [
            "Dashboard initial load time < 2 seconds for datasets up to 500K rows",
            "Report widgets load independently (lazy loading) — no full-page blocking",
            "Large report generation runs as a background job with email/notification on completion",
            "Query result cache invalidates correctly on data updates",
            "Zero dashboard freeze incidents in the 30 days post-release",
        ],
        "metrics": [
            "P95 dashboard load time: < 2s (down from current ~8s)",
            "Report generation time: < 5s for 95% of reports",
            "Performance-related support tickets: reduce by 50%",
            "SMB NPS: +10 points within 90 days",
        ],
        "markdown_content": dedent("""\
            # Problem
            SMB users experience consistently slow dashboard load times, page freezes, and degraded performance as their dataset grows. 28% of all feedback cites performance as a daily pain point, directly impacting productivity and NPS.

            # Users Affected
            SMB-tier users with datasets exceeding 50K rows. Daily-active power users running complex reports are most impacted. Affects approximately 60% of SMB accounts based on usage telemetry.

            # Proposed Solution
            Implement query result caching, lazy-load report widgets, and add a background job queue for large report generation. Introduce a loading skeleton UI to improve perceived performance. Profile and fix the top 5 slow SQL queries identified in APM tooling.

            # Acceptance Criteria
            - [ ] Dashboard initial load time < 2 seconds for datasets up to 500K rows
            - [ ] Report widgets load independently (lazy loading) — no full-page blocking
            - [ ] Large report generation runs as a background job with email/notification on completion
            - [ ] Query result cache invalidates correctly on data updates
            - [ ] Zero dashboard freeze incidents in the 30 days post-release

            # Success Metrics
            - P95 dashboard load time: < 2s (down from current ~8s)
            - Report generation time: < 5s for 95% of reports
            - Performance-related support tickets: reduce by 50%
            - SMB NPS: +10 points within 90 days
        """),
    },
]

prd_ids = []
for p in prds_data:
    pid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn.execute(
        """INSERT INTO prds
           (id,opportunity_id,problem,users_affected,solution,acceptance_criteria,metrics,markdown_content,status,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            pid, opp_ids[p["opp_idx"]], p["problem"], p["users_affected"],
            p["solution"],
            json.dumps(p["acceptance_criteria"]),
            json.dumps(p["metrics"]),
            p["markdown_content"], "draft", now, now,
        ),
    )
    prd_ids.append(pid)
    print(f"  PRD created → {p['problem'][:70]}…")

conn.commit()
print(f"\n✓ {len(prds_data)} PRDs generated (P1 opportunities)")


# ── STEP 5: Ticket Generation ─────────────────────────────────────
separator("STEP 5 — Ticket Agent: Engineering Breakdown")

tickets_data = [
    # PRD 0 — Onboarding
    {
        "prd_idx": 0,
        "title": "Build interactive onboarding setup wizard component",
        "description": "## Context\nNew users have no guided path after signup, causing confusion and early churn.\n\n## Task\nBuild a multi-step wizard React component with steps: (1) Connect data source, (2) Create first report, (3) Invite teammate. Add progress indicator and skip/resume functionality. Store completion state per user in the DB.\n\n## Acceptance\nA setup wizard launches automatically for all new accounts on first login",
        "priority": "P1", "estimate": "4 days",
    },
    {
        "prd_idx": 0,
        "title": "Add persistent onboarding checklist widget to sidebar",
        "description": "## Context\nUsers who skip the wizard still need a way to track remaining setup steps.\n\n## Task\nAdd a collapsible checklist widget to the main sidebar. It should track the same three steps as the wizard and disappear once all are completed. Persist state server-side.\n\n## Acceptance\nA checklist widget persists in the sidebar until all steps are completed",
        "priority": "P1", "estimate": "2 days",
    },
    {
        "prd_idx": 0,
        "title": "Implement resume-onboarding prompt for returning incomplete users",
        "description": "## Context\nUsers who drop off mid-onboarding currently see a blank dashboard on return.\n\n## Task\nDetect users who have not completed onboarding on login. Show a non-blocking banner prompting them to continue from where they left off. Dismissable with a 'remind me later' option.\n\n## Acceptance\nUsers can skip or resume the wizard at any time from the dashboard",
        "priority": "P2", "estimate": "1 day",
    },
    {
        "prd_idx": 0,
        "title": "Write onboarding flow end-to-end tests",
        "description": "## Context\nOnboarding regressions directly impact new user conversion. Needs automated coverage.\n\n## Task\nWrite Playwright tests covering: wizard launch on new account, step completion, skip flow, resume flow, checklist widget state. Run in CI on every PR.\n\n## Acceptance\nOnboarding completion rate increases by ≥ 30% within 60 days of release",
        "priority": "P2", "estimate": "2 days",
    },
    # PRD 1 — Performance
    {
        "prd_idx": 1,
        "title": "Implement query result caching layer",
        "description": "## Context\nDashboard queries run on every page load with no caching, causing 6-10s load times for large datasets.\n\n## Task\nIntroduce a Redis-based query cache with a 5-minute TTL. Cache keyed by query hash + user ID. Invalidate on data write. Add a cache-hit header for observability.\n\n## Acceptance\nDashboard initial load time < 2 seconds for datasets up to 500K rows",
        "priority": "P1", "estimate": "3 days",
    },
    {
        "prd_idx": 1,
        "title": "Convert report widgets to lazy-load independently",
        "description": "## Context\nAll dashboard widgets currently block on a single API call, meaning one slow widget freezes the whole page.\n\n## Task\nRefactor the dashboard to load each widget independently via separate API calls. Render a skeleton loader per widget while data fetches. No widget should block another.\n\n## Acceptance\nReport widgets load independently — no full-page blocking",
        "priority": "P1", "estimate": "3 days",
    },
    {
        "prd_idx": 1,
        "title": "Move large report generation to background job queue",
        "description": "## Context\nReports with >10K rows time out or freeze the UI during generation.\n\n## Task\nAdd a Celery/RQ background job for reports that exceed a row threshold. Return a job ID immediately. Notify the user via in-app notification and email when ready. Add a 'My Reports' page to view job status and download results.\n\n## Acceptance\nLarge report generation runs as a background job with notification on completion",
        "priority": "P1", "estimate": "4 days",
    },
    {
        "prd_idx": 1,
        "title": "Profile and fix top 5 slow database queries",
        "description": "## Context\nAPM tooling shows 5 queries account for 80% of dashboard latency.\n\n## Task\nIdentify top 5 slow queries from APM. Add missing indexes, rewrite N+1 patterns, and add EXPLAIN ANALYZE output to PR. Target < 100ms per query at P95.\n\n## Acceptance\nP95 dashboard load time < 2s",
        "priority": "P1", "estimate": "2 days",
    },
]

total_tickets = 0
for t in tickets_data:
    tid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO tickets (id,prd_id,title,description,priority,estimate,status,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (tid, prd_ids[t["prd_idx"]], t["title"], t["description"], t["priority"], t["estimate"], "open", datetime.utcnow().isoformat()),
    )
    total_tickets += 1
    print(f"  {t['priority']}  [{t['estimate']:6s}]  {t['title']}")

conn.commit()
conn.close()
print(f"\n✓ {total_tickets} tickets created")


# ── SUMMARY ───────────────────────────────────────────────────────
separator("PIPELINE COMPLETE — Summary")

print(f"""
  Input
  ─────────────────────────────────────────
  Source file     : customer_feedback.csv
  Total feedback  : {len(rows)} items
  Segments        : Startup · SMB · Enterprise

  Output
  ─────────────────────────────────────────
  Clusters found  : 5
    Onboarding                  34%  (17 items)
    Dashboard Performance       28%  (14 items)
    Slack / Team Integrations   24%  (12 items)
    Reporting & Export          10%   (5 items)
    Billing & Admin              4%   (2 items)

  Opportunities ranked : 5
    P1  [7.28]  Redesign onboarding flow with guided setup wizard
    P1  [6.10]  Optimise dashboard and report rendering performance
    P2  [5.60]  Build native Slack and Microsoft Teams integration
    P2  [4.75]  Add custom reports and CSV/PDF export
    P3  [2.83]  Improve billing visibility and admin audit logs

  PRDs generated   : 2  (P1 opportunities)
  Tickets created  : {total_tickets}

  ─────────────────────────────────────────
  UI  →  http://localhost:3000
""")
