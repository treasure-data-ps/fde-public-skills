# Classification Model — Technical Handoff

Template for technical handoff documentation. Replace placeholders with customer-specific values.

---

## Project Summary

| Field | Value |
|-------|-------|
| **Customer** | [CUSTOMER NAME] |
| **Use Case** | [USE CASE DESCRIPTION] |
| **Target Variable** | `[target_variable]` — [DEFINITION] |
| **Model Type** | [xgboost / catboost / logistic] |
| **Sink Database** | `[sink_database]` |
| **Table Prefix** | `[table_prefix]` |
| **Workflow Project Name** | [TD workflow project name] |
| **Workflow Working Copy** | `agent_outputs/[customer_slug]/classifier/workflow/classify/` |
| **Training Frequency** | [quarterly / monthly / ad-hoc] |
| **Prediction Frequency** | [weekly / daily / ad-hoc] |

## Configuration Summary

### config.yml

```yaml
sink_database: [value]
td_endpoint: [value]
user_id_col: [value]
model_type: [value]
model_name: [value]
fbeta_beta: [value]
n_trials: [value]
threshold_strategy: [value]
look_back_months_training: [value]
train_end_months_from_now: [value]
look_back_months_prediction: [value]
table_prefix: [value]
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Model type | [xgboost/catboost/logistic] | [Why this model was chosen] |
| `fbeta_beta` | [value] | [Why this precision/recall tradeoff] |
| `threshold_strategy` | [value] | [Why this threshold selection method] |
| `train_end_months_from_now` | [value] | [Label maturity period for this use case] |
| `look_back_months_training` | [value] | [Why this training window length] |

## Data Prep Architecture

### Feature Sources

| Source Table | Features Generated | Aggregation Logic |
|-------------|-------------------|-------------------|
| [database.table1] | [list of feature types] | [e.g., "count/sum/avg per user over 30/60/90 days"] |
| [database.table2] | [list of feature types] | [aggregation description] |

### SQL Files

| File | Purpose | Key Logic |
|------|---------|-----------|
| `sql/[file1].sql` | [description] | [notable join logic, filters, or calculations] |
| `sql/[file2].sql` | [description] | [notable logic] |

### columns_to_drop

```
[comma-separated list matching both train.dig and predict.dig]
```

**Reason for each:**
- `[column]` — [why it's not a feature]

## Model Performance

### Latest Training Metrics

| Metric | Train | Test | Gap |
|--------|-------|------|-----|
| AUC-ROC | [value] | [value] | [value] |
| Precision | [value] | [value] | [value] |
| Recall | [value] | [value] | [value] |
| F-beta | [value] | [value] | [value] |
| F1 | [value] | [value] | [value] |

### Classification Threshold

| Field | Value |
|-------|-------|
| Strategy | [threshold_strategy] |
| Optimal threshold | [best_threshold from run_log] |
| At this threshold: precision | [value] |
| At this threshold: recall | [value] |

### Top 10 Features

| Rank | Feature | Importance | Direction | Business Meaning |
|------|---------|-----------|-----------|-----------------|
| 1 | [name] | [SHAP value] | [up/down] | [explanation] |
| 2 | [name] | [SHAP value] | [up/down] | [explanation] |
| ... | ... | ... | ... | ... |

## Ongoing Maintenance

### What to Monitor

1. **PSI after each prediction run** — alert if > 0.25
2. **Metrics trend across retraining runs** — flag if AUC drops by > 0.05
3. **Feature table freshness** — verify source tables are being populated
4. **Score distribution shape** — compare buckets across prediction runs

### When to Retrain

- On schedule: [FREQUENCY]
- On PSI alert: when PSI > 0.25 for two consecutive prediction runs
- On business change: if the target variable definition changes, or if new data sources are added

### How to Add Features

1. Write new SQL in `sql/` directory
2. Add the SQL step to `data_prep.dig` (runs for both train and predict)
3. Join the new features into the final features table
4. If new non-feature columns are introduced, add them to `columns_to_drop` in BOTH dig files
5. Retrain and compare metrics with the previous model

### How to Change Model Type

1. Update `model_type` in `config.yml`
2. Update `model_name` to a descriptive tag (e.g., `churn_catboost_v2`)
3. Run training — the pipeline auto-adjusts preprocessing (scaling, imputation) based on model type
4. Compare metrics with the previous model type in `run_log`

## Access & Ownership

| Role | Person | Responsibility |
|------|--------|---------------|
| Model owner | [NAME] | Retraining schedule, metric monitoring |
| Data engineer | [NAME] | Feature table maintenance, data pipeline |
| Business stakeholder | [NAME] | Score consumption, business rules |
| Solution engineer | [NAME] | Initial setup, support escalation |

## Artifacts Inventory

| Artifact | Location |
|----------|----------|
| Workflow code | Working copy at `agent_outputs/[customer_slug]/classifier/workflow/classify/` (deployed to the TD Workflow project below) |
| TD Workflow project | [project name in TD console] |
| Engagement docs | `agent_outputs/[customer_slug]/classifier/docs/` |
| Run history | `${sink_database}.${table_prefix}run_log` |
| Model binary | `${sink_database}.ml_model_store` (model_name = `[model_name]`) |
