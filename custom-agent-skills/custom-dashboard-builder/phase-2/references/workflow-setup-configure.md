# Phase 2: Steps 2a-2d (Copy, Configure, Build, Datamodel)

> **⛔ GUARDRAILS CHECK — before doing anything else:**
> Have you read `../../references/guardrails-lite.md` this session?
> ```
> AskUserQuestion:
>   header: "Guardrails"
>   question: "Have you read guardrails-lite.md this session?"
>   options:
>     - label: "Yes — proceed"
>       description: "guardrails-lite.md was read at session start"
>     - label: "Read it now"
>       description: "Load guardrails-lite.md before continuing"
> ```
> If "Read it now" → read `../../references/guardrails-lite.md` in full before any step.
>
> **Single local file for state — no Confluence, no git.**
> Only update: `state.md`, in `./<project_name>/`.

## ⚠ CRITICAL: Schema Inspection BEFORE Any SQL (5 min)

**Do this first, before Steps 2a-2d:**

Before writing ANY SQL queries, run `tdx describe` on EVERY source table to validate actual column names against Stage A/B assumptions. Real databases often have different naming:

```bash
tdx describe -d <source_database> <table_name>
```

**Why:** Column names from Stage A/B notes can drift from actual schema:
- Stage A/B note: `state` → Actual: `state_code`
- Stage A/B note: `service_cost` → Actual: `cost`
- Stage A/B note: `status` → Actual: `resolution_status`
- Stage A/B note: `ticket_category` → Actual: `category`

Mismatched names cause workflow failures mid-run. Copy exact column names from `tdx describe` output, never from Stage A/B notes.

**Multi-source:** If Stage B identified tables across multiple databases, run `tdx describe` on each:
```bash
tdx describe -d crm_production customers
tdx describe -d web_analytics page_views
tdx describe -d commerce_db orders
```

**Validation checklist:**
- ✅ Ran `tdx describe` on all Stage A/B source tables
- ✅ Confirmed all assumed column names exist in actual schema
- ✅ Noted any renamed or missing columns
- ✅ Updated `state.md` with corrections if needed

---

## ⚠ MANDATORY: JOIN Fan-Out Gate BEFORE Any Aggregation SQL (2 min)

**Run this check before writing any multi-table SQL that uses SUM, COUNT, or AVG:**

If you are joining two tables and then aggregating, check whether the join inflates the row count:

```sql
-- Count WITH the join
SELECT COUNT(*) FROM base_table b LEFT JOIN other_table o ON b.id = o.id

-- Count WITHOUT the join (base table alone)
SELECT COUNT(*) FROM base_table
```

**If joined_count > base_count:** you have fan-out. `SUM()` on any column from `base_table` will be over-counted by the ratio (e.g. 1.59× if there are avg 1.59 rows in `other_table` per base row).

**Fix:** Pre-aggregate the many-side table into a subquery keyed on the join key BEFORE joining:

```sql
-- ✅ Correct — pre-aggregate other_table first
SELECT b.*, ot.total_items, ot.total_line_value
FROM base_table b
LEFT JOIN (
  SELECT id, COUNT(*) AS total_items, SUM(amount) AS total_line_value
  FROM other_table
  GROUP BY id
) ot ON b.id = ot.id

-- ❌ Wrong — fan-out inflates all SUM() values
SELECT b.*, SUM(o.amount)
FROM base_table b LEFT JOIN other_table o ON b.id = o.id
GROUP BY b.id
```

Past incident: `transactions LEFT JOIN transactions_items` (avg 1.59 items/order) inflated `SUM(amount)` by 1.59× — workflow SINK showed $6.86M vs source $4.32M. `COUNT(DISTINCT order_id)` was correct because DISTINCT is fan-out-safe, but SUM was not.

---

## Phase 2 Entry Requirements: Read From Stage A (5 min — DO THIS NEXT)

**Before starting Step 2a, extract these values from `state.md` Session Setup block:**

This step ensures Phase 2 has all required configuration from Stage A, without re-asking the user.

### Required Stage A Artifacts:

Open `./<project_name>/state.md` (local file) and locate:

