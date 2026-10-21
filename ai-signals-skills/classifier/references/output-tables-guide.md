# Classifier — Output Tables Guide

Every table the workflow writes, its columns and the query that reads it. Read it when validating a run beyond `workflow-setup.md` §4, writing the agent's data dictionary, building the dashboard, or answering "where is X stored?". `<db>` = `sink_database`, `<pred>` = `pred_output_table`.

## Rules for every query

1. **Every write appends** (except the input tables and `<pred>_latest`, replaced each run). Filter to one run — the latest by `time`: `WHERE time = (SELECT MAX(time) FROM <db>.<table>)`, or `session_id = (SELECT max_by(session_id, time) FROM <db>.<table>)` for multi-row runs.
2. **Train and predict have different `session_id`s** — each is the session of the run that built its input. There is no `train_session_id` / `pred_session_id` column, and predictions don't record which training run produced the model. Use each table's own latest run.
3. **No `model_name` column.** The `classifier_*` names are fixed, so one sink database holds one classifier project; two models trained into one database share these tables.
4. `time` (bigint, upload epoch seconds) is on every table — use it for run timestamps (`FROM_UNIXTIME(time)`). `created_at` / `prediction_timestamp` are strings.
5. `count` is a reserved word — quote it: `"count"`.
6. Row-level queries: always `ORDER BY` + `LIMIT`.
7. Metric scales: every run-log metric (`auc_roc`, `aucpr`, `f1_score`, `precision`, `recall`, `fbeta`, `test_accuracy`) is 0–1; the ROC `fpr` / `tpr` and the `percentage` columns are 0–100.
8. Artifacts describe the **evaluation model** (train / test split). The stored model is refit on all rows with the same `best_params` and `best_threshold`.

## Tables at a glance

| Written by | Table | Grain |
|---|---|---|
| `data_prep.dig` | `train_input_table`, `pred_input_table` | One row per entity per cutoff — replaced each run |
| `classifier_train` | `classifier_run_log`, `classifier_train_run_log` | One row per training run (test / train split) |
| | `classifier_feature_list`, `classifier_feature_importance`, `classifier_shap_directional`, `classifier_xgboost_gain_importance` / `classifier_catboost_gain_importance` | One row per feature per run |
| | `classifier_roc_curve`, `classifier_prediction_bins` | ROC points / 10 score bins per run |
| | `classifier_target_correlations`, `classifier_feature_correlations`, `classifier_vif_scores`, `classifier_corr_drop_report` | Numeric diagnostics per run (`corr_drop_report` only when features were dropped) |
| | `classifier_optuna_trials` | One row per search trial (only if `n_trials > 0`) |
| `classifier_predict` | `<pred>` (default `classifier_predictions`) | One row per scored entity per run — appended |
| `predict.dig` `+latest_scores` | `<pred>_latest` | The latest batch, one row per `user_id` — the Parent Segment attribute table |

`train_output_table` is required by the API but never written. The model itself is stored by the AI Signals service under `model_name`, not in TD.

## Training tables

### classifier_run_log — test-split metrics (1 row per run)

Columns: `session_id`, `model_type`, `test_accuracy`, `precision`, `recall`, `f1_score`, `fbeta`, `fbeta_beta`, `auc_roc`, `aucpr`, `best_threshold`, `true_negatives`, `false_positives`, `false_negatives`, `true_positives`, `confusion_matrix`, `test_samples`, `total_features`, `train_shape`, `test_shape`, `train_target_dist`, `test_target_dist`, `best_params`, `corr_threshold`, `min_metric_floor`, `optuna_metric`, `threshold_strategy`, `cv_folds`, `early_stopping_rounds`, `class_balance_strategy`, `eval_metric`, `log_likelihood_model`, `log_likelihood_null`, `chi_square`, `mcfadden_r2`, `cox_snell_r2`, `psi`, `time`.
`psi` = train-vs-test score PSI. `model_type` is the source of truth for the model family.

```sql
SELECT session_id, model_type, auc_roc, aucpr, precision, recall, f1_score, fbeta, best_threshold, psi,
       true_positives, false_positives, false_negatives, true_negatives, test_samples, FROM_UNIXTIME(time) AS run_time
FROM <db>.classifier_run_log
WHERE time = (SELECT MAX(time) FROM <db>.classifier_run_log)
```

### classifier_train_run_log — train-split metrics (same schema)

`test_accuracy` / `test_samples` hold **train** values; `psi` is NULL. A gap above ~0.05 AUC or ~0.1 F-beta against `classifier_run_log` = overfitting.

