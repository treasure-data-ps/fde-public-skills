# Knowledge Base Template — SQL Templates & Workflow Reference

Fill in from Phase 3 queries (sql_templates.md) and Phase 2 deployment notes (workflow_reference.md), if Phase 2 was run.

---

# SQL Templates — [CUSTOMER_NAME] Dashboard

Each query below is parameterized. Replace `{SINK_DB}` with the actual SINK database name when running manually.

**Parameter reference:**
- `{SINK_DB}` — SINK database (e.g., `customer_travel_sink`)
- `{SOURCE_DB}` — Source database fallback (e.g., `travel_demo`)
- `{DATE_RANGE_DAYS}` — Lookback window in days (e.g., `90`)
- `{FILTER_DIMENSION}` — Optional WHERE clause dimension filter

---

## Q1: [Query Name — e.g., "Executive KPIs"]

**What this answers:** [Plain English — e.g., "Total bookings, revenue, cancellation rate for the KPI header row"]  
**Dashboard location:** [Tab + section — e.g., "Overview tab, top KPI cards"]  
**Returns:** [N] rows, shape: `{ total_bookings, total_revenue, cancelled, ... }`

```sql
SELECT
  COUNT(*) AS total_bookings,
  ROUND(SUM(amount), 2) AS total_revenue,
  COUNT(CASE WHEN booking_status = 'Cancelled' THEN 1 END) AS cancelled
FROM {SINK_DB}.fact_bookings
-- Exclusions: [describe what is excluded and why]
```

**Validated value (Phase 1/3 spot-check):** total_bookings = [N], total_revenue = $[N]

---

## Q2: [Query Name — e.g., "Monthly Trend"]

**What this answers:** [Plain English]  
**Dashboard location:** [Tab + chart name]  
**Returns:** [N] rows per month, shape: `{ month, bookings, revenue }`

```sql
SELECT
  month,
  COUNT(*) AS bookings,
  ROUND(SUM(amount), 2) AS revenue
FROM {SINK_DB}.fact_bookings
GROUP BY month
ORDER BY month
```

---

## [Q3 … QN] — continue pattern above

---

## Template 5 (Project-Specific): [Most-Asked Question from Phase 1 Stage A]

**Purpose:** Every engagement has one question customers will ask first — capture it here as a named, validated template so the agent answers it correctly on first try, without re-deriving the SQL.

**Triggered by:** [The exact phrasing captured in state.md during Phase 1 — e.g. "biggest churn risk area", "which segment should we focus on", "what drove last month's revenue drop"]
**Expected shape:** [N] rows, shape: `{ [dim_1], [dim_2], [metric] }`
**Row count expectation:** [N] rows, sums to [confirmed total from state.md]

```sql
-- Customize: replace with the validated SQL for this project's #1 business question.
-- This query was run and confirmed in Phase 3 — do not change column names or GROUP BY.
SELECT [dim_1], [dim_2], SUM([metric_col]) AS [metric_alias]
FROM {SINK_DB}.[table]
WHERE [exclusion_clause]   -- from Phase 1/2 filter scope map; omit if no exclusion
GROUP BY [dim_1], [dim_2]
ORDER BY [metric_alias] DESC
```

**Validation:** SUM([metric_alias]) across all rows = [confirmed total from state.md]

> **Why Template 5 matters:** This template anchors the agent's first real interaction with the user. Without it, the agent writes a fresh query on the fly — risking fan-out, wrong column names, or missing the exclusion clause. Populate this before the Track B push in Phase 4.

---

## Fallback Queries (Source Tables)

When SINK tables don't exist, replace `{SINK_DB}.fact_bookings` with:

```sql
-- Q1 fallback: direct from source
SELECT
  COUNT(*) AS total_bookings,
  ROUND(SUM(amount), 2) AS total_revenue,
  COUNT(CASE WHEN booking_status = 'Cancelled' THEN 1 END) AS cancelled
FROM {SOURCE_DB}.bookings
WHERE td_time_range(time, '2024-01-01', NULL)
-- Note: source tables have no pre-aggregation; GROUP BY required for trend queries
```

---

## Workflow SQL (Source → SINK Transformation)

