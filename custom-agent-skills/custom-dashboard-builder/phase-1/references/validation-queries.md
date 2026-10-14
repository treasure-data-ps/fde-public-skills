# Stage B: Query Patterns for Validation

## Metric Validation Queries

### Basic Metric Queries (Apply Stage A Filters)

```sql
-- Total Revenue (SUM with filters)
SELECT SUM(order_amount) as total_revenue 
FROM orders 
WHERE order_date >= DATE_SUB(current_date, interval 90 day)
AND status != 'cancelled';

-- Order Count (COUNT with filters)
SELECT COUNT(*) as order_count 
FROM orders 
WHERE order_date >= DATE_SUB(current_date, interval 90 day)
AND status != 'cancelled';

-- Unique Customers (COUNT DISTINCT)
SELECT COUNT(DISTINCT customer_id) as unique_customers 
FROM orders 
WHERE order_date >= DATE_SUB(current_date, interval 90 day)
AND status != 'cancelled';

-- Average Order Value (AVG)
SELECT AVG(order_amount) as avg_order_value 
FROM orders 
WHERE order_date >= DATE_SUB(current_date, interval 90 day)
AND status != 'cancelled';
```

### Rate/Ratio Metrics

```sql
-- Conversion Rate (events → conversions)
SELECT 
  COUNT(DISTINCT CASE WHEN event_type = 'conversion' THEN user_id END) as converters,
  COUNT(DISTINCT user_id) as total_users,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'conversion' THEN user_id END) 
        / COUNT(DISTINCT user_id), 2) as conversion_rate_pct
FROM events 
WHERE event_date >= DATE_SUB(current_date, interval 30 day);

-- Churn Rate (users in period N vs period N-1)
WITH prev_period AS (
  SELECT DISTINCT customer_id 
  FROM orders 
  WHERE order_date BETWEEN DATE_SUB(current_date, interval 60 day) AND DATE_SUB(current_date, interval 30 day)
),
curr_period AS (
  SELECT DISTINCT customer_id 
  FROM orders 
  WHERE order_date >= DATE_SUB(current_date, interval 30 day)
)
SELECT 
  (SELECT COUNT(*) FROM prev_period) as prev_period_customers,
  (SELECT COUNT(*) FROM curr_period) as curr_period_customers,
  ROUND(100.0 * (SELECT COUNT(*) FROM prev_period) - (SELECT COUNT(*) FROM curr_period) / 
        (SELECT COUNT(*) FROM prev_period), 2) as churn_rate_pct
FROM (SELECT 1);
```

---

## Dimension Validation Queries

### Discover Distinct Values

```sql
-- Get all distinct values for a dimension
SELECT DISTINCT region 
FROM customers 
ORDER BY region;

-- Get dimension value counts
SELECT segment, COUNT(DISTINCT customer_id) as customer_count 
FROM customers 
GROUP BY segment 
ORDER BY customer_count DESC;

-- Check for nulls in dimension
SELECT 
  COUNT(*) as total_rows,
  COUNT(region) as non_null_count,
  COUNT(*) - COUNT(region) as null_count
FROM customers;
```

---

## Exclusion Rule Validation

```sql
-- Validate exclusion rule: "Exclude cancelled orders"
SELECT 
  COUNT(*) as total_orders,
  SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_count,
  SUM(CASE WHEN status != 'cancelled' THEN 1 ELSE 0 END) as non_cancelled_count,
  ROUND(100.0 * SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_excluded
FROM orders;

-- Validate multiple exclusion rules
SELECT 
  COUNT(*) as total_events,
  SUM(CASE WHEN environment = 'test' THEN 1 ELSE 0 END) as test_events,
  SUM(CASE WHEN environment = 'test' THEN 0 ELSE 1 END) as production_events
FROM events;
```

---

## Join Path Validation

```sql
-- Test join cardinality (should be 1-to-1, not 1-to-many)
SELECT o.order_id, COUNT(*) as join_count
FROM orders o 
JOIN customers c ON o.customer_id = c.customer_id 
GROUP BY o.order_id 
HAVING COUNT(*) > 1;
-- Expected result: ZERO rows (no duplicates)

-- If above returns rows, investigate the join issue
-- Check if customer has multiple rows:
SELECT customer_id, COUNT(*) as row_count
FROM customers 
GROUP BY customer_id 
HAVING COUNT(*) > 1;

-- Check if customer_id is nullable
SELECT 
  COUNT(*) as total_orders,
  COUNT(customer_id) as non_null_count,
  COUNT(*) - COUNT(customer_id) as null_count
FROM orders;
```

