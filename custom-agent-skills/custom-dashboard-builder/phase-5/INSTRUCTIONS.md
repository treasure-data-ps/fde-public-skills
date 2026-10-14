---
name: phase-5-instructions
description: Phase 5 specific instructions for handoff documentation
priority: LOW
load_order: 1.5
---

# Phase 5 Instructions — Handoff Documentation

**Read this BEFORE `./SKILL.md`.**

**Phase 5 is OPTIONAL (after Phase 3 approved).**

---

## Phase 5 Goal

Create 4 markdown documentation files for users and operators:

1. **Architecture.md** — How the dashboard works (data flow, components, dependencies)
2. **Usage Guide.md** — How to use the dashboard (filters, KPIs, how to interpret)
3. **Runbook.md** — How to operate/troubleshoot (workflows, SINK tables, common issues)
4. **Access & Ownership.md** — Who can access, who to contact (no generic "contact your admin")

**Deliverable:** 4 markdown files saved locally, ready to share or publish

---

## Quick Checklist (Quick Reference)

**Pre-Phase-5 Gate**
- [ ] Phase 3 complete (dashboard.html approved)
- [ ] Phase 4 complete (optional, if automation done)
- [ ] state.md updated through all prior phases
- [ ] Project owner identified (name, email, Slack)

**4 Documentation Files to Create**

**Architecture.md** - Data Flow & Components
- [ ] Data flow diagram (source → workflow? → SINK → queries → HTML)
- [ ] Component list (tables, workflow, SINK, queries, dashboard)
- [ ] Dependencies and refresh frequency
- [ ] Troubleshooting section

**Usage Guide.md** - How to Use Dashboard
- [ ] 1-2 sentence overview
- [ ] How to open (download, email, web server)
- [ ] KPIs with real values + interpretation
- [ ] Filters (options and effects)
- [ ] Charts descriptions
- [ ] Tips & tricks (export, share, spot-check)
- [ ] FAQs

**Runbook.md** - Operations & Troubleshooting
- [ ] Owner + backup owner (names, emails, Slack, phone)
- [ ] Daily health checks (workflow status, SINK freshness)
- [ ] Weekly maintenance (check logs, table growth, feedback)
- [ ] Troubleshooting (common issues + solutions)
- [ ] Emergency procedures
- [ ] Scheduled maintenance windows
- [ ] Real escalation contacts + phone numbers

**Access & Ownership.md** - Permissions & Change Management
- [ ] Owner/backup owner details (real names, not "contact admin")
- [ ] Access tiers (Tier 1: view only, Tier 2: operator, Tier 3: admin)
- [ ] How to request access
- [ ] Change management process (minor vs major)
- [ ] TD permissions by role
- [ ] Disaster recovery procedures
- [ ] Support SLA + response time

---

## ✅ Before You Proceed: Required Reads

**Before executing Phase 5 documentation creation, read these reference files:**
1. **`./references/template-architecture-md.md`** — Architecture.md template (if exists)
2. **`./references/template-usage-guide-md.md`** — Usage Guide.md template (if exists)
3. **`./references/template-runbook-md.md`** — Runbook.md template (if exists)
4. **`./references/template-access-ownership-md.md`** — Access & Ownership.md template (if exists)

These templates ensure consistent structure and cover all required sections (no generic "contact admin" placeholder language).

---

**Content Validation**
- [ ] Architecture.md: Project-specific (not template), actual table names, real costs
- [ ] Usage Guide.md: Real KPI values, actual filter options, real user workflows
- [ ] Runbook.md: Real owner names + phone, tested diagnostic commands
- [ ] Access & Ownership.md: Real people + roles (not "contact admin")

**Quality Gate**
- [ ] All 4 docs approved by owner
- [ ] Owner checked: data flow correct, permissions accurate, contacts current
- [ ] Ready for handoff

**Project Completion**
- [ ] Update state.md: "PROJECT COMPLETE"
- [ ] All 4 docs saved to shared location
- [ ] Share with stakeholders
- [ ] Training/onboarding using docs
- [ ] Claude engagement complete

