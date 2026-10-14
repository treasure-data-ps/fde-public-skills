# Visualizations & Analysis

Create dashboards and analyze recommendation results after the workflow has run successfully.

## Dashboard config.json Structure

The NBP workflow generates a TD dashboard via `config.json`. Replace `<prefix>` with the value from `params.yml` (e.g., `nbp_`) and `sink_database` with the actual database name.

```json
{
  "model_name": "<prefix>_<model_type>_<project>",
  "model_tables": [
    {"db": "sink_database", "name": "<prefix>dash_final_recs_stats_daily"},
    {"db": "sink_database", "name": "<prefix>dash_item_category_mapping_agg"},
    {"db": "sink_database", "name": "<prefix>dash_model_param_stats_agg"},
    {"db": "sink_database", "name": "<prefix>dash_most_ordered_items"},
    {"db": "sink_database", "name": "<prefix>dash_similarity_stats_agg"},
    {"db": "sink_database", "name": "<prefix>dash_testset"},
    {"db": "sink_database", "name": "<prefix>dash_testset_numbers"},
    {"db": "sink_database", "name": "<prefix>global_session_filter"}
  ],
  "shared_user_list": ["user1@example.com"],
  "change_schema_cols": {
    "date": ["event_date"],
    "text": ["ENTER_NAME"],
    "float": ["ENTER_NAME"],
    "bigint": ["ENTER_NAME"]
  },
  "join_relations": {
    "pairs": [
      {"db1": "sink_database", "tb1": "<prefix>global_session_filter", "join_key1": "session_id",
       "db2": "sink_database", "tb2": "<prefix>dash_model_param_stats_agg", "join_key2": "session_id"},
      {"db1": "sink_database", "tb1": "<prefix>global_session_filter", "join_key1": "session_id",
       "db2": "sink_database", "tb2": "<prefix>dash_testset_numbers", "join_key2": "session_id"},
      {"db1": "sink_database", "tb1": "<prefix>global_session_filter", "join_key1": "session_id",
       "db2": "sink_database", "tb2": "<prefix>dash_testset", "join_key2": "session_id"}
    ]
  }
}
```

**Note**: Include the `dash_testset` and `dash_testset_numbers` tables and their join pairs only when `run_model_test_set: yes`.

---

## Dashboard Tables

### `{prefix}dash_final_recs_stats_daily`

Recommendation distribution — how many users received each item/category combination at each rank.

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | varchar | Date of the workflow run |
| `unixtime_tstamp` | bigint | Unix timestamp of event_date |
| `nbp_1` through `nbp_5` | varchar | Recommended item name at each rank |
| `nb_category_1` through `nb_category_5` | varchar | Recommended item category at each rank |
| `item_recs_combo` | varchar | Concatenated item recommendation string |
| `category_recs_combo` | varchar | Concatenated category recommendation string |
| `event_cnt` | bigint | Number of users who received this combination |
| `time` | bigint | TD time column (unixtime) |

**Visualizations**: Top-1 recommendation distribution bar chart, category spread across ranks, recommendation combo frequency.

### `{prefix}dash_most_ordered_items`

Historical ordering frequency per item — shows which items are most popular in the source data.

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | varchar | Date of the workflow run |
| `itemid` | varchar | Item identifier |
| `times_ordered` | bigint | Total number of times this item was ordered |
| `item_name` | varchar | Human-readable item name |
| `time` | bigint | TD time column (unixtime) |

**Visualizations**: Most ordered items bar chart (sorted descending), item popularity distribution.

### `{prefix}dash_item_category_mapping_agg`

Item catalog summary — distinct items per category.

| Column | Type | Description |
|--------|------|-------------|
| `item_category` | varchar | Category name |
| `item_list` | varchar | Comma-separated list of items in this category |
| `item_count` | bigint | Number of distinct items in this category |
| `time` | bigint | TD time column (unixtime) |

**Visualizations**: Category distribution pie chart, item catalog table.

### `{prefix}dash_model_param_stats_agg`