Copy each SQL task from the workflow `.dig` files here. Use this section when:
- SINK tables don't exist yet (pre-workflow run)
- A SINK table is partially populated or suspect
- User wants to extend a metric and needs to see the original aggregation logic
- Debugging a SINK value mismatch — compare source query result vs SINK

**Source:** `./<project-name>/workflows/` (SQL is either a separate file under `queries/` or inline in the `.dig` file itself).

---

### WF-Q1: [Workflow Task Name — e.g., "Build Monthly Sales SINK"]

**Builds:** `{SINK_DB}.[sink_table_name]`  
**Source table:** `{SOURCE_DB}.[source_table_name]`  
**What it does:** [Plain English — e.g., "Aggregates raw order rows into monthly totals by region, channel, and customer segment"]

```sql
SELECT
  order_month,
  region,
  channel,
  customer_segment,
  COUNT(*) AS orders,
  SUM(revenue) AS total_revenue
FROM {SOURCE_DB}.[source_table]
WHERE td_time_range(time, TD_TIME_ADD(TD_SCHEDULED_TIME(), '-90d', 'UTC'), NULL, 'UTC')
GROUP BY order_month, region, channel, customer_segment
```

**To run against source directly:**
```bash
tdx query -d {SOURCE_DB} "SELECT order_month, region, channel, customer_segment, COUNT(*) AS orders, SUM(revenue) AS total_revenue FROM [source_table] GROUP BY order_month, region, channel, customer_segment" --format json --limit 10000
```

---

### WF-Q2: [Workflow Task Name — e.g., "Build Geography Reference SINK"]

**Builds:** `{SINK_DB}.[sink_geography_table]`  
**Source table:** `{SOURCE_DB}.[source_geography_table]`  
**What it does:** [Plain English — e.g., "Snapshot of region → state → city mapping; no date column; full table"]  
**Note:** This is a snapshot table — no date column. Do not apply date filters when querying.

```sql
SELECT DISTINCT
  region,
  state,
  city
FROM {SOURCE_DB}.[source_geography_table]
```

**To run against source directly:**
```bash
tdx query -d {SOURCE_DB} "SELECT DISTINCT region, state, city FROM [source_geography_table]" --format json --limit 1000
```

---

### [WF-Q3 … WF-QN] — continue pattern above for each workflow SQL task

---

# Workflow Reference — [CUSTOMER_NAME] Dashboard

Use this when a user asks: "How often does this data update?", "Where is the workflow?", "Why did the data not refresh?"

## Workflow Identity

| Field | Value |
|---|---|
| **TD Workflow project name** | `[project_name]` |
| **Entry workflow file** | `dashboard-workflow-launch.dig` |
| **SINK database** | `[sink_db_name]` |
| **Source database** | `[source_db_name]` |
| **Treasure Data account** | `[account_name]` (region: [us01/eu01/jp01]) |

## Schedule

| Field | Value |
|---|---|
| **Frequency** | [e.g., "Daily at 2 AM UTC"] |
| **Cron** | `[0 2 * * *]` |
| **Full refresh or incremental** | [Full refresh — `create_table:` replaces on every run] |
| **Typical run time** | ~[N] minutes |

## Data Flow

```
[source_db].[raw_tables]
  → dashboard-workflow-data-prep.dig (SQL aggregations)
  → [sink_db].fact_* (SINK tables — one per domain)
  → Phase 3 dashboard queries
  → dashboard.html (HTML Client)
```

## Last Known Good Run

| Field | Value |
|---|---|
| **Date** | [Last validated date from Phase 2] |
| **Attempt ID** | [attempt_id from `tdx wf timeline`] |
| **Row counts** | [table: N rows, table: N rows, ...] |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Dashboard shows stale data | Workflow not running on schedule | Check `tdx wf sessions [project]` for recent runs |
| SINK table missing | SQL task failed | `tdx wf attempt [id] tasks --include-subtasks` |
| Row count = 0 | Date range in input_params.yaml doesn't overlap source data | Update `start_date` / `end_date` in params, re-push, re-run |

→ For full troubleshooting: `../../../phase-2/references/testing-troubleshooting.md` (if Phase 2 was run) or `../../../phase-3/references/testing-troubleshooting.md`

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