---


## ⚠️ Blocking Phase 5 Gate

Before creating handoff documents, verify the Phase 5 section of `../references/execution-contract.md` and obtain explicit user selection. Do not treat Phase 5 as automatic after Phase 4.

## Phase 5 Specific Rules (In Addition to Universal Rules)

### Rule P5-1: Architecture.md Must Show Real Data Flow

Never generic — always specific to this project.

**Structure:**
```markdown
# Architecture: [Project Name] Dashboard

## Data Flow Diagram

```
Source Tables (Treasure Data)
    ↓
[Phase 2 Workflow (if applicable)] → SINK Tables
    ↓
Phase 3 Queries
    ↓
dashboard.html (self-contained)
```

## Components

### 1. Source Tables
- **Table:** [table_name]
  - Rows: [estimated count]
  - Refresh: [frequency, e.g., "daily at 2 AM"]
  - Last updated: [timestamp]

### 2. Phase 2 Workflow (if applicable)
- **Workflow Name:** [name]
- **Schedule:** [frequency, time, timezone]
- **Duration:** ~[Xm] per run
- **Output:** SINK tables (below)

### 3. SINK Tables (if applicable)
- **Table:** [project_name]_sink_[group]
  - Columns: [list]
  - Updated by: Workflow (scheduled)
  - Used by: Phase 3 queries

### 4. Dashboard Queries
- **Query 1:** [description]
  - Source: [SINK table or source table]
  - Aggregation: [e.g., "SUM(revenue) by region"]
  
- **Query 2:** [description]
  - Source: [table]
  - Aggregation: [...]

### 5. Dashboard HTML
- **File:** dashboard.html
- **Size:** [Xmb]
- **Data Inlined:** Yes (self-contained)
- **Deployment:** Copy to any web server or email directly
- **Browser Support:** Chrome, Firefox, Safari (modern versions)

## Dependencies

- ✓ Treasure Data account access
- ✓ Source tables exist and are populated
- ✓ (If Phase 2) Workflow running and SINK tables populated
- ✓ Network access to open dashboard.html

## Refresh Frequency

- Dashboard data is current as of: [last query run time]
- To refresh dashboard: [regenerate dashboard.html with latest data]
- Automated refresh: [only if Phase 2 workflow — state schedule]

---

## Troubleshooting

**Dashboard shows no data:**
→ Check: (1) SINK tables exist? (2) Workflow ran successfully? (3) Source data present?

**Dashboard loads slowly:**
→ Check: (1) File size (should be <5mb), (2) Browser resources, (3) Network latency

**Numbers don't match other reports:**
→ Check: (1) Time period filter (what date range?), (2) Dimension filter (what region/segment?), (3) Metric definition (same calculation?)
```

---

### Rule P5-2: Usage Guide Must Have Real Examples

Never generic — always use actual KPIs and filters from this project.

