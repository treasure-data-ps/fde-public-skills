# Phase 2: Deploy Dashboard Workflow

**Convert approved Stage B queries into a scheduled Treasure Data Workflow with pre-aggregated output tables (SINK tables).**

**Entry:** After Stage B Workflow path chosen | **Exit:** Workflow output tables (SINK tables) populated, workflow scheduled

---

## Phase 2 Overview

After Stage B, users choose between:
- **Non-Workflow Path:** Stage A/B (Requirements + Discovery) → Phase 3 (Build Dashboard) — skip Phase 2, query source tables on-demand
- **Workflow Path:** Stage A/B → Phase 2 (Build Workflow & Data Prep) → Phase 3 (Build Dashboard) — deploy workflow, query pre-aggregated SINK tables

Choose Phase 2 (Workflow) if:
- You need **daily scheduled freshness** (not manual refresh)
- Dashboard will be **accessed repeatedly** (frequent re-renders justify aggregation)
- Query performance matters (SINK tables typically 10-100x faster than source)
- **Cost efficiency is a goal** (scheduled runs replace repeated on-demand queries)

**Skip this phase if you don't need scheduled refresh** — go straight to Phase 3 (Build Dashboard) and query source tables directly.

---

## Phase 2 Architecture: Query Bridge

```
Stage A/B: Interactive     Phase 2: Workflow           Phase 3: Dashboard
(Approved SQL queries)     (Scheduled aggregation)     (Renders SINK tables)
         ↓                       ↓                            ↓
"Show revenue by date"   "Run daily 2 AM UTC"       "Query pre-agg tables"
"Show by region"         "Output to kpi_daily"      "Fast, < 2 seconds"
"Show trends over 365d"  "Pre-calculated metrics"   "Scheduled freshness"
```

**Key difference:**
- Stage A/B queries: Source tables directly (slow, ~5-10 sec)
- Phase 2 queries: Optimized for incremental updates (fast daily runs, ~30 sec)
- Phase 3 queries: SINK tables (pre-aggregated, < 2 sec, scheduled freshness)

→ **See [`workflow-setup-configure.md`](references/workflow-setup-configure.md)** for full architecture details

---

## Phase 2: Quick Reference - 8 Steps

| Step | Topic | Details |
|------|-------|---------|
| 2a | Set up workflow project | **Copy the locally embedded workflow templates** — see `./references/workflow-templates/`. See [`workflow-setup-configure.md`](references/workflow-setup-configure.md) |
| 2b | Configure parameters | Edit `input_params.yaml` with Stage B metrics, tables, filters, SINK DB. **Multi-source:** use flat `source_db_*` keys (one per database) — never nest. See [`workflow-setup-configure.md`](references/workflow-setup-configure.md) + [`input_params_examples.md`](references/input_params_examples.md) |
| 2c | Customize SQL queries | Replace template SQL with Stage B queries; optimize with `td_time_range()`. See [`workflow-setup-configure.md`](references/workflow-setup-configure.md) + [`td-time-functions.md`](references/td-time-functions.md) |
| 2d | Configure datamodel | Only if you're using an SINK-aware analytics layer that requires a schema config file (e.g. a datamodel/join config). Skip if not applicable. See [`workflow-setup-configure.md`](references/workflow-setup-configure.md) |
| 2e | Review config | **Verify workflow file structure with the user** (AskUserQuestion) + pre-deploy checklist + dry-run validation. See [`workflow-deployment-validate.md`](references/workflow-deployment-validate.md) |
| 2f | **Deploy workflow + collision check** | Push to Treasure Data + trigger first run. **⚠️ Before locking in `project_prefix`, check for SINK table collisions** (see Step 2f details). See [`workflow-deployment-validate.md`](references/workflow-deployment-validate.md) |
| 2g | **Validate output + re-verify metrics** | **Verify SINK tables created, row counts correct, re-run Stage B metrics fresh and diff against Stage B spot-checks** (not just verify column names exist). See [`workflow-deployment-validate.md`](references/workflow-deployment-validate.md) |
| 2h | **Incremental strategy** | **After first run validated: assess data volatility, apply incremental pattern (append/upsert/state), run incremental test run and verify row counts + duration**. See [`workflow-deployment-validate.md`](references/workflow-deployment-validate.md) |

