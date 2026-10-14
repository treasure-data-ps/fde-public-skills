# Phase 2 Entry Requirements: Extract Stage A/B Configuration

**MANDATORY — Do this FIRST before proceeding with Phase 2 steps. Time: 5 min.**

Phase 2 workflow optimization depends on 5 configuration values captured during Stage A/B. These are stored in `state.md`.

## The 5 Required Fields

Extract these from `./<project_name>/state.md` (Section: "Session Setup" — DO NOT EDIT):

1. **Historical Window** — Used in `td_time_range()` queries for partition pruning (e.g., `365`, `90`, `30` days)
2. **Refresh Schedule** — Determines cron schedule in `.dig` file (e.g., `daily`, `hourly`, `weekly`)
3. **SINK Database** — Target database for `create_table:` tasks (e.g., `analytics`, `dashboards`)
4. **Workflow Project Name** — Used in `.dig` file naming and `tdx wf` CLI commands (e.g., `customer-dashboard-wf`)
5. **Data Volatility** — Determines incremental processing pattern:
   - `append-only`: New data only, no updates
   - `1-day`: Last 1 day reprocessed each run
   - `7-day`: Last 7 days reprocessed for late arrivals
   - `event-driven`: Custom trigger, no regular schedule

## Why Each Field Matters

- **Historical window:** Enables efficient backfills and limits table scan scope in incremental runs
- **Refresh schedule:** Determines workflow frequency and when metric refreshes occur
- **SINK database:** Separates dashboard tables from source analytics (isolation + performance)
- **Workflow project name:** Required for CLI deployment; matches org naming conventions
- **Data volatility:** Controls whether to use `INSERT INTO` (append) or `DELETE + INSERT` (upsert); affects query cardinality and run time

## If Any Field Is Missing

Do **not** proceed with Phase 2. Return to Stage A/B and complete the discovery phase first. Missing configuration will result in:
- Incorrect time windows (backfill fails or query timeouts)
- Wrong refresh timing (dashboards stale or over-refreshed)
- Schema conflicts or permission errors on SINK write

---

## Next Step

Once all 5 fields are extracted and confirmed, proceed to **Phase 2 Steps 2a–2h**.

See `./phase-2-walkthrough.md` for the full step-by-step deployment guide.
