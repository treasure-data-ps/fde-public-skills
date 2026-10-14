# Phase 2: Testing Checklist & Troubleshooting

## Phase 2 Testing Checklist

Before handing off to Phase 3, verify all items:

### Configuration Tests
- [ ] `input_params.yaml` variables are all top-level (no `globals:` nesting)
- [ ] SQL files use `SELECT` (or `SELECT ... UNION ALL`), never `INSERT INTO`
- [ ] `cleanup_temp_tables: 'no'` unless temp tables are actually used
- [ ] `refresh_mode` set correctly (`'full'` for first run, `'incremental'` for scheduled runs)

### Schema & Structure Tests
- [ ] SINK database exists: `tdx databases --json | python3 -c "import sys,json; data=json.load(sys.stdin); print([d['database_name'] for d in data if '<sink_db>' in d.get('database_name','')])"`
- [ ] All expected SINK tables created: `tdx tables --database <sink_database>`
- [ ] Each table has correct columns: `tdx describe <sink_database>.<table_name>`
- [ ] All breakdown types present in multi-breakdown tables (check `GROUP BY breakdown_type`)

### Data Quality Tests
- [ ] **No zero-row tables** — most critical check (see troubleshooting below)
- [ ] Row counts match expectations (see breakdown_type cardinality)
- [ ] **NULL audit passed** — `COALESCE(SUM(col), 0)` applied to all metric columns; no NULLs remain
- [ ] **Date column types confirmed** — date columns are DATE not VARCHAR (VARCHAR breaks Phase 3 date range filters silently)
- [ ] Spot-check metric vs Stage B validated values (must match exactly)
- [ ] Cross-join table: dimension combinations have correct cardinality
- [ ] **Column names locked in `state.md`** — exact names from `tdx describe` recorded as Phase 3 contract

### Workflow Execution Tests
- [ ] Workflow pushed/uploaded successfully
- [ ] First run completed: `tdx wf sessions <project> --status success`
- [ ] Timeline shows all tasks green: `tdx wf timeline <project>.<project_name>_launch`
- [ ] No tasks in error state: `tdx wf attempt <id> tasks`
- [ ] `create_table:` behavior confirmed — replaces on re-run (no duplicates)

### Performance Tests
- [ ] Initial historical load: < 5 minutes
- [ ] Query performance on SINK tables: < 2 seconds
- [ ] `td_time_range()` present in all SQL files: `grep -r "td_time_range" sql/`

---

## Troubleshooting Phase 2 Issues

### Workflow fails immediately — "Failed to evaluate variable ${...}"

**Symptoms:**
```
{"message":"Failed to evaluate a variable ${sink_database}"}
```

**Cause:** Variables nested under `globals:` or any parent key in `input_params.yaml`.

**Fix:**
```yaml
# WRONG — nested variables not resolved by digdag
globals:
  sink_database: my_db

# CORRECT — all variables at top level
sink_database: my_db
```

---

### SQL task fails — INSERT INTO error

**Symptoms:**
```
Error: Table 'sink_db.my_table' does not exist
```

**Cause:** SQL file uses `INSERT INTO` but the target table doesn't exist on first run. The `td>` operator with `create_table:` expects a plain `SELECT`.

**Fix:** Replace `INSERT INTO ... SELECT` with plain `SELECT` in the SQL file. For multiple breakdowns, use `SELECT ... UNION ALL SELECT ...`.

```sql
-- ❌ WRONG
INSERT INTO sink_db.my_kpis SELECT ...

-- ✅ CORRECT
SELECT ...
UNION ALL
SELECT ...
```

---

### SINK tables empty (0 rows) after successful run

**Symptoms:**
```
✅ All workflow tasks green
SELECT COUNT(*) FROM sink_db.my_table → 0
```

**Cause:** `td_time_range()` filter window doesn't overlap with actual data dates, OR the JOIN in `01_data_prep.sql` dropped all rows.

**Diagnosis:**
```bash
# Check actual data range in source
tdx query "SELECT MIN(FROM_UNIXTIME(time)) as earliest, MAX(FROM_UNIXTIME(time)) as latest FROM <source_database>.<source_table>"

# Compare to input_params.yaml start_date / end_date
# If they don't overlap → rows = 0
```

**Fix:**
1. Update `start_date` / `end_date` in `input_params.yaml` to match source data range
2. Re-push workflow
3. Re-run: `tdx wf run <project_name>.<project_name>_launch`

---

### Duplicate rows after second run — `create_table:` REPLACES, not appends