---

## Starting Point: Locally Embedded Templates

The workflow templates are bundled with this skill — no external repo access needed. Everything in `./references/workflow-templates/` (`<project_name>_launch.dig`, `<project_name>_data_prep.dig`, `<project_name>_cleaner.dig`, `input_params.yaml`, `sql/*.sql`) is a ready-to-customize starting point.

---


### ⚠️ Cron `?` Wildcard — When You Need It

Digdag's `cron>:` scheduler uses a Quartz-style cron format with 5 fields: `minute hour day-of-month month day-of-week`. Quartz cron treats `day-of-month` and `day-of-week` as mutually exclusive: when one of them is constrained to a specific value, the other must be set to `?` ("no specific value") rather than `*`.

**✅ DO use `?`** in whichever of `day-of-month` / `day-of-week` you are NOT constraining:
```yaml
# Every Monday at 8 AM — day-of-week is constrained (MON), so day-of-month is "?"
schedule:
  cron>: "0 8 ? * MON"

# 1st of month at 2 AM — day-of-month is constrained (1), so day-of-week is "?"
schedule:
  cron>: "0 2 1 * ?"
```

**✅ DO use `*`** for simple daily schedules where neither day-of-month nor day-of-week is constrained:
```yaml
schedule:
  cron>: "0 2 * * *"   # Run daily at 2 AM UTC
```

**Common mistake:** Using `*` for BOTH day-of-month and day-of-week when one of them is actually constrained (e.g., `"0 8 * * MON"`) — Quartz cron rejects or misinterprets this because both fields can't be simultaneous wildcards when one of them has meaning tied to the other. When you constrain day-of-week (e.g., `MON`), set day-of-month to `?`, and vice versa.

→ **See [`workflow-setup-configure.md`](references/workflow-setup-configure.md) → "Schedule Configuration"** for the full cron cheat sheet and worked examples.

---




## Phase 2 Optional: Data Retention with Cleaner Task

**Template:** `./references/workflow-templates/<project_name>_cleaner.dig`

**When to use:**
- Dashboard only needs recent data (e.g., last 90 days)
- SINK tables grow large (> 100 GB)
- Cost reduction is a priority

**How to wire into your workflow:**

1. **Configure retention** in `input_params.yaml`:
   ```yaml
   SINK_RETENTION_DAYS: 90
   ```

2. **Include cleaner in your main workflow** (`<project_name>_launch.dig`):
   ```yaml
   +run_cleaner:
     +call>: <project_name>_cleaner.dig
     params: {SINK_DB: ${SINK_DB}, SINK_RETENTION_DAYS: ${SINK_RETENTION_DAYS}}
   ```

3. **Verify deletion** (after first workflow run):
   ```sql
   SELECT MIN(date) as oldest, MAX(date) as newest
   FROM {SINK_DB}.{SINK_PREFIX}_kpis;
   -- Should show oldest ≈ SINK_RETENTION_DAYS old
   ```

**Storage impact:** Steady-state ~40-50 GB (vs. 500+ GB without cleaner)

---


## How to Execute Phase 2

### Step 0: Copy Workflow Templates

```bash
# Copy workflow templates into your project working directory
mkdir -p ./<project_name>/workflows

cp -r ./references/workflow-templates/. ./<project_name>/workflows/
```

---


### Multi-Database Joins (Cross-DB Queries)

**If your dashboard joins tables from DIFFERENT Treasure Data databases:**

**Problem:** Joins across databases are slower (~2-5x) than same-database joins because data must be shuffled across nodes.

**Solution (Phase 2 workflow):**

1. **Pre-aggregate in workflow:** Join at query time in the `.dig` file, output to a SINGLE SINK table

```sql
-- sql/01-join-across-dbs.sql
SELECT 
  a.date,
  a.region,
  a.product,
  b.channel,
  COUNT(*) as n,
  SUM(a.revenue) as r
FROM {SOURCE_DB_A}.orders a
JOIN {SOURCE_DB_B}.channels b ON a.channel_id = b.id
WHERE td_time_range(a.time, '{START_DATE}', '{END_DATE}')
GROUP BY 1,2,3,4
```

