# NBP — Data Dictionary

Schema reference for the dashboard tables produced by the NBP workflow on each run.

All tables live in the customer's `sink_database` (recorded in `project_state.md`). Table names use the configured `prefix` (default: `nbp_`). Replace `{prefix}` and `{db}` with actual values when writing queries.

> **Customer identifier portability:** NBP dashboard tables are session-level aggregates and expose user counts rather than individual IDs, so dashboard SQL does not assume `canonical_id` or `customer_id`. For a profile-level drill-down, resolve `original_user_id_column_name` from the customer's `params.yml` or run `DESCRIBE {db}.<table>` first. The configured identifier may be `td_consumer_id`, `td_canonical_id`, `canonical_id`, `cdp_profile_id`, `user_id`, or another customer-specific column.

---

## Table 1: `{prefix}global_session_filter` — session inventory

**Grain:** one row per workflow run.

Use this as the **central filter table**. Always join other tables on `session_id`, and use `session_rnk = 1` to get the latest run.

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | bigint | Workflow session identifier. Larger = more recent. |
| `session_rnk` | bigint | Run rank: `1` = most recent, `2` = second-most-recent, etc. |
| `run_time` | varchar | Human-readable run timestamp (e.g., `"2026-04-18 06:00:00"`) |
| `time` | bigint | Run timestamp (UNIX). Convert with `TD_TIME_FORMAT(time, 'yyyy-MM-dd HH:mm', 'UTC')` |

### Common SQL patterns

**Get the latest session ID:**
```sql
SELECT session_id FROM {prefix}global_session_filter WHERE session_rnk = 1
```

**List all runs in reverse chronological order:**
```sql
SELECT session_id, session_rnk, run_time FROM {prefix}global_session_filter ORDER BY session_rnk ASC
```

---

## Table 2: `{prefix}dash_model_param_stats_agg` — run config and coverage stats

**Grain:** one row per workflow run.

Use when the user asks about **coverage**, **model config**, **training data size**, or wants to **compare runs**.

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | varchar | Date of the workflow run (e.g., `"2026-04-18"`) |
| `unixtime_tstamp` | bigint | Unix timestamp of `event_date` |
| `session_id` | bigint | Run identifier. Join to `global_session_filter` for rank/timestamp. |
| `distinct_users_transactions_table` | bigint | Distinct users in the source transaction table (before model) |
| `users_with_recs` | bigint | Users who received at least one recommendation |
| `users_with_recs_after_filter` | bigint | Users with recs after exclusion filtering |
| `distinct_items_recommended` | bigint | Distinct items that appear anywhere in the recommendation output |
| `distinct_items_transactions_table` | bigint | Distinct items in the source transaction table |
| `distinct_categories_transactions_table` | bigint | Distinct categories in the source data |
| `time_range_days` | bigint | Days spanned by the training data |
| `least_recent_event` | varchar | Oldest event date in the training data |
| `most_recent_event` | varchar | Most recent event date in the training data |
| `model_params` | varchar | JSON string of model configuration (`model_type`, `automl_model_type`, key tuning params) |
| `exclusion_filters` | varchar | Description of applied exclusion filters |
| `filtered_item_count` | bigint | Number of items excluded by filters |
| `filtered_categories` | varchar | Categories excluded |
| `filtered_products` | varchar | Products excluded |
| `mean_sim` | double | Mean item-item similarity score (hive engine only; NULL for automl) |
| `median_sim` | double | Median item-item similarity score (hive engine only) |
| `std_sim` | double | Std deviation of similarity scores (hive engine only) |
| `model_metrics` | varchar | Additional model metrics (JSON string) |
| `time` | bigint | Run timestamp (UNIX) |

### Common SQL patterns

**Latest run coverage summary:**
```sql
SELECT users_with_recs, distinct_users_transactions_table,
       ROUND(100.0 * users_with_recs / NULLIF(distinct_users_transactions_table, 0), 1) AS coverage_pct,
       distinct_items_recommended, time_range_days, least_recent_event, most_recent_event,
       model_params, exclusion_filters
FROM {prefix}dash_model_param_stats_agg
WHERE session_id = (SELECT session_id FROM {prefix}global_session_filter WHERE session_rnk = 1)
```

**Compare last two runs:**
```sql
SELECT s.session_id, s.run_time,
       m.users_with_recs, m.distinct_users_transactions_table,
       ROUND(100.0 * m.users_with_recs / NULLIF(m.distinct_users_transactions_table, 0), 1) AS coverage_pct,
       m.distinct_items_recommended, m.time_range_days, m.model_params
FROM {prefix}dash_model_param_stats_agg m
JOIN {prefix}global_session_filter s ON m.session_id = s.session_id
WHERE s.session_rnk <= 2
ORDER BY s.session_rnk ASC
```

---

## Table 3: `{prefix}dash_final_recs_stats_daily` — recommendation distribution

**Grain:** one row per (event_date, item/category combination). Aggregated recommendation output.

