# Data Dictionary Guide

## Read description of available tables/columns before doing any analysis

---

## Table 1: journey_src_union_summary
**Purpose:** Source metadata - event/channel distributions, filtering logic, date ranges.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `src_table` | varchar | Original source table name |
| `events_list` | varchar | JSON string of event types with counts |
| `channel_list` | varchar | JSON string of channels with counts |
| `source_list` | varchar | JSON string of traffic sources with counts |
| `campaign_list` | varchar | JSON string of campaigns with counts |
| `utm_mailing_list` | varchar | JSON string of UTM mailing parameters with counts |
| `context_list` | varchar | JSON string of context values with counts |
| `total_profiles` | bigint | Count of unique customer profiles |
| `total_events` | bigint | Total event count |
| `conversion_events` | double | Count of conversion events |
| `min_date` | varchar | Earliest event date in source |
| `max_date` | varchar | Latest event date in source |
| `table_description` | varchar | Human-readable description of table contents |
| `final_where_clause` | varchar | SQL WHERE clause used to filter source data |
---

## TABLE 2: mta_sankey_journeys
**Purpose**: Pre-aggregated journey flows for path analysis and Sankey visualizations. Every path terminates at a `conversion` or `churn` node — use this table (NOT `mta_markov_transition_final`) for all Sankey diagrams.

**Key Columns:**

| Column | Description |
|--------|-------------|
| `target` | Journey outcome: `'conversion'` or `'churn'` |
| `conversion_month` | Month of conversion — rows are split per month, so always SUM(conversions) when aggregating |
| `from_step` | Origin node in format `"N-channel"` where N is the 1-indexed position in the journey (e.g. `"1-organic"`, `"2-crm"`) |
| `to_step` | Destination node in same format, or `"N-conversion"` / `"N-churn"` when the path ends (e.g. `"2-conversion"`, `"3-conversion"`) |
| `conversions` | Number of journeys following this edge in this conversion_month — **must be summed across months** |
| `total_events` | Total events for these journeys |
| `avg_journey_length` | Average total touchpoints in these journeys |
| `conv_perc` | Conversion rate for journeys following this path |
| `rnk` | Rank of the **complete journey pattern** by volume. All rows sharing the same `rnk` are edges of one single path |

**Critical: How `rnk` works — tracing a complete path**

Each `rnk` value = one complete journey pattern. All edges of that pattern share the same `rnk`. To reconstruct a path, collect all rows for a given `rnk` in step order:

```
rnk=4: "1-non-brand sem" → "2-organic"      (edge 1 of this pattern)
rnk=4: "2-organic"       → "3-conversion"   (edge 2 of this pattern — terminates at conversion)
```

This means the same channel label (e.g. `"2-organic"`) appears as both a `to_step` in one row and a `from_step` in the next — that is what creates the connected multi-step flow.

**Critical: Duplicate rows per month**

The table stores one row per `(rnk, from_step, to_step, conversion_month)`. When building a Sankey, always aggregate:
```sql
SELECT from_step, to_step, SUM(conversions) AS flow
FROM mta_sankey_journeys
WHERE target = 'conversion' AND rnk <= 10
GROUP BY from_step, to_step
ORDER BY SUM(conversions) DESC
```

**Critical: Sankey node naming — preserve the `N-` prefix**

Always use `from_step` and `to_step` values as-is (e.g. `"1-organic"`, `"2-conversion"`) as Sankey node names. Do NOT strip the numeric prefix. This preserves journey position so the same channel at different steps (e.g. `"2-organic"` vs `"3-organic"`) renders as distinct nodes in the flow.

**Usage:** Filter `target='conversion' AND rnk <= 10` for top 10 conversion paths. The `to_step` always ends in `N-conversion` — every path visibly terminates at the conversion event.

---

