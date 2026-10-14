# RFM YAML Configuration Structure

This document explains the complete structure of the `input_params.yml` file for RFM workflows.

## Complete Template

```yaml
#####################################################################
########################## GLOBAL PARAMS ############################
#####################################################################
globals:
  # User identifier column name (must be consistent across all tables)
  canonical_id: canonical_id

  # Output database where results will be stored
  sink_database: <sink_database>

  # Model type - 'custom' for PS quartile code, 'automl' for AI-Signals scoring
  model_type: 'custom'

  # Whether union activity table was pre-built
  built_union_activity: yes

  # Archive previous results before new run
  archive_results: yes

  # Store historical scores for trending analysis
  store_historic_scores: no

  # Timezone for date/time operations
  time_zone: 'UTC'

  # Treasure Data API endpoint
  api_endpoint: 'api.treasuredata.com'

  # Number of bins for histogram display (NOT scoring scale — scoring always uses quartiles 1-4)
  num_bins: 10

### Output Table Names (TOP LEVEL — NOT nested under globals) ###
union_activity_table: rfm_combined_user_events
input_table: rfm_input_table
output_table: rfm_output_table
stats_table: rfm_stats

############## TIME FILTER PARAMS (TOP LEVEL) ##########################
# Whether to apply time filtering to data
apply_time_filter: 'no'

# 'range' for fixed start/end dates OR 'interval' for lookback period
time_filter_type: interval

# Start date for TD_TIME_RANGE (format: YYYY-MM-DD)
time_range_start_date: 2022-01-01

# End date - use '2222-22-22' for "always use latest available date"
time_range_end_date: 2222-22-22

# Lookback period for TD_INTERVAL
# Examples: '-180d' (180 days), '-6M' (6 months), '-2w' (2 weeks)
lookback_period: '-180d'

############## UNION BEHAVIOR TABLES PARAMS ##########################
################ INPUT TABLE PARAMS ###################################
aggregate_metrics_tables:
  - src_table: <source_database>.enriched_pageviews
    name: 'pageviews'
    unixtime_col: time
    join_key: canonical_id
    order_amount: 0.0
    context_col: td_title
    custom_filter:
    apply_time_filter: 'no'
    query_type:

  - src_table: <source_database>.enriched_orders
    name: 'order_events'
    unixtime_col: time
    join_key: canonical_id
    order_amount: unit_price
    context_col: order_status
    custom_filter: "NOT REGEXP_LIKE(lower(order_status), ''cancel|return'')"
    apply_time_filter: 'no'
    query_type:

  - src_table: <source_database>.enriched_email_events
    name: 'email_activity'
    unixtime_col: time
    join_key: canonical_id
    order_amount: 0.0
    context_col: event_type
    custom_filter: "event_type IN (''friendforward'', ''webform'', ''open'', ''click'', ''conversion'', ''unsubscribe'', ''reply'')"
    apply_time_filter: 'no'
    query_type:

  - src_table: <source_database>.sales_rep_interactions
    name: 'sales_rep_interactions'
    unixtime_col: time
    join_key: canonical_id
    order_amount: 0.0
    context_col: interaction_type
    custom_filter:
    apply_time_filter: 'no'
    query_type:
```

## Parameter Explanations

### Global Parameters

| Parameter | Type | Description | Example Values |
|-----------|------|-------------|----------------|
| `canonical_id` | string | Column name for user identifier | `canonical_id`, `cdp_profile_id`, `user_id` |
| `sink_database` | string | Database for output tables | `analytics_prod`, `rfm_results` |
| `model_type` | string | Type of model to run | `custom` (PS quartile code), `automl` (AI-Signals scoring) |
| `built_union_activity` | yes/no | Whether union table pre-exists | `yes`, `no` |
| `archive_results` | yes/no | Archive previous run results | `yes`, `no` |
| `store_historic_scores` | yes/no | Keep historical RFM scores | `yes`, `no` |
| `auto_build_segments` | yes/no | Auto-create customer segments | `yes`, `no` |
| `time_zone` | string | Timezone for operations | `UTC`, `America/New_York` |
| `create_dashboard` | string | Create visualization dashboard | `yes`, `no` |
| `api_endpoint` | string | TD API endpoint | `api.treasuredata.com`, `api-us.treasuredata.com` |
| `num_bins` | integer | Histogram display bins (NOT scoring scale — scoring uses quartiles 1-4) | `10`, `5` |

### Time Filter Parameters

| Parameter | Type | Description | Example Values |
|-----------|------|-------------|----------------|
| `apply_time_filter` | string | Enable time filtering | `yes`, `no` |
| `time_filter_type` | string | Filter method | `range` (fixed dates), `interval` (lookback) |
| `time_range_start_date` | date | Start date for range filter | `2022-01-01`, `2023-06-15` |
| `time_range_end_date` | date | End date (use 2222-22-22 for "latest") | `2024-12-31`, `2222-22-22` |
| `lookback_period` | string | Interval lookback period | `-180d`, `-6M`, `-2w`, `-1Y` |

