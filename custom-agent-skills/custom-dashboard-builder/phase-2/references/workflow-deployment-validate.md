# Phase 2: Steps 2e-2h (Review, Deploy, Validate)

## Step 2e: Review Configuration (10-15 min)

**What to do:**
- Review and confirm configuration with the user before deployment
- Verify workflow file structure
- Run dry-run validation

### Workflow Structure Verification (MANDATORY — before dry-run)

Before running any validation, show the user the complete workflow file tree and ask them to confirm it matches their intent.

```bash
# Print the full workflow folder tree
find ./<project_name>/workflows -type f | sort
```

Present the output and use `AskUserQuestion`:

```
AskUserQuestion:
  header: "Verify workflow structure"
  question: "Workflow structure (pasted below). Confirm all .dig, SQL, and config files present:

<paste find output here>"
  options:
    - label: "Looks good — proceed"
    - label: "Stop — fix first"
    - label: "Show .dig contents"
```

If user selects **"Show me the .dig file contents first"**, run:
```bash
# Print each .dig file for review
for f in ./<project_name>/workflows/*.dig; do echo "=== $f ==="; cat "$f"; echo; done
```

Then re-ask the AskUserQuestion above. Do NOT proceed to dry-run until the user explicitly confirms the structure is correct.

**Configuration Review Checklist:**

- [ ] `input_params.yaml` — all variables at TOP LEVEL (no `globals:` nesting)
- [ ] `cleanup_temp_tables: 'no'` unless temp tables are actually created by SQL
- [ ] SQL files under `sql/` use plain `SELECT` (or `SELECT + UNION ALL`) — output is written via `create_table:`/`insert_into:` on the `.dig` task, not `INSERT INTO` in the SQL itself
- [ ] Launch file (`<project_name>_launch.dig`) runs `+run_data_prep_and_sink` unconditionally, and `+check_if_cleanup_needed` only if `cleanup_temp_tables: 'yes'`
- [ ] Database names correct (`source_database`, `sink_database`)
- [ ] Table names match Stage B validated schema
- [ ] Metrics calculations match Stage B requirements
- [ ] Exclusion rules from Stage A Step 1o present as `table_filter` entries in `aggregate_metrics_tables`
- [ ] `apply_time_filter` / `td_time_range()` used correctly for time filtering
- [ ] `APPROX_DISTINCT` used for high-cardinality columns (not `COUNT(DISTINCT)`)
- [ ] `COALESCE(SUM(col), 0)` used for nullable metric columns
- [ ] Schedule appropriate (frequency matches Stage A Step 1f)
- [ ] `start_date` / `end_date` cover Stage A Step 1g historical window
- [ ] `api_endpoint` matches correct TD region (US: `api.treasuredata.com` / EU: `api.eu01.treasuredata.com`)
- [ ] No YAML syntax errors (`python3 -c "import yaml,sys; yaml.safe_load(sys.stdin)" < input_params.yaml`)

**Dry-run validation:**

```bash
cd ./<project_name>/workflows
tdx wf push --dry-run

# Expected output:
# ✔ Project: <workflow_project_name>
# Changes: +N new, ~0 modified
# Dry run - nothing pushed
```

**Output:**
- ✅ All checklist items passed
- ✅ No syntax errors
- ✅ Ready for deployment

---

## Step 2f: Deploy Workflow to Treasure Data (10-15 min)

**What to do:**
- Check for existing TD workflow projects with similar names and confirm final project name
- Create SINK database if it doesn't exist
- Deploy workflow using `tdx wf upload` (new projects) or `tdx wf push` (existing)
- Trigger first run manually

⚠️ **CRITICAL: Use `tdx wf upload` for NEW projects, `tdx wf push` for EXISTING**

| Scenario | Command | Why |
|----------|---------|-----|
| **First deployment to Treasure Data** | `tdx wf upload --name <project_name>` | Creates new project and `tdx.json` |
| **Subsequent deployments** | `tdx wf push` | Updates existing project using `tdx.json` |

If you run `tdx wf push` without a prior `tdx.json`, it fails with "no workflow project found".

**Actions:**

1. **Check for existing projects with similar names:**

   ```bash
   tdx wf projects 2>&1
   ```

   Scan the list for projects that share the same name or are close variations of the intended `workflow_project_name` (from `state.md`, set in Stage A). Present findings to the user:

   ```
   Existing projects found:
   - acme_dashboard         (2025-03-10)
   - acme_kpi_v2            (2025-11-01)

   Intended: acme_custom_dashboard
   ```

   Then use `AskUserQuestion`:

   ```
   AskUserQuestion:
     header: "Project name"
     question: "Use acme_custom_dashboard, or rename to avoid collision?"
     options:
       - label: "Use acme_custom_dashboard"
       - label: "Rename to acme_custom_dashboard_v2"
       - label: "Custom name — I'll enter it"
   ```

   **Naming rules to enforce:**
   - Lowercase only, underscores for spaces (no hyphens — TD project names use underscores)
   - If an identical name already exists: always rename — pushing to an existing project with the same name overwrites it
   - If user picks a custom name: capture it and confirm before continuing

   Lock in the confirmed name as `PROJECT_NAME` before proceeding.