2. **Result:** Single SINK table with pre-joined data → Phase 3 queries are fast

**Alternative (Phase 3 without workflow):**

If you skip Phase 2, your Phase 3 queries will hit both databases on EVERY dashboard render. This is **slower but simpler for one-off dashboards**.

**Best practice:** If you're joining databases, use Phase 2 to pre-aggregate once per day; Phase 3 just queries the SINK table.

---


### Step 2a: Set Up Project

**Customize workflow templates with Stage B discoveries:**

```bash
# Templates are now in your local working directory
# Follow Steps 2a-2d below to customize them for this engagement
```

1. **Edit `input_params.yaml`** — primary config: source tables, SINK DB, metrics list, time window, exclusion filters
2. **Customize SQL files** — replace template SQL with Stage B queries; apply `td_time_range()` for partition pruning

→ **See [`workflow-setup-configure.md`](references/workflow-setup-configure.md)** for detailed per-step guidance
→ **See [`input_params_examples.md`](references/input_params_examples.md)** for `input_params.yaml` worked examples

### Step 2b: TD Time Functions

**3 Key Functions:**
- `td_scheduled_time()` — Fixed reference time for reproducible runs
- `td_time_string()` — Format dates as YYYY-MM-DD strings
- `td_time_range()` — Partition pruning (CRITICAL for performance)

**Incremental Processing Modes:**
- **Append-only:** For immutable data (fastest, ~30 sec daily)
- **1-day lookback:** For same-day corrections
- **7-day lookback:** For corrections up to 7 days old

→ **See [`td-time-functions.md`](references/td-time-functions.md)** for patterns, examples, and performance impact

### Step 2e-2g: Review & Deploy

1. **Review configuration** (checklist in step 2e)
2. **Deploy workflow** to Treasure Data
3. **Validate output tables** (verify SINK tables created with correct data)

→ **See [`workflow-deployment-validate.md`](references/workflow-deployment-validate.md)** for deployment commands and validation queries

### Test & Troubleshoot (if needed)

- Run testing checklist (schema, data quality, workflow, performance)
- If issues, use troubleshooting guide for common problems

→ **See [`testing-troubleshooting.md`](references/testing-troubleshooting.md)** for full checklist and troubleshooting guide

---

## Key Reference Materials

| I want to... | See... |
|---|---|
| **Understand the template structure** | `./references/workflow-templates/` — launch, data-prep, cleaner, input_params.yaml |
| **Get detailed guidance per step** | [`workflow-setup-configure.md`](references/workflow-setup-configure.md) (2a-2d), [`workflow-deployment-validate.md`](references/workflow-deployment-validate.md) (2e-2h) |
| **Configure `input_params.yaml`** | [`input_params_examples.md`](references/input_params_examples.md) — worked examples for metrics, filters, time windows |
| **Understand TD time functions** | [`td-time-functions.md`](references/td-time-functions.md) — patterns, incremental modes, performance testing |
| **Test & troubleshoot** | [`testing-troubleshooting.md`](references/testing-troubleshooting.md) — checklist, common issues, diagnostics |
| **Understand Phase 2 architecture** | [`workflow-setup-configure.md`](references/workflow-setup-configure.md) — architecture, key principles, datamodel design |
| **See all reference files** | [`INDEX.md`](references/INDEX.md) — directory index |

---

## Phase 2 Input Requirements (Read From Stage A & Stage B)

**From Stage A** (via `state.md` Session Setup block — see `workflow-setup-configure.md` → "Phase 2 Entry Requirements"):

- ✅ **Historical window** — How far back (days)? (from Stage A Step 1g)
- ✅ **Refresh schedule** — When should workflow run? (from Stage A Step 1e+1f — daily 2 AM UTC typical)
- ✅ **SINK database** — Where to store aggregated tables (from Stage A Step 1q — Workflow path only)
- ✅ **Workflow project name** — TD project identifier (from Stage A Step 1q — Workflow path only)
- ✅ **Data volatility** — Incremental strategy: append-only / 1-day lookback / 7-day lookback (from Stage A Step 1q)

**From Stage B** (via `state.md` Data Discovery block):

