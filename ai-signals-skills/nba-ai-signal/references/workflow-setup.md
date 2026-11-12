# NBA AI Signal — Workflow Setup

Use with `../../shared/push_pattern_td_workflows.md`. Source of truth in the working copy (`<workdir>` = `agent_outputs/<project_slug>/workflow`):

| File | Defines |
|---|---|
| `<workdir>/README.md` | Structure, what each parameter does, outputs, customization points |
| `<workdir>/config.yml` | Exact keys and syntax — edit in place, keep every key |
| `<workdir>/sql/README.md` | Input SQL output contract and variables |

This file adds only: Phase 1 findings → SQL and config values, deploy details, output checks, troubleshooting.

**NBA AI Signal exception:** `sql/input_features.sql` is project code — an example structure rewritten for every project (`../../shared/solution_standard.md` §5).

**Minimal push first (Phase 3):** SQL from the Phase 1 confirmation, "First push" values below, template values for the rest, tuning off, schedule and alert email commented. Record each assumption in `project_state.md` as "default — confirm in requirements"; resolve caveats in Phase 4.

---

## 1. Write the input SQL

One file, two modes: training rows are logged actions, scoring rows are customers. Design and patterns: `dataprep-guide.md`.

| Part | From Phase 1 | Config |
|---|---|---|
| Actions | Action log table, action column (grouped to 2–100 labels), action time | `action_column`, `train_window_days` |
| Reward | Outcome table + rule, or the reward column on the log | `reward_column`, `reward_window_days` |
| Context | Activity, order, engagement tables + stable profile attributes | `feature_lookback_days`, `exclude_columns` |
| Scoring population | Profile table (or Parent Segment `customers`) + eligibility | `user_column` |

Rules:
- **Shape:** `bounds` → `anchors` (train branch: the log; pred branch: the population) → `anchors_n` → one CTE per context source → `reward` → final SELECT (`session_id`, user, action, reward, timestamp, features). Join every CTE on the user **and** `anchor_id`.
- **First push:** 5–12 numeric features — window counts, active days, recency, monetary sums, prior actions, 1–2 stable attributes as numbers.
- **No leakage:** features end at the anchor; no column describing the outcome or the action (`dataprep-guide.md` §2 checklist).
- **Event time:** UNIX seconds — `time` if it is the real event time, else `TD_TIME_PARSE(<col>)`. Keep `TD_TIME_RANGE(…, '${scan_start}', '${scan_end}')` on every scan.
- **Join keys** differ per source → join through the lookup table from Phase 1.
- **`exclude_columns`:** `time|session_id` + every other non-feature column the SQL outputs.

### Discovery queries

Run yourself (no subagents), all in one shell command (`tdx query … & tdx query … & wait`). Never start SQL with a `--` comment (`tdx query` reads it as an option).

**1. Source profile** — one `UNION ALL` block per table:

```sql
SELECT '<table>' AS src, COUNT(*) AS n_rows, COUNT(DISTINCT <id_col>) AS ids, COUNT_IF(<id_col> IS NULL) AS null_ids,
       TD_TIME_FORMAT(MIN(<ts>), 'yyyy-MM-dd') AS first_event, TD_TIME_FORMAT(MAX(<ts>), 'yyyy-MM-dd') AS last_event
FROM <source_database>.<table>
UNION ALL SELECT '<next table>', … FROM …
```

**2. Action mix and reward per action** over the planned training window (`<start>` … `<end>` = `<last_date>` − `reward_window_days` − `train_window_days` … − `reward_window_days`):

```sql
WITH a AS (SELECT <id_col> AS id, <action_col> AS action, <action_time_col> AS ts FROM <source_database>.<action_log_table>
           WHERE TD_TIME_RANGE(<action_time_col>, '<start>', '<end>')),
o AS (SELECT DISTINCT a.id, a.ts, a.action FROM a JOIN <source_database>.<outcome_table> x
      ON x.<id_col> = a.id AND x.<outcome_time_col> >= a.ts AND x.<outcome_time_col> < a.ts + <reward_window_days> * 86400)
SELECT a.action, COUNT(*) AS n_rows, COUNT(DISTINCT a.id) AS users, COUNT(o.id) AS rewarded,
       ROUND(100.0 * COUNT(o.id) / COUNT(*), 2) AS reward_pct
FROM a LEFT JOIN o ON o.id = a.id AND o.ts = a.ts AND o.action = a.action
GROUP BY 1 ORDER BY 2 DESC
```

