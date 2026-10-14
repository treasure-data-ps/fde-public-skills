---
name: phase-2-instructions
description: Phase 2 specific instructions for workflow deployment and SINK table creation
priority: HIGH
load_order: 1.2
---

# Phase 2 Instructions — Workflow Deployment

**Read this BEFORE `./SKILL.md`.**

**Phase 2 is OPTIONAL and only for Score 4-6 (or user override).**

---

## Phase 2 Goal

Deploy a scheduled Treasure Data workflow that:
- Runs on a defined schedule (daily/weekly/custom)
- Pre-aggregates metrics into SINK tables
- Provides optimized tables for Phase 3 dashboard queries

**Deliverable:** 
- SINK tables created and populated
- Workflow deployed and validated
- state.md appended with Phase 2 results

---

## Pre-Execution Validation (Checkpoint)

**Cannot execute Phase 2 without validating:**

From `state.md` Phase 1 section, verify:
- ✅ Phase 1 marked ✅ Complete
- ✅ Time column documented (is it still non-nullable?)
- ✅ Join keys tested (cardinality check documented)
- ✅ Dashboard Complexity Score ≥ 4 (or user override recorded)
- ✅ User approved Workflow path (approval recorded)

**Runtime validation before proceeding:**
```bash
# Verify Phase 1 requirements still valid
tdx describe <SOURCE_DB>.<time_column_table>
# Verify time column exists and is non-nullable

# Verify SINK database exists
tdx databases | grep <SINK_DB>
```

**If ANY validation FAILS:**
→ STOP: "Prerequisite validation failed: [reason]"
→ User action: Go back to Phase 1, update state.md, or re-run validation

---

## Quick Checklist (Quick Reference)

**Pre-Phase-2 Gate**
- [ ] Phase 1 complete (state.md saved with Stage A/B)
- [ ] Dashboard Complexity Score 4-6 OR user chose Workflow at score 3
- [ ] SINK database confirmed
- [ ] Workflow project name decided

**Workflow Deployment Steps**
- [ ] 2a: Copy workflow template
- [ ] 2b: Configure input_params.yaml (databases, schedule, date range)
- [ ] 2c: Build queries from state.md (verify metrics/dimensions)
- [ ] 2d: Configure datamodel (if applicable)
- [ ] 2e: Review configuration, run --dry-run
- [ ] 2f: Deploy workflow, verify SINK tables created
- [ ] 2g: Validate SINK output (metrics match, performance < 1s)
- [ ] 2h: Set incremental strategy (if applicable)

**Quality Gate (Before Phase 3)**
- [ ] All Stage B metrics reproduced in SINK
- [ ] Query performance acceptable (SINK < 1s)
- [ ] SINK schema documented in state.md
- [ ] No data validation errors

**Handoff to Phase 3**
- [ ] Update state.md: "Phase 2 — Complete"
- [ ] SINK table info documented (names, columns)
- [ ] Ready for Phase 3: Build Dashboard from SINK

---

---

## ✅ Before You Proceed: Required Reads

**Before executing Phase 2 workflow deployment (step 2a), read these reference files:**
1. **`./references/sink-architecture-patterns.md`** — SINK table design patterns and aggregation strategies
2. **`./references/workflow-setup-configure.md`** — Workflow configuration best practices

These files establish SINK table structure and workflow patterns to prevent fan-out aggregation errors and query performance issues.

---


## ⚠️ Blocking Phase 2 Gate

Before any workflow, SINK, or physical-object action, verify the Phase 1 section of `../references/execution-contract.md`. The dry-run must complete and be reviewed before approval. Only a case-insensitive response matching `YES, APPROVE [ACTION]` unlocks creation; any other response re-opens the gate.

## Phase 2 Specific Rules (In Addition to Universal Rules)

### Rule P2-0: Dry-Run First (Before Approval)

**⚠️ CRITICAL: CANNOT request approval without showing dry-run output first.**

**Step 1: Run dry-run BEFORE presenting approval template**

```bash
# Show user what WILL happen (no actual creation)
tdx wf run [workflow_name] --dry-run
```

