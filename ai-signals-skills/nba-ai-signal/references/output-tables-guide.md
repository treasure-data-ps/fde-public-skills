# NBA AI Signal — Output Tables Guide

Every table the workflow writes to `sink_database`, its columns and the queries that read it. Table names starting with `nba_ais_` are fixed (one project per sink database); `<pred>` = `pred_output_table` (default `nba_ais_actions`). How the model produces them: `ai-signals-guide.md` §5–§6.

## Rules for every query

- **Latest training run:** `nba_ais_run_log ORDER BY time DESC LIMIT 1`; its `session_id` keys `nba_ais_train_metrics`.
- **Latest scoring run:** `<pred>` (always the latest, one row per user); `nba_ais_action_stats` and `<pred>_history` filtered on `session_id = (SELECT max_by(session_id, time) FROM <table>)`.
- **Latest tuning run:** `run_id = (SELECT max_by(run_id, time) FROM nba_ais_tuning_results)`; `is_best` is the string `'true'` / `'false'`.
- Never `MAX(session_id)` to find the latest — order by `time`. `session_id` is VARCHAR.
- A run started with `nba_ais.dig` has the same `session_id` for training and scoring; `train.dig` / `predict.dig` scheduled apart have different ones.
- `time` is UNIX seconds — show with `TD_TIME_FORMAT(time, 'yyyy-MM-dd HH:mm', 'UTC')`.

## Tables at a glance

| Table | Written by | Grain | Mode |
|---|---|---|---|
| `train_input_table` (`nba_ais_train_input`) | `data_prep.dig` (train) | One row per logged action | Replaced |
| `pred_input_table` (`nba_ais_pred_input`) | `data_prep.dig` (pred) | One row per customer | Replaced |
| `nba_ais_run_log` | `train.dig` `+log_run` | One row per training run | Appended |
| `nba_ais_train_metrics` | `train.dig` `+log_train_metrics` | (run, metric) | Appended |
| `nba_ais_tuning_results` | `nba_tune` (service) | (tuning run, trial) | Appended, only with `enable_tuning` |
| `<pred>` | `predict.dig` `+latest_actions` | One row per user | Replaced — Parent Segment table |
| `<pred>_history` | `predict.dig` `+append_history` | (scoring run, user) | Appended |
| `nba_ais_action_stats` | `predict.dig` `+action_stats` | (scoring run, action) | Appended |

## Training tables

### `nba_ais_run_log`

| Column | Meaning |
|---|---|
| `session_id`, `train_run_id` | Workflow session; ml-batch-api run id of `nba_train` |
| `run_date` | Run date used for the windows (`reference_date` or the session date) |
| `model_name`, `model_type` | Stored model; policy type from the config, or `tuned` when `enable_tuning` was on (chosen type in `nba_ais_tuning_results`) |
| `enable_tuning` | `'true'` / `'false'` |
| `train_rows`, `train_users`, `n_actions` | Size of the training log |
| `logged_avg_reward` | Average reward of the past decisions — the baseline |
| `estimated_policy_value`, `ci_lower`, `ci_upper` | Off-policy estimate of the average reward if the learned policy had chosen, with its 95% interval (in-sample) |
| `estimated_lift_pct` | `100 × (estimated_policy_value / logged_avg_reward − 1)` |
| `reward_window_days`, `train_window_days`, `feature_lookback_days` | Windows of the run |

### `nba_ais_train_metrics`

`session_id`, `train_run_id`, `model_name`, `metric`, `value` — the raw rows from `nba_train`: `estimated_policy_value`, `confidence_interval_lower`, `confidence_interval_upper` (+ `neural_linucb_active` for `neural_lin_ucb`).

### `nba_ais_tuning_results`

| Column | Meaning |
|---|---|
| `run_id`, `session_id` | Tuning run (its id is passed to training as `tuning_run_id`) |
| `phase` | `baseline_random`, `phase0_preprocessing`, `phase1_ope`, `phase2_policy` |
| `phase_trial`, `is_best`, `overall_score`, `execution_time`, `diverged` | Trial number, best trial of its phase, its score |
| `phase0_impute_type`, `phase0_scaler_type`, `phase0_std_score` | Preprocessing grid |
| `phase1_estimator_type`, `phase1_*` | Off-policy estimator and its settings |
| `phase2_model_type`, `phase2_base_classifier`, `phase2_lin_ucb_alpha`, `phase2_lin_eps_greedy_epsilon`, `phase2_policy_rf_*`, `phase2_ESS` | Policy settings and effective sample size |
| `estimated_policy_value`, `ci_lower`, `ci_upper`, `lift_vs_random_pct` | Best phase-2 row only: value of the chosen policy on the 30% time hold-out, and its lift over a random policy |