---

## Data Freshness Checks

```sql
-- Check last updated timestamp
SELECT 
  MAX(order_date) as latest_order_date,
  current_date as today,
  DATEDIFF(DAY, MAX(order_date), current_date) as days_since_last_update
FROM orders;

-- Check for stale data
SELECT 
  COUNT(*) as total_rows,
  COUNT(CASE WHEN order_date >= DATE_SUB(current_date, interval 7 day) THEN 1 END) as recent_rows_7d,
  COUNT(CASE WHEN order_date >= DATE_SUB(current_date, interval 30 day) THEN 1 END) as recent_rows_30d
FROM orders;
```

---

## Large Table Optimization

### Presto (Default) - Apply Filters First

```sql
-- ❌ RISKY: May timeout on large tables
SELECT SUM(revenue) FROM orders;

-- ✅ BETTER: Apply Stage A filters first
SELECT SUM(revenue) FROM orders 
WHERE order_date >= DATE_SUB(current_date, interval 90 day)
AND status != 'cancelled'
AND region IN ('North America', 'Europe');  -- Add dimension filters
```

### Hive (If Presto Times Out)

```sql
-- Enable parallel execution
SET hive.exec.parallel=true;
SET hive.exec.parallel.thread.number=8;

-- Run query with Hive
SELECT SUM(revenue) FROM orders 
WHERE order_date >= DATE_SUB(current_date, interval 90 day)
AND status != 'cancelled';
```

### Query Performance Baseline

Document this for the workflow/build decision:

```
Query: SUM(order_amount) for last 90 days, non-cancelled orders
- Table size: 500M rows
- Presto execution time: 8 seconds
- Hive execution time: 3 seconds (with parallel=true)
- Performance notes: Presto acceptable; Hive preferred for large windows
```

---

## Data Quality Gate — Pre-Phase 2/3 Checks (BOTH PATHS)

**CRITICAL: Run these checks BEFORE routing to Phase 2 (Workflow) or Phase 3 (Build). Data quality issues caught here prevent failures in both paths.**

**Red flags that block BOTH paths:**
- Query returns 0 rows (no data to work with)
- Metric contains significant nulls (≥10%)
- Metric contains unexpected negatives
- Data is stale (unacceptable for use case)
- Cardinality extremely high (>1M unique values on a dimension)
- Join explosion (row count >> base table)

**Path-specific performance thresholds:**
- Phase 2 (Workflow): Query must complete in < 30 seconds (daily aggregation jobs)
- Phase 3 (Build, no workflow): Query must complete in < 60 seconds (on-demand queries)

---

### Check 1: Verify Metric Columns Exist & Data Types Match

```sql
-- Verify metric column exists and has correct data type
SELECT 
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_schema = '{database}'
AND table_name = '{table}'
AND column_name IN ('{metric_col1}', '{metric_col2}', '{dimension_col1}')
ORDER BY column_name;

-- Expected result:
-- - metric columns are BIGINT, DECIMAL, FLOAT, INT (numeric)
-- - dimension columns are VARCHAR, STRING, INT (not TIMESTAMP)
-- - is_nullable tells you if NULL is possible
```

---

### Check 2: Metric Nulls — Critical Red Flag ⚠️

```sql
-- Check null percentage in each metric column
SELECT 
  COUNT(*) as total_rows,
  COUNT({metric_col}) as non_null_count,
  COUNT(*) - COUNT({metric_col}) as null_count,
  ROUND(100.0 * (COUNT(*) - COUNT({metric_col})) / COUNT(*), 2) as null_pct
FROM {table}
WHERE {time_filter};  -- Apply Stage A date range

-- RED FLAG: If null_pct >= 10%, metric may not be reliable
-- ACTION: Use COALESCE({metric_col}, 0) in the workflow/build query
```

---