**Structure:**
```markdown
# Usage Guide: [Project Name] Dashboard

## Overview

This dashboard shows [1-2 sentences describing what it measures and audience].

**Last updated:** [timestamp]
**Refreshed:** [frequency, e.g., "Daily at 3 AM UTC"]

---

## How to Use This Dashboard

### 1. Open the Dashboard

- Desktop: Download `dashboard.html`, double-click to open
- Mobile: Open `dashboard.html` on any smartphone (Chrome/Safari)
- Share: Email the file or upload to shared drive

### 2. KPIs (Top of Dashboard)

The dashboard shows these key metrics:

**Total Revenue:** $[X]
- What it means: Sum of all revenue for the selected period and filters
- How to interpret: Trend up = growth, trend down = decline
- Related metric: Revenue by region (see chart below)

**Unique Customers:** [X]
- What it means: Number of distinct customers (deduplicated)
- How to interpret: Steady = retention, up = growth, down = churn
- Related metric: New customers (see chart below)

**Conversion Rate:** [X]%
- What it means: (Conversions / Sessions) × 100
- How to interpret: Industry benchmark is [Y]%
- Note: Includes all channels (web + mobile)

### 3. Filters

Use filters to slice the data:

**Region Filter:** Select one or more regions
- Options: [list: US, EU, APAC, etc.]
- Default: All regions
- Effect: Updates all charts below filter

**Date Range Filter:** Select start and end dates
- Default: Last 30 days
- Min/Max: [date range in data]
- Effect: Updates KPIs and all charts

**Product Category Filter:** Select one or more categories
- Options: [list: Electronics, Apparel, etc.]
- Default: All categories
- Effect: Updates revenue chart and conversion rate

### 4. Charts

**Revenue by Region (Line Chart)**
- What it shows: Daily revenue trend for each region
- How to use: Hover over line to see exact date/value
- Interpretation: Peaks = high-demand days, valleys = slow periods

**Customer Acquisition (Bar Chart)**
- What it shows: New customers by week
- How to use: Click legend to hide/show specific channels
- Interpretation: Wider bars = stronger acquisition

**Conversion Funnel (Table)**
- What it shows: Sessions → Leads → Customers (by stage)
- How to use: Sort by column (click header)
- Interpretation: Largest drop = biggest bottleneck

### 5. Tips & Tricks

**Export to CSV:**
- Tables: Right-click → Export as CSV
- Charts: Use browser print (Cmd/Ctrl+P) → "Save as PDF"

**Share a specific view:**
- Apply filters, then copy `dashboard.html` + send to colleague
- They will see the same dashboard (but filters reset on their copy)

**Spot-check numbers:**
- For exact values, query the database directly:
  ```sql
  SELECT SUM(revenue) FROM sales_revenue 
  WHERE date >= '2026-07-01' AND region = 'US'
  ```

---

## Common Questions

**Q: Why are my numbers different from [other report]?**
A: Likely cause: Different time period, different dimension filter, or different metric definition. Compare (1) date ranges, (2) filters applied, (3) metric calculation.

**Q: Can I download historical data?**
A: Yes. The dashboard shows the last 30 days by default. Extend the date range in the filter to go further back (up to [max_date]).

**Q: Can I add my own metrics?**
A: The dashboard is read-only (self-contained HTML). To add metrics, we'd need to regenerate it with new data. Contact [owner name].

**Q: Is this real-time?**
A: No. The dashboard data is current as of the last refresh ([last_refresh_time]). For real-time access, use [agent name] conversational agent (if available) or query Treasure Data directly.
```

---

### Rule P5-3: Runbook Must Have Real Names & Procedures

Never "contact your admin" — always specific owner name and escalation path.

**Structure:**
```markdown
# Runbook: [Project Name] Dashboard

## Overview

This runbook documents operational procedures for maintaining the dashboard.

**Owner:** [Name] ([email])
**Backup Owner:** [Name] ([email])
**Escalation:** [Team/Slack channel]

---

## Daily Operations

### Monitor Dashboard Health

**Check every morning (or via alert):**

1. Verify workflow ran successfully
   ```bash
   tdx wf show [project_name]-dashboard
   ```
   - Expected: Last attempt = yesterday
   - Status = SUCCESS
   
2. Verify SINK tables are fresh
   ```bash
   tdx query "SELECT MAX(date) FROM [project_name]_sink_metrics"
   ```
   - Expected: Yesterday's date (or latest data date)
   - If NULL or stale: Investigate workflow logs

3. Spot-check a KPI
   ```bash
   tdx query "SELECT SUM(revenue) FROM sales_revenue WHERE DATE(event_time) = CURRENT_DATE"
   ```
   - Compare against dashboard KPI
   - If 1% off or more: Investigate query

**If all healthy:** No action needed.
**If issue detected:** Go to Troubleshooting (below).

---

## Weekly Maintenance

**Every Monday:**

1. Review workflow execution history (last 7 days)
   ```bash
   tdx workflow:result show [project_name]-dashboard --limit 7
   ```
   - Any failures? → Go to troubleshooting
   - All SUCCESS? → Continue

2. Review SINK table growth
   ```bash
   tdx query "SELECT COUNT(*) FROM [project_name]_sink_metrics"
   ```
   - Growth reasonable (e.g., 7 new days)? → OK
   - No growth or excessive growth? → Investigate

3. User feedback
   - Check Slack channel for issues/requests
   - Any recurring questions? → Update Usage Guide

---

## Troubleshooting

### Issue: "Workflow did not run today"

**Diagnosis:**
```bash
# Check workflow status
tdx wf show [project_name]-dashboard