Use when the user asks about **which items/categories are most commonly recommended** or **rank distribution**.

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | varchar | Date of the workflow run |
| `unixtime_tstamp` | bigint | Unix timestamp of `event_date` |
| `nbp_1` through `nbp_5` | varchar | Recommended item name at each rank |
| `nb_category_1` through `nb_category_5` | varchar | Recommended item category at each rank |
| `item_recs_combo` | varchar | Concatenated full item recommendation string (all ranks) |
| `category_recs_combo` | varchar | Concatenated full category recommendation string |
| `event_cnt` | bigint | Number of users who received this item/category combination |
| `time` | bigint | TD time column (UNIX) |

Note: Only ranks up to `max_recommended_items` from `params.yml` are populated (default: 5 for hive; configurable for automl).

### Common SQL patterns

**Top-10 most recommended items at rank 1:**
```sql
SELECT nbp_1, SUM(event_cnt) AS user_count
FROM {prefix}dash_final_recs_stats_daily
WHERE event_date = (SELECT MAX(event_date) FROM {prefix}dash_final_recs_stats_daily)
GROUP BY nbp_1 ORDER BY user_count DESC LIMIT 10
```

**Category distribution at rank 1:**
```sql
SELECT nb_category_1 AS category, SUM(event_cnt) AS user_count
FROM {prefix}dash_final_recs_stats_daily
WHERE event_date = (SELECT MAX(event_date) FROM {prefix}dash_final_recs_stats_daily)
GROUP BY nb_category_1 ORDER BY user_count DESC
```

**Category spread across all ranks (rank 1 through 3):**
```sql
SELECT 'rank_1' AS rank_label, nb_category_1 AS category, SUM(event_cnt) AS user_count
FROM {prefix}dash_final_recs_stats_daily
WHERE event_date = (SELECT MAX(event_date) FROM {prefix}dash_final_recs_stats_daily)
GROUP BY nb_category_1
UNION ALL
SELECT 'rank_2', nb_category_2, SUM(event_cnt)
FROM {prefix}dash_final_recs_stats_daily
WHERE event_date = (SELECT MAX(event_date) FROM {prefix}dash_final_recs_stats_daily)
GROUP BY nb_category_2
UNION ALL
SELECT 'rank_3', nb_category_3, SUM(event_cnt)
FROM {prefix}dash_final_recs_stats_daily
WHERE event_date = (SELECT MAX(event_date) FROM {prefix}dash_final_recs_stats_daily)
GROUP BY nb_category_3
ORDER BY rank_label, user_count DESC
```

---

## Table 4: `{prefix}dash_most_ordered_items` — historical item popularity

**Grain:** one row per item. Reflects source transaction data, not model output.

Use when the user asks about **item popularity in the historical data** or wants to compare recommended items vs. most-purchased items.

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | varchar | Date of the workflow run |
| `itemid` | varchar | Item identifier (matches `original_item_id_column_name` from params) |
| `item_name` | varchar | Human-readable item name |
| `times_ordered` | bigint | Total times this item was ordered in the training data |
| `time` | bigint | TD time column (UNIX) |

### Common SQL patterns

**Most popular items in source data:**
```sql
SELECT item_name, times_ordered
FROM {prefix}dash_most_ordered_items
ORDER BY times_ordered DESC LIMIT 20
```

**Items recommended most vs. purchased most (popularity vs. rec divergence):**
```sql
-- Most recommended (rank 1 only)
SELECT nbp_1 AS item, SUM(event_cnt) AS rec_count
FROM {prefix}dash_final_recs_stats_daily
WHERE event_date = (SELECT MAX(event_date) FROM {prefix}dash_final_recs_stats_daily)
GROUP BY nbp_1 ORDER BY rec_count DESC LIMIT 10
```
Then compare against `dash_most_ordered_items` — divergence between the two lists shows the model is surfacing personalized long-tail items (desirable) rather than just recommending popular items.

---

## Table 5: `{prefix}dash_item_category_mapping_agg` — catalog category breakdown

**Grain:** one row per category.

Use when the user asks about **product catalog structure** or **category diversity**.

| Column | Type | Description |
|--------|------|-------------|
| `item_category` | varchar | Category name |
| `item_list` | varchar | Comma-separated list of items in this category |
| `item_count` | bigint | Number of distinct items in this category |
| `time` | bigint | TD time column (UNIX) |

### Common SQL patterns

**Category breakdown:**
```sql
SELECT item_category, item_count
FROM {prefix}dash_item_category_mapping_agg
ORDER BY item_count DESC
```

---

## Table 6: `{prefix}dash_similarity_stats_agg` — item-item similarity pairs (hive engine only)

**Grain:** one row per item pair.

Only populated when `model_type: hive`. Empty or absent for automl.