2. **⚠️ CONFIRMATION GATE — Confirm SINK database creation:**

   Before creating the SINK database, show the user what will be created:

   ```
   AskUserQuestion:
     header: "Create SINK database"
     question: "Create SINK database: <sink_database> in Treasure Data?"
     options:
       - label: "Yes, create now"
         description: "Create schema: tdx query CREATE SCHEMA <sink_database>"
       - label: "No, it already exists"
         description: "Database already exists; skip creation"
       - label: "Cancel — review first"
         description: "Let me review before creating"
   ```

   Only run `tdx query "CREATE SCHEMA..."` after user explicitly selects "Yes, create now".

3. **Check for SINK table collisions with existing tables (before creating SINK database):**

   If the SINK database (`sink_database`) already contains tables from other projects in your TD account (per Stage A Step 1q), a collision on SINK table names could silently overwrite that data.

   ```bash
   # List all existing tables matching the project_prefix pattern
   tdx tables --database <sink_database> 2>&1 | grep ${project_prefix}_
   ```

   **If tables with that prefix already exist:**

   ```
   AskUserQuestion:
     header: "SINK table collision"
     question: "Found existing tables with prefix '${project_prefix}_' in <sink_database>. These will be REPLACED on workflow run. Proceed?"
     options:
       - label: "Proceed — replace existing tables"
         description: "This project will overwrite the existing <sink_database>.${project_prefix}_* tables"
       - label: "Use different prefix"
         description: "Change project_prefix to avoid collision"
       - label: "Use different SINK database"
         description: "Specify a separate SINK database for this project"
   ```

   **Rules:**
   - If collision is from an unrelated table/project → **STOP and use a different prefix or SINK DB** (data loss risk)
   - If collision is from this same project (workflow re-deployed) → **OK to proceed** (intentional full refresh)
   - Document collision findings in `state.md` (Phase 2 section) for reference

