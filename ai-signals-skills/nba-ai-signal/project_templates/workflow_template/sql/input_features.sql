-- Model input table, written to ${train_input_table} (mode = train) or ${pred_input_table}
-- (mode = pred) by data_prep.dig, from the sequential touchpoints in ${touchpoints_table}.
-- The action follows nba_type (config.yml):
--   channel   the touch's channel (email, paid_search, social, app, direct, ...)
--   time      the local time slot of the touch (time_grain: daypart | hour | dow_daypart)
--   campaign  the touch's campaign
--   custom    the touch's action_label (offer, treatment, content ...)
-- EXAMPLE STRUCTURE for the context features — keep the anchors, reward and output contract;
-- set the per-channel feature columns to the top channels from discovery (sql/README.md):
--   session_id, ${user_column}, ${action_column}, ${reward_column}, ${timestamp_column}, features
-- Variables: mode, run_date, train_start, train_end, scan_start, scan_end, nba_type, time_grain,
-- local_timezone, action_sources, reward_window_days, reward_attribution, reward_type,
-- min_action_share, feature_lookback_days (config.yml, data_prep.dig)

WITH bounds AS (
  SELECT TO_UNIXTIME(CAST(DATE '${run_date}' AS TIMESTAMP))    AS run_ts,
         TO_UNIXTIME(CAST(DATE '${train_start}' AS TIMESTAMP)) AS train_start_ts,
         TO_UNIXTIME(CAST(DATE '${train_end}' AS TIMESTAMP))   AS train_end_ts
),

touches AS (
  -- Non-conversion touches with their local time slot
  SELECT t.*,
         HOUR(FROM_UNIXTIME(t.touch_ts, '${local_timezone}'))        AS local_hour,
         DAY_OF_WEEK(FROM_UNIXTIME(t.touch_ts, '${local_timezone}')) AS local_dow,
         CASE WHEN HOUR(FROM_UNIXTIME(t.touch_ts, '${local_timezone}')) BETWEEN 6 AND 11  THEN 'morning'
              WHEN HOUR(FROM_UNIXTIME(t.touch_ts, '${local_timezone}')) BETWEEN 12 AND 17 THEN 'afternoon'
              WHEN HOUR(FROM_UNIXTIME(t.touch_ts, '${local_timezone}')) BETWEEN 18 AND 23 THEN 'evening'
              ELSE 'overnight' END                                    AS daypart
  FROM ${touchpoints_table} t
  WHERE t.is_conversion = 0
),

conversions AS (
  SELECT ${user_column}, touch_ts, conversion_value FROM ${touchpoints_table} WHERE is_conversion = 1
),

decisions AS (
  -- Decision touches: every touch, or only those from action_sources; the next decision of the
  -- same customer bounds the reward window when reward_attribution = next_touch
  SELECT d.*,
         CASE '${nba_type}'
           WHEN 'channel'  THEN d.channel
           WHEN 'campaign' THEN d.campaign
           WHEN 'time'     THEN CASE '${time_grain}'
                                  WHEN 'hour'        THEN LPAD(CAST(d.local_hour AS VARCHAR), 2, '0') || 'h'
                                  WHEN 'dow_daypart' THEN ELEMENT_AT(ARRAY['mon','tue','wed','thu','fri','sat','sun'], d.local_dow) || '_' || d.daypart
                                  ELSE d.daypart END
           ELSE d.action_label
         END                                                            AS raw_action,
         LEAD(d.touch_ts) OVER (PARTITION BY d.${user_column} ORDER BY d.touch_ts) AS next_decision_ts
  FROM touches d
  WHERE '${action_sources}' = '' OR CONTAINS(SPLIT('${action_sources}', '|'), d.src_name)
),

train_decisions AS (
  SELECT d.* FROM decisions d CROSS JOIN bounds b
  WHERE '${mode}' = 'train' AND d.raw_action IS NOT NULL
    AND d.touch_ts >= b.train_start_ts AND d.touch_ts < b.train_end_ts
),

action_shares AS (
  -- Actions below min_action_share of the training rows are grouped as 'other' (not for time)
  SELECT raw_action, COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () AS share
  FROM train_decisions GROUP BY raw_action
),

anchors AS (
  -- train: one row per decision touch whose reward window ends by the run date
  SELECT d.${user_column},
         IF('${nba_type}' <> 'time' AND s.share < ${min_action_share}, 'other', d.raw_action) AS ${action_column},
         d.touch_ts AS anchor_ts,
         LEAST(d.touch_ts + ${reward_window_days} * 86400,
               IF('${reward_attribution}' = 'next_touch', COALESCE(d.next_decision_ts, 9999999999), 9999999999)) AS reward_end_ts
  FROM train_decisions d
  JOIN action_shares s ON s.raw_action = d.raw_action
  UNION ALL
  -- pred: every customer with a touch in the context window, once, at the run date
  SELECT DISTINCT t.${user_column}, CAST(NULL AS VARCHAR), b.run_ts, b.run_ts
  FROM touches t CROSS JOIN bounds b
  WHERE '${mode}' = 'pred'
    AND t.touch_ts >= b.run_ts - ${feature_lookback_days} * 86400 AND t.touch_ts < b.run_ts
),

anchors_n AS (
  -- anchor_id tells repeated decisions of the same customer apart in the joins below
  SELECT *, ROW_NUMBER() OVER (PARTITION BY ${user_column} ORDER BY anchor_ts, ${action_column}) AS anchor_id
  FROM anchors
),