# Check last run logs
tdx workflow:result show [project_name]-dashboard
```

**Common causes:**
1. **Treasure Data was down** → Wait and re-run manually
2. **SQL error in workflow** → Check error message, fix SQL, redeploy
3. **Authentication failed** → Verify API key is valid

**Resolution:**
```bash
# Manually re-run workflow
tdx wf run [project_name]-dashboard

# Monitor progress
tdx workflow:result show [project_name]-dashboard --follow
```

**If still failing:** Escalate to [Team name] (see owner contact above).

---

### Issue: "Dashboard numbers are wrong"

**Diagnosis:**
1. Query the source table directly
   ```sql
   SELECT SUM(revenue) FROM sales_revenue 
   WHERE DATE(event_time) = '2026-07-22'
   ```

2. Compare against SINK table
   ```sql
   SELECT SUM(revenue) FROM [project_name]_sink_metrics 
   WHERE date = '2026-07-22'
   ```

3. Check if they match (exactly)

**Possible causes:**
- **Join fan-out:** SINK table has inflated numbers
- **Missing filter:** Source query missing WHERE clause
- **Data quality issue:** NULL values, duplicates
- **Stale dashboard:** Regenerate HTML to pick up latest data

**Resolution:**
1. If SINK mismatch: Rerun Phase 2 workflow
   ```bash
   tdx wf run [project_name]-dashboard
   ```
2. If source mismatch: Debug the workflow SQL (reach out to [owner])
3. Regenerate dashboard.html:
   ```bash
   node render.js  # Fetch latest data + rebuild HTML
   ```

---

### Issue: "Workflow is too slow / too expensive"

**Diagnosis:**
```bash
# Check workflow cost
tdx workflow:result show [project_name]-dashboard
# Look for "Query cost" in last run
```

**Common causes:**
- Query scans too much data (no partition pruning)
- Join on unindexed column
- Missing pre-aggregation

**Resolution:**
1. Add partition pruning to workflow SQL
   ```sql
   WHERE TD_TIME_RANGE(time, '{{start_time}}', '{{end_time}}')
   ```
2. Pre-aggregate before joins
3. Reduce retention period (e.g., keep last 90 days vs 1 year)

**If optimization unclear:** Escalate to [owner].

---

## Emergency Procedures

### "Dashboard is not updating (critical issue)"

**Immediate action:**

1. Check if Treasure Data is operational
   - Visit: https://status.treasuredata.com
   - If DOWN: Wait for service restore, no action needed

2. Manually trigger workflow
   ```bash
   tdx wf run [project_name]-dashboard
   ```

3. Monitor for completion
   ```bash
   tdx workflow:result show [project_name]-dashboard --follow
   ```

4. If workflow succeeds: Regenerate dashboard.html
   ```bash
   node render.js
   ```

5. If workflow fails: Check error logs and escalate

**Stakeholder communication:**
- Notify [Slack channel] of status
- Provide ETA for resolution
- Post update every 30 minutes

---

## Maintenance Windows

**Scheduled downtime for maintenance:**
- Thursdays 2-3 AM UTC (monthly)
- Workflow will not run during this time
- Dashboard will be stale (OK for 1 hour)

**Notification:** [Slack channel] (@channel) posted 24 hours in advance

---

## Contacts & Escalation

**For questions about:**

- **Dashboard usage** → [Owner name] (Slack: @[handle])
- **Workflow issues** → [Owner name] ([email])
- **Data quality** → [Data team] ([Slack channel])
- **Treasure Data account** → [Admin name] ([email])
- **Emergency escalation** → [Manager name] ([phone])
```