4. **Create SINK database (if it doesn't exist):**

   ```bash
   tdx query "CREATE SCHEMA IF NOT EXISTS <sink_database>"
   ```

5. **⚠️ CONFIRMATION GATE — Show deployment preview before pushing:**

   Display the proposed deployment configuration and wait for explicit user confirmation:

   ```
   AskUserQuestion:
     header: "Review before deploying workflow"
     question: "Ready to deploy this workflow to Treasure Data? Review config below:"
     options:
       - label: "Yes, deploy now"
         description: "Push workflow: tdx wf upload/push"
       - label: "No, let me review first"
         description: "Cancel this push. Let me review the .dig files / SQL / config"
       - label: "Show dry-run output first"
         description: "Run dry-run, then ask again"
   ```

   **Show this preview to the user:**
   ```markdown
   **Workflow Deployment Preview:**
   - Project name: <PROJECT_NAME>
   - SINK database: <sink_database>
   - SINK table prefix: ${project_prefix}
   - Schedule: [cron expression, e.g., daily 2 AM UTC]
   - First run: full history from [start_date] to [end_date]
   - Tables to create: [list from .dig files, e.g., aggregate_final, path_stats]
   - Incremental mode: [append-only / lookback / state]
   - Location: <PROJECT_NAME console URL>
   ```

   If user selects **"Show dry-run output first"**:
   ```bash
   cd ./<project_name>/workflows
   tdx wf push --dry-run
   ```
   Display output, then re-ask the confirmation above. **Do NOT push until user explicitly selects "Yes, deploy now"**.

6. **First deployment: Create project with `tdx wf upload`** (only after confirmation above)

   ```bash
   cd ./<project_name>/workflows
   tdx wf upload --name ${PROJECT_NAME}

   # Expected:
   # ✔ Project uploaded
   # Project ID: <id>
   # Console: https://console.us01.treasuredata.com/app/workflows/<id>/info

   # This creates tdx.json automatically:
   # cat tdx.json
   # {"workflow_project": "<PROJECT_NAME>"}
   ```

7. **Subsequent deployments: Update with `tdx wf push`** (same confirmation pattern — ask before pushing)

   ```bash
   cd ./<project_name>/workflows
   tdx wf push --dry-run

   # Expected:
   # ✔ Project: <PROJECT_NAME>
   # Changes: +N new, ~0 modified, -0 deleted
   # Dry run - nothing pushed

   # Push for real (only after user confirms):
   tdx wf push --yes

   # Expected:
   # ✔ Push complete
   # Project ID: <id>
   # Revision: <timestamp>
   ```

8. **⚠️ CONFIRMATION GATE — Confirm before triggering first run:**

   The workflow is now deployed, but hasn't run yet. Show the user what will happen and get explicit approval:

   ```
   AskUserQuestion:
     header: "Trigger first workflow run"
     question: "Start the first workflow run covering historical data? This will create SINK tables in Treasure Data."
     options:
       - label: "Yes, trigger now"
         description: "Run: tdx wf run <PROJECT_NAME>.<project_name>_launch — creates SINK tables"
       - label: "No, I'll trigger manually"
         description: "Cancel this run. I'll trigger it manually from the TAS console"
       - label: "No, cancel — review first"
         description: "Cancel. Let me review the .dig files before running"
   ```

   **Show this run preview to the user:**
   ```markdown
   **First Workflow Run Preview:**
   - Project: <PROJECT_NAME>
   - Workflow: <project_name>_launch
   - Date range: [start_date] to [end_date] (historical full load)
   - SINK tables created: [aggregate_final, path_stats, unique_visitors, etc.]
   - Row count: [N rows expected per SINK table]
   - Estimated duration: 2-5 minutes
   - SINK location: <sink_database>
   - Status tracking: https://console.us01.treasuredata.com/app/workflows/<PROJECT_ID>/info
   ```

   **Only run `tdx wf run` after user explicitly selects "Yes, trigger now".**

9. **Trigger first historical run manually:**

   ```bash
   tdx wf run ${PROJECT_NAME}.<project_name>_launch

   # Expected:
   # ✔ Workflow run started
   # Attempt ID: <id>
   # Session ID: <id>
   ```

10. **Monitor the run in real-time:**

   ```bash
   # Visual timeline (updates live)
   tdx wf timeline ${PROJECT_NAME}.<project_name>_launch --follow

   # Or check after a few seconds
   tdx wf timeline ${PROJECT_NAME}.<project_name>_launch --attempt-id <attempt_id>

   # Expected (all green):
   # +run_data_prep_and_sink
   #   +check_refresh_mode
   #   +validate_data_quality
   #   +create_aggregates
   #   +create_path_stats
   #   +create_unique_visitors
   ```

   > If a task fails, get details:
   > ```bash
   > tdx wf attempt <attempt_id> tasks --include-subtasks
   > # Look for error message in the 'error' column
   > ```

**Output:**
- ✅ Existing projects checked — no name collision, or user confirmed rename
- ✅ `PROJECT_NAME` locked in before push
- ✅ SINK database created
- ✅ Workflow pushed (Project ID recorded)
- ✅ First run triggered and completed successfully
- ✅ Console URL bookmarked for monitoring

---

## Step 2g: Validate SINK Tables (10-15 min)

**What to do:**
- Verify all SINK tables exist with expected row counts
- Check for zero-row tables (silent failure mode)
- Spot-check metric accuracy against Stage B
- Verify `create_table:` behavior — replaces on re-run (no truncate needed)

**Actions:**

1. **Check all SINK tables exist:**

   ```bash
   tdx tables --database <sink_database>

   # Expected: all SINK tables listed (e.g. <project_prefix>_aggregate_final, _path_stats, _unique_visitors)
   # If any missing → check workflow logs for that task
   ```

2. **Validate row counts — zero rows = silent failure:**

   ```bash
   # Check each SINK table has rows
   tdx query "SELECT COUNT(*) as total_rows FROM <sink_database>.<table_name>"

   # ⚠ If result = 0 rows, diagnose:
   # 1. Check start_date / end_date in input_params.yaml match your data range
   # 2. Run this to see actual data range in source:
   tdx query "SELECT MIN(FROM_UNIXTIME(time)) as earliest, MAX(FROM_UNIXTIME(time)) as latest FROM <source_database>.<source_table>"
   # 3. If dates don't overlap → update start_date / end_date → re-push → re-run
   ```

3. **Validate breakdown types are populated (if using UNION ALL multi-breakdown pattern):**

   ```bash
   tdx query "SELECT breakdown_type, COUNT(*) as rows FROM <sink_database>.<table_name> GROUP BY breakdown_type ORDER BY breakdown_type"

   # Expected: each breakdown_type has the right number of rows
   ```

4. **Spot-check metric accuracy against Stage B — RE-RUN METRICS FRESH:**

   ⚠️ **CRITICAL: Re-run each Stage B metric query fresh and compare against the Stage B spot-check value.** Do NOT just verify column names exist — verify the VALUES are correct. Mistakes in WHERE clauses (e.g., unfiltered vs filtered lookback windows) are easy to miss and will silently ship wrong data to Phase 3.

   **For each Stage B-validated metric:**
   1. Copy the query from Stage B (or the `sql/` file if already updated)
   2. Run it against the source tables (do NOT query SINK yet — SINK is still being populated)
   3. Compare result to the Stage B recorded sample value
   4. If mismatch: identify why (missing WHERE clause? wrong column? JOIN fan-out?) and fix before Phase 3
   5. Document each metric check in `state.md` (Phase 2 section): one row per metric — Stage B value → Phase 2 re-run value → ✅/❌

   **Example:**
   ```bash
   # Stage B spot-check (from state.md):
   # Metric: "Active Customers (90-day)" → Value: 558 (55.8%)

   # Phase 2 validation (re-run fresh):
   tdx query "SELECT COUNT(DISTINCT customer_id) as active_customers_90d FROM <source_database>.<table> WHERE order_date >= DATE_SUB(current_date, interval 90 day)"

   # Result: 558 ✅ MATCHES Stage B → safe to proceed
   # If result: 737 ❌ MISMATCH → Stage B query had no WHERE clause; fix the metric before deploying
   ```

   Also compare SINK table results after first run:
   ```bash
   # Compare SINK table result to Stage B validated value
   tdx query "SELECT total_revenue FROM <sink_database>.<project_prefix>_aggregate_final WHERE breakdown_type = 'overall'"
   ```

5. **`create_table:` behavior on subsequent runs — verified:**

   > ✅ `create_table:` in the TD `td>` operator **replaces** the table on every run — it does NOT append.
   > No truncate step is needed for full-refresh SINK tables using `create_table:`.
   > Each scheduled run produces a clean, fresh set of SINK rows.
   >
   > **When duplicates CAN occur:** Only if you switch from `create_table:` to `insert_into:` without a preceding DELETE/truncate step. For incremental workflows (append new rows only), use `insert_into:` with a time-filtered SQL window — see Step 2h below.

   > ⚠️ **`retry --resume-from` caveat:** `tdx wf retry --resume-from <task>` is session-bound to the original workflow revision. After a re-push (which creates a new revision), `--resume-from` returns a 404 error for the old session. **Do NOT use `--resume-from` after a re-push.** Instead, trigger a fresh run: `tdx wf run`.

6. **Validate cross-join table cardinality (if applicable):**

   ```bash
   tdx query "SELECT dim_a, dim_b, COUNT(*) as rows FROM <sink_database>.<cross_join_table> GROUP BY dim_a, dim_b ORDER BY dim_a, dim_b"

   # Expected: row count = |dim_a values| × |dim_b values|
   # If 0 rows for any combination → check JOIN key + source data
   ```

7. **Lock in column names as Phase 3 contract (prevents silent empty widgets):**

   For every SINK table, run `tdx describe` and record the exact column names. Phase 3 (dashboard build) queries these columns by name — any mismatch returns empty results with no error.

   ```bash
   tdx describe -d <sink_database> <table_name>
   ```

   For each table, confirm:
   - Date column name (e.g., `date`, `event_date`, `order_date`) — Phase 3 date filters use this exact name
   - Metric column names match what Stage B approved (e.g., `total_revenue` not `revenue`)
   - Dimension column names match Stage B filter spec (e.g., `region` not `geo_region`)

   Document confirmed column names in `state.md` (Phase 2 section) → "SINK Tables" list. Phase 3 reads this before writing any query.

   **If a column name differs from the Stage B plan:** update `state.md` now — do not leave Phase 3 to discover the discrepancy mid-build.

8. **NULL audit on all metric columns (prevents silent blank widgets):**

   A SINK table with NULLs in metric columns causes dashboard widgets to show blank or zero without any error. Check every metric column per table:

   ```sql
   -- Run for each SINK table, replacing column names with actuals
   SELECT
     COUNT(*) AS total_rows,
     COUNT(CASE WHEN total_revenue IS NULL THEN 1 END) AS null_revenue,
     COUNT(CASE WHEN order_count IS NULL THEN 1 END)   AS null_count,
     COUNT(CASE WHEN unique_users IS NULL THEN 1 END)  AS null_users
   FROM <sink_database>.<table_name>;
   ```

   **Expected:** all NULL counts = 0.

   **If NULLs found:** wrap the column in `COALESCE(SUM(col), 0)` in the SQL file, re-push, re-run:
   ```sql
   -- Fix: replace bare SUM with COALESCE
   COALESCE(SUM(amount), 0) AS total_revenue
   ```

9. **Date column type check (prevents silent date filter failures in Phase 3):**

   SINK tables built with `DATE_FORMAT(FROM_UNIXTIME(...), '%Y-%m-%d')` produce VARCHAR, not DATE. Phase 3 date range filters fail silently if the column type is VARCHAR when a DATE is expected.

   ```bash
   tdx describe -d <sink_database> <table_name>
   # Look at the type column for your date field
   # VARCHAR → needs CAST in Phase 3 queries or fix the SQL now
   # DATE    → safe to use directly in date range filters
   ```

   **If date column is VARCHAR:** two options — fix in workflow SQL now (preferred), or note it in `state.md` so Phase 3 applies a `CAST(date_col AS DATE)` in every query.

   Fix in SQL (preferred):
   ```sql
   -- Replace VARCHAR date expression with explicit CAST
   CAST(DATE_FORMAT(FROM_UNIXTIME(TD_DATE_TRUNC('day', event_time)), '%Y-%m-%d') AS DATE) AS date
   ```

   If fixing now: re-push workflow, re-run, re-check row counts.

**Output:**
- ✅ All SINK tables exist with > 0 rows
- ✅ All breakdown types populated (if applicable)
- ✅ Spot-check metrics match Stage B values
- ✅ `create_table:` behavior confirmed — replaces on re-run (no duplicates, no truncate needed)
- ✅ Cross-join table cardinality validated (if applicable)
- ✅ Column names locked in `state.md` as Phase 3 contract
- ✅ No NULLs in metric columns
- ✅ Date column types confirmed (DATE, not VARCHAR)
- ✅ **Ready for Phase 3 (dashboard build)**

---

## SINK Table Documentation Template (After Step 2g)

After validating SINK tables, document each one. This becomes the reference for Phase 3 dashboard queries, Phase 4 agent knowledge base, and Phase 5 customer handoff.

**Create one entry per SINK table (in `state.md`):**

```
## [SINK_DB].[table_name]

| Property | Value |
|----------|-------|
| Rows     | [N] (grain: one row per [DIMENSION]) |
| Refresh  | [Daily/Weekly] at [TIME] UTC |
| Source   | [source_table] (joined with [lookup_table]) |
| Dimensions | [dim_1], [dim_2], [date_column] |
| Metrics  | [metric_1], [metric_2], [avg_metric] |
| Grain Note | [Fan-out note if rows > unique count — e.g., "1 customer × N vehicles = fan-out; always SUM + GROUP BY, never COUNT(*)"] |

Usage:
- Phase 3: source for [Widget 1], [Widget 2]
- Phase 4: agent queries for [Use Case]
```

### Grain & Fan-Out Reference Table

| Table | Grain | Unique Count | Rows | Fan-out? | Rule |
|-------|-------|--------------|------|----------|------|
| [table_1] | [grain] | [N] | [M] | M > N → YES | SUM + GROUP BY |
| [table_2] | [grain] | [N] | [M] | M = N → NO | Safe to COUNT(*) |

**Critical Rule:** If Rows > Unique Count, the table has fan-out. Use `SUM([metric]) GROUP BY`, never `COUNT(*)`.

### Quick Discovery Queries

```sql
-- Check row count and grain
SELECT COUNT(*) AS total_rows
     , COUNT(DISTINCT [dimension]) AS unique_dimension
FROM [SINK_DB].[table];

-- Check data freshness
SELECT MAX([date_column]) AS latest_date FROM [SINK_DB].[table];

-- Check for nulls in key columns
SELECT [column], COUNT(*) AS null_count
FROM [SINK_DB].[table]
WHERE [column] IS NULL
GROUP BY [column];
```

---

## Step 2h: Incremental Strategy Check + Test

**When:** After Step 2g passes — all SINK tables validated, row counts confirmed, metrics match Stage B.

**Goal:** Determine if the workflow can run incrementally (processing only new/changed data) rather than full-refreshing all history on every run. If yes, apply the incremental pattern and run a test.

---

### Step 2h-1 — Assess Each SQL File for Incremental Eligibility

Not every SQL file in the workflow can be made incremental. Evaluate each one individually before applying any changes.

**For each SQL file under `sql/`**, check three criteria:

| Criterion | How to check | Incremental eligible? |
|-----------|-------------|----------------------|
| Has a time column for partition pruning | `tdx describe -d ${source_database} ${source_table}` — look for `time`, `event_time`, `created_at`, `updated_at`, epoch column | ✅ Yes if found |
| Aggregates row-level transactional data | Read the SQL — does it `GROUP BY` date/dimension and `SUM`/`COUNT` rows? | ✅ Yes |
| Is a snapshot, cumulative total, or full-table join | Read the SQL — does it reference the entire history with no natural time partition? e.g. lifetime totals, dimension lookups, cohort tables, state tables | ❌ No — must stay full-refresh |

**Common non-incremental patterns (keep `create_table:`, do NOT switch to `insert_into:`):**
- Cumulative/running total queries (need all history to compute correctly)
- Dimension/lookup table joins (no time column, small static tables)
- Cohort tables (cohort month requires full historical scan)
- Cross-join cardinality tables (dimension × dimension, not time-partitioned)
- Any query with no `td_time_range()`-eligible column in the source

**Build an eligibility table** — list every SQL file and its verdict:

| SQL file | Source time column | Pattern | Incremental? |
|----------|--------------------|---------|-------------|
| `sql/10_create_aggregates.sql` | `event_time` | append-only | ✅ Yes |
| `sql/11_create_path_stats.sql` | `event_time` | append-only | ✅ Yes |
| `sql/cohort_retention.sql` | `cohort_month` (full scan) | snapshot | ❌ No |
| `sql/dim_customer.sql` | none | lookup | ❌ No |

**If NO files are eligible:** full-refresh is the only option. Proceed to the next step (Step 2h-2) and skip applying incremental — go straight to Phase 3.

**Report eligibility to the user before continuing:**

```
Incremental eligibility assessment:

✅ Can be made incremental (N files):
  - sql/10_create_aggregates.sql — has event_time, transactional aggregation
  - sql/11_create_path_stats.sql — has event_time, transactional aggregation

❌ Must stay full-refresh (N files):
  - sql/cohort_retention.sql — full historical scan required (cohort logic)
  - sql/dim_customer.sql — dimension lookup, no time column

Only the ✅ files will be switched to insert_into:. The ❌ files will keep create_table: unchanged.
```

Use `AskUserQuestion` to confirm before applying:

```
AskUserQuestion:
  header: "Incremental scope"
  question: "<N> of <total> SQL files can be incremental. <M> must stay full-refresh. Apply?"
  options:
    - label: "Yes — apply incremental to eligible only"
    - label: "Skip — keep full-refresh"
```

If **Skip**, proceed directly to Phase 3 — full-refresh (`refresh_mode: 'full'`) is production-ready as-is.

Also ask about data volatility for the eligible files:

```
AskUserQuestion:
  header: "Incremental mode"
  question: "Can source data be corrected after first recorded? (refunds, cancellations, re-sent events)"
  options:
    - label: "No — append-only (events, logs)"
    - label: "Yes — corrections within 1-3 days"
    - label: "Yes — corrections anytime / complex transformations"
```

> **Engine note for large datasets:** If source tables are very large (100M+ rows, multi-year history) and Trino queries are timing out or running slow, consider switching eligible SQL files to **Hive** engine. Hive handles large full-scans more reliably than Trino at the cost of speed. Set `engine: hive` on those specific `.dig` tasks. Only the large-scan tasks need Hive — keep Trino for small/incremental tasks.

---

### Step 2h-2 — Set the `refresh_mode` Flag

The embedded template already wires `refresh_mode` in `input_params.yaml` — every task in `<project_name>_data_prep.dig` branches on it:

```yaml
# Refresh mode — controls whether SQL loads the full historical window or appends incrementally
# 'full'        → uses start_date → end_date; run this on first deploy and after schema changes
# 'incremental' → appends the last incremental_look_back_days only; use for daily scheduled runs
refresh_mode: 'full'
incremental_look_back_days: 2       # days to look back on incremental runs (covers late-arriving data)
```

```yaml
# From <project_name>_data_prep.dig — already wired in the template
# NOTE: 01_data_prep.sql branches directly on ${refresh_mode} inside its own SQL
# (refresh_mode is already exported globally from input_params.yaml) — there is
# no .dig-level if> for this staging task and no "session_vars" parameter.
# ⚠️ session_vars is NOT a real digdag/td> parameter. An earlier version of this
# template passed a per-branch flag via "session_vars: data_window: full/incremental"
# — this is silently ignored by the td> operator, so ${data_window} was undefined and
# every run failed at evaluation time with "ReferenceError: data_window is not defined".
# Never reintroduce this pattern — branch on ${refresh_mode} (or another real exported
# variable) directly inside the SQL, or in the .dig file's own if>/_do/_else_do.
+prepare_source_data:
  td>: sql/01_data_prep.sql
  engine: presto
  create_table: ${project_prefix}_events_prep
```

**If your eligibility assessment (Step 2h-1) found tasks that need per-task `insert_into:` branching**, split into two files (`_full.sql` / `_incremental.sql`) and wire an `if>` block per eligible task in the `.dig` file itself, following the same pattern:

```yaml
# ✅ Eligible task — branches on refresh_mode
+kpi_daily:
  if>: ${refresh_mode == 'incremental'}
  _do:
    _retry: 3
    +delete_stale:
      td>:
        data: |
          DELETE FROM ${sink_database}.kpi_daily
          WHERE date >= TD_TIME_ADD(TD_SCHEDULED_TIME(), '-${incremental_look_back_days}d', 'UTC')
      engine: presto
      database: ${sink_database}
    +insert_incremental:
      td>: sql/kpi_daily_incremental.sql
      engine: presto
      database: ${sink_database}
      insert_into: kpi_daily
  _else_do:
    +full_refresh:
      td>: sql/kpi_daily.sql
      engine: presto
      database: ${sink_database}
      create_table: kpi_daily

# ❌ Non-eligible task — always full-refresh, no branching
+cohort_retention:
  td>: sql/cohort_retention.sql
  engine: presto
  database: ${sink_database}
  create_table: cohort_retention
```

**Two things that will fail silently or loudly if you get them wrong:**

1. **`td>: data: |`, never `td>: query: |`** for an inline literal statement like DELETE. Using `query:` produces `Parameter 'data' is required but not...` — `query:` is for referencing a query *template with variable substitution in a different sub-field structure*; for a plain inline SQL string, `data:` is the required key.
2. **Match the DELETE comparison type to your grain key's actual column type.** If your SINK table's date/grain column is a BIGINT epoch (e.g. produced by `TD_DATE_TRUNC`), compare against `TD_TIME_ADD(...)` directly (also bigint) — do NOT wrap it in `DATE_FORMAT`/`FROM_UNIXTIME` to compare as a string, that produces `Cannot apply operator: bigint <= varchar`. If your grain key is a formatted date STRING (e.g. from `DATE_FORMAT(FROM_UNIXTIME(...), '%Y-%m-%d')`), compare against the same string form instead. **Verify the actual column type** with `tdx describe <sink_database>.<sink_table>` before writing the DELETE, and test the DELETE manually against a COPY of the table (see the mandatory safety gate below) before trusting it in the workflow.

**Two SQL files per eligible task:**
- `sql/kpi_daily.sql` — full date range (`${start_date}` → `${end_date}`), used on `full` path
- `sql/kpi_daily_incremental.sql` — rolling lookback window, used on `incremental` path:

```sql
-- kpi_daily_incremental.sql
SELECT ...
FROM ${source_database}.orders
WHERE td_time_range(time,
  TD_TIME_ADD(TD_SCHEDULED_TIME(), '-${incremental_look_back_days}d', 'UTC'),
  TD_SCHEDULED_TIME(), 'UTC')
GROUP BY ...
```

**Switching between modes is a one-line change:**

```yaml
# First run (or force full re-process):
refresh_mode: 'full'

# All subsequent daily runs:
refresh_mode: 'incremental'
```

After Step 2g validation passes, update `input_params.yaml`, re-push, and run the incremental test (Step 2h-3 onward).

Use `AskUserQuestion`:

```
AskUserQuestion:
  header: "Apply incremental"
  question: "Push incremental changes? (refresh_mode: full → incremental)"
  options:
    - label: "Yes — push changes"
    - label: "No — revert and keep full refresh"
```

If No, restore `input_params.yaml` to the previous full-refresh settings.

> **State-managed pattern**: See `incremental_update_patterns.md` Pattern 3 — the `if>` structure is the same; the SQL delta logic reads from a state table instead of a fixed lookback window.

---

### ⚠️ MANDATORY: Pre-Incremental Safety Gate (run BEFORE Step 2h-3 push)

**This gate is not optional and cannot be skipped, even under time pressure.** A production incident occurred from skipping exactly this check: switching a live project's `refresh_mode` from `'full'` to `'incremental'` without first validating the incremental SQL/DELETE logic silently collapsed 5 years of backfilled SINK data down to a few days, because the incremental variant read-and-replaced the same table it was writing to under `create_table:` instead of using DELETE+`insert_into:`. The workflow *deployed successfully* and only failed at runtime, against real production tables that were already serving a live dashboard.

**Before pushing any `refresh_mode: 'incremental'` change to a project whose SINK tables already hold real historical data:**

1. **Record a baseline — for every SINK table, capture row count AND date range, not just row count:**
   ```bash
   tdx query "SELECT COUNT(*) as row_count, MIN(date) as min_date, MAX(date) as max_date FROM ${sink_database}.<project_prefix>_aggregate_final"
   # Repeat for every SINK table produced by this workflow. Save these numbers somewhere
   # you can compare against after the test run — do not rely on memory.
   ```

2. **Manually dry-run the DELETE statement's WHERE clause as a SELECT first** (never trust a DELETE you haven't previewed):
   ```bash
   # Swap DELETE FROM ... WHERE ... for SELECT COUNT(*) FROM ... WHERE ... with the
   # exact same WHERE clause the .dig task will run. Confirm the row count it will
   # delete looks like "the last N days" and not "the entire table".
   tdx query "SELECT COUNT(*) FROM ${sink_database}.<project_prefix>_aggregate_final WHERE <delete_where_clause>"
   ```

