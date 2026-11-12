# NBA AI Signal (Next Best Action) — Workflow Template

## Overview

This Treasure Workflow project learns which action — an offer, message, campaign, content or channel — works best for each customer from a log of past actions and their outcomes, then recommends one action per customer, with the AI Signals Next Best Action model (ml-batch-api `nba_tune` / `nba_train` / `nba_predict`, contextual bandits). No Python runs in the workflow: tuning, training, off-policy evaluation and scoring all happen in the AI Signals service.

- **Data prep** — the project's input SQL (`sql/`) builds two tables with the same numeric context features: a **training log** with one row per past action (customer, action, reward, action time, the customer's context just before it) and a **prediction table** with one row per customer (context at the run date).
- **Tune (optional)** — `enable_tuning: true` runs the three-phase cross-validated off-policy search (preprocessing → estimator → policy) and appends the trials to `nba_ais_tuning_results`; training then uses the best values.
- **Train** — a contextual-bandit policy (`lin_ucb` by default; `lin_ts`, `lin_eps_greedy`, `ipw_learner`) replays the log, is evaluated off-policy (estimated reward per customer if it had chosen the actions, with a 95% interval) and is stored by the service under `model_name`.
- **Predict** — the stored policy picks the best action for every customer; `pred_output_table` holds the latest action per customer (the Parent Segment attribute table) and `<pred_output_table>_history` every scoring run.

Any use case with a choice among 2–100 actions and an outcome per action fits: offer or discount selection, campaign or content choice, channel choice, retention treatment. The log must contain several actions given to comparable customers — the model learns only from the variation in what was done before.

TD project name: `nba_ais` (from `tdx.json`). Entry point: `nba_ais.dig`. All parameters live in `config.yml`.

## Workflow Structure

```
nba_ais.dig                        # entry point: schedule, error email, train then predict
├── train.dig                      # mode = train
│   ├── data_prep.dig              # 0. +create_sink_database; sql/input_features.sql → train_input_table
│   ├── +check_training_dataset    # 1. rows, 2–100 actions, varying reward, no NULL keys — else fail
│   ├── +train                     # 2. enable_tuning: nba_tune → poll → nba_train with the tuning run id
│   │                              #    otherwise: nba_train with the ML MODEL settings
│   ├── +wait_for_training         #    polls /v1/runs/{id}/status (408 running, 400 failed, 200 done)
│   ├── +clear_*                   # 3. a re-run of the same session first removes its log rows
│   ├── +log_train_metrics         # 4. off-policy metrics → nba_ais_train_metrics
│   ├── +log_run                   # 5. config, logged reward, policy value → nba_ais_run_log
│   └── +drop_working_table
└── predict.dig                    # mode = pred
    ├── data_prep.dig              # 0. sql/input_features.sql → pred_input_table (one row per customer)
    ├── +check_prediction_dataset  # 1. non-empty, no repeated or NULL IDs — else fail
    ├── +predict_nba               # 2. POST /v1/runs, solution nba_predict, model under model_name
    ├── +wait_for_prediction
    ├── +latest_actions            # 4. next_best_action per user → pred_output_table
    ├── +clear_*                   #    a re-run of the same session first removes its history / stats rows
    ├── +append_history            #    → <pred_output_table>_history
    ├── +action_stats              # 5. logged vs recommended action mix → nba_ais_action_stats
    └── +drop_working_table
```

`train.dig` and `predict.dig` also run on their own — schedule them separately when retraining and scoring have different cadences (e.g. monthly retrain, daily recommendations).

| Folder / file | Contents |
|---|---|
| `config.yml` | All parameters; the DERIVED block at the end computes the run date and training window — do not edit it |
| `sql/` | The project's input SQL — `input_features.sql` ships as an example structure and is rewritten for every project (`sql/README.md` has the output contract) |
| `body.txt` | Failure email body (used when an `_error` block is enabled) |

## Configuration