**Step 2: Present dry-run output to user**

Include in presentation:
- ✓ What tasks will run (task graph)
- ✓ What queries will execute (which SQL)
- ✓ What SINK tables will be created (names, schemas)
- ✓ Estimated duration per run
- ✓ Estimated query cost
- ✓ Schedule start time
- ✓ Frequency (daily/weekly/etc)

**Example:**
```
Dry-run shows:
  Task 1: aggregate_revenue.sql
    - Will read from: sales_events
    - Will write to: project_name_sink_revenue
    - Estimated rows: 365 (one per day for 1 year)
  
  Task 2: aggregate_customers.sql
    - Will read from: customers
    - Will write to: project_name_sink_customers
    - Estimated rows: 1,200,000
  
  Total cost per run: ~$2.50
  Total storage (incremental): ~500 MB/month
  Schedule: Daily at 02:00 UTC
```

**Step 3: Ask user: "Does this match your expectations?"**

- If NO → Adjust plan (different schedule, different metrics, etc.)
- If YES → Proceed to approval template (Rule P2-1)

**Why:** Dry-run lets user see exactly what will happen BEFORE committing. Prevents surprises.

---

### Rule P2-1: Approval Gate — SINK Table Creation (ENFORCEMENT)

**⚠️ CRITICAL: CANNOT create SINK tables without explicit user approval.**

**Step 1: Present approval template (COPY/PASTE exactly):**

```
📋 Ready to create SINK tables in Treasure Data:

Database: [database_name]

SINK Tables:
  • [project_name]_sink_[metric_group_1]
  • [project_name]_sink_[metric_group_2]
  • [project_name]_sink_[metric_group_3]

Workflow:
  • Name: [workflow_name]
  • Schedule: [e.g., "Daily at 02:00 UTC"]
  • Duration: ~[Xm] per run

💰 Cost Impact:
  • Query cost: ~$X per run
  • Storage cost: ~$X per month (tables)
  • Total estimated: $X per month

⚠️ This CANNOT be easily undone. Tables will start populating immediately upon deployment.

To approve, please type exactly: YES, APPROVE SINK TABLE CREATION FOR [PROJECT_SLUG]
(not just "yes" — type the full phrase)
```

**Step 2: Wait for response**
- If user types: "YES, APPROVE SINK TABLE CREATION FOR [PROJECT_SLUG]" → Proceed ✓
- If user types: "NO" or "REVIEW" or anything else → **STOP immediately** ✗

**Step 3: If NO or REVIEW**
- Do not create anything
- Ask explicitly: "What would you like to change?"
- Gather feedback (e.g., different schedule, fewer tables, lower cost)
- Adjust plan and re-present approval template
- Repeat until explicit YES approval

**Step 4: If user says "just do it anyway"**
Respond:
> "I cannot proceed without explicit approval. SINK tables create real costs (storage + compute) and have real consequences (data starts flowing immediately). This cannot be easily undone.
>
> Please type exactly: YES, APPROVE SINK TABLE CREATION FOR [PROJECT_SLUG]
>
> Or tell me what to adjust so you can approve."

**Why:** SINK tables are real costs and real consequences. Accidental deployment = data flowing, compute charges, storage costs — hard to undo.

---

### Rule P2-2: Join Validation (MUST complete before Phase 2)

From Phase 1, you should have identified all join keys. **Validate before deployment:**

- [ ] For each join, test cardinality:
  ```sql
  SELECT COUNT(DISTINCT join_key) FROM table_a;
  SELECT COUNT(DISTINCT join_key) FROM table_b;
  -- Counts should match (within 5%)
  ```

- [ ] Check column types are identical:
  ```bash
  tdx describe <db>.table_a
  tdx describe <db>.table_b
  # join_key column type must match
  ```

- [ ] If cardinality mismatch, determine pre-aggregation strategy:
  ```sql
  -- Pre-aggregate many-side BEFORE join
  SELECT SUM(agg.total) FROM table_a a
  JOIN (
    SELECT join_key, SUM(amount) AS total FROM table_b GROUP BY join_key
  ) agg ON a.join_key = agg.join_key
  ```

