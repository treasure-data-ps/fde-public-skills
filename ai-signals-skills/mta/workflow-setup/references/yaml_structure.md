# MTA Journey Analytics — YAML Configuration Structure

This document explains the complete structure of the `input_params.yml` file for the MTA Journey Analytics workflow.

## Complete Template

```yaml
#####################################################################
########################## GLOBAL PARAMS ############################
#####################################################################
sink_database: <sink_database>                     # Database for all output tables
unique_user_id: canonical_id                 # Main join key across all tables
api_endpoint: 'api.treasuredata.com'         # TD API endpoint
cleanup_temp_tables: 'no'                    # 'yes' deletes temp tables after run
include_non_converted_channels: yes          # Include channels with zero conversions in output

######################## CUSTOMER ANALYSIS ENRICHMENT ################
add_customer_analysis: 'no'                  # 'yes' joins customer labels to journey table
customers_table: <source_database>.rfm_output_table   # Full table name for customer data
attributes_list: 'recency, frequency, monetary_value, rfm_segment'  # Columns to add

#####################################################################
######################## FILTER PARAMS ##############################
#####################################################################
time_filter_type: range                      # 'range' for fixed dates OR 'interval' for lookback
time_range_start_date: 2022-01-01            # Start date (YYYY-MM-DD)
time_range_end_date: 2222-22-22              # End date (2222-22-22 = latest available)
lookback_period: -180d                       # Only used with 'interval' type

######################## SESSION & JOURNEY PARAMS ####################
session_length: 3600                         # Seconds of inactivity to start new session (3600 = 1hr)
backfill_partition_col: ${unique_user_id}    # Backfill NULL touchpoints across journey or session
top_k_channel_perc: 0.01                     # Collapse low-frequency channels to 'others'
top_k_conv_perc: 0.01                        # Collapse low-conversion channels to 'others'
top_k_journeys: 50                           # Top distinct conversion journeys to extract
sample_tpoint_limit: 25                      # Max touchpoints per sample journey
journey_steps_lookback: 20                   # First/last-N touchpoints per journey
max_journey_days: 180                        #Max number of days to lookback from conversion event
agg_analysis_cols: ["event_context", "channel"]  # Columns for aggregation analysis
summary_table_top_k: 20                      # Top-K distinct values for summary stats

#####################################################################
############## TABLE INPUT PARAMS FOR UNION TABLE ###################
#####################################################################
aggregate_metrics_tables:
  - src_table: <source_database>.enriched_pageviews
    table_description: 'Web Activity data streamed from JS SDK'
    name: pageviews
    unixtime_col: time
    url_col: td_url
    referral_col: td_referrer
    medium_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_medium'), url_extract_parameter(LOWER(td_url),'medium'))"
    source_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_source'), url_extract_parameter(LOWER(td_url),'source'))"
    campaign_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_campaign'), url_extract_parameter(LOWER(td_url),'campaign'))"
    utm_mailing_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_mailing'), url_extract_parameter(LOWER(td_url),'mailing'))"
    context_col: td_title
    event_type: "'web activity'"
    custom_filter: "${unique_user_id} IS NOT NULL AND REGEXP_LIKE(lower(td_language), 'en')"
    conversion_flag: "IF(REGEXP_LIKE(lower(td_path), 'thank_you'), 1.0, 0.0)"
    item_price: 1.0
    apply_time_filter: false
    query_type:

  - src_table: <source_database>.enriched_email_events
    table_description: 'Email activity from SFMC'
    name: email_events
    unixtime_col: time
    url_col: CAST(NULL AS VARCHAR)
    referral_col: "'email'"
    medium_col: "'email'"
    source_col: "'sfmc'"
    campaign_col: "REGEXP_REPLACE(lower(campaign_name), '[- ]', '_')"
    utm_mailing_col: "REGEXP_REPLACE(lower(campaign_name), '[- ]', '_')"
    context_col: "REGEXP_REPLACE(lower(email_name), '[- ]', '_')"
    event_type: "CONCAT('email_', event_type)"
    custom_filter: "${unique_user_id} IS NOT NULL AND NOT REGEXP_LIKE(lower(event_type), 'send')"
    conversion_flag: 0.0
    item_price: 0.0
    apply_time_filter: false
    query_type:

  - src_table: <source_database>.enriched_sales_rep_interactions
    table_description: 'Sales rep notes from SFDC'
    name: sales_rep_interactions
    unixtime_col: time
    url_col: CAST(NULL AS VARCHAR)
    referral_col: CAST(NULL AS VARCHAR)
    medium_col: "'sales_rep_interactions'"
    source_col: source
    campaign_col: topic
    utm_mailing_col: topic
    context_col: topic
    event_type: "CONCAT('sales_rep_interactions_', source)"
    custom_filter: ${unique_user_id} IS NOT NULL
    conversion_flag: 0.0
    item_price: 0.0
    apply_time_filter: false
    query_type:

  - src_table: <source_database>.enriched_orders
    table_description: 'Order history with item price and status'
    name: order_events
    unixtime_col: time
    url_col: CAST(NULL AS VARCHAR)
    referral_col: CAST(NULL AS VARCHAR)
    medium_col: CAST(NULL AS VARCHAR)
    source_col: CAST(NULL AS VARCHAR)
    campaign_col: CAST(NULL AS VARCHAR)
    utm_mailing_col: CAST(NULL AS VARCHAR)
    context_col: order_type
    event_type: "CONCAT(lower(order_type), '_order')"
    custom_filter: "${unique_user_id} IS NOT NULL AND order_status IN ('COMPLETE', 'PROCESSING')"
    conversion_flag: 1.0
    item_price: unit_price
    apply_time_filter: false
    query_type: 'custom'
```