> ✅ **`create_table:` in the TD `td>` operator REPLACES the table on every run — it does NOT append.**
> Row counts should be identical after run 1 and run 2. No truncate step needed.
> Scheduled runs are safe — each run produces a clean, fresh set of SINK tables.

**When duplicates CAN occur:** Only if you use `insert_into:` without a preceding DELETE/truncate. For incremental workflows where you want to append only new rows, use `insert_into:` with a time-filtered SQL window (see Step 2h in `workflow-deployment-validate.md`).

---

### Workflow push fails — confirmation required in non-interactive mode

**Symptoms:**
```
Error: Confirmation required but running in non-interactive mode
Use -y or --yes flag to apply changes without confirmation
```

**Fix:** Add `--yes` flag:
```bash
tdx wf push --yes
```

---

### Workflow push fails — "no workflow project found"

**Symptoms:**
```
Error: No workflow project found
```

**Cause:** This is a new project — `push` only works for projects that already exist on TD.

**Fix:** Use `upload` for the first deployment; use `push` for every deployment after that.
```bash
# NEW project — creates the project on TD
tdx wf upload --name <project_name>

# EXISTING project — updates it
tdx wf push --yes
```

---

### Cleanup step fails — temp tables don't exist

**Symptoms:**
```
❌ +drop_table_<item> — Table not found
```

**Cause:** `cleanup_temp_tables: 'yes'` but no temp tables were actually created by your SQL, or `temporary_tables:` lists a table name that doesn't match what was actually created.

**Fix:** Set `cleanup_temp_tables: 'no'` in `input_params.yaml` if your SQL files don't create intermediate temp tables. If they do, make sure `temporary_tables:` lists the exact table names.

---

### Metrics don't match Stage B values

**Symptoms:**
```
Stage B validated query: Revenue = $9,191,636
Phase 2 SINK table: Revenue = $10,337,934 (includes cancelled bookings!)
```

**Cause:** An exclusion rule confirmed during Stage A/B was never applied in the SQL file.

**Diagnosis:**
```bash
# Check if table_filter is set in input_params.yaml
grep "table_filter" input_params.yaml

# Check if the same WHERE condition is in the SQL
grep "booking_status" sql/10_create_aggregates.sql
```

**Fix:** Ensure `table_filter` is set in `input_params.yaml` AND applied in the SQL:
```yaml
table_filter: "booking_status != 'Cancelled'"
```
```sql
WHERE td_time_range(time, ...) AND booking_status != 'Cancelled'
```

---

### Cannot create database — `tdx db:create` not found

**Symptoms:**
```
command not found: tdx db:create
```

**Cause:** `tdx db:create` does not exist.

**Fix:**
```bash
# CORRECT — use CREATE SCHEMA via tdx query
tdx query "CREATE SCHEMA IF NOT EXISTS <database_name>"

# Verify
tdx databases --json | python3 -c "import sys,json; data=json.load(sys.stdin); print([d['database_name'] for d in data if '<database_name>' in d.get('database_name','')])"
```

---

### `insert_into:` vs `create_table:` — What's the Difference?

| Operator | Behavior | Use When |
|---------|---------|---------|
| `create_table: <name>` | **Replaces** table on every run | Full-refresh SINK tables — the default, safest pattern ✅ |
| `insert_into: <name>` | Appends to existing table (table must already exist) | Incremental runs — append only new time window rows |

**Full-refresh pattern (default for dashboard SINK tables):**
```yaml
# .dig file — create_table: replaces on every run, no truncate needed
+create_aggregates:
  td>: sql/10_create_aggregates.sql
  create_table: ${project_prefix}_aggregate_final
  database: ${sink_database}
```

**Incremental pattern (for append-only use cases):**
```yaml
# .dig file — insert_into: appends; SQL must filter to new time window only
+insert_aggregates:
  td>: sql/10_create_aggregates_incremental.sql   # SQL uses TD_SCHEDULED_TIME() window
  insert_into: ${project_prefix}_aggregate_final
  database: ${sink_database}
```

---

### Workflow task fails mid-run — "Table not found" or "Column not found"

**Symptom:** Workflow starts but fails at a specific task (e.g., `+create_aggregates`)

**Cause:** Column name mismatch between SQL and actual database schema

**Fix:**
1. Check actual schema:
   ```bash
   tdx describe <source_database>.<source_table>
   ```
2. Find the failing task in the timeline:
   ```bash
   tdx wf timeline <project_name>.<project_name>_launch --attempt-id <attempt_id> --log <task_name>
   ```
