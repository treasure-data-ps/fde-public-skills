# NBA Engagement Scores — Data Dictionary

Schema reference for the three dashboard tables produced by `nba_dash_stats.dig` at the end of each NBA workflow run.

All tables live in `{{sink_database}}` (the `sink_database` in the workflow's `config/input_params.yml`).

> **Customer identifier portability:** These dashboard tables are run-level aggregates (`profile_count`, `unique_profiles`, and `profiles_scored`); they do not require an individual customer ID in dashboard SQL. If analysis expands to raw/profile-level data, resolve the configured `join_key` from `nba_dash_model_metrics` or run `DESCRIBE {{sink_database}}.<table>` first. Customer setups may use `td_consumer_id`, `cdp_profile_id`, `canonical_id`, `user_id`, or another configured identifier—never assume `canonical_id`.

---

## Table 1: `nba_dash_stats_summary` — score / flag distributions per run

**Grain:** one row per `(session_id, metric_name, metric_value)`.

Use when the user asks about **distribution of scores** or **how many users fall into each bucket**.

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | bigint | Identifier of the workflow run. Larger = more recent. |
| `metric_name` | varchar | Which NBA metric column this row describes. Three groups of values appear:<br>• **Affinity scores** — `next_best_channel_<channel>`, `next_best_time_<daypart>` (one row per channel or daypart per profile bucket).<br>• **Profile-level flags** — `conversion_flag`, `ad_engagement_flag`, `recent_ad_engagement_flag`, `recent_purchase_flag`, `cart_abandon_flag`, `new_visitor_flag`, `no_ads_or_purchases_flag`. All seven are emitted every run.<br>• **Pick fields** — `next_best_channel`, `next_best_time`, `next_best_campaign` (single best-pick label per profile). |
| `metric_value` | varchar | The score/flag value, as a string. For `quartile` scoring → `"1"`..`"4"`. For `percentile` / `minmax` → numeric string. For boolean flags → `"0"` / `"1"`. |
| `profile_count` | bigint | Number of unique profiles at that `metric_value` |
| `converted_users` | bigint | How many of those profiles had at least one conversion event in the data window |
| `time` | bigint | Run timestamp (UNIX). Convert to readable form with `TD_TIME_FORMAT(time, 'yyyy-MM-dd HH:mm', 'UTC')` |

### Common SQL patterns

**List metrics available in the latest run:**
```sql
SELECT DISTINCT metric_name FROM nba_dash_stats_summary
WHERE session_id = (SELECT MAX(session_id) FROM nba_dash_model_metrics)
ORDER BY 1
```

**Distribution of a specific metric with conversion rate:**
```sql
SELECT metric_value, profile_count, converted_users,
       ROUND(IF(profile_count > 0, 1.0 * converted_users / profile_count, 0), 4) AS conversion_rate
FROM nba_dash_stats_summary
WHERE session_id = (SELECT MAX(session_id) FROM nba_dash_model_metrics)
  AND metric_name = '<metric>'
ORDER BY TRY_CAST(metric_value AS DOUBLE)
```

**Cart-abandon / new-visitor / engagement / recent-purchase / dormant flag rates (all 7 flags):**
```sql
SELECT metric_name, metric_value, profile_count
FROM nba_dash_stats_summary
WHERE session_id = (SELECT MAX(session_id) FROM nba_dash_model_metrics)
  AND metric_name IN (
    'conversion_flag',
    'ad_engagement_flag',
    'recent_ad_engagement_flag',
    'recent_purchase_flag',
    'cart_abandon_flag',
    'new_visitor_flag',
    'no_ads_or_purchases_flag'
  )
ORDER BY metric_name, metric_value
```
Always pull all 7 — they describe non-overlapping audience segments and skipping any of them gives marketers an incomplete picture of the run.

---

## Table 2: `nba_dash_model_metrics` — run config snapshot

**Grain:** one row per run.

Use when the user asks **"how was the model configured?"**, **"what lookback was used?"**, **"what's the cart-abandon rule?"**, or wants to compare config across runs.

### Run-level columns

| Column | Description |
|--------|-------------|
| `session_id` | Run identifier |
| `profiles_scored` | Total distinct profiles that received at least one NBA score in this run |
| `cart_abandon_logic` | Exact regex/SQL used for cart-abandon detection (`abandon_regexp` from config) |
| `conversion_logic` | Exact rule for what counted as a conversion (`conversion_flag > 0` by default) |
| `ad_engagement_logic` | Channels that disqualify a profile from being "new" |
| `event_lookback_days` | Cart-abandon lookback window |
| `new_customers_days` | Max age of first visit for new-visitor flag |
| `time_filter_type` | `range` or `interval` |
| `time_range_start_date` / `time_range_end_date` | Used when `time_filter_type = 'range'` |
| `lookback_period` | Used when `time_filter_type = 'interval'` (e.g., `-180d`) |
| `time` | Run timestamp (UNIX) |

### Per-source columns (one set per source table in the run's config)

| Column | Description |
|--------|-------------|
| `src_table` | Full `database.table` of source |
| `event_name` | Short identifier (e.g., `pageviews`, `email_events`, `order_events`) |
| `event_type` | The `event_type` SQL expression used |
| `url_col` / `referral_col` | URL and referrer column names (or `NULL` for non-web sources) |
| `medium_col` / `source_col` / `campaign_col` | Channel-extraction expressions per source |
| `join_key` | Configured profile ID column; resolve its actual name from the run/config or source schema (do not assume `canonical_id`) |
| `conversion_flag` | Conversion flag expression for that source |
| `item_price` | Revenue column or constant |
| `custom_filter` | The SQL WHERE clause applied to that source |

### Common SQL patterns

**Snapshot of current config:**
```sql
SELECT * FROM nba_dash_model_metrics
WHERE session_id = (SELECT MAX(session_id) FROM nba_dash_model_metrics)
```

**Compare last two runs' config:**
```sql
SELECT session_id, event_lookback_days, new_customers_days, time_filter_type,
       lookback_period, profiles_scored
FROM nba_dash_model_metrics
ORDER BY session_id DESC
LIMIT 2
```

**Quote back a specific rule:**
```sql
SELECT cart_abandon_logic, ad_engagement_logic, conversion_logic
FROM nba_dash_model_metrics
WHERE session_id = (SELECT MAX(session_id) FROM nba_dash_model_metrics)
```

---

## Table 3: `nba_dash_source_tables` — per-source data volumes per run

**Grain:** one row per `(session_id, source_table)`.

Use when the user asks **"which source contributed the most?"**, **"how much data went into the latest run?"**, or **"what time range does this cover?"**.

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | bigint | Run identifier |
| `source_table` | varchar | e.g., `enriched_pageviews`, `enriched_email_events`, `sales_rep_interactions`, `enriched_orders` |
| `unique_profiles` | bigint | `APPROX_DISTINCT` profiles seen in that source for this run |
| `num_events` | bigint | Total event/row count |
| `total_conversions` | bigint | `SUM(conversion_flag)` for that source |
| `total_spend` | double | `SUM(item_price)` — describes source-data volume only, NOT a predicted ROI |
| `day_range` | varchar | Human-readable date range (e.g. `"2024-01-01 to 2024-06-30"`) |
| `min_date` | varchar | Earliest event date |
| `max_date` | varchar | Latest event date |
| `time` | bigint | Run timestamp (UNIX) |

### Common SQL patterns

**Top sources by event volume in latest run:**
```sql
SELECT source_table, num_events, unique_profiles, total_conversions
FROM nba_dash_source_tables
WHERE session_id = (SELECT MAX(session_id) FROM nba_dash_model_metrics)
ORDER BY num_events DESC
```

**Date coverage of latest run:**
```sql
SELECT source_table, day_range, min_date, max_date
FROM nba_dash_source_tables
WHERE session_id = (SELECT MAX(session_id) FROM nba_dash_model_metrics)
```

**Source contribution change run-over-run:**
```sql
SELECT session_id, source_table, num_events
FROM nba_dash_source_tables
WHERE session_id IN (
  SELECT session_id FROM nba_dash_model_metrics ORDER BY session_id DESC LIMIT 3
)
ORDER BY session_id DESC, num_events DESC
```

---

## Cross-Table Patterns

### Full latest-run summary

Three queries in this order:
1. **Config:** `SELECT * FROM nba_dash_model_metrics WHERE session_id = <latest>`
2. **Volume:** `SELECT source_table, num_events, unique_profiles, total_conversions FROM nba_dash_source_tables WHERE session_id = <latest> ORDER BY num_events DESC`
3. **Distribution highlights:** `SELECT metric_name, metric_value, profile_count, converted_users FROM nba_dash_stats_summary WHERE session_id = <latest> AND metric_name IN ('cart_abandon_flag', 'new_visitor_flag') ORDER BY metric_name, metric_value`

### Run-over-run drift detection

For ANY metric change the user notices, always fetch the corresponding config columns alongside:
```sql
WITH latest_two AS (
  SELECT session_id FROM nba_dash_model_metrics ORDER BY session_id DESC LIMIT 2
)
SELECT m.session_id, m.metric_name, m.metric_value, m.profile_count,
       c.event_lookback_days, c.new_customers_days, c.lookback_period
FROM nba_dash_stats_summary m
JOIN nba_dash_model_metrics c ON m.session_id = c.session_id
WHERE m.session_id IN (SELECT session_id FROM latest_two)
  AND m.metric_name = '<metric_of_interest>'
ORDER BY m.session_id DESC, m.metric_value
```

This way you can attribute the change to either real audience drift or a config change.

---

## Data Quality Notes

- **`metric_value` is VARCHAR** — always `TRY_CAST` to numeric if you need to sort or aggregate numerically. Different `scoring_logic` settings produce different value formats.
- **`session_id` ordering** — larger numbers are more recent runs, but always confirm with `MAX(session_id)` rather than assuming a specific value.
- **`time` is UNIX bigint** — show with `TD_TIME_FORMAT(time, 'yyyy-MM-dd HH:mm', 'UTC')`. The customer's marketing timezone may differ — the workflow's `timeshift_hours` offset (in the workflow config, not in any output table) shifts the dashboard dates, while dayparts use UTC hours.
- **`total_spend` is descriptive, not predictive** — it's a `SUM(item_price)` from the source data. Do NOT project ROI or revenue forecasts from it.
- **Missing metrics** — if a metric_name you expect is absent from `nba_dash_stats_summary` for the latest session, check whether the metric was disabled in config or whether `topk_values` collapsed it into `'others'`.
