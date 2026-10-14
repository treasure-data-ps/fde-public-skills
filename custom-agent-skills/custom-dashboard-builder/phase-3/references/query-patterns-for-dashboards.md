# SQL Query Patterns for Dashboards

Use these SQL patterns to extract real data for Stage B / Phase 2 validation and Phase 3-4 dashboard queries.

All patterns use standard SQL compatible with Treasure Data.

---

## Critical Performance Patterns (NEW)

### Always Run Queries in Parallel

When building dashboards with multiple queries, use JavaScript `Promise.all()` to execute queries concurrently instead of sequentially:

```javascript
// ❌ WRONG: Sequential (5s total if each query takes ~1s)
const metric1 = await executeQuery('SELECT ...');
const metric2 = await executeQuery('SELECT ...'); // Waits for metric1
const metric3 = await executeQuery('SELECT ...'); // Waits for metric2
// Total time: ~5 seconds

// ✅ CORRECT: Parallel (1.5s total, time of slowest query)
const [metric1, metric2, metric3, metric4, metric5] = await Promise.all([
  executeQuery('SELECT ...'),
  executeQuery('SELECT ...'),
  executeQuery('SELECT ...'),
  executeQuery('SELECT ...'),
  executeQuery('SELECT ...')
]);
// Total time: ~1.5 seconds (70% improvement!)
```

**Impact:** Query execution drops from sequential sum to the slowest single query.

---

### SELECT Only What the Template Reads

Every unnecessary column adds payload size and query time. Before writing queries:

1. **Map template column usage** — which fields does the dashboard display?
2. **Write query to fetch ONLY those columns** (no "might be useful later" columns)
3. **Add calculated fields in the inject script** if needed
4. **Never fetch unused pre-computed columns** (e.g., `rate_percent`, `status_friendly`)

```sql
-- ❌ WRONG: Fetching unused columns
SELECT customer_id, vehicle_model, region, service_type,
       fuel_type, vehicle_type, tickets_resolved,  -- Not used in dashboard!
       SUM(revenue) as total_revenue,
       AVG(satisfaction_score) as avg_score
FROM automotive_fact_customer_overview
GROUP BY customer_id, vehicle_model, region, service_type, fuel_type, vehicle_type, tickets_resolved;
-- Result: Extra 445 KB payload with zero benefit

-- ✅ CORRECT: Only dashboard columns
SELECT customer_id, vehicle_model, region, service_type,
       SUM(revenue) as total_revenue,
       AVG(satisfaction_score) as avg_score
FROM automotive_fact_customer_overview
GROUP BY customer_id, vehicle_model, region, service_type;
-- Result: Compact payload, faster transfer
```

---

### GROUP BY Filter Dimensions Only (SINK Grain Optimization)

If the underlying table has more dimensions than your dashboard filters on, push GROUP BY into SQL to avoid fan-out:

```sql
-- ❌ WRONG: SINK has 7 dimensions, dashboard only filters on 4
-- Result: 6,619 rows (customer appears multiple times due to vehicle fan-out)
SELECT * FROM automotive_fact_customer_overview;

-- ✅ CORRECT: GROUP BY only the 4 filter dimensions
SELECT customer_id, vehicle_model, region, service_type,
       SUM(revenue), AVG(satisfaction_score), COUNT(*)
FROM automotive_fact_customer_overview
GROUP BY customer_id, vehicle_model, region, service_type;
-- Result: 2,240 rows (60% reduction) + 60% smaller payload
```

**Integration:** Phase 3 Step 4b (Query Scaffolding) — always audit SINK grain vs filter dimensions before writing queries.

---

## PHASE 3 CRITICAL: Three Data Shapes Required

Every Phase 3 dashboard must generate exactly three query shapes for the two-tier filter architecture to work:

### Shape S1: Daily, No Dimensions (Global Date Filter)
```sql
-- Use: Overview KPIs when no dimension filter is active
-- Source: sink_overview_kpis (Workflow) or source table (Non-Workflow)
-- Key: Daily grain to support per-day filtering

SELECT date,
       SUM(net_revenue) as revenue,
       COUNT(DISTINCT order_id) as order_count,
       COUNT(DISTINCT customer_id) as unique_customers,
       SUM(email_sends) as email_sends
FROM sink_overview_kpis
WHERE td_time_range(date, '2026-06-23', '2026-07-23')
GROUP BY date
ORDER BY date ASC;
-- Result: ~31 rows (one per day)
```

