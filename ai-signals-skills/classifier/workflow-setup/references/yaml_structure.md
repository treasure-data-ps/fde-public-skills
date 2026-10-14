# Binary Classification — Configuration Structure

This document explains the complete structure of the `config.yml` file and all parameters in `train.dig` and `predict.dig` for the Classification workflow.

## Complete Template

```yaml
#####################################################################
########################## CORE SETTINGS ###########################
#####################################################################
sink_database: lead_scoring               # TD database for all output tables
td_endpoint: 'https://api.treasuredata.com'  # TD API endpoint
user_id_col: 'ucp_id'                    # Unique record identifier column
description: 'initial model run'          # Logged with each run for tracking

#####################################################################
##################### TRAINING TIME WINDOW #########################
#####################################################################
look_back_months_training: 27             # Months of history for training features
train_end_months_from_now: 2              # Gap before now to avoid label leakage
look_back_months_prediction: 12           # History window for prediction features

#####################################################################
##################### OUTPUT TABLE PREFIX ##########################
#####################################################################
table_prefix: ''                          # Empty = generic names; 'lead_scoring_' = prefixed names

#####################################################################
##################### MODEL SELECTION ##############################
#####################################################################
model_type: 'xgboost'                    # logistic | xgboost | catboost
model_store_table: 'ml_model_store'       # TD table for tree model binaries
model_name: 'scorer_xgb'                  # Name tag for model store lookup

#####################################################################
##################### TUNING PARAMETERS ############################
#####################################################################
fbeta_beta: '0.7'                        # F-beta weight (<1=precision, 1.0=F1, >1=recall)
n_trials: '30'                           # Optuna search iterations
corr_threshold: '0.90'                   # Drop features with correlation above this
min_metric_floor: '0.35'                 # Safety floor (auto-selects recall or precision)

#####################################################################
##################### TUNING STRATEGY ##############################
#####################################################################
optuna_metric: 'fbeta'                   # Metric Optuna maximizes
threshold_strategy: 'precision_optimal'   # How the classification threshold is chosen
fixed_threshold: '0.5'                   # Used only when threshold_strategy = 'fixed'
cv_folds: '3'                            # Stratified CV folds (2-10)
early_stopping_rounds: '0'              # Early stopping for tree models (0=disabled)
class_balance_strategy: 'balanced'        # balanced | none
xgb_eval_metric: 'aucpr'                # Eval metric during training
```

## Parameter Reference

### Core Settings

| Parameter | Type | Description | Example Values |
|-----------|------|-------------|----------------|
| `sink_database` | string | TD database for all output tables | `lead_scoring`, `analytics_prod` |
| `td_endpoint` | string | TD API endpoint | `https://api.treasuredata.com` (US), `https://api.treasuredata.co.jp` (JP) |
| `user_id_col` | string | Column uniquely identifying each record | `ucp_id`, `customer_id`, `lead_id` |
| `description` | string | Run description for audit trail | `'initial model run'`, `'v2 with new features'` |

### Training Time Window

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `look_back_months_training` | integer | Months of history for training features | `27` |
| `train_end_months_from_now` | integer | Gap before now to prevent label leakage | `2` |
| `look_back_months_prediction` | integer | History window for prediction features | `12` |

**How the training window is computed:**
- **Start date**: `session_time - look_back_months_training` (e.g., 27 months ago)
- **End date**: `session_time - train_end_months_from_now` (e.g., 2 months ago)

The gap between end date and now ensures that recent outcomes (which may not be finalized) don't leak into training labels.

### Output Table Prefix

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `table_prefix` | string | Prefix for all output table names | `''` (empty) or `'lead_scoring_'` |

When `table_prefix: ''`, output tables are named `run_log`, `predictions`, `feature_importance`.
When `table_prefix: 'lead_scoring_'`, they become `lead_scoring_run_log`, `lead_scoring_predictions`, etc.
Must end with `_` if non-empty.

### Model Selection