## Table 3: mta_journeys
**Purpose:** Event-level journey data with touchpoints, sessions, RFM segmentation.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `date_time` | varchar | Timestamp of event |
| `event_date` | varchar | Date of event |
| `conversion_month` | varchar | Month in which conversion occurred |
| `day_of_week` | varchar | Day name |
| `<customer_id_col>` (e.g., `td_consumer_id`, `canonical_id`) | varchar | Unique customer identifier configured via `unique_user_id` in `input_params.yml` (run `DESCRIBE mta_journeys` to confirm) |
| `url` | varchar | Page URL visited |
| `referral_domain` | varchar | Referring domain |
| `event_type` | varchar | Type of event |
| `events_num` | bigint | Number of events in this record |
| `context_col` | varchar | Context column name used |
| `event_context` | varchar | Actual context value |
| `channel` | varchar | Marketing channel |
| `source` | varchar | Traffic source |
| `campaign` | varchar | Campaign identifier |
| `conversion_journey_id` | varchar | Unique conversion journey ID |
| `conversion_flag` | double | 1.0 if conversion event, 0.0 otherwise |
| `journey_length` | bigint | Total touchpoints in conversion journey |
| `journey_index` | bigint | Position of this event in journey (1-indexed) |
| `journey_touchpoints_total` | bigint | Total touchpoints across journey |
| `conversion_value_total_sales` | double | |
| `touchpoint_histogram` | varchar | Distribution of touchpoints by channel |
| `sess_rank_asc` | bigint | Session rank ascending (first = 1) |
| `top_channels` | array(varchar) | Array of channels used in journey |
| `channel_list_final` | varchar | Deduplicated channel sequence, where a multi-channel journey will have the distinct channel values separated by '>' |
| `journey_history` | varchar | Full journey path with timestamps |
| `journey_duration_mins` | bigint | Journey duration in minutes |
| `journey_duration_days` | bigint | Journey duration in days |
| `recency` | bigint | Days since last touchpoint (RFM) |
| `frequency` | bigint | Number of touchpoints (RFM) |
| `monetary_value` | double | Total spend |
| `rfm_segment` | varchar | RFM customer segment |

**Key Columns:**
- 'conversion_flag' - use to flag when application happen
- 'conversion_journey_id' - Unique journey ID, so use APPROX_DISTINCT(conversion_journey_id) when counting how many journeys meet a criteria in a GROUP BY analysis
- `channel_list_final` - If a distinct journey_id contains multiple channel touchpoints, they will be separated by '>' in order of occurrence. Single channel journeys meet criteria "WHERE NOT REGEXP_LIKE(channel_list_final, '>') ".
- 'conversion_value' - when >0 THEN this means this is a converted journey, but do NOT sum this to get count of converted journeys, instead you should do "APPROX_DISTINCT(conversion_journey_id) WHERE conversion_value > 0"

**Usage:** When trying to answer journey related questions to find patterns of channels that appear in converted vs. non converted journeys etc.

---

## Table 4: mta_models_standard
**Purpose:** Rule-based attribution models (first-touch, last-touch, linear, U-shaped) by channel/source/campaign.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `attribution_type` | varchar | Attribution model used |
| `conversion_month` | varchar | Month in which conversion occurred |
| `channel` | varchar | Marketing channel receiving attribution |
| `source` | varchar | Traffic source |
| `campaign` | varchar | Campaign identifier |
| `total_conversions` | double | Number of conversions attributed |
| `total_sales` | double | Revenue attributed |

---

## Table 5: mta_markov_attribution_final (Markov Chain Attribution)
**Purpose:** Algorithmic attribution using Markov chains. Measures each channel's incremental impact via removal effect (0-1 scale).

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `run_time` | varchar | timestamp when model was ran|
| `channels` | varchar | Marketing channel |
| `attribution_markov_algorithmic` | double | Markov-calculated conversions attributed to channel |
| `removal_effect` | double | Decrease in conversions if channel removed (0-1 scale) |

**Usage:** High removal_effect (>0.20) indicates critical channels; use for budget prioritization. Use MAX(run_time) to fetch the latest metrics.

---

## Table 6: mta_shapley_attribution_final (Shapley Value Attribution)
**Purpose:** Game theory-based fair credit distribution using Shapley values. Evaluates all channel combinations and marginal contributions.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `run_time` | varchar | timestamp when model was ran|
| `day` | bigint | Day number where 0 is conversion event day |
| `channels` | varchar | Marketing channel |
| `value` | double | Shapley value (conversions attributed) |
| `percentage` | double | Percentage of total conversions attributed |

**Usage:** Compare vs. Markov/rule-based models; day-level time series analysis. Use MAX(run_time) to fetch the latest metrics.
---

## Table 7: mta_journey_stats_yearly (Journey Stats Summary by Year)
**Purpose:** Provide summary of important journey stats broken by year
**Usage:** Validate high-level statistics for the mta_journeys table aggregated at the yearly level
---


## Cross-Table Analysis Patterns

### Attribution Model Comparison
Combine mta_models_standard, mta_markov_attribution, and mta_shapley_attribution_final to see how credit allocation changes across methodologies.

### Historic Trends Analysis
- GROUP BY 'conversion_month' when asked to show historic trends of channel performance
- For markov and shapely tables use MAX(run_time) to show the latest metric, and when asked to show how attribution % change across historic runs use `run_time' timestamp column to show changing trends in attribution % over time

---

## Data Quality Notes

**Characteristics:** Channel naming uses lowercase with underscores (e.g. `paid_search_google`); percentages stored as decimals (0.25 = 25%); some channels may not appear in all models if insufficient data.

**Edge Cases:** Physical store tracking requires loyalty program use; cross-device journeys may fragment without login; micro-conversions tracked separately.
