"""
Wipes and re-seeds clusters / opportunities / PRDs / tickets
using the exact UUID format SQLAlchemy+SQLite expects (32-char hex, no hyphens).
"""

import sqlite3
import uuid
import json
from datetime import datetime
from textwrap import dedent

DB = r"C:\Users\Admin\Desktop\Claude code\ai-product-manager\ai-product-manager\ai_pm.db"


def uid():
    return uuid.uuid4().hex          # 32-char, no hyphens — matches SQLAlchemy Uuid


def now():
    return datetime.utcnow().isoformat()


conn = sqlite3.connect(DB)

# ── Wipe stale data ───────────────────────────────────────────────
conn.execute("DELETE FROM tickets")
conn.execute("DELETE FROM prds")
conn.execute("DELETE FROM opportunities")
conn.execute("DELETE FROM feedback_clusters")
conn.commit()
print("Cleared old data")

# ── Clusters ──────────────────────────────────────────────────────
clusters = [
    {
        "id": uid(),
        "theme": "Confusing Onboarding Experience",
        "frequency_score": 0.34,
        "summary": "New users, primarily Startups, struggle to complete setup and don't know what to do after signup.",
        "evidence": [
            "Onboarding is confusing and I don't know what to do after signup.",
            "I almost abandoned signup because onboarding was confusing.",
            "I expected a guided setup wizard.",
        ],
    },
    {
        "id": uid(),
        "theme": "Slow Dashboard & Reporting Performance",
        "frequency_score": 0.28,
        "summary": "SMB customers report consistently slow load times and page freezes when working with larger datasets.",
        "evidence": [
            "Dashboard takes too long to load.",
            "Dashboard performance is very slow.",
            "Dashboard freezes occasionally.",
        ],
    },
    {
        "id": uid(),
        "theme": "Missing Slack & Team Integrations",
        "frequency_score": 0.24,
        "summary": "Enterprise customers are blocked without Slack and Microsoft Teams integrations.",
        "evidence": [
            "Need Slack integration for team notifications.",
            "Slack integration is required for our workflow.",
            "Slack integration would save us a lot of time.",
        ],
    },
    {
        "id": uid(),
        "theme": "Limited Reporting & Export Features",
        "frequency_score": 0.10,
        "summary": "SMB and Enterprise users find reporting too basic — missing custom reports and export options.",
        "evidence": [
            "Reporting dashboard feels limited.",
            "The analytics reports lack export options.",
            "Custom reports are missing.",
        ],
    },
    {
        "id": uid(),
        "theme": "Billing & Admin Management",
        "frequency_score": 0.04,
        "summary": "Enterprise admins struggle to find invoices, manage permissions, and access audit logs.",
        "evidence": [
            "Billing invoices are difficult to find.",
            "User permissions are hard to manage.",
            "Need better audit logs.",
        ],
    },
]

for c in clusters:
    conn.execute(
        "INSERT INTO feedback_clusters (id,theme,frequency_score,summary,evidence,created_at) VALUES (?,?,?,?,?,?)",
        (c["id"], c["theme"], c["frequency_score"], c["summary"], json.dumps(c["evidence"]), now()),
    )
    print(f"  Cluster  {c['theme'][:45]}")

conn.commit()

# ── Opportunities ─────────────────────────────────────────────────
opps = [
    dict(cluster=0, title="Redesign onboarding flow with guided setup wizard",
         ci=9.0, bi=8.5, effort=4.0, score=7.28, priority="P1",
         rationale="Affects 34% of feedback; directly blocks new user activation and drives Startup churn."),
    dict(cluster=1, title="Optimise dashboard and report rendering performance",
         ci=8.5, bi=8.0, effort=5.0, score=6.10, priority="P1",
         rationale="28% of feedback; SMB daily-active users most impacted. Directly affects retention and NPS."),
    dict(cluster=2, title="Build native Slack and Microsoft Teams integration",
         ci=9.0, bi=9.0, effort=6.0, score=5.60, priority="P2",
         rationale="Top Enterprise request (24% of feedback). High impact, moderate engineering effort."),
    dict(cluster=3, title="Add custom reports and CSV/PDF export",
         ci=7.0, bi=7.5, effort=4.0, score=4.75, priority="P2",
         rationale="Unblocks analytical workflows for SMB and Enterprise. Reduces support load."),
    dict(cluster=4, title="Improve billing visibility and admin audit logs",
         ci=5.0, bi=5.5, effort=3.0, score=2.83, priority="P3",
         rationale="Low frequency but high friction during Enterprise procurement and compliance reviews."),
]