| Stage A Step | Field | Location in state.md | Phase 2 Use |
|---|---|---|---|
| **1g** | Historical Data Depth | Under "Historical Data Retention" | How many days back for `td_time_range()` window |
| **1e+1f** | Refresh Schedule | Under "Data Freshness & Refresh" | When should workflow run? (daily 2 AM UTC typical) |
| **1q** | SINK Database | Under "Workflow Configuration" | Where to write aggregated tables |
| **1q** | Workflow Project Name | Under "Workflow Configuration" | TD project name for `tdx wf` commands |
| **1q** | Data Volatility / Lookback | Under "Workflow Configuration" | Incremental strategy: append-only / 1-day / 7-day |

### Extraction Checklist:

```
From state.md Session Setup block:

Historical window:
  [ ] Found under Step 1g: _____ days (e.g., 365)
  
Refresh schedule:
  [ ] Found under Step 1e+1f: _____ (e.g., "Daily 2 AM UTC")
  
SINK database:
  [ ] Found under Step 1q: _____ (e.g., "td_reporting_agents")
  
Workflow project name:
  [ ] Found under Step 1q: _____ (e.g., "acme_dashboard_prod")
  
Data volatility / lookback:
  [ ] Found under Step 1q: _____ (append-only / 1-day / 7-day)
```

**If ANY field is missing:** Go back to Stage A/B and confirm the field directly with the user, then update `state.md` before proceeding.

**Proceed to Step 2a only after all fields extracted.**

---

## Single vs Multi-Source: Decide Before Step 2b

**Single source** (default): all source tables are in one database.
```yaml
source_database: sales_db
# SQL: FROM ${source_database}.orders
```

**Multi-source**: tables span multiple databases (e.g., CRM in `crm_db`, events in `analytics_db`).
```yaml
# Flat top-level keys — one per source database
source_db_crm: crm_production
source_db_events: web_analytics
source_db_commerce: commerce_db
# SQL: FROM ${source_db_crm}.customers, FROM ${source_db_commerce}.orders
```

**Rule: always use flat top-level keys** — never nest under `globals:` or any parent key. Digdag resolves only root-level keys. A nested key like `source_databases: {crm: crm_production}` causes `Failed to evaluate variable ${source_db_crm}` at runtime.

**When to choose multi-source:**
- Stage B identified tables in 2+ different databases
- Metrics require a JOIN across databases (e.g., orders + CRM tier)
- Dashboard has tabs covering different domains (web, CRM, commerce)

→ **See [`input_params_examples.md`](input_params_examples.md) — Example 3** for a complete multi-source configuration with SQL patterns.

---

## Step 2a: Set Up Workflow Project Folder (10-15 min)

**What to do:**
- Set up workflow project folder using the locally embedded template
- Rename workflow files with the project name

**Action items:**

1. **Copy the embedded template into your project working directory:**
   ```bash
   mkdir -p ./<project_name>/workflows
   cp -r ../references/workflow-templates/. ./<project_name>/workflows/
   ```

2. **Rename workflow files with project name** (REQUIRED):
   ```bash
   cd ./<project_name>/workflows
   
   # Rename all .dig files to use the project name
   mv SLUG_launch.dig <project_name>_launch.dig
   mv SLUG_data_prep.dig <project_name>_data_prep.dig
   mv SLUG_cleaner.dig <project_name>_cleaner.dig
   ```
   
   **Example:** If `project_name = "sales_dashboard"`:
   ```bash
   mv SLUG_launch.dig sales_dashboard_launch.dig
   mv SLUG_data_prep.dig sales_dashboard_data_prep.dig
   mv SLUG_cleaner.dig sales_dashboard_cleaner.dig
   ```

3. **Verify template structure after renaming:**
   ```
   ./<project_name>/workflows/
   ├── input_params.yaml                    ← Customize: metrics, dimensions, schedule
   ├── <project_name>_launch.dig            ← Renamed from SLUG_launch.dig
   ├── <project_name>_data_prep.dig         ← Renamed from SLUG_data_prep.dig
   ├── <project_name>_cleaner.dig           ← Renamed from SLUG_cleaner.dig
   └── sql/
       ├── 01_data_prep.sql
       ├── 02_data_validation.sql
       ├── 03_create_time_filter.sql  ← optional/reference-only, not wired into the default .dig files
       ├── 10_create_aggregates.sql
       ├── 11_create_path_stats.sql
       └── 12_create_unique_visitors.sql
   ```

**Output:** Workflow template directory structure verified, files renamed with project name, ready locally

---

