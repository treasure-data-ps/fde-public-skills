# AI Signals Next Best Action (Contextual Bandit) — Model Guide

For any question about the model: how it tunes, trains, evaluates and recommends, API parameters, other parameter values or policy types, changing its input or output tables. The template (`train.dig`, `predict.dig`, `config.yml`) is what this setup sends; this guide is what the API accepts and how the model behaves. `workflow-setup.md`, `dataprep-guide.md` and `output-tables-guide.md` are files of the setup skill (`fde-nba-ai-signal`).

**Public documentation:** https://docs.treasure.ai/products/customer-data-platform/machine-learning/ai-signals — share it after answering from this guide.

## 1. What it does

A **contextual bandit**: from a log of past decisions (which action a customer got, what the customer looked like just before, what happened after), it learns a policy that maps a customer's current context to the action with the highest expected reward. One model = one set of 2–100 actions = one recommended action per customer. Batch only.

| Solution | Does | Runs |
|---|---|---|
| `nba_tune` (optional) | Cross-validated off-policy search over preprocessing, the evaluation estimator and the policy; appends the trials. Stores no model | Single node |
| `nba_train` | Preprocesses, trains the policy by replaying the log, evaluates it off-policy, stores it under `model_name` | Single node |
| `nba_predict` | Loads the policy and picks the best action per customer | Distributed, sharded by a hash of the user ID |

| `model_type` | Policy | Choose when |
|---|---|---|
| `lin_ucb` (default) | Linear UCB — adds an uncertainty bonus (`epsilon` = alpha) | Default; keeps trying actions it knows little about |
| `lin_ts` | Linear Thompson sampling | Similar to UCB, randomized exploration; ignores `epsilon` |
| `lin_eps_greedy` | Linear model, explores at rate `epsilon` | Simple and easy to explain |
| `ipw_learner` | Inverse-propensity-weighted classifier (`base_classifier`: random forest / logistic regression) | Offline learning from a log with known or well-estimated propensities; non-linear context effects |
| `neural_lin_ucb` | Neural feature encoder + LinUCB | Large logs with non-linear context; training only — not searched by tuning; needs `neural_lin_ucb_params` |

Unsure → turn on tuning (it compares `lin_ucb` and `ipw_learner` by default), or train two projects with different `model_name`s and compare the policy value.

## 2. Input tables

Feature engineering happens upstream in `sql/input_features.sql` (`dataprep-guide.md`).

| Item | Training log | Prediction input |
|---|---|---|
| Grain | One row per logged action (a customer repeats) | **Exactly one row per customer** (the API keeps the last row per user; the template fails on repeats) |
| User | `user_column` — written back as `user_id` | Same |
| Action | Any type, encoded internally; **2–100** distinct values (more fails) | Not needed (ignored by the saved name) |
| Reward | Numeric (0/1 or a value); it must vary | Not needed |
| Timestamp | UNIX seconds or UTC text `YYYY-MM-DD HH:MM:SS`; used for the tuning time split | Required (the run date) |
| Features | Every other column is context — **numeric only** (no categorical encoding): counts, recency, sums, ratios, 0/1 flags | Same columns, names and types — a training column missing at prediction fails or silently shifts the context, depending on the imputer |
| Excluded | `exclude_columns` globs (pipe-separated) + action, reward, timestamp, user, `time`, the propensity column | Same |

Rule of thumb: several hundred rows per action at least, each action given to a mix of customers. An action given only to one segment can't be compared with the others for anyone else.

## 3. Parameters

### Training — `solution_name: nba_train`

