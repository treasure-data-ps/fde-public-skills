-- Create aggregated KPI metrics table (INCREMENTAL MODE — fresh window only)
-- Skill: sql-skills:trino | sql-skills:trino-optimizer
--
-- Used only when refresh_mode == 'incremental' (daily scheduled runs), paired with
-- insert_into: in the .dig file (NOT create_table:) — a separate +delete_lookback_window
-- task clears the affected date range from the SINK table first, then this query's
-- output is INSERTed. DELETE and INSERT are always two separate tasks; this query never
-- reads from the table it writes to.
--
-- ⚠️ WHY THIS MATTERS: an earlier version of this template used create_table: for BOTH
-- full and incremental modes. Since create_table: REPLACES the entire table on every run,
-- running in incremental mode silently discarded all history outside the lookback window
-- — a real data-loss incident caught during a production engagement (5 years of backfilled
-- data collapsed to ~7 days). See phase-2/references/incremental_update_patterns.md
-- "Critical SQL Rules" for the full writeup. Never use create_table: for the incremental
-- variant of any SINK table.
--
-- No WHERE/td_time_range() filter needed here — events_prep (01_data_prep.sql) was already
-- scoped to just the incremental_look_back_days window for this run, so every row in
-- events_prep belongs in this aggregation.

SELECT
  event_date,
  user_id,
  COUNT(*)                                                    AS total_events,
  COUNT(DISTINCT session_id)                                  AS sessions,
  COUNT(CASE WHEN event_type = 'conversion' THEN 1 END)       AS conversions,
  COALESCE(SUM(event_value), 0)                               AS total_value,
  APPROX_DISTINCT(session_id)                                 AS approx_sessions,
  MAX(device_type)                                            AS last_device
FROM
  ${sink_database}.${project_prefix}_events_prep
GROUP BY
  event_date,
  user_id