**Why:** Invalid joins cause silent data inflation. Phase 2 is the right place to test and bake in the pre-aggregation.

---

### Rule P2-3: Time Column Must Be Present & Non-Nullable

- [ ] Confirmed from Phase 1: time column identified
- [ ] Time column must be non-nullable in source table
- [ ] If nullable, flag as data quality issue — may require fallback logic
- [ ] Workflow uses this column for incremental loading

**Example (Phase 2 workflow):**
```yaml
scheduling:
  frequency: daily
  time_column: event_time  # MUST be non-nullable
  backfill_start: 2026-01-01
```

---

### Rule P2-4: SINK Table Naming Convention

SINK table names MUST follow this pattern:

**`<project_name>_sink_<metric_group>`**

Where:
- `project_name` = lowercase, hyphens, derived from project name (e.g., "sales-dashboard" → "sales_dashboard")
- `metric_group` = lowercase, hyphens, logical grouping (e.g., "revenue", "pipeline", "customers")

**Examples:**
- `sales_dashboard_sink_revenue`
- `sales_dashboard_sink_pipeline`
- `sales_dashboard_sink_customers`

**Why:** Phase 3 dashboard queries reference these exact names. Misnamed tables = no data in dashboard.

---

### Rule P2-4a: Fan-Out Detection (REQUIRED BEFORE SINK DESIGN)

**⚠️ CRITICAL: Check for 1-to-many join fan-out that will overcount metrics.**

For every join in Phase 2 SQL:

1. **Identify the join relationship:** Is it 1-to-1, 1-to-many, many-to-many?
2. **Check if it affects COUNT DISTINCT:**
   - If joining `orders (1) ←→ order_items (many)`, COUNT DISTINCT customer_id will overcount
   - If joining `users (1) ←→ sessions (many)`, COUNT DISTINCT user_id will overcount

3. **Test cardinality:**
```sql
-- Check join fan-out
SELECT COUNT(DISTINCT order_id), COUNT(*) 
FROM orders o 
JOIN order_items oi ON o.order_id = oi.order_id;

-- If COUNT(DISTINCT) < COUNT(*), there's a 1-to-many join
```

4. **If fan-out detected:**
   - ❌ Do NOT pre-aggregate COUNT DISTINCT in multi-dimension SINK
   - ✅ DO query source at dashboard build time (Pattern: `querySrc()` function)
   - ✅ Or create separate date-only SINK for COUNT DISTINCT

**Capture in state.md:**
```yaml
### Join Fan-Out Analysis

| Source Join | Type | COUNT Impact | Solution |
|--|--|--|--|
| orders ← order_items | 1-to-many | Overcounts | Query source at build time |
| customers ← sessions | 1-to-many | No impact on COUNT(customer_id) | Safe to pre-aggregate |
```

---

### Rule P2-4b: COUNT DISTINCT Pattern — Never Pre-Aggregate with Multiple Dimensions

**⚠️ CRITICAL: Never put COUNT DISTINCT in a multi-dimension SINK grain.**

❌ **WRONG:**
```sql
SELECT 
  DATE(date) AS date,
  region,
  category,
  status,
  COUNT(DISTINCT customer_id) AS unique_customers  -- WRONG GRAIN!
FROM events
GROUP BY date, region, category, status
```

This counts the same customer multiple times if they appear in multiple status groups.

✅ **RIGHT Option 1: Date-only SINK for COUNT DISTINCT**
```sql
-- SINK table: sink_unique_customers (date-only)
SELECT 
  DATE(event_date) AS date,
  COUNT(DISTINCT customer_id) AS unique_customers
FROM events
GROUP BY DATE(event_date)
```

✅ **RIGHT Option 2: Query source at dashboard build time**
```javascript
// In dashboard generation script
function querySrc() {
  // Fetch COUNT DISTINCT from source at build time
  // Not pre-aggregated, so joins don't overcount
  return executeQuery(`SELECT COUNT(DISTINCT customer_id) FROM events`);
}
```