## Step 2b: Configure Queries with TD Time Functions (20-30 min)

**What to do:**
- Optimize approved Stage B queries using Treasure Data time functions
- Choose incremental processing mode

**Key Pattern: Replace CURRENT_DATE with td_time_range()**

```sql
-- Before (unpredictable — depends on run time)
WHERE order_date >= CURRENT_DATE - INTERVAL '365 days'

-- After (deterministic — always uses scheduled time)
WHERE td_time_range(order_time,
  td_time_add(td_scheduled_time(), '-365d'),
  td_scheduled_time()
)
```

**3 Critical Time Function Patterns:**

1. **td_scheduled_time()** — Fixed reference time for reproducible runs
2. **DATE_FORMAT(FROM_UNIXTIME(...), '%Y-%m-%d')** — Format dates with YYYY-MM-DD (strftime format, NOT Java format)
3. **td_time_range()** — Partition pruning (CRITICAL for performance)

**IMPORTANT: Date Format Gotcha**

⚠️ **Broken:** `TD_TIME_STRING(col, 'yyyy-MM')` — uses Java SimpleDateFormat syntax (NOT supported by TD)  
✅ **Fixed:** `DATE_FORMAT(FROM_UNIXTIME(TD_DATE_TRUNC('month', col)), '%Y-%m')` — uses strftime format codes

Treasure Data uses **strftime-style format strings** (`%Y`, `%m`, `%d`), NOT Java SimpleDateFormat (yyyy, MM, dd).

**Critical: Incremental Processing**

Do NOT reprocess all 365 days every day — process only NEW data.

```sql
-- WRONG: Full refresh every day — SLOW (10+ minutes) ❌
SELECT DATE(order_date) as date, SUM(amount) as revenue
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '365 days'
GROUP BY DATE(order_date)

-- RIGHT: Append only yesterday — FAST (30 seconds) ✓
SELECT DATE_FORMAT(FROM_UNIXTIME(TD_DATE_TRUNC('day', order_time)), '%Y-%m-%d') as date, SUM(amount) as revenue
FROM orders
WHERE td_time_range(order_time,
  td_time_add(td_scheduled_time(), '-1d'),
  td_scheduled_time()
)
GROUP BY DATE_FORMAT(FROM_UNIXTIME(TD_DATE_TRUNC('day', order_time)), '%Y-%m-%d')
```

**Impact:** First run: 2-5 min (one-time) | Daily runs: 30 sec (20x faster)

**Data Volatility Decision:**

Ask the user: "Can metrics change after being recorded?"
- NO (immutable) → Use **append-only** pattern (fastest)
- YES → Ask: "How soon are corrections made?"
  - Within 1 day → **1-day lookback** (handles same-day corrections)
  - Within 7 days → **7-day lookback** (catches delayed corrections)

**Validate Performance:**

```bash
# Test execution time
tdx query -d sales_db < sql/kpi_daily_optimized.sql

# Should return results in < 5 seconds
```

**Output:**
- ✅ All Stage B queries optimized with `td_time_range()` + `td_time_string()`
- ✅ Incremental processing mode chosen (append-only, 1-day, or 7-day)
- ✅ Performance validated (each query < 5 seconds)

---

## Step 2c: Build Workflow (.dig file) (15-25 min)

**What to do:**
- Define scheduled workflow using Digdag syntax
- Map queries to output tables
- (If needed) Add additional tasks to the orchestrator

The template already ships with a working `.dig` orchestrator (`<project_name>_launch.dig` → `<project_name>_data_prep.dig` → optional `<project_name>_cleaner.dig`, all driven by `input_params.yaml`). Most of the time you only need to edit `input_params.yaml` and the `sql/*.sql` files — not the `.dig` files themselves.

**Note:** `.dig` files were already renamed to `<project_name>_*.dig` format in Step 2a. If you need to add additional tasks or modify the orchestration, edit the renamed files directly.

⚠️ **CRITICAL: `database:` parameter must be on a separate line**

```yaml
timezone: UTC

# Run daily at 2:00 AM UTC
schedule:
  daily>: "02:00:00"

_export:
  td:
    database: dashboard_db      # Output database — REQUIRED
    engine: trino               # Query engine

# Task 1: Daily KPI metrics
+kpi_daily:
  td>: sql/10_create_aggregates.sql
  database: ${database}         # ✅ REQUIRED: separate line, not combined path
  create_table: kpi_daily
```

