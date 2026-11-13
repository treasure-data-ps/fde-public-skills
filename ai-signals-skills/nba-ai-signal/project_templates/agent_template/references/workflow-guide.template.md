# NBA AI Signal — Workflow Guide (<project name>)

Use this document to answer questions about how **this customer's deployed** Next Best Action workflow works end to end: its structure, execution order, the input SQL (actions, reward, context, scoring population), configuration, model settings, customizations and the tables each step writes. For how the model works, see `ai-signals-guide.md`; for this customer's business definitions, see `business-context.md`; for table schemas, see `data-dictionary.md`.

<!-- Build instructions (Phase 4 interim or Phase 5 final — remove this comment and every `fill` block when done):
- Interim (Phase 4): describe the setup deployed so far; mark assumed defaults "to confirm"; sections with nothing yet
  (e.g. Parent Segment) say "Not done yet — Phase 5". Final (Phase 5): update the interim file in place, keep the history.
- Save the filled copy as references/workflow-guide.md in the agent staging folder. Never install this .template.md file.
- Sources, in priority order: the deployed working copy (workflow/config.yml, workflow/sql/input_features.sql — always read,
  it is project code — and workflow/*.dig: nba_ais.dig, train.dig, predict.dig, data_prep.dig), project_state.md,
  docs/architecture.md, the latest validated run (nba_ais_run_log, {{pred_table}}). Describe what is DEPLOYED,
  never template defaults.
- Explain parameters in plain words (meanings from workflow/README.md) and quote exact values and expressions in backticks.
  No YAML blocks, no secrets, no personal names or email addresses (write the role or "alert recipient").
- Record "as of" dates. Refresh this file whenever the workflow config, the input SQL or the .dig files change.
-->

**Status:** <Interim — pre-production | Final — production>  ·  **As of:** <date of the deployed revision this guide describes>

---

## Workflow Overview

<!-- fill:
- One paragraph: the decision the workflow makes for this customer, the actions, the success measure, how the
  recommendations are used
- TD workflow project name and ID, entry point (nba_ais; train / predict if scheduled separately), last pushed revision
  and date (workflow/tdx.json)
- Sink database, model name (`model_name`), recommendations table (`pred_output_table`, `<pred_output_table>_history`),
  working copy path (<engagement dir>/workflow/)
- The AI Signals NBA solutions: endpoint (`ml_batch_api_endpoint`, region), tuning on / off, `model_type`
- Schedules (or "manual runs only"), failure alert (enabled / commented out)
-->

## End-to-End Pipeline

<!-- fill:
- Tree as deployed: nba_ais → train (data_prep → check → [tune → poll] → train → poll → log metrics → log run) →
  predict (data_prep → check → predict → poll → latest actions → history → action stats)
- Mark any step that is disabled, scheduled separately or added for this customer, with the reason
- One line per stage on what it produces
-->

## Input SQL

<!-- fill — from workflow/sql/touchpoints_union.sql, touchpoints.sql and input_features.sql:
- Decision: `nba_type` (and `time_grain`, `local_timezone` for time), the decision touches (`action_sources`), the final list of
  action labels and how they were grouped (`min_action_share`, campaign themes), the training window (`train_window_days`)
- Union: one line per source block — `src_name`, table, ID, time column, filters, how its channel is set (channel_hint, UTM
  from the URL / referrer, traffic-source column), conversions (`is_conversion`, `conversion_value`)
- Channel rules added for this customer in touchpoints.sql (UTM value → channel) and `session_gap_minutes`
- Reward: the success rule in plain words, the window (`reward_window_days`), `reward_attribution`, `reward_type`, the latest average reward
- Context: one line per source CTE — table, what it measures, the window (`feature_lookback_days`), the feature names
- Scoring population: source, eligibility and exclusions, the ID column (`user_column`)
- `reference_date` ('' = run date), `exclude_columns` and why each column is excluded
- Tables reviewed in Phase 1 but not used, with the reason (from project_state.md)
-->

## Model Settings as Deployed

<!-- fill:
- Table: parameter → deployed value → what it means for this customer → why this value (from project_state.md decisions)
- Cover: `model_name`, `enable_tuning`; untuned: `model_type`, `epsilon`, `impute_type`, `scaler_type`, `base_classifier`;
  tuned: the budgets (`hyperparam_tune_sample_ratio`, `ocv_phase0_k`, `ocv_phase1_trials`, `ocv_phase2_trials`) and the
  settings the latest tuning run chose; any argument added to the .dig requests (propensity column, search space)
- Latest validated results with the session ID: training rows, actions, logged average reward, estimated policy value
  with its interval, estimated lift, tuning hold-out lift (if any), customers scored and the recommended mix
-->

## Step-by-Step Reference

<!-- fill — one subsection per .dig file that runs (data_prep, train, predict):
- Purpose in one sentence
- Steps in order → output table of each step
- The guards (`+assert_*`) and what makes them fail
-->

## Customizations Beyond the Template

<!-- fill:
- Table: file → change → reason → date (from project_state.md and docs/runbook.md)
- Always: the input SQL (`sql/input_features.sql`) and any added feature tables in data_prep.dig; plus .dig edits (schedule,
  alert, polling, added API arguments)
-->

## Output Tables

<!-- fill:
- Table: table → produced by (.dig) → grain → purpose; note which are appended (nba_ais_*, {{pred_table}}_history) and which
  are replaced (input tables, {{pred_table}})
- {{pred_table}} (the Parent Segment attribute table): `user_id`, `next_best_action`, `scored_date`
- Parent Segment name and how {{pred_table}} is joined (key) — or "Not done yet — Phase 5"
-->

## Changing or Re-running the Workflow

<!-- fill:
- Pointer to runbook.md for the re-deploy, run and monitoring commands
- Where to change the common requests: action set (anchors CTE), success definition or window (reward CTE,
  `reward_window_days`), context (SQL + `exclude_columns`), who is scored (pred branch), tuning, policy type,
  retrain vs scoring schedule
- Reminder that after a config or SQL change this guide and the agent must be refreshed
-->
