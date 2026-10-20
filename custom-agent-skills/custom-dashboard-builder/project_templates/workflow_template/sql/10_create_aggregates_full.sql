-- Create aggregated KPI metrics table (FULL MODE)
-- Skill: sql-skills:trino | sql-skills:trino-optimizer
--
-- Used only when refresh_mode == 'full' (first deploy / full backfill / after schema changes).
-- Paired with create_table: in the .dig file — atomically replaces the entire SINK table
-- with the full start_date → end_date historical window.
--
-- To JOIN a dimension table, add a LEFT JOIN below and COALESCE null dimension values.
-- Example from a validated engagement:
--   LEFT JOIN ${source_database}.master_customers c ON t.${main_id_key} = c.${main_id_key}
--   , COALESCE(c.customer_segment, 'Unknown') AS customer_segment
--
-- Customize the SELECT list to match Phase 2 confirmed metrics (Step 2c).
-- Add/remove metric columns; keep event_date and user_id as grain keys.

SELECT
  event_date,
  user_id,
  COUNT(*)                                                    AS total_events,
  COUNT(DISTINCT session_id)                                  AS sessions,
  COUNT(CASE WHEN event_type = 'conversion' THEN 1 END)       AS conversions,
  COALESCE(SUM(event_value), 0)                               AS total_value,
  -- approx_distinct is 20–50x faster than COUNT(DISTINCT) on large tables
  -- Use for high-cardinality columns (user_id, session_id)
  APPROX_DISTINCT(session_id)                                 AS approx_sessions,
  MAX(device_type)                                            AS last_device
FROM
  ${sink_database}.${project_prefix}_events_prep
GROUP BY
  event_date,
  user_id