**Rule:** If a KPI is COUNT DISTINCT and the SINK has 2+ dimensions, choose Option 1 or 2.

**Document in state.md:**
```yaml
### COUNT DISTINCT Handling

**Metric: Unique Customers**
- Grain: Date only (not by region/category)
- Reason: Avoids over-counting across dimensions
- SINK table: project_sink_unique_customers
- Query pattern: Date-only grouping
```

---

### Rule P2-4c: SINK → Dashboard Section Mapping (OUTPUT ARTIFACT)

**⚠️ REQUIRED: Before Phase 3, create a mapping table showing which SINK table feeds which dashboard widget.**

**Create this as a Phase 2 deliverable in state.md:**

```yaml
### SINK → Dashboard Mapping

| Dashboard Section | Widget | Metric | SINK Table | SINK Columns |
|--|--|--|--|--|
| Tab 1: KPI Overview | Card: Revenue | Total Revenue | project_sink_revenue | date, total_revenue |
| Tab 1: KPI Overview | Card: Customers | Unique Customers | project_sink_unique_customers | date, unique_customers |
| Tab 2: Analysis | Chart: Revenue by Region | Revenue by Region | project_sink_revenue | date, region, total_revenue |
| Tab 3: Data Table | Table: Orders | All Orders | project_sink_orders | order_id, date, region, status, revenue |
```

**Why:** Eliminates ambiguity during Phase 3. Phase 3 builder knows exactly which SINK to query for each widget.

---

### Rule P2-5: Workflow SQL Must Use Pre-Aggregation

Every Phase 2 workflow SQL query MUST pre-aggregate metrics:

```sql
-- ✅ RIGHT: GROUP BY dimensions that dashboard actually uses
SELECT 
  DATE(event_time) AS date,
  region,
  product_category,
  SUM(revenue) AS total_revenue,
  COUNT(DISTINCT customer_id) AS unique_customers
FROM source_events
GROUP BY DATE(event_time), region, product_category
ORDER BY date DESC, region, product_category
```

**NOT:**
```sql
-- ❌ WRONG: returns raw events (defeats Phase 2 purpose)
SELECT * FROM source_events
WHERE event_time >= CURRENT_DATE - INTERVAL 7 DAY
```

---

### Rule P2-6: Incremental Load Strategy (Advanced / Optional)

**DEFAULT: Full-refresh workflows only. Incrementality is an optional add-on for technical users only.**

#### Phase 1: Always Start with Full-Refresh

Configure workflows to do **full refreshes by default**:
- Query entire date range each run
- Replace SINK table completely (or truncate + re-insert)
- Simple, predictable, no edge cases
- Best for most dashboards (data sizes < 1GB, date ranges < 2 years)

```yaml
# Full-refresh (DEFAULT — what users see)
td:
  database: <db>

+aggregate_metrics:
  td>: queries/aggregate_metrics.sql
  
  # Write to SINK table (full refresh)
  insert_into: <project_name>_sink_metrics
```

#### Phase 2 (Optional): Incrementality Only for Technical Users

**DO NOT expose incrementality to non-technical users.** Only configure if:
1. **Data size justifies it:** SINK tables > 500MB or growing rapidly
2. **Deep history requested:** Date range > 2 years of daily data
3. **User is technical:** Has explicit consent + understanding of complexity

**When to use incremental:**
- Append-only: Immutable data (events, logs) → append new rows only
- 1-day lookback: Update last N days (handles late-arriving data)
- 7-day lookback: Reprocess wide window (handles corrections)

**Pattern:**
```yaml
# Incremental load (ADVANCED — not shown by default)
td:
  database: <db>

+aggregate_metrics:
  td>: queries/aggregate_metrics.sql
  parameters:
    # Only process new/updated data
    start_time: ${session.last_attempt_time}
    end_time: ${moment().format('YYYY-MM-DD HH:mm:ss')}
  
  # Append or upsert (not full replace)
  insert_into: <project_name>_sink_metrics
```

**Why:** Full-refresh is simpler, more predictable, easier to debug. Incrementality adds complexity (late-arriving data, corrections, edge cases). Only use when data size forces it.

