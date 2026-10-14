# RFM Workflow — Output Table Validation

Run these checks after every workflow execution (Phase 3 minimal push and Phase 4 re-run). Use `tdx-skills:tdx-basic` to execute each query against `${sink_database}`.

---

## 1. Primary Output Table — `rfm_output_table`

**What it is:** Final per-profile RFM scores and segment labels. This is the table joined to the Parent Segment in Audience Studio.

```sql
-- Row count and distinct profile count
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT customer_id) AS distinct_profiles
FROM ${sink_database}.rfm_output_table;
```

**Pass criteria:**
- `total_rows > 0`
- `distinct_profiles` is in the same order of magnitude as the Parent Segment profile count (within ~20%)

```sql
-- Confirm expected score columns exist and are non-null
SELECT
  COUNT(*) AS total,
  COUNT(CASE WHEN r_quartile IS NOT NULL THEN 1 END) AS has_recency,
  COUNT(CASE WHEN f_quartile IS NOT NULL THEN 1 END) AS has_frequency,
  COUNT(CASE WHEN m_quartile IS NOT NULL THEN 1 END) AS has_monetary,
  COUNT(CASE WHEN rfm_segment IS NOT NULL THEN 1 END) AS has_segment
FROM ${sink_database}.rfm_output_table;
```

**Pass criteria:** All four columns are non-null for the majority of rows (>80%).

```sql
-- Score distribution sanity check (quartile → expect 4 distinct values per score)
SELECT r_quartile, COUNT(*) AS cnt
FROM ${sink_database}.rfm_output_table
GROUP BY 1 ORDER BY 1;
```

**Pass criteria (quartile):** 4 distinct score values (1, 2, 3, 4) with roughly equal distribution (~25% each). Heavily skewed distributions suggest data quality issues or an overly narrow time filter.

---

## 1b. Input vs Output Profile Count Check

**Run this check immediately after the primary output table check.** Compare `rfm_input_table` distinct profiles against `rfm_output_table` distinct profiles — they must match exactly.

```sql
SELECT
  (SELECT COUNT(DISTINCT customer_id) FROM ${sink_database}.rfm_input_table) AS input_profiles,
  (SELECT COUNT(DISTINCT customer_id) FROM ${sink_database}.rfm_output_table) AS output_profiles
```

**Pass criteria:** `input_profiles = output_profiles`

**If they do not match**, flag this explicitly in your validation summary. The most common cause for `output_profiles` being a multiple of `input_profiles` (e.g. 2x) is scoring appending results into an existing table instead of replacing it. Do not mark Phase 3 validation as passed until this check is green.

---

## 2. Stats Table — `rfm_stats`

**What it is:** Per-segment distribution statistics. Consumed by the RFM Analysis Agent and TI dashboard.

```sql
SELECT rfm_segment, segment_size
FROM ${sink_database}.rfm_stats
ORDER BY segment_size DESC;
```

**Pass criteria:**
- Rows exist for multiple segments
- Segment labels are recognizable (e.g., Champions, Loyal Customers, At-Risk, Lost)
- The `ALL` row `segment_size` matches `distinct_profiles` in `rfm_output_table`
- All other segments have `segment_size > 0`

---

## 3. Union Activity Table — `rfm_combined_user_events`

**What it is:** Union of all source tables — one aggregated row per (profile, source). Used to derive R/F/M inputs.

```sql
-- Confirm all expected sources are present
SELECT source AS source_name, COUNT(*) AS profile_count,
       MIN(recency_days) AS min_recency, MAX(total_touchpoints) AS max_freq
FROM ${sink_database}.rfm_combined_user_events
GROUP BY 1 ORDER BY 2 DESC;
```

**Pass criteria:**
- One row group per configured source (e.g., `pageviews`, `email_activity`, `order_events`, `sales_rep_interactions`)
- No source has `profile_count = 0` — a zero means the source table was empty after filters
- `recency_days` values are positive and reasonable (not 0 or extremely large)

---

## 4. Dashboard Tables

```sql
-- Histogram table
SELECT COUNT(*) AS rows FROM ${sink_database}.rfm_stats_histogram;

-- Model params table
SELECT COUNT(*) AS rows FROM ${sink_database}.rfm_stats_model_params;
```

**Pass criteria:** Both tables have rows (required for TI dashboard to render).

---

## Common Failure Modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `rfm_output_table` is empty | Workflow failed mid-run or `sink_database` doesn't exist | Check attempt logs: `tdx wf attempt <id> logs +rfm_custom` |
| Score distribution is all `1` | All profiles fall in the bottom quartile — data may be sparse or time filter too narrow | Remove time filter or widen lookback period |
| A source is missing from `rfm_combined_user_events` | That source table had 0 rows after `custom_filter` | Inspect the filter — check distinct `order_status` or `event_type` values in source |
| `monetary_score` is uniform (all same value) | No orders table configured, or `order_amount: 0.0` on all tables | Confirm the orders table has a real `order_amount` column configured |
| Profile count much lower than Parent Segment | Source tables don't cover the full audience | Confirm `join_key` is consistent across all tables; check for NULL user IDs |
| `rfm_stats_histogram` is empty | `create_dashboard: 'no'` in config | Set `create_dashboard: 'yes'` and re-run |
