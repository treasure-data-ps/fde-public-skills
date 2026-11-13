# Data Dictionary — NBA AI Signal (Next Best Action) Output Tables

All tables live in `{{sink_database}}`. The workflow writes its logs under **fixed names** (`nba_ais_*`, no project prefix) and the recommendations to `{{pred_table}}` (latest) and `{{pred_table}}_history`. Every table except `{{pred_table}}` and the two input tables is **appended on every run** and stamped with `session_id` (the Workflow session) — always filter on one run.

## Picking a run

| Need | Filter |
|---|---|
| Latest training run | `nba_ais_run_log ORDER BY time DESC LIMIT 1` |
| Its raw metrics | `nba_ais_train_metrics WHERE session_id = <that session>` |
| Latest scoring run | `{{pred_table}}` (no filter); `nba_ais_action_stats` / `{{pred_table}}_history` with `session_id = (SELECT max_by(session_id, time) FROM <table>)` |
| Latest tuning run | `nba_ais_tuning_results WHERE run_id = (SELECT max_by(run_id, time) FROM nba_ais_tuning_results)` |

`session_id` is VARCHAR. Never use `MAX(session_id)` to find the latest run — order by `time`. A run started with `nba_ais.dig` has the same `session_id` for training and scoring. Filter `is_best` in the tuning table with `LOWER(CAST(is_best AS VARCHAR)) = 'true'` (text or boolean).

## Scales — read before comparing values

| Columns | Scale |
|---|---|
| `logged_avg_reward`, `estimated_policy_value`, `ci_lower`, `ci_upper` | The reward's own unit — a 0/1 reward makes them rates (0–1); a revenue reward makes them currency per customer |
| `estimated_lift_pct`, `lift_vs_random_pct` | Percent (e.g. `12.5` = +12.5%) |
| `logged_share`, `recommended_share` | 0–1 |
| `overall_score` (tuning) | Objective of the phase — compare only within one phase |

---

## What the outputs mean

| Term | Meaning | Good / watch |
|---|---|---|
| **Action** | One of the options the business chooses between (`next_best_action` values) | Only actions in the training log can be recommended |
| **Reward** | The success measure after an action, as defined in `business-context.md` | — |
| **Logged average reward** | How successful the past decisions were on average (the baseline) | — |
| **Estimated policy value** | Off-policy estimate of the average reward if the model had chosen the action for every logged customer; mean of several estimators, in-sample | At or above the logged reward; above it with the whole interval = confident improvement |
| **Confidence interval** (`ci_lower`, `ci_upper`) | 95% range of the policy value | Interval spanning the logged reward = no evidence of improvement yet; very wide = too little data per action |
| **Estimated lift** | Policy value vs logged reward, in % | Read with the interval; large lifts with wide intervals are not reliable |
| **Tuning hold-out lift** (`lift_vs_random_pct`) | Best tuned policy vs a random policy on the latest 30% of the log (not seen in the search) | Positive = the policy beats random choices out of sample |
| **Action mix** | Share of each action in the past log vs in the recommendations | Shifts toward actions with better results for the customers who get them |
| **Exploration** (`epsilon`, LinUCB alpha) | How much the policy favors actions it knows little about | — |

Context effects are associations in the past decisions: if an action was only sent to one kind of customer, the model can't judge it for others. A randomized holdout after go-live is the real test.

---

## Training tables

### `nba_ais_run_log` — one row per training run

| Column | Type | Description |
|---|---|---|
| `session_id` | varchar | Workflow session |
| `train_run_id` | varchar | AI Signals run id of `nba_train` |
| `run_date` | varchar | Run date of the windows (`YYYY-MM-DD`) |
| `model_name` | varchar | Stored model |
| `model_type` | varchar | Policy from the config, or `tuned` (chosen type in `nba_ais_tuning_results`) |
| `enable_tuning` | varchar | `true` / `false` |
| `nba_type`, `time_grain` | varchar | Decision type (`channel`, `time`, `campaign`, `custom`) and the time-slot grain for `time` |
| `train_rows`, `train_users`, `n_actions` | bigint | Size of the training log |
| `logged_avg_reward` | double | Average reward of the logged decisions |
| `estimated_policy_value`, `ci_lower`, `ci_upper` | double | Policy value and its 95% interval |
| `estimated_lift_pct` | double | `100 × (estimated_policy_value / logged_avg_reward − 1)` |
| `reward_window_days`, `train_window_days`, `feature_lookback_days` | bigint | Windows of the run |
| `time` | bigint | Write time (UNIX) |

