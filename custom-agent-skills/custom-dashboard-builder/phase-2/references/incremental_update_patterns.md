---
name: dashboard-incremental-update-patterns
description: |
  Reference guide for designing incremental updates to pre-aggregated tables.
  Shows three patterns (append-only, upsert, state-managed) with SQL examples,
  performance comparisons, and decision logic for choosing the right approach.
---

# Incremental Update Patterns for Dashboard Workflows

> **Note on config keys below:** this file uses an illustrative `incremental_strategy`/`fresh_run` schema to explain the three conceptual patterns. The embedded `workflow-templates/input_params.yaml` implements Pattern 1 (Append-Only) out of the box via `refresh_mode: 'full' | 'incremental'` + `incremental_look_back_days` — see `input_params_examples.md`. Only reach for the Upsert or State Managed patterns below if Step 2h's eligibility assessment finds tasks the built-in `refresh_mode` branching doesn't cover (e.g. source data that gets corrected after the fact).

## Critical SQL Rules (Learned from Production)

Before choosing an incremental pattern, note these hard rules for TD digdag workflows:

### Rule 1: Use `SELECT`, not `INSERT INTO`

The `td>` operator with `create_table:` runs your SQL as a `SELECT` and writes results automatically. Never use `INSERT INTO` inside the SQL file — the target table doesn't exist yet on first run and the operator will fail.

```sql
-- ✅ CORRECT — plain SELECT; td> handles writing
SELECT date, region, SUM(amount) AS revenue
FROM source_db.orders
WHERE td_time_range(time, '${start_date}', '${end_date}', 'UTC')
GROUP BY date, region

-- ❌ WRONG — INSERT INTO fails on first run (table doesn't exist yet)
INSERT INTO sink_db.orders_kpis
SELECT date, region, SUM(amount) AS revenue ...
```

### Rule 2: Multi-Breakdown Tables → `UNION ALL` in One SQL File

For SINK tables with multiple row types (overall + by_dimension + monthly_trend), put all breakdowns in one SQL file using `UNION ALL`. Do NOT create multiple `.dig` tasks writing to the same SINK table.

```sql
-- ✅ CORRECT — all breakdowns in one SELECT + UNION ALL
SELECT 'overall' AS breakdown_type, 'all' AS breakdown_value,
       COUNT(*) AS total, SUM(amount) AS revenue
FROM source_db.orders
WHERE td_time_range(time, '${start_date}', '${end_date}', 'UTC')

UNION ALL

SELECT 'monthly' AS breakdown_type,
       DATE_FORMAT(FROM_UNIXTIME(time), '%Y-%m') AS breakdown_value,
       COUNT(*) AS total, SUM(amount) AS revenue
FROM source_db.orders
WHERE td_time_range(time, '${start_date}', '${end_date}', 'UTC')
GROUP BY DATE_FORMAT(FROM_UNIXTIME(time), '%Y-%m')
```

---

## Overview

When building production dashboards with scheduled runs, **incremental updates** are critical for cost efficiency and speed. Instead of re-aggregating all historical data every run, process only new/changed data since the last run.

**Performance Impact:**
- ❌ Full re-aggregation: 10-15 minutes, $50-100 cost per run
- ✅ Incremental update: 30 seconds, $1-2 cost per run
- **Savings: 95% reduction in time and cost**

---

## Three Incremental Patterns

### Pattern 1: Append-Only (Recommended for Simple Cases)

**When to use:**
- Source data is never updated, only appended
- New events arrive continuously
- Perfect for event streams, logs, transactions

**Characteristics:**
- Simple to implement
- Minimal state tracking
- Fastest execution (30 sec)
- Best for high-volume append-only data

**Example: Append-Only Aggregation**

```sql
-- Only process data from last 1-2 days
-- Accounts for late arrivals (events delayed by 1 day)

SELECT
  DATE(event_timestamp) as date,
  region,
  SUM(amount) as total_revenue,
  COUNT(*) as transaction_count,
  CURRENT_TIMESTAMP() as _load_time
FROM ${source_database}.events
WHERE DATE(event_timestamp) BETWEEN 
  CURRENT_DATE() - INTERVAL '1 day'
  AND CURRENT_DATE()
AND status = 'completed'
AND email NOT LIKE '%@test.%'
GROUP BY DATE(event_timestamp), region
```

**Workflow Integration:**