```sql
SELECT 'test' AS split, auc_roc, precision, recall, fbeta FROM <db>.classifier_run_log
WHERE time = (SELECT MAX(time) FROM <db>.classifier_run_log)
UNION ALL
SELECT 'train', auc_roc, precision, recall, fbeta FROM <db>.classifier_train_run_log
WHERE time = (SELECT MAX(time) FROM <db>.classifier_train_run_log)
```

### classifier_feature_list — features used by the model

Columns: `session_id`, `feature_name`, `feature_index`, `created_at`.

```sql
SELECT feature_index, feature_name FROM <db>.classifier_feature_list
WHERE session_id = (SELECT max_by(session_id, time) FROM <db>.classifier_feature_list)
ORDER BY feature_index
```

### classifier_feature_importance — SHAP mean |value|

Columns: `feature_name`, `mean_abs_shap_value`, `rank`, `session_id`, `created_at`.

```sql
SELECT feature_name, mean_abs_shap_value, rank FROM <db>.classifier_feature_importance
WHERE session_id = (SELECT max_by(session_id, time) FROM <db>.classifier_feature_importance)
ORDER BY rank LIMIT 15
```

### classifier_shap_directional — SHAP direction per feature

Columns: `feature_name`, `mean_shap`, `mean_abs_shap`, `median_shap`, `shap_std`, `pct_pushing_up`, `pct_pushing_down` (0–100), `direction_confidence` (0–1), `pearson_value_vs_shap`, `direction` (`increases score` | `decreases score` | `mixed / non-monotonic` | `weakly directional` | `neutral`), `rank`, `session_id`, `created_at`.

```sql
SELECT feature_name, mean_shap, pct_pushing_up, pct_pushing_down, direction, direction_confidence
FROM <db>.classifier_shap_directional
WHERE session_id = (SELECT max_by(session_id, time) FROM <db>.classifier_shap_directional)
ORDER BY rank LIMIT 15
```

### classifier_xgboost_gain_importance / classifier_catboost_gain_importance — native importance

Columns: `feature_name`, `importance`, `rank`, `session_id`, `created_at`. Query the table matching `model_type` in `classifier_run_log` — the catboost table exists only after a catboost run.

```sql
SELECT feature_name, importance, rank FROM <db>.classifier_xgboost_gain_importance
WHERE session_id = (SELECT max_by(session_id, time) FROM <db>.classifier_xgboost_gain_importance)
ORDER BY rank LIMIT 15
```

### classifier_roc_curve — ROC points (test split)

Columns: `session_id`, `fpr`, `tpr` (0–100), `threshold`, `created_at`.

```sql
SELECT fpr, tpr, threshold FROM <db>.classifier_roc_curve
WHERE session_id = (SELECT max_by(session_id, time) FROM <db>.classifier_roc_curve)
ORDER BY fpr, tpr
```

### classifier_prediction_bins — test-split score histogram

Columns: `session_id`, `bin_range` (`0.0-0.1` … `0.9-1.0`, all 10 present), `"count"`, `percentage` (0–100), `created_at`.

```sql
SELECT bin_range, "count", percentage FROM <db>.classifier_prediction_bins
WHERE session_id = (SELECT max_by(session_id, time) FROM <db>.classifier_prediction_bins)
ORDER BY bin_range
```

### Numeric diagnostics

| Table | Columns | Read as |
|---|---|---|
| `classifier_target_correlations` | `feature`, `target_correlation`, `abs_target_correlation`, `rank` | \|corr\| near 1 → check for leakage |
| `classifier_feature_correlations` | `feature_a`, `feature_b`, `correlation`, `abs_correlation` | Redundant pairs |
| `classifier_vif_scores` | `feature`, `vif` | VIF > 10 strong, 5–10 moderate multicollinearity |
| `classifier_corr_drop_report` | `kept_feature`, `dropped_feature`, `correlation` | Dropped above `corr_threshold`. Missing table = nothing dropped |

All also carry `session_id`, `created_at`, `time`.

```sql
SELECT feature, target_correlation, rank FROM <db>.classifier_target_correlations
WHERE session_id = (SELECT max_by(session_id, time) FROM <db>.classifier_target_correlations)
ORDER BY rank LIMIT 15
```

### classifier_optuna_trials — hyperparameter search

Columns: `number`, `value` (CV objective), `datetime_start`, `datetime_complete`, `duration`, `state` (`COMPLETE` | `PRUNED` | `FAIL`), `params_<name>` (one per searched hyperparameter — check `tdx describe` for the active model type), `session_id`, `created_at`. Not written when `n_trials = 0`.

```sql
SELECT number, value, state, params_max_depth, params_learning_rate, params_n_estimators
FROM <db>.classifier_optuna_trials
WHERE session_id = (SELECT max_by(session_id, time) FROM <db>.classifier_optuna_trials) AND state = 'COMPLETE'
ORDER BY value DESC LIMIT 10
```

