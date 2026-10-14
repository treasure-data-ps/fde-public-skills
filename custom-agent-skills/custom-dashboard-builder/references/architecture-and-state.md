# FDE TAIS Dashboard Builder — Pipeline Architecture & state.md Pattern

## 5-Phase Pipeline Overview

```
Phase 1: Requirements + Data Discovery
  ↓
  ├─→ Score 0-2, OR skip_workflow=true
  │   ↓
  │   Phase 3: Build Dashboard (direct)
  │
  ├─→ Score 3
  │   ↓
  │   [Ask user: Phase 2 or Phase 3?]
  │
  └─→ Score 4-6, AND skip_workflow≠true
      ↓
      Phase 2: Deploy Workflow (optional but recommended)
      ↓
      Phase 3: Build Dashboard
      ↓
      Phase 4: Automate & Deploy (optional — Track A/B)
      ↓
      Phase 5: Handoff Documentation (optional)
```

### When Each Phase Runs

| Phase | Mandatory? | When | Output |
|-------|-----------|------|--------|
| **1** | ✅ Always | First | Dashboard Complexity Score (0-6) + path decision + `state.md` created |
| **2** | 🟡 Optional | If score 4-6 AND `skip_workflow ≠ true` | Pre-aggregated SINK tables + workflow schedule |
| **3** | ✅ Always | After 1 or 2 | Approved interactive `dashboard.html` + `generate-data.js` |
| **4** | 🟡 Optional | After 3 if user wants automation | Reusable skill (Track A) or Foundry agent (Track B) |
| **5** | 🟡 Optional | After 3 or 4 if user wants handoff docs | 4 markdown files for team maintenance |

---

## The `state.md` Append-Only Pattern

Every project has **one** local file: `./<project-name>/state.md`

This file is the **single source of truth** for cross-phase context. It is **append-only** — never edited, only appended to:

### How It Works

1. **Phase 1 writes the first section:**
   ```markdown
   # travel-dashboard — Dashboard Project State

   ## Phase 1 — Session Setup (2026-07-22)
   - Project Slug: travel-dashboard
   - Business Goal: Track weekly booking volume and ARPU by destination
   - Platform: Treasure Work
   - Data Source Type: Raw/Transactional
   - skip_workflow: false

   ## Phase 1 — Requirements
   - Metrics: Bookings (count), Revenue (SUM), ARPU (SUM/COUNT)
   - Dimensions: Destination, Region, Customer Segment
   - Filters: Dashboard-level: Date range, Region
   - Date range: Last 90 days, UTC
   - Timezone: UTC
   - Benchmark Values: "4,200 bookings/week, $450K revenue, $107 ARPU"

   ## Phase 1 — Data Discovery
   - Database.Table: bookings_db.transactions
   - Time column: event_time (business event, timestamp)
   - Confirmed metrics: [list]
   - Confirmed dimensions: [list]
   - Data Quality Gate: PASS (all 12 checks)

   ## Phase 1 — Dashboard Complexity Score & Path
   - Q1 (Frequency): 2
   - Q2 (History): 2  
   - Q3 (Audience): 2
   - Total: 6/6
   - Path: Workflow (recommended)
   ```

2. **Phase 2 (if run) appends its section at the bottom:**
   ```markdown
   ## Phase 2 — Workflow Deployment (2026-07-23)
   - Workflow project: travel_dashboard_wf
   - SINK database: dashboard_aggregates
   - SINK tables: agg_bookings_by_destination, agg_bookings_by_region
   - Schedule: 0 8 * * * (daily at 8 AM UTC)
   - Incremental mode: 1-day lookback
   ```

3. **Phase 3 appends:**
   ```markdown
   ## Phase 3 — Dashboard Build (2026-07-24)
   - Dashboard file: dashboards/dashboard.html
   - Queries: Pulling from SINK tables (agg_*)
   - Filters applied: region_filter (dashboard-level), date_range_picker
   - Performance: 100ms query, <2MB HTML
   - Status: User-approved ✓
   ```

4. **Phase 4 (if run) appends:**
   ```markdown
   ## Phase 4 — Automation (2026-07-25)
   - Track A (Skill): skills/travel_dashboard_skill/SKILL.md
   - Status: Packaged and tested ✓
   ```

5. **Phase 5 (if run) appends:**
   ```markdown
   ## Phase 5 — Handoff (2026-07-26)
   - Docs: docs/architecture.md, docs/usage_guide.md, docs/runbook.md, docs/access_ownership.md
   - Status: Shared with team ✓
   ```

### The Rule

- **Never rewrite prior sections** — only append new dated blocks at the end
- **Every phase reads the entire file** — to understand prior decisions
- **Future sessions resume by reading** `state.md` → jumping to "Next action" at the bottom
- **No external context needed** — `state.md` is self-contained, git-tracked, and portable

---

## Resuming an Existing Project

If `./<project-name>/state.md` exists:

1. **Read the entire file top-to-bottom**
2. **Find the last section** (the most recent phase)
3. **Check the "Next action"** field at the bottom — it says which phase to run
4. **Resume at that phase** — DO NOT re-run earlier phases, even if data seems incomplete

Example: If `state.md` shows:
```
## Phase 1 — Dashboard Complexity Score & Path
...
Path: Workflow (recommended)

## Next action
Run Phase 2: Deploy workflow for dashboard_aggregates, schedule = daily @ 8 AM
```

Then the next person resumes at Phase 2, not Phase 1.

---

## When to Skip Phases

**Phase 2 (Workflow):**
- If `skip_workflow = true` (pre-aggregated data) → jump straight from Phase 1 to Phase 3
- If score 0-2 → ask user, then decide (common: skip to Phase 3 for quick prototypes)
- If score 3 → ask user: "Quick build now (Phase 3), or scheduled refresh (Phase 2 → Phase 3)?"

**Phase 4 (Automate & Deploy):**
- If user doesn't need a reusable skill or Foundry agent → skip to Phase 5
- If user doesn't need handoff docs → close engagement entirely

**Phase 5 (Handoff):**
- If this is a one-off dashboard with no ongoing support needed → skip to close

---

## Architecture: Single-Session vs Multi-Session

**Single-session:**
- User starts Phase 1, we route through all needed phases, and finish in one chat
- Everything lives locally — one project folder, one `state.md`, one final `dashboard.html`

**Multi-session:**
- User starts Phase 1 in session A
- User resumes in session B: "I'm continuing the travel-dashboard project"
- Session B reads the same `state.md`, resumes at the stated next action
- `state.md` grows longer each session

Both patterns work because `state.md` is the bridge.

---

## No External Dependencies

- **No Confluence** — all docs live in the project folder
- **No git branching** — working on one local `./<project-name>/` directory
- **No external APIs** — skill is self-contained with references/ subfolder at each level
- **No live dashboards** — everything is generated fresh, not fetched from an existing system
- **HTML Client only** — no server, no hosting required; the `.html` file is portable and offline-ready

