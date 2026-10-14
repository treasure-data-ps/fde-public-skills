---
name: fde-classifier
description: |
  Binary Classification (Classify) workflow for Treasure Data. Configures workflows that train and score binary classification models using Logistic Regression, XGBoost, or CatBoost with Optuna hyperparameter tuning, SHAP explainability, and parallel artifact writes. Supports any binary prediction use case — lead scoring, churn prediction, conversion propensity, fraud detection, campaign response, and more. Trigger on: classifier, classification, classify, lead scoring, lead score, churn prediction, churn model, conversion model, propensity model, binary classification, binary model, XGBoost, CatBoost, logistic regression, scoring model, predict churn, predict conversion, fraud detection, predict response, binary prediction, SHAP, feature importance.
---

# Binary Classification (Classify)

Generic binary classification workflow that trains and scores models to predict whether something will or will not happen. Supports Logistic Regression, XGBoost, and CatBoost with automated hyperparameter tuning, threshold optimization, SHAP explainability, and drift detection.

## How to Start

Read `../shared/playbook.md` — it defines the entry point (new vs. resume), the phase sequence, and when to read each shared pattern file. Follow that flow. This file provides the Classifier-specific context you need at each phase.

## Phase Summary

| Phase | What happens |
|---|---|
| Phase 1 | Data exploration — discover feature tables, confirm schema, identify target variable, check class balance |
| Phase 2 | Bootstrap `agent_outputs/` + `project_state.md` + Requirements Doc |
| Phase 3 | Push minimal workflow, validate training output tables |
| Phase 4 | Re-configure workflow from filled requirements, re-validate |
| Phase 5 | Parent Segment update + example audiences, then customer-facing documentation set |

---

## Classifier-Specific Context by Phase

### Phase 1: Data Exploration

Use `tdx-skills:tdx-basic` to explore the customer's TD databases. Follow these steps:

**Step 1 — Identify the use case, target variable, and where the label lives.**

Unlike the other ML solutions, the Classifier asks these questions *before* exploring: the target decides which tables and features matter and how the label is derived. Ask with the `AskUserQuestion` tool (pre-populated options from the table below, plus "Other") — never as a plain text list.

Ask the user:

> What binary outcome are you trying to predict?

Common patterns:

| Category | Use Case | Target Variable Example |
|----------|----------|------------------------|
| Sales & Revenue | Lead scoring / conversion prediction | `converted` (1 = won deal) |
| Sales & Revenue | Upsell / cross-sell propensity | `upsold` (1 = purchased upgrade) |
| Customer Retention | Churn prediction | `churned` (1 = cancelled) |
| Customer Retention | Subscription renewal | `renewed` (1 = renewed) |
| Marketing | Campaign response prediction | `responded` (1 = clicked/converted) |
| Product & Engagement | Trial-to-paid conversion | `converted_to_paid` (1 = subscribed) |
| Risk & Compliance | Fraud detection | `is_fraud` (1 = fraudulent) |
| Operations | Support ticket escalation | `escalated` (1 = needed escalation) |

Then ask: **Does an existing column already represent this outcome as a 0/1 value, or does it need to be derived?**