Which `phase*_` columns exist depends on the search space — check with `SHOW COLUMNS FROM nba_ais_tuning_results` before selecting one.

```sql
-- chosen settings of the latest tuning run
SELECT phase, phase0_impute_type, phase0_scaler_type, phase1_estimator_type, phase2_model_type,
       overall_score, estimated_policy_value, ci_lower, ci_upper, lift_vs_random_pct
FROM nba_ais_tuning_results
WHERE run_id = (SELECT max_by(run_id, time) FROM nba_ais_tuning_results) AND is_best = 'true'
ORDER BY phase
```

## Prediction tables

### `<pred>` and `<pred>_history`

| Column | Meaning |
|---|---|
| `user_id` | Customer ID (the input's `user_column`, always named `user_id`) |
| `next_best_action` | The action the policy chose — one of the logged action labels |
| `model_name` | Model that scored |
| `scored_date` | Run date of the scoring |
| `session_id` | Scoring session |

No score or ranking of the other actions exists — the API returns the chosen action only.

### `nba_ais_action_stats`

| Column | Meaning |
|---|---|
| `session_id`, `scored_date` | Scoring run |
| `action` | Action label |
| `logged_rows`, `logged_share`, `logged_avg_reward` | In the training log at scoring time: how often the action was taken, its share, its average reward |
| `recommended_users`, `recommended_share` | In this run's recommendations |

```sql
-- logged vs recommended mix of the latest scoring run
SELECT action, logged_share, logged_avg_reward, recommended_share
FROM nba_ais_action_stats
WHERE session_id = (SELECT max_by(session_id, time) FROM nba_ais_action_stats)
ORDER BY recommended_share DESC
```

`logged_avg_reward` per action is a raw average over who received the action — it is not the action's effect; the policy's choice also depends on each customer's context.

### Stability across scoring runs

```sql
WITH c AS (SELECT session_id, next_best_action, MIN(scored_date) AS scored_date, MIN(time) AS t, COUNT(*) AS cnt
           FROM <pred>_history GROUP BY 1, 2)
SELECT session_id, MIN(scored_date) AS scored_date, SUM(cnt) AS users, COUNT(*) AS actions_used,
       max_by(next_best_action, cnt) AS top_action, MAX(cnt) * 1.0 / SUM(cnt) AS top_action_share
FROM c GROUP BY session_id ORDER BY MIN(t)
```

Customers whose action changed between the last two runs:

```sql
WITH s AS (SELECT session_id, ROW_NUMBER() OVER (ORDER BY MIN(time) DESC) AS rn FROM <pred>_history GROUP BY 1)
SELECT COUNT(*) AS users_both, COUNT_IF(a.next_best_action <> b.next_best_action) AS changed
FROM <pred>_history a JOIN <pred>_history b ON b.user_id = a.user_id
WHERE a.session_id = (SELECT session_id FROM s WHERE rn = 1) AND b.session_id = (SELECT session_id FROM s WHERE rn = 2)
```

## Question → tables

| Question | Tables |
|---|---|
| Is the policy better than what we did before? | `nba_ais_run_log` (`estimated_policy_value` vs `logged_avg_reward`, interval) ; tuning hold-out lift |
| Which settings did tuning pick? | `nba_ais_tuning_results` (`is_best = 'true'`) |
| How many customers get each action? | `<pred>`; `nba_ais_action_stats` |
| How does the mix differ from the past? | `nba_ais_action_stats` |
| Why does customer X get action A? | `<pred>` ⨝ `pred_input_table` (context) vs. the averages of customers getting A |
| Are recommendations stable over time? | `<pred>_history` |
| Did following the recommendation pay off? | `<pred>_history` ⨝ the action log and outcomes (`workflow-setup.md` §4 check 6) |