Model run metadata and summary statistics — one row per workflow run.

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | varchar | Date of the workflow run |
| `unixtime_tstamp` | bigint | Unix timestamp of event_date |
| `exclusion_filters` | varchar | Applied exclusion filter description |
| `model_params` | varchar | Model parameters used (JSON string) |
| `filtered_item_count` | bigint | Number of items excluded by filters |
| `filtered_categories` | varchar | Categories excluded |
| `filtered_products` | varchar | Products excluded |
| `least_recent_event` | varchar | Oldest event date in the training data |
| `most_recent_event` | varchar | Most recent event date in the training data |
| `time_range_days` | bigint | Days spanned by the training data |
| `distinct_users_transactions_table` | bigint | Distinct users in the source transaction table |
| `distinct_items_transactions_table` | bigint | Distinct items in the source transaction table |
| `users_with_recs` | bigint | Users who received recommendations |
| `users_with_recs_after_filter` | bigint | Users with recs after exclusion filtering |
| `distinct_items_recommended` | bigint | Distinct items that appear in recommendations |
| `mean_sim` | double | Mean item-item similarity score (hive engine) |
| `median_sim` | double | Median item-item similarity score (hive engine) |
| `std_sim` | double | Std deviation of similarity scores (hive engine) |
| `distinct_categories_transactions_table` | bigint | Distinct categories in the source data |
| `session_id` | bigint | Workflow session ID |
| `model_metrics` | varchar | Additional model metrics (JSON string) |
| `time` | bigint | TD time column (unixtime) |

**Visualizations**: Run summary card (users, items, coverage), trend lines over historical runs, model parameter display.

### `{prefix}dash_similarity_stats_agg`

Item-item similarity pairs — shows which items are most similar to each other (hive engine).

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | varchar | Date of the workflow run |
| `item_pair` | varchar | Item ID pair (e.g., `itemA:itemB`) |
| `item_name` | varchar | Name of the first item |
| `other_item_name` | varchar | Name of the second item |
| `similarity` | double | Similarity score between the two items |
| `time` | bigint | TD time column (unixtime) |

**Visualizations**: Top similar item pairs table, similarity score distribution histogram.

### `{prefix}dash_testset` *(only when `run_model_test_set: yes`)*

Test set evaluation distribution — binned precision/recall histograms per session.

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | bigint | Workflow session ID |
| `label` | double | Bin label (e.g., 0.0, 0.2, 0.4, ...) |
| `bin_cnt` | double | Count of users in this bin |
| `type` | varchar | Metric type: `precision` or `recall` |
| `time` | bigint | TD time column (unixtime) |

**Visualizations**: Precision histogram, recall histogram, overlaid precision/recall distribution.

### `{prefix}dash_testset_numbers` *(only when `run_model_test_set: yes`)*

Test set aggregate metrics — summary precision/recall per session.

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | bigint | Workflow session ID |
| `total_items_bought` | bigint | Total items bought in the test period |
| `total_customers` | bigint | Total customers in the test set |
| `total_bought_above_median` | bigint | Customers who bought above median items |
| `total_product_matches` | bigint | Product-level recommendation matches |
| `total_category_matches` | bigint | Category-level recommendation matches |
| `customers_above_median` | bigint | Customers above median with a match |
| `customers_cat_match` | bigint | Customers with at least one category match |
| `random_item_rate` | double | Expected random item match rate (baseline) |
| `random_category_rate` | double | Expected random category match rate (baseline) |
| `time` | bigint | TD time column (unixtime) |

**Visualizations**: Precision/recall KPI cards, precision vs random baseline comparison, trend over historical runs.

### `{prefix}global_session_filter`

Session index — maps session IDs to run timestamps. Used as the join hub for filtering other tables by session.

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | bigint | Workflow session ID |
| `session_rnk` | bigint | Session rank (1 = most recent) |
| `run_time` | varchar | Human-readable run timestamp |
| `time` | bigint | TD time column (unixtime) |

**Visualizations**: Session selector dropdown (filter other charts by run).

---

## Join Relationships

The `global_session_filter` table is the central filter — it joins to other tables on `session_id`:

```
global_session_filter.session_id --> dash_model_param_stats_agg.session_id
global_session_filter.session_id --> dash_testset_numbers.session_id    (testset only)
global_session_filter.session_id --> dash_testset.session_id            (testset only)
```

The remaining tables (`dash_final_recs_stats_daily`, `dash_most_ordered_items`, `dash_item_category_mapping_agg`, `dash_similarity_stats_agg`) are standalone and filtered by `event_date` or shown as-is.

---

## Suggested Dashboard Layout

| Tab | Tables Used | Charts |
|-----|------------|--------|
| **Overview** | `dash_most_ordered_items`, `dash_model_param_stats_agg` | KPI cards (users with recs, distinct items, coverage), most ordered items bar chart |
| **Item Analysis** | `dash_item_category_mapping_agg`, `dash_most_ordered_items` | Category distribution pie chart, full item catalog table |
| **Recommendations** | `dash_final_recs_stats_daily` | Top-1 recommendation distribution bar chart, category spread across ranks |
| **Model Performance** | `dash_model_param_stats_agg`, `dash_similarity_stats_agg` | Similarity score distribution, run detail card |
| **Test Set** *(testset only)* | `dash_testset_numbers`, `dash_testset` | Precision/recall KPI cards, precision vs random baseline, precision/recall histograms, trend over runs |

