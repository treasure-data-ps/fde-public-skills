---
name: fde-classifier-insights-agent
description: |
  Classification model analysis and setup agent. Queries trained classification model output tables (predictions, feature importance, SHAP explanations, run logs) to answer questions about model performance, feature drivers, score distributions, individual record explanations, drift monitoring, and workflow setup/configuration. Trigger on: classifier analysis, classification insights, lead score analysis, feature importance, SHAP analysis, model performance, prediction analysis, churn model analysis, classification results, explain prediction, why did this score, model metrics, classification setup, classifier configuration, how to configure classifier, classifier parameters, "show me classifier dashboard", "open classifier dashboard", "get classifier dashboard", "classifier dashboard", "generate classifier dashboard", "load classifier dashboard", "classification dashboard", "view classifier dashboard".
---

## Initialization

Before answering any question, read these shared reference files (once per session):
1. Read [business-context.md](references/business-context.md) — customer business model, use case definition, target variable meaning
2. Read [data-dictionary.md](references/data-dictionary.md) — output table schemas, column descriptions, cross-table patterns
3. Read [visualization-instructions.md](references/visualization-instructions.md) — chart standards, TD color palette, render_chart/render_react vs HTML-template usage
4. Read [dashboard_template.html](references/dashboard_template.html) ONLY when the user asks for an HTML / shareable / exportable / standalone dashboard. The template's header comment lists every `{{TOKEN}}` and the queries that feed each section.

## Routing Logic

**Load analysis references for:**
- Model performance questions (precision, recall, AUC, threshold, overfitting)
- Feature importance and SHAP analysis (global and per-record)
- Score distribution and bucket analysis
- Prediction deep dives (why does record X score high/low?)
- Drift monitoring (PSI between training and prediction)
- Model comparison across training runs
- Data validation and quality checks

**Load setup/configuration references for:**
- How to configure `config.yml` parameters
- What each parameter does and how to choose values
- When to use XGBoost vs CatBoost vs Logistic Regression
- How to set precision/recall tradeoff (`fbeta_beta`)
- How to add features or change the data prep SQL
- Troubleshooting failed runs or poor model quality

For setup questions, also read `../../workflow-setup/references/parameter_guide.md` for plain-language parameter explanations and `../../workflow-setup/references/yaml_structure.md` for the full parameter reference.

## Execution Workflow

1. Read shared references (once per session)
2. Route — determine if this is an analysis or setup/configuration question
3. For analysis: Query data via `tdx query -d ${sink_database} "SQL"`
4. Analyze — generate insights from query results
5. Visualize — create charts using `render_chart` / `render_react`
6. Present — unified response following output format

## Query Rules

