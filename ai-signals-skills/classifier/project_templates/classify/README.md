# Classify — Generic Binary Classification Workflow

A reusable Treasure Data (Digdag) workflow for training and scoring binary classification models.
Supports **Logistic Regression**, **XGBoost**, and **CatBoost** with Optuna hyperparameter tuning,
SHAP explainability, and parallel artifact writes.

## Use Cases

This workflow can be applied to any **binary classification** problem — any scenario where you
need to predict whether something will or will not happen. Prepare your data prep SQL, set the
target variable, and the pipeline handles the rest.

| Category | Use Case | Target Variable Example |
|----------|----------|------------------------|
| **Sales & Revenue** | Lead scoring / conversion prediction | `converted` (1 = won deal) |
| | Opportunity win/loss prediction | `deal_won` (1 = closed-won) |
| | Upsell / cross-sell propensity | `upsold` (1 = purchased upgrade) |
| | Quote acceptance prediction | `quote_accepted` (1 = accepted) |
| **Customer Retention** | Churn prediction | `churned` (1 = cancelled) |
| | Subscription renewal prediction | `renewed` (1 = renewed) |
| | Customer reactivation likelihood | `reactivated` (1 = came back) |
| | At-risk account identification | `at_risk` (1 = downgraded/complained) |
| **Marketing** | Campaign response prediction | `responded` (1 = clicked/converted) |
| | Email open/click prediction | `clicked` (1 = clicked CTA) |
| | Ad conversion prediction | `converted` (1 = completed action) |
| | Audience qualification scoring | `qualified` (1 = meets criteria) |
| **Product & Engagement** | Feature adoption prediction | `adopted` (1 = used feature) |
| | Trial-to-paid conversion | `converted_to_paid` (1 = subscribed) |
| | User activation prediction | `activated` (1 = completed onboarding) |
| | Power user identification | `is_power_user` (1 = high engagement) |
| **Risk & Compliance** | Fraud detection | `is_fraud` (1 = fraudulent) |
| | Credit default prediction | `defaulted` (1 = missed payment) |
| | Claim approval prediction | `approved` (1 = claim approved) |
| | Policy cancellation risk | `cancelled` (1 = cancelled policy) |
| **Operations** | Support ticket escalation | `escalated` (1 = needed escalation) |
| | SLA breach prediction | `breached` (1 = missed SLA) |
| | Employee attrition prediction | `left` (1 = resigned) |
| | Inventory stockout prediction | `stocked_out` (1 = went out of stock) |

> **Key requirement**: your target variable must be binary (0/1). For multi-class problems,
> train separate one-vs-rest models. For regression (predicting a continuous value), use a
> different workflow.

---

## Directory Structure

```
classify/
├── config.yml              # All tunable parameters (single source of truth)
├── classify.dig            # Top-level wrapper (optional)
├── train.dig               # Training workflow
├── predict.dig             # Prediction / scoring workflow
├── data_prep.dig           # Shared data prep (add your SQL steps here)
├── models.py               # Model classes (Logistic, XGBoost, CatBoost)
├── explainer.py            # SHAP, metrics, threshold selection
├── preprocessor.py         # One-hot encoding, imputation, correlation drop
├── parallel_writer.py      # Concurrent TD table writer
├── queries/
│   └── get_latest_batchids.sql
├── sql/                    # Put your data prep SQL files here
└── python/
    ├── train.py            # Training entry point (py>:)
    ├── predict_main.py     # Prediction entry point (py>:)
    ├── predictor.py        # Model loading + scoring logic
    └── data_handler.py     # TD read/write helper
```

---

## Quick Start

### 1. Set up `config.yml`

Open `config.yml` and configure:

```yaml
sink_database: your_database        # TD database for all output tables
td_endpoint: 'https://api.treasuredata.com'  # or .co.jp for JP region

user_id_col: 'your_id_column'       # Column that uniquely identifies each record
description: 'brief run description'
```

### 2. Add your data prep SQL

### 3. Run training: `digdag run train.dig`

### 4. Run prediction: `digdag run predict.dig`

---

## Data Prep Steps

Data prep is the **only part you must customize** for each use case. The workflow expects
a final features table named `{table_prefix}final_features_{mode}` (where `mode` is `train` or `pred`).

### Where to add data prep

There are three places to add SQL steps:

| File | When it runs | What to add |
|------|-------------|-------------|
| `train.dig` | Training only | Steps to build the training base table (must include a **target variable**) |
| `predict.dig` | Prediction only | Steps to build the prediction base table (no target needed) |
| `data_prep.dig` | Called from both | Shared feature engineering steps (called with `mode='train'` or `mode='pred'`) |

