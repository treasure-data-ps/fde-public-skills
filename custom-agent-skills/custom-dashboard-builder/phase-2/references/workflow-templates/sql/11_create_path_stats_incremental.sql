-- Create user journey path / funnel statistics (INCREMENTAL MODE — fresh window only)
-- Skill: sql-skills:trino | sql-skills:trino-optimizer
--
-- Used only when refresh_mode == 'incremental', paired with insert_into: (NOT create_table:)
-- after a separate +delete_lookback_window task clears the affected date range from the
-- SINK table. See 10_create_aggregates_incremental.sql header for full rationale — never
-- use create_table: for an incremental SINK write.
--
-- No WHERE/td_time_range() filter needed — events_prep was already scoped to the
-- incremental_look_back_days window by 01_data_prep.sql for this run.

SELECT
  event_date,
  device_type,
  country,
  event_type,
  COUNT(*)                        AS path_count,
  COUNT(DISTINCT user_id)         AS unique_users,
  APPROX_PERCENTILE(event_value, 0.5) AS median_value
FROM
  ${sink_database}.${project_prefix}_events_prep
GROUP BY
  event_date,
  device_type,
  country,
  event_type
