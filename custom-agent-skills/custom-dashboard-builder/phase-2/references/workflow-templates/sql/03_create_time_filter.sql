-- Create / refresh time dimension table for Treasure Data dashboard filtering
-- Skill: sql-skills:trino | sql-skills:time-filtering
--
-- OPTIONAL / REFERENCE-ONLY: not wired into the default .dig files (see deploy-workflow-guide.md
-- "Workflow File Naming" section). Wire it in only if your dashboard needs a shared date-dimension
-- table to join all SINK tables against.
--
-- FIRST RUN: Creates the table with the full history window.
-- INCREMENTAL: INSERT INTO appends only the new date row for yesterday.
-- The dashboard joins all SINK tables to this table on event_date.
-- Never drop and recreate — always INSERT INTO to preserve history.

INSERT INTO ${sink_database}.${project_prefix}_global_time_filter
SELECT DISTINCT
  event_date,
  CAST(YEAR(event_date)               AS BIGINT)              AS year,
  CAST(MONTH(event_date)              AS BIGINT)              AS month,
  CAST(DAY(event_date)                AS BIGINT)              AS day,
  CAST(WEEK(event_date)               AS BIGINT)              AS week,
  DATE_FORMAT(event_date, '%Y-%m')                            AS month_str,
  DATE_FORMAT(event_date, '%Y')                               AS year_str
FROM
  ${sink_database}.${project_prefix}_events_prep
WHERE
  -- Only insert yesterday's new date (incremental)
  td_time_range(event_time,
    TD_TIME_ADD(TD_SCHEDULED_TIME(), '-1d', 'UTC'),
    TD_SCHEDULED_TIME(), 'UTC')
  -- Deduplicate: skip if this date already exists in the time filter table
  AND event_date NOT IN (
    SELECT DISTINCT event_date
    FROM ${sink_database}.${project_prefix}_global_time_filter
  )
ORDER BY event_date DESC