### Check 3: Metric Unexpected Negatives — Critical Red Flag ⚠️

```sql
-- Check for negative values (only if metric should be >= 0)
SELECT 
  COUNT(*) as total_rows,
  COUNT(CASE WHEN {metric_col} < 0 THEN 1 END) as negative_count,
  ROUND(100.0 * COUNT(CASE WHEN {metric_col} < 0 THEN 1 END) / COUNT(*), 2) as negative_pct,
  MIN({metric_col}) as min_value,
  MAX({metric_col}) as max_value
FROM {table}
WHERE {time_filter};

-- RED FLAG: Unexpected negatives (e.g., revenue < 0 when none expected)
-- ACTION: Investigate reason (refunds? data entry error?) and document
```

---

### Check 4: Metric Zero Values — Possible Quality Issue

```sql
-- Check distribution of zero vs non-zero values
SELECT 
  COUNT(*) as total_rows,
  COUNT(CASE WHEN {metric_col} = 0 THEN 1 END) as zero_count,
  COUNT(CASE WHEN {metric_col} > 0 THEN 1 END) as non_zero_count,
  ROUND(100.0 * COUNT(CASE WHEN {metric_col} = 0 THEN 1 END) / COUNT(*), 2) as zero_pct,
  ROUND(100.0 * COUNT(CASE WHEN {metric_col} > 0 THEN 1 END) / COUNT(*), 2) as non_zero_pct
FROM {table}
WHERE {time_filter};

-- CAUTION: If zero_pct > 30%, distribution may be skewed
-- ACTION: Confirm this is expected (many customers with $0 activity?) or investigate
```

---

### Check 5: Metric Completeness — Query Returns Rows

```sql
-- Apply Stage A filters; confirm data exists after filtering
SELECT 
  COUNT(*) as row_count_after_filters,
  COUNT(DISTINCT {id_col}) as unique_ids
FROM {table}
WHERE {time_filter}
AND {exclusion_filters};

-- RED FLAG: If row_count = 0 after all Stage A filters applied
-- ACTION: Review exclusion rules — are they too strict?
```

---

### Check 6: Data Freshness — Stale Data Detection ⚠️

**Skip this check for Snapshot tables (no business event time column).**

For Behavior and Aggregate tables only:

```sql
-- Check when data was last updated (use business event datetime, NOT TD's `time` column)
-- `time` = insert time (when row was written to TD), NOT event time
SELECT 
  MIN({event_date_col}) as earliest_event,
  MAX({event_date_col}) as latest_event,
  current_date as today,
  DATEDIFF(day, MAX({event_date_col}), current_date) as days_since_latest_event
FROM {table};

-- Also check TD insert time to confirm data is flowing:
SELECT 
  MIN(time) as earliest_insert,
  MAX(time) as latest_insert,
  DATEDIFF(day, MAX(time), current_timestamp) as hours_since_insert
FROM {table};

-- RED FLAG: If days_since_latest_event > acceptable for use case (1 day for daily, 7 for weekly)
-- RED FLAG: If latest_insert is very old, data pipeline may be stuck
-- ACTION: Confirm with the user — is refresh on schedule? Check ETL status
```

**For Snapshot tables:** No event datetime column → no freshness age to check. Confirm Snapshot is point-in-time intentional (e.g., customer profile snapshot as of yesterday) and use case accepts it.

---

### Check 7: Dimension Cardinality — Catch High-Cardinality Issues

```sql
-- Check unique value count for each dimension
SELECT 
  COUNT(DISTINCT {dimension_col1}) as unique_{dimension_col1},
  COUNT(DISTINCT {dimension_col2}) as unique_{dimension_col2},
  COUNT(DISTINCT {dimension_col3}) as unique_{dimension_col3}
FROM {table}
WHERE {time_filter};

-- RED FLAG: If unique_count > 1,000,000 on any dimension
-- ACTION: This dimension may not be suitable for a dashboard filter (too many values)
-- OPTION: Aggregate/bucket it (e.g., user_id is too high-cardinality; use customer_segment instead)
```

---

### Check 8: Dimension NULL Values

