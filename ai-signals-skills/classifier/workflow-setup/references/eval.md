# Binary Classification — Workflow Output Validation

Run these checks after every workflow execution (Phase 3 minimal push and Phase 4 re-run). Execute all queries against `${sink_database}` using `tdx-skills:tdx-basic`.

---

## 1. Training Run Log — `{tp}run_log`

**What it is:** One row per training run with test-set metrics, threshold, best hyperparameters, and run metadata. The primary indicator of model quality.

```sql
SELECT
  session_id,
  model_type,
  ROUND(CAST(best_threshold AS DOUBLE), 4) AS best_threshold,
  ROUND(CAST(test_precision AS DOUBLE), 4) AS precision,
  ROUND(CAST(test_recall AS DOUBLE), 4) AS recall,
  ROUND(CAST(test_f1 AS DOUBLE), 4) AS f1,
  ROUND(CAST(test_fbeta AS DOUBLE), 4) AS fbeta,
  ROUND(CAST(test_auc_roc AS DOUBLE), 4) AS auc_roc,
  ROUND(CAST(test_aucpr AS DOUBLE), 4) AS aucpr
FROM ${sink_database}.${table_prefix}run_log
ORDER BY session_id DESC
LIMIT 5;
```

**Pass criteria:**
- `test_auc_roc > 0.55` — above 0.5 means the model is better than random
- `test_precision > 0.10` and `test_recall > 0.10` — neither metric is zero (degenerate model)
- `test_fbeta` is reasonable for the use case (varies by problem; > 0.30 is a good minimum bar)
- `best_threshold` is between 0.0 and 1.0

**Warning signs:**
- `test_auc_roc > 0.98` — suspiciously high, check for feature leakage
- `test_precision = 1.0` and `test_recall` is very low — model only predicts the majority class
- `test_recall = 1.0` and `test_precision` is very low — model predicts everything as positive

---

## 2. Overfitting Check — `{tp}run_log` vs `{tp}train_run_log`

**What it is:** Compare train-set metrics with test-set metrics. Large gaps indicate overfitting.

```sql
SELECT
  r.session_id,
  ROUND(CAST(t.train_auc_roc AS DOUBLE), 4) AS train_auc,
  ROUND(CAST(r.test_auc_roc AS DOUBLE), 4) AS test_auc,
  ROUND(CAST(t.train_auc_roc AS DOUBLE) - CAST(r.test_auc_roc AS DOUBLE), 4) AS auc_gap,
  ROUND(CAST(t.train_fbeta AS DOUBLE), 4) AS train_fbeta,
  ROUND(CAST(r.test_fbeta AS DOUBLE), 4) AS test_fbeta,
  ROUND(CAST(t.train_fbeta AS DOUBLE) - CAST(r.test_fbeta AS DOUBLE), 4) AS fbeta_gap
FROM ${sink_database}.${table_prefix}run_log r
JOIN ${sink_database}.${table_prefix}train_run_log t ON r.session_id = t.session_id
ORDER BY r.session_id DESC
LIMIT 5;
```

**Pass criteria:**
- `auc_gap < 0.10` — a gap over 10% suggests overfitting
- `fbeta_gap < 0.15` — F-beta gap should be moderate

**If overfitting detected:**
- Increase `corr_threshold` (drop more correlated features)
- Decrease `max_depth_max` (shallower trees)
- Increase `n_trials` (better hyperparameter search)
- Enable `early_stopping_rounds: '50'` (stop boosting when validation plateaus)

---

## 3. Feature Importance — `{tp}feature_importance`

**What it is:** SHAP-based feature importance ranking (mean absolute SHAP value per feature). Shows which features matter most to the model.

```sql
SELECT
  feature_name,
  ROUND(CAST(mean_abs_shap AS DOUBLE), 6) AS importance
FROM ${sink_database}.${table_prefix}feature_importance
WHERE session_id = (SELECT MAX(session_id) FROM ${sink_database}.${table_prefix}feature_importance)
ORDER BY CAST(mean_abs_shap AS DOUBLE) DESC
LIMIT 20;
```