| Argument | Template | Default | Notes |
|---|---|---|---|
| `model_name` | `${model_name}` | `nba_model_<input table>` | Overwritten by every run; predict loads it |
| `user_column`, `action_column`, `reward_column`, `timestamp_column` | config | `user_id`, `action`, `reward`, `timestamp` | Must exist in the input |
| `exclude_columns` | user + `user_id` + config | — | Pipe-separated `fnmatch` globs (`time|pre_*`); commas are **not** separators |
| `model_type` | config (untuned) | `lin_ucb` | §1 |
| `epsilon` | config (untuned) | `0.1` | 0–1; LinUCB alpha / ε-greedy rate |
| `impute_type` | config (untuned) | `knn` | `knn`, `hybrid`, `median`, `drop`, `none`; `knn` / `hybrid` → median above 50K rows |
| `scaler_type` | config (untuned) | `standard` | `standard`, `minmax`, `robust`, `maxabs`, `none` |
| `base_classifier` | config (untuned) | `random_forest` | `ipw_learner` only; plus `rf_n_estimators`, `rf_max_depth`, `rf_min_samples_split`, `lr_C`, `lr_max_iter` |
| `propensity_column` | — | — | Logged probability of the chosen action (randomized tests); with `propensity_type: true_propensity` |
| `propensity_type` | — | `logistic` | `logistic` (estimated), `uniform`, `none`, `true_propensity` |
| `tuning_results_table`, `tuning_run_id` | tuned branch | — | Fill every model setting **not** sent in the request from the best trials of that tuning run. If the rows can't be loaded, training logs "Could not load tuning results" and uses the API defaults — not the config values — while `nba_ais_run_log.model_type` still says `tuned` |
| `n_predictions` | — | `1` | Output is always the single best action |
| `max_ope_samples` | — | `200000` | Rows used for the off-policy evaluation |
| `max_training_samples_per_model` | — | 5M linear / 1M `ipw_learner`, `neural_lin_ucb` | Subsampling cap |
| `arm_feature_columns`, `neural_lin_ucb_params` | — | — | `neural_lin_ucb` only |

### Tuning — `solution_name: nba_tune`

| Argument | Template | Default | Notes |
|---|---|---|---|
| `action_column`, `reward_column`, `timestamp_column` | config | as training | **No `user_column`** — the template excludes the ID through `exclude_columns` |
| `hyperparam_tune_sample_ratio` | config | `0.01` | 0.001–1 of the 70% time-ordered tuning split |
| `ocv_phase0_k` | config | `5` | 2–10 folds, impute × scaler grid |
| `ocv_phase1_trials`, `ocv_phase2_trials` | config | `20`, `50` | 5–200 each |
| `ocv_k`, `ocv_max_k` | — | auto, `3` | OCV folds; auto targets ≥ 20 rows per action per fold |
| `ocv_sigma_coef` | — | `0.0` | Phase 2 scores mean − coef × std (higher = more conservative) |
| `ocv_ess_config` | — | on, min ESS 10 | Drops trials whose effective sample size is too small |
| `search_space` | — | see below | Sections `preprocessing`, `reward`, `ope`, `policy` only (deep-merged into the defaults) |

Default search space: impute `knn` / `hybrid` / `median`, scaler `minmax` / `standard`; reward model logistic regression `lr_C` 0.01–100; estimator `ipw` / `dm` / `dr` with lambda 0–1000; policy `ipw_learner` / `lin_ucb` with random-forest sizes and `epsilon` 0.01–5.

### Prediction — `solution_name: nba_predict`

| Argument | Template | Notes |
|---|---|---|
| `model_name` | `${model_name}` | The policy trained last under this name |
| `user_column`, `timestamp_column` | config | Action and reward are excluded by the names saved with the model |
| `exclude_columns` | as training | |

### Endpoint by region (`ml_batch_api_endpoint`, from `tdx status`)

| Site | Endpoint |
|---|---|
| US (us01) | `https://ml-batch-api.treasuredata.com` (or `https://ml-batch-api.us01.treasuredata.com`) |
| Japan (jp01) | `https://ml-batch-api.treasuredata.co.jp` |
| EU (eu01) | `https://ml-batch-api.eu01.treasuredata.com` |
| AP (ap02) | `https://ml-batch-api.ap02.treasuredata.com` |
| AP (ap03) | `https://ml-batch-api.ap03.treasuredata.com` |

Prerequisite: AI Signals includes `nba_train` and `nba_predict` (and `nba_tune` for tuning) for the account; otherwise the API answers that the solution is not enabled.

## 4. Workflow syntax