**Why separate?** The .dig parser doesn't handle `create_table: ${database}.table_name` — it requires `database:` on its own directive line, then `create_table:` as a separate directive.

**Advanced: Use Session Variables for Dynamic Dates**

```yaml
# <project_name>_data_prep.dig — all queries live here
+kpi_daily:
  td>: sql/10_create_aggregates.sql
  engine: presto
  database: ${sink_database}
  create_table: kpi_daily
```

```sql
-- sql/10_create_aggregates.sql — use session variables for dynamic incremental window
INSERT INTO ${sink_database}.${project_prefix}_aggregate_final
SELECT
  DATE_FORMAT(FROM_UNIXTIME(TD_DATE_TRUNC('day', order_time)), '%Y-%m-%d') AS date,
  SUM(amount) AS revenue
FROM ${source_database}.orders
WHERE td_time_range(order_time,
  TD_TIME_ADD(TD_SCHEDULED_TIME(), '-1d', 'UTC'),
  TD_SCHEDULED_TIME(), 'UTC')
GROUP BY DATE_FORMAT(FROM_UNIXTIME(TD_DATE_TRUNC('day', order_time)), '%Y-%m-%d')
```

**Reference:** `workflow-skills:digdag` for full Digdag syntax

**Output:**
- ✅ Launch + data-prep `.dig` files configured — orchestrates data-prep
- ✅ Schedule set (typically daily 2 AM UTC)
- ✅ Output tables defined with `create_table:` (full-refresh)
- ✅ Session variables configured (if using incremental)

**About `create_table:` vs `insert_into:`:**
- **`create_table:`** — Replace entire table on each run (full-refresh). ✅ **Correct for dashboards.**
- **`insert_into:`** — Append to table (incremental). Only use if you pre-aggregate and want append-only semantics.

Dashboard workflows always use `create_table:` for SINK tables. No truncate step needed — the table is replaced on every run.

---

## Step 2d: Configure Datamodel (Optional — Only If Needed) (10-15 min)

**Skip this step unless you're feeding an analytics layer that requires an explicit schema/join config file.** Most lite deployments don't need this — the SINK tables produced by Step 2c are queried directly by Phase 3 dashboard SQL, with no separate datamodel config required.

**What to do (if applicable):**
- Map metrics, dimensions, relationships in a simple config file for downstream tooling
- Document SINK table structure for Phase 3

**Example: config.json**

```json
{
  "name": "Sales KPI Dashboard",
  "database": "dashboard_db",
  "description": "Daily KPI tracking with regional breakdown",
  
  "fact_tables": [
    {
      "name": "kpi_daily",
      "label": "Daily Metrics",
      "grain": "daily",
      "time_column": "date",
      "metrics": [
        "total_revenue",
        "order_count",
        "avg_order_value",
        "unique_customers"
      ]
    }
  ],
  
  "dimension_tables": [
    {
      "name": "kpi_by_dimension",
      "label": "Dimension Breakdown",
      "columns": ["date", "region", "segment", "revenue"]
    }
  ],
  
  "relationships": [
    {
      "fact_table": "kpi_daily",
      "dimension_table": "kpi_by_dimension",
      "fact_key": "date",
      "dim_key": "date"
    }
  ]
}
```

**Map from Stage B Requirements:**

| Stage B | Maps to config.json | Example |
|---------|---|---|
| Metrics (5-10) | `fact_tables[*].metrics[]` | `total_revenue`, `order_count` |
| Dimensions (3-5) | `dimension_tables[]` | `region`, `segment`, `product_category` |
| Output DB | `database` | `dashboard_db` |
| Time grain | `fact_tables[*].grain` | `daily`, `hourly`, `weekly` |

**Validate JSON Syntax:**

```bash
jq '.' config.json  # Should output JSON without errors
```

**Output (if this step was needed):**
- ✅ `config.json` created and validated
- ✅ Fact tables mapped from `kpi_daily`
- ✅ Dimension tables mapped
- ✅ Relationships defined

---

## Datamodel Design Principles (Step 2d Reference)

### Core Principles

