# input_params.yaml Examples

Real-world configuration examples for custom dashboard workflows, using the exact schema shipped in `workflow-templates/input_params.yaml`.

> ⚠️ **Critical Rules (learned from production deployments):**
> 1. **All variables MUST be top-level** — never nest under `globals:` or any parent key. Digdag resolves only root-level keys; nested variables cause `Failed to evaluate variable ${...}` at runtime.
> 2. **`cleanup_temp_tables: 'no'` unless temp tables are used** — setting `'yes'` when no temp tables exist causes cleanup to fail.
> 3. **SQL files use plain `SELECT`, not `INSERT INTO`** — the `td>` operator with `create_table:`/`insert_into:` handles writing. See SQL examples below.
> 4. **`refresh_mode`** controls the full ↔ incremental execution path. Set `'full'` for first run; switch to `'incremental'` after Step 2g validation passes.
> 5. **There is no YAML-driven "list of aggregate tables" schema.** Each SINK table is its own explicit task pair in the `.dig` file (`+create_<name>` with `if>: ${refresh_mode == 'full'}` branching to a `create_table:` task or a DELETE + `insert_into:` task pair) and its own `_full.sql` / `_incremental.sql` file. Adding a new SINK table means adding a new task pair to the `.dig` file and a new SQL file pair — not adding an entry to an `aggregate_metrics_tables:` list. (An earlier version of this doc showed such a list; it was never actually read by any `.dig` or `.sql` file and has been removed below.)

---

## refresh_mode Flag (Standard for All Workflows)

Every workflow includes these two parameters. They control whether Step 1 of `<project_name>_data_prep.dig` takes the full-refresh path or the incremental path:

```yaml
# 'full'        — loads the complete start_date → end_date historical window
# 'incremental' — appends only the last incremental_look_back_days (covers late-arriving data)
refresh_mode: 'full'

# Lookback window used when refresh_mode = 'incremental'
# append-only data: 2 | upsert (corrections): 7 | state-managed: set dynamically
incremental_look_back_days: 2
```

**Lifecycle:**
- **Phase 2 Step 2f (first deploy):** `refresh_mode: 'full'` — runs full historical window
- **Phase 2 Step 2h (after Step 2g passes):** change to `refresh_mode: 'incremental'` → push → run incremental test
- **Production (all scheduled runs):** stays `'incremental'`
- **Force re-process:** flip back to `'full'`, push, run once, flip back to `'incremental'`

---

## Example 1: E-commerce Dashboard

**Use case:** Track daily sales metrics by product category and month

```yaml
project_prefix: ecom
sink_database: ecom_dashboards
source_database: ecom_production
source_table: orders
main_id_key: customer_id
api_endpoint: 'https://api.treasuredata.com'
cleanup_temp_tables: 'no'
refresh_mode: 'full'
incremental_look_back_days: 2
table_filter: "status != 'cancelled'"
start_date: '2024-01-01'
end_date: '2024-12-31'

td:
  database: ecom_dashboards

temporary_tables: []
```

**Corresponding SQL file (`sql/10_create_aggregates_full.sql`, paired with `..._incremental.sql`):**
```sql
-- ✅ Plain SELECT + UNION ALL — NOT INSERT INTO
-- Multiple breakdown types in one SINK table (task uses create_table: on the full path,
-- DELETE + insert_into: on the incremental path — see workflow-deployment-validate.md
-- Step 2h-2 for the .dig task pair this pairs with)

SELECT 'overall' AS breakdown_type, 'all' AS breakdown_value,
       COUNT(*) AS total_orders, COALESCE(SUM(amount),0) AS total_revenue,
       APPROX_DISTINCT(customer_id) AS unique_customers
FROM ${source_database}.${source_table}
WHERE td_time_range(time, TD_TIME_PARSE('${start_date} 00:00:00', 'UTC'), TD_TIME_PARSE('${end_date} 23:59:59', 'UTC'), 'UTC')
  AND status != 'cancelled'

UNION ALL

SELECT 'product_category' AS breakdown_type, product_category AS breakdown_value,
       COUNT(*) AS total_orders, COALESCE(SUM(amount),0) AS total_revenue,
       APPROX_DISTINCT(customer_id) AS unique_customers
FROM ${source_database}.${source_table}
WHERE td_time_range(time, TD_TIME_PARSE('${start_date} 00:00:00', 'UTC'), TD_TIME_PARSE('${end_date} 23:59:59', 'UTC'), 'UTC')
  AND status != 'cancelled'
GROUP BY product_category

UNION ALL

SELECT 'monthly_trend' AS breakdown_type,
       DATE_FORMAT(FROM_UNIXTIME(time), '%Y-%m') AS breakdown_value,
       COUNT(*) AS total_orders, COALESCE(SUM(amount),0) AS total_revenue,
       APPROX_DISTINCT(customer_id) AS unique_customers
FROM ${source_database}.${source_table}
WHERE td_time_range(time, TD_TIME_PARSE('${start_date} 00:00:00', 'UTC'), TD_TIME_PARSE('${end_date} 23:59:59', 'UTC'), 'UTC')
  AND status != 'cancelled'
GROUP BY DATE_FORMAT(FROM_UNIXTIME(time), '%Y-%m')
```

