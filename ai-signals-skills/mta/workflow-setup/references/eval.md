# MTA Journey Analytics — Workflow Output Validation

Run these checks after every workflow execution (Phase 3 minimal push and Phase 4 re-run). Execute all queries against `${sink_database}` using `tdx-skills:tdx-basic`.

---

## 1. Source Union — `journey_src_union_final`

**What it is:** The unified touchpoint table before journey construction — one row per touchpoint across all configured source tables. Used to verify that every source table flowed through correctly and that channel/source values resolved as expected.

```sql
-- Row count, unique customers, and conversion count
SELECT
  COUNT(*) AS total_touchpoints,
  COUNT(DISTINCT customer_id) AS unique_customers,
  CAST(SUM(conversion_flag) AS BIGINT) AS total_conversions
FROM ${sink_database}.journey_src_union_final;
```

**Pass criteria:**
- `total_touchpoints > 0`
- `unique_customers > 0`
- `total_conversions > 0` — if zero, the `conversion_flag` expression in `input_params.yml` is not matching any rows (see Common Failure Modes)

```sql
-- Confirm all configured source tables are present and only conversion tables have conversions > 0
SELECT
  src_table,
  COUNT(*) AS touchpoints,
  CAST(SUM(conversion_flag) AS BIGINT) AS conversions
FROM ${sink_database}.journey_src_union_final
GROUP BY 1
ORDER BY 2 DESC;
```

**Pass criteria:**
- One row per table listed in `aggregate_metrics_tables` in `input_params.yml` — a missing table means it returned 0 rows after applying `custom_filter` or the time filter
- Only the designated conversion source(s) have `conversions > 0`; all touchpoint-only sources should show `0`

```sql
-- Channel distribution — check for unexpected nulls or dominance of 'others'
SELECT channel_final, COUNT(*) AS cnt
FROM ${sink_database}.journey_src_union_final
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;
```

**Pass criteria:**
- Channel values are meaningful (e.g. UTM mediums, hardcoded channel strings from config)
- `others` or NULL should not dominate (>70%) — if so, reduce `top_k_channel_perc` or check UTM coverage

---

## 2. Source Union Summary — `journey_src_union_summary`

**What it is:** One row per configured source table — event counts, profile counts, conversion counts, date range, and the exact config expressions applied (medium_col, source_col, etc.). The primary config audit table.

```sql
-- One row per source — confirm all sources ran and conversion counts are correct
SELECT
  src_table,
  table_description,
  total_profiles,
  total_events,
  CAST(conversion_events AS BIGINT) AS conversion_events,
  min_date,
  max_date
FROM ${sink_database}.journey_src_union_summary
ORDER BY total_events DESC;
```

**Pass criteria:**
- One row per configured source table
- `total_events > 0` for every source — zero means the source was filtered out entirely
- `conversion_events > 0` only for designated conversion source(s)
- `min_date` and `max_date` fall within the configured lookback window

```sql
-- Verify the filter and channel expressions that were actually applied
SELECT src_table, final_where_clause, medium_col, source_col, campaign_col
FROM ${sink_database}.journey_src_union_summary
ORDER BY src_table;
```

**Pass criteria:**
- `final_where_clause` for each source matches what was configured in `custom_filter` (e.g. email excludes `sent`/`bounced`)
- `medium_col` / `source_col` / `campaign_col` expressions match `input_params.yml`

---

## 3. Journey Table — `mta_journeys`

**What it is:** Sessionized, journey-enriched touchpoint table — one row per touchpoint with journey context (journey ID, index, length, channel list, duration). This is the main table consumed by the MTA journey analysis skill (`fde-mta-journey-agent`) for path analysis.

```sql
-- Row count, unique customers, conversions, and journey count
SELECT
  COUNT(*) AS total_touchpoints,
  COUNT(DISTINCT customer_id) AS unique_customers,
  CAST(SUM(conversion_flag) AS BIGINT) AS total_conversions,
  COUNT(DISTINCT conversion_journey_id) AS distinct_journeys
FROM ${sink_database}.mta_journeys;
```

**Pass criteria:**
- Counts are consistent with `journey_src_union_final` (same order of magnitude)
- `distinct_journeys > 0`

```sql
-- Journey length distribution sanity check
SELECT
  journey_length,
  COUNT(DISTINCT conversion_journey_id) AS journeys
FROM ${sink_database}.mta_journeys
GROUP BY 1
ORDER BY 1
LIMIT 20;
```

**Pass criteria:**
- Journey lengths range from 1 to reasonable values (not all single-touchpoint journeys, which would degenerate attribution)
- Very long journeys (>50 steps) are rare — if most journeys are length 1, check `session_length` config or whether sources have overlapping timestamps

---

## 4. Journey Validation Summary — `mta_journeys_validate`

**What it is:** Pre-aggregated channel-level summary with conversion and revenue percentages. The fastest way to sanity-check attribution distribution across channels.

```sql
-- Full channel summary sorted by events
SELECT
  channel,
  total_events,
  ROUND(perc_of_total_events * 100, 1) AS pct_events,
  CAST(total_conversions AS BIGINT) AS conversions,
  ROUND(perc_of_total_conv * 100, 1) AS pct_conversions,
  distinct_journeys,
  converted_journeys
FROM ${sink_database}.mta_journeys_validate
ORDER BY total_events DESC;
```

