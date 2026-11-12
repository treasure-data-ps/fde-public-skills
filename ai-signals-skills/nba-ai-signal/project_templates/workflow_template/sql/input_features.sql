-- Model input table, written to ${train_input_table} (mode = train) or ${pred_input_table}
-- (mode = pred) by data_prep.dig.
-- EXAMPLE STRUCTURE — replace every <...> placeholder with the customer's tables and
-- columns before the first run (sql/README.md). Keep the output contract:
--   session_id            the Workflow session (in exclude_columns)
--   ${user_column}        train: one row per logged action; pred: exactly one row per customer
--   ${action_column}      the action label (VARCHAR); NULL when scoring
--   ${reward_column}      numeric outcome of the action in [action time, + reward_window_days); NULL when scoring
--   ${timestamp_column}   UNIX seconds: the action time (train) or the run date (pred)
--   feature columns       NUMERIC context computed only from data BEFORE that time — same columns in both modes
-- Variables: mode, run_date, train_start, train_end, scan_start, scan_end (config.yml, data_prep.dig)

WITH bounds AS (
  SELECT TO_UNIXTIME(CAST(DATE '${run_date}' AS TIMESTAMP)) AS run_ts
),

anchors AS (
  -- train: every action logged in [train_start, train_end) — its reward window ends by the run date
  SELECT a.<id_col>                          AS ${user_column},
         CAST(a.<action_col> AS VARCHAR)     AS ${action_column},
         a.<action_time_col>                 AS anchor_ts
  FROM <source_database>.<action_log_table> a
  WHERE '${mode}' = 'train'
    AND TD_TIME_RANGE(a.<action_time_col>, '${train_start}', '${train_end}')
    AND a.<id_col> IS NOT NULL
    AND a.<action_col> IS NOT NULL
  UNION ALL
  -- pred: the customers to recommend for, once each, at the run date
  SELECT DISTINCT p.<id_col>, CAST(NULL AS VARCHAR), b.run_ts
  FROM <source_database>.<profile_table> p
  CROSS JOIN bounds b
  WHERE '${mode}' = 'pred'
    AND p.<id_col> IS NOT NULL
),

anchors_n AS (
  -- anchor_id tells repeated actions of the same user apart in the joins below
  SELECT *, ROW_NUMBER() OVER (PARTITION BY ${user_column} ORDER BY anchor_ts, ${action_column}) AS anchor_id
  FROM anchors
),

activity_features AS (
  -- Behavior in [anchor_ts - feature_lookback_days, anchor_ts)
  SELECT an.${user_column}, an.anchor_id,
         COUNT(*)                                                         AS events_cnt,
         COUNT_IF(e.<event_time_col> >= an.anchor_ts - 30 * 86400)        AS events_30d,
         COUNT(DISTINCT TD_TIME_FORMAT(e.<event_time_col>, 'yyyy-MM-dd')) AS active_days,
         (an.anchor_ts - MAX(e.<event_time_col>)) / 86400                 AS days_since_last_event
  FROM anchors_n an
  JOIN <source_database>.<activity_table> e
    ON e.<id_col> = an.${user_column}
   AND e.<event_time_col> >= an.anchor_ts - ${feature_lookback_days} * 86400
   AND e.<event_time_col> <  an.anchor_ts
  WHERE TD_TIME_RANGE(e.<event_time_col>, '${scan_start}', '${scan_end}')
  GROUP BY an.${user_column}, an.anchor_id, an.anchor_ts
),

prior_actions AS (
  -- Contact pressure: actions the customer received in the 30 days before
  SELECT an.${user_column}, an.anchor_id, COUNT(*) AS actions_30d
  FROM anchors_n an
  JOIN <source_database>.<action_log_table> a
    ON a.<id_col> = an.${user_column}
   AND a.<action_time_col> >= an.anchor_ts - 30 * 86400
   AND a.<action_time_col> <  an.anchor_ts
  WHERE TD_TIME_RANGE(a.<action_time_col>, '${scan_start}', '${scan_end}')
  GROUP BY an.${user_column}, an.anchor_id
),

reward AS (
  -- Outcome in [anchor_ts, anchor_ts + reward_window_days) — training only
  SELECT an.${user_column}, an.anchor_id, 1.0 AS ${reward_column}
  FROM anchors_n an
  JOIN <source_database>.<outcome_table> o
    ON o.<id_col> = an.${user_column}
   AND o.<outcome_time_col> >= an.anchor_ts
   AND o.<outcome_time_col> <  an.anchor_ts + ${reward_window_days} * 86400
  WHERE '${mode}' = 'train'
    AND TD_TIME_RANGE(o.<outcome_time_col>, '${train_start}', '${scan_end}')
  GROUP BY an.${user_column}, an.anchor_id
)

SELECT '${session_id}'                                  AS session_id,
       an.${user_column},
       an.${action_column},
       IF('${mode}' = 'train', COALESCE(r.${reward_column}, 0.0)) AS ${reward_column},
       CAST(an.anchor_ts AS BIGINT)                     AS ${timestamp_column},
       COALESCE(f.events_cnt, 0)                        AS events_cnt,
       COALESCE(f.events_30d, 0)                        AS events_30d,
       COALESCE(f.active_days, 0)                       AS active_days,
       f.days_since_last_event,
       COALESCE(pa.actions_30d, 0)                      AS actions_30d
FROM anchors_n an
LEFT JOIN activity_features f ON f.${user_column} = an.${user_column} AND f.anchor_id = an.anchor_id
LEFT JOIN prior_actions pa    ON pa.${user_column} = an.${user_column} AND pa.anchor_id = an.anchor_id
LEFT JOIN reward r            ON r.${user_column} = an.${user_column} AND r.anchor_id = an.anchor_id