**In Phase 1 Step 1e (Freshness/Update Frequency):**
- Ask user: "How far back do you need data? (90 days, 1 year, 3+ years?)"
- If < 2 years: Use full-refresh (default)
- If ≥ 2 years + GB-scale data: Mention incrementality exists, but NOT as primary recommendation

---

### Rule P2-7: TD Account Access — Verify Before Deployment

- [ ] User can run `tdx auth show` (confirms valid auth)
- [ ] User has CREATE TABLE permission
- [ ] User has access to the target database

**Verification commands:**
```bash
# Test auth
tdx auth show

# Test database access
tdx databases

# Test CREATE TABLE permission
tdx query "CREATE TABLE IF NOT EXISTS test_table (id INT)" --database <target_db>
```

**If any of these fail, STOP and ask user to run `tdx auth setup`.**

---

### Rule P2-8: Workflow SQL Must Be Tested Before Deployment

Before deploying workflow, execute the aggregation query manually:

- [ ] Run: `tdx query -f workflow_query.sql -d <database>`
- [ ] Verify: Results are aggregated (not raw data)
- [ ] Verify: Row count is reasonable
- [ ] Spot-check: Numbers match expectations from Phase 1

**Example test:**
```sql
-- Test the aggregation query
SELECT 
  DATE(event_time) AS date,
  region,
  SUM(revenue) AS total_revenue,
  COUNT(DISTINCT customer_id) AS unique_customers
FROM source_events
WHERE event_time >= CURRENT_DATE - INTERVAL 7 DAY
GROUP BY DATE(event_time), region
ORDER BY date DESC, region
LIMIT 100;

-- Spot-check results:
-- - Dates are recent? ✓
-- - Regions are expected? ✓
-- - Revenue numbers look reasonable? ✓
```

---

### Rule P2-9: State.md Append

Append Phase 2 results to state.md (created in Phase 1):

```yaml
---

## Phase 2 — Workflow Deployment
**Date:** [date]
**Status:** ✅ Complete

### SINK Tables Created

- **Table:** [project_name]_sink_[group_1]
  - Rows: [N]
  - Columns: [list]
  - First populated: [timestamp]
  
- **Table:** [project_name]_sink_[group_2]
  - Rows: [N]
  - Columns: [list]
  - First populated: [timestamp]

### Workflow Deployed

- **Workflow Name:** [name]
- **Schedule:** [frequency, time, timezone]
- **Duration:** ~[Xm] per run
- **Last Run:** [timestamp]
- **Status:** ✓ Running successfully

### Validation Results

- [ ] Join cardinality validated
- [ ] Time column confirmed non-nullable
- [ ] SQL query tested manually (results verified)
- [ ] First run completed successfully
- [ ] SINK tables populated with expected data

---

## Next Action

1. ✓ Phase 2 complete
2. SINK tables ready for Phase 3 queries
3. Jump to Phase 3 (`../phase-3/INSTRUCTIONS.md`)
```

---

## Phase 2 Pre-Flight Checklist

**Before starting Phase 2, verify:**

### Prerequisites from Phase 1
- [ ] Dashboard Complexity Score ≥ 4 (or Score 3 and user chose Phase 2)
- [ ] state.md exists from Phase 1
- [ ] All Phase 1 requirements + data findings documented in state.md

### TD Account Setup
- [ ] `tdx auth show` returns valid profile
- [ ] User has CREATE TABLE permission
- [ ] Target database is accessible

### Workflow Planning
- [ ] Aggregation SQL logic planned (pre-aggregation identified)
- [ ] Metric groups defined (dimensions for GROUP BY)
- [ ] Refresh schedule decided (daily/weekly/custom)
- [ ] Cost estimate provided

### User Approval
- [ ] User approved SINK table creation (approval template completed)
- [ ] User approved schedule and cost impact

---

## Phase 2 Decision Tree