- If an existing column already represents it (e.g., a `churned` flag, a `status = 'cancelled'` field), record the table and column name.
- If it needs to be derived (e.g., "churned" isn't a stored flag but must be calculated from inactivity, or "converted" must be derived by joining a lead table to an orders table with a date cutoff), record the derivation logic in plain language now — the exact query will be built once the relevant tables are found in Steps 3–5. Do not assume the label already exists as a column; many use cases require a calculated label.

**Step 2 — Check for an existing Parent Segment.**

Ask the user:

> Is there an existing Parent Segment for this customer that you'd like to use as a source of features?

Use the `AskUserQuestion` tool with options: "Yes — use an existing Parent Segment (Recommended if one exists)", "No — explore raw database tables only". If yes, ask for the Parent Segment name.

If a Parent Segment is provided:
- Run `tdx ps desc "<Parent Segment Name>" -o <customer_slug>_ps_schema.json` to get its output database schema (see `tdx-skills:parent-segment-analysis`).
- Read the schema file. The `customers` table columns are candidate features that are **already aggregated and joined to the canonical ID** — no additional feature engineering or data prep SQL is needed to use these as model inputs. This is a meaningfully faster path than raw table feature engineering.
- The `behavior_*` tables are candidate raw feature sources if the customer wants more granular signals than what's already aggregated into the Parent Segment. Disregard any behavior tables that come back empty (not yet generated) — do not treat this as a blocker.
- Note the Parent Segment's join key (e.g., `cdp_customer_id`, `td_canonical_id`) as a candidate for `user_id_col`. If the schema exposes more than one plausible join key column, do not guess — ask the user which one to use (see Step 5 for reconciling this across multiple source tables).
- Present the `customers` table attribute list to the user (name, type) so they can flag which ones are relevant to this use case before moving on.

**Step 3 — Ask about additional raw tables, regardless of the Parent Segment answer.**

Whether or not a Parent Segment was provided, ask:

> Are there any other tables — in the same database or a different one — that should be considered as additional feature sources? (e.g., a support-ticket system in a separate database, a marketing database not yet joined to the Parent Segment)

The Parent Segment's `customers` table will not contain every signal a customer wants (e.g., a newly integrated data source, or a database that was never joined into ID Unification). Support **any number of additional databases** — do not assume all raw tables live in a single database.

For each database the user names (the Parent Segment's own output database, plus any additional ones):
- Run `tdx databases` if the user is unsure of exact names.
- Run `tdx tables "<database>.*"` to get the full table list for that database.

If no Parent Segment applies and the customer doesn't have one set up yet, this step becomes the primary discovery path — ask for at least one database to explore.

**Step 4 — Classify each table.**
For every table found in Step 3 (across all databases), run `tdx describe` to inspect its schema. Classify it into one of four buckets:

| Bucket | Criteria |
|---|---|
| **Feature source table** | Contains behavioral, transactional, or attribute data that can be engineered into predictive features. One row per event/record with a user ID + timestamp. |
| **Label / outcome table** | Contains the target variable (conversion, churn, purchase) or the data needed to derive it, per Step 1. May be the same table as a feature source. |
| **Profile / dimension table** | One row per customer with static attributes (demographics, segments, tiers). Can provide features but not behavioral signals. |
| **System / output table** | Workflow output, audit logs, ML result tables. Not a source table. |

**Step 5 — For each candidate feature source table, note down:**
- Full table name (including database — tables may come from different databases)
- User ID / join key column name. **The join key is not guaranteed to be the same column across every source table.** If a table's ID column doesn't match the join key confirmed in Step 2 (or the Parent Segment isn't in use), ask the user which column to use as the join key for that specific table, and whether a lookup/join table is needed to reconcile it back to the canonical ID.
- Timestamp column name
- Approximate row count and date range
- Key columns that could become features (counts, amounts, statuses, categories)

**Step 6 — Locate or construct the target variable.**

Using the label location/derivation logic captured in Step 1:
- If the label is an existing column, confirm its exact `database.table.column` now that the table has been discovered in Steps 3–5.
- If the label needs to be derived, write the derivation query now (e.g., a churn flag from `CASE WHEN days_since_last_order > 180 THEN 1 ELSE 0 END`, or a conversion flag from joining a leads table to an orders table). Present the derivation logic to the user for confirmation before using it in the class balance check below.

**Step 7 — Check class balance for the target variable.**

```sql
SELECT
  <target_variable_column_or_expression>,
  COUNT(*) AS cnt,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM <database_name>.<label_table>
GROUP BY 1
ORDER BY 1;
```

Replace `<target_variable_column_or_expression>`, `<database_name>`, and `<label_table>` with the actual values or derivation expression confirmed in Step 6.

**Pass criteria:**
- Both classes (0 and 1) have rows
- Minority class is at least 1% of total (if < 1%, the workflow's `class_balance_strategy: 'balanced'` may not be sufficient — flag to the user)
- If heavily imbalanced (>95:5), recommend `optuna_metric: 'auc_pr'` and `xgb_eval_metric: 'aucpr'`

**Step 8 — Present findings to the user before proceeding.**
Show a unified table of ALL candidates — Parent Segment attributes (if applicable) AND raw feature source tables — with a `Source Type` column (`Parent Segment attribute` / `Raw table — needs feature engineering`), the join key used for each, your recommendation (include / exclude), and a one-line reason for each. Use the `AskUserQuestion` tool — never as a plain text list.

**Solution slug for `agent_outputs/`:** `classifier`

### Phase 2: Requirements Doc

Before writing anything, bootstrap `agent_outputs/` per `../shared/local_outputs.md` and create `agent_outputs/<customer_slug>/classifier/project_state.md` per `../shared/project_state.md`.

This phase has two parts — a live interview that unblocks Phase 3, and a customer-shareable artifact that feeds Phase 4.

**Part A — Live interview (synchronous).**
Run Steps 3a–3i in `workflow-setup/references/requirements_doc.md` with the user now, using `AskUserQuestion`. This gathers enough to configure a real (not blindly-defaulted) minimal workflow in Phase 3 — use Phase 1 findings plus these answers.

Key questions the live interview must answer: use case description, target variable name/definition and whether it exists or needs deriving, user ID column and any per-table join key exceptions, Parent Segment (if any) and its join key, feature source tables across all databases in use, training time window, prediction time window, model type preference (XGBoost recommended), precision/recall tradeoff preference, output database name, columns to exclude from features.

**Part B — Customer-shareable doc (asynchronous).**
Doc title: `Classification Requirements Gathering - <Customer>`
File: `agent_outputs/<customer_slug>/classifier/requirements.md`

Write this doc per `../shared/requirements_doc_pattern.md`, using the canonical template structure in `workflow-setup/references/requirements_doc.md` Step 7 as the section-to-answer mapping. Unlike a blank customer-fillable form, **pre-fill every section with what was learned in Part A and Phase 1** — this saves the customer from re-answering things already discovered, and focuses their attention on judgment calls only they can make (business context, feature relevance, edge cases). Give the user the file path to share with the customer and update `project_state.md`. This is the doc Phase 4 reads back.

### Phase 3: Push Minimal Workflow

**Workflow template:** `project_templates/classify/`
**Working copy:** `agent_outputs/<customer_slug>/classifier/workflow/classify/`
**Config file:** `config.yml` (inside the working copy)

For the minimal push, populate `config.yml` with what you know from Phase 1 (database, user ID column, target variable, model type). Use Phase 2 answers if already available; otherwise use safe defaults.

Read `workflow-setup/references/workflow_setup_guide.md` for full setup instructions.
Read `workflow-setup/references/yaml_structure.md` for the parameter reference.
Read `workflow-setup/references/parameter_guide.md` for non-technical parameter explanations.
Use `workflow-setup/references/input_params_template.yml` as the starting point — write the result to `config.yml` in the working copy (the deployed config file is `config.yml`, not `input_params.yml`).

**Before any push command:** Read `../shared/push_pattern_td_workflows.md` for the template copy step, the mandatory project name confirmation gate, and push mechanics, and `workflow-setup/references/deploy_instructions.md` for the Classifier-specific steps (including the required `apikey` secret). Do not run `tdx wf push` or `tdx wf upload` until this file has been read and the project name confirmed with the user via `AskUserQuestion`.

After the workflow run finishes, validate output tables following instructions in `workflow-setup/references/eval.md`.

After validation, update `project_state.md`: Phase 3 complete, workflow project name, push date.

### Phase 4: Update Workflow with Customer Requirements

After reading the filled requirements doc, present a summary of the parameter changes you plan to make before touching any files. Key areas that typically change between Phase 3 and Phase 4:

- Target variable name and definition (customer may have a more precise label)
- `columns_to_drop` list (add non-feature columns discovered during data prep)
- `fbeta_beta` and `threshold_strategy` (based on customer's precision/recall preference)
- `model_type` (if customer prefers a different model)
- Training/prediction time windows (`look_back_months_training`, `train_end_months_from_now`, `look_back_months_prediction`)
- `n_trials` (increase for production runs)
- Data prep SQL (the main customization point — feature engineering queries)

Read `workflow-setup/references/workflow_setup_guide.md` for update mechanics. Edit `config.yml` in the working copy, then re-push from there.
Re-run the workflow and re-validate output tables (same checks as Phase 3).

### Phase 5: Parent Segment & Customer Documentation

**Step 1 — Parent Segment attributes + example audiences.**
Read `../shared/parent_segment_update.md` for the process (approval gates, push mechanics, `attributes:` placement rules).
Read `prod-docs/references/parent_segment.md` for the Classifier-specific "what" — which attribute columns (`predicted_proba`, `predicted_label`, `score_bucket`) and which example segments to create based on the use case (lead scoring, churn, campaign response). Do not read this file until the user has approved the plan in Step 1 of `parent_segment_update.md`.

**Step 2+ — Documentation files.**
Read `../shared/customer_docs_pattern.md` for the doc set. Write all files to `agent_outputs/<customer_slug>/classifier/docs/`.

Classifier-specific content for each doc is in `prod-docs/references/`:

| Doc file | Reference file |
|---|---|
| `docs/architecture.md` | `prod-docs/references/runbook.md` (architecture section) |
| `docs/runbook.md` | `prod-docs/references/runbook.md` |
| `docs/behavior.md` (customer-facing overview) | `prod-docs/references/customer_docs.md` |
| `docs/eval_results.md` | `workflow-setup/references/eval.md` results from the final run |
| `docs/access_ownership.md` (technical handoff) | `prod-docs/references/technical_handoff.md` |

---

## Quick Reference

- **Workflow template**: `project_templates/classify/` (read-only; copy to `agent_outputs/<customer_slug>/classifier/workflow/classify/`)
- **Default TD workflow project name**: `classify`
- **Entry points**: `train.dig`, `predict.dig`
- **Config file**: `config.yml` (inside the working copy)
- **Key training outputs**: `{tp}run_log`, `{tp}feature_importance`, `{tp}shap_directional`, `{tp}test_predictions` in the sink database
- **Key prediction outputs**: `{tp}predictions`, `{tp}prediction_shap`, `{tp}prediction_run_log` in the sink database
- **Models**: Logistic Regression, XGBoost, CatBoost (with Optuna tuning)
- **Solution slug**: `classifier`

## Companion skill (separate entry point)

Registered as its own skill — it triggers directly from user prompts, no need to route through this file:

- **`fde-classifier-insights-agent`** — query the classification output tables to answer model performance, feature importance, SHAP explanation, score distribution, and setup/configuration questions, or generate the standalone Classification Summary Dashboard. Follow this companion skill whenever the user asks for dashboards or analytical deep dives after workflow setup.

## How It Works

1. **Data Prep**: Customer-specific SQL creates feature tables from raw behavioral/transactional data
2. **Train**: Load features + binary target → stratified split → preprocess → Optuna tuning → fit model → threshold selection → evaluate → SHAP → write artifacts
3. **Predict**: Load trained model → load new data → preprocess identically → score → per-row SHAP (positives only) → PSI drift check → write outputs
4. **Explain**: SHAP values explain every prediction — which features pushed the score up or down, globally and per-record