```yaml
+aggregate_incremental:
  td>: sql/03_aggregate_incremental_metrics.sql
  create_table: dashboard_metrics_temp

+delete_stale_dates:
  td>: |
    DELETE FROM ${sink_database}.${output_metrics_table}
    WHERE date >= (SELECT MIN(date) FROM dashboard_metrics_temp)

+insert_fresh:
  td>: |
    INSERT INTO ${sink_database}.${output_metrics_table}
    SELECT * FROM dashboard_metrics_temp
```

**Configuration:**

```yaml
incremental_strategy:
  mode: "append"
  look_back_days: 2  # 1 day data + 1 day buffer for late arrivals
  partition_column: "event_timestamp"
  fresh_run: "yes"  # First run only
```

---

### Pattern 2: Upsert (For Data Corrections)

**When to use:**
- Source data might be corrected or re-sent
- Customer reports "metric was wrong yesterday"
- Need to re-process 2-3 days of history
- Data has update timestamps or event IDs

**Characteristics:**
- Handles data corrections
- Look back multiple days to catch updates
- Delete + re-insert for affected dates
- Runtime: 1-2 minutes

**Example: Upsert with Deduplication**

```sql
-- Process last 3 days to catch corrections
-- Remove duplicates (if events re-sent multiple times)

WITH fresh_metrics AS (
  SELECT
    DATE(event_timestamp) as date,
    region,
    SUM(amount) as total_revenue,
    COUNT(*) as transaction_count,
    CURRENT_TIMESTAMP() as _load_time,
    ROW_NUMBER() OVER (
      PARTITION BY DATE(event_timestamp), region 
      ORDER BY last_modified DESC
    ) as rn
  FROM ${source_database}.events
  WHERE DATE(event_timestamp) BETWEEN 
    CURRENT_DATE() - INTERVAL '3 days'
    AND CURRENT_DATE()
  AND status = 'completed'
  AND email NOT LIKE '%@test.%'
  GROUP BY DATE(event_timestamp), region
),

-- Dedup: keep only latest version of each date/region
deduped AS (
  SELECT * FROM fresh_metrics
  WHERE rn = 1
),

-- Keep old data (older than 3 days)
old_data AS (
  SELECT * FROM ${sink_database}.${output_metrics_table}
  WHERE date < CURRENT_DATE() - INTERVAL '3 days'
)

-- Combine fresh (last 3 days) + old (before 3 days)
SELECT * FROM deduped
UNION ALL
SELECT * FROM old_data
```

**Workflow Integration:**

```yaml
+calculate_upsert_range:
  td>: |
    SELECT 
      CURRENT_DATE() - INTERVAL '3 days' as lookback_start,
      CURRENT_DATE() as lookback_end
  store_last: date_range

+aggregate_upsert:
  td>: sql/03_aggregate_upsert_metrics.sql
  create_table: dashboard_metrics_fresh

+remove_lookback:
  td>: |
    DELETE FROM ${sink_database}.${output_metrics_table}
    WHERE date >= '${date_range.lookback_start}'

+insert_upsert:
  td>: |
    INSERT INTO ${sink_database}.${output_metrics_table}
    SELECT * FROM dashboard_metrics_fresh
```

**Configuration:**

```yaml
incremental_strategy:
  mode: "upsert"
  look_back_days: 3  # Re-process 3 days to catch corrections
  partition_column: "event_timestamp"
  dedup_column: "last_modified"  # Use most recent version
  fresh_run: "yes"
```

**When Upsert Helps (Example):**

```
Day 1 (Tuesday 2 AM):
  - Aggregate Monday's data
  - Output: 100K transactions, $500K revenue

Day 2 (Wednesday 2 AM):
  - Some Monday transactions corrected/refunded
  - Upsert pattern re-processes Monday (look_back_days=3)
  - Output: 98K transactions, $495K revenue (updated)

Customer never sees stale data!
```

---

### Pattern 3: State Managed (For Complex Transformations)

**When to use:**
- Complex transformations requiring state tracking
- Multiple source tables with different update frequencies
- Need exact "last processed" timestamp
- Handling dedups, corrections, and late arrivals simultaneously

**Characteristics:**
- Most control and flexibility
- Tracks "last processed" state in table
- Process only delta since last run
- Runtime: 30-60 seconds
- Best for high-volume, mission-critical dashboards

**Example: State-Managed with Delta Processing**

