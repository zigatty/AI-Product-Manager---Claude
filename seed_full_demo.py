"""
Seeds complete demo analysis across all 5 opportunities.
Every page in the UI will have rich, realistic content.
"""

import sqlite3, uuid, json
from datetime import datetime
from textwrap import dedent

DB = r"C:\Users\Admin\Desktop\Claude code\ai-product-manager\ai-product-manager\ai_pm.db"
conn = sqlite3.connect(DB)

def uid(): return uuid.uuid4().hex
def now(): return datetime.utcnow().isoformat()

# ── Wipe PRDs and tickets only (keep feedback + clusters + opportunities) ─────
conn.execute("DELETE FROM tickets")
conn.execute("DELETE FROM prds")
conn.commit()

# ── Fetch existing opportunity IDs in priority order ─────────────────────────
opps = conn.execute(
    "SELECT id, title, priority FROM opportunities ORDER BY composite_score DESC"
).fetchall()

print(f"Found {len(opps)} opportunities")
for o in opps:
    print(f"  {o[2]}  {o[1][:55]}")

# ── PRD data for all 5 opportunities ─────────────────────────────────────────
prd_templates = [
    # 0 — Onboarding (P1)
    dict(
        problem="New users — primarily Startups — have no guided path after account creation. 34% of all feedback identifies onboarding confusion as the primary reason for early drop-off and failed activation.",
        users_affected="Startup-tier users in their first 24 hours. ~17 of 50 feedback submissions cite this. Also affects account managers onboarding enterprise clients manually.",
        solution="Build an interactive 3-step setup wizard (connect data source → create first report → invite teammate). Add a persistent sidebar checklist, contextual tooltips at each step, and a 'resume onboarding' prompt for returning incomplete users.",
        criteria=[
            "Setup wizard launches automatically on first login for all new accounts",
            "Wizard covers exactly 3 steps: connect data source, create report, invite teammate",
            "Users can skip or resume wizard from any point in the dashboard",
            "Persistent checklist in sidebar disappears only when all steps complete",
            "Onboarding completion rate increases by ≥ 30% within 60 days of launch",
        ],
        metrics=[
            "Onboarding completion rate: ≥ 70% within 60 days (up from ~40%)",
            "Time-to-first-value: < 1 day (down from 3 days)",
            "Day-7 churn: reduce by 25%",
            "Onboarding support tickets: reduce by 40%",
        ],
        markdown=dedent("""\
            # Problem
            New users — primarily Startups — have no guided path after account creation. 34% of all feedback identifies onboarding confusion as the primary reason for early drop-off and failed activation.

            # Users Affected
            Startup-tier users in their first 24 hours. ~17 of 50 feedback submissions cite this. Also affects account managers onboarding enterprise clients manually.

            # Proposed Solution
            Build an interactive 3-step setup wizard (connect data source → create first report → invite teammate). Add a persistent sidebar checklist, contextual tooltips at each step, and a 'resume onboarding' prompt for returning incomplete users.

            # Acceptance Criteria
            - [ ] Setup wizard launches automatically on first login for all new accounts
            - [ ] Wizard covers exactly 3 steps: connect data source, create report, invite teammate
            - [ ] Users can skip or resume wizard from any point in the dashboard
            - [ ] Persistent checklist in sidebar disappears only when all steps complete
            - [ ] Onboarding completion rate increases by ≥ 30% within 60 days of launch

            # Success Metrics
            - Onboarding completion rate: ≥ 70% within 60 days (up from ~40%)
            - Time-to-first-value: < 1 day (down from 3 days)
            - Day-7 churn: reduce by 25%
            - Onboarding support tickets: reduce by 40%
        """),
        tickets=[
            ("Build multi-step onboarding wizard UI component", "P1", "4 days",
             "## Context\nNo guided setup exists — users see a blank dashboard after signup.\n\n## Task\nBuild a React wizard component with 3 steps: Connect data source, Create first report, Invite teammate. Include progress bar, step validation, skip and back navigation. Persist completion state per user in the database.\n\n## Acceptance\nWizard launches automatically on first login for all new accounts"),
            ("Add persistent onboarding checklist to sidebar", "P1", "2 days",
             "## Context\nUsers who dismiss the wizard need a fallback to track remaining steps.\n\n## Task\nAdd a collapsible checklist widget to the app sidebar. Mirrors the 3 wizard steps. Disappears when all complete. State synced server-side so it survives sessions.\n\n## Acceptance\nPersistent checklist in sidebar disappears only when all steps complete"),
            ("Implement resume-onboarding nudge for returning users", "P2", "1 day",
             "## Context\nUsers who abandon the wizard mid-flow see no prompt to continue on return.\n\n## Task\nOn login, detect users with incomplete onboarding. Show a non-blocking top banner: 'Continue your setup →'. Dismissable per session with 'Remind me later'.\n\n## Acceptance\nUsers can skip or resume wizard from any point in the dashboard"),
            ("Onboarding funnel analytics instrumentation", "P2", "1 day",
             "## Context\nWe have no visibility into which step users drop off at.\n\n## Task\nAdd analytics events: wizard_started, step_completed (with step number), wizard_skipped, wizard_completed, checklist_item_checked. Send to existing analytics pipeline.\n\n## Acceptance\nOnboarding completion rate increases by ≥ 30% within 60 days"),
            ("Write Playwright E2E tests for onboarding flows", "P2", "2 days",
             "## Context\nOnboarding regressions directly hurt new user conversion.\n\n## Task\nWrite Playwright tests: new account wizard auto-launch, complete flow, skip flow, resume flow, checklist persistence. Run in CI on every PR targeting main.\n\n## Acceptance\nAll acceptance criteria verifiable via automated tests"),
        ],
    ),
    # 1 — Dashboard Performance (P1)
    dict(
        problem="SMB users report consistently slow load times (6–10 seconds), page freezes, and degraded performance under load. 28% of all feedback targets this directly, making it the second-highest frequency issue.",
        users_affected="SMB-tier users with datasets > 50K rows. Affects ~60% of SMB accounts in daily active usage. Power users running multi-widget dashboards are hit hardest.",
        solution="Introduce a query result cache (5-min TTL), refactor report widgets to load independently via lazy loading, move large report generation to a background job queue, and fix the top 5 slow database queries identified via APM.",
        criteria=[
            "Dashboard initial load time < 2s for datasets up to 500K rows",
            "Each report widget loads independently — no full-page blocking",
            "Reports with > 10K rows run as background jobs with completion notification",
            "Query cache invalidates correctly on any data write",
            "Zero dashboard freeze incidents in 30 days post-release",
        ],
        metrics=[
            "P95 dashboard load time: < 2s (down from ~8s)",
            "Report generation time: < 5s for 95% of reports",
            "Performance-related support tickets: -50% within 30 days",
            "SMB NPS score: +10 points within 90 days",
        ],
        markdown=dedent("""\
            # Problem
            SMB users report consistently slow load times (6–10 seconds), page freezes, and degraded performance under load. 28% of all feedback targets this directly.

            # Users Affected
            SMB-tier users with datasets > 50K rows. Affects ~60% of SMB accounts in daily active usage. Power users running multi-widget dashboards are hit hardest.

            # Proposed Solution
            Introduce a query result cache (5-min TTL), refactor report widgets to lazy-load independently, move large report generation to a background job queue, and fix the top 5 slow database queries.

            # Acceptance Criteria
            - [ ] Dashboard initial load time < 2s for datasets up to 500K rows
            - [ ] Each report widget loads independently — no full-page blocking
            - [ ] Reports with > 10K rows run as background jobs with completion notification
            - [ ] Query cache invalidates correctly on any data write
            - [ ] Zero dashboard freeze incidents in 30 days post-release

            # Success Metrics
            - P95 dashboard load time: < 2s (down from ~8s)
            - Report generation time: < 5s for 95% of reports
            - Performance-related support tickets: -50% within 30 days
            - SMB NPS score: +10 points within 90 days
        """),
        tickets=[
            ("Implement query result caching with 5-minute TTL", "P1", "3 days",
             "## Context\nEvery page load re-runs the same expensive queries with no caching layer.\n\n## Task\nAdd an in-memory cache (or Redis) keyed by query hash + user ID, TTL 5 minutes. Invalidate on any data write to the affected tables. Expose cache hit/miss ratio via a metrics endpoint.\n\n## Acceptance\nDashboard initial load time < 2s for datasets up to 500K rows"),
            ("Refactor dashboard widgets to lazy-load independently", "P1", "3 days",
             "## Context\nAll widgets block on a single API call — one slow widget freezes the whole page.\n\n## Task\nRefactor each widget to fire its own independent API call on mount. Render a skeleton loader while data fetches. No widget blocks another from rendering.\n\n## Acceptance\nEach report widget loads independently — no full-page blocking"),
            ("Add background job queue for large report generation", "P1", "4 days",
             "## Context\nReports > 10K rows time out the UI and block the main thread.\n\n## Task\nQueue reports exceeding a size threshold as background jobs. Return a job ID immediately to the client. Poll for status. Notify via in-app notification + email on completion. Add a 'My Reports' history page.\n\n## Acceptance\nReports with > 10K rows run as background jobs with completion notification"),
            ("Profile and fix top 5 slow database queries", "P1", "2 days",
             "## Context\nAPM shows 5 queries account for 80% of all dashboard latency.\n\n## Task\nIdentify the 5 slowest queries from APM. Add missing indexes, fix N+1 patterns, and rewrite any suboptimal joins. Attach EXPLAIN ANALYZE output to PR. Each query must run < 100ms at P95.\n\n## Acceptance\nQuery cache invalidates correctly on any data write"),
            ("Add loading skeleton UI for dashboard widgets", "P2", "1 day",
             "## Context\nBlank screens during load feel like crashes to users.\n\n## Task\nAdd skeleton loader components matching the shape of each dashboard widget. Show skeleton during the initial fetch. Transition to real content without layout shift.\n\n## Acceptance\nZero dashboard freeze incidents in 30 days post-release"),
        ],
    ),
    # 2 — Slack Integration (P2)
    dict(
        problem="Enterprise customers require Slack and Microsoft Teams integrations to embed the product into their existing workflows. 24% of all feedback — exclusively from Enterprise users — cites missing integrations as a blocker for team adoption.",
        users_affected="Enterprise-tier users in team-based workflows. Mentioned by 12 of 50 respondents. Affects procurement decisions and expansion ARR for existing Enterprise accounts.",
        solution="Build a native Slack integration: post report summaries, threshold alerts, and digest notifications to user-configured channels. Add a Microsoft Teams connector using the same webhook architecture. Provide an Integrations settings page for configuration.",
        criteria=[
            "Users can connect their Slack workspace via OAuth from the Integrations settings page",
            "Report-ready and alert notifications post to a selected Slack channel automatically",
            "Microsoft Teams connector available via webhook URL configuration",
            "Integration can be paused or disconnected without data loss",
            "Slack and Teams integration used by ≥ 40% of Enterprise accounts within 90 days",
        ],
        metrics=[
            "Enterprise integration adoption: ≥ 40% of accounts within 90 days",
            "Enterprise expansion ARR influenced by integrations: +15%",
            "Integration-related support tickets: < 5 per month after launch",
            "Enterprise NPS: +8 points within 90 days of launch",
        ],
        markdown=dedent("""\
            # Problem
            Enterprise customers require Slack and Microsoft Teams integrations to embed the product into their existing workflows. 24% of all feedback — exclusively from Enterprise — cites missing integrations as a blocker.

            # Users Affected
            Enterprise-tier users in team workflows. 12 of 50 respondents. Affects procurement decisions and expansion ARR for existing Enterprise accounts.

            # Proposed Solution
            Build a native Slack integration with OAuth, posting report summaries and alerts to configured channels. Add a Microsoft Teams connector via webhook. Provide a unified Integrations settings page.

            # Acceptance Criteria
            - [ ] Users can connect Slack workspace via OAuth from Integrations settings
            - [ ] Report-ready and alert notifications post to selected Slack channel automatically
            - [ ] Microsoft Teams connector available via webhook URL configuration
            - [ ] Integration can be paused or disconnected without data loss
            - [ ] Slack and Teams integration used by ≥ 40% of Enterprise accounts within 90 days

            # Success Metrics
            - Enterprise integration adoption: ≥ 40% of accounts within 90 days
            - Enterprise expansion ARR influenced: +15%
            - Integration support tickets: < 5/month after launch
            - Enterprise NPS: +8 points within 90 days
        """),
        tickets=[
            ("Implement Slack OAuth connection flow", "P2", "3 days",
             "## Context\nEnterprise users have no way to connect their Slack workspace.\n\n## Task\nAdd a Slack OAuth2 flow accessible from the Integrations settings page. Store the workspace token securely. Show connection status and the connected workspace name. Allow disconnect.\n\n## Acceptance\nUsers can connect their Slack workspace via OAuth from the Integrations settings page"),
            ("Build Slack notification delivery service", "P2", "3 days",
             "## Context\nOnce connected, the app needs to deliver notifications to Slack channels.\n\n## Task\nBuild a notification service that posts formatted messages to a user-selected Slack channel when: (1) a report finishes generating, (2) a threshold alert fires. Use Block Kit for rich formatting.\n\n## Acceptance\nReport-ready and alert notifications post to selected Slack channel automatically"),
            ("Add Microsoft Teams webhook integration", "P2", "2 days",
             "## Context\nSeveral Enterprise accounts use Teams instead of Slack.\n\n## Task\nAdd a Teams connector on the Integrations settings page. Accept an incoming webhook URL from the user. Send the same notification payloads as Slack using Teams Adaptive Card format.\n\n## Acceptance\nMicrosoft Teams connector available via webhook URL configuration"),
            ("Build Integrations settings page", "P2", "2 days",
             "## Context\nNo UI exists for users to manage their connected integrations.\n\n## Task\nCreate an Integrations settings page listing Slack, Teams, and future connectors. Show connection status for each. Add connect/disconnect/pause controls. Link from the main settings navigation.\n\n## Acceptance\nIntegration can be paused or disconnected without data loss"),
        ],
    ),
    # 3 — Reporting (P2)
    dict(
        problem="SMB and Enterprise users find the built-in reporting too limited for their analytical workflows. Missing features include custom report builders, CSV/PDF export, and scheduled report delivery.",
        users_affected="SMB users running weekly reporting workflows and Enterprise analysts producing stakeholder reports. ~10% of all feedback (5 respondents) — low frequency but high severity for affected users.",
        solution="Build a custom report builder with drag-and-drop metrics selection, add CSV and PDF export to all report views, and introduce scheduled report delivery via email on a user-defined cadence.",
        criteria=[
            "Users can create custom reports by selecting and arranging any available metrics",
            "All report views have a one-click CSV export and a formatted PDF export",
            "Users can schedule any report to be emailed on daily, weekly, or monthly cadence",
            "Custom reports persist and are accessible from a 'My Reports' library",
            "Report export used by ≥ 50% of SMB and Enterprise users within 60 days",
        ],
        metrics=[
            "Custom report creation: ≥ 60% of SMB/Enterprise accounts within 60 days",
            "Export feature adoption: ≥ 50% of eligible users within 60 days",
            "Reporting-related support tickets: -35% within 30 days",
            "Feature NPS for reporting: improve from 3.2 to ≥ 4.0 out of 5",
        ],
        markdown=dedent("""\
            # Problem
            SMB and Enterprise users find built-in reporting too limited. Missing: custom report builders, CSV/PDF export, and scheduled delivery.

            # Users Affected
            SMB users running weekly reporting workflows and Enterprise analysts. ~5 respondents — low frequency but high severity for affected users.

            # Proposed Solution
            Build a custom report builder with drag-and-drop metrics, add CSV and PDF export to all report views, and introduce scheduled email delivery.

            # Acceptance Criteria
            - [ ] Users can create custom reports by selecting and arranging any available metrics
            - [ ] All report views have one-click CSV and formatted PDF export
            - [ ] Users can schedule any report to be emailed on daily, weekly, or monthly cadence
            - [ ] Custom reports persist in a 'My Reports' library
            - [ ] Report export used by ≥ 50% of SMB and Enterprise users within 60 days

            # Success Metrics
            - Custom report creation: ≥ 60% of SMB/Enterprise accounts within 60 days
            - Export adoption: ≥ 50% of eligible users within 60 days
            - Reporting support tickets: -35% within 30 days
            - Reporting feature NPS: 3.2 → ≥ 4.0
        """),
        tickets=[
            ("Build custom report builder UI", "P2", "5 days",
             "## Context\nUsers can only view pre-built reports with no customisation.\n\n## Task\nBuild a drag-and-drop report builder: metric picker panel on the left, canvas on the right. Support at least 3 chart types (bar, line, table). Save and name reports. Store in a 'My Reports' section.\n\n## Acceptance\nUsers can create custom reports by selecting and arranging any available metrics"),
            ("Add CSV and PDF export to all report views", "P2", "2 days",
             "## Context\nUsers have no way to extract report data for stakeholder sharing.\n\n## Task\nAdd an Export dropdown to every report view. CSV: raw data as a flat file. PDF: rendered chart + data table with logo/date header. Trigger as a background job for large exports.\n\n## Acceptance\nAll report views have one-click CSV and formatted PDF export"),
            ("Implement scheduled report email delivery", "P3", "3 days",
             "## Context\nUsers manually re-run reports each week for stakeholder updates.\n\n## Task\nAdd a 'Schedule' option to any report. Let users choose cadence (daily/weekly/monthly) and recipient email list. Use the background job queue to generate and send on schedule.\n\n## Acceptance\nUsers can schedule any report to be emailed on daily, weekly, or monthly cadence"),
        ],
    ),
    # 4 — Billing & Admin (P3)
    dict(
        problem="Enterprise admins struggle to locate invoices, manage user permissions at scale, and access audit logs required for internal compliance reviews. While low in feedback volume, these friction points surface during procurement and renewal cycles.",
        users_affected="Enterprise account admins and finance stakeholders. 2 of 50 respondents — low frequency but critical during procurement, compliance audits, and contract renewals.",
        solution="Redesign the Billing section with a dedicated invoice history page, add a role-based permissions manager with bulk user controls, and expose structured audit logs with search and export capabilities.",
        criteria=[
            "Admins can view, filter, and download all invoices from a dedicated Billing page",
            "Role-based permissions can be assigned to users individually or in bulk",
            "Audit log shows all admin actions with timestamp, user, and action type",
            "Audit log is exportable as CSV for compliance use",
            "Admin task completion time (invoice download, permission change) < 2 minutes",
        ],
        metrics=[
            "Invoice-related support tickets: reduce to 0 within 30 days",
            "Admin task completion time: < 2 minutes for core tasks",
            "Enterprise renewal friction score: -20% (measured in renewal survey)",
            "Audit log export used by ≥ 80% of Enterprise accounts within 90 days",
        ],
        markdown=dedent("""\
            # Problem
            Enterprise admins struggle to locate invoices, manage user permissions at scale, and access audit logs for compliance reviews. Surfaces during procurement and renewal cycles.

            # Users Affected
            Enterprise account admins and finance stakeholders. 2 of 50 respondents — critical during procurement, compliance audits, and renewals.

            # Proposed Solution
            Redesign Billing with a dedicated invoice history page, add a role-based permissions manager with bulk controls, and expose structured audit logs with search and CSV export.

            # Acceptance Criteria
            - [ ] Admins can view, filter, and download all invoices from a dedicated Billing page
            - [ ] Role-based permissions assignable individually or in bulk
            - [ ] Audit log shows all admin actions with timestamp, user, and action type
            - [ ] Audit log exportable as CSV for compliance
            - [ ] Admin task completion time < 2 minutes for core tasks

            # Success Metrics
            - Invoice support tickets: reduce to 0 within 30 days
            - Admin task completion time: < 2 minutes
            - Enterprise renewal friction: -20%
            - Audit log export adoption: ≥ 80% Enterprise accounts within 90 days
        """),
        tickets=[
            ("Redesign Billing page with invoice history and download", "P3", "2 days",
             "## Context\nAdmins can't find invoices — they contact support to get copies.\n\n## Task\nBuild a dedicated Billing page under Account Settings. List all invoices with date, amount, status. Allow filter by date range. One-click PDF download per invoice. Show current plan and next billing date at top.\n\n## Acceptance\nAdmins can view, filter, and download all invoices from a dedicated Billing page"),
            ("Build role-based permissions manager with bulk controls", "P3", "3 days",
             "## Context\nEnterprise admins manage permissions user-by-user with no bulk operations.\n\n## Task\nAdd a User Management page under Admin settings. Show all users with their current role. Allow multi-select and bulk role assignment. Support roles: Viewer, Editor, Admin. Log all role changes to audit log.\n\n## Acceptance\nRole-based permissions assignable individually or in bulk"),
            ("Implement structured audit log with search and CSV export", "P3", "2 days",
             "## Context\nNo audit trail exists — compliance teams cannot verify who changed what.\n\n## Task\nCreate an Audit Log page under Admin settings. Log: user login/logout, role changes, report creation/deletion, integration connect/disconnect, data exports. Add text search and date filter. CSV export button.\n\n## Acceptance\nAudit log shows all admin actions and is exportable as CSV"),
        ],
    ),
]