1. **Pre-aggregation** — Output tables are dashboard-ready (aggregated, not raw events)
2. **Grain clarity** — Each output table has a clear grain (date, country, product, etc.)
3. **Cardinality control** — Target < 100K rows for < 1 sec queries (soft limit; 100K-500K acceptable with user approval)
4. **Additive measures** — Design metrics that can be safely SUMmed up
5. **Star schema** — Facts + dimensions (dimensional modeling best practices)

### Additive vs Non-Additive Measures

**Additive (safe to SUM):** `COUNT(*)`, `SUM(revenue)`, `COUNT(DISTINCT user_id)` pre-deduped  
**Non-additive (never SUM):** avg order value, conversion rate, median — recalculate from additive components instead:

```sql
-- ✅ CORRECT: recalculate from components
SELECT SUM(total_revenue) / SUM(order_count) as avg_order_value

-- ❌ WRONG: summing a pre-computed average
SELECT SUM(avg_order_value)
```

### Cardinality Planning

**Soft Limit: < 100K rows per SINK table** for optimal < 1 second dashboard queries.

- **< 100K rows** → Fast queries (< 1 sec), optimal for dashboards
- **100K-500K rows** → Acceptable, monitor query performance in Phase 3
- **> 500K rows** → Acceptable if justified, but requires testing + user approval on performance trade-offs

```
✅ Grain: [date, country, device_type] = 365 × 5 × 3 = 5,475 rows
⚠️ Grain: [date, country, product_id] = 365 × 5 × 50,000 = 91.25M rows (TOO HIGH)
```

Fix cardinality explosion: aggregate product_id → product_category, or split into separate tables.

### Cardinality Audit Checklist (Before Finalizing SINK Tables)

**Step 1: Calculate estimated row count**
```sql
-- For each SINK table, estimate grain cardinality
SELECT 
  COUNT(DISTINCT date) as unique_dates,
  COUNT(DISTINCT country) as unique_countries,
  COUNT(DISTINCT product_category) as unique_categories,
  COUNT(DISTINCT date, country, product_category) as estimated_grain_rows
FROM source_table
WHERE <date_filter>
```

**Step 2: Show user BEFORE/AFTER summary**

Present a summary showing:
```
SINK Table: sales_daily_metrics

BEFORE (original grain):
  Dimensions: [date, country, region, customer_segment, product_id]
  Estimated rows: 365 × 50 × 500 × 10 × 100,000 = 91.25B rows ❌

AFTER (optimized grain):
  Dimensions: [date, country, region, customer_segment, product_category]
  Estimated rows: 365 × 50 × 500 × 10 × 50 = 456.25M rows ⚠️

WHY: product_id has 100K unique values (too high). 
Aggregated to product_category (50 unique values).
Query performance: ~2-3 seconds (acceptable).

Metrics: revenue (SUM), order_count (SUM), unique_customers (COUNT DISTINCT pre-deduped)
```

**Step 3: User approval gate (if filters needed)**

If optimization requires removing dimensions or filters:

```
AskUserQuestion:
  header: "Cardinality optimization"
  question: "To reach acceptable performance, I propose aggregating product_id → product_category. 
  
  This means:
  - Dashboard can filter by category (e.g., 'Electronics', 'Clothing')
  - Dashboard cannot filter by individual product (e.g., 'SKU-12345')
  
  Is this acceptable?"
  options:
    - label: "Yes, proceed with aggregation"
    - label: "No — keep individual products"
      description: "Accept slower queries (3-5s), or split into separate tables"
    - label: "Alternative — split into multiple SINK tables"
      description: "One table per product category, less flexible filtering"
```

**Step 4: Final validation checklist**

- [ ] Final SINK table row count documented (actual or estimated)
- [ ] Grain is explicit and documented (list all dimensions)
- [ ] If > 100K rows: user approved trade-offs (performance, filtering scope)
- [ ] All measures are additive (or recalculated from additive components)
- [ ] Dashboard query performance estimated/tested (< 3 seconds acceptable)
- [ ] Filters removed vs original requirements: documented in state.md with reasoning

---

## SQL Aggregation Patterns (Reference for Step 2c)

Common patterns for the SQL files in `sql/10_*.sql` and `sql/11_*.sql`. All examples should be converted to `INSERT INTO` + `td_time_range()` before deploying — see Step 2b for the incremental wrapper. Use `sql-skills:trino` and `sql-skills:trino-optimizer` for TD-specific function reference.

