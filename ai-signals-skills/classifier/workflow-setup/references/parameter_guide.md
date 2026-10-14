# Binary Classification — Non-Technical Parameter Guide

This guide explains every configuration parameter in plain language. Use it when a non-technical stakeholder (product manager, business analyst, marketing lead) asks "what does this setting do and how should I choose?"

---

## Core Settings — "Where does the model run and what does it look at?"

### `sink_database`
**What it is:** The Treasure Data database where all model results will be saved.

**How to set it:** Ask your TD admin which database to use. This is where prediction scores, feature importance reports, and run logs will appear. Example: `lead_scoring`, `analytics_prod`.

### `user_id_col`
**What it is:** The column that uniquely identifies each person/record being scored.

**How to set it:** This is the "who" column — the ID that connects a prediction back to a real customer or lead. Common values: `customer_id`, `ucp_id`, `email`, `account_id`. It must exist in your feature tables and be consistent across all data sources.

### `description`
**What it is:** A short note about this particular model run, like a version tag.

**How to set it:** Write something that helps you remember what changed. Examples: `'first production run'`, `'added email engagement features'`, `'retrained after Q3 data'`. This gets logged with every run for audit purposes.

### `td_endpoint`
**What it is:** Which Treasure Data region your account is in.

**How to set it:**
- US accounts: `'https://api.treasuredata.com'` (most common)
- Japan accounts: `'https://api.treasuredata.co.jp'`

---

## Training Time Window — "How much history does the model learn from?"

### `look_back_months_training`
**What it is:** How many months of historical data the model uses to learn patterns.

**How to think about it:** More history = more examples to learn from, but very old data may reflect outdated patterns. Default: `27` months (about 2 years).

**Rule of thumb:**
- If your business changes slowly (e.g., insurance, banking): use 24–36 months
- If your business changes quickly (e.g., SaaS, e-commerce): use 12–18 months

### `train_end_months_from_now`
**What it is:** A safety gap — stop using data from the most recent N months for training.

**Why it matters:** Imagine you're predicting whether a lead converts within 90 days. If you use data from last month, many leads labeled "not converted" simply haven't had enough time yet. The gap prevents this mislabeling.

**How to set it:** Match it to your typical conversion/churn cycle:
- Leads typically convert within 30 days → `train_end_months_from_now: 1`
- Churn typically happens within 90 days → `train_end_months_from_now: 3`
- Default: `2` (safe for most use cases)

### `look_back_months_prediction`
**What it is:** How many months of recent data to use when building features for scoring new records.

**How to set it:** This is usually shorter than the training lookback. You want recent behavior to drive predictions. Default: `12` months.

---

## Output Table Prefix — "How are the result tables named?"

### `table_prefix`
**What it is:** An optional prefix added to every output table name.

**Examples:**
- `table_prefix: ''` → tables named `run_log`, `predictions`, `feature_importance`
- `table_prefix: 'lead_scoring_'` → tables named `lead_scoring_run_log`, `lead_scoring_predictions`, etc.

**When to use a prefix:** If you plan to run multiple models in the same database (e.g., one for lead scoring and one for churn), use different prefixes to keep outputs separate.

---

## Model Selection — "What algorithm does the model use?"

### `model_type`
**What it is:** The machine learning algorithm the model uses to learn patterns.

**Your options:**

| Model | Best for | In plain language |
|-------|----------|-------------------|
| `xgboost` | Most use cases (Recommended) | The gold standard for structured/tabular data. Fast, accurate, handles missing data automatically. |
| `catboost` | Lots of text-like categories | Similar to XGBoost but better when your data has many category-type fields (e.g., product names, regions, campaign names). |
| `logistic` | Maximum transparency | The simplest model. Produces clear "if X goes up by 1, the score changes by Y" coefficients. Choose when auditors or regulators need to inspect the model logic. |

**If unsure:** Use `xgboost`. It's the recommended default for a reason — it works well on almost any tabular dataset.

### `model_store_table` and `model_name`
**What they are:** Where the trained model is saved inside TD (only for XGBoost/CatBoost).

