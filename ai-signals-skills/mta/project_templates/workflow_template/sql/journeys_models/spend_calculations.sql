WITH
-- ============================================================
-- STEP 1: Standardize MTA source → std_source to match spend final_marketing_layer
-- ============================================================
mta_standardized AS (
    SELECT
        attribution_type,
        conversion_month,
        -- Map MTA channel 'other' to match spend mta_marketing_channel 'display'
        CASE WHEN channel = 'other' THEN 'display' ELSE channel END AS channel,
        source,
        total_conversions,
        total_conv_attr_perc,
        total_sales,
        total_booked,
        total_approved,

        CASE
            -- ── Affiliates ──
            WHEN channel = 'affiliates' AND source = 'affiliates other'  THEN 'Affiliates Other'
            WHEN channel = 'affiliates' AND source = 'borrowell'         THEN 'Borrowell'
            WHEN channel = 'affiliates' AND source = 'clearscore'        THEN 'ClearScore'
            WHEN channel = 'affiliates' AND source = 'creditkarma'       THEN 'Credit Karma'
            WHEN channel = 'affiliates' AND source = 'fig'               THEN 'Fig'
            WHEN channel = 'affiliates' AND source = 'loanconnect'       THEN 'LoanConnect'
            WHEN channel = 'affiliates'                                  THEN 'Affiliates Other'

            -- ── Direct Mail ──
            WHEN channel = 'direct_mail' AND source = 'pbs - mail'       THEN 'PBS Mail'
            WHEN channel = 'direct_mail' AND source IN ('customer_mail','costomer_mail',
                'prospect_mail','propsect_mail','prosp','direct_mail',
                'merchandise','magnet')                                  THEN 'PBS Mail'
            WHEN channel = 'direct_mail'                                 THEN 'PBS Mail'

            -- ── Direct Mail Call (single rolled-up bucket) ──
            WHEN channel = 'direct_mail_call'                            THEN 'Mail Call'

            -- ── Email: explicit CBS/PBS sources ──
            WHEN channel = 'email' AND source = 'cbs - fb email'        THEN 'CBS FB Email'
            WHEN channel = 'email' AND source = 'cbs - pb email'        THEN 'CBS PB Email'
            WHEN channel = 'email' AND source = 'cbs - sf email'        THEN 'CBS SF Email'
            WHEN channel = 'email' AND source = 'pbs - email'           THEN 'PBS Email'
            -- Email: email_medium campaign strings
            WHEN channel = 'email' AND REGEXP_LIKE(source, '_fb_|paramail_fb')                      THEN 'CBS FB Email'
            WHEN channel = 'email' AND REGEXP_LIKE(source, '_pb_|paramail_pb')                      THEN 'CBS PB Email'
            WHEN channel = 'email' AND REGEXP_LIKE(source, '_sf_')                                  THEN 'CBS SF Email'
            WHEN channel = 'email' AND REGEXP_LIKE(source, 'paramail_rpos|paramail_20|copy of email') THEN 'PBS Email'
            WHEN channel = 'email' AND REGEXP_LIKE(source, '_iql_|_mep|_cbs_newsletter|_fig_cross') THEN 'Email'
            -- Email: everything else (braze, sfmc, newsletter, misc)
            WHEN channel = 'email'                                       THEN 'Email'

            -- ── Paid Search ──
            WHEN channel = 'paid_search' AND source = 'branded'          THEN 'Branded'
            WHEN channel = 'paid_search' AND source = 'generic'          THEN 'Generic'
            WHEN channel = 'paid_search'                                 THEN 'Paid Search'

            -- ── Social ──
            WHEN channel = 'social' AND REGEXP_LIKE(source, 'facebook|fb') THEN 'Facebook'
            WHEN channel = 'social' AND source = 'instagram'             THEN 'Instagram'
            WHEN channel = 'social'                                      THEN 'Facebook'

            -- ── Organic ──
            WHEN channel = 'organic'                                     THEN 'Organic'

            -- ── Direct / Other / Roam → display bucket ──
            WHEN channel = 'direct'                                      THEN 'Other Digital'
            WHEN channel IN ('other','roam')                             THEN 'All Other'

            ELSE 'All Other'
        END AS std_source

    FROM mta_models_standard
),

-- ============================================================
-- STEP 2: Aggregate MTA at channel + std_source grain
-- ============================================================
mta_agg AS (
    SELECT
        attribution_type,
        conversion_month,
        channel,
        std_source,
        SUM(total_conversions)  AS total_conversions,
        SUM(total_sales)        AS total_sales,
        SUM(total_booked)       AS total_booked,
        SUM(total_approved)     AS total_approved
    FROM mta_standardized
    GROUP BY attribution_type, conversion_month, channel, std_source
),

-- ============================================================
-- STEP 3: Roll up spend — aggregate Mail Call rows together
-- ============================================================
spend_agg AS (
    SELECT
        CAST(year AS VARCHAR) || '-' || LPAD(CAST(month AS VARCHAR), 2, '0') AS conversion_month,
        mta_marketing_channel,
        CASE
            WHEN REGEXP_LIKE(final_marketing_layer, 'Mail Call') THEN 'Mail Call'
            ELSE final_marketing_layer
        END AS std_source,
        SUM(spend) AS spend
    FROM ${sink_database}.marketing_channel_spends
    GROUP BY
        year, month,
        mta_marketing_channel,
        CASE
            WHEN REGEXP_LIKE(final_marketing_layer, 'Mail Call') THEN 'Mail Call'
            ELSE final_marketing_layer
        END
)

-- ============================================================
-- STEP 4: Join on channel + std_source and compute CPA, CPB, CPAA
-- ============================================================
SELECT
    m.attribution_type,
    m.conversion_month,
    m.channel,
    m.std_source,
    m.total_conversions,
    m.total_sales,
    m.total_booked,
    m.total_approved,
    s.spend,
    CASE WHEN m.total_conversions > 0 THEN ROUND(s.spend / m.total_conversions, 3) ELSE NULL END AS cpa,
    CASE WHEN m.total_booked      > 0 THEN ROUND(s.spend / m.total_booked, 3)      ELSE NULL END AS cpb,
    CASE WHEN m.total_approved    > 0 THEN ROUND(s.spend / m.total_approved, 3)     ELSE NULL END AS cpapp
FROM mta_agg m
LEFT JOIN spend_agg s
    ON  m.conversion_month      = s.conversion_month
    AND m.channel               = s.mta_marketing_channel
    AND m.std_source            = s.std_source
-- WHERE spend IS NOT NULL
ORDER BY
    m.attribution_type,
    m.conversion_month,
    m.channel,
    m.std_source