**Pass criteria:**
- Features make business sense — the top features should be related to the prediction target
- No single feature dominates (>50% of total importance) — unless there's a clear business reason
- ID columns, dates, or metadata are NOT in the feature list (they should be in `columns_to_drop`)

**Warning signs:**
- A feature that directly encodes the target (e.g., `days_since_conversion` for a conversion model) — this is feature leakage
- Features with suspicious names that suggest future information

---

## 4. SHAP Directional — `{tp}shap_directional`

**What it is:** For each feature, whether higher values push the prediction score up or down, and with what confidence.

```sql
SELECT
  feature_name,
  direction,
  ROUND(CAST(mean_shap AS DOUBLE), 6) AS mean_shap,
  ROUND(CAST(direction_confidence AS DOUBLE), 4) AS confidence,
  ROUND(CAST(pct_pushing_up AS DOUBLE), 4) AS pct_up,
  ROUND(CAST(pct_pushing_down AS DOUBLE), 4) AS pct_down
FROM ${sink_database}.${table_prefix}shap_directional
WHERE session_id = (SELECT MAX(session_id) FROM ${sink_database}.${table_prefix}shap_directional)
ORDER BY CAST(mean_abs_shap AS DOUBLE) DESC
LIMIT 20;
```

**Pass criteria:**
- Directions are business-sensible (e.g., more visits → higher conversion score, longer inactivity → higher churn score)
- `direction_confidence` > 0.5 for top features (strong directional signal)

---

## 5. Test Predictions — `{tp}test_predictions`

**What it is:** Row-level predictions on the held-out test set with actual labels and outcome classification (TP/TN/FP/FN).

```sql
-- Confusion matrix from test predictions
SELECT
  outcome_class,
  COUNT(*) AS cnt
FROM ${sink_database}.${table_prefix}test_predictions
WHERE session_id = (SELECT MAX(session_id) FROM ${sink_database}.${table_prefix}test_predictions)
GROUP BY 1
ORDER BY 1;
```

**Pass criteria:**
- All four outcome classes present: TP, TN, FP, FN
- Distribution aligns with the precision/recall numbers in `run_log`

```sql
-- Score distribution by outcome
SELECT
  outcome_class,
  COUNT(*) AS cnt,
  ROUND(AVG(CAST(predicted_proba AS DOUBLE)), 4) AS avg_score,
  ROUND(MIN(CAST(predicted_proba AS DOUBLE)), 4) AS min_score,
  ROUND(MAX(CAST(predicted_proba AS DOUBLE)), 4) AS max_score
FROM ${sink_database}.${table_prefix}test_predictions
WHERE session_id = (SELECT MAX(session_id) FROM ${sink_database}.${table_prefix}test_predictions)
GROUP BY 1
ORDER BY 1;
```

**Pass criteria:**
- TP (true positives) should have the highest average scores
- TN (true negatives) should have the lowest average scores
- Good separation between TP and FP average scores indicates a useful model

---

## 6. Prediction Scores — `{tp}predictions`

**What it is:** One row per scored record with the probability score, predicted label, and score bucket. This is the main output table for downstream use.

```sql
SELECT
  COUNT(*) AS total_scored,
  ROUND(AVG(CAST(predicted_proba AS DOUBLE)), 4) AS avg_score,
  ROUND(MIN(CAST(predicted_proba AS DOUBLE)), 4) AS min_score,
  ROUND(MAX(CAST(predicted_proba AS DOUBLE)), 4) AS max_score,
  SUM(CASE WHEN predicted_label = 1 THEN 1 ELSE 0 END) AS predicted_positive,
  ROUND(SUM(CASE WHEN predicted_label = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS pct_positive
FROM ${sink_database}.${table_prefix}predictions
WHERE pred_session_id = (SELECT MAX(pred_session_id) FROM ${sink_database}.${table_prefix}predictions);
```

**Pass criteria:**
- `total_scored > 0` — predictions were generated
- `avg_score` is reasonable (not all 0.0 or all 1.0)
- `pct_positive` is in a sensible range for the use case (e.g., for lead scoring, 10–30% positive is typical)