| Parameter | Type | Description | Options |
|-----------|------|-------------|---------|
| `model_type` | string | Classification algorithm | `logistic`, `xgboost`, `catboost` |
| `model_store_table` | string | TD table for tree model binaries | `ml_model_store` |
| `model_name` | string | Name tag for model lookup | `scorer_xgb`, `churn_model_v1` |

**Model comparison:**

| Aspect | Logistic Regression | XGBoost | CatBoost |
|--------|-------------------|---------|----------|
| NaN handling | Imputed (median) | Native (learned split direction) | Native (nan_mode=Min) |
| Feature scaling | StandardScaler required | None needed | None needed |
| Model storage | Coefficient table in TD | td-model-store binary blob | td-model-store binary blob |
| SHAP explainer | LinearExplainer (fast) | TreeExplainer (fast) | TreeExplainer (fast) |
| Interpretability | Highest (coefficients) | High (SHAP + gain) | High (SHAP + importance) |
| Best for | Simple/linear data, small feature sets | Most tabular data (recommended default) | High-cardinality categorical features |

### Tuning Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `fbeta_beta` | float | F-beta weight controlling precision/recall tradeoff | `0.7` |
| `n_trials` | integer | Optuna hyperparameter search budget | `30` |
| `corr_threshold` | float | Correlation threshold for feature deduplication | `0.90` |
| `min_metric_floor` | float | Safety floor for threshold selection | `0.35` |

### Tuning Strategy

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `optuna_metric` | string | Metric Optuna optimizes | `fbeta` |
| `threshold_strategy` | string | How classification threshold is selected | `precision_optimal` |
| `fixed_threshold` | float | Fixed threshold value (only when strategy=fixed) | `0.5` |
| `cv_folds` | integer | Cross-validation folds in Optuna | `3` |
| `early_stopping_rounds` | integer | Early stopping for tree models (0=disabled) | `0` |
| `class_balance_strategy` | string | Class imbalance handling | `balanced` |
| `xgb_eval_metric` | string | Eval metric during tree model training | `aucpr` |

### Training-Specific Settings (in `train.dig` `_env`)

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `target_variable` | string | Binary 0/1 target column name | `app_conversion` |
| `test_size` | float | Fraction held out for evaluation | `0.3` |
| `columns_to_drop` | string | Comma-separated non-feature columns to exclude | `web_session_id,batch_id,...` |
| `session_id` | string | The run identifier written to `{tp}run_log` / `{tp}train_run_log` / etc. — set from digdag's `${session_id}` built-in variable, not generated by the Python pipeline. See "Session ID Tracking" below. | `${session_id}` |
| `shap_max_samples` | integer | SHAP computation sample size | `20000` |
| `shap_interactions_enabled` | boolean | Pairwise SHAP interactions (expensive) | `false` |
| `write_concurrency` | integer | Parallel TD write threads | `6` |

### Prediction-Specific Settings (in `predict.dig` `_env`)

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `pred_session_id` | string | The run identifier written to `{tp}predictions` / `{tp}prediction_shap` / `{tp}prediction_run_log` — set from digdag's `${session_id}` built-in variable (same mechanism as training, in the prediction attempt). See "Session ID Tracking" below. | `${session_id}` |
| `shap_topn_per_direction` | integer | Top N positive + N negative SHAP drivers per record | `5` |
| `shap_max_rows` | integer | Max rows for SHAP computation (0=all) | `0` |
| `write_concurrency` | integer | Parallel TD write threads | `4` |

### Session ID Tracking

Every output table's `session_id` (training) or `pred_session_id` (prediction) column is populated from digdag's **`${session_id}`** built-in variable — the integer session ID digdag assigns to that specific workflow run. This is not something the Python pipeline generates on its own; it must be passed in explicitly.

Wire it through in `train.dig` and `predict.dig` via `_env`:

```yaml
# train.dig
_env:
  session_id: ${session_id}
  target_variable: 'app_conversion'
  columns_to_drop: >-
    web_session_id,batch_id,reference_date,ucp_id,time
  # ... other _env settings

# predict.dig
_env:
  pred_session_id: ${session_id}
  # ... other _env settings
```

Because `${session_id}` is unique per digdag run, re-running `train.dig` produces a new `session_id` in `{tp}run_log` (and every other training output table) without overwriting the previous run's row — this is what lets `eval.md`'s validation queries and the insights agent compare metrics across retraining runs with `MAX(session_id)` / `ORDER BY session_id DESC`. The same applies to `pred_session_id` across prediction runs.

**Naming collision to watch for:** `session_id` here refers to the **digdag workflow run** — do not confuse it with a raw feature-table column also named `session_id` that represents a **web/browsing session** (e.g., from pageview tracking). If a source table has its own `session_id` column, treat it like any other non-predictive ID column — it belongs in `columns_to_drop`. To avoid ambiguity in data prep SQL, consider aliasing a raw table's session column (e.g., `web_session_id`) before it reaches the final features table, since both concepts can otherwise coexist under the same name.

### XGBoost / CatBoost Tuning Ranges (in `train.dig` `_env`)

These control Optuna's search space for tree model hyperparameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `n_estimators_min` / `n_estimators_max` | Boosting rounds range | `50` – `700` |
| `max_depth_min` / `max_depth_max` | Tree depth range | `3` – `10` |
| `learning_rate_min` / `learning_rate_max` | Learning rate range (log-uniform) | `0.01` – `0.5` |

Additional hyperparameters (subsample, colsample_bytree, min_child_weight, reg_alpha, reg_lambda, gamma) are tuned by Optuna with fixed ranges inside `models.py`.

## Output Tables

All output tables are prefixed with `{table_prefix}` (empty by default).

### Training Outputs

| Table | Description |
|-------|-------------|
| `{tp}run_log` | Test-set metrics, threshold, best hyperparameters per training run |
| `{tp}train_run_log` | Train-set metrics (compare with test for overfitting check) |
| `{tp}feature_list` | Ordered feature names used by the model |
| `{tp}feature_importance` | SHAP-based feature importance (magnitude ranking) |
| `{tp}shap_directional` | SHAP direction per feature (pushes score up vs. down) |
| `{tp}shap_interactions` | Top feature pairs by interaction strength (if enabled) |
| `{tp}roc_curve` | ROC curve data points |
| `{tp}prediction_bins` | Score distribution histogram (test set) |
| `{tp}probability_train_bins` | Training score bins (baseline for PSI drift detection) |
| `{tp}test_predictions` | Row-level test-set predictions with outcome class (TP/TN/FP/FN) |
| `{tp}vif_scores` | Variance Inflation Factor per feature |
| `{tp}feature_correlations` | Pairwise feature correlation matrix |
| `{tp}target_correlations` | Feature-to-target correlations |
| `{tp}corr_drop_report` | Which features were dropped for high correlation and why |
| `{tp}optuna_trials` | Full Optuna trial history (hyperparams, metric per trial) |
| `{tp}coefficient` | Logistic regression coefficients (logistic only) |
| `{tp}scaler_params` | StandardScaler mean/scale (logistic only) |
| `{tp}xgb_gain_importance` | Native XGBoost gain importance (xgboost only) |
| `{tp}cb_gain_importance` | Native CatBoost importance (catboost only) |
| `ml_model_store` | Model binary blob (xgboost/catboost via td-model-store) |

### Prediction Outputs

| Table | Description |
|-------|-------------|
| `{tp}predictions` | One row per scored record (user_id, lead_score, predicted_label, score_bucket) |
| `{tp}prediction_shap` | Per-record top-N SHAP drivers in long format (feature_name, shap_value, direction, rank) |
| `{tp}prediction_bins` | Prediction score distribution histogram |
| `{tp}prediction_run_log` | Run audit row (records_scored, score_min/max/mean/median, PSI, threshold) |