```sql
-- Step 1: Get last processed state
WITH last_state AS (
  SELECT MAX(last_processed_timestamp) as last_run
  FROM ${sink_database}.dashboard_state
  WHERE dashboard_name = 'revenue_dashboard'
),

-- Step 2: Find new/updated events since last run
new_events AS (
  SELECT
    event_id,
    DATE(event_timestamp) as date,
    region,
    amount,
    CASE WHEN last_modified > '${last_run}' THEN 'UPDATED'
         ELSE 'NEW' END as change_type,
    last_modified
  FROM ${source_database}.events
  CROSS JOIN last_state
  WHERE last_modified > COALESCE(last_state.last_run, '2020-01-01')
  AND status = 'completed'
),

-- Step 3: Aggregate new/updated events
fresh_metrics AS (
  SELECT
    date,
    region,
    SUM(amount) as total_revenue,
    COUNT(DISTINCT event_id) as transaction_count,
    CURRENT_TIMESTAMP() as _load_time
  FROM new_events
  GROUP BY date, region
),

-- Step 4: Find affected dates (any date with new/updated events)
affected_dates AS (
  SELECT DISTINCT date FROM fresh_metrics
),

-- Step 5: Remove old versions of affected dates
old_data AS (
  SELECT * FROM ${sink_database}.${output_metrics_table}
  WHERE date NOT IN (SELECT date FROM affected_dates)
)

-- Combine: old unaffected + fresh aggregates
SELECT * FROM fresh_metrics
UNION ALL
SELECT * FROM old_data
```

**Workflow Integration:**

```yaml
+get_state:
  td>: sql/02_get_dashboard_state.sql
  store_last: last_state

+identify_delta:
  td>: sql/03_identify_delta_events.sql
  create_table: delta_events

+aggregate_delta:
  td>: sql/04_aggregate_delta_metrics.sql
  create_table: fresh_metrics

+merge_with_old:
  td>: sql/05_merge_old_and_fresh.sql
  create_table: dashboard_metrics_new

+swap_tables:
  td>: |
    DROP TABLE IF EXISTS ${sink_database}.${output_metrics_table}_old;
    ALTER TABLE ${sink_database}.${output_metrics_table} 
      RENAME TO ${output_metrics_table}_old;
    ALTER TABLE dashboard_metrics_new 
      RENAME TO ${output_metrics_table};

+update_state:
  td>: |
    INSERT INTO ${sink_database}.dashboard_state
    SELECT 
      'revenue_dashboard' as dashboard_name,
      CURRENT_TIMESTAMP() as last_processed_timestamp
    WHERE NOT EXISTS (
      SELECT 1 FROM ${sink_database}.dashboard_state
      WHERE dashboard_name = 'revenue_dashboard'
    );
    
    UPDATE ${sink_database}.dashboard_state
    SET last_processed_timestamp = CURRENT_TIMESTAMP()
    WHERE dashboard_name = 'revenue_dashboard'
```

**State Table Schema:**

```sql
CREATE TABLE IF NOT EXISTS ${sink_database}.dashboard_state (
  dashboard_name VARCHAR(255) PRIMARY KEY,
  last_processed_timestamp TIMESTAMP,
  rows_processed_last_run INT,
  last_error_message VARCHAR(1024),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
```

**Configuration:**

```yaml
incremental_strategy:
  mode: "state_managed"
  state_table: "dashboard_state"
  state_update_frequency: "every_run"
  partition_column: "event_timestamp"
  fresh_run: "yes"
```

---

## Decision Matrix: Which Pattern to Choose

```
Question 1: Is source data ever updated/corrected?
│
├─ NO (append-only events)
│  └─→ Question 2: How fast does new data arrive?
│      ├─ Hours or later (late arrivals common)
│      │  └─→ USE PATTERN 1 (Append-Only)
│      │     look_back_days: 2
│      │     Runtime: 30 sec
│      │
│      └─ Minutes (real-time streams)
│         └─→ USE PATTERN 1 (Append-Only)
│            look_back_days: 1
│            Runtime: 15 sec
│
└─ YES (corrections/updates possible)
   └─→ Question 3: How complex is the transformation?
       ├─ Simple (direct aggregation)
       │  └─→ USE PATTERN 2 (Upsert)
       │     look_back_days: 2-3
       │     Runtime: 1-2 min
       │
       └─ Complex (multiple joins, dedup, state)
          └─→ USE PATTERN 3 (State Managed)
             look_back_days: dynamic (from state)
             Runtime: 30-60 sec
```

---

## Configuration Examples

### Example 1: Append-Only (Simple Event Stream)

```yaml
# input_params.yml
incremental_strategy:
  mode: "append"
  look_back_days: 2
  partition_column: "created_at"
  fresh_run: "yes"

refresh_schedule: "0 2 * * *"  # 2 AM daily
historical_window: 365
```