---

### Rule P5-4: Access & Ownership.md Must Name Real People

**Structure:**
```markdown
# Access & Ownership: [Project Name] Dashboard

## Project Owner

**Primary Owner:** [Full Name]
- Email: [email]
- Slack: @[handle]
- Availability: [timezone, work hours]
- Responsibilities: Maintains dashboard, approves changes, troubleshoots issues

**Backup Owner:** [Full Name]
- Email: [email]
- Slack: @[handle]
- Covers: Weekends, on-call rotation

---

## Access Tiers

### Tier 1: View Only (Read dashboard.html)

**Who:** [Role/Team] — e.g., "Sales team", "Executives"

**Can do:**
- ✓ Open dashboard.html in browser
- ✓ Filter by date/region/metric
- ✓ Export data to CSV
- ✓ Share the dashboard file with others

**Cannot do:**
- ✗ Modify dashboard or queries
- ✗ Access source data directly
- ✗ Change SINK table definitions
- ✗ Access Treasure Data console

**How to get access:** Email [owner] with use case

---

### Tier 2: Operator (Maintain workflow)

**Who:** [Role/Team] — e.g., "Data Engineering"

**Can do:**
- ✓ Regenerate dashboard.html
- ✓ Adjust workflow schedule
- ✓ Monitor workflow execution
- ✓ Debug query issues
- ✓ Update SINK table definitions

**Cannot do:**
- ✗ Delete source tables
- ✗ Change approval gates
- ✗ Modify dashboard architecture

**How to get access:** Email [owner] with justification

---

### Tier 3: Administrator (Full control)

**Who:** [Name] — Only project owner

**Can do:**
- ✓ Full access to all components
- ✓ Modify architecture
- ✓ Add/remove users
- ✓ Delete SINK tables / workflows

**Request changes:** File issue with [owner] and justification

---

## Change Management

**Minor changes (filter, date range, new metric to existing dashboard):**
- Notify: [owner]
- Approval: [owner] (same-day typical)
- Deployment: [owner] or designee
- Rollback: Simple (rebuild dashboard.html)

**Major changes (new data sources, new workflow):**
- Proposal: Write 1-page summary (data, cost, risk)
- Approval: [owner] + [manager] sign-off
- Implementation: 2-week sprint
- Testing: QA in staging before production

---

## Requesting Changes

**To request a change to the dashboard:**

1. **Email [owner]** with:
   - What: New metric? New filter? Different data?
   - Why: Business impact? Use case?
   - Timeline: When needed?

2. **Owner responds** with:
   - Feasibility: Is it technically possible?
   - Effort: How long will it take?
   - Cost: Any additional compute/storage?
   - Timeline: When will it be ready?

3. **If approved:**
   - Implementation starts
   - Owner provides ETA
   - Testing phase
   - Deployment + validation

4. **If blocked:**
   - Owner explains constraint
   - Offers alternative solution if applicable

---

## Permissions in Treasure Data

The following permissions are required to operate this dashboard:

| Role | Permission | Scope |
|------|-----------|-------|
| Owner | CREATE TABLE | [database] |
| Owner | SELECT | all tables |
| Operator | SELECT | [database] |
| Operator | UPDATE | SINK tables |
| User | SELECT | SINK tables only |

**To grant permissions:**
```bash
# Owner grants SELECT on SINK tables to Operator
tdx user:grant [username] SELECT [database].[table_name]
```

---

## Disaster Recovery

**If source tables are deleted:**
1. Restore from backup (Treasure Data SLA: [N] days)
2. Notify [owner]
3. Workflow will fail until restored
4. Dashboard will show stale data (last successful run)

**If SINK tables are deleted:**
1. Rerun Phase 2 workflow
2. SINK tables are recreated with full historical backfill
3. Time: ~[X] minutes

**If dashboard.html is lost:**
1. Regenerate from source queries
   ```bash
   node render.js
   ```
2. Time: <5 minutes

---

## Support & Questions

**For urgent issues:**
- Slack: @[owner] (real-time)
- Email: [email] (within 2 hours)
- Phone: [phone] (escalation only)

**For non-urgent questions:**
- Email: [email]
- Response time: 24 hours

**For feature requests:**
- File on [Jira/Linear/GitHub]
- Roadmap reviewed: Monthly
```

