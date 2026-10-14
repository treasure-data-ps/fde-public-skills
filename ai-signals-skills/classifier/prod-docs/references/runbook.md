# Classification Model — Runbook & Architecture

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Treasure Data Platform                                             │
│                                                                     │
│  ┌───────────────┐     ┌──────────────────┐     ┌───────────────┐  │
│  │ Source Tables  │────▸│ Feature Eng SQL  │────▸│ Final Features│  │
│  │ (behavioral,  │     │ (data_prep.dig)  │     │ Table         │  │
│  │  transactional,│     │                  │     │               │  │
│  │  profile)      │     └──────────────────┘     └───────┬───────┘  │
│  └───────────────┘                                       │          │
│                                                          ▼          │
│                              ┌────────────────────────────────────┐ │
│                              │ Classification Pipeline (Python)   │ │
│                              │                                    │ │
│                              │  Training:                        │ │
│                              │  ├─ Stratified split              │ │
│                              │  ├─ Preprocess (encode, impute)   │ │
│                              │  ├─ Correlation-based feature drop│ │
│                              │  ├─ Optuna hyperparameter search  │ │
│                              │  ├─ Model fit (XGB/CB/LR)        │ │
│                              │  ├─ Threshold selection           │ │
│                              │  ├─ Evaluation (train + test)     │ │
│                              │  └─ SHAP explainability           │ │
│                              │                                    │ │
│                              │  Prediction:                      │ │
│                              │  ├─ Load trained model            │ │
│                              │  ├─ Preprocess + align features   │ │
│                              │  ├─ Score all records             │ │
│                              │  ├─ Per-row SHAP (positives only) │ │
│                              │  └─ PSI drift detection           │ │
│                              └────────────────┬───────────────────┘ │
│                                               │                     │
│                                               ▼                     │
│                              ┌────────────────────────────────────┐ │
│                              │ Output Tables (sink_database)      │ │
│                              │ ├─ {tp}predictions                │ │
│                              │ ├─ {tp}prediction_shap            │ │
│                              │ ├─ {tp}run_log                    │ │
│                              │ ├─ {tp}feature_importance         │ │
│                              │ └─ ... (~20 artifact tables)      │ │
│                              └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Workflow Files

| File | Purpose |
|------|---------|
| `config.yml` | All tunable parameters (single source of truth) |
| `train.dig` | Training orchestration — data prep + Python training pipeline |
| `predict.dig` | Prediction orchestration — data prep + Python scoring pipeline |
| `data_prep.dig` | Shared feature engineering SQL (called by both train and predict) |
| `models.py` | Model classes (Logistic, XGBoost, CatBoost) with Optuna |
| `explainer.py` | SHAP explainability, threshold selection, evaluation metrics |
| `preprocessor.py` | One-hot encoding, imputation, correlation-based feature drop |
| `parallel_writer.py` | Concurrent TD table writer (thread-pool) |
| `python/train.py` | Training entry point |
| `python/predict_main.py` | Prediction entry point |
| `python/predictor.py` | Model loading and scoring logic |
| `python/data_handler.py` | TD read/write helper |

### Model Types

| Model | Storage | NaN Handling | Scaling |
|-------|---------|-------------|---------|
| XGBoost | `ml_model_store` (td-model-store binary) | Native (learned split direction) | None |
| CatBoost | `ml_model_store` (td-model-store binary) | Native (nan_mode=Min) | None |
| Logistic | `{tp}coefficient` + `{tp}scaler_params` tables | Mean imputation | StandardScaler |

---

## Runbook

### Routine Operations

#### Running Training

```bash
# Trigger training workflow
digdag run train.dig
# Or via tdx
tdx wf run train.dig
```

**Expected duration:** Depends on data size and `n_trials`. Typical ranges:
- Small data (<100K rows, 30 trials): 10–20 minutes
- Medium data (100K–1M rows, 30 trials): 30–60 minutes
- Large data (>1M rows, 50+ trials): 1–3 hours

**After training, verify:**
1. Check `run_log` for metrics (see eval.md validation queries)
2. Compare train vs test AUC for overfitting
3. Review top features in `feature_importance`
4. Check SHAP directions in `shap_directional` for business sense