**Why:** Raw event stream, never updated, arrives daily with 1-2 day delay

### Example 2: Upsert (E-commerce Orders)

```yaml
# input_params.yml
incremental_strategy:
  mode: "upsert"
  look_back_days: 3
  partition_column: "order_date"
  dedup_column: "updated_at"
  fresh_run: "yes"

refresh_schedule: "0 2 * * *"  # 2 AM daily
historical_window: 365
```

**Why:** Orders can be refunded/cancelled, need to catch corrections from previous 2-3 days

### Example 3: State Managed (High-Volume CDP)

```yaml
# input_params.yml
incremental_strategy:
  mode: "state_managed"
  state_table: "dashboard_cdp_state"
  partition_column: "event_timestamp"
  fresh_run: "yes"

refresh_schedule: "0 * * * *"  # Every hour (more frequent)
historical_window: 365
```

**Why:** Large volume, complex joins, need to track exact "last processed" for audit

---

## Best Practices

### 1. Always Use Incremental in Production

```yaml
# DON'T: Full re-aggregation every time
fresh_run: "no"  # This re-processes all history every day!

# DO: Incremental mode for production
incremental_strategy:
  mode: "upsert"
  look_back_days: 2
```

### 2. First Run = Full History, Then Incremental

```yaml
# First deployment: fresh_run: "yes" (illustrative — the embedded template uses refresh_mode: 'full' for the same purpose)
# This processes all 365 days of history once

# After first run succeeds, change to:
fresh_run: "no"
# Now runs only do incremental lookback_days
```

### 3. Monitor Rows Processed

```sql
-- Add monitoring query to workflow
+monitor:
  td>: |
    SELECT 
      CURRENT_DATE() as run_date,
      COUNT(*) as rows_processed,
      SUM(amount) as revenue_aggregated
    FROM dashboard_metrics_temp
    GROUP BY CURRENT_DATE()
```

Track: If rows_processed drops to zero for 3 consecutive runs, investigate!

### 4. Handle Late Arrivals

```yaml
# Events typically arrive 1-2 days late
look_back_days: 2

# Upsert pattern will:
# - Day 1 (Tuesday 2 AM): Process Monday (might be incomplete)
# - Day 2 (Wednesday 2 AM): Re-process Monday + Tuesday (Monday now complete)
# - Day 3 (Thursday 2 AM): Re-process Tuesday + Wednesday (Tuesday complete)
```

### 5. Test Both Patterns (First vs Subsequent Runs)

```
Fresh Run (fresh_run: "yes"):
- Input: Entire history (365 days)
- Expected output: Full dataset

Incremental Run (fresh_run: "no"):
- Input: Last look_back_days (e.g., 2 days)
- Expected output: Same as fresh run but only 2 days
- Comparison: Should produce identical results for same date range
```

---

## Performance Benchmarks

| Scenario | Pattern | Runtime | Cost | Notes |
|----------|---------|---------|------|-------|
| 100M events/day, 1 year retention | Append-Only | 30 sec | $1 | Simple case |
| 100M events/day, with corrections | Upsert | 2 min | $3 | Extra 3-day lookback |
| 1B events/day, complex joins | State Managed | 1 min | $2 | Delta processing |
| 1B events/day, full re-agg | N/A | 15 min | $30 | ❌ Don't do this! |

---

## Troubleshooting

**Problem: Metrics changed from yesterday (seems wrong)**

→ Check look_back_days setting. If events corrected/refunded, re-processing previous days is correct!

**Problem: Workflow takes 10+ minutes**

→ Check if incremental mode is enabled. Are you re-processing all history?

```sql
-- Debug: Check WHERE clause
SELECT COUNT(*) FROM source_table
WHERE date >= CURRENT_DATE() - INTERVAL '2 days'  ← Should be small
-- vs
SELECT COUNT(*) FROM source_table  ← Should be huge
```

**Problem: Dashboard incomplete (missing recent data)**

→ Check partition_column. Events arriving late? Increase look_back_days.

---

## Summary

| Pattern | Setup | Runtime | Cost | Best For |
|---------|-------|---------|------|----------|
| **Append-Only** | Simple | 30 sec | $1 | Event streams, never updated |
| **Upsert** | Moderate | 1-2 min | $3 | Data with corrections |
| **State Managed** | Complex | 30-60 sec | $2 | High-volume, mission-critical |

**Default recommendation: Start with Upsert** (good balance of simplicity and reliability)
---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