**Core principle:** Aggregate as much as possible in the workflow SQL layer. Target < 100K rows per output table so Phase 3 dashboard queries run < 1 second.

```
Raw events (100M rows)
  ↓ Workflow SQL aggregation
Output SINK table (50K rows)
  ↓ Phase 3 dashboard query
Visualization (< 1 sec)
```

### Pattern 1: Daily Metrics by Dimension

**Before deploying, estimate grain cardinality:**
```sql
-- Estimate: 365 days × 50 countries × 200 products = 3.65M rows (too high)
-- Fix: aggregate product → product_category (20 categories) = 365M rows (still high, acceptable with testing)
```

```sql
INSERT INTO ${sink_database}.${project_prefix}_aggregate_final
SELECT
  event_date,
  country,
  product_category,                                                     -- Aggregated from product_id
  APPROX_DISTINCT(user_id)                                              AS unique_users,
  APPROX_DISTINCT(session_id)                                           AS sessions,
  COUNT(*)                                                              AS event_count,
  COUNT(CASE WHEN event_type = 'purchase' THEN 1 END)                  AS purchases,
  COALESCE(SUM(CASE WHEN event_type = 'purchase' THEN event_value END), 0) AS revenue,
  APPROX_PERCENTILE(event_value, 0.5)                                   AS median_value
FROM ${sink_database}.${project_prefix}_events_prep
WHERE td_time_range(event_time,
  TD_TIME_ADD(TD_SCHEDULED_TIME(), '-1d', 'UTC'),
  TD_SCHEDULED_TIME(), 'UTC')
GROUP BY event_date, country, product_category
```

### Pattern 2: Cumulative / Running Total

```sql
INSERT INTO ${sink_database}.${project_prefix}_cumulative
SELECT
  date,
  country,
  unique_users,
  SUM(unique_users) OVER (PARTITION BY country ORDER BY date) AS cumulative_users,
  SUM(revenue)      OVER (PARTITION BY country ORDER BY date) AS cumulative_revenue
FROM ${sink_database}.${project_prefix}_aggregate_final
WHERE td_time_range(event_time,
  TD_TIME_ADD(TD_SCHEDULED_TIME(), '-1d', 'UTC'),
  TD_SCHEDULED_TIME(), 'UTC')
```

### Pattern 3: Week-over-Week / Period Comparison

```sql
INSERT INTO ${sink_database}.${project_prefix}_wow
SELECT
  date,
  country,
  unique_users,
  revenue,
  LAG(unique_users) OVER (PARTITION BY country ORDER BY date) AS prev_week_users,
  ROUND(
    (unique_users - LAG(unique_users) OVER (PARTITION BY country ORDER BY date)) * 100.0
    / NULLIF(LAG(unique_users) OVER (PARTITION BY country ORDER BY date), 0)
  , 2)                                                         AS wow_growth_pct
FROM ${sink_database}.${project_prefix}_aggregate_final
WHERE td_time_range(event_time,
  TD_TIME_ADD(TD_SCHEDULED_TIME(), '-1d', 'UTC'),
  TD_SCHEDULED_TIME(), 'UTC')
```

### Pattern 4: Filtered / Conditional Aggregations

```sql
-- Multiple metrics in one pass with conditional aggregation
-- Avoids multiple table scans for each metric
INSERT INTO ${sink_database}.${project_prefix}_filtered_kpis
SELECT
  event_date,
  country,
  APPROX_DISTINCT(user_id)                                              AS all_users,
  APPROX_DISTINCT(CASE WHEN event_type = 'purchase' THEN user_id END)  AS purchase_users,
  COALESCE(SUM(CASE WHEN event_type = 'purchase' THEN event_value END), 0) AS purchase_revenue,
  ROUND(
    APPROX_DISTINCT(CASE WHEN event_type = 'purchase' THEN user_id END) * 100.0
    / NULLIF(APPROX_DISTINCT(user_id), 0)
  , 2)                                                                  AS purchase_rate_pct
FROM ${sink_database}.${project_prefix}_events_prep
WHERE td_time_range(event_time,
  TD_TIME_ADD(TD_SCHEDULED_TIME(), '-1d', 'UTC'),
  TD_SCHEDULED_TIME(), 'UTC')
GROUP BY event_date, country
```

### Pattern 4b: CRITICAL — Avoid Many-to-Many JOINs via Pre-Aggregation

