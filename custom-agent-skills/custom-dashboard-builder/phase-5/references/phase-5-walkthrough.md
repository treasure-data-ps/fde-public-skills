---
name: shared-phase-5-handoff-lite
description: |
  Step-by-step Phase 5 workflow for handing off validated dashboards. Creates 4 local markdown documentation files: Dashboard Architecture, Usage Guide, Runbook, and Access & Ownership. Invoked after Phase 3 dashboard validation (and optional Phase 4 automation/agent deployment). Lite version — no Confluence, no git.
---

# Phase 5: Handoff Documentation (Lite)

**Entry Point:** After Phase 3 (and optional Phase 4)
**Prerequisite:** Phase 3 deliverable (validated interactive dashboard)
**Output:** 4 local markdown files saved in `./<project-name>/docs/`

---

## Phase 5 Overview

After your dashboard is validated and working, create 4 documentation files so you (and anyone else who picks this up) can use, maintain, and support the dashboard independently. These are written locally as markdown files and shared however you prefer (email, Slack, Google Docs, etc.).

---

## ⚠️ Step 5-0: Extract Phase 1-4 Configuration (MANDATORY — 10 min)

**Before creating any documentation, verify all Phase 1-4 decisions are locked.**

Open `state.md` and locate:

| Phase | Field | Phase 5 Use |
|---|---|---|
| **1 (Stage A)** | Dashboard Name, Project Slug | File names, headers |
| **1 (Stage A)** | Core Metrics (5-10 KPIs) | Architecture doc, metrics table |
| **1 (Stage A)** | Dimensions & Filters | Usage Guide, filter documentation |
| **1 (Stage A)** | Date Range & Timezone | Usage Guide, timezone callout |
| **1 (Stage A)** | Target Users & Sharing Model | Access & Ownership, audience |
| **1 (Stage A)** | Compliance / Sensitivity | Access & Ownership, security notes |
| **1 (Stage B)** | Confirmed Database, Tables, Columns | Architecture doc, data source section |
| **1 (Stage B)** | Rendering | Always HTML Client — no engine rationale needed |
| **2** | Workflow Project Name, SINK DB | Architecture doc, maintenance section (only if Phase 2 ran) |
| **3** | Dashboard Parameters (queries, filters, performance) | Architecture doc, technical specs |
| **4** | Track A Skill / Track B Agent (if deployed) | Architecture doc, reusability note |

### Extraction Checklist:

```
From state.md:

Session Setup:
  [ ] Project name: _____
  [ ] Dashboard solution name: _____

Business Requirements (Phase 1, Stage A):
  [ ] Metrics (count): _____ KPIs documented
  [ ] Dimensions & filters: documented
  [ ] Date range & timezone: _____
  [ ] Historical depth: _____ days
  [ ] Target users & sharing: documented
  [ ] Compliance flagged: [ ] None [ ] Yes: _____

Data Discovery (Phase 1, Stage B):
  [ ] Database confirmed: _____
  [ ] Tables confirmed: count = _____
  [ ] Rendering: HTML Client (fixed, no choice made)

Workflow (Phase 2, if run):
  [ ] Workflow project: _____
  [ ] SINK database: _____

Dashboard Build (Phase 3):
  [ ] Query performance baseline: _____

Automation (Phase 4, Track A):
  [ ] Skill extracted: [ ] No [ ] Yes

Agent (Phase 4, Track B):
  [ ] Agent deployed: [ ] No [ ] Yes
```

**If ANY field is missing or "TBD":** A prior phase is incomplete — do not proceed until all artifacts are finalized.

---

## Step 5b-pre: Approval Gate

Present the plan and wait for explicit confirmation.

```
AskUserQuestion:
  header: "Phase 5 plan"
  question: "Ready to create 4 documentation files for <project-name>?

  Files to create locally:
  - ./<project-name>/docs/architecture.md     ← share with your team/stakeholders
  - ./<project-name>/docs/usage_guide.md      ← share with your team/stakeholders
  - ./<project-name>/docs/runbook.md          ← maintainer-only
  - ./<project-name>/docs/access_ownership.md ← maintainer-only"
  options:
    - label: "Yes, create all 4 files (Recommended)"
      description: "Proceed with the plan above"
    - label: "Adjust file names first"
      description: "I want to rename one or more files"
    - label: "Skip Phase 5 for now"
      description: "Come back to documentation later"
```

