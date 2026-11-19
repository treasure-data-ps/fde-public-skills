-- Sequential touchpoints, written to ${touchpoints_table} by data_prep.dig (both modes).
-- FIXED LOGIC — reads ${touchpoints_table}_raw (sql/touchpoints_union.sql). Edit only the
-- channel rules below, to map customer-specific UTM values (sql/README.md):
--   1. channel per event: channel_hint → UTM medium / source → external referrer host
--   2. events without a signal inherit the latest signal of their source session (internal
--      pageviews keep the landing page's channel); a session without any signal → 'direct'
--   3. all sources ordered by time per customer; consecutive events in the same channel within
--      session_gap_minutes collapse into one touch; a channel change or a longer gap starts a new one
--   4. conversions are kept as their own rows (is_conversion = 1) and never merged into touches
-- Output: one row per touch or conversion — ${user_column}, touch_ts, touch_end_ts, channel,
-- campaign, action_label, src_name, event_type, events_in_touch, is_conversion, conversion_value

WITH raw AS (
  SELECT r.*,
         REGEXP_REPLACE(LOWER(TRY(url_extract_host(r.url))), '^www\.', '')      AS url_host,
         REGEXP_REPLACE(LOWER(TRY(url_extract_host(r.referrer))), '^www\.', '') AS ref_host
  FROM ${touchpoints_table}_raw r
  WHERE r.${user_column} IS NOT NULL AND r.event_ts IS NOT NULL
),

src_sessions AS (
  -- Sessions per customer and source: a gap above session_gap_minutes starts a new one
  SELECT raw.*,
         IF(COALESCE(event_ts - LAG(event_ts) OVER (PARTITION BY ${user_column}, src_name ORDER BY event_ts),
                     ${session_gap_minutes} * 60 + 1) > ${session_gap_minutes} * 60, 1, 0) AS session_start
  FROM raw
  WHERE is_conversion = 0
),

signals AS (
  SELECT s.*,
         SUM(session_start) OVER (PARTITION BY ${user_column}, src_name ORDER BY event_ts
                                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS src_session,
         COALESCE(
           NULLIF(LOWER(TRIM(channel_hint)), ''),
           -- UTM / traffic-source rules — extend with the customer's own medium and source values
           CASE
             WHEN COALESCE(utm_medium, utm_source) IS NULL THEN NULL
             WHEN REGEXP_LIKE(COALESCE(utm_medium, ''), 'e-?mail|newsletter|crm')
               OR REGEXP_LIKE(COALESCE(utm_source, ''), 'sfmc|braze|klaviyo|mailchimp|sendgrid|newsletter') THEN 'email'
             WHEN REGEXP_LIKE(COALESCE(utm_medium, ''), '^sms$|text') THEN 'sms'
             WHEN REGEXP_LIKE(COALESCE(utm_medium, ''), 'push|notification') THEN 'push'
             WHEN REGEXP_LIKE(COALESCE(utm_medium, ''), 'affiliate|partner') THEN 'affiliate'
             WHEN REGEXP_LIKE(COALESCE(utm_medium, '') || ' ' || COALESCE(utm_source, ''), 'facebook|instagram|meta|tiktok|linkedin|twitter|pinterest|snapchat|youtube|social|reddit')
               THEN IF(REGEXP_LIKE(COALESCE(utm_medium, ''), 'cpc|ppc|cpm|paid'), 'paid_social', 'social')
             WHEN REGEXP_LIKE(COALESCE(utm_medium, ''), 'cpc|ppc|paid_?search|sem|paidsearch') THEN 'paid_search'
             WHEN REGEXP_LIKE(COALESCE(utm_medium, ''), 'display|banner|cpm|programmatic|dsp|rtb|video') THEN 'display'
             WHEN REGEXP_LIKE(COALESCE(utm_medium, ''), 'referral') THEN 'referral'
             WHEN REGEXP_LIKE(COALESCE(utm_medium, ''), 'organic') THEN 'organic_search'
             WHEN utm_medium IS NOT NULL THEN REGEXP_REPLACE(utm_medium, '[^a-z0-9]+', '_')
             ELSE REGEXP_REPLACE(utm_source, '[^a-z0-9]+', '_')
           END,
           -- An external referrer (a new entry to the site); a self-referral (internal navigation) is no signal
           IF(ref_host IS NOT NULL AND ref_host <> COALESCE(url_host, ''),
              CASE
                -- webmail before search: mail.google.com is an email click, not a search
                WHEN REGEXP_LIKE(ref_host, '(^|\.)(mail\.|outlook\.|gmail)') THEN 'email'
                WHEN REGEXP_LIKE(ref_host, '(^|\.)(google|bing|yahoo|duckduckgo|baidu|yandex|ecosia|naver)\.') THEN 'organic_search'
                WHEN REGEXP_LIKE(ref_host, '(^|\.)(facebook|instagram|t\.co|twitter|x\.com|linkedin|pinterest|tiktok|youtube|reddit|snapchat)') THEN 'social'
                ELSE 'referral'
              END)
         ) AS channel_signal
  FROM src_sessions s
),

events AS (
  -- Every event takes the latest channel signal of its source session (the landing page's UTM
  -- or referrer for web); a session without any signal is 'direct'
  SELECT ${user_column}, event_ts, src_name, event_type, campaign, action_label,
         COALESCE(LAST_VALUE(channel_signal) IGNORE NULLS OVER (
                    PARTITION BY ${user_column}, src_name, src_session ORDER BY event_ts
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 'direct') AS channel
  FROM signals
),

sequenced AS (
  -- All sources in time order: a new touch starts on a channel change or a gap above session_gap_minutes
  SELECT e.*,
         IF(LAG(channel) OVER (PARTITION BY ${user_column} ORDER BY event_ts, src_name) IS NULL
            OR LAG(channel) OVER (PARTITION BY ${user_column} ORDER BY event_ts, src_name) <> channel
            OR event_ts - LAG(event_ts) OVER (PARTITION BY ${user_column} ORDER BY event_ts, src_name) > ${session_gap_minutes} * 60,
            1, 0) AS new_touch
  FROM events e
),

numbered AS (
  SELECT sequenced.*,
         SUM(new_touch) OVER (PARTITION BY ${user_column} ORDER BY event_ts, src_name
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS touch_seq
  FROM sequenced
)

SELECT ${user_column},
       MIN(event_ts)                                                                AS touch_ts,
       MAX(event_ts)                                                                AS touch_end_ts,
       ARBITRARY(channel)                                                           AS channel,
       element_at(ARRAY_AGG(campaign ORDER BY event_ts) FILTER (WHERE campaign IS NOT NULL), 1)         AS campaign,
       element_at(ARRAY_AGG(action_label ORDER BY event_ts) FILTER (WHERE action_label IS NOT NULL), 1) AS action_label,
       element_at(ARRAY_AGG(src_name ORDER BY event_ts), 1)                         AS src_name,
       element_at(ARRAY_AGG(event_type ORDER BY event_ts), 1)                       AS event_type,
       COUNT(*)                                                                     AS events_in_touch,
       0                                                                            AS is_conversion,
       CAST(NULL AS DOUBLE)                                                         AS conversion_value
FROM numbered
GROUP BY ${user_column}, touch_seq

UNION ALL

SELECT ${user_column}, event_ts, event_ts, CAST(NULL AS VARCHAR), campaign, action_label, src_name, event_type,
       1, 1, conversion_value
FROM raw
WHERE is_conversion = 1