Use when the user asks **"what's similar to item X?"** or wants to understand the model's similarity structure.

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | varchar | Date of the workflow run |
| `item_pair` | varchar | Item ID pair (e.g., `"itemA:itemB"`) |
| `item_name` | varchar | Name of the first item |
| `other_item_name` | varchar | Name of the second item |
| `similarity` | double | Cosine similarity score (0–1). Higher = more similar. |
| `time` | bigint | TD time column (UNIX) |

### Common SQL patterns

**Top similar item pairs:**
```sql
SELECT item_name, other_item_name, similarity
FROM {prefix}dash_similarity_stats_agg
ORDER BY similarity DESC LIMIT 20
```

**Items most similar to a specific item:**
```sql
SELECT other_item_name, similarity
FROM {prefix}dash_similarity_stats_agg
WHERE item_name = '<item_name>'
ORDER BY similarity DESC LIMIT 10
```

---

## Table 7: `{prefix}dash_testset` — precision/recall histograms (testset only)

**Grain:** one row per (session_id, bin_label, metric_type).

Only present when `run_model_test_set: yes` in `params.yml`. Verify existence before querying.

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | bigint | Workflow session ID |
| `label` | double | Bin label (e.g., 0.0, 0.2, 0.4, ...) |
| `bin_cnt` | double | Count of users in this bin |
| `type` | varchar | Metric type: `precision` or `recall` |
| `time` | bigint | TD time column (UNIX) |

### Common SQL patterns

**Precision/recall histogram for latest run:**
```sql
SELECT t.label, t.bin_cnt, t.type
FROM {prefix}dash_testset t
JOIN {prefix}global_session_filter s ON t.session_id = s.session_id
WHERE s.session_rnk = 1
ORDER BY t.type, t.label
```

---

## Table 8: `{prefix}dash_testset_numbers` — aggregate test set metrics (testset only)

**Grain:** one row per session.

Only present when `run_model_test_set: yes`. Verify existence before querying.

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | bigint | Workflow session ID |
| `total_items_bought` | bigint | Total items bought in the test holdout period |
| `total_customers` | bigint | Total customers in the test set |
| `total_bought_above_median` | bigint | Customers who bought above median items in holdout |
| `total_product_matches` | bigint | Exact product-level matches between recs and actual purchases |
| `total_category_matches` | bigint | Category-level matches between recs and actual purchases |
| `customers_above_median` | bigint | Customers above median with at least one product match |
| `customers_cat_match` | bigint | Customers with at least one category match |
| `random_item_rate` | double | Expected match rate for random item recommendations (baseline) |
| `random_category_rate` | double | Expected match rate for random category recommendations (baseline) |
| `time` | bigint | TD time column (UNIX) |

### Common SQL patterns

**Aggregate test set metrics for latest run:**
```sql
SELECT n.*
FROM {prefix}dash_testset_numbers n
JOIN {prefix}global_session_filter s ON n.session_id = s.session_id
WHERE s.session_rnk = 1
```

**Test set trend across runs:**
```sql
SELECT s.session_id, s.run_time,
       ROUND(100.0 * n.total_product_matches / NULLIF(n.total_items_bought, 0), 2) AS product_match_rate,
       ROUND(100.0 * n.total_category_matches / NULLIF(n.total_items_bought, 0), 2) AS category_match_rate,
       ROUND(n.random_item_rate * 100, 2) AS random_item_baseline_pct
FROM {prefix}dash_testset_numbers n
JOIN {prefix}global_session_filter s ON n.session_id = s.session_id
ORDER BY s.session_rnk ASC
```

---

## Join Relationships

```
{prefix}global_session_filter.session_id  -->  {prefix}dash_model_param_stats_agg.session_id
{prefix}global_session_filter.session_id  -->  {prefix}dash_testset_numbers.session_id      (testset only)
{prefix}global_session_filter.session_id  -->  {prefix}dash_testset.session_id              (testset only)
```

`dash_final_recs_stats_daily`, `dash_most_ordered_items`, `dash_item_category_mapping_agg`, and `dash_similarity_stats_agg` are filtered by `event_date` (use `MAX(event_date)` for the latest run).

---

## Data Quality Notes

- **Table names use the configured `prefix`** — if the customer's `params.yml` uses `prefix: client_nbp_`, all table names are `client_nbp_dash_*`. Always confirm the prefix before querying.
- **`session_rnk = 1` is always the latest run** — prefer this over `MAX(session_id)` for clarity.
- **`model_params` is a JSON string** — parse it to extract `model_type`, `automl_model_type`, and tuning params. Don't assume the engine from context alone.
- **Testset tables may not exist** — check with `SHOW TABLES` before querying; don't assume they're present.
- **`dash_similarity_stats_agg` is hive-only** — for automl runs this table will be empty or absent.
- **`time` is UNIX bigint** — show with `TD_TIME_FORMAT(time, 'yyyy-MM-dd HH:mm', 'UTC')`.
- **`event_date` vs `session_id`** — `dash_final_recs_stats_daily` and item tables are filtered by `event_date` (varchar), not `session_id`. Use `MAX(event_date)` for the latest run in those tables.