```yaml
+train_nba:
  http>: ${ml_batch_api_endpoint}/v1/runs
  method: POST
  retry: false                                # never submit the same run twice
  headers:
    - authorization: "TD1 ${secret:td.apikey}"   # keep exactly as in the template
    - X-TD-ML-SESSION-ID: ${session_id}
    - X-TD-ML-ATTEMPT-ID: ${attempt_id}
  content_format: json
  store_content: true                         # the poll reads the run id from the response
  content:
    input_table: ${sink_database}.${train_input_table}
    output_table: ${sink_database}.mltmp_nba_ais_train_${project_id}_${attempt_id}
    solution_name: nba_train
    version: ${ml_batch_api_version}
    solution_arguments:
      model_name: ${model_name}
      user_column: ${user_column}
      action_column: ${action_column}
      reward_column: ${reward_column}
      timestamp_column: ${timestamp_column}
      exclude_columns: "${user_column + '|user_id' + (exclude_columns ? '|' + exclude_columns : '')}"
      model_type: ${model_type}

+wait_for_training:
  http>: ${ml_batch_api_endpoint}/v1/runs/${JSON.parse(http.last_content).id}/status
  method: GET
  headers:
    - authorization: "TD1 ${secret:td.apikey}"
  store_content: false                        # keep the submitted run in http.last_content
```

- The status call answers **408** while the run is PENDING / RUNNING (`http>` keeps retrying), **400** when it FAILED or was CANCELLED (the task fails, with the error messages in the log) and **200** when it SUCCEEDED. `http>` keeps retrying a 408 on its own (up to the task time limit), so the polls need no `_retry` — one would only re-poll a failed run.
- Authentication: the API accepts only `TD1 <key>` or `Bearer <token>` in the `Authorization` header (anything else → 400 "Invalid key format"), so the template sends `"TD1 ${secret:td.apikey}"`, like the official NBA template. The key is provided by the AI Signals architecture — never ask the user to set `td.apikey`, and keep the header as in the template.
- The service appends to its output tables. The template writes training and prediction to per-attempt `mltmp_nba_ais_*` tables, copies them to the published tables and drops them.
- Unknown `solution_arguments` keys are ignored silently — a typo does not fail, it is just not applied. `solution_arguments` must stay under ~6 KB.
- Cancel a stuck run: `DELETE /v1/runs/<run_id>` with the same header (run id in the poll task log); then re-run the whole workflow, not a single task.

## 5. How it works

**Training:**

| # | Step |
|---|---|
| 1 | Load the log (subsampled above `max_training_samples_per_model`); check the user, action, reward and timestamp columns |
| 2 | Drop non-features; encode actions 0…n−1; impute (`impute_type`) and scale (`scaler_type`) the context |
| 3 | Train the policy by replaying the log row by row (linear policies) or fitting the IPW classifier |
| 4 | Off-policy evaluation on the same log (≤ `max_ope_samples`): the mean of SNIPW, DR, IPW, DRos and DM estimates of the reward per customer the policy would get, with a 95% interval |
| 5 | Store the policy and its preprocessing (action mapping, imputer, scaler, column names) under `model_name` |

The training metrics are **in-sample** off-policy estimates — read them against the logged average reward, not as a guaranteed result. Propensities are estimated (logistic) unless the log carries them; estimates are biased when the past policy was very deterministic.