- ✅ **Approved SQL queries** — 5-10 validated queries covering metrics, dimensions, trending (from Stage B Steps 2c-2d)
- ✅ **Sample data validated** — Metric spot-checks confirmed accuracy (Phase 2 Step 2g will re-validate against SINK output)
- ✅ **Datamodel decisions** — Grain, dimensions, filters (from Stage B Steps 2a-2f)

**Stage A/B→Phase 2→Phase 3 Chain:** Stage A captures schedule + window → Stage B validates metrics + queries → Phase 2 deploys with this context.

---

## Performance Expectations

| Stage | Time | Notes |
|---|---|---|
| Historical load (365 days) | 2-5 min | One-time, first run |
| Daily incremental run | 30-45 sec | Using td_time_range() partition pruning |
| Phase 3 dashboard queries | < 2 sec | Reading pre-aggregated SINK tables |

---

## Phase 2 Key Principle

**Query optimization enables daily scheduled freshness at fast query speeds.**

| Aspect | Non-Workflow (Stage A/B → Phase 3 (Build Dashboard)) | Workflow (Stage A/B → Phase 2 (Build Workflow & Data Prep) → Phase 3 (Build Dashboard)) |
|--------|--------|---------|
| Query target | Source tables directly | Pre-aggregated SINK tables |
| Query speed | 5-10 seconds | < 2 seconds |
| Freshness | Always fresh | Scheduled (daily 2 AM UTC) |
| Refresh method | Manual (user reloads) | Automatic (workflow runs) |
| Build time | Faster | Slower (workflow setup) |
| Cost | Higher (many queries) | Lower (batched runs) |
| Use case | Exploratory | Production, recurring |

---

## Troubleshooting & Testing

- **Testing checklist:** See [`testing-troubleshooting.md`](references/testing-troubleshooting.md) (schema, data quality, workflow, performance)
- **Common issues:** See [`testing-troubleshooting.md`](references/testing-troubleshooting.md) (deployment, empty tables, slow runs, etc.)
- **Performance tuning:** See [`td-time-functions.md`](references/td-time-functions.md) (td_time_range optimization)

---

## Next: Phase 3 (Build Interactive Dashboard)

**Before proceeding:** Append Phase 2 outputs to `state.md`.

→ **See "Phase 2 Deliverables (End of Phase)" below** for the single `state.md` append template and end-of-phase checklist.

Phase 3 covers:
- Build dashboard from SINK tables (queries now < 2 seconds instead of 5-10 seconds), rendered as a single portable HTML Client dashboard
- Add filters, drill-downs, exports
- Validate dashboard accuracy
- Performance & mobile testing

**Entry point:** `./phase-3/SKILL.md` → `./phase-3/references/phase-3-walkthrough.md`

**Key difference:** Phase 3 queries `dashboard_db.kpi_daily` (SINK from Phase 2) instead of `sales_db.orders` (source from Stage B).

---

## Reference Directory

All detailed guidance lives in: `./references/`

→ **Start with [`INDEX.md`](references/INDEX.md)** for complete directory and file descriptions.

---

## Pre-Phase 2 Checklist

Before starting Phase 2, confirm all Stage A/B deliverables:

- ✅ Stage A/B complete: Requirements + Data discovery finished, confirmed directly with the user
- ✅ `state.md` accessible locally — **read it at Phase 2 start** for SINK DB name, project name, schedule, metric definitions
- ✅ Score 4–6 confirmed (Workflow path)
- ✅ Dashboard plan reviewed and confirmed with the user
- ✅ TD credentials with write access to SINK database
- ✅ TD API endpoint known (US: `api.treasuredata.com` / EU: `api.eu01.treasuredata.com`)

**If `skip_workflow = true`** (data source is pre-aggregated — set in Stage A Step 1-pre-D): Skip this phase. Go directly to Phase 3.

**If resuming Phase 2:** Read `./<project_name>/state.md` → find current step → jump there.

---

## CRITICAL: Before Pushing Workflow to Treasure Data

**Do not run `tdx wf push` until you've completed the Pre-Deployment Checklist.**