⚠️ **Broken:** Joining high-cardinality tables directly silently inflates metrics
```sql
-- ❌ WRONG: Joining service_history (1M rows) × service_appointments (13M rows)
--    Results in 13M × 1M cartesian explosion = revenue multiplied by 13x
SELECT 
  h.service_id, 
  SUM(h.cost) as revenue,
  COUNT(a.appointment_id) as appointments
FROM service_history h
LEFT JOIN service_appointments a ON h.service_id = a.service_id
GROUP BY h.service_id
```

✅ **Fixed:** Pre-aggregate each table, then join aggregates
```sql
-- First aggregate: service history by service_id
WITH service_agg AS (
  SELECT 
    service_id, 
    SUM(cost) as total_cost,
    COUNT(*) as service_count
  FROM service_history
  GROUP BY service_id
),
-- Second aggregate: appointments by service_id
appointment_agg AS (
  SELECT 
    service_id,
    COUNT(*) as appointment_count,
    COUNT(DISTINCT technician_id) as unique_technicians
  FROM service_appointments
  GROUP BY service_id
)
-- Join aggregates (now 1M rows × 1M rows, not expanded)
SELECT 
  s.service_id,
  s.total_cost as revenue,
  a.appointment_count,
  a.unique_technicians
FROM service_agg s
LEFT JOIN appointment_agg a ON s.service_id = a.service_id
```

**Rule:** Always pre-aggregate before joining high-cardinality dimension tables.

---

### Pattern 5: Join Dimension Table After Aggregation

```sql
-- ✅ CORRECT: Aggregate first, join dimension after
-- Joining before aggregation inflates dimension cardinality
INSERT INTO ${sink_database}.${project_prefix}_enriched
SELECT
  m.event_date,
  m.country,
  c.tier,
  c.segment,
  m.unique_users,
  m.revenue
FROM ${sink_database}.${project_prefix}_aggregate_final m
LEFT JOIN ${source_database}.dim_customer c ON m.user_id = c.customer_id
WHERE td_time_range(m.event_time,
  TD_TIME_ADD(TD_SCHEDULED_TIME(), '-1d', 'UTC'),
  TD_SCHEDULED_TIME(), 'UTC')
GROUP BY m.event_date, m.country, c.tier, c.segment
```

### Pattern 6: Cohort Analysis

```sql
INSERT INTO ${sink_database}.${project_prefix}_cohort_retention
WITH first_event AS (
  SELECT user_id,
    MIN(event_date)                          AS first_date,
    DATE_TRUNC('month', MIN(event_date))     AS cohort_month
  FROM ${source_database}.${source_table}
  WHERE event_type = 'purchase'
  GROUP BY user_id
)
SELECT
  fp.cohort_month,
  DATE_TRUNC('month', e.event_date)          AS activity_month,
  DATEDIFF('month', fp.cohort_month, DATE_TRUNC('month', e.event_date)) AS months_since_cohort,
  APPROX_DISTINCT(e.user_id)                 AS active_users
FROM ${source_database}.${source_table} e
JOIN first_event fp ON e.user_id = fp.user_id
WHERE e.event_type = 'purchase'
  AND td_time_range(e.event_time,
    TD_TIME_ADD(TD_SCHEDULED_TIME(), '-1d', 'UTC'),
    TD_SCHEDULED_TIME(), 'UTC')
GROUP BY fp.cohort_month, DATE_TRUNC('month', e.event_date)
```

### Pattern 7: Percentile / Distribution

```sql
-- APPROX_PERCENTILE is faster and memory-efficient on large datasets
-- Use for p25/p50/p75/p95/p99 distribution metrics
INSERT INTO ${sink_database}.${project_prefix}_distribution
SELECT
  event_date,
  country,
  APPROX_PERCENTILE(event_value, 0.25) AS p25,
  APPROX_PERCENTILE(event_value, 0.50) AS median,
  APPROX_PERCENTILE(event_value, 0.75) AS p75,
  APPROX_PERCENTILE(event_value, 0.95) AS p95,
  APPROX_PERCENTILE(event_value, 0.99) AS p99,
  AVG(event_value)                      AS avg_value,
  STDDEV(event_value)                   AS stddev_value
FROM ${sink_database}.${project_prefix}_events_prep
WHERE td_time_range(event_time,
  TD_TIME_ADD(TD_SCHEDULED_TIME(), '-1d', 'UTC'),
  TD_SCHEDULED_TIME(), 'UTC')
GROUP BY event_date, country
```