### Required final table schema

Your data prep must produce a table called `{table_prefix}final_features_{mode}` with:

| Column | Required | Description |
|--------|----------|-------------|
| `session_id` | Yes | Batch/session identifier (used to track runs) |
| `{user_id_col}` | Yes | Unique record identifier (set in config.yml) |
| `{target_variable}` | Training only | Binary target (0/1). Set in `train.dig` `_env` |
| Feature columns | Yes | All numeric/categorical features for the model |

### Example: Adding data prep to `train.dig`

```yaml
# Add these steps BEFORE +get_latest_batchid in train.dig:

+create_base_table:
  td>: sql/create_training_base.sql
  create_table: base_data_train

+create_feature_tables:
  call>: data_prep.dig

+create_final_features:
  td>: sql/join_final_features.sql
  create_table: ${table_prefix}final_features_${mode}
```

### Example: Adding shared features to `data_prep.dig`

```yaml
+create_features:
  _parallel: true

  +feature_set_1:
    td>: sql/features_behavioral.sql
    create_table: features_behavioral_${mode}

  +feature_set_2:
    td>: sql/features_demographic.sql
    create_table: features_demographic_${mode}
```

### Key rules for data prep

- Use `${mode}` suffix on intermediate tables to avoid train/pred collisions
- The final features table must have `session_id` for batch tracking
- Include `{user_id_col}` in the table — it gets auto-dropped before training
- For training, include the target variable column
- For prediction, do NOT include a target variable
- `columns_to_drop` in the dig `_env` section must list all non-feature columns
  (IDs, dates, metadata) so they don't leak into the model

---

## Model Parameters (`config.yml`)

### Core Settings

```yaml
sink_database: your_database         # TD database for output tables
td_endpoint: 'https://api.treasuredata.com'
user_id_col: 'your_id_column'        # Unique record ID column name
description: 'run description'       # Logged with each run for tracking
```

### Training Window

```yaml
look_back_months_training: 27        # How many months of history for training
train_end_months_from_now: 2         # Stop training data N months before now
                                     # (creates a gap to avoid label leakage)
look_back_months_prediction: 12      # History window for prediction features
```

The training window is computed as:
- **Start**: `session_time - look_back_months_training`
- **End**: `session_time - train_end_months_from_now`

### Output Table Prefix

```yaml
table_prefix: ''                     # Empty = generic names (run_log, predictions)
                                     # Set to e.g. 'lead_scoring_' for prefixed names
                                     # Must end with '_' if non-empty
```

When `table_prefix: ''`, output tables are named like `run_log`, `predictions`, `feature_importance`.
When `table_prefix: 'lead_scoring_'`, they become `lead_scoring_run_log`, `lead_scoring_predictions`, etc.

### Model Selection

```yaml
model_type: 'xgboost'               # Options: logistic | xgboost | catboost
model_store_table: 'ml_model_store'  # TD table for storing model binary (tree models)
model_name: 'my_model_xgb'          # Name tag in model store
```

| Parameter | logistic | xgboost | catboost |
|-----------|----------|---------|----------|
| NaN handling | Imputed (median) | Native (learned splits) | Native (nan_mode=Min) |
| Scaling | StandardScaler | None | None |
| Model storage | Coefficient table | td-model-store | td-model-store |
| SHAP explainer | LinearExplainer | TreeExplainer | TreeExplainer |

### Tuning Parameters

```yaml
# ── Shared across all model types ──
fbeta_beta: '0.7'                    # F-beta weight: <1 = precision-biased, >1 = recall-biased
n_trials: '30'                       # Number of Optuna trials (more = better search, slower)
corr_threshold: '0.90'              # Drop features with correlation above this
min_metric_floor: '0.35'            # Safety floor: auto-selects recall or precision based on fbeta_beta
```

**`fbeta_beta`** — Controls the precision/recall tradeoff in threshold selection:
- `0.5` = strongly precision-biased (fewer false positives)
- `0.7` = moderately precision-biased
- `1.0` = balanced (standard F1)
- `2.0` = recall-biased (fewer false negatives)

**`n_trials`** — Optuna hyperparameter search budget:
- `3-5` for quick tests
- `30-50` for production runs
- `100+` for thorough optimization