3. **Confirm the DELETE comparison type matches the grain key's actual column type** — run `tdx describe ${sink_database}.<project_prefix>_aggregate_final` and check whether the grain/date column is BIGINT or VARCHAR before trusting any `WHERE date >= ...` comparison (see the type-matching note under Step 2h-2).

4. **Run the full workflow once in a scratch/test project against a COPY of production data, or against the production project but only after Step 1's baseline is recorded** — either way, confirm the run succeeds AND that post-run row counts + date ranges exactly match the pre-run baseline from Step 1 (not "close to" — exactly, unless new rows were genuinely expected in the incremental window).

5. **If anything is wrong at this point — STOP.** Do not let the workflow run on its schedule while unverified. Revert `refresh_mode` to `'full'` in `input_params.yaml`, re-push, and re-run a full backfill to restore any data that may have already been affected, before debugging further.

```
AskUserQuestion:
  header: "Pre-incremental safety gate"
  question: "Baseline recorded for all N SINK tables (row count + date range)? DELETE WHERE clause previewed as a SELECT? Grain key type confirmed?"
  options:
    - label: "Yes — all checks passed, proceed to push"
    - label: "No — I need to complete these checks first"
```

**Do not proceed to Step 2h-3 without an explicit "Yes" on this gate.**

---