---

## Ad-Hoc Analysis Queries

These queries are for analyzing results outside of the dashboard. Replace `{db}` and `{prefix}` with actual values.

### Overview: Key Metrics from Latest Run

```sql
SELECT * FROM {db}.{prefix}dash_model_param_stats_agg
ORDER BY unixtime_tstamp DESC LIMIT 1;
```

### Most Ordered Items

```sql
SELECT * FROM {db}.{prefix}dash_most_ordered_items
ORDER BY times_ordered DESC;
```

### Category Breakdown

```sql
SELECT * FROM {db}.{prefix}dash_item_category_mapping_agg;
```

### Recommendation Distribution (Top-1 Rank)

```sql
SELECT nbp_1, SUM(event_cnt) AS user_count
FROM {db}.{prefix}dash_final_recs_stats_daily
GROUP BY nbp_1
ORDER BY user_count DESC;
```

### Category Diversity of Recommendations

```sql
SELECT nb_category_1 AS top_category, SUM(event_cnt) AS user_count
FROM {db}.{prefix}dash_final_recs_stats_daily
GROUP BY nb_category_1
ORDER BY user_count DESC;
```

### Recommendation Coverage Rate

```sql
SELECT
  (SELECT COUNT(*) FROM {db}.{prefix}user_master_attr WHERE nbp_1 IS NOT NULL) AS users_with_recs,
  (SELECT COUNT(DISTINCT userid) FROM {db}.{prefix}transaction) AS total_users,
  ROUND(
    CAST((SELECT COUNT(*) FROM {db}.{prefix}user_master_attr WHERE nbp_1 IS NOT NULL) AS DOUBLE)
    / (SELECT COUNT(DISTINCT userid) FROM {db}.{prefix}transaction) * 100, 1
  ) AS coverage_pct;
```

### Test Set Precision/Recall (Latest Run)

```sql
-- Aggregate metrics
SELECT n.*
FROM {db}.{prefix}dash_testset_numbers n
JOIN {db}.{prefix}global_session_filter s ON n.session_id = s.session_id
WHERE s.session_rnk = 1;

-- Precision/recall histograms
SELECT t.*
FROM {db}.{prefix}dash_testset t
JOIN {db}.{prefix}global_session_filter s ON t.session_id = s.session_id
WHERE s.session_rnk = 1;
```

### Similarity Stats (Hive Engine Only)

```sql
SELECT * FROM {db}.{prefix}dash_similarity_stats_agg
ORDER BY similarity DESC;
```

### Top Similar Item Pairs (Hive Engine Only)

```sql
SELECT item_name, other_item_name, similarity
FROM {db}.{prefix}dash_similarity_stats_agg
ORDER BY similarity DESC
LIMIT 20;
```

### Run-Over-Run Comparison

```sql
-- Compare coverage across runs
SELECT
  s.run_time,
  m.distinct_users_transactions_table AS source_users,
  m.users_with_recs,
  m.distinct_items_recommended,
  m.time_range_days
FROM {db}.{prefix}dash_model_param_stats_agg m
JOIN {db}.{prefix}global_session_filter s ON m.session_id = s.session_id
ORDER BY s.session_rnk;
```

---

## Interpreting Test Set Results

### Key Metrics

- **`total_product_matches`**: Exact product matches between recommendations and actual purchases during the holdout period. Higher = better recommendation quality.
- **`total_category_matches`**: Category-level matches. Even when exact product isn't matched, recommending the right category indicates the model captures user preferences.
- **`random_item_rate`**: Expected match rate if recommendations were random. Model performance should significantly exceed this baseline.
- **`random_category_rate`**: Expected category match rate if random. Model should exceed this too.

### What "Good" Looks Like

- Product match rate > 2x random baseline
- Category match rate > 3x random baseline
- Coverage rate > 80% of source users receiving recommendations

### When Results Are Poor

- **Very low precision**: Model may not have enough training data, or the data signal is weak (e.g., using views instead of purchases)
- **Good category match but poor product match**: Expected for diverse catalogs — the model captures preferences but specific items are hard to predict
- **Results close to random baseline**: Check if the training data is too sparse, if exclusion filters removed too much data, or if `orders_lookback` is too short
