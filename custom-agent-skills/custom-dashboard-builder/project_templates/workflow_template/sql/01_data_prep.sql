-- Data Preparation: Clean and validate source data into a staging table
-- Skill: sql-skills:trino | sql-skills:time-filtering
--
-- STAGING TABLE — this task uses create_table: at the .dig level (see SLUG_data_prep.dig),
-- not INSERT INTO. events_prep only ever needs to hold the CURRENT run's window (the full
-- historical window on a 'full' run, or just the incremental lookback window on an
-- 'incremental' run) — downstream tasks (10/11/12) consume it within the same run and
-- do not need it to accumulate history itself. Using create_table: here means:
--   - First run ever: no "table doesn't exist" crash (a bare INSERT INTO would fail —
--     TD's engine does not auto-create the target table; verified: throws TABLE_NOT_FOUND).
--   - No duplicate-row risk from re-inserting the same days on every incremental run.
--
-- ⚠️ Branches directly on ${refresh_mode} (from input_params.yaml, exported globally) —
-- do NOT introduce a separate per-branch variable like "session_vars: data_window: full"
-- to signal which mode this run is in. session_vars is not a real digdag/td> parameter;
-- an earlier version of this template used it and every run failed at evaluation time
-- with "ReferenceError: data_window is not defined" — session_vars is silently ignored
-- by the td> operator, so the variable was simply never defined. refresh_mode is already
-- available here via the top-level _export in input_params.yaml; branch on it directly.
--
-- FULL MODE (refresh_mode='full'):
--   Loads the complete start_date → end_date historical window.
--   Run this on first deploy and after schema changes.
--
-- INCREMENTAL MODE (refresh_mode='incremental'):
--   Loads only the last incremental_look_back_days to cover late-arriving/corrected data.
--
-- td_time_range() prunes partitions at the storage layer — always faster
-- than a WHERE on a cast date column. Never remove it for production runs.
--
-- ⚠️ event_time is a VARCHAR, not a native TIMESTAMP. Two things were tried and both
-- failed on TD's engine: (1) td_time_string(..., 'yyyy-MM-dd HH:mm:ss', 'UTC') — that
-- 3-arg form with a Java-style format string errors ("yyy-MM-dd HH:mm:ss... is
-- malformed"); TD's td_time_string expects a strftime-style single-format 2-arg call
-- instead (see td-time-functions.md). (2) CAST(... AS TIMESTAMP) inside a create_table:
-- (CTAS) errors with "Column type: timestamp(3) not supported" — TD's table format does
-- not support TIMESTAMP as a materialized column type at any precision. DATE_FORMAT +
-- FROM_UNIXTIME produces an equivalent human-readable string TD's CTAS accepts natively.

SELECT
  DATE_FORMAT(FROM_UNIXTIME(TD_TIME_PARSE(timestamp, 'UTC')), '%Y-%m-%d %H:%i:%s') AS event_time,
  td_canonical_id                                                        AS user_id,
  event_type,
  CAST(event_value AS DOUBLE)                                           AS event_value,
  session_id,
  device_type,
  country,
  TD_DATE_TRUNC('day', TD_TIME_PARSE(timestamp, 'UTC'), 'UTC')          AS event_date
FROM
  ${source_database}.${source_table}
WHERE
  td_time_range(TD_TIME_PARSE(timestamp, 'UTC'),
    ${refresh_mode == 'full'
      ? "TD_TIME_PARSE('" + start_date + " 00:00:00', 'UTC'), TD_TIME_PARSE('" + end_date + " 23:59:59', 'UTC')"
      : "TD_TIME_ADD(TD_SCHEDULED_TIME(), '-" + incremental_look_back_days + "d', 'UTC'), TD_SCHEDULED_TIME()"},
    'UTC')
  AND td_canonical_id IS NOT NULL
  AND timestamp IS NOT NULL
  ${table_filter != "" ? "AND " + table_filter : ""}