opp_ids = []
for o in opps:
    oid = uid()
    opp_ids.append(oid)
    conn.execute(
        """INSERT INTO opportunities
           (id,cluster_id,title,customer_impact,business_impact,effort,composite_score,priority,rationale,status,created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (oid, clusters[o["cluster"]]["id"], o["title"],
         o["ci"], o["bi"], o["effort"], o["score"],
         o["priority"], o["rationale"], "new", now()),
    )
    print(f"  {o['priority']}  [{o['score']}]  {o['title'][:50]}")

conn.commit()

# ── PRDs ──────────────────────────────────────────────────────────
prds = [
    {
        "opp_idx": 0,
        "problem": "New users, especially in the Startup segment, do not know what actions to take after account creation. The current onboarding lacks a guided sequence, leaving 34% of users confused and at risk of churning before reaching their first activation milestone.",
        "users_affected": "Startup-tier users (34% of feedback). First-time users within 24 hours of signup. Also affects account managers who onboard clients manually.",
        "solution": "Redesign the onboarding flow with an interactive step-by-step setup wizard. Guide users through: (1) connect data source, (2) create first report, (3) invite a teammate. Include a persistent checklist, contextual tooltips, and a progress indicator. Add a 'resume onboarding' prompt for users who dropped off.",
        "acceptance_criteria": [
            "Setup wizard launches automatically for all new accounts on first login",
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
            New users, especially in the Startup segment, do not know what actions to take after account creation. The current onboarding lacks a guided sequence, leaving 34% of users confused and at risk of churning before reaching their first activation milestone.

            # Users Affected
            Startup-tier users (34% of feedback). First-time users within 24 hours of signup. Also affects account managers who onboard clients manually.

            # Proposed Solution
            Redesign the onboarding flow with an interactive step-by-step setup wizard covering: (1) connect data source, (2) create first report, (3) invite a teammate. Include a persistent checklist, contextual tooltips, and a progress indicator. Add a 'resume onboarding' prompt for drop-offs.

            # Acceptance Criteria
            - [ ] Setup wizard launches automatically for all new accounts on first login
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
        "users_affected": "SMB-tier users with datasets exceeding 50K rows. Daily-active power users running complex reports are most impacted — approximately 60% of SMB accounts.",
        "solution": "Implement query result caching, lazy-load report widgets, and add a background job queue for large report generation. Introduce skeleton loading UI. Profile and fix the top 5 slow SQL queries identified in APM tooling.",
        "acceptance_criteria": [
            "Dashboard initial load time < 2 seconds for datasets up to 500K rows",
            "Report widgets load independently via lazy loading — no full-page blocking",
            "Large report generation runs as a background job with notification on completion",
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
            SMB-tier users with datasets exceeding 50K rows. Daily-active power users running complex reports are most impacted — approximately 60% of SMB accounts.

            # Proposed Solution
            Implement query result caching, lazy-load report widgets, and add a background job queue for large report generation. Introduce skeleton loading UI. Profile and fix the top 5 slow SQL queries identified in APM tooling.

            # Acceptance Criteria
            - [ ] Dashboard initial load time < 2 seconds for datasets up to 500K rows
            - [ ] Report widgets load independently via lazy loading — no full-page blocking
            - [ ] Large report generation runs as a background job with notification on completion
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
for p in prds:
    pid = uid()
    prd_ids.append(pid)
    ts = now()
    conn.execute(
        """INSERT INTO prds
           (id,opportunity_id,problem,users_affected,solution,acceptance_criteria,metrics,markdown_content,status,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (pid, opp_ids[p["opp_idx"]], p["problem"], p["users_affected"], p["solution"],
         json.dumps(p["acceptance_criteria"]), json.dumps(p["metrics"]),
         p["markdown_content"], "draft", ts, ts),
    )
    print(f"  PRD  {p['problem'][:60]}…")

conn.commit()

# ── Tickets ───────────────────────────────────────────────────────
tickets = [
    # PRD 0 — Onboarding
    ("Build interactive onboarding setup wizard component",
     "## Context\nNew users have no guided path after signup, causing confusion and early churn.\n\n## Task\nBuild a multi-step wizard React component with steps: (1) Connect data source, (2) Create first report, (3) Invite teammate. Add progress indicator and skip/resume functionality. Store completion state per user.\n\n## Acceptance\nSetup wizard launches automatically for all new accounts on first login",
     0, "P1", "4 days"),
    ("Add persistent onboarding checklist widget to sidebar",
     "## Context\nUsers who skip the wizard still need a way to track remaining setup steps.\n\n## Task\nAdd a collapsible checklist widget to the main sidebar. Track the same three steps as the wizard. Disappears once all are completed. Persist state server-side.\n\n## Acceptance\nA checklist widget persists in the sidebar until all steps are completed",
     0, "P1", "2 days"),
    ("Implement resume-onboarding prompt for returning users",
     "## Context\nUsers who drop off mid-onboarding see a blank dashboard on return.\n\n## Task\nDetect users who have not completed onboarding on login. Show a non-blocking banner prompting them to continue. Dismissable with 'remind me later' option.\n\n## Acceptance\nUsers can skip or resume the wizard at any time from the dashboard",
     0, "P2", "1 day"),
    ("Write onboarding flow end-to-end tests",
     "## Context\nOnboarding regressions directly impact new user conversion.\n\n## Task\nWrite Playwright tests covering wizard launch, step completion, skip flow, resume flow, and checklist state. Run in CI on every PR.\n\n## Acceptance\nOnboarding completion rate increases by ≥ 30% within 60 days",
     0, "P2", "2 days"),
    # PRD 1 — Performance
    ("Implement query result caching layer",
     "## Context\nDashboard queries run on every page load with no caching, causing 6–10s load times.\n\n## Task\nIntroduce a cache with 5-minute TTL, keyed by query hash + user ID. Invalidate on data write. Add cache-hit header for observability.\n\n## Acceptance\nDashboard initial load time < 2 seconds for datasets up to 500K rows",
     1, "P1", "3 days"),
    ("Convert report widgets to lazy-load independently",
     "## Context\nAll dashboard widgets block on a single API call, meaning one slow widget freezes the page.\n\n## Task\nRefactor dashboard to load each widget independently. Render a skeleton loader per widget while fetching. No widget should block another.\n\n## Acceptance\nReport widgets load independently — no full-page blocking",
     1, "P1", "3 days"),
    ("Move large report generation to background job queue",
     "## Context\nReports with >10K rows time out or freeze the UI during generation.\n\n## Task\nAdd a background job for reports exceeding a row threshold. Return a job ID immediately. Notify user via in-app notification and email when ready.\n\n## Acceptance\nLarge report generation runs as a background job with notification on completion",
     1, "P1", "4 days"),
    ("Profile and fix top 5 slow database queries",
     "## Context\nAPM tooling shows 5 queries account for 80% of dashboard latency.\n\n## Task\nIdentify top 5 slow queries from APM. Add missing indexes, rewrite N+1 patterns. Target < 100ms per query at P95.\n\n## Acceptance\nP95 dashboard load time < 2s",
     1, "P1", "2 days"),
]

for title, desc, prd_idx, priority, estimate in tickets:
    conn.execute(
        "INSERT INTO tickets (id,prd_id,title,description,priority,estimate,status,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (uid(), prd_ids[prd_idx], title, desc, priority, estimate, "open", now()),
    )
    print(f"  {priority}  [{estimate:6}]  {title[:52]}")

conn.commit()
conn.close()

print("\nDone. All data seeded with correct UUID format.")
print("Refresh http://localhost:3000/insights")