### Step 2h-3 — Push Updated Workflow

**Confirm before pushing:**

```
AskUserQuestion:
  header: "Confirm incremental push"
  question: "Push to <PROJECT_NAME>? (refresh_mode + <N> branching tasks)"
  options:
    - label: "Yes — push"
    - label: "No — revert"
    - label: "Show diff"
```

If user selects **"Show me the diff first"**: show a summary of what changed in `input_params.yaml`.
Then re-ask the confirmation above. Do NOT push until explicit "Yes".

Only push after explicit "Yes":
```bash
cd ./<project_name>/workflows
tdx wf push --yes
```

Confirm push succeeded before running the incremental test.

---

### Step 2h-4 — Run Incremental Test

Trigger a new manual run against the same project:

```bash
tdx wf run <project_name>.<project_name>_launch
```

Monitor until complete:
```bash
tdx wf timeline <project_name>.<project_name>_launch --follow
```

**Validate the incremental run — compare against the Pre-Incremental Safety Gate baseline you recorded, not just "does it look reasonable":**

```bash
# 1. Row count should match: (baseline row count) - (rows the DELETE removed) + (fresh rows inserted).
#    If your incremental window doesn't add NEW dates (e.g. you're testing against a
#    window with no new source data), the count should be EXACTLY UNCHANGED from baseline.
tdx query "SELECT COUNT(*) as row_count, MIN(date) as min_date, MAX(date) as max_date FROM ${sink_database}.<project_prefix>_aggregate_final"

# 2. Confirm the ENTIRE date range from baseline is still present — not just the max date.
#    A collapsed table (the exact incident this gate exists to prevent) still has a
#    plausible-looking MAX(date); only checking MIN(date) too catches it.

# 3. Check for duplicate grain-key rows introduced by an overlapping DELETE/INSERT boundary
tdx query "SELECT date, <other_grain_columns>, COUNT(*) as cnt FROM ${sink_database}.<project_prefix>_aggregate_final GROUP BY date, <other_grain_columns> HAVING COUNT(*) > 1 LIMIT 5"
# Expect: no rows returned. If rows come back, the DELETE and the fresh INSERT window
# don't line up exactly (e.g. comparing a truncated day boundary against a full
# TD_SCHEDULED_TIME() timestamp) — fix the WHERE clause boundary before trusting this run.

# 4. Run duration should be much shorter than the first (full) run
tdx wf sessions <project_name> --limit 2
# Compare duration of session 1 (historical/full) vs session 2 (incremental)
```

