# TD Time Functions: Query Optimization Patterns

**Phase 2 relies on Treasure Data time functions for efficient scheduling. These patterns ensure queries run fast and support incremental processing.**

---

## 3 Critical Functions

### 1. td_scheduled_time() — Fixed Reference Time

Returns the scheduled run time (fixed for that execution).

```sql
-- Without td_scheduled_time() — unpredictable
WHERE order_date >= CURRENT_DATE - INTERVAL '365 days'
-- Depends on WHEN you run the query (could be 12:01 AM or 2:59 AM)

-- With td_scheduled_time() — deterministic
WHERE td_time_range(order_time,
  td_time_add(td_scheduled_time(), '-365d'),
  td_scheduled_time()
)
-- Always uses 2:00 AM (scheduled time) as reference
```

**Use case:** Reproducible, consistent runs for the same date window

---

### 2. td_time_string() — Format Dates

Produces YYYY-MM-DD strings for clean output.

```sql
-- Before
SELECT DATE(order_date) as date, ...
-- Result: 2024-03-15 (DATE type)

-- After
SELECT td_time_string(order_time, 'd!', 'UTC') as date, ...
-- Result: "2024-03-15" (string, same visual, better for grouping)
```

**Use case:** Clean date formatting in output tables

---

### 3. td_time_range() — Partition Pruning (CRITICAL for Performance)

Filters by time efficiently, enabling partition pruning.

```sql
-- Without td_time_range() — scans all rows
WHERE order_date >= CURRENT_DATE - INTERVAL '365 days'
-- Scans every row in table, then filters (~10 seconds on large table)

-- With td_time_range() — skips partitions
WHERE td_time_range(order_time,
  td_time_add(td_scheduled_time(), '-365d'),
  td_scheduled_time()
)
-- Only reads partitions matching time range (~2 seconds)
```

**Impact:** 5x-10x faster on large tables

---

## Incremental Processing Patterns

**CRITICAL:** Do NOT reprocess all historical data every day.

### Pattern A: Append-Only (Immutable Data)

For data that never changes after recording (events, immutable logs):

```sql
-- Daily query: Process only yesterday
SELECT td_time_string(order_time, 'd!', 'UTC') as date,
       SUM(amount) as revenue
FROM orders
WHERE td_time_range(order_time,
  td_time_add(td_scheduled_time(), '-1d'),
  td_scheduled_time()
)
GROUP BY td_time_string(order_time, 'd!', 'UTC')
```

**Workflow:**
- Day 1: Appends 2024-03-15 data
- Day 2: Appends 2024-03-16 data (2024-03-15 unchanged)
- Result: Cumulative table, no duplicates

**Performance:** ~30 seconds daily | Historical load: 2-5 minutes (one-time)

---

### Pattern B: 1-Day Lookback (Same-Day Corrections)

For data that may be corrected within 1 day (e.g., sales with same-day refunds):

```sql
-- Daily query: Process last 1 day (catches yesterday + same-day corrections)
SELECT td_time_string(order_time, 'd!', 'UTC') as date,
       SUM(amount) as revenue
FROM orders
WHERE td_time_range(order_time,
  td_time_add(td_scheduled_time(), '-1d'),
  td_scheduled_time()
)
GROUP BY td_time_string(order_time, 'd!', 'UTC')
```

**Workflow:**
- Day 1 (March 16, 2 AM): Processes March 15-16 data
  - Includes any March 15 corrections made overnight
- Day 2 (March 17, 2 AM): Processes March 16-17 data
  - Includes any March 16 corrections made overnight

**Strategy:** Use MERGE or REPLACE INTO pattern in workflow to upsert corrected data

```yaml
+kpi_daily_1day:
  td>: sql/kpi_daily_1day.sql
  insert_into: kpi_daily  # Upsert existing rows, insert new ones
```

**Performance:** ~30 seconds daily | Handles same-day corrections

---

### Pattern C: 7-Day Lookback (Delayed Corrections)

For data corrected up to 7 days later (e.g., reporting with delayed payouts):

```sql
-- Daily query: Process last 7 days (catches corrections up to 7 days old)
SELECT td_time_string(order_time, 'd!', 'UTC') as date,
       SUM(amount) as revenue
FROM orders
WHERE td_time_range(order_time,
  td_time_add(td_scheduled_time(), '-7d'),
  td_scheduled_time()
)
GROUP BY td_time_string(order_time, 'd!', 'UTC')
```

**Workflow:**
- Day 1 (March 16): Processes March 9-16 data
- Day 8 (March 23): Processes March 16-23 data (March 16 already in table, will be corrected)

**Strategy:** Use REPLACE INTO pattern to overwrite potentially stale data:

```yaml
+kpi_daily_7day:
  td>: sql/kpi_daily_7day.sql
  create_table: kpi_daily  # Replace full 7-day window daily
```

**Performance:** ~45 seconds daily | Handles corrections up to 7 days old

---

## Choosing Your Pattern

**Ask the customer: "Can metrics change after being recorded?"**

| Answer | Pattern | Example |
|--------|---------|---------|
| NO — immutable | Append-only | Event logs, completed transactions |
| YES — corrected same day | 1-day lookback | E-commerce with same-day refunds |
| YES — corrected within 7 days | 7-day lookback | Accounting with delayed posting |
| YES — corrected anytime | Full historical | Data quality corrections ongoing (not recommended for scheduled workflow) |

---

## Session Variables (Advanced)

For dynamic date handling in .dig files:

```yaml
+kpi_daily:
  td>: |
    SELECT 
      td_time_string(order_time, 'd!', 'UTC') as date,
      SUM(amount) as revenue
    FROM orders
    WHERE td_time_range(order_time,
      '${moment(session_time).subtract(1, "days").format("YYYY-MM-DD")}',
      '${moment(session_time).format("YYYY-MM-DD")}'
    )
    GROUP BY td_time_string(order_time, 'd!', 'UTC')
  create_table: kpi_daily
```

`session_time` = the scheduled execution time (2 AM UTC in this example)
`moment()` = moment.js library for date math

---

## Performance Testing

```bash
# Test query performance
tdx query -d sales_db < sql/kpi_daily_optimized.sql

# Expected: < 5 seconds

# If > 5 seconds:
# - Add td_time_range() if missing
# - Reduce date lookback window
# - Check for full table scans in WHERE clause
# - Consider creating indexes on filter columns
```

---

## Common Pitfall: Missing td_time_range()

```sql
-- ❌ SLOW: Full scan of 500M rows
WHERE order_date >= '2024-01-01'

-- ✅ FAST: Partition pruning (scans only matching partitions)
WHERE td_time_range(order_time,
  '2024-01-01',
  '2024-12-31'
)
```

Without `td_time_range()`, Treasure Data scans ALL rows then filters. With `td_time_range()`, Treasure Data skips entire partitions (typically 10x-100x speedup).
---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
