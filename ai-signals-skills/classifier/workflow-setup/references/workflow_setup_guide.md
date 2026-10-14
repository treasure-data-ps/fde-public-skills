# Binary Classification Workflow Setup Guide

Step-by-step guide for configuring and deploying the Binary Classification workflow in Treasure Data.

The workflow trains a binary classification model on historical data with a known outcome (0/1 target), then scores new records to predict likelihood of the target event occurring.

## What is Binary Classification?

Binary classification predicts a yes/no outcome — will a lead convert, will a customer churn, will a transaction be fraudulent. The model outputs a probability score (0.0–1.0) for each record, along with SHAP explanations showing which features drove each prediction.

**Key outputs:**
- Probability scores for every record (the "lead score" / "churn score" / "propensity score")
- Per-record SHAP explanations (top features pushing the score up/down)
- Feature importance rankings (which features matter most globally)
- Model performance metrics (precision, recall, F-beta, AUC)
- Score drift detection (PSI) between training and prediction

## Use Cases

- Lead scoring / conversion prediction
- Churn prediction / retention risk
- Campaign response propensity
- Upsell / cross-sell likelihood
- Fraud detection
- Customer reactivation likelihood
- Any problem where you need to predict a binary outcome from tabular features

## Classification Workflow Configuration

### Step 1: Gather Requirements

Walk through `requirements_doc.md` with the user — it covers use case definition, target variable, data sources, and model preferences.

For a quick setup without the full requirements gathering, ask the user:
1. **What are you trying to predict?** (e.g., lead conversion, churn, fraud)
2. **What is the target variable column name?** (e.g., `converted`, `churned`)
3. **Is there an existing Parent Segment to use as a feature source?** (if yes, get the name; its join key is a strong candidate for `user_id_col` — see Step 2 below)
4. **What other database(s) have tables to explore for additional features?** (e.g., `lead_scoring`; there can be more than one)
5. **What is the user ID column?** (e.g., `ucp_id`, `customer_id` — confirm it matches or can be joined to the Parent Segment's join key, if one is in use)
6. **Do you prefer precision or recall?** (e.g., "fewer false positives" = precision-biased)

### Step 2: Check for a Parent Segment, Then Explore Additional Databases

**Before exploring raw tables**, check whether the customer has an existing Parent Segment. If so, run `tdx ps desc "<name>" -o <slug>_ps_schema.json` and review its `customers` table — those attributes are already aggregated and joined to the canonical ID, so they can be used as model features with no additional data prep SQL. See `tdx-skills:parent-segment-analysis` for the discovery workflow.

Regardless of whether a Parent Segment exists, ask whether there are additional raw tables to include — **these can live in any number of databases**, not just the Parent Segment's own output database. A Parent Segment rarely covers every useful signal (a newly integrated data source, or a database that hasn't gone through ID Unification, are common examples). Use **Trino SQL** via **tdx-skills** to discover raw feature source tables in each database named.

The classifier needs:
1. **A feature table** with numeric and categorical features per record
2. **A binary target column** (0/1) in the training data

Look for tables that contain:

#### Behavioral Features
- Tables like: `user_activity`, `page_views`, `session_data`, `engagement_metrics`
- Aggregate into features like: visit_count_30d, pages_viewed, avg_session_duration
- **Purpose**: Behavioral signals that predict the target outcome

#### Transactional Features
- Tables like: `orders`, `purchases`, `transactions`, `subscriptions`
- Aggregate into features like: total_spend, order_count, avg_order_value, days_since_last_order
- **Purpose**: Purchase/transaction patterns

#### Profile / Demographic Features
- Tables like: `customer_profiles`, `user_attributes`, `demographics`
- Features like: account_age_days, region, plan_type, industry
- **Purpose**: Static attributes that may correlate with the outcome

#### CRM / Interaction Features
- Tables like: `support_tickets`, `sales_interactions`, `marketing_touches`
- Aggregate into features like: ticket_count, days_since_last_contact, email_opens_30d
- **Purpose**: Engagement and interaction history

### Step 3: Copy the Classification Workflow Template

The template ships with this skill at `project_templates/classify/` (read-only). Copy it into the engagement working directory (see `../../../shared/local_outputs.md`):

```bash
dest="agent_outputs/<customer_slug>/classifier/workflow"
mkdir -p "$dest"
[ -d "$dest/classify" ] || cp -R "<classifier_skill_dir>/project_templates/classify" "$dest/"
```

