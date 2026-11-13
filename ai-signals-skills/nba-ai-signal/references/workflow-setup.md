# NBA AI Signal — Workflow Setup

Use with `../../shared/push_pattern_td_workflows.md`. Source of truth in the working copy (`<workdir>` = `agent_outputs/<project_slug>/workflow`):

| File | Defines |
|---|---|
| `<workdir>/README.md` | Structure, what each parameter does, outputs, customization points |
| `<workdir>/config.yml` | Exact keys and syntax — edit in place, keep every key |
| `<workdir>/sql/README.md` | Input SQL output contract and variables |

This file adds only: Phase 1 findings → SQL and config values, deploy details, output checks, troubleshooting.

**NBA AI Signal exception:** `sql/touchpoints_union.sql` is project code — an example structure rewritten for every project — and `sql/input_features.sql` is adapted (`../../shared/solution_standard.md` §5).

**Minimal push first (Phase 3):** SQL from the Phase 1 confirmation, "First push" values below, template values for the rest, tuning off, schedule and alert email commented. Record each assumption in `project_state.md` as "default — confirm in requirements"; resolve caveats in Phase 4.

---

## 1. Write the input SQL

Three files, two modes: training rows are decision touches, scoring rows are customers. Design and patterns: `dataprep-guide.md`.

| File | From Phase 1 | Config |
|---|---|---|
| `touchpoints_union.sql` (rewrite) | One block per confirmed source: `src_name`, ID, time column, URL / referrer / UTM or traffic-source columns, `channel_hint`, campaign, custom label, conversions | `user_column`, `session_gap_minutes` |
| `touchpoints.sql` (extend rules only) | Customer-specific UTM mediums / sources from discovery query 3 | — |
| `input_features.sql` (adapt context) | Top channels for the per-channel columns; extra source-specific features | `nba_type`, `time_grain`, `local_timezone`, `action_sources`, `min_action_share`, `reward_*`, windows, `exclude_columns` |

Rules:
- **Union:** every block returns the 14 contract columns in order (`sql/README.md` §1), one customer ID everywhere, `TD_TIME_RANGE(<time>, '${scan_start}', '${scan_end}')` on every scan, NULL IDs dropped. Web: UTM from the URL with the referrer URL as fallback, or the traffic-source columns; `channel_hint` NULL. Non-web: `channel_hint` set. Conversions: `is_conversion = 1`.
- **Decision touches:** `action_sources` names the `src_name` values that are decisions — `''` for `channel`; give business sends their own `src_name` (`email_send`) for `time` / `campaign`.
- **Context, first push:** keep the shipped features; set the per-channel columns to the 3–6 largest channels from query 3; 5–20 numeric features in total.
- **No leakage:** features end at the anchor; nothing describing the outcome or the action (`dataprep-guide.md` §2 checklist).
- **Event time:** UNIX seconds — `time` if it is the real event time, else `TD_TIME_PARSE(<col>)`.
- **Join keys** differ per source → join through the lookup table from Phase 1 inside that source's block.
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

**2. UTM / traffic-source coverage** — per web table, over the last 90 days:

```sql
SELECT COUNT(*) AS pageviews,
       ROUND(AVG(IF(url_extract_parameter(<url_col>, 'utm_medium') IS NOT NULL, 1.0, 0.0)), 3)      AS utm_in_url,
       ROUND(AVG(IF(url_extract_parameter(<referrer_col>, 'utm_medium') IS NOT NULL, 1.0, 0.0)), 3) AS utm_in_referrer,
       ROUND(AVG(IF(<referrer_col> IS NOT NULL AND <referrer_col> <> '', 1.0, 0.0)), 3)              AS has_referrer
FROM <source_database>.<pageview_table> WHERE TD_INTERVAL(<ts>, '-90d')
```

If a traffic-source / medium column exists, add its fill rate. Coverage near 0 in both → the referrer host is the only signal; tell the user most web visits will be `direct` / `referral` / `organic_search`.

**3. Traffic-source values** — the mediums and sources the channel rules must cover:

```sql
SELECT LOWER(COALESCE(url_extract_parameter(<url_col>, 'utm_medium'), url_extract_parameter(<referrer_col>, 'utm_medium'))) AS medium,
       LOWER(COALESCE(url_extract_parameter(<url_col>, 'utm_source'), url_extract_parameter(<referrer_col>, 'utm_source'))) AS source,
       COUNT(*) AS pageviews
FROM <source_database>.<pageview_table> WHERE TD_INTERVAL(<ts>, '-90d')
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 50
```

Map every frequent value the rules in `touchpoints.sql` don't cover (`dataprep-guide.md` §3 table) — e.g. `aff`, `cj` → `affiliate`, `mail` → `email`. After the first run, the channel mix of `nba_ais_touchpoints` (§4 check 1) is the final check.

**4. Action mix and reward per action** — before the first run, from the source that will hold the decision touches (for `channel`, the per-source counts of query 1 plus query 3 approximate the mix). For `time` / `campaign` / `custom`, over the planned training window (`<start>` … `<end>` = `<last_date>` − `reward_window_days` − `train_window_days` … − `reward_window_days`):

