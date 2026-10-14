# Data Dictionary — Classification Model Output Tables

## Read description of available tables/columns before doing any analysis

All tables are in the **${sink_database}** database. Table names use the configured prefix (`${table_prefix}`, may be empty).

> **Profile identifier portability:** Dashboard queries use run-level aggregates and do not require an individual ID. For row-level analysis (`predictions`, `test_predictions`, or `prediction_shap`), first run `DESCRIBE ${sink_database}.${table_prefix}predictions` (or inspect the workflow user-ID parameter). The deployed output may expose `user_id`, while the originating source can use `td_consumer_id`, `canonical_id`, `cdp_profile_id`, or another configured identifier. Never copy an identifier name from a generic example without checking the customer schema.

> **⚠️ Column names and types below reflect the ACTUAL deployed schema (verified against a live `fde-classify` run), not the naming convention originally assumed by this doc.** There is no `test_`/`train_` prefix on metric columns, and most metric columns are already numeric (`double`/`bigint`), not `varchar`. Always run `DESCRIBE ${sink_database}.${table_prefix}<table>` (or the agent's `list_columns()` tool) before writing a query if you have any doubt — table-generation logic can change between template versions.

> **⚠️ Metric scale is NOT uniform within `run_log`/`train_run_log`.** `precision`, `recall`, `fbeta`, `test_accuracy` are on a **0–1** scale. `f1_score`, `auc_roc`, `aucpr` are on a **0–100** scale (i.e. already multiplied by 100). Never plot these two groups on the same axis without rescaling one of them (divide the 0–100 group by 100, or multiply the 0–1 group by 100) — a naive chart will show a bar at "90" (auc_roc) next to a bar at "0.66" (precision) as if they were comparable.

---

## Table 1: {tp}run_log
**Purpose:** One row per training run — test-set metrics, classification threshold, best hyperparameters, and run metadata. The primary model quality indicator.

| Column Name | Data Type | Scale | Description |
|------------|-----------|-------|-------------|
| `session_id` | bigint | — | Training run identifier |
| `model_type` | varchar | — | Algorithm used (logistic, xgboost, catboost) |
| `best_threshold` | double | 0–1 | Optimal classification threshold |
| `precision` | double | 0–1 | Precision on held-out test set |
| `recall` | double | 0–1 | Recall on held-out test set |
| `f1_score` | double | **0–100** | F1 score on test set |
| `fbeta` | double | 0–1 | F-beta score on test set (weighted by fbeta_beta) |
| `fbeta_beta` | double | — | The fbeta_beta value used for this run |
| `auc_roc` | double | **0–100** | Area under ROC curve (ranking quality) |
| `aucpr` | double | **0–100** | Area under precision-recall curve |
| `test_accuracy` | double | 0–1 | Overall accuracy |
| `true_negatives` | bigint | — | True negatives count |
| `false_positives` | bigint | — | False positives count |
| `false_negatives` | bigint | — | False negatives count |
| `true_positives` | bigint | — | True positives count |
| `confusion_matrix` | varchar | — | JSON string of the confusion matrix |
| `test_samples` | bigint | — | Held-out test set row count |
| `total_features` | bigint | — | Number of features used by the model |
| `train_shape` | varchar | — | Training set shape, e.g. "(700, 43)" |
| `test_shape` | varchar | — | Test set shape |
| `train_target_dist` | varchar | — | Training class distribution, e.g. "{0: 615, 1: 85}" |
| `test_target_dist` | varchar | — | Test class distribution |
| `best_params` | varchar | — | JSON string of best hyperparameters found |
| `description` | varchar | — | Run description from config |
| `psi` | double | — | (present but populated at prediction time, not training) |
| `evaluation_note` | varchar | — | e.g. "precision_optimal threshold applied" |
| `time` | bigint | — | Unix epoch seconds — **the only timestamp column on this table** (no `created_at` / `run_timestamp`) |

**Usage:** Always use `MAX(session_id)` to get the latest training run. Do NOT `CAST` these columns — they are already numeric. To get a human-readable run date, use `TD_TIME_FORMAT(time, 'yyyy-MM-dd HH:mm', 'UTC')`.

---

## Table 2: {tp}train_run_log
**Purpose:** One row per training run — train-set metrics. **Same column names as `run_log`** (no `train_` prefix) — the table itself, not the column name, tells you it's the train-set view. JOIN on `session_id` and alias columns to disambiguate.

| Column Name | Data Type | Scale | Description |
|------------|-----------|-------|-------------|
| `session_id` | bigint | — | Training run identifier (matches run_log) |
| `auc_roc` | double | **0–100** | AUC-ROC on training set |
| `fbeta` | double | 0–1 | F-beta on training set |
| `precision` | double | 0–1 | Precision on training set |
| `recall` | double | 0–1 | Recall on training set |
| `time` | bigint | — | Unix epoch seconds |

(Remaining columns mirror `run_log`'s schema.)

**Usage:** JOIN with `run_log` on `session_id`, e.g.:
```sql
SELECT r.session_id,
       t.auc_roc AS train_auc_roc, r.auc_roc AS test_auc_roc,
       t.fbeta   AS train_fbeta,   r.fbeta   AS test_fbeta
FROM ${sink_database}.${table_prefix}run_log r
JOIN ${sink_database}.${table_prefix}train_run_log t ON r.session_id = t.session_id
WHERE r.session_id = (SELECT MAX(session_id) FROM ${sink_database}.${table_prefix}run_log)
```
Gap > 0.10 in AUC-ROC (after rescaling to the same 0–1 or 0–100 basis) or > 0.15 in F-beta suggests overfitting.

---

## Table 3: {tp}feature_importance
**Purpose:** SHAP-based feature importance — mean absolute SHAP value per feature. Shows which features matter most globally.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `feature_name` | varchar | Feature column name |
| `mean_abs_shap_value` | double | Mean absolute SHAP value (importance magnitude) — **note: `mean_abs_shap_value`, not `mean_abs_shap`** |
| `rank` | bigint | Importance rank (1 = most important) |
| `session_id` | bigint | Training run identifier |
| `created_at` | varchar | Timestamp string (this table DOES have `created_at`, unlike `run_log`) |
| `time` | bigint | Unix epoch seconds |

**Usage:** `ORDER BY mean_abs_shap_value DESC` (already `double`, no CAST needed) or `ORDER BY rank ASC`. Filter by latest `session_id`.

---

## Table 4: {tp}shap_directional
**Purpose:** For each feature, whether higher values push the prediction score up or down, and with what confidence.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `feature_name` | varchar | Feature column name |
| `mean_shap` | double | Mean SHAP value (signed — positive = increases score) |
| `mean_abs_shap` | double | Mean absolute SHAP value (this table DOES use the `mean_abs_shap` name, unlike `feature_importance`'s `mean_abs_shap_value`) |
| `median_shap` | double | Median SHAP value |
| `shap_std` | double | Standard deviation of SHAP values |
| `pct_pushing_up` | double | % of samples where feature increases score (0–100 scale) |
| `pct_pushing_down` | double | % of samples where feature decreases score (0–100 scale) |
| `direction` | varchar | 'increases score', 'decreases score', 'mixed / non-monotonic', 'weakly directional' |
| `direction_confidence` | double | Confidence in direction assignment (0–1) |
| `pearson_value_vs_shap` | double | Correlation between feature value and SHAP value |
| `rank` | bigint | Importance rank |
| `session_id` | bigint | Training run identifier |
| `created_at` | varchar | Timestamp string |
| `time` | bigint | Unix epoch seconds |

**Usage:** Shows not just which features matter (importance) but HOW they affect the score (direction). Use for business explanations like "more website visits → higher conversion score". Note `feature_importance.mean_abs_shap_value` and `shap_directional.mean_abs_shap` are the same underlying metric under two different column names — do not assume they're interchangeable by name when writing a JOIN; join on `feature_name` + `session_id` instead.

---

## Table 5: {tp}test_predictions
**Purpose:** Row-level predictions on the held-out test set with actual labels and outcome classification.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `session_id` | bigint | Training run identifier |
| `user_id` | varchar | Record identifier (from user_id_col) |
| `predicted_proba` | double | Predicted probability (0.0–1.0) |
| `predicted_label` | bigint | Binary label (0 or 1, based on threshold) |
| `actual_label` | bigint | True label from training data |
| `threshold_used` | double | Threshold applied |
| `is_correct` | bigint | 1 if predicted_label == actual_label, else 0 |
| `outcome_class` | varchar | TP, TN, FP, or FN |
| `score_bucket` | varchar | Score bucket label |
| `created_at` | varchar | Timestamp string |
| `time` | bigint | Unix epoch seconds |

**Usage:** Use for confusion matrix analysis, threshold sensitivity analysis, and identifying misclassified records.

---

## Table 6: {tp}predictions
**Purpose:** Main prediction output — one row per scored record with probability score, predicted label, and score bucket.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `pred_session_id` | bigint | Prediction run identifier |
| `train_session_id` | bigint | The training session this prediction run scored against |
| `model_type` | varchar | Algorithm used |
| `model_session_id` | bigint | Session ID of the model artifact loaded from model store |
| `user_id` | varchar | Record identifier |
| `lead_score` | double | Predicted probability (0.0–1.0) |
| `predicted_label` | bigint | Binary label (0 or 1) — **⚠️ see the threshold-lookup caveat in `business-context.md`; this may not reflect the trained `best_threshold` if the deployment hit the known `predictor.py` threshold-fallback bug. When in doubt, recompute as `lead_score >= <best_threshold from run_log>` instead of trusting this column.** |
| `threshold_applied` | double | Threshold actually used to compute `predicted_label` for this run — compare against `run_log.best_threshold` to detect the fallback-to-0.5 bug |
| `score_bucket` | varchar | Score bucket label (also threshold-independent — this is a raw score-range bucket, unaffected by the predicted_label bug) |
| `prediction_timestamp` | varchar | Timestamp string |
| `time` | bigint | Unix epoch seconds |

**Usage:** This is the main output table for downstream consumption (marketing, sales, audience creation). Filter by latest `pred_session_id`. Always cross-check `threshold_applied` against the training run's `best_threshold` before trusting `predicted_label` at face value.

---

## Table 7: {tp}prediction_shap
**Purpose:** Per-record top-N SHAP features — the top features pushing each record's score up and down. Long format (one row per record × feature).

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `pred_session_id` | bigint | Prediction run identifier |
| `train_session_id` | bigint | Training session the model came from |
| `model_type` | varchar | Algorithm used |
| `user_id` | varchar | Record identifier |
| `lead_score` | double | This record's predicted probability |
| `feature_name` | varchar | Feature name |
| `feature_value` | double | Feature value for this record |
| `shap_value` | double | SHAP contribution (positive = pushes score up) |
| `direction` | varchar | `'positive'` or `'negative'` (lowercase, no "score" suffix — differs from `shap_directional.direction`'s longer strings) |
| `rank_within_direction` | bigint | Rank (1 = most impactful in this direction) |
| `top_n_per_direction` | bigint | The configured `shap_topn_per_direction` value for this run |
| `created_at` | varchar | Timestamp string |
| `time` | bigint | Unix epoch seconds |

**Usage:** Only computed for records predicted as positive (above threshold). Use to explain individual predictions — "why does this record score high?" JOIN to `predictions` on `user_id` + `pred_session_id` for the overall score alongside the per-feature drivers.

---

## Table 8: {tp}prediction_run_log
**Purpose:** Audit row per prediction run — records scored, score statistics, PSI drift metric.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `pred_session_id` | bigint | Prediction run identifier |
| `train_session_id` | bigint | Training session this run scored against |
| `model_type` | varchar | Algorithm used |
| `records_scored` | bigint | Number of records scored |
| `data_shape` | varchar | Shape of the scored data, e.g. "(1000, 43)" |
| `score_min` | double | Minimum score |
| `score_max` | double | Maximum score |
| `score_mean` | double | Mean prediction score |
| `score_median` | double | Median prediction score |
| `score_std` | double | Score standard deviation |
| `threshold_applied` | double | Classification threshold actually applied (compare against `run_log.best_threshold`) |
| `predicted_positive` | bigint | Count of records with `predicted_label = 1` |
| `predicted_negative` | bigint | Count of records with `predicted_label = 0` |
| `psi` | double | Population Stability Index (drift from training) |
| `total_features` | bigint | Feature count |
| `run_timestamp` | varchar | Timestamp string — **this table DOES have `run_timestamp`; `run_log` does NOT** (do not assume the two tables share a timestamp column name) |
| `time` | bigint | Unix epoch seconds |

**Usage:** Monitor PSI across prediction runs. PSI < 0.10 = stable, 0.10–0.25 = monitor, > 0.25 = retrain. Also use `threshold_applied` here (and on `predictions`) to detect the fallback-to-0.5 threshold bug by comparing against `run_log.best_threshold` for the matching `train_session_id`.

---

## Table 9: {tp}roc_curve
**Purpose:** ROC curve data points — false positive rate vs true positive rate at each threshold.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `session_id` | bigint | Training run identifier |
| `fpr` | double | False positive rate |
| `tpr` | double | True positive rate |
| `threshold` | double | Classification threshold at this point |
| `created_at` | varchar | Timestamp string |
| `time` | bigint | Unix epoch seconds |

**Usage:** Plot ROC curve. AUC = area under this curve (should match `run_log.auc_roc` / 100).

---

## Table 10: {tp}prediction_bins / {tp}probability_train_bins
**Purpose:** Score distribution histogram — count of records in each score bin.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `session_id` (train bins) / `pred_session_id` (prediction bins) | bigint | Run identifier |
| `bin_range` | varchar | Score range, e.g. "0.0-0.1" |
| `count` | bigint | Number of records in this bin |
| `percentage` | double | Percentage of total records |
| `created_at` | varchar | Timestamp string |
| `time` | bigint | Unix epoch seconds |

`{tp}prediction_bins` additionally carries `pred_session_id` + `train_session_id` + `source` columns; `{tp}probability_train_bins` uses `session_id` only.

**Usage:** Compare `probability_train_bins` (training) with `prediction_bins` (prediction) for visual drift detection.

---

## Table 11: {tp}feature_correlations
**Purpose:** Pairwise feature correlation matrix in long format.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `feature_a` | varchar | First feature name (not `feature_1`) |
| `feature_b` | varchar | Second feature name (not `feature_2`) |
| `correlation` | double | Pearson correlation coefficient |
| `abs_correlation` | double | Absolute value of the correlation |
| `session_id` | bigint | Training run identifier |
| `created_at` | varchar | Timestamp string |
| `time` | bigint | Unix epoch seconds |

---

## Table 12: {tp}target_correlations
**Purpose:** Feature-to-target correlation for each feature.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `feature` | varchar | Feature name (column is `feature`, not `feature_name`) |
| `target_correlation` | double | Pearson correlation with target variable |
| `abs_target_correlation` | double | Absolute value of the correlation |
| `rank` | bigint | Rank by absolute correlation |
| `session_id` | bigint | Training run identifier |
| `created_at` | varchar | Timestamp string |
| `time` | bigint | Unix epoch seconds |

---

## Table 13: {tp}optuna_trials
**Purpose:** Full Optuna hyperparameter search history — one row per trial. **There is no single `params` JSON column** — each hyperparameter is its own `params_*` column.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `number` | bigint | Optuna trial number (column is `number`, not `trial_number`) |
| `value` | double | Metric value achieved this trial |
| `datetime_start` / `datetime_complete` | varchar | Trial timing |
| `duration` | varchar | Trial duration |
| `params_colsample_bytree`, `params_gamma`, `params_learning_rate`, `params_max_depth`, `params_min_child_weight`, `params_n_estimators`, `params_reg_alpha`, `params_reg_lambda`, `params_subsample` | double/bigint | Individual XGBoost/CatBoost hyperparameters tried this trial (exact set may vary by `model_type`) |
| `state` | varchar | e.g. "COMPLETE" |
| `session_id` | bigint | Training run identifier |
| `created_at` | varchar | Timestamp string |
| `time` | bigint | Unix epoch seconds |

**Usage:** `ORDER BY value DESC` to see the best trials. Scatter plot `number` (x) vs `value` (y) to visualize the search. Helps assess whether more trials would improve results.

---

## Tables that may NOT exist for this deployment (model-type-dependent)

`{tp}coefficient`, `{tp}scaler_params`, and `{tp}vif_scores` are only written when `model_type = 'logistic'`. **Before referencing any of these three in a knowledge base or a query, confirm they exist** (`SHOW TABLES` / `list_columns()` / a quick `DESCRIBE`) — for `xgboost`/`catboost` deployments they are simply absent, and a knowledge-base config that lists them anyway will break every query that auto-generates a CTE across the full table list. Prefer `{tp}feature_importance` + `{tp}shap_directional` + `{tp}xgb_gain_importance` (xgboost) / `{tp}cb_gain_importance` (catboost) for feature-driver questions on tree models instead.

---

## Cross-Table Analysis Patterns

### Model Performance Dashboard
Combine `run_log` (metrics), `feature_importance` (top features), `prediction_bins` (score distribution), and `prediction_run_log` (PSI) for a comprehensive model health check.

### Overfitting Detection
JOIN `run_log` and `train_run_log` on `session_id`. Compare `auc_roc` (rescale consistently — both are 0–100 on these two tables) and `fbeta` (both 0–1). Gap > 0.10 in AUC-ROC (on a common 0–1 basis) or > 0.15 in F-beta = overfitting concern.

### Individual Record Explanation
JOIN `predictions` and `prediction_shap` on `user_id` and `pred_session_id` to get both the score and the top SHAP drivers for a specific record.

### Drift Monitoring Over Time
Query `prediction_run_log` for PSI across multiple `pred_session_id` values. Trend PSI over time to detect gradual drift before it crosses the 0.25 threshold.

### Feature Deep Dive
Combine `feature_importance` (how much), `shap_directional` (which direction), `target_correlations` (raw correlation), and — only if the model is logistic and the table exists — `vif_scores` (multicollinearity) for a complete feature profile.

---

## Data Quality Notes

**Column types:** Metric columns observed in this deployment were already `double`/`bigint` in TD, not `varchar` — a `CAST` is harmless but unnecessary. Always confirm actual types with `DESCRIBE` rather than assuming; table-generation code has changed between template versions and may differ again.

**Timestamp columns are inconsistent across tables.** `run_log` and `train_run_log` have ONLY `time` (unix epoch seconds) — no `created_at`, no `run_timestamp`. Most other tables (`feature_importance`, `shap_directional`, `test_predictions`, `roc_curve`, bins tables, correlation tables, `optuna_trials`) have BOTH `created_at` (a formatted timestamp string) and `time` (unix epoch). `prediction_run_log` uniquely has `run_timestamp` instead of `created_at`. When you need a human-readable run date and the table lacks `created_at`, derive it from `time` with `TD_TIME_FORMAT(time, 'yyyy-MM-dd HH:mm', 'UTC')`. Never assume a timestamp column name exists on a given table without checking first.

**Session ID as run tracker:** Every training run produces a unique `session_id`; every prediction run produces a unique `pred_session_id`. Both come from digdag's `${session_id}` built-in variable for that workflow run (see the workflow's `yaml_structure.md` "Session ID Tracking") — they are unrelated to any web/browsing session ID column that might exist in a raw feature source table. Use `MAX()` to get the latest.

**SHAP computation scope:** Per-row SHAP (`prediction_shap`) is only computed for records predicted as positive (above threshold). Records predicted negative do not have SHAP rows.

**Known threshold-fallback bug:** In some `fde-classify` deployments, the prediction pipeline's threshold-lookup query fails silently (referencing a column that doesn't exist on `run_log`) and falls back to a hardcoded threshold of `0.5` instead of the trained `best_threshold`. This makes `predictions.predicted_label` / `score_bucket` unreliable. Always sanity-check by comparing `predictions.threshold_applied` (or `prediction_run_log.threshold_applied`) against `run_log.best_threshold` for the matching training session — if they differ, recompute "predicted positive" as `lead_score >= <run_log.best_threshold>` rather than trusting `predicted_label`.