**`corr_threshold`** — Correlation-based feature deduplication:
- `0.80` = aggressive (drops more features, less multicollinearity)
- `0.90` = moderate (recommended for tree models)
- `0.95` = conservative (keeps most features)

**`min_metric_floor`** — Adaptive safety net for threshold selection. The pipeline
automatically decides what this floor protects based on `fbeta_beta`:
- When `fbeta_beta < 1` (precision-biased): acts as a **minimum recall floor** — the
  pipeline maximizes precision but won't let recall drop below this value
- When `fbeta_beta >= 1` (recall-biased): acts as a **minimum precision floor** — the
  pipeline maximizes recall but won't let precision drop below this value

This means you only need to set one parameter — the pipeline knows which metric needs
protection based on your optimization bias.

### Tuning Strategy Parameters

These control how the model is optimized and how the classification threshold is selected.
All are set in `config.yml` with sensible defaults.

```yaml
optuna_metric: 'fbeta'               # Metric Optuna optimizes during hyperparameter search
threshold_strategy: 'precision_optimal' # How the classification threshold is chosen
fixed_threshold: '0.5'              # Used only when threshold_strategy = fixed
cv_folds: '3'                       # Number of cross-validation folds in Optuna
early_stopping_rounds: '0'          # 0 = disabled; > 0 = stop if no improvement (tree models only)
class_balance_strategy: 'balanced'   # How class imbalance is handled
xgb_eval_metric: 'aucpr'            # Eval metric for XGBoost/CatBoost during training
```

**`optuna_metric`** — The objective function Optuna maximizes (or minimizes for `log_loss`):
- `fbeta` — F-beta score weighted by `fbeta_beta` (default, precision/recall tradeoff)
- `auc_roc` — Area under the ROC curve (ranking quality)
- `auc_pr` — Area under the Precision-Recall curve (good for imbalanced data)
- `precision` — Precision at the default threshold
- `recall` — Recall at the default threshold
- `log_loss` — Log loss (minimized; measures calibration)

**`threshold_strategy`** — How the binary classification threshold is selected after training:
- `precision_optimal` — Maximizes precision while keeping recall above `min_metric_floor` (default)
- `f1_optimal` — Picks the threshold that maximizes F1 score
- `recall_optimal` — Maximizes recall while keeping precision above `min_metric_floor`
- `youden_j` — Maximizes Youden's J statistic (TPR - FPR), balances sensitivity and specificity
- `fixed` — Uses the value from `fixed_threshold` (no optimization)

**`fixed_threshold`** — Only used when `threshold_strategy: 'fixed'`. Set to any float between 0 and 1.

**`cv_folds`** — Number of stratified cross-validation folds used in Optuna trials:
- `3` = fast (default)
- `5` = more stable estimates, slower
- `10` = thorough, significantly slower

**`early_stopping_rounds`** — Stops boosting early during Optuna CV folds if the eval metric
doesn't improve for this many rounds. Only applies to XGBoost and CatBoost (ignored for logistic).
- `0` = disabled (default)
- `50` = good starting point for most datasets
- `100` = more patient, allows slower convergence

**`class_balance_strategy`** — How the pipeline handles imbalanced classes:
- `balanced` — Automatically adjusts class weights (default). XGBoost uses `scale_pos_weight`,
  CatBoost uses `auto_class_weights='Balanced'`, logistic regression searches over
  `class_weight` options including `'balanced'`.
- `none` — No class weight adjustment. Use when classes are roughly balanced or when you
  prefer to handle imbalance via sampling outside the pipeline.

**`xgb_eval_metric`** — Evaluation metric used during XGBoost/CatBoost training. Automatically
mapped to CatBoost equivalents when using CatBoost:
- `aucpr` → CatBoost: `PRAUC` (default, best for imbalanced data)
- `auc` → CatBoost: `AUC`
- `logloss` → CatBoost: `Logloss`
- `error` → CatBoost: `Accuracy`

### XGBoost / CatBoost Tuning Ranges

These are set in `train.dig` under `_env` and control Optuna's search space:

```yaml
# ── Tree model search ranges (in train.dig _env) ──
n_estimators_min: '50'               # Min boosting rounds
n_estimators_max: '700'              # Max boosting rounds
max_depth_min: '3'                   # Min tree depth
max_depth_max: '10'                  # Max tree depth
learning_rate_min: '0.01'            # Min learning rate
learning_rate_max: '0.5'             # Max learning rate
```

Additional XGBoost params (subsample, colsample_bytree, min_child_weight, reg_alpha,
reg_lambda, gamma) are tuned by Optuna with fixed ranges inside `models.py`.