touch_features AS (
  -- Touch history in [anchor_ts - feature_lookback_days, anchor_ts)
  SELECT an.${user_column}, an.anchor_id,
         COUNT(*)                                                     AS touches_cnt,
         COUNT_IF(t.touch_ts >= an.anchor_ts - 30 * 86400)            AS touches_30d,
         COUNT(DISTINCT TD_TIME_FORMAT(t.touch_ts, 'yyyy-MM-dd'))     AS active_days,
         COUNT(DISTINCT t.channel)                                    AS distinct_channels,
         (an.anchor_ts - MAX(t.touch_ts)) / 86400                     AS days_since_last_touch,
         -- per-channel counts: one column per top channel from discovery (names must be literal)
         COUNT_IF(t.channel = 'email')                                AS touches_email,
         COUNT_IF(t.channel = 'paid_search')                          AS touches_paid_search,
         COUNT_IF(t.channel = 'social')                               AS touches_social,
         COUNT_IF(t.channel = 'direct')                               AS touches_direct,
         COUNT_IF(t.channel = 'app')                                  AS touches_app,
         -- time-of-day profile (shares of touches per daypart)
         AVG(IF(t.daypart = 'morning', 1.0, 0.0))                     AS share_morning,
         AVG(IF(t.daypart = 'afternoon', 1.0, 0.0))                   AS share_afternoon,
         AVG(IF(t.daypart = 'evening', 1.0, 0.0))                     AS share_evening,
         AVG(IF(t.local_dow IN (6, 7), 1.0, 0.0))                     AS share_weekend
  FROM anchors_n an
  JOIN touches t
    ON t.${user_column} = an.${user_column}
   AND t.touch_ts >= an.anchor_ts - ${feature_lookback_days} * 86400
   AND t.touch_ts <  an.anchor_ts
  GROUP BY an.${user_column}, an.anchor_id, an.anchor_ts
),

conversion_features AS (
  -- Conversion history in the same window
  SELECT an.${user_column}, an.anchor_id,
         COUNT(*)                                       AS conversions_cnt,
         SUM(COALESCE(c.conversion_value, 0))           AS conversion_value_sum,
         (an.anchor_ts - MAX(c.touch_ts)) / 86400       AS days_since_last_conversion
  FROM anchors_n an
  JOIN conversions c
    ON c.${user_column} = an.${user_column}
   AND c.touch_ts >= an.anchor_ts - ${feature_lookback_days} * 86400
   AND c.touch_ts <  an.anchor_ts
  GROUP BY an.${user_column}, an.anchor_id, an.anchor_ts
),

prior_decisions AS (
  -- Contact pressure: decision touches the customer had in the 30 days before
  SELECT an.${user_column}, an.anchor_id, COUNT(*) AS decisions_30d
  FROM anchors_n an
  JOIN decisions d
    ON d.${user_column} = an.${user_column}
   AND d.touch_ts >= an.anchor_ts - 30 * 86400
   AND d.touch_ts <  an.anchor_ts
  GROUP BY an.${user_column}, an.anchor_id
),

reward AS (
  -- Outcome in [anchor_ts, reward_end_ts): 1 if the customer converted (reward_type = binary)
  -- or the converted value (reward_type = value) — training only
  SELECT an.${user_column}, an.anchor_id,
         IF('${reward_type}' = 'value', SUM(COALESCE(c.conversion_value, 0)), 1.0) AS ${reward_column}
  FROM anchors_n an
  JOIN conversions c
    ON c.${user_column} = an.${user_column}
   AND c.touch_ts >= an.anchor_ts
   AND c.touch_ts <  an.reward_end_ts
  WHERE '${mode}' = 'train'
  GROUP BY an.${user_column}, an.anchor_id
)

SELECT '${session_id}'                                             AS session_id,
       an.${user_column},
       an.${action_column},
       IF('${mode}' = 'train', COALESCE(r.${reward_column}, 0.0))  AS ${reward_column},
       CAST(an.anchor_ts AS BIGINT)                                AS ${timestamp_column},
       COALESCE(f.touches_cnt, 0)                                  AS touches_cnt,
       COALESCE(f.touches_30d, 0)                                  AS touches_30d,
       COALESCE(f.active_days, 0)                                  AS active_days,
       COALESCE(f.distinct_channels, 0)                            AS distinct_channels,
       f.days_since_last_touch,
       COALESCE(f.touches_email, 0)                                AS touches_email,
       COALESCE(f.touches_paid_search, 0)                          AS touches_paid_search,
       COALESCE(f.touches_social, 0)                               AS touches_social,
       COALESCE(f.touches_direct, 0)                               AS touches_direct,
       COALESCE(f.touches_app, 0)                                  AS touches_app,
       f.share_morning, f.share_afternoon, f.share_evening, f.share_weekend,
       COALESCE(cf.conversions_cnt, 0)                             AS conversions_cnt,
       COALESCE(cf.conversion_value_sum, 0)                        AS conversion_value_sum,
       cf.days_since_last_conversion,
       COALESCE(pd.decisions_30d, 0)                               AS decisions_30d
FROM anchors_n an
LEFT JOIN touch_features f       ON f.${user_column} = an.${user_column}  AND f.anchor_id = an.anchor_id
LEFT JOIN conversion_features cf ON cf.${user_column} = an.${user_column} AND cf.anchor_id = an.anchor_id
LEFT JOIN prior_decisions pd     ON pd.${user_column} = an.${user_column} AND pd.anchor_id = an.anchor_id
LEFT JOIN reward r               ON r.${user_column} = an.${user_column}  AND r.anchor_id = an.anchor_id
