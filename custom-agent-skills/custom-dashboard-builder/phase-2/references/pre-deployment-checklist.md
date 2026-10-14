---
name: phase-2-pre-deployment-checklist
description: Pre-deployment validation checklist for Phase 2 workflows — catch schema, cardinality, and configuration issues before pushing
metadata:
  type: feedback
---

# Phase 2: Pre-Deployment Checklist

**Before running `tdx wf push` or `tdx wf upload`, complete all checks below.**

Failures here cause mid-run workflow crashes or silently wrong metrics. This checklist takes 30 minutes and prevents 2-4 hour rebuilds.

---

## Schema Validation (MANDATORY)

- [ ] Ran `tdx describe` on EVERY source table used in Stage A/B
- [ ] Copied exact column names from `tdx describe` output into SQL
- [ ] No column names guessed or from Stage A/B notes (verify each one)
- [ ] If any columns missing or renamed: updated `state.md` with actual names
- [ ] All Stage B metric names match real database columns

**Example check:**
```bash
tdx describe -d <source_db> service_history
# Copy exact output column names (state_code, not state)
```

---

## SQL Configuration (MANDATORY)

### Time Functions
- [ ] All aggregation queries use `TD_DATE_TRUNC('day', col)` for dates
- [ ] All date formatting uses `DATE_FORMAT(FROM_UNIXTIME(...), '%Y-%m-%d')` (strftime, NOT Java format)
- [ ] All time filters use `td_time_range(event_time, start, end)` for partition pruning
- [ ] No `TD_TIME_STRING` with Java format (yyyy-MM) — replaced with strftime

### Query Logic
- [ ] No direct many-to-many JOINs (checked cardinality before and after)
- [ ] All high-cardinality JOINs use CTE pre-aggregation pattern (see Pattern 4b)
- [ ] Checked: `SELECT COUNT(*) before_join FROM table1; SELECT COUNT(*) after_join FROM table1 JOIN table2`
  - If `after_join > 2 * before_join` → JOIN is 1-to-many, use CTEs
- [ ] All nullable metric columns use `COALESCE(SUM(col), 0)` instead of bare `SUM(col)`
- [ ] High-cardinality distinct counts use `APPROX_DISTINCT` (not `COUNT(DISTINCT)`)

### .dig File Format
- [ ] Every `create_table:` has a SEPARATE `database:` line (not combined path)
  ```yaml
  +task_name:
    td>: query.sql
    database: ${database}      # ✅ Separate line
    create_table: table_name   # ✅ Not: ${database}.table_name
  ```
- [ ] All aggregation tasks use `create_table:` (full-refresh), unless intentionally switched to `insert_into:` for incremental (Step 2h)
- [ ] No truncate step needed alongside `create_table:` (replaces on every run)
- [ ] Schedule confirmed with the user (daily 2 AM typical)
- [ ] `td_time_range` parameters match schedule frequency (if daily schedule, use 1-day window)

---

## Database & Infrastructure (MANDATORY)

- [ ] SINK database exists (or will be created: `tdx query "CREATE SCHEMA IF NOT EXISTS <sink_database>"`)
- [ ] SINK database name matches `${sink_database}` in `input_params.yaml`
- [ ] Source database accessible to your TD account
- [ ] Source and SINK databases different (don't write to source)

---

## Configuration Files (MANDATORY)

- [ ] `input_params.yaml` syntax valid (`python3 -c "import yaml,sys; yaml.safe_load(sys.stdin)" < input_params.yaml`)
- [ ] `input_params.yaml` has all required fields: `sink_database`, `source_database`, `project_prefix`, etc. — all at TOP LEVEL
- [ ] `config.json` syntax valid, if used (`jq '.' config.json` returns no errors)
- [ ] All `${variable}` references in `.dig` files are defined in `input_params.yaml`
- [ ] No hardcoded database names in SQL (all use `${sink_database}`, `${source_database}`)

---

## Workflow Structure Verification (MANDATORY)

- [ ] Ran `find ./<project_name>/workflows -type f | sort` and presented output to the user
- [ ] User explicitly confirmed all expected `.dig` files are present
- [ ] User explicitly confirmed all expected SQL files under `sql/` are present
- [ ] User confirmed no leftover or unintended template files are in the folder
- [ ] If user requested `.dig` file review: printed each `.dig` file and re-confirmed before proceeding

**Do NOT proceed to dry-run without explicit user confirmation of structure.**

---

## Deployment Method (CRITICAL)

- [ ] Ran `tdx wf projects` and scanned for existing projects with similar or matching names
- [ ] Presented matches to the user via `AskUserQuestion` — user confirmed or chose a different name
- [ ] `PROJECT_NAME` locked in (lowercase, underscores)
- [ ] If identical name already exists: user confirmed rename — never silently overwrite
- [ ] First time pushing this project? Use: `tdx wf upload --name ${PROJECT_NAME}`
  - Creates `tdx.json` automatically
  - Don't use `push` without a prior `tdx.json`
- [ ] Existing project? Use: `tdx wf push`
  - Verify `tdx.json` exists in the folder
  - `push` fails if no `tdx.json`

---

## Dry-Run Validation (MANDATORY)

```bash
# Run dry-run BEFORE pushing
tdx wf push --dry-run

# Expected output:
# ✔ Project: <project_name>
# Changes: +N new, ~0 modified
# Dry run - nothing pushed
```

- [ ] Dry-run completed without errors
- [ ] Dry-run shows expected number of new tasks
- [ ] No syntax errors in output

---

## Query Performance (RECOMMENDED)

Test each aggregation query individually:

```bash
# Test a single aggregation query (should complete in < 5 seconds)
tdx query -d <sink_database> < sql/10_create_aggregates.sql

# Monitor timeline to confirm fast partition pruning
# If query > 30 seconds, likely a cardinality issue
```

- [ ] Spot-check 2-3 aggregation queries complete in < 5 seconds
- [ ] If slow (> 30s): Check for missing `td_time_range()` or many-to-many JOINs

---

## Sign-Off

- [ ] All checks above completed and passed
- [ ] Ready to push: `tdx wf push --yes` (or `tdx wf upload --name <project_name>` if new)
- [ ] After push: Monitor first run in `tdx wf timeline <project>.<workflow> --follow`

**If any check fails: STOP. Fix the issue before pushing.**

---

**Failure Cost:** Pushing with unchecked issues → 2-4 hour debugging + user delay
**Prevention Cost:** This 30-minute checklist
**ROI:** 4-8x better (30 min investment prevents 2-4 hour problem)
---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