Present results:

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| Row count vs baseline | Matches expected delta exactly (see above) | — | |
| MIN(date) unchanged | Same as Pre-Incremental Safety Gate baseline | — | |
| MAX(date) | Today or yesterday | — | |
| Duplicate grain-key rows | Zero | — | |
| Run duration | Much shorter than full run | — | |

**If MIN(date) moved forward (history is missing):** This is the collapsed-table incident — the incremental branch used `create_table:` instead of DELETE+`insert_into:`, or the DELETE's WHERE clause matched far more rows than intended. STOP, revert `refresh_mode` to `'full'`, re-push, and re-run a full backfill to restore the lost history before debugging further.
**If row counts don't match the expected delta:** `insert_into:` ran without the delete step (rows accumulated/duplicated), or the delete/insert windows don't line up (a gap or overlap) — fix the delete task's WHERE clause and re-run.
**If duplicate grain-key rows exist:** DELETE and INSERT windows overlap at a boundary (e.g. comparing a truncated day against a precise timestamp) — align both to the same granularity (see the type-matching note under Step 2h-2) and re-run.
**If latest date is stale:** Time filter window is off — check `TD_SCHEDULED_TIME()` usage in the SQL.
**If duration unchanged:** Partition pruning not applied — verify `td_time_range()` is in the SQL WHERE clause.