---

## Step 5b: Create 4 Documentation Files

Create the folder and write all 4 files locally:

```bash
mkdir -p ./<project-name>/docs
```

---

### File 1: Dashboard Architecture

**Path:** `./<project-name>/docs/architecture.md`
**Label:** User-facing (share with your team/stakeholders)

**Content to include:**
- Dashboard name and business purpose
- Data sources (database/tables)
- Rendering approach (always HTML Client — single portable file)
- Update frequency (real-time vs scheduled workflow)
- Key metrics and dimensions tracked
- Data retention period

**Template:**
```markdown
# <Dashboard Name> Dashboard Architecture

## Overview
<Brief description of what this dashboard provides and why it was built>

## Data Source
- **Database:** <database_name>
- **Fact table(s):** <table_names>
- **Query method:** <Direct query | Scheduled workflow (SINK table)>
- **Refresh schedule:** <Daily at Xam UTC | Real-time | Manual>

## Dashboard Engine
- **Type:** HTML Client — single portable `dashboard.html` with data inlined at build time
- **Interactive elements:** <date range picker, filters, drill-down, etc.>

## Key Metrics
<List each metric with its definition>
- **<Metric 1>:** <formula>
- **<Metric 2>:** <formula>

## Filters & Dimensions
<List each filter>
- **<Filter 1>:** <column> — Default: <default value>
- **<Filter 2>:** <column> — Default: <default value>

## Data Retention
- Historical data available for: <X days/months/years>
- Timezone: <UTC | PST | JST | etc.>

## Workflow (if applicable)
- **Workflow project:** <td_project_name>
- **SINK database:** <sink_database>
- **Schedule:** <cron or human-readable schedule>

## Automation (if applicable)
- **Reusable skill:** <skill_name or N/A>
- **AI agent:** <agent_name or N/A>

## Maintenance Contact
- **Dashboard owner:** <name>
- **Support channel:** <Slack channel or email>
```

---

### File 2: Usage Guide

**Path:** `./<project-name>/docs/usage_guide.md`
**Label:** User-facing (share with your team/stakeholders)

**Content to include:**
- How to access the dashboard
- How to use each filter
- How to interpret each metric
- How to export data (if applicable)

**Template:**
```markdown
# <Dashboard Name> Usage Guide

## Accessing the Dashboard
<Link to dashboard.html or instructions to find/open it>

## Using Filters

### Date Range
<Default: last X days. Supports custom range picker: yes/no>

### <Filter 2>
<Description of values, default, and what it controls>

### <Filter N>
<Description of values, default, and what it controls>

## Key Metrics Explained

- **<Metric 1>:** <plain-language definition, e.g. "Count of unique customers who placed an order in the selected period">
- **<Metric 2>:** <plain-language definition>

## Date & Timezone Notes
All dates shown in <timezone>. Historical data goes back <X days/months>.

## Exporting Data
<If export is supported: explain how. If not: state "Export not available in this version.">

## Common Questions
**Q: Why does the total not match my other report?**
A: This dashboard <filters, exclusions, or scope that might cause discrepancy>.

**Q: How fresh is the data?**
A: Data refreshes <schedule>. The most recent data shown is from <lag description>.
```

---

### File 3: Runbook

**Path:** `./<project-name>/docs/runbook.md`
**Label:** Maintainer-only

**Content to include:**
- Regular maintenance tasks
- How to update the dashboard when data schema changes
- Common failure modes and resolution steps
- Re-deployment instructions