## Prediction tables

### `<pred>` — per-entity scores, appended per run

Columns: `session_id`, `model_type`, `user_id` (always named `user_id`, whatever `user_id_column` is; its type follows the input), `score` (P(class = 1)), `predicted_label` (1 if `score >= threshold_applied`), `threshold_applied` (= `best_threshold`), `score_bucket` (`0.0-0.1` … `0.9-1.0`), `prediction_timestamp`, `time`. Large — always aggregate or `LIMIT`.

```sql
-- Latest run summary
SELECT session_id, COUNT(*) AS scored, SUM(predicted_label) AS predicted_pos,
       ROUND(AVG(score), 4) AS score_mean, APPROX_PERCENTILE(score, 0.5) AS score_median,
       MAX(threshold_applied) AS threshold
FROM <db>.<pred>
WHERE session_id = (SELECT max_by(session_id, time) FROM <db>.<pred>)
GROUP BY 1

-- Score distribution of the latest run
SELECT score_bucket, COUNT(*) AS cnt, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM <db>.<pred>_latest GROUP BY 1 ORDER BY 1

-- Scoring history
SELECT session_id, FROM_UNIXTIME(MIN(time)) AS scored_at, COUNT(*) AS scored,
       AVG(score) AS score_mean, AVG(CAST(predicted_label AS DOUBLE)) AS positive_rate
FROM <db>.<pred> GROUP BY 1 ORDER BY 2 DESC LIMIT 10
```

### `<pred>_latest` — the Parent Segment attribute table

Same columns as `<pred>`, the latest batch only, one row per `user_id`, replaced each scoring run. Use it for single-entity lookups, segments and the Parent Segment join (`parent_segment.md`).

```sql
SELECT user_id, score, predicted_label, threshold_applied, score_bucket
FROM <db>.<pred>_latest WHERE CAST(user_id AS VARCHAR) = '<id>'
```

### Drift — live scores vs the test split (PSI)

```sql
WITH t AS (
  SELECT bin_range, GREATEST(percentage / 100.0, 0.0001) AS e FROM <db>.classifier_prediction_bins
  WHERE session_id = (SELECT max_by(session_id, time) FROM <db>.classifier_prediction_bins)
), p AS (
  SELECT score_bucket AS bin_range, CAST(COUNT(*) AS DOUBLE) / SUM(COUNT(*)) OVER () AS a
  FROM <db>.<pred>_latest GROUP BY 1
), j AS (
  SELECT t.bin_range, t.e, GREATEST(COALESCE(p.a, 0), 0.0001) AS a FROM t LEFT JOIN p ON t.bin_range = p.bin_range
)
SELECT bin_range, ROUND(100 * e, 1) AS test_pct, ROUND(100 * a, 1) AS live_pct, SUM((a - e) * LN(a / e)) OVER () AS psi
FROM j ORDER BY bin_range
```

PSI bands: stable < 0.10, monitor 0.10–0.25, drift / retrain > 0.25. With `class_balance_strategy: balanced` the live distribution is shifted up for both — compare shapes, not levels. A changed population (e.g. stacked training cutoffs vs one scoring cutoff with a different mix) also moves it.

## Question → tables

| Question | Tables (query in parallel) |
|---|---|
| Model overview | `classifier_run_log` + `<pred>` latest summary |
| Top drivers | `classifier_feature_importance` + `classifier_shap_directional` |
| Score distribution | `<pred>_latest` (+ `classifier_prediction_bins` for test vs live) |
| ROC curve | `classifier_roc_curve` + `classifier_run_log.auc_roc` |
| Is the model drifting? | PSI query + `classifier_run_log.psi` |
| Train vs test / overfitting | `classifier_run_log` UNION ALL `classifier_train_run_log` |
| Trend across runs | `classifier_run_log` ordered by `time`; `<pred>` grouped by `session_id` |
| Correlations, multicollinearity | `classifier_target_correlations`, `classifier_feature_correlations`, `classifier_vif_scores`, `classifier_corr_drop_report` |
| Hyperparameter tuning | `classifier_optuna_trials` + `classifier_run_log.best_params` |
| Confusion matrix / errors | `classifier_run_log` (TP / FP / FN / TN) |
| Why did entity X score high / low | `<pred>_latest` (score vs threshold) + `classifier_shap_directional` (global drivers) |
| Label rate per snapshot | `train_input_table` grouped by `cutoff_date` |

**Not available:** per-entity SHAP, row-level test-set predictions, a prediction run log, a model-store table in TD. Say so plainly; for an entity explanation show its score and bucket against the threshold and the global SHAP drivers.