All keys are in `config.yml`. The template values are a working example; change the ones in **bold** for every project.

### Output and model

| Parameter | What it does | How to choose it |
|---|---|---|
| **`sink_database`** | Database for the input tables, every `nba_ais_*` table and the recommendations | The confirmed sink database. Created by the first run if missing. The `nba_ais_*` names are fixed, so one sink database holds one NBA AI Signal project |
| `description` | Free-text note; not sent to the API | One line on the use case |
| **`ml_batch_api_endpoint`** | AI Signals ml-batch-api base URL | The account's region: US `https://ml-batch-api.treasuredata.com` (also listed as `https://ml-batch-api.us01.treasuredata.com`), Japan `https://ml-batch-api.treasuredata.co.jp`, EU `https://ml-batch-api.eu01.treasuredata.com`, AP `https://ml-batch-api.ap02.treasuredata.com` / `https://ml-batch-api.ap03.treasuredata.com` |
| `ml_batch_api_version` | AI Signals solution version | `stable` |
| **`model_name`** | Name the trained policy is stored under; predict loads it | Unique per TD account — every training run overwrites it. Project-specific (e.g. `loyalty_offer_nba`) |
| **`model_type`** | Bandit policy, used when `enable_tuning` is false | `lin_ucb` (default, explores where it is uncertain); `lin_ts` (Thompson sampling); `lin_eps_greedy` (simple, explores at rate `epsilon`); `ipw_learner` (classifier-based offline learner, best with logged propensities) |
| `epsilon` | Exploration: alpha for `lin_ucb`, exploration rate for `lin_eps_greedy` | `0.1`; higher explores more, lower exploits the best-known action |
| `impute_type` | Fills missing feature values | `median` (fast, any size); `knn` / `hybrid` fall back to median above 50K rows; `drop` removes rows with gaps |
| `scaler_type` | Feature scaling | `standard`; `robust` for heavy outliers (spend, counts) |
| `base_classifier` | Classifier inside `ipw_learner` | `random_forest`; `logistic_regression` for small data |

### Tables and columns

| Parameter | What it does | How to choose it |
|---|---|---|
| `train_input_table`, `pred_input_table` | Model input tables written by `data_prep.dig` | Keep the defaults unless the names clash |
| **`pred_output_table`** | Latest recommendation per user (replaced each run); also names `<pred_output_table>_history` | `nba_ais_actions`, or a use-case name (e.g. `offer_nba`) |
| `user_column` | Customer ID column of both input tables; the API always writes it back as `user_id` | The ID the Parent Segment joins on, as named by the input SQL |
| `action_column` | Action label column of the training log | The name the input SQL writes |
| `reward_column` | Numeric outcome column of the training log | The name the input SQL writes |
| `timestamp_column` | Action time (train) / run date (pred) in UNIX seconds | The name the input SQL writes — not `timestamp` or `time` |
| **`exclude_columns`** | Pipe-separated globs of non-feature columns; the user (and `user_id`), action, reward and timestamp columns are always excluded | `time|session_id` + every other column of the input that is not a numeric feature |

### Data prep (read by the input SQL)

Each logged action in the training window becomes one training row: its context from the `feature_lookback_days` before it, its reward from the `reward_window_days` after it. Only actions whose reward window ended by the run date are used. Scoring builds the context at the run date.

| Parameter | What it does | How to choose it |
|---|---|---|
| **`reward_window_days`** | How long after an action its outcome counts | The business definition ("redeemed within 14 days" → `14`); the typical time from action to outcome |
| **`train_window_days`** | How many days of logged actions to learn from | `180`; shorter (`60`–`90`) when actions or offers change often, longer when actions are rare |
| **`feature_lookback_days`** | Context history before each action / the run date | `90`; up to `365` for slow buying cycles |
| `reference_date` | Run date used for the windows; `''` = the session date | `''` for live data; a `YYYY-MM-DD` date near the end of the data for demo or stale data |
| `run_date`, `train_start`, `train_end` | DERIVED block: the run date and the training-action range, computed from `reference_date` and the windows; read by the SQL and the logs | Never edit |
| `timezone` | Informational only — the workflow time zone is the top-level `timezone:` of each `.dig` (UTC) | Keep `UTC` |