### `nba_ais_train_metrics` — raw metrics per training run

`session_id`, `train_run_id`, `model_name`, `metric` (`estimated_policy_value`, `confidence_interval_lower`, `confidence_interval_upper`, `neural_linucb_active`), `value`, `time`.

### `nba_ais_tuning_results` — one row per tuning trial (only when tuning is on)

| Column | Description |
|---|---|
| `run_id`, `session_id` | Tuning run |
| `phase` | `baseline_random`, `phase0_preprocessing`, `phase1_ope`, `phase2_policy` |
| `phase_trial`, `is_best`, `overall_score`, `execution_time`, `diverged` | Trial number, best of its phase (text or boolean), score, duration |
| `phase0_impute_type`, `phase0_scaler_type` | Preprocessing chosen in phase 0 |
| `phase1_estimator_type`, other `phase1_*` | Off-policy estimator settings |
| `phase2_model_type`, `phase2_lin_ucb_alpha`, `phase2_lin_eps_greedy_epsilon`, `phase2_base_classifier`, `phase2_policy_rf_*`, `phase2_ESS` | Policy settings, effective sample size |
| `estimated_policy_value`, `ci_lower`, `ci_upper`, `lift_vs_random_pct` | The `baseline_random` row (random policy on the 30% time hold-out, lift 0) and the best `phase2_policy` row (the chosen policy on the same hold-out, and its lift over random) |

Which `phase*_` columns exist depends on what was searched — check with `SHOW COLUMNS FROM nba_ais_tuning_results` first.

---

## Prediction tables

### `{{pred_table}}` — latest scoring run, one row per customer

| Column | Type | Description |
|---|---|---|
| `user_id` | follows the input | Customer ID (the workflow's `user_column`, always named `user_id`) |
| `next_best_action` | varchar | The recommended action |
| `model_name` | varchar | Model that scored |
| `scored_date` | varchar | Run date of the scoring |
| `session_id` | varchar | Scoring session |

Replaced on every scoring run. The Parent Segment attribute table. There is no score or ranking of the other actions — the model returns the chosen action only.

### `{{pred_table}}_history` — every scoring run

Same columns plus `time`, appended. Use for stability over time and for the live check against later outcomes.

### `nba_ais_action_stats` — per scoring run and action

`session_id`, `scored_date`, `action`, `logged_rows`, `logged_share`, `logged_avg_reward` (in the training log at scoring time), `recommended_users`, `recommended_share` (in that run's recommendations), `time`.

`logged_avg_reward` per action is a raw average over who received it — not the action's effect.

### `nba_ais_touchpoints` — sequential touches (rebuilt each run)

One row per touch or conversion for the last run's scan window: `<user_column>`, `touch_ts`, `touch_end_ts` (UNIX), `channel` (from the source, the UTM medium / source, or the external referrer; `direct` without signal), `campaign`, `action_label`, `src_name`, `event_type`, `events_in_touch` (consecutive same-channel events merged), `is_conversion`, `conversion_value`. `nba_ais_touchpoints_raw` is the union before sequencing, one row per source event, with `url`, `referrer`, `utm_medium`, `utm_source`, `utm_campaign`. Use them to explain channels and journeys; they are not a history.

### Model input tables

`train_input_table` / `pred_input_table` from the workflow config (defaults `nba_ais_train_input` / `nba_ais_pred_input`): the training log (one row per decision touch with its action, reward and context) and the scoring context (one row per customer), replaced each run. Use them to describe who received which action, or to compare the context of customers recommended different actions — join on the ID column (`user_column` in `{{engagement_dir}}/workflow/config.yml`) to `user_id`.

---

## Cross-table patterns

- **Is the model better than before?** `nba_ais_run_log` (latest): policy value vs logged reward with the interval; plus the tuning hold-out lift when tuning ran.
- **What changes for the customers?** `nba_ais_action_stats` (latest session): logged vs recommended share per action.
- **Why does customer X get action A?** `{{pred_table}}` ⨝ `pred_input_table` on the ID; compare the customer's context with the average context of customers recommended each action. Per-customer explanations are not written by the model — say it is an approximation.
- **Stability:** `{{pred_table}}_history` grouped by `session_id`: customers, actions used, top action share; customers whose action changed between the last two runs.
- **Run-over-run:** `nba_ais_run_log` ordered by `time`; check whether windows, `model_type` or `enable_tuning` changed before attributing a change to the data.