**Tuning (OCV-DR, three phases):** time split 70% / 30% (with UNIX-second timestamps the split stays chronological, but the service's 1-hour gap between the parts is not applied) → sample `hyperparam_tune_sample_ratio` of the 70% → Phase 0 grid over impute × scaler (K-fold) → Phase 1 Optuna over the estimator (IPW / DM / DR) and its lambda with cross-validated off-policy evaluation → Phase 2 Optuna over the policy, scored by a lower confidence bound with effective-sample-size filtering → final evaluation of the best policy on the 30% hold-out against a random policy (`lift_vs_random_pct`). Training reads the best trial of each phase.

**Prediction:** load the policy → shard by user → keep one row per user → score every action for the context → pick the highest → decode back to the action label → append `user_id`, `predictions` (a one-element list).

**Choosing the setup:**

| Situation | Setting |
|---|---|
| First push, unknown data | `lin_ucb`, `epsilon: 0.1`, `median`, `standard`, tuning off |
| Input stable, `nba_tune` enabled | `enable_tuning: true`; sample ratio so ≥ ~50K rows are searched |
| Log from a randomized test (known assignment probabilities) | `propensity_column` + `propensity_type: true_propensity` — the most reliable estimates |
| Strong non-linear context effects, enough data | `ipw_learner` with `random_forest`, or tuning |
| Recommendations collapse onto one action | More / better context features; check that every action was given to varied customers; higher `epsilon` |
| Heavy outliers in spend or counts | `scaler_type: robust`, or log-transform in the SQL |

## 6. Output tables

| Table | Contents |
|---|---|
| Training `output_table` | `metric`, `value`: `estimated_policy_value`, `confidence_interval_lower`, `confidence_interval_upper` (+ `neural_linucb_active`) — copied with the session to `nba_ais_train_metrics`, pivoted into `nba_ais_run_log` |
| Tuning `output_table` (`nba_ais_tuning_results`) | One row per trial: `run_id`, `session_id`, `phase` (`baseline_random`, `phase0_preprocessing`, `phase1_ope`, `phase2_policy`), `phase_trial`, `is_best` (true once per phase — text or boolean), `overall_score`, `phase0_*` / `phase1_*` / `phase2_*` chosen values; the `baseline_random` row (random policy, lift 0) and the best `phase2_policy` row carry `estimated_policy_value`, `ci_lower`, `ci_upper`, `lift_vs_random_pct` (30% hold-out) |
| Prediction `output_table` | `user_id`, `predictions` (list of one action label) — flattened to `next_best_action` in `pred_output_table` |

No score, probability or ranking of the other actions is written — the output is the chosen action only. Columns and queries: `output-tables-guide.md` (setup skill) / `data-dictionary.md` (project agent).

### Validate

| Check | Healthy |
|---|---|
| Training log | 2–100 actions, hundreds+ rows each, reward rate > 0 for every action |
| Policy value vs logged reward | `estimated_policy_value` ≥ `logged_avg_reward`; `ci_lower` above it = a confident improvement; interval spanning it = no evidence yet |
| Interval width | Narrow relative to the value; very wide = too little data per action or extreme weights |
| Tuning (if on) | `lift_vs_random_pct` > 0 on the hold-out; phase-2 ESS not tiny |
| Recommendations | One row per customer; more than one action recommended unless one action truly dominates |

### Interpret

- The policy value is the **expected reward per customer** if every logged customer had received the policy's action, estimated from past data. Compare it with the logged average reward (what the past decisions earned).
- A recommended action is the best **among the logged actions** for that context; actions never logged can't be recommended.
- Context effects are associations in the log; a randomized hold-out after go-live is the real test (`workflow-setup.md` §4 check 6).

### Limits

- Top-1 output only; no per-action scores.
- 100 actions at most; numeric features only.
- Training metrics are in-sample; tuning's hold-out metrics are the out-of-sample view.
- Without logged propensities, estimates rely on estimated propensities and may be biased.

## 7. Common changes

| Change | How |
|---|---|
| Decision type | `nba_type` (`channel`, `time` + `time_grain` / `local_timezone`, `campaign`, `custom`) and `action_sources` — a new project per decision type |
| Action set | Sources in `sql/touchpoints_union.sql`, channel rules in `sql/touchpoints.sql`, `min_action_share` for rare actions |
| Reward definition or window | Conversion blocks of the union; `reward_window_days`, `reward_attribution`, `reward_type` (`dataprep-guide.md` §1–§2) |
| Context features | `sql/input_features.sql` (same in both modes); non-features → `exclude_columns` |
| Who is scored | `pred` branch of the `anchors` CTE in `sql/input_features.sql` |
| Policy type / exploration | `model_type`, `epsilon` (tuning off) |
| Tuning | `enable_tuning: true`; budgets in config; custom `search_space` in `+tune_nba` |
| Known propensities | `propensity_column`, `propensity_type: true_propensity` in `+train_nba` |
| Retrain / score cadence | Separate schedules in `train.dig` / `predict.dig` (`dataprep-guide.md` §6) |

### Troubleshooting (model)

Workflow failures (data prep, 401/403, polling): `workflow-setup.md` §4.

| Symptom | Cause | Fix |
|---|---|---|
| `Invalid columns: …` | A configured column is not in the input | Match `user_column` / `action_column` / `reward_column` / `timestamp_column` to the SQL |
| Too many actions | > 100 distinct actions | Group actions (offer type instead of offer ID) |
| Tuning: too few samples / unstable trials | Sample ratio too small for the actions | Raise `hyperparam_tune_sample_ratio`, lower `ocv_phase0_k` |
| `true_propensity` without a column | `propensity_type` set alone | Add `propensity_column` |
| Prediction fails on missing columns | Feature columns differ between modes | One SQL for both modes; same feature list |
| Every customer gets the same action | Weak context, or one action dominates the log | Better features; check the logged mix and rewards per action |
| A setting has no effect | Misspelled argument (ignored silently) or tuning overrode it | Check the request in `train.dig`; with tuning, only settings sent explicitly win |
