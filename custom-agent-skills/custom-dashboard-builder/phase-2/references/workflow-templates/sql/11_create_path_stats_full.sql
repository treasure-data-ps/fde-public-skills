-- Create user journey path / funnel statistics (FULL MODE)
-- Skill: sql-skills:trino | sql-skills:trino-optimizer
--
-- Used only when refresh_mode == 'full'. Paired with create_table: in the .dig file.
--
-- If one of your SINK tables is a snapshot (no time column — e.g. a customer dimension table),
-- do NOT add a td_time_range() filter. Snapshot tables ignore date/channel/category filters
-- on the dashboard — document this in knowledge/data_dictionary.md (Phase 5 Step 5a).
--
-- Remove this file (both variants) and its .dig tasks if path/funnel analysis is not in
-- scope for this engagement.

SELECT
  event_date,
  device_type,
  country,
  event_type,
  COUNT(*)                        AS path_count,
  COUNT(DISTINCT user_id)         AS unique_users,
  -- APPROX_PERCENTILE is more memory-efficient than exact PERCENTILE_CONT on large datasets
  APPROX_PERCENTILE(event_value, 0.5) AS median_value
FROM
  ${sink_database}.${project_prefix}_events_prep
GROUP BY
  event_date,
  device_type,
  country,
  event_type