## Parameter Reference

### Global Parameters

| Parameter | Type | Description | Example Values |
|-----------|------|-------------|----------------|
| `sink_database` | string | Database for output tables | `<sink_database>`, `analytics_prod` |
| `unique_user_id` | string | User identifier column name | `canonical_id`, `cdp_profile_id` |
| `api_endpoint` | string | TD API endpoint | `api.treasuredata.com` |
| `cleanup_temp_tables` | yes/no | Delete temp tables after run | `yes`, `no` |
| `include_non_converted_channels` | yes/no | Include zero-conversion channels | `yes`, `no` |

### Customer Enrichment Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `add_customer_analysis` | yes/no | Join customer labels to journey table |
| `customers_table` | string | Full `database.table` for customer data (e.g., RFM output) |
| `attributes_list` | string | Comma-separated column names to add from customer table |

### Time Filter Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `time_filter_type` | string | `range` (fixed dates) or `interval` (lookback) | `range` |
| `time_range_start_date` | date | Start date (YYYY-MM-DD) | `2022-01-01` |
| `time_range_end_date` | date | End date (`2222-22-22` = latest) | `2222-22-22` |
| `lookback_period` | string | Lookback for interval mode | `-180d`, `-6M`, `-2w` |

### Session & Journey Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `session_length` | integer | Seconds of inactivity to start new session | `3600` |
| `backfill_partition_col` | string | Backfill NULLs by user (`${unique_user_id}`) or by session (`session_id`) | `${unique_user_id}` |
| `top_k_channel_perc` | float | Collapse channels below this % of touchpoints to 'others' | `0.01` |
| `top_k_conv_perc` | float | Collapse channels below this % of conversions to 'others' | `0.01` |
| `top_k_journeys` | integer | Number of top distinct conversion journeys to extract | `50` |
| `sample_tpoint_limit` | integer | Max touchpoints per sample journey for review | `25` |
| `journey_steps_lookback` | integer | First/last-N touchpoints to keep per journey | `20` |
| `agg_analysis_cols` | array | Columns for aggregation analysis | `["event_context", "channel"]` |
| `summary_table_top_k` | integer | Top-K distinct values for summary JSON stats | `20` |

### Per-Table Parameters (aggregate_metrics_tables)

| Parameter | Type | Description |
|-----------|------|-------------|
| `src_table` | string | Full `database.table_name` |
| `table_description` | string | Human-readable description |
| `name` | string | Short identifier (used in output table names) |
| `unixtime_col` | string | Timestamp column |
| `url_col` | string/SQL | URL column or `CAST(NULL AS VARCHAR)` |
| `referral_col` | string/SQL | Referrer column or hardcoded string |
| `medium_col` | string/SQL | Marketing medium (e.g., `'email'`, UTM extraction) |
| `source_col` | string/SQL | Marketing source (e.g., `'sfmc'`, column name) |
| `campaign_col` | string/SQL | Campaign name column or expression |
| `utm_mailing_col` | string/SQL | Mailing identifier column or expression |
| `context_col` | string/SQL | Context column (page title, email name, topic) |
| `event_type` | string/SQL | Event type label expression |
| `custom_filter` | string | SQL WHERE clause for filtering |
| `conversion_flag` | float/SQL | `0.0` for touchpoints, `1.0` for conversions, or SQL expression |
| `item_price` | float/string | Revenue column name or constant |
| `apply_time_filter` | boolean | Whether to apply global time filter to this table |
| `query_type` | string | Blank for YAML params, `'custom'` for SQL file in `sql/union_src_tables/` |

## Key Differences from RFM Configuration

| Aspect | RFM | MTA |
|--------|-----|-----|
| Per-table columns | `join_key`, `order_amount` | `url_col`, `referral_col`, `medium_col`, `source_col`, `campaign_col`, `utm_mailing_col`, `context_col`, `event_type`, `conversion_flag`, `item_price` |
| Global params | `num_bins`, `model_type`, output table names | `session_length`, `backfill_partition_col`, `top_k_*`, `journey_steps_lookback` |
| Purpose of each table | All contribute to R/F/M scores | Each is a touchpoint source; one or more define conversions |
| Conversion concept | Not applicable | Explicit `conversion_flag` per table |
| Channel attribution | Not applicable | `medium_col`, `source_col`, `campaign_col` per table |
