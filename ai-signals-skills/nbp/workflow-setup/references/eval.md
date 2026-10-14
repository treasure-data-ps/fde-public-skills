# NBP — Workflow Output Validation

Run these checks after every workflow execution (Phase 3 minimal push and Phase 4 re-run). Use `tdx-skills:tdx-basic` to execute each query against `${sink_database}`.

---

## 1. Primary Output Table — `nbp_user_master`

**What it is:** Final per-profile recommendation table. One row per user with `nbp_1`, `nbp_2`, ... columns. This is the table joined to the Parent Segment in Audience Studio.

```sql
-- Row count and distinct user count
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT unique_user_id) AS distinct_users
FROM ${sink_database}.nbp_user_master;
```

**Pass criteria:**
- `total_rows > 0`
- `distinct_users` is in the same order of magnitude as the transaction table's unique user count (within ~20%)

```sql
-- Confirm recommendation columns exist and are non-null
SELECT
  COUNT(*) AS total,
  COUNT(CASE WHEN nbp_1 IS NOT NULL THEN 1 END) AS has_rec_1,
  COUNT(CASE WHEN nbp_2 IS NOT NULL THEN 1 END) AS has_rec_2,
  COUNT(CASE WHEN nb_category_1 IS NOT NULL THEN 1 END) AS has_category_1
FROM ${sink_database}.nbp_user_master;
```

**Pass criteria:** `nbp_1` and `nb_category_1` are non-null for the majority of users (>80%). Lower coverage indicates item info join issues or sparse interaction data.

```sql
-- Sample recommendations — confirm names and categories look correct
SELECT unique_user_id, nbp_1, nb_category_1, nbp_2, nb_category_2
FROM ${sink_database}.nbp_user_master
LIMIT 10;
```

**Pass criteria:** Item names are human-readable strings (not raw SKU IDs), categories match expected values from the catalog.

---

## 2. Session Filter — `nbp_global_session_filter`

**What it is:** Session index — one row per workflow run. `session_rnk = 1` is always the latest run.

```sql
SELECT session_id, session_rnk, run_time
FROM ${sink_database}.nbp_global_session_filter
ORDER BY session_rnk ASC
LIMIT 5;
```

**Pass criteria:** At least one row exists. `session_rnk = 1` corresponds to the most recent run.

---

## 3. Dashboard Table — `nbp_dash_model_param_stats_agg`

**What it is:** One row per run. Stores model config + coverage stats (users with recs, distinct items recommended, date range used, model parameters, exclusion filters).

```sql
SELECT session_id, users_with_recs, distinct_items_recommended, time_range_days, model_params, exclusion_filters
FROM ${sink_database}.nbp_dash_model_param_stats_agg
WHERE session_id = (SELECT session_id FROM ${sink_database}.nbp_global_session_filter WHERE session_rnk = 1);
```

**Pass criteria:**
- `users_with_recs` matches `distinct_users` in `nbp_user_master`
- `model_params` reflects the configured algorithm (e.g., `als`)
- `time_range_days` is consistent with `orders_lookback` setting (`0` = all history)

---

## 4. Dashboard Table — `nbp_dash_final_recs_stats_daily`

**What it is:** Daily recommendation distribution — user counts per item/category combination at each rank position.

```sql
SELECT event_date, nbp_1, nb_category_1, item_recs_combo, event_cnt
FROM ${sink_database}.nbp_dash_final_recs_stats_daily
WHERE session_id = (SELECT session_id FROM ${sink_database}.nbp_global_session_filter WHERE session_rnk = 1)
ORDER BY event_cnt DESC
LIMIT 20;
```

**Pass criteria:**
- Rows exist for the latest session
- Top recommended items look like real products (not NULLs or test SKUs)
- Distribution shows variety — no single item dominating >50% of all recommendations (unless `popular` algorithm)

---

## 5. Test Set Evaluation (when `run_model_test_set: yes`)

```sql
-- Check test set table exists and has results
SELECT COUNT(*) AS test_rows
FROM ${sink_database}.nbp_dash_testset_numbers;
```

```sql
-- Review precision/recall vs random baseline
SELECT *
FROM ${sink_database}.nbp_dash_testset_numbers
WHERE session_id = (SELECT session_id FROM ${sink_database}.nbp_global_session_filter WHERE session_rnk = 1);
```

**Pass criteria:** Model precision/recall should exceed the random baseline. If not, the catalog may be too small or interaction data too sparse for ALS — consider switching to `similar_to_latest` or `popular`.

---

## Common Failure Modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `nbp_user_master` is empty | Workflow failed mid-run or `sink_database` doesn't exist | Check attempt logs: `tdx wf attempt <id> logs` |
| Item names show as raw SKU IDs | Item info join failed — item ID mismatch between tables | Verify `original_item_info_table` and that item IDs match after VARCHAR cast |
| Very low `users_with_recs` vs transaction table | Sparse interaction data or ALS cold-start issue | Consider switching to `similar_to_latest` or `popular`; lower `als_sample_rate` threshold |
| `nbp_dash_model_param_stats_agg` has no rows | Dashboard step failed | Check for workflow errors in the `+nbp_dashboard` task |
| Recommendations all from one category | Narrow catalog or unbalanced training data | Review item category distribution; consider `filter_viewed: true` |
| Test set precision < random baseline | Too few items or too sparse interactions | Dataset may be too small for ALS; switch to `similar_to_latest` |

---

## After All Checks Pass — Record Results

Once validation passes (or known issues are documented), record the validation results, the TD workflow project name, and the push date in `agent_outputs/<customer_slug>/nbp/project_state.md` (see `../../../shared/project_state.md`).