**How to set them:** Use the defaults unless you're running multiple models:
- `model_store_table: 'ml_model_store'`
- `model_name: 'scorer_xgb'` (or something descriptive like `'churn_model_v1'`)

---

## Tuning Parameters — "How does the model decide what's a good prediction?"

### `fbeta_beta` — The precision/recall dial

**What it is:** Controls the tradeoff between two types of mistakes:
- **False positives** (predicting "yes" when the answer is "no") — e.g., flagging a loyal customer as a churn risk
- **False negatives** (predicting "no" when the answer is "yes") — e.g., missing a customer who will actually churn

**The dial:**

| Setting | What it means | Example use case |
|---------|--------------|-----------------|
| `0.5` | "Avoid false positives at all costs" | Sales outreach — don't waste reps' time on bad leads |
| `0.7` | "Lean toward fewer false positives" (Default) | Most lead scoring / propensity models |
| `1.0` | "Both mistakes are equally bad" | General purpose |
| `2.0` | "Don't miss any positive cases, even if some are wrong" | Fraud detection — better to flag 10 legitimate transactions than miss 1 fraudulent one |

**Simple rule:** If acting on a wrong prediction is expensive (e.g., sending a sales rep to a bad lead costs $500), go lower. If missing a positive case is expensive (e.g., missing fraud costs $50,000), go higher.

### `n_trials` — How hard the model searches for good settings

**What it is:** The number of different hyperparameter combinations the model tries during training.

**The dial:**
- `3-5` — Quick test (minutes). Good for checking if the pipeline works.
- `30` — Production quality (Default). Good balance of quality and speed.
- `50-100` — Thorough optimization. Use for critical production models.

**Analogy:** Like trying on shoes. 3 pairs is quick but you might miss the best fit. 30 pairs gives a good selection. 100 pairs is exhaustive but takes longer.

### `corr_threshold` — How similar can two features be before one is removed?

**What it is:** If two features are highly correlated (e.g., "total_visits_30d" and "total_visits_28d"), one is redundant. This threshold decides the cutoff.

**The dial:**
- `0.80` — Aggressive: removes more redundant features (cleaner model, less noise)
- `0.90` — Moderate (Default, recommended for tree models)
- `0.95` — Conservative: keeps more features

**If unsure:** Leave at `0.90`.

### `min_metric_floor` — "Don't let one metric fall below this"

**What it is:** A safety net. When the model optimizes for precision, this ensures recall doesn't drop below the floor (and vice versa).

**Example:** With `fbeta_beta: 0.7` (precision-biased) and `min_metric_floor: 0.35`, the model maximizes precision but guarantees recall stays above 35%.

**The dial:**
- `0.25` — Relaxed: allows the non-optimized metric to drop low
- `0.35` — Moderate (Default)
- `0.50` — Strict: forces a minimum quality bar on both metrics

---

## Tuning Strategy — "How exactly does the model pick the best threshold?"

### `optuna_metric` — What the model tries to maximize during training

| Option | When to use |
|--------|------------|
| `fbeta` | Most cases — balances precision and recall based on `fbeta_beta` (Default) |
| `auc_roc` | When ranking quality matters more than the exact threshold |
| `auc_pr` | When your data is heavily imbalanced (e.g., 1% positive class) |
| `precision` | When false positives are extremely costly |
| `recall` | When missing positives is extremely costly |

### `threshold_strategy` — How the yes/no cutoff is chosen

Every prediction is a probability (e.g., 0.73). The threshold decides: above = positive, below = negative.

| Strategy | What it does |
|----------|-------------|
| `precision_optimal` | Finds the threshold that maximizes precision while keeping recall above `min_metric_floor` (Default) |
| `f1_optimal` | Finds the threshold that balances precision and recall equally |
| `recall_optimal` | Finds the threshold that maximizes recall while keeping precision above `min_metric_floor` |
| `youden_j` | Statistical optimality — maximizes the gap between true positive rate and false positive rate |
| `fixed` | Uses whatever value you set in `fixed_threshold` — no optimization |