`<classifier_skill_dir>` is the absolute path of the directory containing the classifier `SKILL.md`. All edits below happen in this working copy.

### Step 4: Configure `config.yml`

The critical file to configure is `config.yml` in the working copy (`agent_outputs/<customer_slug>/classifier/workflow/classify/config.yml`)

**Reference**: Read `yaml_structure.md` for the complete parameter reference.
**Reference**: Read `parameter_guide.md` for non-technical parameter explanations.

#### Core Settings

```yaml
sink_database: lead_scoring              # Where output tables go
td_endpoint: 'https://api.treasuredata.com'  # TD region
user_id_col: 'ucp_id'                   # Unique record ID column
description: 'initial model run'         # Audit trail description
```

#### Training Time Window

```yaml
look_back_months_training: 27            # History for training features
train_end_months_from_now: 2             # Gap to avoid label leakage
look_back_months_prediction: 12          # History for prediction features
```

**Key decision**: `train_end_months_from_now` creates a gap between training data and now. This prevents using labels that haven't fully matured (e.g., a lead that was labeled "not converted" simply because not enough time passed). Set to match the customer's typical conversion/churn cycle length.

#### Model Selection

```yaml
model_type: 'xgboost'                   # Recommended default
model_store_table: 'ml_model_store'
model_name: 'scorer_xgb'
```

**When to choose each model:**

| Model | When to use |
|-------|------------|
| `xgboost` | Default choice. Best for most tabular datasets. Handles NaN natively. |
| `catboost` | When data has many high-cardinality categorical features. Also handles NaN natively. |
| `logistic` | When interpretability is critical (provides coefficients). Best for simple/linear relationships. |

#### Tuning Parameters

```yaml
fbeta_beta: '0.7'                       # Precision/recall tradeoff
n_trials: '30'                          # Optuna search budget
corr_threshold: '0.90'                  # Feature correlation threshold
min_metric_floor: '0.35'               # Safety floor
```

**Key decision — `fbeta_beta`:**
- Customer says "I can't afford false positives" → `0.5` (strongly precision-biased)
- Customer says "balance is fine" → `0.7` (moderately precision-biased, recommended default)
- Customer says "I can't miss any positive cases" → `2.0` (recall-biased)

#### Tuning Strategy

```yaml
optuna_metric: 'fbeta'
threshold_strategy: 'precision_optimal'
cv_folds: '3'
class_balance_strategy: 'balanced'
xgb_eval_metric: 'aucpr'
```

### Step 5: Configure Data Prep SQL

This is the **main customization point**. The workflow needs a final features table named `{table_prefix}final_features_{mode}`.

Add SQL steps to `train.dig` (before `+get_latest_batchid`), `predict.dig` (before `+get_latest_batch`), and `data_prep.dig` (shared feature engineering).

Each SQL step should:
1. Query raw source tables — **and, per Phase 1/2 discovery, Parent Segment attributes.** Parent Segment output tables (e.g., `cdp_audience_<id>.customers`) and any additional raw source tables almost always live in a **different database** than `sink_database`. Cross-database queries are expected and fine — fully qualify every table reference (`<database>.<table>`), do not assume everything is in `sink_database`.
2. Reconcile join keys per source. If Phase 1/2 flagged that a table's ID column doesn't match the canonical `user_id_col` (e.g., a raw table uses a different customer ID that needs a lookup/mapping table to resolve to the canonical ID), perform that join here — before aggregating that source's features.
3. Aggregate behavioral data into features (counts, sums, averages per user)
4. **Materialize the target variable if it was flagged in Phase 1/2 as needing derivation** (rather than existing as a stored column). Add it as an explicit output column in this SQL — e.g., `CASE WHEN days_since_last_order > 180 THEN 1 ELSE 0 END AS churned`. `target_variable` in Step 8 below then just references this materialized column name; the derivation logic itself belongs here, not in `train.dig`/`predict.dig` directly.
5. Join multiple feature sets
6. Output a final wide table with one row per record

```yaml
# Example: Add to train.dig before +get_latest_batchid
+create_base_table:
  td>: sql/create_training_base.sql
  create_table: base_data_train

+create_feature_tables:
  call>: data_prep.dig

+create_final_features:
  td>: sql/join_final_features.sql
  create_table: ${table_prefix}final_features_${mode}
```