### Shape S2: All-Time, With Dimensions (Breakdown Charts)
```sql
-- Use: Breakdown charts when filtering by dimension only (no date range)
-- Key: All-time aggregate, one row per dimension value

SELECT category, SUM(net_revenue) as revenue, COUNT(*) as count
FROM sink_sales_daily
GROUP BY category
ORDER BY revenue DESC;

-- Result: ~12 rows (one per category)
-- Use cases: "Revenue by category (all time)", "Orders by payment (all time)"
```

### Shape S3: Monthly + Dimensions ⭐ (CRITICAL - Respond to BOTH Filters)
```sql
-- Use: KPI cards when BOTH date range + dimension filter are active
-- Key: Monthly grain allows date filtering + dimensions allow filtering by category/region/etc
-- This shape is what enables dashboard responsiveness to both filter tiers

SELECT SUBSTR(date, 1, 7) as month,
       category,
       payment_type,
       status,
       SUM(net_revenue) as revenue,
       COUNT(DISTINCT order_id) as order_count,
       COUNT(DISTINCT customer_id) as unique_customers
FROM sink_sales_daily
WHERE td_time_range(date, '2025-01-01', '2026-12-31')
GROUP BY 1, 2, 3, 4
ORDER BY month ASC;
-- Result: 61 months × 12 categories × 4 payment_types × 3 statuses = ~8,784 rows
-- CRITICAL: Set LIMIT to at least 2× expected rows
LIMIT 20000;
```

**Why Three Shapes:**
- S1 only: Can't filter by dimension
- S2 only: Can't filter by date range
- S1 + S2 only: Can't do BOTH simultaneously
- S1 + S2 + S3: Full flexibility for two-tier architecture ✓

---

## ⚠️ WORKFLOW PATH: VARCHAR Date Columns in SINK Tables

**Critical:** SINK tables store dates as **VARCHAR** (e.g., `'2025-03-15'`) from `DATE_FORMAT(FROM_UNIXTIME(...), '%Y-%m-%d')`, not native DATE type.

When grouping by month in **Workflow queries**, do **NOT** use `DATE_FORMAT(date, '%Y-%m')`:

```sql
-- ❌ WRONG: DATE_FORMAT fails on VARCHAR
SELECT DATE_FORMAT(date, '%Y-%m') as month,
       SUM(revenue) as total
FROM sink_table
GROUP BY DATE_FORMAT(date, '%Y-%m');
-- Error: Invalid column/function in GROUP BY

-- ✅ CORRECT: Use SUBSTR to extract year-month
SELECT SUBSTR(date, 1, 7) as month,
       SUM(revenue) as total
FROM sink_table
GROUP BY SUBSTR(date, 1, 7);
-- Result: month = '2025-03'
```

**Applies to:**
- Workflow path only (Phase 2 → Phase 3 queries on SINK tables)
- Non-Workflow path unaffected (source tables use native DATE/TIMESTAMP)

**Why:** SINK tables produce VARCHAR for database compatibility and simplicity. Javascript's `Date` object can parse VARCHAR YYYY-MM-DD format directly (no extra processing needed).


---

## Pattern: Pre-Aggregate by Filter Dimensions (Dashboard Load Optimization)

**Problem:** Dashboard shows overview filters (channel, type, status, date) but includes all individual detail rows. Result: 3,749 rows in payload, 500+ KB JSON.

**Solution:** Pre-aggregate to the unique **combinations** of filter dimensions. Reduces payload by 90%.

### Before (3,749 rows → 500+ KB):
```sql
SELECT date, booking_channel, booking_type, booking_status, 
       booking_count, total_revenue, avg_revenue, unique_customers
FROM travel_bookings_daily
ORDER BY date;
-- Result: One row per day × channel × type × status = 3,749 rows
```

### After (100–200 rows → 50 KB):
```sql
SELECT booking_channel AS ch, 
       booking_type AS type, 
       booking_status AS status,
       SUBSTR(date, 1, 7) AS month,
       SUM(booking_count) AS cnt,
       SUM(total_revenue) AS rev,
       AVG(avg_revenue) AS avg,
       SUM(unique_customers) AS cust
FROM travel_bookings_daily
GROUP BY booking_channel, booking_type, booking_status, SUBSTR(date, 1, 7)
ORDER BY month;
-- Result: One row per unique (channel, type, status, month) combo = ~100-200 rows
```