3. Compare the SQL in `sql/10_*.sql` / `sql/11_*.sql` / `sql/12_*.sql` against the `tdx describe` output — look for column name differences (e.g., `state` vs `state_code`)
4. Update the SQL file with the EXACT column name from `tdx describe`
5. Re-push: `tdx wf push --yes`

---

### Metrics look wrong — a number is much larger than expected

**Symptom:** A metric is many times larger than the value confirmed during Stage B

**Cause:** Many-to-many JOIN cardinality explosion (most common)

**Fix:**
1. Check JOIN cardinality:
   ```bash
   # Before join
   tdx query "SELECT COUNT(*) FROM service_history"
   # Result: 100,000

   # After join
   tdx query "
   SELECT COUNT(*) FROM service_history h
   LEFT JOIN service_appointments a ON h.service_id = a.service_id
   "
   # Result: 1,300,000 (13x bigger!)
   ```
2. If expanded > 2x original: it's a 1-to-many JOIN causing cardinality explosion
3. Fix using the CTE pre-aggregation pattern:
   ```sql
   WITH service_agg AS (
     SELECT service_id, SUM(cost) as total_cost FROM service_history GROUP BY service_id
   ),
   appointment_agg AS (
     SELECT service_id, COUNT(*) as appointments FROM service_appointments GROUP BY service_id
   )
   SELECT s.*, a.* FROM service_agg s LEFT JOIN appointment_agg a ON s.service_id = a.service_id
   ```
4. Update the SQL file and re-run the workflow

---

### Workflow runs slowly (> 5 min)

**Symptoms:**
```
✓ Workflow succeeded
✗ Runtime: 12 minutes (too slow for daily run)
```

**Diagnosis:**
```bash
# Check if td_time_range() is being used
grep -r "td_time_range" sql/
```

**Fix:**
- Verify `td_time_range()` is first in the WHERE clause (enables partition pruning)
- Reduce historical date range if possible
- Use `APPROX_DISTINCT`/`APPROX_PERCENTILE` instead of exact equivalents on high-cardinality columns
- See Performance Tuning below

---

### Permission denied

**Symptoms:**
```
Error: Permission denied creating database dashboard_db
```

**Fix:**
- Re-authenticate: `tdx login`
- Verify database permissions: `tdx databases`
- Check if the output database already exists with a different name

---

## Common Issue Summary Table

| Issue | Cause | Fix |
|-------|-------|-----|
| `${sink_database}` not resolved | Variables nested under `globals:` | Move all vars to top level in `input_params.yaml` |
| `INSERT INTO` fails | Target table doesn't exist yet | Use plain `SELECT` — `td>` with `create_table:` handles write |
| 0 rows in SINK tables | `td_time_range()` window doesn't overlap data | Check source data date range; update `start_date`/`end_date` |
| Duplicate rows (unexpected) | Using `insert_into:` without a filtered window | Switch to `create_table:`, or scope `insert_into:` SQL to the new time window only |
| Push fails — no project | New project — `push` requires an existing project | Use `tdx wf upload --name <project_name>` for the first deploy |
| Push fails — confirmation | Running in non-interactive mode | Use `tdx wf push --yes` |
| Cleanup fails | `cleanup_temp_tables: 'yes'` but no temp tables | Set `cleanup_temp_tables: 'no'` |
| Metrics mismatch | Exclusion rule not applied | Add `table_filter` in `input_params.yaml` + WHERE in SQL |
| `tdx db:create` not found | Command doesn't exist | Use `tdx query "CREATE SCHEMA IF NOT EXISTS <name>"` |
| Column errors | Typo or column doesn't exist | `tdx describe` to verify columns |
| Permission denied | Not authenticated | `tdx login` and verify permissions |

---

## Performance Tuning

Reference for optimizing workflow queries and SINK table design. Goal: SINK tables small enough that Phase 3 dashboard queries run < 1 second. Use `sql-skills:trino-optimizer` for deeper optimization help.

### Output Cardinality Targets (Soft Limits)

| Metric | Optimal | Acceptable | Needs Review |
|--------|---------|-----------|--------------|
| **Rows per SINK table** | < 100K | 100K-500K | > 500K (requires user approval + testing) |
| **Compression ratio** (raw → SINK) | > 100:1 | > 50:1 | < 50:1 (add aggregation) |
| **Workflow daily run time** | < 2 min | 2-5 min | > 5 min (optimize queries) |
| **Phase 3 dashboard query time** | < 1 sec | 1-3 sec | > 3 sec (split table or coarsen) |