**`.dig` task pair (`SLUG_data_prep.dig`):**
```yaml
+create_aggregates:
  if>: ${refresh_mode == 'full'}
  _do:
    +full:
      td>: sql/10_create_aggregates_full.sql
      engine: presto
      database: ${sink_database}
      create_table: ${project_prefix}_aggregate_final
  _else_do:
    _retry: 3
    +delete_lookback_window:
      td>:
        data: |
          DELETE FROM ${sink_database}.${project_prefix}_aggregate_final
          WHERE breakdown_type = 'overall'  -- adjust to your grain key; verify type per Step 2h-2
      engine: presto
      database: ${sink_database}
    +insert_fresh:
      td>: sql/10_create_aggregates_incremental.sql
      engine: presto
      database: ${sink_database}
      insert_into: ${project_prefix}_aggregate_final
```

**Expected SINK table rows:** ~50 rows (1 overall + ~10 categories + ~12 months)

---

## Example 2: SaaS Usage Analytics

**Use case:** Track feature adoption, active users, subscription revenue — two SINK tables from two source tables in the same database

```yaml
project_prefix: saas
sink_database: saas_analytics
source_database: saas_events
source_table: events
main_id_key: user_id
api_endpoint: 'https://api.treasuredata.com'
cleanup_temp_tables: 'no'
refresh_mode: 'full'
incremental_look_back_days: 2
table_filter: ""
start_date: '2024-01-01'
end_date: '2024-12-31'

td:
  database: saas_analytics

temporary_tables: []
```

