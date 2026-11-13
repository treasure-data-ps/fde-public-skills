-- Touchpoint union, written to ${touchpoints_table}_raw by data_prep.dig (both modes).
-- EXAMPLE STRUCTURE — one UNION ALL block per source table found in Phase 1; replace every
-- <...> placeholder and delete the blocks that don't apply (sql/README.md). Every block
-- returns exactly these columns, in this order:
--   ${user_column}     customer ID (same ID in every block — join through a lookup table if not)
--   event_ts           UNIX seconds BIGINT of the event
--   src_name           short source label ('web', 'email', 'app', 'orders', ...) — used by action_sources
--   event_type         what happened ('pageview', 'email_open', 'app_session', 'order', ...)
--   url, referrer      page URL and referrer (web only, else NULL)
--   utm_medium, utm_source, utm_campaign   extracted UTM / traffic-source values (else NULL)
--   channel_hint       the channel when the source itself is one ('email', 'app', 'sms', ...); NULL for web
--   campaign           campaign / content name of the touch (utm_campaign, email campaign, ...) or NULL
--   action_label       label for nba_type = custom (offer, treatment, content ...) or NULL
--   is_conversion      1 for conversion events (orders, sign-ups) — they become the reward, never an action
--   conversion_value   value of a conversion (order total) or NULL
-- Variables: scan_start, scan_end (data_prep.dig)

-- Web: channel comes from UTM parameters on the landing URL (fallback: the referrer URL),
-- or an explicit traffic-source column; sessions without either are classified from the
-- referrer host in touchpoints.sql
SELECT w.<id_col>                                                   AS ${user_column},
       CAST(w.<event_time_col> AS BIGINT)                           AS event_ts,
       'web'                                                        AS src_name,
       'pageview'                                                   AS event_type,
       w.<url_col>                                                  AS url,
       w.<referrer_col>                                             AS referrer,
       LOWER(TRIM(COALESCE(TRY(url_extract_parameter(w.<url_col>, 'utm_medium')),
                           TRY(url_extract_parameter(w.<referrer_col>, 'utm_medium')))))   AS utm_medium,
       LOWER(TRIM(COALESCE(TRY(url_extract_parameter(w.<url_col>, 'utm_source')),
                           TRY(url_extract_parameter(w.<referrer_col>, 'utm_source')))))   AS utm_source,
       LOWER(TRIM(COALESCE(TRY(url_extract_parameter(w.<url_col>, 'utm_campaign')),
                           TRY(url_extract_parameter(w.<referrer_col>, 'utm_campaign'))))) AS utm_campaign,
       CAST(NULL AS VARCHAR)                                        AS channel_hint,
       LOWER(TRIM(TRY(url_extract_parameter(w.<url_col>, 'utm_campaign'))))              AS campaign,
       CAST(NULL AS VARCHAR)                                        AS action_label,
       0                                                            AS is_conversion,
       CAST(NULL AS DOUBLE)                                         AS conversion_value
FROM <source_database>.<pageview_table> w
WHERE TD_TIME_RANGE(w.<event_time_col>, '${scan_start}', '${scan_end}')
  AND w.<id_col> IS NOT NULL

UNION ALL
-- Email: customer engagement (opens, clicks) — or sends, when the decision is what to send
SELECT e.<id_col>, CAST(e.<event_time_col> AS BIGINT), 'email', LOWER(e.<event_type_col>),
       CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
       'email', LOWER(e.<esp_col>), LOWER(e.<campaign_col>),
       'email', LOWER(e.<campaign_col>), CAST(NULL AS VARCHAR),
       0, CAST(NULL AS DOUBLE)
FROM <source_database>.<email_events_table> e
WHERE TD_TIME_RANGE(e.<event_time_col>, '${scan_start}', '${scan_end}')
  AND e.<id_col> IS NOT NULL
  AND LOWER(e.<event_type_col>) IN ('<open>', '<click>')

UNION ALL
-- Email sends: the business decisions for nba_type time / campaign (action_sources: 'email_send');
-- delete this block for channel decisions. A send and the opens / clicks after it share the
-- email channel, so they collapse into one touch whose src_name is email_send
SELECT s.<id_col>, CAST(s.<send_time_col> AS BIGINT), 'email_send', 'email_send',
       CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
       'email', LOWER(s.<esp_col>), LOWER(s.<campaign_col>),
       'email', LOWER(s.<campaign_col>), CAST(NULL AS VARCHAR),
       0, CAST(NULL AS DOUBLE)
FROM <source_database>.<email_sends_table> s
WHERE TD_TIME_RANGE(s.<send_time_col>, '${scan_start}', '${scan_end}')
  AND s.<id_col> IS NOT NULL

UNION ALL
-- App: sessions or in-app events; push opens could be a separate block with channel_hint 'push'
SELECT a.<id_col>, CAST(a.<event_time_col> AS BIGINT), 'app', LOWER(a.<event_name_col>),
       CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
       CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
       'app', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
       0, CAST(NULL AS DOUBLE)
FROM <source_database>.<app_events_table> a
WHERE TD_TIME_RANGE(a.<event_time_col>, '${scan_start}', '${scan_end}')
  AND a.<id_col> IS NOT NULL

UNION ALL
-- Conversions: one row per order / sign-up; is_conversion = 1, the value feeds reward_type = value
SELECT o.<id_col>, CAST(o.<order_time_col> AS BIGINT), 'orders', 'order',
       CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
       CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
       CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
       1, CAST(o.<order_amount_col> AS DOUBLE)
FROM <source_database>.<orders_table> o
WHERE TD_TIME_RANGE(o.<order_time_col>, '${scan_start}', '${scan_end}')
  AND o.<id_col> IS NOT NULL
  AND o.<status_col> NOT IN ('<cancelled>', '<refunded>')
