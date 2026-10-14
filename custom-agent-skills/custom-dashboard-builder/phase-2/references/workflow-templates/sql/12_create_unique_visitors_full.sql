-- Create unique visitor metrics by date (FULL MODE)
-- Skill: sql-skills:trino | sql-skills:trino-optimizer
--
-- Used only when refresh_mode == 'full'. Paired with create_table: in the .dig file.
--
-- Use APPROX_DISTINCT instead of COUNT(DISTINCT) for columns with high
-- cardinality — 2% error margin is acceptable for dashboard display.
-- Remove this file (both variants) and its .dig tasks if visitor-level metrics are
-- not in scope for this engagement.

SELECT
  event_date,
  -- APPROX_DISTINCT is 20–50x faster than COUNT(DISTINCT) for large cardinality
  APPROX_DISTINCT(user_id)        AS unique_visitors,
  COUNT(*)                        AS total_events_all_users
FROM
  ${sink_database}.${project_prefix}_events_prep
GROUP BY
  event_date
ORDER BY
  event_date