| Result | Action |
|---|---|
| 2–100 actions, hundreds+ rows and some rewards each | Continue |
| > 100 actions, or many with < ~200 rows | Group to families; drop retired actions |
| One action holds > ~90% of rows | The model will mostly learn about that one — tell the user; ask in requirements about rotations or tests |
| No rewards for an action, or reward rate 0 / 100% overall | Check the outcome rule and window before continuing |

**3. Assignment check** — did each action reach a mix of customers? Compare a simple context per action:

```sql
SELECT a.<action_col> AS action, COUNT(*) AS n_rows,
       ROUND(AVG(CAST(p.<numeric_attr> AS DOUBLE)), 2) AS avg_attr, COUNT(DISTINCT p.<segment_col>) AS segments_reached
FROM <source_database>.<action_log_table> a JOIN <source_database>.<profile_table> p ON p.<id_col> = a.<id_col>
WHERE TD_TIME_RANGE(a.<action_time_col>, '<start>', '<end>') GROUP BY 1 ORDER BY 2 DESC
```

Actions sent to a single segment only → note it as a caveat: the model can't compare them for other customers.

**4. ID overlap** — one block per context source; a low `matched` share = join-key mismatch:

```sql
SELECT '<table>' AS src, COUNT(DISTINCT a.id) AS log_ids, COUNT(DISTINCT s.<id_col>) AS matched
FROM (SELECT DISTINCT <id_col> AS id FROM <source_database>.<action_log_table>) a
LEFT JOIN <source_database>.<table> s ON s.<id_col> = a.id
```

## 2. Choose the other values

| Key | First push | Change when |
|---|---|---|
| `reward_window_days` | Per use case (`dataprep-guide.md` §1) | The business outcome window differs |
| `train_window_days` | `180` | Actions change often → `60`–`90`; history check fails → shorter |
| `feature_lookback_days` | `90` | Slow buying cycle → `180`–`365` |
| `reference_date` | `''` | Data ends before today → last action date (query 1) |
| `model_type`, `epsilon` | `lin_ucb`, `0.1` | Phase 4 answers or tuning results (`ai-signals-guide.md` §5) |
| `impute_type`, `scaler_type` | `median`, `standard` | Heavy outliers → `robust` |
| `enable_tuning` | `false` | Input stable and `nba_tune` enabled → `true`; sample ratio per the README |
| `model_name` | `<project_prefix>_nba` | Never shared — same name overwrites the other model |
| `pred_output_table` | `nba_ais_actions` | Use-case name (`offer_nba`) |
| Failure email | Commented | Requirements give an address → uncomment `_error` in `nba_ais.dig`, project name in `subject` |

## 3. Deploy details

| Item | Value |
|---|---|
| Project / entry point | `nba_ais` (`tdx.json`) / `nba_ais`; `train`, `predict` run alone |
| Secrets | None — `${secret:td.apikey}` is provided by AI Signals; never ask for it; keep the header as is |
| API endpoint | `ml_batch_api_endpoint` for the region (`tdx status`; values in the template README) |
| Sink database | Created by `+create_sink_database`; owner can't create databases → user creates it in the Console. `tdx tables "<sink_database>.nba_ais_*"` must be empty |
| Schedule | Commented; ask; different cadences → `train.dig` / `predict.dig` (`dataprep-guide.md` §6) |
| Push / run | `tdx wf push -y` from `<workdir>`, then `tdx wf run <project>.nba_ais` after the one approval; training takes several minutes, tuning adds more |
| Concurrency | One attempt at a time per `model_name` |

## 4. Validate

After every run: direct `tdx query -d <db>` calls in one shell command (no scripts). `<db>` = `sink_database`, `<pred>` = `pred_output_table`; latest run by `time`. Record results in `project_state.md`. Column details: `output-tables-guide.md`.

| # | Check | Pass |
|---|---|---|
| 1 | Training log per action | Same actions as discovery query 2; hundreds+ rows and some rewards each. Off → `dataprep-guide.md` §5 |
| 2 | Policy value | `estimated_policy_value` ≥ `logged_avg_reward`; `ci_lower` above it = confident improvement; interval spanning it = no evidence yet (more data, better context); far above (> ~3× with a wide interval) = few rows per action or extreme weights |
| 3 | Tuning (if on) | Best phase-2 trial with `lift_vs_random_pct` > 0; chosen settings plausible |
| 4 | Recommendations | `users` = `pred_input_table` rows; every `next_best_action` is a logged action; more than one action recommended (or a clear reason) |
| 5 | Action mix | `nba_ais_action_stats`: recommended shares differ from logged shares in a way the rewards per action explain |
| 6 | Live check (once `reward_window_days` passed after a scoring run) | Customers who received the recommended action have a higher reward rate than those who received another one |