### `cv_folds` — How many times to validate during training

| Value | Speed | Stability | When to use |
|-------|-------|-----------|------------|
| `3` | Fast | OK | Default — good for quick iterations |
| `5` | Medium | Good | Production models |
| `10` | Slow | Very good | When you need high confidence |

### `class_balance_strategy` — How to handle imbalanced data

If 95% of your records are negative and only 5% are positive:

| Option | What it does |
|--------|-------------|
| `balanced` | Automatically adjusts so the model pays more attention to the minority class (Default) |
| `none` | No adjustment — use when classes are roughly balanced (40-60% split) |

### `xgb_eval_metric` — What the tree model monitors during training

| Option | Best for |
|--------|---------|
| `aucpr` | Imbalanced data (Default, recommended) |
| `auc` | General purpose |
| `logloss` | When calibration matters (probability accuracy) |
| `error` | When you only care about classification accuracy |

### `early_stopping_rounds` — When to stop training

| Value | What it does |
|-------|-------------|
| `0` | Disabled — always train for the full number of rounds (Default) |
| `50` | Stop if the model hasn't improved in 50 rounds — prevents overfitting |
| `100` | More patient — allows slower convergence |

---

## Training-Specific Settings (in `train.dig`)

### `target_variable`
**What it is:** The column name that contains the answer the model is trying to predict.

**Requirements:** Must contain only 0 and 1 values. 1 = the event happened (converted, churned, etc.), 0 = it didn't.

### `test_size`
**What it is:** What fraction of the training data is held back to test the model's accuracy.

**Default:** `0.3` (30% held back for testing, 70% used for training). Usually don't need to change this.

### `columns_to_drop`
**What it is:** A list of columns in your feature table that should NOT be used as features.

**Must include:** IDs, dates, session markers, metadata, the target variable — anything that's not a genuine predictive feature.

**Why it matters:** If an ID column accidentally becomes a feature, the model may memorize specific IDs instead of learning general patterns. This is called "leakage."

### `shap_max_samples`
**What it is:** How many records to use when computing feature importance explanations.

**Default:** `20000`. Higher = more accurate statistics but slower. For most use cases, 1000–20000 is sufficient.

---

## Prediction-Specific Settings (in `predict.dig`)

### `shap_topn_per_direction`
**What it is:** For each scored record, how many top features to show pushing the score up and down.

**Default:** `5` — shows the top 5 features increasing the score and top 5 decreasing it.

**Example output for one lead:** "Top reasons this lead scores high: visited pricing page 12 times (+0.15), downloaded whitepaper (+0.08), enterprise plan (+0.06). Top reasons holding the score back: no email opens in 30 days (-0.04), short session duration (-0.03)."

### `shap_max_rows`
**What it is:** Maximum number of records to compute per-row SHAP explanations for.

**Default:** `0` (compute for all predicted positives). Set to a number (e.g., `100000`) to cap computation time for very large datasets.

---

## Quick Start Recommendations

### "I'm doing lead scoring for the first time"

```yaml
model_type: 'xgboost'
fbeta_beta: '0.7'
n_trials: '30'
threshold_strategy: 'precision_optimal'
class_balance_strategy: 'balanced'
```

### "I'm building a churn model"

```yaml
model_type: 'xgboost'
fbeta_beta: '1.0'          # Balance precision and recall
n_trials: '30'
threshold_strategy: 'f1_optimal'
class_balance_strategy: 'balanced'
```

### "I'm doing fraud detection"

```yaml
model_type: 'xgboost'
fbeta_beta: '2.0'          # Don't miss fraud
n_trials: '50'
threshold_strategy: 'recall_optimal'
class_balance_strategy: 'balanced'
xgb_eval_metric: 'aucpr'   # Better for highly imbalanced data
```

### "I need a quick test to see if the pipeline works"

```yaml
model_type: 'xgboost'
fbeta_beta: '0.7'
n_trials: '5'              # Minimal search
cv_folds: '2'              # Fastest validation
threshold_strategy: 'f1_optimal'
```