```sql
-- Check null percentage in each dimension
SELECT 
  COUNT(*) as total_rows,
  COUNT({dimension_col}) as non_null_count,
  COUNT(*) - COUNT({dimension_col}) as null_count,
  ROUND(100.0 * (COUNT(*) - COUNT({dimension_col})) / COUNT(*), 2) as null_pct
FROM {table}
WHERE {time_filter};

-- CAUTION: If null_pct >= 5%, filter may have "Unknown" rows
-- ACTION: Decide: drop NULLs in the workflow/build query, or include them as "Unknown" category?
```

---

### Check 9: Join Cardinality — Confirm 1-to-1, Catch Explosions

```sql
-- Before join
SELECT COUNT(*) as base_table_rows FROM {base_table};

-- After join (critical — do NOT skip this)
SELECT 
  COUNT(*) as joined_rows,
  COUNT(DISTINCT {base_id}) as unique_base_ids
FROM {base_table} b
JOIN {lookup_table} l ON b.{join_key} = l.{join_key}
WHERE {time_filter};

-- Expected: joined_rows ≈ base_table_rows (1-to-1) or slightly more (1-to-many, acceptable if documented)
-- RED FLAG: joined_rows >> base_table_rows (join explosion — duplicate rows)
-- ACTION: Check join key cardinality; use GROUP BY instead of JOIN if needed
```

---

### Check 10: Query Performance Baseline — ESSENTIAL for Both Paths ⚠️

**Document performance BEFORE routing to Phase 2 or Phase 3.**
- Phase 2 (Workflow): Daily aggregation jobs must complete in < 30 seconds
- Phase 3 (Build, no workflow): On-demand queries must complete in < 60 seconds

```sql
-- Time this query; document in state.md
-- Include ALL Stage A filters and exclusions
SELECT 
  {dimension_col1},
  {dimension_col2},
  SUM({metric_col1}) as metric1,
  SUM({metric_col2}) as metric2,
  COUNT(DISTINCT {id_col}) as unique_ids
FROM {table}
WHERE {time_filter}
AND {exclusion_filters}
GROUP BY {dimension_col1}, {dimension_col2};

-- RED FLAG (Phase 2): Query takes > 30 seconds
-- RED FLAG (Phase 3): Query takes > 60 seconds
-- ACTION: Add indexes on {dimension_col1}, {dimension_col2}, {time_filter_col}
--         or simplify query (fewer GROUP BY dimensions)
```

**Document result:**
```
Query Performance Baseline
- Query: SUM({metric}) GROUP BY {dimensions} (from Stage A)
- Table: {table_name} ({row_count} rows)
- Presto execution time: {X} seconds
- Path: Phase 2 (Workflow) | Phase 3 (Build, no workflow)
- Status (Phase 2): ✅ ACCEPTABLE (< 5s) | ⚠️ MARGINAL (5-30s) | ❌ TOO SLOW (> 30s)
         (Phase 3): ✅ ACCEPTABLE (< 5s) | ⚠️ MARGINAL (5-60s) | ❌ TOO SLOW (> 60s)
- If slow: recommended index(es) or query simplification
```

---

### Check 11: Comprehensive Data Quality Summary (All-in-One)

**Run this after individual checks to catch combined issues:**

```sql
-- Comprehensive quality snapshot for all metrics + dimensions
SELECT 
  '{table_name}' as table_name,
  COUNT(*) as total_rows,
  COUNT(DISTINCT {id_col}) as unique_ids,
  COUNT(CASE WHEN {metric_col} IS NULL THEN 1 END) as metric_nulls,
  ROUND(100.0 * COUNT(CASE WHEN {metric_col} IS NULL THEN 1 END) / COUNT(*), 2) as metric_null_pct,
  COUNT(CASE WHEN {metric_col} < 0 THEN 1 END) as negative_metric_count,
  COUNT(CASE WHEN {metric_col} = 0 THEN 1 END) as zero_metric_count,
  MIN({metric_col}) as min_metric,
  MAX({metric_col}) as max_metric,
  ROUND(AVG({metric_col}), 2) as avg_metric,
  MIN({date_col}) as earliest_date,
  MAX({date_col}) as latest_date,
  DATEDIFF(day, MAX({date_col}), current_date) as days_since_update,
  COUNT(DISTINCT {dimension_col1}) as unique_{dimension_col1},
  COUNT(DISTINCT {dimension_col2}) as unique_{dimension_col2}
FROM {table}
WHERE {time_filter};
```