```sql
-- Score bucket distribution
SELECT
  score_bucket,
  COUNT(*) AS cnt
FROM ${sink_database}.${table_prefix}predictions
WHERE pred_session_id = (SELECT MAX(pred_session_id) FROM ${sink_database}.${table_prefix}predictions)
GROUP BY 1
ORDER BY 1;
```

**Pass criteria:**
- Scores are distributed across buckets (not all clustered in one bucket)
- Distribution shape is reasonable (not heavily skewed to 0.0 or 1.0)

---

## 7. Prediction SHAP — `{tp}prediction_shap`

**What it is:** Per-record top-N features that pushed the score up and down (long format). Only computed for records predicted as positive.

```sql
SELECT
  COUNT(DISTINCT user_id) AS users_with_shap,
  COUNT(*) AS total_shap_rows,
  COUNT(DISTINCT feature_name) AS distinct_features
FROM ${sink_database}.${table_prefix}prediction_shap
WHERE pred_session_id = (SELECT MAX(pred_session_id) FROM ${sink_database}.${table_prefix}prediction_shap);
```

**Pass criteria:**
- `users_with_shap` approximately matches the predicted positive count from Step 6
- `distinct_features` > 1 — multiple features are contributing
- `total_shap_rows` ≈ `users_with_shap × (2 × shap_topn_per_direction)` (top N up + top N down per user)

---

## 8. Prediction Run Log — `{tp}prediction_run_log`

**What it is:** Audit row for each prediction run — records scored, score statistics, PSI drift metric, and threshold applied.

```sql
SELECT
  pred_session_id,
  records_scored,
  ROUND(CAST(score_mean AS DOUBLE), 4) AS score_mean,
  ROUND(CAST(score_min AS DOUBLE), 4) AS score_min,
  ROUND(CAST(score_max AS DOUBLE), 4) AS score_max,
  ROUND(CAST(psi AS DOUBLE), 4) AS psi,
  ROUND(CAST(threshold_used AS DOUBLE), 4) AS threshold_used
FROM ${sink_database}.${table_prefix}prediction_run_log
ORDER BY pred_session_id DESC
LIMIT 5;
```

**Pass criteria:**
- `records_scored > 0`
- `psi < 0.25` — PSI (Population Stability Index) measures drift between training and prediction score distributions
  - `< 0.10`: No significant drift
  - `0.10–0.25`: Moderate drift — monitor closely
  - `> 0.25`: Significant drift — model may need retraining
- `threshold_used` matches the `best_threshold` from training `run_log`

---

## Common Failure Modes

| Symptom | Likely Cause | Fix |
|---|---|---|
| `run_log` is empty | Training failed mid-run or `sink_database` does not exist | Check attempt logs in TD console; confirm `sink_database` exists |
| AUC-ROC ≈ 0.50 | Model is no better than random — features have no predictive signal | Check feature engineering; verify target variable is correct; add more features |
| AUC-ROC > 0.98 | Feature leakage — a feature encodes the target | Review `columns_to_drop`; look for features derived from the target variable |
| All predictions are 0 (or all 1) | Degenerate model, poor threshold, or extreme class imbalance | Lower `min_metric_floor`; adjust `fbeta_beta`; verify training data has both classes |
| `predictions` table is empty | Prediction pipeline failed or no data in prediction window | Check `look_back_months_prediction`; verify prediction feature table exists |
| PSI > 0.25 | Score distribution shifted — data drift | Feature distributions have changed; retrain model on recent data |
| Feature importance shows IDs or dates | `columns_to_drop` is incomplete | Add the leaked columns to `columns_to_drop` in both `train.dig` and `predict.dig` |
| Train AUC much higher than test AUC | Overfitting | Reduce `max_depth_max`; enable `early_stopping_rounds`; increase `corr_threshold` |
| prediction_shap is empty | No records predicted as positive, or SHAP disabled | Check threshold — it may be too high for the prediction data; lower `min_metric_floor` |