```sql
WITH a AS (SELECT <id_col> AS id, <action_expr> AS action, <time_col> AS ts FROM <source_database>.<decision_table>
           WHERE TD_TIME_RANGE(<time_col>, '<start>', '<end>')),
o AS (SELECT DISTINCT a.id, a.ts, a.action FROM a JOIN <source_database>.<orders_table> x
      ON x.<id_col> = a.id AND x.<order_time_col> >= a.ts AND x.<order_time_col> < a.ts + <reward_window_days> * 86400)
SELECT a.action, COUNT(*) AS n_rows, COUNT(DISTINCT a.id) AS users, COUNT(o.id) AS rewarded,
       ROUND(100.0 * COUNT(o.id) / COUNT(*), 2) AS reward_pct
FROM a LEFT JOIN o ON o.id = a.id AND o.ts = a.ts AND o.action = a.action
GROUP BY 1 ORDER BY 2 DESC
```

`<action_expr>`: the campaign column, the custom label, or for `time` the local daypart `HOUR(FROM_UNIXTIME(<time_col>, '<local_timezone>'))` bucketed as in `sql/README.md`.

| Result | Action |
|---|---|
| 2–100 actions, hundreds+ rows and some rewards each | Continue |
| > 100 actions, or many with < ~200 rows | Group (campaign themes, coarser `time_grain`, higher `min_action_share`) |
| One action holds > ~90% of rows | The model will mostly learn about that one — tell the user; ask in requirements about rotations or tests |
| No rewards for an action, or reward rate 0 / 100% overall | Check the conversion source and window before continuing |

**5. Assignment check** — did each action reach a mix of customers? Compare a simple context per action (decision table ⨝ profile):

```sql
SELECT <action_expr> AS action, COUNT(*) AS n_rows,
       ROUND(AVG(CAST(p.<numeric_attr> AS DOUBLE)), 2) AS avg_attr, COUNT(DISTINCT p.<segment_col>) AS segments_reached
FROM <source_database>.<decision_table> a JOIN <source_database>.<profile_table> p ON p.<id_col> = a.<id_col>
WHERE TD_TIME_RANGE(a.<time_col>, '<start>', '<end>') GROUP BY 1 ORDER BY 2 DESC
```

Actions given to a single segment only → note it as a caveat: the model can't compare them for other customers.

**6. ID overlap** — one block per source; a low `matched` share = join-key mismatch:

```sql
SELECT '<table>' AS src, COUNT(DISTINCT p.id) AS customers, COUNT(DISTINCT s.<id_col>) AS matched
FROM (SELECT DISTINCT <id_col> AS id FROM <source_database>.<main_source_table>) p
LEFT JOIN <source_database>.<table> s ON s.<id_col> = p.id
```

## 2. Choose the other values

| Key | First push | Change when |
|---|---|---|
| `nba_type` | The decision from Phase 1 | — |
| `time_grain`, `local_timezone` | `daypart`, the customers' main zone | Phase 4 answers; `hour` only with tens of thousands of decisions |
| `action_sources` | `''` for `channel`; the send / decision `src_name` otherwise | Requirements name other decision sources |
| `min_action_share` | `0.01` | Long tail of campaigns or mediums → `0.02`–`0.05` |
| `reward_attribution`, `reward_type` | `next_touch`, `binary` | Sparse sends → `window`; revenue goal → `value` |
| `session_gap_minutes` | `30` | `events_per_touch` ≈ 1 for web → `60` |
| `reward_window_days` | Per decision (`dataprep-guide.md` §1) | The business outcome window differs |
| `train_window_days` | `180` | Actions change often → `60`–`90`; history check fails → shorter |
| `feature_lookback_days` | `90` | Slow buying cycle → `180`–`365` |
| `reference_date` | `''` | Data ends before today → last event date (query 1) |
| `model_type`, `epsilon` | `lin_ucb`, `0.1` | Phase 4 answers or tuning results (`ai-signals-guide.md` §5) |
| `impute_type`, `scaler_type` | `median`, `standard` | Heavy outliers → `robust` |
| `enable_tuning` | `false` | Input stable and `nba_tune` enabled → `true`; sample ratio per the README |
| `model_name` | `<project_prefix>_nba` | Never shared — same name overwrites the other model |
| `pred_output_table` | `nba_ais_actions` | Use-case name (`channel_nba`) |
| Failure email | Commented | Requirements give an address → uncomment `_error` in `nba_ais.dig`, project name in `subject` |

## 3. Deploy details