---

### Check 12: Go / No-Go Decision Template

**Fill this out BEFORE routing to Phase 2 or Phase 3.**

**⚠️ NOTE: Thresholds are GUIDELINES, not hard limits.**
- Some use cases legitimately have > 30% zero values (sparse data)
- Some product catalogs need > 1M cardinality (millions of SKUs)
- Some dimensions have > 5% nulls by design
- If you exceed a guideline threshold, document WHY it's acceptable for this use case, then proceed

```markdown
## Data Quality Gate — APPROVAL REQUIRED

**Dashboard:** {dashboard_name}
**Database:** {database_name}
**Date Checked:** {YYYY-MM-DD}
**Checked By:** {your_name}
**Target Path:** Phase 2 (Workflow) | Phase 3 (Build, no workflow)

### Critical Checks (MUST PASS FOR BOTH PATHS)
- [ ] Query returns rows (> 0 rows after Stage A filters)
- [ ] Metric nulls < 10% (or documented exception)
- [ ] No unexpected negative values (or documented reason)
- [ ] Data freshness acceptable (suitable for use case)
- [ ] Join cardinality verified (no explosion)
- [ ] Query performance acceptable
  - Phase 2 (Workflow): < 30 seconds ✅
  - Phase 3 (Build, no workflow): < 60 seconds ✅

### Caution Items (Review Required — guidelines, not hard limits)
- [ ] Metric zero values < 30% (or confirmed as normal for this use case)
- [ ] Dimension cardinality < 1,000,000 (or plan for bucketing)
- [ ] Dimension null values < 5% (or plan for "Unknown" category)

### DECISION
- [ ] ✅ READY FOR PHASE 2/3 — All critical checks passed, data quality acceptable
- [ ] ⚠️ MARGINAL — Caution items present; confirm acceptable before Phase 2/3
- [ ] ❌ BLOCKED — Critical checks failed; resolve before proceeding to either phase

**If BLOCKED, document issue + resolution plan:**
_________________________________________________________________________
```

---

## Treasure Data CLI Commands

```bash
# List all databases
tdx databases

# List tables in a database (NOT "tdx table <database>" — that command doesn't exist)
tdx tables --in <database>

# Get column schema for a specific table (tdx describe always requires a table —
# it does NOT accept a bare database name or a wildcard pattern)
tdx describe <database>.<table>

# Run ad-hoc query for validation (NOT "tdx query <database> \"SQL\"" — database is
# a -d/--database flag, not a positional argument)
tdx query "SELECT SUM(revenue) FROM orders LIMIT 10" -d <database>

# Get table row count
tdx query "SELECT COUNT(*) FROM orders" -d <database>

# Get date range
tdx query "SELECT MIN(order_date), MAX(order_date) FROM orders" -d <database>
```

**Verified against the real CLI** (`tdx describe --help`, `tdx tables --help`, `tdx query --help`):
- `tdx describe <database>` alone errors with a usage message — always pass `<database>.<table>` or `<table> --in <database>`.
- `tdx table <database>` is not a real command — the correct form is `tdx tables --in <database>` (or `tdx tables "<database>.*"`).
- `tdx query <database> "SQL"` is not valid — `database` is only accepted via `-d`/`--database`/`--in`, never as a leading positional argument.

---

## Query Performance Troubleshooting

| Issue | Solution |
|---|---|
| Query timeout in Presto | Try Hive with `set hive.exec.parallel=true` |
| Slow COUNT(*) on large table | Use `set hive.stats.autogather=true` to cache stats |
| Out of memory on JOIN | Use `set hive.exec.dynamic.memory.sort=true` |
| Need column statistics | Run: `ANALYZE TABLE orders COMPUTE STATISTICS;` |
| Confused about data type | Use: `tdx describe <db>.<table>` to see column types |

---

## Referencing TD Skills

For optimization help:
- **`sql-skills:trino-optimizer`** — Trino/Presto query optimization
- **`sql-skills:time-filtering`** — Time-window query patterns
- **`tdx-skills:tdx-basic`** — TD CLI commands and basics
---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