→ **See: `./references/pre-deployment-checklist.md`** — catches 99% of workflow failures:
- Schema validation (column names match actual database)
- Time function format (strftime, not Java format)
- JOIN cardinality checks (prevent 10x metric inflation)
- `.dig` file format (explicit `database:` parameter)
- Deployment method (`tdx wf push`)

---

## If Workflow Fails After Deployment

→ **See: `./references/testing-troubleshooting.md`** — covers: table not found, column not found, JOIN cardinality explosion, workflow push failures, missing `td_time_range`, date formatting issues.

---

## Workflow File Naming: Understanding the Numbering Convention

**Current template structure:**
```
<project_name>_launch.dig         ← main orchestrator
<project_name>_data_prep.dig      ← data preparation
<project_name>_cleaner.dig        ← temp cleanup
```

### Numbering Not Required (But Clarifies Execution Order)

The template intentionally avoids numeric prefixes (01_, 02_, 03_) because:
- **Digdag executes explicitly** — tasks run based on `call>:` dependencies, not filename order
- **Naming is for humans** — use descriptive names like `data-prep`, `validation`, `deploy` instead of `01-*`, `02-*`, `03-*`
- **Easier to maintain** — adding a new workflow step doesn't require renumbering all files

### If You Prefer Numeric Prefixes

You can rename files for clarity (optional):

```bash
# Personal preference only — not required
mv <project_name>_launch.dig       01-<project_name>_launch.dig
mv <project_name>_data_prep.dig    02-<project_name>_data_prep.dig
mv <project_name>_cleaner.dig      03-<project_name>_cleaner.dig

# Update `call>:` references in main .dig files:
# Before: call>: <project_name>_data_prep.dig
# After:  call>: 01-<project_name>_data_prep.dig
```

### Best Practice

**Use descriptive names, not numbers:**
- ✅ `dashboard-data-prep.dig` — clear purpose
- ✅ `dashboard-validation.dig` — clear purpose
- ❌ `01_workflow.dig` — unclear purpose

**Keep the execution DAG explicit in your main `.dig` file:**
```yaml
# <project_name>_launch.dig
+run_data_prep:
  call>: <project_name>_data_prep.dig

+run_cleanup:
  call>: <project_name>_cleaner.dig
```

Readers see the execution order right there, no need for filenames to communicate it.

---


---

## SQL File Numbering Convention (01, 02, 03, 10, 11, 12)

**Current structure:**
```
01_data_prep.sql              ← stage 1
02_data_validation.sql        ← stage 2
03_create_time_filter.sql     ← stage 3 (optional/reference-only — not wired into any .dig file by default; see workflow-setup-configure.md Step 2a)
10_create_aggregates.sql      ← stage 10 (main aggregations)
11_create_path_stats.sql      ← stage 11 (supplementary stats)
12_create_unique_visitors.sql ← stage 12 (supplementary stats)
```

**Numbering rationale:**
- **01-03:** Data preparation and validation (initial stage)
- **10-12:** Aggregate table creation (final output, can be parallelized)

**Why this numbering?**
- Digdag can parallelize 10, 11, 12 (all after 01-03 complete)
- Gaps (10 vs 04) leave room for new intermediate steps without renumbering

**If adding new steps:**
- After validation? Use **04, 05, 06** (sequential with 01-03)
- Parallel aggregations? Use **13, 14, 15** (after 10-12)

---

---

## Phase 2 Deliverables (End of Phase)

At end of Phase 2, you have:

✅ **Deployed Treasure Data Workflow**
✅ **Scheduled SINK tables** (pre-aggregated daily output)
✅ **Optimized queries** (using `td_time_range` for partition pruning)
✅ **Data validated** (metrics match Stage B, no quality issues)
✅ **Workflow running on schedule** (daily 2 AM UTC)

**→ Ready for Phase 3** — Dashboard renders from fast SINK tables

**Document Update Rule: APPEND, never overwrite.** Read `state.md` first, append below the Stage B block — never touch prior content.

Append to **`state.md`**:

```markdown
## Phase 2: Workflow Deployment Complete (YYYY-MM-DD)

### Workflow Project
- workflow_name / TD project name: [project-name]
- Orchestrator: [main .dig file, e.g. <project_name>_launch.dig]
- Schedule: [daily 2 AM UTC / other — first run = full history; subsequent = incremental]
- SINK Database: [sink_database]
- First run mode: full (start_date: [YYYY-MM-DD] → end_date: [YYYY-MM-DD])
- Incremental strategy: [append-only / 1-day lookback / 7-day lookback]

### SINK Tables Validated
| Table Name | SQL File | Row Count | Notes |
|---|---|---|---|
| [table_1] | [10_*.sql] | [N rows] ✓ | [e.g. daily KPI aggregates] |
| [table_2] | [11_*.sql] | [N rows] ✓ | [e.g. dimension breakdown] |

### Metric Cross-Checks (Phase 2 vs Stage B)
| Metric | Stage B spot-check | Phase 2 SINK value | Match? |
|---|---|---|---|
| [Metric 1] | [value] | [value] | ✅ |
| [Metric 2] | [value] | [value] | ✅ |

### SQL Changes vs Stage B Plan
- [List any changes to queries, filters, or table names from Stage B approved queries]
- [None if no changes]

### Performance
- Historical load (first run): [X min]
- Daily incremental run: [X sec]

### SINK Table → Dashboard Section Mapping
*(Phase 3 reads this to know which table to query for each widget)*
| Dashboard Section | SINK Table | Key Columns |
|---|---|---|
| [KPI cards] | [table name] | [columns] |
| [Monthly trend] | [table name] | [columns] |
| [By dimension] | [table name] | [columns] |

### Status
✅ All sub-workflows completed successfully
✅ SINK tables validated against Stage B spot-checks
✅ Ready for Phase 3

### Next Action
→ Phase 3 (Build Dashboard): Build dashboard querying [sink_database] SINK tables
```

**End-of-Phase Checklist:**
- ✅ Templates copied to `./<project_name>/workflows/`
- ✅ `input_params.yaml` configured with Stage B metrics, source tables, exclusion filters
- ✅ All SQL files updated with `td_time_range()` optimization
- ✅ **User confirmed workflow file structure before push (AskUserQuestion)**
- ✅ SINK database created and populated
- ✅ All SINK tables exist with expected row counts
- ✅ Metric values cross-validated against Stage B spot-checks
- ✅ All sub-workflow sessions show SUCCESS
- ✅ **Incremental strategy assessed (append / upsert / state / skipped)**
- ✅ **If incremental applied: test run passed (row counts unchanged, latest date correct, duration reduced)**
- ✅ `state.md` Phase 2 block updated locally

---

## Quick Reference: Which File?

| Question | Reference |
|----------|-----------|
| Template structure | `./references/workflow-templates/` |
| Configure `input_params.yaml` | `./references/input_params_examples.md` |
| Use `td_time_range()` | `./references/td-time-functions.md` |
| Incremental mode choice | `./references/td-time-functions.md` — volatility decision table |
| Configure datamodel (if applicable) | `./references/workflow-setup-configure.md` — Datamodel Design Principles section |
| Deploy with `tdx wf push` | `./references/workflow-deployment-validate.md` Step 2f |
| Validate SINK tables | `./references/workflow-deployment-validate.md` Step 2g |
| Troubleshoot failures | `./references/testing-troubleshooting.md` |

---

## Next Phase

### ➡ Route to Phase 3 (always — after Step 2g validation passes)

**SINK table contract for Phase 3:**
- Star schema, pre-aggregated — each row is one unique combination of ALL filter dimensions with metrics pre-computed
- Phase 3 queries use `WHERE` + `GROUP BY` — never JOINs
- All filters apply at SQL `WHERE` clause, never post-filter client-side

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team

---

## ℹ️ Phase 2 Step Numbering Reference

| Step | Topic | Duration |
|---|---|---|
| 2a | Set up workflow project | 5-10 min |
| 2b | Configure parameters | 10-15 min |
| 2c | Customize SQL queries | 20-30 min |
| 2d | Configure datamodel (optional) | 10-15 min |
| 2e | Review config & pre-deploy checklist | 5-10 min |
| 2f | Deploy workflow & collision check | 5 min |
| 2g | Validate output & re-verify metrics | 10 min |
| 2h | Incremental strategy (optional) | 15-20 min |

---