History needed before the run date: `reward_window_days + train_window_days + feature_lookback_days` (template values: 14 + 180 + 90 = 284 days).

### Tuning

| Parameter | What it does | How to choose it |
|---|---|---|
| **`enable_tuning`** | `true` runs `nba_tune` before training and trains with the best settings (the ML MODEL values are then ignored). If training can't read the tuning rows, it silently falls back to the API defaults (`lin_ucb`, `knn`, `standard`), not the ML MODEL values — check the train log for "Could not load tuning results" | `false` for the first push; `true` once the input is stable and the account has `nba_tune` |
| `hyperparam_tune_sample_ratio` | Share of the tuning split (70% of rows, by time) that is searched | Aim at ≥ ~50K sampled rows and ≥ ~100 per action per fold: `0.1` for ~1M rows, `0.5`–`1.0` below ~200K |
| `ocv_phase0_k` | Folds for the impute × scaler grid | `5`; `3` for small data |
| `ocv_phase1_trials` | Optuna trials for the off-policy estimator | `20`; `10` for a quick run |
| `ocv_phase2_trials` | Optuna trials for the policy | `50`; `20` for a quick run |

## Outputs

All tables are in `sink_database`.

- `nba_ais_train_input`, `nba_ais_pred_input` (`train_input_table`, `pred_input_table`) — model inputs, replaced each run
- `pred_output_table` — `user_id`, `next_best_action`, `model_name`, `scored_date`, `session_id`; one row per customer, replaced each scoring run (Parent Segment attribute table)
- `<pred_output_table>_history` — the same columns for every scoring run, appended
- `nba_ais_run_log` — one row per training run: config, training rows, actions, logged average reward, estimated policy value with its 95% interval, estimated lift
- `nba_ais_train_metrics` — the raw off-policy metrics per training run (`metric`, `value`), appended
- `nba_ais_action_stats` — per scoring run and action: logged rows, share and average reward in the training log; recommended customers and share
- `nba_ais_tuning_results` — one row per tuning trial (only with `enable_tuning`), appended by the service

The policy itself is stored by the AI Signals service under `model_name`, not in TD. Columns and queries: the skill's `references/output-tables-guide.md`.

## Secrets & Requirements

- **Secrets:** none — `${secret:td.apikey}` is provided by AI Signals and sent as `Authorization: TD1 <key>`, the only key format the ml-batch-api accepts.
- **Account:** AI Signals enabled for `nba_train` and `nba_predict` (and `nba_tune` when `enable_tuning` is true).
- **Data:** a log of past actions per customer with an observable outcome — 2–100 distinct actions, at least a few hundred rows (better thousands) per action, each action given to a mix of customers, and some rewards for every action.
- **Permissions:** create the sink database and tables; read the source databases used by the input SQL.
- **Failure email and schedule:** commented placeholders in `nba_ais.dig`, `train.dig` and `predict.dig`. Uncomment `nba_ais.dig` for one cadence, or `train.dig` and `predict.dig` for separate cadences — never both.
- **One attempt at a time** per `model_name`: two concurrent runs overwrite each other's model.

## Customization Points

| Change | Where |
|---|---|
| Actions, reward, context features, who is scored | `sql/input_features.sql` (contract in `sql/README.md`) |
| Windows | `config.yml` DATA PREP |
| Extra feature tables | `_parallel` block in `data_prep.dig`, joined in `sql/input_features.sql` |
| Logged propensities (randomized tests) | Add `propensity_column` (and `propensity_type: true_propensity`) to `+train_nba` in `train.dig`; output the column in the input SQL |
| Compare two policies | A second project with its own `model_name` and sink database (the `nba_ais_*` names are fixed) |