### Prediction-specific Settings (in `predict.dig`)

```yaml
shap_topn_per_direction: '5'         # Top N positive + N negative SHAP drivers per record
shap_max_rows: '0'                   # 0 = SHAP for all records; >0 = sample cap
write_concurrency: '4'              # Parallel TD write threads
```

### Training-specific Settings (in `train.dig`)

```yaml
target_variable: 'your_target'       # Binary 0/1 column name
test_size: '0.3'                     # Fraction held out for evaluation
shap_max_samples: '20000'           # SHAP sample size for aggregate stats
shap_interactions_enabled: 'false'   # Pairwise SHAP interactions (expensive)
columns_to_drop: >-                  # Comma-separated non-feature columns
  session_id,batch_id,reference_date,your_id_col
```

**`columns_to_drop`** — Critical list. Must include:
- All ID columns (`user_id_col`, `session_id`, `batch_id`)
- Date/time columns (`reference_date`, `time`)
- Any metadata columns that aren't features
- The same list must appear in both `train.dig` and `predict.dig`

---

## Output Tables

All output tables are prefixed with `{table_prefix}` (empty by default).

### Training outputs

| Table | Description |
|-------|-------------|
| `{tp}run_log` | Test-set metrics, params, threshold per training run |
| `{tp}train_run_log` | Train-set metrics (for overfitting comparison) |
| `{tp}feature_list` | Ordered feature names used by the model |
| `{tp}feature_importance` | SHAP-based feature importance (magnitude) |
| `{tp}shap_directional` | SHAP direction per feature (pushes score up/down) |
| `{tp}roc_curve` | ROC curve data points |
| `{tp}prediction_bins` | Score distribution histogram (test set) |
| `{tp}probability_train_bins` | Training score bins (used for PSI at prediction) |
| `{tp}test_predictions` | Row-level test-set predictions (if `user_id_col` set) |
| `{tp}vif_scores` | Variance Inflation Factor per feature |
| `{tp}feature_correlations` | Pairwise feature correlation matrix |
| `{tp}target_correlations` | Feature-to-target correlations |
| `{tp}corr_drop_report` | Which features were dropped for high correlation |
| `{tp}optuna_trials` | Full Optuna trial history |
| `{tp}coefficient` | Logistic regression coefficients (logistic only) |
| `{tp}scaler_params` | StandardScaler mean/scale (logistic only) |
| `{tp}xgb_gain_importance` | Native XGBoost gain importance (xgboost only) |
| `{tp}cb_gain_importance` | Native CatBoost importance (catboost only) |
| `ml_model_store` | Model binary blob (xgboost/catboost via td-model-store) |

### Prediction outputs

| Table | Description |
|-------|-------------|
| `{tp}predictions` | One row per scored record (score, label, bucket) |
| `{tp}prediction_shap` | Per-record top-N SHAP drivers (positive + negative) |
| `{tp}prediction_bins` | Score distribution histogram |
| `{tp}prediction_run_log` | Run audit (records scored, PSI, threshold) |

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────┐
│  TRAINING (train.dig)                           │
│                                                 │
│  1. [You add] Data prep SQL steps               │
│  2. [You add] call>: data_prep.dig              │
│  3. [You add] Create final_features_train       │
│  4. [Built-in] Get latest batch ID              │
│  5. [Built-in] Python training pipeline:        │
│     → Load data                                 │
│     → Stratified train/test split               │
│     → Preprocess (encode, impute, scale)        │
│     → Drop correlated features                  │
│     → Optuna hyperparameter search              │
│     → Fit final model                           │
│     → Threshold selection (precision-optimal)   │
│     → Evaluate (train + test metrics)           │
│     → SHAP explainability                       │
│     → Write all artifacts to TD (parallel)      │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  PREDICTION (predict.dig)                       │
│                                                 │
│  1. [You add] Data prep SQL steps               │
│  2. [You add] call>: data_prep.dig              │
│  3. [You add] Create final_features_pred        │
│  4. [Built-in] Get latest batch IDs             │
│  5. [Built-in] Python prediction pipeline:      │
│     → Load trained model (from model store)     │
│     → Load threshold + training bins            │
│     → Load + preprocess prediction data         │
│     → Align features to training set            │
│     → Score all records                         │
│     → Per-row SHAP (predicted positives only)   │
│     → PSI drift check vs training               │
│     → Write outputs to TD (parallel)            │
└─────────────────────────────────────────────────┘
```