**Template:**
```markdown
# <Dashboard Name> Runbook

## Overview
Dashboard queries `<database>.<table>`. Built with HTML Client (single portable `dashboard.html`).

## Regular Maintenance

### Weekly
- [ ] Verify dashboard loads and renders correctly
- [ ] Check data freshness: `SELECT MAX(<date_col>) FROM <database>.<table>`

### Monthly
- [ ] Review query performance (should be < <baseline_ms>ms)
- [ ] Check for schema changes in source tables

## Updating the Dashboard

### Adding a New Metric
1. Confirm column exists: `tdx describe <database>.<table>` (or `tdx describe <table> --in <database>`)
2. Update `generate-data.js` query or `dashboard.html` widget
3. Test with sample data
4. Re-run `generate-data.js` and reopen `dashboard.html` to confirm

### Changing Filter Behavior
1. Edit filter logic in `dashboard.html`
2. Test all filter combinations
3. Redistribute the updated `dashboard.html`

## Common Issues

### "No data returned"
```sql
-- Check data freshness
SELECT MAX(<date_col>) FROM <database>.<table>;
-- Verify permissions
tdx describe <database>.<table>
```

### "Dashboard is slow"
```sql
-- Check query performance
EXPLAIN <query>;
```
- Consider narrowing date range or adding WHERE clauses

## Re-deployment

```bash
# Regenerate data and rebuild the dashboard
node ./<project-name>/dashboards/generate-data.js
# Open ./<project-name>/dashboards/dashboard.html to verify
```

## Escalation
- Data quality issues → data platform team
- Performance issues → infrastructure team
- Feature requests → start a new engagement at Phase 1
```

---

### File 4: Access & Ownership

**Path:** `./<project-name>/docs/access_ownership.md`
**Label:** Maintainer-only

**Content to include:**
- Dashboard owner and backup
- Primary stakeholders
- Support channel and expectations
- Escalation path

**Template:**
```markdown
# <Dashboard Name> Access & Ownership

## Ownership
- **Dashboard Owner:** <name>
- **Backup Owner:** <backup name>
- **Engagement Date:** <YYYY-MM-DD>

## Access
- **Primary users:** <audience from Phase 1>
- **Access method:** <shared file, internal link, Treasure AI Studio skill, etc.>
- **User count estimate:** <N users>

## Support & Questions
- **Quick questions:** <Slack channel or email>
- **Feature requests:** <Slack channel or ticket system>
- **Response time expectation:** <24h for non-critical>

## Dashboard Changes
To request updates:
1. Contact via <support channel> with description
2. Owner provides an estimate
3. Update delivered within <agreed timeline>

## Escalation Path
- **L1 — Dashboard questions:** <Slack channel> (same day)
- **L2 — Data accuracy issues:** Data platform team
- **L3 — Platform issues:** Infrastructure team

## Compliance Notes
<Any PII, data sensitivity, or regulatory notes from Phase 1 Stage A Step 1l — or "None">
```

---

## Step 5c: Update state.md

Append a Phase 5 block to `state.md`:

```markdown
## Phase 5 — Handoff Documentation (<YYYY-MM-DD>)

### Documentation Files
- Architecture: ./<project-name>/docs/architecture.md
- Usage Guide: ./<project-name>/docs/usage_guide.md
- Runbook (maintainer-only): ./<project-name>/docs/runbook.md
- Access & Ownership (maintainer-only): ./<project-name>/docs/access_ownership.md

### Status
✅ Phase 5 complete — engagement closed
```

---

## Step 5d: Share the Docs

Share the two user-facing files however is most convenient:

**Example message:**
```
Hi team,

Your [Dashboard Name] dashboard is live! Here's the documentation:

📐 Architecture (what it is + how it was built): [attached or linked]
📊 Usage Guide (how to use it): [attached or linked]
💬 Questions? [Slack channel or email]
```

**Share only:**
- `architecture.md` (or rendered version)
- `usage_guide.md` (or rendered version)

**Keep maintainer-only:**
- `runbook.md`
- `access_ownership.md`

---

## Phase 5 Deliverables

- ✅ 4 local markdown files created under `./<project-name>/docs/`
- ✅ `state.md` appended with Phase 5 block
- ✅ User-facing docs shared

---

## After Phase 5: Ongoing Support

**Weekly (or as needed):** Monitor support channel, address data quality or performance issues.
**Monthly:** Review usage, update runbook with new common issues.
**Quarterly:** Assess enhancements — if major changes requested, start new engagement at Phase 1.

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team

### Deployment: Just Share the File

**No deployment infrastructure needed.**

Since `dashboard.html` is self-contained:

1. **Development:** User develops locally
2. **Testing:** User shares `dashboard.html` with stakeholders
3. **Production:** Same file used in production (no changes)

**Distribution options:**
- Email the file
- Store in shared drive (Google Drive, Dropbox, etc.)
- Version control (GitHub, GitLab — commit as binary)
- Knowledge base/wiki (attach HTML file)
- Embed in Confluence page (upload as attachment)

**No deployment pipeline needed** — the file IS the deployment artifact.

---