**Two source tables in one database → two independent SINK task pairs** (both use `source_database`, but the second SQL file references `${source_database}.subscriptions` directly instead of `${source_table}` since it's a second table, not the primary one):

```yaml
# SLUG_data_prep.dig — one task pair per SINK table
+create_usage_kpis:
  if>: ${refresh_mode == 'full'}
  _do:
    +full:
      td>: sql/10_usage_kpis_full.sql       # FROM ${source_database}.${source_table} (events)
      engine: presto
      database: ${sink_database}
      create_table: ${project_prefix}_usage_kpis
  _else_do:
    _retry: 3
    +delete_lookback_window: {td>: {data: "DELETE FROM ${sink_database}.${project_prefix}_usage_kpis WHERE ..."}, engine: presto, database: ${sink_database}}
    +insert_fresh:
      td>: sql/10_usage_kpis_incremental.sql
      engine: presto
      database: ${sink_database}
      insert_into: ${project_prefix}_usage_kpis

+create_subscription_kpis:
  if>: ${refresh_mode == 'full'}
  _do:
    +full:
      td>: sql/11_subscription_kpis_full.sql  # FROM ${source_database}.subscriptions (explicit table name)
      engine: presto
      database: ${sink_database}
      create_table: ${project_prefix}_subscription_kpis
  _else_do:
    _retry: 3
    +delete_lookback_window: {td>: {data: "DELETE FROM ${sink_database}.${project_prefix}_subscription_kpis WHERE ..."}, engine: presto, database: ${sink_database}}
    +insert_fresh:
      td>: sql/11_subscription_kpis_incremental.sql
      engine: presto
      database: ${sink_database}
      insert_into: ${project_prefix}_subscription_kpis
```

```sql
-- sql/10_usage_kpis_full.sql
SELECT
  TD_DATE_TRUNC('day', TD_TIME_PARSE(time, 'UTC'), 'UTC') AS event_date,
  APPROX_DISTINCT(user_id) AS active_users,
  COUNT(*) AS event_count
FROM ${source_database}.${source_table}
WHERE td_time_range(TD_TIME_PARSE(time, 'UTC'), TD_TIME_PARSE('${start_date} 00:00:00', 'UTC'), TD_TIME_PARSE('${end_date} 23:59:59', 'UTC'), 'UTC')
GROUP BY TD_DATE_TRUNC('day', TD_TIME_PARSE(time, 'UTC'), 'UTC')
```

```sql
-- sql/11_subscription_kpis_full.sql
SELECT
  TD_DATE_TRUNC('day', TD_TIME_PARSE(time, 'UTC'), 'UTC') AS event_date,
  COUNT(CASE WHEN status = 'active' THEN 1 END) AS active_subscriptions,
  COALESCE(SUM(CASE WHEN status = 'active' THEN monthly_price END), 0) AS mrr
FROM ${source_database}.subscriptions
WHERE td_time_range(TD_TIME_PARSE(time, 'UTC'), TD_TIME_PARSE('${start_date} 00:00:00', 'UTC'), TD_TIME_PARSE('${end_date} 23:59:59', 'UTC'), 'UTC')
GROUP BY TD_DATE_TRUNC('day', TD_TIME_PARSE(time, 'UTC'), 'UTC')
```

---

## Example 3: Multi-Source Dashboard (multiple source databases)

**Use case:** Dashboard pulls from CRM, web events, and transactions — each in a separate database.

**Pattern: flat `source_db_*` keys** — one top-level variable per source database, in addition to the standard `source_database`/`source_table`. Digdag resolves only root-level keys; never nest these under `globals:` or any parent.

```yaml
project_prefix: retail
sink_database: retail_dashboards
source_database: commerce_db          # primary source, used by the default source_table
source_table: orders
main_id_key: customer_id
api_endpoint: 'https://api.treasuredata.com'
cleanup_temp_tables: 'no'
refresh_mode: 'full'
incremental_look_back_days: 2
table_filter: "status != 'cancelled'"
start_date: '2024-01-01'
end_date: '2024-12-31'

# Additional source databases — one flat key per database, resolves as ${source_db_crm} etc. in SQL
source_db_crm: crm_production
source_db_events: web_analytics

td:
  database: retail_dashboards

temporary_tables: []
```

**Three SINK tables (customer_kpis, web_kpis, orders_kpis) → three independent task pairs in `SLUG_data_prep.dig`**, each with its own `_full.sql`/`_incremental.sql` file pair pointing at the relevant `source_db_*` variable:

**Corresponding SQL file (`sql/10_create_aggregates.sql`) using multi-source variables:**
```sql
-- Source databases from input_params.yaml flat keys
-- ${source_db_crm}    → crm_production
-- ${source_db_events} → web_analytics
-- ${source_database}  → commerce_db

SELECT
  DATE_FORMAT(FROM_UNIXTIME(o.time), '%Y-%m') AS month,
  c.tier                                        AS customer_tier,
  COUNT(*)                                      AS total_orders,
  COALESCE(SUM(o.amount), 0)                    AS total_revenue,
  APPROX_DISTINCT(o.customer_id)               AS unique_customers
FROM ${source_database}.orders o
LEFT JOIN ${source_db_crm}.customers c ON o.customer_id = c.customer_id
WHERE td_time_range(o.time, '${start_date}', '${end_date}', 'UTC')
  AND o.status != 'cancelled'
GROUP BY DATE_FORMAT(FROM_UNIXTIME(o.time), '%Y-%m'), c.tier
```

**Why flat keys scale:**
- Switch environments (staging → prod): change `source_db_crm: crm_staging` in one file
- All databases visible in one config section
- No scattered hardcoded DB names across SQL files

---

## Configuration Tips

### Variable Scope — Top Level Only

```yaml
# WRONG — nested variables fail at runtime
globals:
  sink_database: my_db       # ${sink_database} → "Failed to evaluate variable"
  start_date: '2024-01-01'

# CORRECT — top-level variables resolve correctly
sink_database: my_db
start_date: '2024-01-01'
```

### Multi-Source — Use `source_db_*` Flat Keys

```yaml
# WRONG — nesting fails at runtime (same root-level-only rule)
source_databases:
  crm: crm_production        # ${source_databases.crm} → "Failed to evaluate variable"
  events: analytics_events

# CORRECT — flat top-level keys, one per additional database
source_db_crm: crm_production
source_db_events: analytics_events
# SQL: FROM ${source_db_crm}.customers — resolves correctly
```

### SQL Pattern — SELECT not INSERT INTO

```yaml
# .dig task
+create_aggregates:
  td>: sql/10_create_aggregates.sql
  engine: presto
  database: ${sink_database}
  create_table: ${project_prefix}_aggregate_final   # td> writes SELECT results here automatically
```

```sql
-- SQL file: plain SELECT
-- For multiple breakdowns: use UNION ALL
SELECT 'overall' AS breakdown_type, COUNT(*) AS total
FROM my_db.my_table
WHERE td_time_range(time, '${start_date}', '${end_date}', 'UTC')

UNION ALL

SELECT 'by_region' AS breakdown_type, COUNT(*) AS total
FROM my_db.my_table
WHERE td_time_range(time, '${start_date}', '${end_date}', 'UTC')
GROUP BY region
```

### Star Schema — The Right SINK Design for Dashboards with Filters

> ⚠️ **Never pre-aggregate by a single breakdown dimension (e.g., one table per "by_booking_type").**
> This means Phase 3 filters can only work for combinations you pre-computed.
>
> ✅ **Pre-aggregate at the grain of ALL filter dimensions combined:**
> One row per unique combination of all dimensions that users can filter on.
> Phase 3 then uses `WHERE` + `GROUP BY` — any filter combination works instantly.

**Correct pattern — all filter dims in GROUP BY:**
```sql
-- Grain: booking_type × channel × destination × month × loyalty_tier
SELECT
    booking_type, booking_channel, destination, month, loyalty_tier,
    COUNT(*) AS total_bookings, SUM(amount) AS total_revenue
FROM source_db.bookings
GROUP BY booking_type, booking_channel, destination, month, loyalty_tier
```

> ⚠️ **Avoid high-cardinality columns as filter dimensions:**
> user_id, order_id, session_id → millions of rows, defeats pre-aggregation.
> Use segment/tier/category (3–30 distinct values) as filter dimensions.

### Size Estimation

**Row count = only actual combinations that exist in data (sparse — far fewer than theoretical max)**

```
date (365 days) * country (5) * product (20) = 36,500 rows
date (365 days) * user_id (1M) * product (20) = HUGE ❌
date (365 days) * user_segment (10) * product (20) = 73,000 rows ✅
```

**Cardinality explosion example:** an article-level metrics table (1000 articles × 180 days × 20 categories) blows past 100K rows before it's useful. Fix: aggregate by `content_category` instead of `article_id`.

### Metric Naming

- Use clear, descriptive names: `unique_customers` not `uc`
- Include unit if not obvious: `avg_session_duration_sec` not `duration`
- Prefix with calculation: `total_revenue` not just `revenue`

### Dimensions

- 2-3 primary dimensions (date + 1-2 attributes)
- Avoid high-cardinality dimensions (user_id, product_sku)
- Use hierarchy levels (country, region, not street address)
- Semi-additive metrics (e.g. `current_stock_units`) need `MAX`/last-value logic, not `SUM`, across a date range — flag these during Stage B

### First-Run Settings

```yaml
# First deploy — backfill the full history
refresh_mode: 'full'
start_date: '2024-01-01'    # earliest available data
end_date: '2024-12-31'      # latest available data

# After Step 2g validation passes — switch to scheduled incremental runs
refresh_mode: 'incremental'
# start_date / end_date no longer drive the query; incremental_look_back_days does
```

---

## Migration Path

**If a SINK table is too large (slow queries, > 100K rows):**

1. **Reduce dimensions:** Remove the least-used dimension from `GROUP BY`
2. **Coarsen grain:** Replace `user_id` with `user_segment` (30 values vs 1M)
3. **Split tables:** Create separate tables for different granularities (daily vs monthly)
4. **Filter data:** Add a date window (`last 90 days` vs full history)

**Common fix:**
```yaml
# BEFORE: 500K rows (too large — queries > 2 sec)
# sql/10_create_aggregates.sql GROUP BY: date, country, product, store_id, user_segment

# AFTER: 50K rows (fast — queries < 1 sec)
# sql/10_create_aggregates.sql GROUP BY: date, country, product_category
```

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