```
START Phase 2: Workflow Deployment
    ↓
Is Dashboard Complexity Score ≥ 4 (or user approved override)?
    YES ↓  → Continue
    NO  ↓  → ERROR: Should not be in Phase 2
    ↓
Verify prerequisites from Phase 1 in state.md
    ↓
Validate join cardinality (Rule P2-2)
    ↓
Plan aggregation logic (GROUP BY dimensions)
    ↓
Define SINK table names (Rule P2-4)
    ↓
Write and test aggregation SQL (Rule P2-8)
    ↓
Present cost/scope approval to user (Rule P2-1)
    ↓
User approves?
    YES ↓ → Deploy workflow
    NO  ↓ → Gather feedback, adjust, re-present
    ↓
Deploy workflow + create SINK tables
    ↓
Run first test cycle (manual trigger)
    ↓
Verify: SINK tables populated with expected data
    ↓
Append Phase 2 results to state.md
    ↓
END Phase 2 → Jump to Phase 3
```

---

## Common Phase 2 Blocks

### "The join has a cardinality mismatch"
**Response:**
> "This means one table has more unique keys than the other. We have two options: (1) Pre-aggregate the many-side table first (common fix), or (2) Use a different join key if available. Let me test the pre-aggregation approach."

### "The query is too slow"
**Response:**
> "Let's optimize: (1) Add partition pruning using td_time_range(), (2) Reduce the date range for testing, or (3) Pre-aggregate further before the join. Which would help?"

### "I'm not sure what the schedule should be"
**Response:**
> "How often do you need the dashboard to refresh? Common options: (1) Daily at 2 AM (most customers), (2) Weekly, (3) After business hours if data updates then. What fits your workflow?"

### "How much will this cost?"
**Response:**
> "Rough estimate based on query volume: ~$X per month. Workflow runs [frequency], and each run queries [N GB] of data. You can adjust the schedule to reduce cost if needed."

---

## Phase Progression Gate (CANNOT Skip)

**⚠️ CRITICAL: Before proceeding to Phase 3, verify:**

- [ ] Phase 1 marked COMPLETE in state.md (Dashboard Complexity Score documented)
- [ ] Dashboard Complexity Score is 4-6 (or user explicitly chose Phase 2)
- [ ] All SINK tables created (listed in state.md)
- [ ] Workflow deployed and first run completed successfully
- [ ] Workflow runs without errors (check logs)
- [ ] SINK tables populated with expected data
- [ ] state.md appended with Phase 2 results:
  - SINK table names (all listed)
  - Workflow name and schedule
  - First run results
  - Validation checklist completed
  - "Next Action" pointer set to Phase 3

**If ANY item is missing or failed:**
> "Cannot proceed to Phase 3. Phase 2 incomplete or failed.
> Missing/Failed: [specific item]
> Please complete or debug before moving forward."

**Only after all items verified:**
- Append "Phase 2 COMPLETE" to state.md
- Proceed to Phase 3

---

## After Phase 2 Completes (Rule 0: Phase Auto-Advance)

**If workflow deploys successfully (IMMEDIATE AUTO-START):**

**Say this (EXACT SCRIPT):**
```
✅ Phase 2 Complete — Workflow deployed and running

### Summary
- SINK tables created: [list]
- Workflow schedule: [frequency]
- First run: [timestamp or "queued"]

### Next: Phase 3 — Build Dashboard
Now we'll create the interactive dashboard using your optimized SINK tables.
Estimated time: 2-3 hours

Starting Phase 3...
```

**Then immediately proceed to Phase 3 (no approval needed, no "let me know")**

**If workflow fails:**
```
✗ Phase 2 Blocked — Troubleshoot before Phase 3
  
Debug checklist:
  1. Is auth still valid? (tdx auth show)
  2. Do SINK tables exist? (tdx tables <db>)
  3. Did the first run complete? (tdx wf show <workflow_name>)
  
Return to user with error details + next troubleshooting step
```

**Why:** Phase 2 success = immediate trigger to Phase 3. No stop, no pause, no "should we continue?"

---

**Version:** 1.0.0
**Last Updated:** 22 July 2026
**Load Order:** 1.2 (read after Phase 1 INSTRUCTIONS.md)