**When to use:** 
- Dashboard has **overview filters** (channel, type, status) that aggregate across details
- Individual daily rows are NOT needed for the filter data
- Trend line can still query daily if needed (separate query for timeline)

**When NOT to use:**
- Dashboard requires drill-down to individual transactions
- User needs to see every single day's values
- Dimension cardinality is already low (< 50 rows total)

**Implementation:**
- Query 1 (filter data / KPI cards): Use pre-aggregated monthly
- Query 2 (trend line, if needed): Query daily separately (faster, < 400 rows)
- JavaScript merges results at render time

---

## Pattern 0: Schema Exploration (Start Here!)

Always verify tables and columns exist BEFORE running metric queries:

```sql
-- List all tables in database
SHOW TABLES;

-- Describe table structure
DESCRIBE {table_name};

-- Sample data from table
SELECT * FROM {table_name} LIMIT 10;

-- Check row count
SELECT COUNT(*) as row_count FROM {table_name};

-- Check date range (if table has date column)
SELECT 
  MIN({date_column}) as earliest_date,
  MAX({date_column}) as latest_date
FROM {table_name};
```

**When to use:** Stage B Step 2b (Table Discovery) before running any aggregate queries

---

## Pattern 1: Overall Metrics (KPIs)

Get high-level dashboard metrics for summary cards:

```sql
SELECT 
  COUNT(*) as total_records,
  COUNT(DISTINCT {id_column}) as unique_entities,
  SUM({metric_column}) as total_metric,
  AVG({metric_column}) as avg_metric,
  MIN({metric_column}) as min_metric,
  MAX({metric_column}) as max_metric
FROM {fact_table};
```

**Use for:**
- KPI cards/summary statistics at top of dashboard
- "Total Orders", "Total Revenue", "Unique Customers"
- First validation query (Pattern 0 → Pattern 1)

**Example (churn dashboard):**
```sql
SELECT 
  COUNT(*) as total_customers,
  COUNT(DISTINCT customer_id) as unique_customers,
  COUNT(CASE WHEN status = 'churned' THEN 1 END) as churned_count,
  AVG(health_score) as avg_health_score
FROM customers;
```

---

## Pattern 2: Dimension Breakdown (GROUP BY)

Get metrics broken down by a single dimension (for bar charts, tables):

```sql
SELECT 
  {dimension_column},
  COUNT(*) as count,
  SUM({metric_column}) as metric_total,
  COUNT(DISTINCT {id_column}) as unique_entities,
  AVG({metric_column}) as avg_metric
FROM {fact_table}
WHERE {optional_filters}
GROUP BY {dimension_column}
ORDER BY metric_total DESC
LIMIT {optional_top_n};
```

**Use for:**
- Bar charts (revenue by region, status, etc.)
- Pie charts (distribution by category)
- Filter dropdown options (use with DISTINCT)
- Tables showing breakdown by category

**Examples:**

```sql
-- Revenue by region
SELECT 
  region,
  COUNT(*) as order_count,
  SUM(amount) as revenue
FROM orders
WHERE status = 'completed'
GROUP BY region
ORDER BY revenue DESC;

-- Churn by customer segment
SELECT 
  segment,
  COUNT(*) as total_customers,
  COUNT(CASE WHEN status = 'churned' THEN 1 END) as churned_customers,
  ROUND(100.0 * COUNT(CASE WHEN status = 'churned' THEN 1 END) / COUNT(*), 2) as churn_rate_pct
FROM customers
GROUP BY segment
ORDER BY churn_rate_pct DESC;

-- Performance by product (with join)
SELECT 
  p.product_name,
  COUNT(o.order_id) as order_count,
  SUM(o.amount) as revenue,
  COUNT(DISTINCT o.customer_id) as unique_customers
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.product_name
ORDER BY revenue DESC;
```

---

## Pattern 3: Time Series Trends (Line Charts)

Get metrics over time to show trends:

```sql
SELECT 
  DATE({date_column}) as date,
  COUNT(*) as count,
  SUM({metric_column}) as metric_total,
  COUNT(DISTINCT {id_column}) as unique_entities,
  AVG({metric_column}) as avg_metric
FROM {fact_table}
WHERE {optional_filters}
GROUP BY DATE({date_column})
ORDER BY date ASC;
```