---

### Step 2h-5 — Confirm Incremental is Production-Ready

```
AskUserQuestion:
  header: "Incremental OK?"
  question: "Row count: <X>, Latest: <DATE>, Duration: <TIME> — looks correct?"
  options:
    - label: "Yes — move to Phase 3"
    - label: "No — investigate"
    - label: "Revert and use full refresh"
```

If **revert**: switch all `insert_into:` back to `create_table:`, remove delete tasks, push again.

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team

---

## Error Recovery: Phase 2 Mistakes

### Scenario: Wrong Metric Definition Found During Phase 3

**Problem:** You realized in Phase 3 that a metric was incorrectly defined in Phase 2 (e.g., revenue should exclude discounts, but workflow doesn't).

**Recovery steps:**

1. **Fix the workflow SQL** in `./<project_name>/workflows/sql/`:
   ```sql
   -- Before (wrong)
   SELECT SUM(revenue) as total FROM sales
   
   -- After (correct)
   SELECT SUM(revenue - discount) as total FROM sales
   ```

2. **Re-deploy workflow:**
   ```bash
   cd ./<project_name>/workflows
   tdx wf push
   tdx wf run <workflow-name>
   ```

3. **Handle SINK table data:**
   - **Option A (clean slate):** Delete old SINK table, re-run workflow
     ```bash
     tdx table delete {SINK_DB}.{sink_table_name}
     tdx wf run <workflow-name>
     ```
   - **Option B (keep history):** Rename SINK table, create new one
     ```bash
     tdx table rename {SINK_DB}.{sink_table} {sink_table}_old
     tdx wf run <workflow-name>
     ```

4. **Re-validate Phase 3:**
   - Re-run Phase 3 validation queries against the corrected SINK tables
   - Verify metrics match expected values (spot-check)
   - Update dashboard queries to match corrected metric definition

5. **Document in state.md:**
   ```markdown
   ## RECOVERY: Metric definition fix
   
   **Issue:** Revenue metric was including discounts (wrong)
   **Fixed:** Changed to SUM(revenue - discount)
   **Action:** Re-deployed workflow, deleted old SINK table, re-ran Phase 3 validation
   **Date:** 2026-07-16
   ```

### Scenario: Workflow Runs But SINK Tables Are Wrong

**Symptom:** Workflow completes but SINK table row counts are zero or suspiciously low.

**Debug steps:**

1. **Check workflow logs:**
   ```bash
   tdx wf log <attempt-id>
   # Look for errors in data-prep tasks
   ```

2. **Check intermediate SINK tables:**
   ```sql
   SELECT COUNT(*) FROM {SINK_DB}.{sink_prefix}_01_raw;
   SELECT COUNT(*) FROM {SINK_DB}.{sink_prefix}_02_agg;
   -- Do counts match expectations?
   ```

3. **Common causes:**
   - Query has wrong WHERE clause (filtering out all rows)
   - JOIN is failing silently (no rows match)
   - Timezone mismatch in time filter (e.g., UTC vs PST)

4. **Fix & re-run:**
   - Correct the SQL in workflow sql/
   - Re-deploy: `tdx wf push && tdx wf run <workflow-name>`
   - OR force re-run: `tdx wf run <workflow-name> --retry`

---