### Aggregation Best Practices

| ✅ DO | ❌ DON'T |
|------|---------|
| Use `APPROX_DISTINCT()` for high-cardinality cols | Use `COUNT(DISTINCT)` on large tables |
| Use `APPROX_PERCENTILE()` for distributions | Use exact `PERCENTILE_CONT()` on large tables |
| Filter with `td_time_range()` first | Use `WHERE date >= CURRENT_DATE - INTERVAL ...` |
| Use `COALESCE(SUM(col), 0)` for nullable metrics | Leave NULL metric columns |
| Aggregate at natural grain, then join dimensions | Join dimensions before aggregating |
| Target < 100K rows (soft limit, 100K-500K acceptable) | Leave output cardinality unchecked; exceed 500K without testing |

---

## Schedule Configuration (Reference for Step 2c)

Configure the `schedule:` block in `<project_name>_launch.dig`. Use `workflow-skills:digdag` for full Digdag schedule operator reference.

### Schedule Patterns

```yaml
# Daily at 2 AM UTC (most common — off-hours, before business start)
schedule:
  daily>: "02:00:00"

# Daily at 9 AM in customer's timezone
timezone: Asia/Tokyo
schedule:
  daily>: "09:00:00"

# Every Monday at 8 AM (weekly report)
timezone: America/New_York
schedule:
  cron>: "0 8 ? * MON"

# First day of month at 2 AM (monthly financials)
schedule:
  cron>: "0 2 1 * ?"

# Every 4 hours (near-real-time monitoring)
schedule:
  cron>: "0 */4 * * ?"

# Business hours only, hourly Mon–Fri
timezone: America/New_York
schedule:
  cron>: "0 9-17 ? * MON-FRI"
```

### Timezone Reference

```yaml
timezone: UTC                    # Default — always works
timezone: America/New_York       # Eastern
timezone: America/Los_Angeles    # Pacific
timezone: Europe/London          # GMT/BST
timezone: Europe/Paris           # CET/CEST
timezone: Asia/Tokyo             # JST
timezone: Asia/Singapore         # SGT
timezone: Australia/Sydney       # AEDT/AEST
```

### Cron Cheat Sheet

| Pattern | Meaning |
|---------|---------|
| `0 2 * * *` | Daily 2 AM |
| `0 9 ? * MON` | Every Monday 9 AM |
| `0 2 1 * ?` | 1st of month 2 AM |
| `0 2 L * ?` | Last day of month 2 AM |
| `0 */4 * * ?` | Every 4 hours |
| `*/30 * * * ?` | Every 30 minutes |
| `0 9-17 * * ?` | Hourly 9 AM–5 PM |
| `0 9 ? * MON-FRI` | Weekdays 9 AM |
| `0 2 ? * MON#1` | First Monday of month |

### Digdag Session Variables (use in SQL)

```sql
-- Available in all .dig-embedded SQL:
-- ${session_time}        — Current scheduled run time (ISO 8601)
-- ${session_date}        — Current run date (YYYY-MM-DD)
-- ${session_unixtime}    — Unix timestamp of run
-- ${last_session_time}   — Previous scheduled run time

WHERE td_time_range(event_time,
  '${moment(session_time).subtract(1, "days").format("YYYY-MM-DD")}',
  '${session_date}', 'UTC')
```

### Questions to Ask the User (from Stage A Step 1e / 1f)

| Question | Options |
|----------|---------|
| How often should the dashboard refresh? | Daily (default) / Weekly / Monthly / Hourly |
| What time should it run? | 2 AM off-hours (default) / Before business start / Custom |
| What timezone? | UTC (default) / User's local timezone |
| Exclude weekends? | No (default) / Yes — use `MON-FRI` cron |

### Common Mistakes

| ❌ Mistake | ✅ Fix |
|-----------|-------|
| Hardcoding UTC when the user is in JST | Always confirm timezone in Stage A Step 1e |
| Scheduling during peak traffic | Suggest 2–4 AM or after ETL window closes |
| Hourly when daily suffices | Ask "how often do you actually look at this?" |
| Not confirming when source data arrives | Ask "when does ETL complete?" — schedule after |
---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