**Use for:**
- Line charts showing trends over time
- Daily/weekly/monthly revenue, orders, customer counts
- Seasonal patterns, anomaly detection
- Dashboard header: "Last 30 days" or "Last 90 days"

**Example (90-day revenue trend):**
```sql
SELECT 
  DATE(order_date) as date,
  COUNT(*) as daily_orders,
  SUM(amount) as daily_revenue,
  COUNT(DISTINCT customer_id) as unique_customers
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '90 day'
  AND status = 'completed'
GROUP BY DATE(order_date)
ORDER BY date ASC;
```

---

## Pattern 4: Top N Items (Rankings)

Get top N items by a metric:

```sql
SELECT 
  {dimension_column},
  COUNT(*) as count,
  SUM({metric_column}) as metric_total,
  COUNT(DISTINCT {id_column}) as unique_entities,
  ROW_NUMBER() OVER (ORDER BY SUM({metric_column}) DESC) as rank
FROM {fact_table}
WHERE {optional_filters}
GROUP BY {dimension_column}
ORDER BY metric_total DESC
LIMIT {n};
```

**Use for:**
- Top 10 customers, products, regions
- Leaderboards
- Key driver identification

**Example (Top 10 at-risk customers):**
```sql
SELECT 
  customer_name,
  health_score,
  churn_probability,
  mrr,
  COUNT(*) OVER () as rank
FROM customers
WHERE status = 'at_risk'
ORDER BY churn_probability DESC
LIMIT 10;
```

---

## Pattern 5: Multi-Dimension Analysis (Crosstab)

Get metrics across multiple dimensions:

```sql
SELECT 
  {dim1_column},
  {dim2_column},
  COUNT(*) as count,
  SUM({metric_column}) as metric_total,
  AVG({metric_column}) as avg_metric
FROM {fact_table}
WHERE {optional_filters}
GROUP BY {dim1_column}, {dim2_column}
ORDER BY metric_total DESC
LIMIT {optional_limit};
```

**Use for:**
- Heatmaps (revenue by region × product)
- Stacked bar charts
- Detailed analysis tables
- Cross-functional insights

**Example (Revenue by region AND segment):**
```sql
SELECT 
  c.region,
  c.segment,
  COUNT(*) as order_count,
  SUM(o.amount) as revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
GROUP BY c.region, c.segment
ORDER BY revenue DESC;
```

---

## Pattern 6: Filtering with WHERE

Apply business rules, date ranges, and exclusion rules:

```sql
SELECT 
  {columns}
FROM {fact_table}
WHERE {date_column} >= {date_start}
  AND {date_column} < {date_end}
  AND {status_column} = {value}
  AND {optional_exclusion_rule}
ORDER BY {column} DESC;
```

**Use for:**
- Excluding test/cancelled/draft data
- Date range filtering (last 30/90 days)
- Status-based segmentation
- Business rule enforcement (exclusion rules from Stage A)

**Example (Last 30 days, completed only):**
```sql
SELECT 
  region,
  SUM(amount) as revenue,
  COUNT(*) as order_count
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 day'
  AND status = 'completed'
  AND customer_type = 'production'  -- exclude test accounts
GROUP BY region
ORDER BY revenue DESC;
```

---

## Pattern 7: Joins for Rich Context

Combine fact and dimension tables to enrich metrics:

```sql
SELECT 
  d.{dimension_name},
  COUNT(*) as count,
  SUM(f.{metric_column}) as metric_total,
  COUNT(DISTINCT f.{id_column}) as unique_entities,
  AVG(d.{attribute}) as avg_attribute
FROM {fact_table} f
JOIN {dimension_table} d ON f.{foreign_key} = d.{primary_key}
WHERE {optional_filters}
GROUP BY d.{dimension_name}
ORDER BY metric_total DESC;
```

**Use for:**
- Adding customer demographics to transactions
- Enriching events with user attributes
- Cross-table analysis
- Adding business context

**Example (Revenue by customer segment):**
```sql
SELECT 
  c.segment,
  c.region,
  COUNT(*) as order_count,
  SUM(o.amount) as revenue,
  COUNT(DISTINCT o.customer_id) as unique_customers,
  AVG(c.lifetime_value) as avg_ltv
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
GROUP BY c.segment, c.region
ORDER BY revenue DESC;
```

---

## Pattern 8: Distinct Values (For Filters & Validation)

Get all unique values in a column (for filter dropdowns, validation):