```sql
-- 1
SELECT <action_column> AS action, COUNT(*) AS n_rows, ROUND(AVG(<reward_column>), 4) AS avg_reward
FROM <db>.<train_input_table> GROUP BY 1 ORDER BY 2 DESC

-- 2
SELECT session_id, run_date, model_type, train_rows, n_actions, logged_avg_reward,
       estimated_policy_value, ci_lower, ci_upper, estimated_lift_pct
FROM <db>.nba_ais_run_log ORDER BY time DESC LIMIT 1

-- 3
SELECT phase, phase_trial, overall_score, estimated_policy_value, ci_lower, ci_upper, lift_vs_random_pct
FROM <db>.nba_ais_tuning_results
WHERE run_id = (SELECT max_by(run_id, time) FROM <db>.nba_ais_tuning_results) AND is_best = 'true'

-- 4
SELECT next_best_action, COUNT(*) AS users FROM <db>.<pred> GROUP BY 1 ORDER BY 2 DESC

-- 5
SELECT action, logged_rows, ROUND(logged_share, 4) AS logged_share, ROUND(logged_avg_reward, 4) AS logged_avg_reward,
       recommended_users, ROUND(recommended_share, 4) AS recommended_share
FROM <db>.nba_ais_action_stats WHERE session_id = (SELECT max_by(session_id, time) FROM <db>.nba_ais_action_stats)
ORDER BY recommended_users DESC

-- 6: actions sent after an earlier scoring run (<scored_date>, <session>) vs its recommendation
WITH rec AS (SELECT user_id, next_best_action FROM <db>.<pred>_history WHERE session_id = '<session>'),
sent AS (SELECT <id_col> AS user_id, CAST(<action_col> AS VARCHAR) AS action, <action_time_col> AS ts
         FROM <source_database>.<action_log_table>
         WHERE TD_TIME_RANGE(<action_time_col>, '<scored_date>', TD_TIME_ADD('<scored_date>', '<reward_window_days>d'))),
res AS (SELECT DISTINCT s.user_id, s.ts FROM sent s JOIN <source_database>.<outcome_table> o
        ON o.<id_col> = s.user_id AND o.<outcome_time_col> >= s.ts AND o.<outcome_time_col> < s.ts + <reward_window_days> * 86400)
SELECT IF(s.action = r.next_best_action, 'followed', 'other action') AS grp, COUNT(*) AS actions_sent,
       ROUND(AVG(IF(x.user_id IS NULL, 0.0, 1.0)), 4) AS reward_rate
FROM sent s JOIN rec r ON r.user_id = s.user_id LEFT JOIN res x ON x.user_id = s.user_id AND x.ts = s.ts
GROUP BY 1
```

Check 6 is only fair when the "other action" group was not chosen for a reason (a randomized split or rotation); otherwise report it as indicative.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `data_prep` fails | `<...>` placeholder or unknown column left; undefined `${…}` (also in SQL comments) | `tdx wf attempt <id> tasks`, `logs +<task>`; fix the SQL |
| `+assert_training_dataset` fails | Empty window, one action, constant reward, NULL keys | Check `reference_date`, windows, the action filter and the reward rule |
| `+assert_prediction_dataset` fails | Repeated customers in the scoring population | `DISTINCT` / one row per customer in the pred branch |
| 401 / 403 on a run | Wrong regional endpoint, or the solution is not enabled | Fix `ml_batch_api_endpoint`; ask the account admin (`nba_train`, `nba_predict`, `nba_tune`) |
| Status poll fails with 400 | The run failed — the error is in the poll task log | Fix the cause (`ai-signals-guide.md` §7), re-run the whole workflow |
| Status poll gives up | Long tuning or training | Raise `_retry` on the wait task; lower tuning budgets |
| `+latest_actions` fails on `element_at` | The prediction table is empty (no rows imported) | Check the prediction input and the poll log |
| Leftover `mltmp_nba_ais_*` tables | An attempt failed before the drop step | Drop them once no run is active |
| Policy value jumps between runs | Different windows, actions, features or tuning | Diff config and SQL of both runs first |

Input-table symptoms (actions, duplicates, reward rate): `dataprep-guide.md` §5. Model symptoms (columns, actions, tuning): `ai-signals-guide.md` §7.
