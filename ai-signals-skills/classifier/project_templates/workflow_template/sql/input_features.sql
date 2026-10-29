-- Model input table: one row per entity and cutoff_date, written to ${train_input_table}
-- (mode = train) or ${pred_input_table} (mode = pred) by data_prep.dig.
-- EXAMPLE STRUCTURE — replace every <...> placeholder with the customer's tables and
-- columns before the first run (sql/README.md). Keep the output contract:
--   session_id          the Workflow session; train.dig trains on MAX(session_id)
--   cutoff_date         the snapshot date (in columns_to_drop)
--   ${user_id_column}   one row per entity per cutoff, never NULL
--   ${target_column}    0/1 label observed in [cutoff, cutoff + label_window_days) — always 0 when scoring
--   feature columns     computed only from data BEFORE the cutoff (no leakage)
-- Variables from data_prep.dig: mode, run_date, snapshot_k_min, snapshot_k_max, scan_start, scan_end

WITH cutoffs AS (
  -- One row per snapshot; unix bounds keep the joins below simple range comparisons
  SELECT CAST(c AS VARCHAR)                                                        AS cutoff_date,
         c                                                                         AS cutoff_dt,
         TO_UNIXTIME(CAST(DATE_ADD('day', -${feature_lookback_days}, c) AS TIMESTAMP)) AS feature_start_ts,
         TO_UNIXTIME(CAST(c AS TIMESTAMP))                                         AS cutoff_ts,
         TO_UNIXTIME(CAST(DATE_ADD('day', ${label_window_days}, c) AS TIMESTAMP))  AS label_end_ts
  FROM UNNEST(SEQUENCE(${snapshot_k_min}, ${snapshot_k_max})) AS t(k)
  CROSS JOIN UNNEST(ARRAY[DATE_ADD('day', -${spacing_days} * k, DATE '${run_date}')]) AS d(c)
),

population AS (
  -- Entities eligible at each cutoff: e.g. profiles created before it, open leads,
  -- active subscribers, customers active in the window (dataprep-guide.md §4)
  SELECT c.cutoff_date, c.cutoff_dt, c.feature_start_ts, c.cutoff_ts, c.label_end_ts,
         p.<id_col> AS ${user_id_column}
  FROM cutoffs c
  JOIN <source_database>.<profile_table> p
    ON p.<created_time_col> < c.cutoff_ts
  WHERE p.<id_col> IS NOT NULL
),

activity_features AS (
  -- Behavior in the feature window [feature_start_ts, cutoff_ts) of each cutoff
  SELECT c.cutoff_date,
         e.<id_col>                                                              AS ${user_id_column},
         COUNT(*)                                                                AS events_cnt,
         COUNT_IF(e.<event_time_col> >= c.cutoff_ts - 30 * 86400)                AS events_30d,
         COUNT(DISTINCT TD_TIME_FORMAT(e.<event_time_col>, 'yyyy-MM-dd'))        AS active_days,
         DATE_DIFF('day', DATE(FROM_UNIXTIME(MAX(e.<event_time_col>))), c.cutoff_dt) AS days_since_last_event
  FROM cutoffs c
  JOIN <source_database>.<activity_table> e
    ON e.<event_time_col> >= c.feature_start_ts
   AND e.<event_time_col> <  c.cutoff_ts
  WHERE TD_TIME_RANGE(e.<event_time_col>, '${scan_start}', '${scan_end}')
  GROUP BY c.cutoff_date, c.cutoff_dt, c.cutoff_ts, e.<id_col>
),

label AS (
  -- Outcome in the label window [cutoff_ts, label_end_ts) of each cutoff
  SELECT DISTINCT c.cutoff_date, o.<id_col> AS ${user_id_column}, 1 AS ${target_column}
  FROM cutoffs c
  JOIN <source_database>.<outcome_table> o
    ON o.<outcome_time_col> >= c.cutoff_ts
   AND o.<outcome_time_col> <  c.label_end_ts
  WHERE TD_TIME_RANGE(o.<outcome_time_col>, '${scan_start}', '${scan_end}')
)

SELECT '${session_id}'                                 AS session_id,
       p.cutoff_date,
       p.${user_id_column},
       COALESCE(a.events_cnt, 0)                        AS events_cnt,
       COALESCE(a.events_30d, 0)                        AS events_30d,
       COALESCE(a.active_days, 0)                       AS active_days,
       a.days_since_last_event,
       CAST(COALESCE(l.${target_column}, 0) AS BIGINT)  AS ${target_column}
FROM population p
LEFT JOIN activity_features a ON a.${user_id_column} = p.${user_id_column} AND a.cutoff_date = p.cutoff_date
LEFT JOIN label l             ON l.${user_id_column} = p.${user_id_column} AND l.cutoff_date = p.cutoff_date