**Pass criteria:**
- All configured channels appear
- `perc_of_total_events` values sum to approximately 100%
- `perc_of_total_conv` values sum to approximately 100%
- No single channel captures >90% of conversions (indicates degenerate journeys)

---

## 5. Top Conversion Journeys — `mta_top_conversion_journeys`

**What it is:** Top-K most frequent conversion path patterns, separated by `target` (converted vs non-converted). Shows which channel sequences most commonly lead to conversion.

```sql
-- Top converting journey sequences
SELECT
  target,
  journey_steps,
  conversions,
  total_events,
  ROUND(avg_journey_length, 1) AS avg_steps,
  ROUND(avg_journey_duration_days, 1) AS avg_days
FROM ${sink_database}.mta_top_conversion_journeys
ORDER BY target, conversions DESC
LIMIT 20;
```

**Pass criteria:**
- Both `target` values are present (converted and non-converted)
- `journey_steps` contain recognizable channel names from the config
- `conversions > 0` for converted journeys
- `avg_journey_duration_days` is a reasonable number (not 0 or thousands)

---

## 6. Markov Attribution — `mta_markov_attribution_final`

**What it is:** Markov chain attribution scores per channel — `attribution_markov_algorithmic` is the percentage of conversions attributed, `removal_effect` is the impact of removing that channel from all journeys. Only present when ML models ran successfully.

```sql
-- Markov channel attribution scores
SELECT
  channels,
  ROUND(attribution_markov_algorithmic * 100, 2) AS attribution_pct,
  ROUND(removal_effect * 100, 2) AS removal_effect_pct,
  run_time
FROM ${sink_database}.mta_markov_attribution_final
ORDER BY attribution_markov_algorithmic DESC;
```

**Pass criteria:**
- One row per channel
- `attribution_markov_algorithmic` values sum to approximately 1.0 (100%)
- `removal_effect > 0` for all channels — zero removal effect means the channel never appears in conversion paths
- `run_time` matches the latest workflow execution date

---

## 7. Markov Transition Matrix — `mta_markov_transition_final`

**What it is:** Channel-to-channel transition probabilities used to build the Markov model. Each row is a `channels → to_channel` pair with the probability of that transition occurring in the data.

```sql
-- Transition probabilities from each channel (rows should sum to 1.0 per channel)
SELECT
  channels,
  to_channel,
  ROUND(trans_prob, 4) AS trans_prob,
  ROUND(_conversion_, 4) AS conversion_prob
FROM ${sink_database}.mta_markov_transition_final
ORDER BY channels, trans_prob DESC
LIMIT 30;
```

**Pass criteria:**
- `channels` and `to_channel` values are recognizable channel names or `(start)` / `(conversion)` / `(null)`
- `trans_prob` values per `channels` group sum to approximately 1.0
- `(conversion)` appears as a `to_channel` for channels that lead to conversion

---

## 8. Shapley Attribution — `mta_shapley_attribution_final`

**What it is:** Shapley value attribution scores per channel per day — `value` is the attributed conversion count, `percentage` is the share of total attribution. Only present when ML models ran successfully.

```sql
-- Shapley attribution summary (latest run)
SELECT
  channels,
  ROUND(SUM(value), 2) AS total_attributed_conversions,
  ROUND(AVG(percentage) * 100, 2) AS avg_daily_attribution_pct,
  run_time
FROM ${sink_database}.mta_shapley_attribution_final
GROUP BY channels, run_time
ORDER BY total_attributed_conversions DESC;
```

**Pass criteria:**
- One group per channel
- `total_attributed_conversions` sums to approximately the total conversion count
- `run_time` matches the latest workflow execution date

---

## Common Failure Modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `journey_src_union_final` is empty | Workflow failed mid-run or `sink_database` does not exist | Check attempt logs in TD console; confirm `sink_database` exists and the workflow user has write access |
| `total_conversions = 0` across all tables | `conversion_flag` expression not matching source values | Query distinct values of the conversion column directly from the source table; check case sensitivity and exact string values |
| Source table missing from `journey_src_union_summary` | Source had 0 rows after `custom_filter` or time filter | Relax `custom_filter`; confirm source table has data within the configured lookback window |
| All channels resolve to `others` | UTM coverage too low or `top_k_channel_perc` too aggressive | Lower `top_k_channel_perc` (e.g. `0.001`); verify UTM coverage on web source tables |
| Journey lengths are all 1 | `session_length` too short or source timestamps are misaligned | Increase `session_length` (e.g. `86400` = 1 day); confirm all sources use the same Unix timestamp column |
| `mta_markov_attribution_final` or `mta_shapley_attribution_final` are empty | Dataset fell below `ml_models_records_limit` | Reduce `ml_models_records_limit` (e.g. to `100000`) or extend `ml_models_lookback_days_limit` |
| Attribution percentages do not sum to 100% | Rounding across many channels | Acceptable if the discrepancy is <1%; check for duplicate rows if larger |
| `mta_top_conversion_journeys` missing `non-converted` rows | No non-converted journeys in the data | Check `include_non_converted_channels: yes` in `input_params.yml` |
