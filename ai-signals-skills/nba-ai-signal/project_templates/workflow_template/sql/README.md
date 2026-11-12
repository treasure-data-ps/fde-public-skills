# Input SQL

`data_prep.dig` runs `input_features.sql` (and any feature queries added before it) in both modes and writes the result to `train_input_table` (`mode = train`) or `pred_input_table` (`mode = pred`). The template file is an **example structure** — it is rewritten for every project from the Phase 1 data discovery; the workflow cannot run until every `<...>` placeholder is replaced. Patterns per action and reward type: the skill's `references/dataprep-guide.md`.

## Output contract

| Column | Train (`mode = train`) | Pred (`mode = pred`) |
|---|---|---|
| `session_id` | `'${session_id}'` (in `exclude_columns`) | same |
| `${user_column}` | One row per **logged action** — a customer appears once per action received; never NULL | **Exactly one row per customer** — `predict.dig` stops on repeats |
| `${action_column}` | The action label, `VARCHAR`, never NULL; 2–100 distinct values | `NULL` |
| `${reward_column}` | Numeric outcome of the action (0/1, or a value such as revenue), never NULL, observed in `[action time, action time + reward_window_days)` | `NULL` |
| `${timestamp_column}` | Action time, UNIX seconds `BIGINT` | The run date, UNIX seconds |
| Features | **Numeric** context known **before** the action time: counts, sums, recency in days, ratios, 0/1 flags | The same columns, names and types, known before the run date |

The model has no categorical encoding: turn a low-cardinality attribute into 0/1 flags (`IF(tier = 'gold', 1, 0) AS tier_gold`) or a number; leave out free text, emails and IDs. Every other non-feature column goes into `exclude_columns` in `config.yml` (pipe-separated globs; the user, action, reward and timestamp columns and `time` are excluded automatically).

## Variables

Set in `config.yml` (DERIVED) and `data_prep.dig`:

| Variable | Train | Pred |
|---|---|---|
| `${mode}` | `train` | `pred` |
| `${run_date}` | `reference_date`, or the session date when empty | same |
| `${train_start}` … `${train_end}` | Actions logged in this range: `run_date − reward_window_days − train_window_days` … `run_date − reward_window_days` | not used |
| `${scan_start}` | `train_start − feature_lookback_days` | `run_date − feature_lookback_days` |
| `${scan_end}` | run date + 1 day | same |

## Rules

- One file for both modes, so the feature columns are always identical. The `anchors` CTE is the only place the modes differ: logged actions (train) vs. the customers to score at the run date (pred).
- Every feature is measured relative to `anchor_ts` (the action time or the run date): `e.<time> >= anchor_ts − lookback AND e.<time> < anchor_ts`. Nothing at or after the anchor — that is the outcome window.
- Join every feature CTE on the user **and** `anchor_id`; a join on the user alone mixes the context of different actions.
- Keep `TD_TIME_RANGE(<unix_col>, '${scan_start}', '${scan_end}')` on every scan for partition pruning; convert string timestamps with `TD_TIME_PARSE`.
- `COALESCE` count-type features to 0 after a `LEFT JOIN`; leave recency-type features NULL when there is no history (the model imputes them with `impute_type`).
- Reward from an outcome table: 1 if the outcome happened in the window, else 0. Reward already on the action log (clicked, redeemed, order value): use that column instead of the `reward` CTE. A customer with several actions in one window credits the outcome to each — end the window at the next action if that over-counts (`dataprep-guide.md` §4).
- Parent Segment attributes hold **today's** values, not values as of the action — use only stable ones (region, acquisition source, tier rarely changing) as features.
- Digdag renders every `${…}` before the query runs, including inside SQL comments — use only the variables above.
