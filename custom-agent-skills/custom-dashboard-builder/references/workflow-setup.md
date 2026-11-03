# Workflow Setup (only when recommended)

Template: `<skill_dir>/project_templates/workflow_template/` — read its `README.md` (structure, customization, rules). This file adds the plan, the names, deploy and validation.

## 1. Plan (shown with the one approval question)

- **SINK tables** — one per data shape the dashboard reads, each with its grain and measures:
  - additive measures (SUM, COUNT) at day × every filter dimension of the widgets that use it;
  - ratios and averages stored as numerator + denominator; never SUM an average, a rate or a median;
  - distinct counts only on their display grain (e.g. per day without dimensions); per-period or per-dimension distinct counts need their own SINK table or a build-time source query;
  - semi-additive values (stock, balances) → last value / MAX per period;
  - no high-cardinality IDs in a grain; estimate rows first (target < 100 K per table, > 500 K needs the user's OK);
  - snapshot data (no time column) gets its own full-refresh table with no date filter.
- **Refresh** — full refresh (default). Mention incremental only for large tables (> 500 MB or ≥ 2 years at GB scale) and only after a validated full run.
- **Schedule** — proposed (e.g. daily 02:00 in the user's timezone, after the source data lands); enabled only after the first run is validated.
- **Names (defaults, accept or change):**
  - workflow project `<project_slug>_dashboard` (hyphens → underscores) — check `tdx wf projects <name>` returns nothing;
  - `sink_database` `<project_prefix>_dashboard` or an existing analytics database — `tdx tables --in <db>` must show no `<project_prefix>_*` tables of another project (they would be replaced); never the source database;
  - `project_prefix` = the project slug with underscores.

## 2. Build

```bash
d="agent_outputs/<project_slug>/workflows"
[ -d "$d" ] || { mkdir -p "$d" && cp -R "<skill_dir>/project_templates/workflow_template/." "$d/"; }
( cd "$d" && mv SLUG_launch.dig <project_prefix>_launch.dig && mv SLUG_data_prep.dig <project_prefix>_data_prep.dig )
```

Then edit the copy: `call>:` in the launch file; `input_params.yaml` (prefix, databases, source table, `event_time_expr`, `table_filter` with every confirmed exclusion, `history_start`); `sql/01_stage_events.sql` columns; one SQL file + one `+sink_*` task per SINK table (remove the examples you don't use).

Before pushing, run each SELECT once against real data (`tdx query -d <source_db> -f …` with the variables filled in by hand) and check it returns aggregated rows with plausible values.

### Several source tables

The template stages one primary table. Every other source table is read by one of three patterns — choose per SINK table:

| Pattern | Use when | How |
|---|---|---|
| **Stage, then SINK** | the primary table, or a table that several SINKs read | Staging SQL (`01_stage_events.sql` or a second `stg_*` task with `create_table:`); the SINK SQL reads `${project_prefix}_stg_*` |
| **Direct-read SINK** | a secondary table that only one SINK needs | The SINK SQL reads `${source_database}.<table>` fully qualified (the `_export` database is the sink) with the same `event_date` expression, `TD_TIME_RANGE(time, '${refresh_mode == "full" ? history_start : incr_start_day}', NULL, 'UTC')` window and `table_filter` as staging — the exclusions must apply to every source table; no staging table |
| **JOIN SINK** | a metric needs two tables at one grain | Pre-aggregate the many side to the join key in a subquery, then `LEFT JOIN` from the base table; report `COUNT_IF(d.<key> IS NULL)` unmatched rows |

For all three:
- Each SINK gets its own `+sink_*` task pair with its own full / incremental branch (see the template) — a direct-read SINK in incremental mode uses the same DELETE window on its `event_date`.
- A secondary table without a time column is a snapshot: read it in full each run, and its SINK stays full-refresh.
- Run the fan-out and match-rate checks (`data-discovery.md` §5) before writing the JOIN SQL.

## 3. Deploy, run, monitor

```bash
tdx query "CREATE SCHEMA IF NOT EXISTS <sink_database>"        # if the project owner may; otherwise the launch file's create step
( cd agent_outputs/<project_slug>/workflows && tdx wf upload --name <project> )   # first deploy; later: tdx wf push --yes
tdx wf run <project>.<project_prefix>_launch
tdx wf timeline <project>.<project_prefix>_launch --follow
```

On failure: `tdx wf attempt <id> tasks --include-subtasks`, then `tdx wf attempt <id> logs <task>`; fix the copy, re-push, and start a fresh run (an old session is bound to the old revision). Tell the user the first run takes several minutes.

## 4. Validate and report

- Every SINK table exists with rows > 0 (0 rows → `history_start` vs the source's MIN/MAX event date).
- No duplicate grain keys: `SELECT <grain>, COUNT(*) FROM t GROUP BY <grain> HAVING COUNT(*) > 1` returns nothing.
- `tdx describe` each SINK table — these column names and types are the contract for `generate-data.js`.
- NULL audit on every measure column.
- ≥ 3 metrics recomputed from the **source** for the same window match the SINK totals exactly (and the confirmed values from discovery).

Report in one short table (table, grain, rows, checks) and record the project name, database, tables and run in `project_state.md`. Then ask about the schedule (it stays disabled unless the user says yes) and continue to Step 4.

## Changing an existing workflow

Edit the copy in `agent_outputs/<project_slug>/workflows/`, re-push, run with `--param refresh_mode=full` once, and re-validate. Switch to incremental only after a validated full run: record row count and MIN/MAX date per SINK table first, run incremental once, and compare — MIN date unchanged, no duplicate grain keys, row delta as expected — before trusting it on the schedule.