#### Running Prediction

```bash
# Trigger prediction workflow
digdag run predict.dig
# Or via tdx
tdx wf run predict.dig
```

**Prerequisites:**
- Training must have run at least once (model exists in model store)
- Prediction feature table (`{tp}final_features_pred`) must exist with current data

**After prediction, verify:**
1. Check `prediction_run_log` for PSI drift
2. Verify `predictions` table has expected record count
3. Spot-check `prediction_shap` for sensible explanations

### Monitoring & Alerts

#### PSI Drift Detection

PSI (Population Stability Index) measures whether the score distribution has shifted between training and prediction:

| PSI Value | Interpretation | Action |
|-----------|---------------|--------|
| < 0.10 | No significant drift | Continue as normal |
| 0.10 – 0.25 | Moderate drift | Monitor closely; consider retraining if sustained |
| > 0.25 | Significant drift | Retrain the model with recent data |

Check PSI after every prediction run:
```sql
SELECT pred_session_id, ROUND(CAST(psi AS DOUBLE), 4) AS psi
FROM ${sink_database}.${table_prefix}prediction_run_log
ORDER BY pred_session_id DESC
LIMIT 5;
```

#### Model Degradation

Compare metrics across training runs:
```sql
SELECT
  session_id,
  ROUND(CAST(test_auc_roc AS DOUBLE), 4) AS auc,
  ROUND(CAST(test_fbeta AS DOUBLE), 4) AS fbeta,
  ROUND(CAST(test_precision AS DOUBLE), 4) AS precision,
  ROUND(CAST(test_recall AS DOUBLE), 4) AS recall
FROM ${sink_database}.${table_prefix}run_log
ORDER BY session_id DESC
LIMIT 10;
```

If AUC or F-beta drops significantly between retraining runs, investigate:
- Has the underlying data distribution changed?
- Are feature sources still being populated?
- Has the target variable definition changed?

### Retraining Cadence

Recommended retraining frequency depends on how quickly the underlying data patterns change:

| Domain | Recommended Frequency | Reason |
|--------|-----------------------|--------|
| Lead scoring (B2B) | Quarterly | Business cycles are long |
| Churn prediction (SaaS) | Monthly | User behavior shifts faster |
| Campaign response | Before each major campaign | Audience changes per campaign |
| Fraud detection | Monthly or on PSI alert | Fraud patterns evolve rapidly |

### Troubleshooting

| Issue | Diagnostic | Resolution |
|-------|-----------|------------|
| Training fails with "no data" | Check `final_features_train` table exists and has rows | Run data prep steps first; verify time window captures data |
| Training fails with memory error | Feature table too wide or too many rows | Reduce features; add `corr_threshold: '0.80'`; sample data |
| Prediction fails with model not found | `model_store_table` doesn't contain the model | Verify training completed; check `model_name` matches |
| Prediction fails with "column mismatch" | `columns_to_drop` differs between train and predict | Sync the `columns_to_drop` list in both dig files |
| All predictions are the same score | Model is degenerate (no signal in features) | Add more features; check target variable; verify data prep |
| SHAP computation is slow | Too many records or features | Set `shap_max_rows` to a sample (e.g., 100000) |
| PSI > 0.25 | Data distribution drift | Retrain model; investigate source data changes |

### Configuration Change Checklist

When updating the model configuration:

1. Update `config.yml` with new parameters
2. If `columns_to_drop` changed, update BOTH `train.dig` AND `predict.dig`
3. If data prep SQL changed, update the SQL files and test with a small lookback first
4. Run training first, verify metrics, then run prediction
5. Compare new metrics with previous run in `run_log`
6. Update `description` in `config.yml` to document what changed
7. Update `agent_outputs/<customer_slug>/classifier/project_state.md` and regenerate the affected files in `docs/`

### Secrets Management

The workflow requires one TD secret, which must be set **before the first `train.dig` or `predict.dig` run** — both fail immediately without it:
- `apikey` — TD Master API Key (`ACCOUNT_ID/KEY` format) with read/write access to `sink_database`

Set via: `tdx wf secrets set <project_name> apikey=<your-api-key>`

OAuth tokens cause 401 errors — the key must be a Master API Key.
