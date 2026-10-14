-- Data Quality Validation
-- Skill: sql-skills:trino
--
-- Runs after 01_data_prep.sql to confirm the just-prepared events_prep staging table
-- produced sane results. This is a SELECT-only query — the workflow reads its output
-- via tdx wf attempt logs. Fails loudly if critical thresholds are breached.
--
-- ⚠️ No WHERE/td_time_range() filter here on purpose. 01_data_prep.sql (Section 1 of
-- SLUG_data_prep.dig) already scoped events_prep to exactly this run's window (full
-- start_date→end_date, or the incremental_look_back_days window) via create_table: —
-- re-filtering here to a hardcoded "yesterday" window is both redundant and wrong on a
-- 'full' run (it would validate almost none of the just-loaded historical data).
--
-- ⚠️ event_date is a BIGINT epoch (from TD_DATE_TRUNC in 01_data_prep.sql), not a DATE.
-- Comparing it to a CAST(... AS DATE) literal fails with a TYPE_MISMATCH error — compare
-- against another epoch value instead (TD_TIME_ADD / TD_SCHEDULED_TIME(), both bigint).
-- Similarly, event_time is a VARCHAR (see 01_data_prep.sql) — if you add a td_time_range()
-- filter elsewhere, wrap it in TD_TIME_PARSE(event_time, 'UTC') first; td_time_range()
-- requires a bigint epoch argument, not a formatted string.
--
-- Extend with additional assertions specific to your Phase 2 confirmed metrics.

SELECT
  COUNT(*)                                                    AS total_records,
  COUNT(DISTINCT user_id)                                     AS unique_users,
  MIN(event_date)                                             AS earliest_date,
  MAX(event_date)                                             AS latest_date,
  COUNT(CASE WHEN user_id    IS NULL THEN 1 END)              AS null_user_ids,
  COUNT(CASE WHEN event_date IS NULL THEN 1 END)              AS null_dates,
  COUNT(CASE WHEN event_value < 0    THEN 1 END)              AS negative_values,
  -- Freshness check: latest row should be within the last 2 days (only meaningful on
  -- incremental runs — on a 'full' historical backfill this will correctly report STALE
  -- for any window that doesn't reach up to the present; that is expected, not an error)
  CASE
    WHEN MAX(event_date) < TD_TIME_ADD(TD_SCHEDULED_TIME(), '-2d', 'UTC')
    THEN 'STALE — check source pipeline (or expected: this is a historical full-load run)'
    ELSE 'OK'
  END                                                         AS freshness_status
FROM
  ${sink_database}.${project_prefix}_events_prep