- All output tables are in the **${sink_database}** database
- Table names use the configured prefix: `${table_prefix}` (may be empty)
- **Profile identifier portability:** Row-level output tables may expose the configured source identifier under `user_id`, but customer workflows can originate from `td_consumer_id`, `canonical_id`, `cdp_profile_id`, or another column. Before a profile lookup or join, run `DESCRIBE ${sink_database}.${table_prefix}predictions` (or read the workflow's user-ID parameter) and use the resolved column; never assume `canonical_id` or `user_id` in a customer source table. The dashboard generator records the detected identifier as metadata.
- Always filter by the latest `session_id` (training) or `pred_session_id` (prediction)
- Use `LIMIT 20` for result sets
- Include `ORDER BY` for deterministic results
- Never hallucinate data — all numbers must come from actual query results
- Use exact column names from the data dictionary — do not assume a `test_`/`train_` prefix exists; `run_log` and `train_run_log` share the same unprefixed column names (`precision`, `recall`, `fbeta`, `auc_roc`, etc.)
- Round metrics to 4 decimal places; percentages to 1 decimal place
- Metric columns observed in live deployments are already numeric (`double`/`bigint`) — `CAST` is unnecessary but harmless. Confirm with `DESCRIBE`/`list_columns()` before assuming a column's type or name; table-generation logic can drift between template versions
- **Scale check:** in `run_log`/`train_run_log`, `precision`/`recall`/`fbeta`/`test_accuracy` are on a 0–1 scale, but `f1_score`/`auc_roc`/`aucpr` are on a 0–100 scale. Rescale before comparing or charting them together (see `data-dictionary.md`)

## Visualization Rules

Read [visualization-instructions.md](references/visualization-instructions.md) for chart standards and color palettes.
Use `render_chart` for standard charts (bar, line, pie, area, scatter, horizontal-bar, stacked-bar, radar, funnel).
Use `render_react` for complex interactive dashboards (Recharts + Tailwind CSS).

Create 3-7 charts per analysis. Always create separate individual charts — never subplots.

## Output Format

**Structure: Charts first (90%), then text (10%)**

1. **Rendered charts** (3-7 visualizations per response)
2. **Key Insights table** (NOT bullet points):

| **Type** | **Finding** | **Metric** | **Priority** |
|----------|-------------|------------|--------------|
| Performance | **Model AUC-ROC** score | **0.XX** | Critical |
| Feature | **Feature Name** is top driver | **+0.XX SHAP** | High |
| Risk | **PSI drift** detected | **0.XX** | Medium |

3. **Recommendations** (maximum 3, as bullet points with bold metrics)

Rules:
- Bold all metrics: **0.85**, **72.3%**, **feature_name**
- No explanatory text like "Based on data" or "This shows"
- No raw JSON output — only rendered charts
- Insights in table format, not bullets

## Critical Business Rules

- The prediction score is a **probability** (0.0–1.0) — higher score = more likely to be positive class
- **Threshold** divides predictions into positive/negative labels — scores above threshold = predicted positive
- **SHAP values** explain each prediction — positive SHAP = pushes score up, negative SHAP = pushes score down
- Always reference the `best_threshold` from `run_log` when discussing classification decisions
- When showing feature importance, use SHAP-based importance (not native gain) for consistency
- **PSI** (Population Stability Index): < 0.10 = stable, 0.10–0.25 = monitor, > 0.25 = retrain
- Never approximate metrics (use **0.847** not "~85%")
- Use the customer's business terminology for the target variable (e.g., "conversion" not "positive class")
- Outcome classes: **TP** (True Positive), **TN** (True Negative), **FP** (False Positive), **FN** (False Negative)

## Pre-Built Analysis Workflows

### 1. Model Performance Summary
Query `run_log` and `train_run_log` for the latest training run. Show precision, recall, F-beta, AUC-ROC, AUC-PR, and threshold. Compare train vs test metrics for overfitting check. Visualize with bar chart (train vs test metrics) and gauge chart for AUC.

### 2. Feature Importance Analysis
Query `feature_importance` and `shap_directional` for the latest session. Show top 20 features by SHAP importance with directional indicators (increases/decreases score). Visualize with horizontal bar chart (importance) and diverging bar chart (directional SHAP).

### 3. Score Distribution Analysis
Query `predictions` and `prediction_bins` for score distribution. Show score histogram, bucket counts, and percentage of records in each bucket. Compare with training score distribution from `probability_train_bins` for drift. Visualize with histogram and overlay comparison chart.

### 4. Individual Record Explanation
For a specific user/record, query `predictions` for the score and `prediction_shap` for the top SHAP drivers. Show the overall score, predicted label, and the top features pushing the score up and down. Before trusting `predicted_label`, compare `predictions.threshold_applied` against `run_log.best_threshold` for the matching training session — if they differ, recompute the classification as `lead_score >= best_threshold` instead (see `data-dictionary.md` "Known threshold-fallback bug"). Visualize with waterfall chart showing SHAP contributions.

### 5. Confusion Matrix & Threshold Analysis
Query `test_predictions` for outcome class distribution (TP/TN/FP/FN). Show confusion matrix, score distributions per outcome class, and how changing the threshold would affect precision/recall using `roc_curve` data. Visualize with heatmap (confusion matrix) and line chart (precision-recall curve).

### 6. Feature Correlation & VIF Analysis
Query `feature_correlations` (columns `feature_a`/`feature_b`/`correlation`, not `feature_1`/`feature_2`) and `target_correlations` (column `feature`, not `feature_name`) to show feature relationships. Identify highly correlated feature pairs. Show which features were dropped and why from `corr_drop_report`. `vif_scores` only exists when `model_type = 'logistic'` — confirm with `DESCRIBE`/`list_columns()` before querying it; for xgboost/catboost deployments this table is absent and should be skipped, not treated as empty. Visualize with heatmap (correlation matrix).

### 7. Training History & Model Comparison
Query `run_log` across multiple sessions to show metric trends over time. Compare precision, recall, AUC across retraining runs. Identify degradation or improvement. Query `optuna_trials` to show hyperparameter search results. Visualize with line chart (metrics over sessions) and scatter plot (trial results).

### 8. Drift Monitoring
Query `prediction_run_log` for PSI values across prediction runs. Compare score distributions between `probability_train_bins` and `prediction_bins`. Flag if PSI > 0.25 (retrain needed) or > 0.10 (monitor). Visualize with line chart (PSI over time) and overlay histogram (train vs prediction distribution).

### 9. Setup & Configuration Guide
For setup questions, read `parameter_guide.md` and present the relevant parameter explanations. Help users choose between model types, set `fbeta_beta` based on their precision/recall preference, configure training windows, and understand output tables. Text-heavy response — charts only if comparing model type characteristics.

### 10. Data Validation
Query `run_log` for latest training metadata: feature count, record count, class distribution. Query `feature_list` for active features. Verify no ID/date columns leaked into features. Check that both classes are represented. Text-only output — no charts.

### 11. Generate an HTML model-summary dashboard / Build a shareable dashboard for the latest run

When the user asks for an **HTML / shareable / exportable / standalone dashboard** (NOT an in-chat React component), use the templated workflow below. This produces a single self-contained file that opens in any browser, includes the TD palette, and is organized into **four tabs**:

- **Tab 1 — Model Performance**: run config + evaluation metrics (test set) + Confusion Matrix + overfitting generalization gaps
- **Tab 2 — Feature Drivers**: top SHAP feature importance + directional SHAP impact + details table
- **Tab 3 — Score & Drift**: KPIs + prediction score distribution histogram + PSI drift metrics
- **Tab 4 — Historic Tracker**: trend lines for metrics and audience volume across runs. Degrades gracefully when only 1 session exists.

**Inputs:**
- Customer name (string)
- `sink_database` (required — the database holding the classifier output tables; ask the user or read it from `project_state.md`)
- `table_prefix` (defaults to empty or table prefix from workflow)

**Output path** — the generator writes to:
```
agent_outputs/<customer_slug>/classifier/dashboards/classifier_summary_dashboard.html
```
relative to the user's working directory (git-ignored — see `../../../shared/local_outputs.md`), where `<customer_slug>` is the lowercase, hyphenated customer name (e.g. `acme-corp`).

**Fast Generation Workflow (authoritative):**

1. Read `references/dashboard_template.html` once per session for layout and token semantics.
2. Run the parallel generator from the user's working directory (`<classifier_insights_dir>` is the absolute path of the directory containing this `SKILL.md`):
   ```bash
   SOURCE_DB=<sink_database> TABLE_PREFIX=<table_prefix> \
   node <classifier_insights_dir>/references/generate-data.js \
     <customer_slug> "<Customer Name>"
   ```
   Or use positional arguments:
   ```bash
   node <classifier_insights_dir>/references/generate-data.js \
     <sink_database> <customer_slug> "<Customer Name>"
   ```
   The script runs Q1–Q8 concurrently, resolves the optional profile identifier from `DESCRIBE <prefix>predictions`, substitutes every token, validates the rendered HTML, and writes the standalone dashboard.
3. Open `agent_outputs/<customer_slug>/classifier/dashboards/classifier_summary_dashboard.html` with `mcp__work__open_file` (or `open <path>`).
4. Do not use `render_react` or manually replace tokens for this standalone dashboard.

**Manual query/token procedure (fallback only — the generator above is the default):**

1. **Read the template**: `references/dashboard_template.html` is the source of truth for layout, charts, tabs, and TD palette. Read it once per session.

2. **Run the eight documented queries** against the customer's `sink_database` and using `table_prefix`. Default to `MAX(session_id)` from `{tp}run_log` and `MAX(pred_session_id)` from `{tp}prediction_run_log` for latest sessions.
   - **Q1** — Latest training run metrics from `{tp}run_log`
   - **Q2** — Latest training overfitting metrics from `{tp}train_run_log`
   - **Q3** — Feature global SHAP importance from `{tp}feature_importance`
   - **Q4** — Feature SHAP directional influence from `{tp}shap_directional`
   - **Q5** — Latest prediction run metadata from `{tp}prediction_run_log`
   - **Q6** — Score distribution bins from `{tp}prediction_bins`
   - **Q7** — Historic training metrics from `{tp}run_log` (order by session_id ASC)
   - **Q8** — Historic prediction runs from `{tp}prediction_run_log` (order by pred_session_id ASC)

3. **Compute derived values** (see `data-dictionary.md` for the scale/column-name caveats — `run_log`/`train_run_log` have no `test_`/`train_` prefix, and `auc_roc`/`aucpr`/`f1_score` are 0–100 while `precision`/`recall`/`fbeta` are 0–1):
   - `test_auc_roc` token = `run_log.auc_roc / 100` ; `test_aucpr` token = `run_log.aucpr / 100` ; `test_f1` token = `run_log.f1_score / 100`
   - `test_precision`/`test_recall`/`test_fbeta` tokens = `run_log.precision`/`recall`/`fbeta` as-is (already 0–1)
   - `test_tp`/`test_tn`/`test_fp`/`test_fn` tokens = `run_log.true_positives`/`true_negatives`/`false_positives`/`false_negatives`
   - `train_auc_roc` token = `train_run_log.auc_roc / 100` ; `train_fbeta`/`train_precision`/`train_recall` tokens = `train_run_log.fbeta`/`precision`/`recall` as-is
   - `auc_gap` = `train_auc_roc - test_auc_roc` (both already rescaled to 0–1; format to 4 decimal places)
   - `fbeta_gap` = `train_fbeta - test_fbeta` (format to 4 decimal places)
   - `test_total` = `test_tp + test_tn + test_fp + test_fn`
   - Percentages for Confusion Matrix cells (e.g. `test_tp / test_total * 100`, formatted with 1 decimal place + `%`)
   - `psi_status_pill`:
     - if `psi < 0.10`: `<span class="pill ok">Stable (${psi})</span>`
     - if `psi >= 0.10 AND psi <= 0.25`: `<span class="pill warn">Monitor (${psi})</span>`
     - if `psi > 0.25`: `<span class="pill error">Retrain (${psi})</span>`
   - `predicted_positive_pct`: `predicted_positive_count / records_scored * 100` (format with 1 decimal place + `%`)
   - `run_count` = number of distinct sessions in training metrics history
   - `pred_run_count` = number of distinct prediction runs in prediction history
   - **Threshold sanity check:** compare `prediction_run_log.threshold_applied` (or `predictions.threshold_applied`) against `run_log.best_threshold` for the matching training session. If they differ, the deployment has likely hit the known threshold-fallback bug — `predictions.predicted_label`/`score_bucket` cannot be trusted, and `predicted_positive_count` should instead be computed as `COUNT(*) WHERE lead_score >= best_threshold` from `run_log`. Surface this explicitly in `tab3_insights_html_li` if detected.

4. **Generate `shap_directional_rows`** — one `<tr>` per feature for the top 15 features in DESC order of importance.
   Row shape:
   ```html
   <tr><td><strong>{feature_name}</strong></td><td><span class="pill {class}">{direction}</span></td><td class="num">{mean_shap}</td><td class="num">{confidence}</td><td class="num">{pct_up}</td><td class="num">{pct_down}</td></tr>
   ```
   where `{class}` is `ok` for 'increases score', `error` for 'decreases score', `warn` for 'mixed', and empty/muted for 'neutral'.

5. **Generate `score_bins_table_rows`** — one `<tr>` per bucket from Q6:
   ```html
   <tr><td><strong>{bin_range}</strong></td><td class="num">{count}</td><td class="num">{percentage}%</td><td>{strategy}</td></tr>
   ```
   Define reasonable action strategies based on the score bins (e.g. scores >= 0.8: "Very High - Direct Engagement", scores between 0.5-0.8: "High - Priority Nurture", scores between 0.2-0.5: "Medium - standard campaigns", scores < 0.2: "Low - suppression / passive tracking").

6. **Build the historic-tracker series** from Q7 and Q8 (`run_log` has no `created_at`/`run_timestamp` — derive dates from `time` via `TD_TIME_FORMAT(time, 'yyyy-MM-dd', 'UTC')`):
   - `historic_run_labels_json` — array of run dates / session_ids in ASC order, e.g. `["2026-04-18","2026-05-18"]`.
   - `historic_session_ids_json` — array of session_ids parallel.
   - `historic_auc_roc_json` — array of `run_log.auc_roc / 100` per row.
   - `historic_fbeta_json` — array of `run_log.fbeta` as-is.
   - `historic_precision_json` — array of `run_log.precision` as-is.
   - `historic_recall_json` — array of `run_log.recall` as-is.
   - `historic_pred_run_labels_json` — array of prediction dates (from `prediction_run_log.run_timestamp`, or `pred_session_id` if unavailable) parallel.
   - `historic_records_scored_json` — array of `records_scored`.
   - `historic_psi_json` — array of `psi`.

7. **Handle the single-run case** (when `run_count = 1` or `pred_run_count = 1`):
   - Set `historic_single_run_callout` to:
     ```html
     <div class="callout"><strong>Only one run available.</strong> The Historic Tracker shows the current snapshot. Trend lines will populate after subsequent workflow runs. Use Tab 1, 2, and 3 for the full latest-run analysis.</div>
     ```
   - In `tab4_insights_html_li`, frame insights as expectations and what to watch for in the next run rather than describing observed shifts.
   - If `run_count >= 2` AND `pred_run_count >= 2`, set `historic_single_run_callout` to empty string `""`.

8. **Generate the four insights sections** (`tab1_insights_html_li`, `tab2_insights_html_li`, `tab3_insights_html_li`, `tab4_insights_html_li`). Each is 4-7 `<li>` bullets. Each must:
   - Start with the headline number/finding (NO filler like "Based on data...")
   - Wrap key metrics in `<strong>` tags (counts, percentages, feature names)
   - Be customer-specific — call out actual metrics, top features, drift indicators

9. **Substitute every `{{TOKEN}}`** in the template. Important steps:
   - **First, strip the leading documentation HTML comment** at the top of the template. The block between `<!DOCTYPE html>` and `<html lang="en">` contains literal `{{...}}` and `{{TOKEN}}` strings as part of the documentation, and they will pollute the output if substituted. Regex: `^<!DOCTYPE html>\s*<!--.*?-->\s*` → `<!DOCTYPE html>\n` (DOTALL flag).
   - Then perform token replacement on the cleaned template.
   - Validate before writing: no `{{` or `}}` should remain in the output file (run `re.findall(r'\{\{[^}]+\}\}', out)` and assert it returns empty).
   - Every JSON token must be valid JSON (no trailing commas, double-quoted strings)
   - Counts use thousands separators (`21,465` not `21465`); percentages use 1 decimal place (`42.1%` not `42%` or `~42%`)

10. **Write the file** with the `Write` tool. Then use `mcp__work__open_file` to surface it in the artifact panel.

11. **Summarize for the user** — state the file path, the 4 tabs, and 1-2 most striking findings. Don't paste raw JSON or chart code into the chat.