---

## Phase 5 Pre-Flight Checklist

**Before starting Phase 5, verify:**

### Prerequisites
- [ ] Phase 3 dashboard is complete and approved
- [ ] Phase 2 workflow completed (if applicable)
- [ ] state.md up-to-date
- [ ] Project owner identified (name, email, Slack)
- [ ] All real names/emails/contacts collected

### Documentation Readiness
- [ ] Architecture diagram drawn (data flow)
- [ ] Workflow details documented (schedule, cost, SINK tables)
- [ ] Usage guide written with real KPIs and examples
- [ ] Runbook procedures tested (troubleshooting steps verified)
- [ ] Owner/escalation contacts finalized

---

## Phase 5 Decision Tree

```
START Phase 5: Handoff Documentation
    ↓
Is Phase 3 dashboard approved?
    NO  ↓ → ERROR: Cannot proceed without Phase 3 complete
    YES ↓ → Continue
    ↓
Collect real information:
  ├─ Owner name/email/Slack
  ├─ Backup owner
  ├─ Escalation contacts
  ├─ Workflow details (if Phase 2)
  ├─ SINK table names (if Phase 2)
  └─ Real KPI values + examples
  ↓
Create 4 markdown files:
  ├─ 1. Architecture.md (data flow, components)
  ├─ 2. Usage Guide.md (filters, KPIs, tips)
  ├─ 3. Runbook.md (operations, troubleshooting)
  └─ 4. Access & Ownership.md (contacts, permissions)
  ↓
Review + finalize with owner
    ↓
Save to local folder (for sharing)
    ↓
Append Phase 5 results to state.md
    ↓
END Phase 5
```

---

## Phase Progression Gate (Final — Project Complete)

**⚠️ CRITICAL: Before marking project COMPLETE, verify:**

- [ ] Phase 3 marked COMPLETE in state.md
- [ ] All 4 documentation files created:
  - [ ] Architecture.md (data flow documented)
  - [ ] Usage Guide.md (how to use documented)
  - [ ] Runbook.md (operations documented)
  - [ ] Access & Ownership.md (permissions documented)
- [ ] Owner approved all 4 docs
- [ ] state.md appended with Phase 5 results:
  - 4 documentation files listed
  - Owner approval captured
  - "PROJECT COMPLETE" status
  - Final notes

**If ANY item is missing or unapproved:**
> "Cannot close project. Phase 5 incomplete.
> Missing/Unapproved: [specific item]
> Please complete before marking project as done."

**Only after all items verified:**
- Append "PROJECT COMPLETE" to state.md
- Handoff complete
- Claude engagement ends

---

## After Phase 5 Completes

**All 4 documentation files created:**
```
✓ Architecture.md — Data flow documented
✓ Usage Guide.md — How to use documented
✓ Runbook.md — Operations documented
✓ Access & Ownership.md — Contacts documented

Handoff ready for:
  • Team onboarding
  • Knowledge transfer
  • Future support
  • Change management
```

**Project is now complete and production-ready:**
```
✅ Phase 1: Requirements validated ✓
✅ Phase 2: Workflow deployed (optional) ✓
✅ Phase 3: Dashboard built & approved ✓
✅ Phase 4: Automation deployed (optional) ✓
✅ Phase 5: Documentation complete ✓

Project ready for:
  • Stakeholder handoff
  • Team training
  • Ongoing operations
```

---

**Version:** 1.0.0
**Last Updated:** 22 July 2026
**Load Order:** 1.5 (read after Phase 1-4 INSTRUCTIONS.md)