| Item | Value |
|---|---|
| Project / entry point | `nba_ais` (`tdx.json`) / `nba_ais`; `train`, `predict` run alone |
| Secrets | None — `${secret:td.apikey}` is provided by AI Signals; never ask for it; keep the header `"TD1 ${secret:td.apikey}"` as is |
| API endpoint | `ml_batch_api_endpoint` for the region (`tdx status`; values in the template README) |
| Sink database | Created by `+create_sink_database`; owner can't create databases → user creates it in the Console. `tdx tables "<sink_database>.nba_ais_*"` must be empty |
| Schedule | Commented; ask; different cadences → `train.dig` / `predict.dig` (`dataprep-guide.md` §6) |
| Push / run | `tdx wf push -y` from `<workdir>`, then `tdx wf run <project>.nba_ais` after the one approval; training takes several minutes, tuning adds more |
| Concurrency | One attempt at a time per `model_name` |

## 4. Validate

After every run: direct `tdx query -d <db>` calls in one shell command (no scripts). `<db>` = `sink_database`, `<pred>` = `pred_output_table`; latest run by `time`. Record results in `project_state.md`. Column details: `output-tables-guide.md`.

| # | Check | Pass |
|---|---|---|
| 0 | Touchpoints | Every union source present; web `direct` share plausible (not most of web); channel values all expected; web `events_per_touch` > 1. Off → `dataprep-guide.md` §5 |
| 1 | Training log per action | The expected actions (discovery query 4); hundreds+ rows and some rewards each. Off → `dataprep-guide.md` §5 |
| 2 | Policy value | `estimated_policy_value` ≥ `logged_avg_reward`; `ci_lower` above it = confident improvement; interval spanning it = no evidence yet (more data, better context); far above (> ~3× with a wide interval) = few rows per action or extreme weights |
| 3 | Tuning (if on) | Best phase-2 trial with `lift_vs_random_pct` > 0; chosen settings plausible |
| 4 | Recommendations | `users` = `pred_input_table` rows; every `next_best_action` is a logged action; more than one action recommended (or a clear reason) |
| 5 | Action mix | `nba_ais_action_stats`: recommended shares differ from logged shares in a way the rewards per action explain |
| 6 | Live check (once `reward_window_days` passed after a scoring run) | Customers who received the recommended action have a higher reward rate than those who received another one |

```sql
-- 0
SELECT src_name, channel, COUNT(*) AS touches, ROUND(AVG(events_in_touch), 1) AS events_per_touch
FROM <db>.<touchpoints_table> WHERE is_conversion = 0 GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 40

-- 1
SELECT <action_column> AS action, COUNT(*) AS n_rows, ROUND(AVG(<reward_column>), 4) AS avg_reward
FROM <db>.<train_input_table> GROUP BY 1 ORDER BY 2 DESC

-- 2
SELECT session_id, run_date, nba_type, time_grain, model_type, train_rows, n_actions, logged_avg_reward,
       estimated_policy_value, ci_lower, ci_upper, estimated_lift_pct
FROM <db>.nba_ais_run_log ORDER BY time DESC LIMIT 1

-- 3
SELECT phase, phase_trial, overall_score, estimated_policy_value, ci_lower, ci_upper, lift_vs_random_pct
FROM <db>.nba_ais_tuning_results
WHERE run_id = (SELECT max_by(run_id, time) FROM <db>.nba_ais_tuning_results) AND LOWER(CAST(is_best AS VARCHAR)) = 'true'

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
| `data_prep` fails | `<...>` placeholder or unknown column left; union blocks with different column counts or types; undefined `${…}` (also in SQL comments) | `tdx wf attempt <id> tasks`, `logs +<task>`; fix the SQL — `+create_touchpoints_raw` failing points at the union |
| `FROM_UNIXTIME` time-zone error | `local_timezone` not an IANA name | e.g. `America/New_York`, `Asia/Tokyo`, `UTC` |
| `+assert_training_dataset` fails | Empty window, one action, constant reward, NULL keys | Check `reference_date`, windows, the action filter and the reward rule |
| `+assert_prediction_dataset` fails | Repeated customers in the scoring population | `DISTINCT` / one row per customer in the pred branch |
| 401 / 403 on a run | Wrong regional endpoint, or the solution is not enabled | Fix `ml_batch_api_endpoint`; ask the account admin (`nba_train`, `nba_predict`, `nba_tune`) |
| Status poll fails with 400 | The run failed — the error is in the poll task log | Fix the cause (`ai-signals-guide.md` §7), re-run the whole workflow |
| Run takes very long | Large table or big tuning budget | `http>` keeps polling (up to the task time limit); lower the tuning budgets or `train_window_days` |
| `+latest_actions` fails on `element_at` | The prediction table is empty (no rows imported) | Check the prediction input and the poll log |
| Re-running a failed attempt | Same session | Safe: the log steps first delete that session's rows in `nba_ais_run_log`, `nba_ais_train_metrics`, `<pred>_history` and `nba_ais_action_stats`, then append. Cancel any ML run still in progress first |
| Leftover `mltmp_nba_ais_*` tables | An attempt failed before the drop step | Drop them once no run is active |
| Policy value jumps between runs | Different windows, actions, features or tuning | Diff config and SQL of both runs first |

Input-table symptoms (actions, duplicates, reward rate): `dataprep-guide.md` §5. Model symptoms (columns, actions, tuning): `ai-signals-guide.md` §7.