# ── Insert PRDs and tickets ───────────────────────────────────────
total_prds = 0
total_tickets = 0

for i, (opp_row, prd_data) in enumerate(zip(opps, prd_templates)):
    opp_id, opp_title, priority = opp_row
    pid = uid()
    ts = now()

    conn.execute(
        """INSERT INTO prds
           (id,opportunity_id,problem,users_affected,solution,
            acceptance_criteria,metrics,markdown_content,status,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (pid, opp_id,
         prd_data["problem"], prd_data["users_affected"], prd_data["solution"],
         json.dumps(prd_data["criteria"]), json.dumps(prd_data["metrics"]),
         prd_data["markdown"], "draft", ts, ts),
    )
    total_prds += 1
    print(f"\n  PRD [{priority}]  {opp_title[:52]}")
    print(f"         {len(prd_data['criteria'])} criteria · {len(prd_data['metrics'])} metrics")

    for title, tick_priority, estimate, description in prd_data["tickets"]:
        conn.execute(
            "INSERT INTO tickets (id,prd_id,title,description,priority,estimate,status,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (uid(), pid, title, description, tick_priority, estimate, "open", now()),
        )
        total_tickets += 1
        print(f"    {tick_priority}  [{estimate:6}]  {title[:52]}")

conn.commit()
conn.close()

print(f"\n{'='*58}")
print(f"  Done  —  {total_prds} PRDs  ·  {total_tickets} tickets")
print(f"  Refresh  http://localhost:3000")
print(f"{'='*58}")