```sql
SELECT DISTINCT {column_name}
FROM {table_name}
WHERE {column_name} IS NOT NULL
ORDER BY {column_name};
```

**Use for:**
- Building filter dropdowns on dashboard
- Validating dimension values exist
- Confirming data quality (no typos, correct case)
- Stage B Step 2d (Dimensions validation)

**Examples:**
```sql
-- All order statuses for filter
SELECT DISTINCT order_status FROM orders ORDER BY order_status;

-- All regions for filter
SELECT DISTINCT region FROM customers ORDER BY region;

-- All product categories for filter
SELECT DISTINCT category FROM products ORDER BY category;

-- Count of distinct values
SELECT COUNT(DISTINCT region) FROM customers;
-- Expected: 3-5 regions (sanity check)
```

---

## Pattern 9: Aggregations with DISTINCT

Count unique entities and metrics:

```sql
SELECT 
  {dimension_column},
  COUNT(DISTINCT {entity_id}) as unique_entities,
  COUNT(*) as total_records,
  SUM({metric_column}) as metric_total,
  AVG({metric_column}) as avg_metric
FROM {fact_table}
GROUP BY {dimension_column}
ORDER BY metric_total DESC;
```

**Use for:**
- Customer acquisition metrics
- Engagement per segment
- Churn analysis
- Repeat customer analysis

**Example (Unique customers per region):**
```sql
SELECT 
  region,
  COUNT(DISTINCT customer_id) as unique_customers,
  COUNT(*) as total_orders,
  SUM(amount) as total_revenue,
  AVG(amount) as avg_order_value
FROM orders
GROUP BY region
ORDER BY total_revenue DESC;
```

---

## Pattern 10: Ratio & Percentage Calculations

Calculate rates, percentages, and ratios:

```sql
SELECT 
  {dimension_column},
  COUNT(CASE WHEN {condition_1} THEN 1 END) as numerator,
  COUNT(CASE WHEN {condition_2} THEN 1 END) as denominator,
  ROUND(
    100.0 * COUNT(CASE WHEN {condition_1} THEN 1 END) 
    / COUNT(CASE WHEN {condition_2} THEN 1 END),
    2
  ) as ratio_pct
FROM {table}
GROUP BY {dimension_column}
ORDER BY ratio_pct DESC;
```

**Use for:**
- Conversion rates (completed / attempted)
- Churn rate (churned / total)
- Success rates
- Penetration metrics

**Example (Churn rate by segment):**
```sql
SELECT 
  segment,
  COUNT(CASE WHEN status = 'churned' THEN 1 END) as churned,
  COUNT(*) as total,
  ROUND(
    100.0 * COUNT(CASE WHEN status = 'churned' THEN 1 END) 
    / COUNT(*),
    2
  ) as churn_rate_pct
FROM customers
GROUP BY segment
ORDER BY churn_rate_pct DESC;
```

**Watch for:** Division by zero (use CASE WHEN denominator > 0 or NULLIF)

---

## Pattern 11: NULL Handling

Explicitly handle missing data:

```sql
-- ❌ BAD - NULLs cause rows to disappear
SELECT 
  region,
  SUM(revenue) as total_revenue
FROM sales
GROUP BY region;

-- ✅ GOOD - NULLs handled explicitly
SELECT 
  COALESCE(region, 'Unknown') as region,
  SUM(COALESCE(revenue, 0)) as total_revenue
FROM sales
GROUP BY COALESCE(region, 'Unknown')
ORDER BY total_revenue DESC;
```

**Use for:**
- Handling missing dimension values
- Treating NULL metrics as 0 (when appropriate)
- Making results more readable

**Test for NULLs:**
```sql
-- Check null count
SELECT COUNT(*) as null_count FROM {table} WHERE {column} IS NULL;

-- Check null percentage
SELECT 
  COUNT(*) as total,
  COUNT({column}) as non_null,
  ROUND(100.0 * (COUNT(*) - COUNT({column})) / COUNT(*), 2) as null_pct
FROM {table};
```

---

## Pattern 12: Data Quality Checks

Validate data before rendering:

```sql
-- Comprehensive quality check
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT {id_column}) as unique_ids,
  COUNT(CASE WHEN {metric_column} IS NULL THEN 1 END) as null_metrics,
  COUNT(CASE WHEN {metric_column} < 0 THEN 1 END) as negative_values,
  COUNT(CASE WHEN {metric_column} = 0 THEN 1 END) as zero_values,
  MIN({metric_column}) as min_value,
  MAX({metric_column}) as max_value,
  MIN({date_column}) as earliest_date,
  MAX({date_column}) as latest_date
FROM {table};
```