**100K Soft Limit Explanation:**
- If SINK table exceeds 100K rows: Show user BEFORE/AFTER summary (Step 2 Cardinality Audit)
- If user approves 100K-500K: Test Phase 3 query performance in Phase 3
- If > 500K: Requires explicit user approval on performance trade-offs before deployment

### Partition Pruning — Must Be First in WHERE

`td_time_range()` prunes at the storage layer before any other filter. If it's missing or placed after other conditions, the engine scans the full table.

```sql
-- ✅ CORRECT: td_time_range first
WHERE td_time_range(event_time, TD_TIME_ADD(...), TD_SCHEDULED_TIME(), 'UTC')
  AND country = 'US'
  AND event_type = 'purchase'

-- ❌ WRONG: Complex filter first defeats partition pruning
WHERE event_type = 'purchase'
  AND CASE WHEN country = 'US' THEN true ELSE false END
  AND td_time_range(event_time, ...)
```

### APPROX Functions — Use by Default

```sql
-- ✅ FAST (2% error margin — acceptable for dashboards)
APPROX_DISTINCT(user_id)           -- vs COUNT(DISTINCT user_id): 20–50x faster
APPROX_PERCENTILE(value, 0.95)     -- vs PERCENTILE_CONT: memory-efficient on large tables

-- Only use exact versions when business requirement demands precision
COUNT(DISTINCT user_id)            -- Exact, but slow on high-cardinality cols
```

### Cardinality Fix Patterns

**Problem:** Output table > 100K rows (soft limit exceeded).

**Pattern: Show User BEFORE/AFTER + Reasoning**

When proposing cardinality optimizations, always show the user:

```
SINK Table: daily_sales_metrics

BEFORE (original grain):
  Dimensions: [date, region, store_id, product_id]
  Estimated rows: 365 × 10 × 500 × 5,000 = 9.125B rows ❌
  Query time: Timeout (table too large)

AFTER (optimized grain):
  Dimensions: [date, region, store_id, product_category]
  Estimated rows: 365 × 10 × 500 × 50 = 912.5K rows ✓
  Query time: ~2-3 seconds (acceptable with testing)

WHY: product_id has 5,000 values (excessive cardinality).
     Aggregated to product_category (50 values).
     Dashboard can filter by category, not individual product.

USER DECISION REQUIRED:
  ☐ Approve aggregation (lose product-level filtering)
  ☐ Keep product-level (accept slower queries, test in Phase 3)
  ☐ Alternative: Split into separate SINK tables
```

| Cause | Fix | User Approval Needed |
|-------|-----|--------|
| Too many grain dimensions | Aggregate high-cardinality dim → lower cardinality category | YES — confirm filtering scope change |
| Date range too long | Reduce `start_date` window (e.g., 365d → 90d rolling) | Confirm if shorter history is acceptable |
| One huge table | Split into per-use-case tables (daily summary + dimension breakdown) | Confirm additional complexity |

```yaml
# BEFORE: Over-grained — 500K+ rows
grain: [date, country, state, city, product, product_variant]

# AFTER: Coarser — ~50K rows
grain: [date, country, product_category]
```

### Slow Dashboard Queries — Diagnosis

```bash
# Check row count of SINK table
tdx query "SELECT COUNT(*) FROM <sink_database>.${project_prefix}_aggregate_final"

# Check execution plan for a slow Phase 3 query
tdx query "EXPLAIN SELECT country, SUM(revenue) FROM <sink_database>.${project_prefix}_aggregate_final WHERE event_date >= '2026-01-01'"
# Look for: Full Table Scan | Partition Scan
```

### Slow Workflow Runs — Diagnosis

```bash
# Check if td_time_range() is present in all SQL
grep -r "td_time_range" sql/
# All files should return matches

# View per-task runtimes
tdx wf attempt <project_name> <session_id>
# Identify slowest task — focus optimization there
```

### Pre-Production Checklist

Before handing off to Phase 3:

- [ ] Workflow daily run time < 2 min
- [ ] Cardinality audit completed with user approval (document BEFORE/AFTER analysis in state.md)
  - [ ] If SINK table ≤ 100K rows: proceed ✓
  - [ ] If SINK table 100K-500K rows: user approved performance trade-offs
  - [ ] If SINK table > 500K rows: explicit user approval + planned Phase 3 testing
- [ ] Any grain aggregations vs original requirements documented + approved
- [ ] `td_time_range()` present in every aggregation SQL file
- [ ] `APPROX_DISTINCT` used for all high-cardinality distinct counts
- [ ] Phase 3 query time spot-checked < 1 second on SINK tables (or 1-3s if > 100K rows)
- [ ] No full-table-scan warnings in `EXPLAIN` output

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