### Aggregate Metrics Tables Parameters

Each table entry requires:

| Parameter | Type | Description | Example Values |
|-----------|------|-------------|----------------|
| `src_table` | string | Database.table name | `<source_database>.enriched_orders` |
| `name` | string | Descriptive identifier | `order_events`, `pageviews` |
| `unixtime_col` | string | Timestamp column name | `time`, `event_time`, `timestamp` |
| `join_key` | string | User ID column name | `canonical_id`, `user_id` |
| `order_amount` | float/string | Revenue column or 0.0 | `unit_price`, `total_amount`, `0.0` |
| `context_col` | string | **REQUIRED.** Column for per-customer event histogram (top 10 values). Must be a real categorical column in src_table. Omitting this causes broken SQL at runtime. | `event_type`, `order_status`, `category`, `outcome`, `sentiment` |
| `custom_filter` | string | SQL WHERE clause | See examples below |
| `apply_time_filter` | string | Apply time filter to this table | `yes`, `no` |
| `query_type` | string | Leave blank for YML, 'custom' for SQL file | `` (blank), `custom` |

## Custom Filter Examples

### Orders Table
```yaml
# Exclude cancelled and returned orders
custom_filter: "NOT REGEXP_LIKE(lower(order_status), ''cancel|return'')"

# More specific status filtering
custom_filter: "order_status IN (''completed'', ''shipped'', ''delivered'')"

# Exclude refunds and minimum order value
custom_filter: "order_status = ''completed'' AND total_amount > 0"
```

### Email Events Table
```yaml
# Include only engagement events
custom_filter: "event_type IN (''friendforward'', ''webform'', ''open'', ''click'', ''conversion'', ''unsubscribe'', ''reply'')"

# More selective engagement
custom_filter: "event_type IN (''open'', ''click'', ''conversion'')"

# Exclude bounces and spam
custom_filter: "event_type NOT IN (''bounce'', ''spam'', ''sent'')"
```

### Pageviews Table
```yaml
# Usually no filter needed
custom_filter:

# Filter out bot traffic if needed
custom_filter: "is_bot = false"

# Specific page types only
custom_filter: "page_type IN (''product'', ''category'', ''checkout'')"
```

## Output Table Names

Configure where RFM results will be stored. These are **top-level** YAML keys, NOT nested under `globals:`:

```yaml
# Combined activity from all source tables
union_activity_table: rfm_combined_user_events

# Preprocessed input features
input_table: rfm_input_table

# Final RFM quartile scores and segments
output_table: rfm_output_table

# Statistical summary per segment (also generates _histogram, _model_params, _global_session_filter, _daily_agg)
stats_table: rfm_stats
```

The workflow also creates these derived stats tables:
- `${stats_table}_histogram` — histogram bins per metric per segment
- `${stats_table}_model_params` — per-source run metadata
- `${stats_table}_global_session_filter` — session ranking
- `${stats_table}_daily_agg` — historical score aggregation (when `store_historic_scores: yes`)

## Time Filter Modes

### Mode 1: No Time Filter (Default)
Use all historical data:
```yaml
apply_time_filter: 'no'
```

### Mode 2: Range Filter (Fixed Dates)
Specify exact start and end dates:
```yaml
apply_time_filter: 'yes'
time_filter_type: range
time_range_start_date: 2023-01-01
time_range_end_date: 2023-12-31
```

### Mode 3: Interval Filter (Rolling Window)
Lookback from latest data:
```yaml
apply_time_filter: 'yes'
time_filter_type: interval
lookback_period: '-180d'  # Last 180 days
time_range_end_date: 2222-22-22  # Use latest available
```

## Best Practices

1. **Consistent join_key**: Use the same user ID column across all tables
2. **Appropriate filters**: Always filter out invalid transactions (cancels, returns)
3. **Test queries first**: Validate table names and column names before generating YAML
4. **Start simple**: Begin with no time filter, add later if needed
5. **Document assumptions**: Comment why specific filters were chosen
6. **Validate order amounts**: Ensure revenue columns have correct names
7. **Check event types**: Query distinct values before setting filters

## Common Mistakes to Avoid

❌ **Different join_key columns across tables**
```yaml
# DON'T DO THIS
- join_key: canonical_id
- join_key: user_id
```

✅ **Consistent join_key**
```yaml
# DO THIS
- join_key: canonical_id
- join_key: canonical_id
```

❌ **Including cancelled orders**
```yaml
# DON'T DO THIS
custom_filter: ""  # No filter on orders
```

✅ **Filter invalid orders**
```yaml
# DO THIS
custom_filter: "NOT REGEXP_LIKE(lower(order_status), ''cancel|return'')"
```

❌ **Including email "sent" events**
```yaml
# DON'T DO THIS - sent is not engagement
custom_filter: "event_type IN (''sent'', ''open'', ''click'')"
```

✅ **Only engagement events**
```yaml
# DO THIS
custom_filter: "event_type IN (''open'', ''click'', ''conversion'')"
```