**Example (Orders data quality):**
```sql
SELECT 
  COUNT(*) as total_orders,
  COUNT(DISTINCT order_id) as unique_orders,
  COUNT(CASE WHEN amount IS NULL THEN 1 END) as null_amounts,
  COUNT(CASE WHEN amount < 0 THEN 1 END) as negative_amounts,
  COUNT(CASE WHEN amount = 0 THEN 1 END) as zero_amounts,
  MIN(amount) as min_amount,
  MAX(amount) as max_amount,
  MIN(order_date) as earliest_date,
  MAX(order_date) as latest_date
FROM orders;
```

---

## Pattern 13: Join Validation

Verify join correctness and cardinality:

```sql
-- Step 1: Count before join
SELECT COUNT(*) as before_join FROM {table1};
-- Expected: baseline number

-- Step 2: Count after join
SELECT COUNT(*) as after_join 
FROM {table1}
JOIN {table2} ON {table1.key} = {table2.key};
-- Expected: same as before (1-to-1) or proportional (1-to-many)

-- Step 3: Verify no join explosion
-- If after_join >> before_join, there may be duplicate join keys
SELECT {table1.key}, COUNT(*) as count
FROM {table2}
GROUP BY {table1.key}
HAVING COUNT(*) > 1
LIMIT 10;
-- If many duplicates, investigate join logic
```

**Example (Customers ↔ Subscriptions):**
```sql
-- Count before
SELECT COUNT(*) FROM customers;  -- 8,500

-- Count after
SELECT COUNT(*) FROM customers c
  JOIN subscriptions s ON c.customer_id = s.customer_id;  -- 8,650
-- OK: 150 extra rows = some customers have 2+ subscriptions (expected 1-to-many)
```

---

## Pattern 14: Performance Testing

Test query performance before embedding in dashboard:

```sql
-- Test with LIMIT first (fast)
SELECT * FROM {large_table}
WHERE {filters}
LIMIT 1000;

-- Then remove LIMIT and run full query
-- Monitor query execution time

-- If slow (> 5 seconds):
-- 1. Check indexes: SHOW INDEX FROM {table}
-- 2. Add index: CREATE INDEX idx_name ON {table}({column})
-- 3. Optimize WHERE clause (use indexed columns, avoid functions)
```

**Timing guidelines:**
- Simple metrics (Pattern 1): < 1 second
- GROUP BY (Pattern 2): < 2 seconds
- Joins (Pattern 7): < 3 seconds
- Large aggregations: < 5 seconds

---

## Workflow: From Query to Dashboard

1. **Run Pattern 0** (Schema Exploration)
   - Verify tables and columns exist

2. **Run Pattern 1** (Overall Metrics)
   - Get KPI totals for dashboard header

3. **Run Pattern 2 or 3** (Dimension/Time breakdown) for each key visualization
   - Get data for charts and tables

4. **Run Pattern 8** (Distinct Values)
   - Get filter dropdown options

5. **Run Pattern 12** (Data Quality Check)
   - Validate data before rendering

6. **Embed results** in dashboard code
   - Use EXACT numbers from queries, not rounded
   - Example: Query result `4859839.200000003` → Store as `4859839.20` (not `4860000`)

---

## Pre-Dashboard Query Checklist

For EACH query used in dashboard:

- [ ] Query runs < 5 seconds
- [ ] Row count is as expected (not 0, not millions)
- [ ] Column count is as expected
- [ ] No unexpected NULLs (or NULLs handled with COALESCE)
- [ ] Values match business logic (sanity check)
- [ ] Join cardinality verified (1-to-1? 1-to-many?)
- [ ] Filters working correctly (WHERE clause produces expected row count)
- [ ] Indexes present on filter columns (if large tables)
- [ ] No SELECT * (explicit columns only)
- [ ] Results reproducible (can run same query twice, get same result)

---

## Related Files

- `steps.md` Step 4b-pre — SINK/source column verification gate before writing any queries
- `../../phase-1/references/validation-queries.md` — Stage B focused validation queries (metric/dimension/join/freshness checks)
- `../../phase-1/requirements-gathering-guide.md` — Stage A/B process; these patterns used in Stage B Steps 2c-2d
---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