**If the target variable is derived from a feature** (e.g., a churn flag calculated from a `recency`/`days_since_last_order` column that is otherwise a legitimate feature), that source column **must** be added to `columns_to_drop` in Step 7 — otherwise the model trains on a column that trivially encodes the label, and the resulting "high accuracy" is actually leakage. Flag this explicitly to the user when it applies.

### Step 6: Confirm the Feature Engineering SQL Produces Valid Train/Test Tables

Before moving to `columns_to_drop` and `target_variable`, run the data prep SQL directly (outside the workflow, via `tdx query`) against the customer's account to confirm it actually produces a usable `{table_prefix}final_features_{mode}` table. Do not assume the SQL is correct just because it looks right — verify it runs and the output shape is sane.

Check:
1. **The query runs without errors** — especially any cross-database joins (Parent Segment database ↔ `sink_database` ↔ any additional raw-table databases) and any join-key reconciliation logic from Step 5.
2. **Row count is reasonable** — one row per `user_id_col` value, no unexpected fan-out from a join (e.g., a one-to-many join that wasn't pre-aggregated would multiply rows).
3. **The target variable column is present and binary** — if derived, spot-check a few rows against the source data to confirm the derivation logic is correct (e.g., pull 5 known-churned and 5 known-active customers and confirm the flag matches expectations).
4. **No unexpected NULLs** in key feature columns — a failed join (e.g., an unreconciled join key) will silently produce NULLs across an entire joined source rather than an error.
5. **Both classes are present** in the resulting table (reuse the class balance query from Phase 1 Step 7 / `requirements_doc.md` Step 5, now against the actual final features table).

If any check fails, fix the SQL and re-run this validation before proceeding — do not push a workflow with unvalidated data prep SQL.

### Step 7: Configure `columns_to_drop` in `train.dig` and `predict.dig`

List all non-feature columns that should be excluded from model training. These are columns present in the final features table that are NOT predictive features:

```yaml
columns_to_drop: >-
  web_session_id,batch_id,reference_date,ucp_id,time,
  any_other_id_or_metadata_columns
```

**CRITICAL**: The `columns_to_drop` list must be identical in both `train.dig` and `predict.dig`. If they differ, feature alignment at prediction time will fail.

**What to include:**
- All ID columns (`user_id_col`, any raw table's own session/browsing ID column, `batch_id`)
- Date/time columns (`reference_date`, `time`, `created_at`)
- The target variable (auto-handled, but explicit listing is clearer)
- **Any column the target variable was derived from in Step 5** (e.g., drop `recency` if `churned` was calculated as `recency > 365`) — this is the most common source of label leakage in derived-label use cases
- Any metadata columns that aren't features

> **Naming note:** If a raw source table has its own `session_id` column (e.g., a web/browsing session from pageview data), that is unrelated to the workflow's own `session_id`/`pred_session_id` (the digdag run identifier written to `run_log`, `predictions`, etc. — see `yaml_structure.md` "Session ID Tracking"). Alias a raw table's session column to something unambiguous (e.g., `web_session_id`) in the data prep SQL so the two concepts never collide under the same column name, then drop it here as usual since it's not a feature.

### Step 8: Configure `target_variable` and `session_id` in `train.dig` / `predict.dig`

Set the binary 0/1 target column name:

```yaml
target_variable: 'app_conversion'        # Must be 0/1 in the training data
```

This must be the name of the column **as materialized in the final features table** — either an existing column carried through from a source table, or the derived column created in Step 5 (e.g., `churned`). `target_variable` never contains a derivation expression itself (e.g., `'recency > 365'` is invalid) — the derivation happens in the data prep SQL, and this field just names the resulting output column.

Also wire the workflow's own run identifier through as `_env`, using digdag's `${session_id}` built-in variable — do not let the Python pipeline generate its own session ID:

```yaml
# train.dig
_env:
  session_id: ${session_id}
  target_variable: 'app_conversion'

# predict.dig
_env:
  pred_session_id: ${session_id}
```

See `yaml_structure.md` "Session ID Tracking" for why this matters — it's what makes `MAX(session_id)` / `ORDER BY session_id DESC` in `eval.md` and the insights agent work correctly across retraining and re-prediction runs.

### Step 9: Present Configuration to User for Approval

Show the user:
1. **Use case summary** — what the model predicts
2. **Target variable** — column name, definition, and whether it's derived (and from what) or pre-existing
3. **Feature sources** — which tables feed into the model, across which databases
4. **Model type** — XGBoost / CatBoost / Logistic and why
5. **Precision/recall preference** — `fbeta_beta` value and what it means
6. **Training window** — date range for training data
7. **The generated `config.yml`**
8. **Request confirmation** before proceeding

### Step 10: Present Final Config and Confirm

Before deploying, **always present the complete `config.yml`** to the user for review.

Show the full config content and ask:

> Here is the final `config.yml` that will be deployed. Please review and confirm this is correct.

**Wait for explicit confirmation before proceeding.**

### Step 11: Deploy

**STOP — read both files below before executing any command in this step:**
1. **`deploy_instructions.md`** — template copy location and working-copy structure.
2. **`../../../shared/push_pattern_td_workflows.md`** — full canonical push flow including the mandatory project name confirmation, push mechanics, secrets setup, workflow run, monitoring, and output validation.

Do not copy the template, write files, or run any `tdx` command until both files have been read.

**Project name gate (mandatory — use `AskUserQuestion`):**
Before pushing, ask the user whether to use the default project name (the `classify/` folder name) or provide a custom name. Record the confirmed name and use it in all subsequent push/run/monitor commands.

Once the user has confirmed both the `config.yml` and the project name:
1. Copy the template into the working copy if not already done (Step 3)
2. Place the configured `config.yml` in the working copy root
3. Add data prep SQL files to `sql/` in the working copy
4. Update `train.dig` and `predict.dig` in the working copy with data prep steps and `columns_to_drop`
5. Push the workflow to TD from inside the working copy (`agent_outputs/<customer_slug>/classifier/workflow/classify/`):
   - **Default name**: `tdx wf push -y` (uses folder name `classify`)
   - **Custom name**: `tdx wf upload <custom_project_name>` (pushes under a different project name without renaming the folder)
6. Set the required workflow secret — the Python training/prediction pipeline needs a TD API key with read/write access to `sink_database` to read source tables and write output tables:
   ```bash
   tdx wf secrets set <project_name> apikey=<TD_API_KEY>
   ```
   Use a Master API Key in `ACCOUNT_ID/KEY` format — OAuth tokens cause 401 errors. Without this secret, `train.dig`/`predict.dig` will fail immediately on the first `td>` or `py>` step. Never handle the key value directly in chat — present the `tdx wf secrets set` command with a placeholder and let the user supply the actual key.
7. Run training (after asking the user): `tdx wf run <project_name>.train`
8. Monitor via `tdx wf sessions` and `tdx wf timeline`
9. After a successful run: validate per `eval.md` and update `project_state.md` (project name, push date, validation summary)

## Critical Configuration Rules

### Target Variable Requirements

The target variable MUST be:
- Binary (only values 0 and 1)
- Present in the training data, absent from prediction data
- Not leaked through other features (e.g., don't include `order_status` as a feature if `converted` is derived from it)

### columns_to_drop Consistency

| Rule | Why |
|------|-----|
| Same list in `train.dig` and `predict.dig` | Feature alignment requires identical preprocessing |
| Include ALL ID and metadata columns | IDs are not predictive features and cause leakage |
| Include `user_id_col` explicitly | Auto-dropped defensively, but explicit is clearer |

### Common Mistakes to Avoid

**1. Feature leakage — including future information in features**
```yaml
# BAD — target-derived column in features
columns_to_drop: >-
  web_session_id,batch_id
# If 'conversion_date' is in the table and derived from the target, it leaks
# GOOD — drop it
columns_to_drop: >-
  web_session_id,batch_id,conversion_date
```

**2. Mismatched columns_to_drop between train and predict**
```yaml
# BAD — predict.dig has different columns
# train.dig:  columns_to_drop: web_session_id,batch_id,reference_date,ucp_id
# predict.dig: columns_to_drop: web_session_id,batch_id,ucp_id
# This will cause feature misalignment
# GOOD — identical lists in both files
```

**3. Using wrong model_type at prediction**
```yaml
# BAD — trained with xgboost, predicting with catboost
# The prediction pipeline loads the model from model store and validates the family
# Mismatch will raise an error
# GOOD — model_type in config.yml is used by both train and predict
```

**4. Not setting n_trials high enough for production**
```yaml
# BAD — 3 trials for a production model
n_trials: '3'
# GOOD — 30-50 for production
n_trials: '30'
```

## Workflow Template Location

The classification workflow template ships with this skill at `project_templates/classify/`. Never edit it directly — after configuring `config.yml` and adding data prep SQL in the working copy, deploy from `agent_outputs/<customer_slug>/classifier/workflow/classify/`.
