# Classifier — Data Prep Guide

Business question → model input tables. Read in Phase 1 (use case, snapshots, history check) and whenever `sql/input_features.sql` is written or changed. Contract and variables: `<workdir>/sql/README.md`.

| Table | Grain | Columns |
|---|---|---|
| `train_input_table` | entity × training cutoff | `session_id`, `cutoff_date`, `user_id_column`, features, `target_column` (0/1) |
| `pred_input_table` | entity at the scoring cutoff (run date) | same; target constant and ignored |

## Rules

1. **Never guess the business definition** — label, horizon, population come from the user (`AskUserQuestion`, options + recommendation).
2. **Leakage-safe:** features `event_time < cutoff`; label `[cutoff, cutoff + label_window_days)`; recency / tenure from the cutoff, never today; no current-state attributes.
3. **One SQL for both modes** — only the cutoff set differs.
4. **Mature labels:** latest training cutoff + horizon ≤ run date — guaranteed by `data_prep.dig` while the data reaches the run date; stale data → `reference_date`.
5. **Validate (§5) before scheduling (§6).**

---

## 1. Define the use case

| Decision | Ask | Typical | Sets |
|---|---|---|---|
| Target event | "What exactly counts as a 1?" | Table below | `label` CTE, `target_column` |
| Horizon | "How far ahead?" | 30 d (weekly / monthly action), 90 d (strategic) | `label_window_days` |
| Observation window | "How much history for features?" | 6–12 months + 7 / 30 / 90-day sub-windows | `feature_lookback_days` |
| Population | "Who is scored?" | Active in the window, minus converted / internal | `population` CTE |
| Snapshots | You decide (§2), user confirms | — | `n_train_snapshots`, `spacing_days` |
| Cadence | "How often retrain / score?" | Monthly / weekly | §6 |
| Expected label rate | "Roughly what share is positive?" | — | §5 sanity check |

### Label templates

| Use case | Population at cutoff | Label = 1 in `[cutoff, cutoff + horizon)` | Ask |
|---|---|---|---|
| Churn — retail / app | ≥ N events in `active_days` before | **No** qualifying activity | Which activity counts · `active_days` · N · returns? |
| Churn — subscription | Active at cutoff (dated history) | Cancellation / non-renewal | Which status / event · voluntary only · downgrades? |
| Conversion | Not converted before, seen in window | Conversion event | Which event · min one touch? |
| Cross-sell / upsell | Active (optionally never bought target) | Purchase in target category | Include existing buyers? |
| Renewal | Contract expiring within horizon | Renews | Renewal window · early renewals? |
| Reactivation | No activity in `lapse_days` before | Any qualifying activity | `lapse_days` · what counts? |
| Campaign response | Targeted / eligible at cutoff | Attributed click / purchase | Attribution · control group |
| Lead scoring | Open leads at cutoff | Lead won / applied | Which stage · lead age cap? |

- Churn is inverse activity — the "active before" population is what makes it meaningful.
- Exclude anything known at the cutoff (already cancelled, converted, closed).
- A status table updated in place can't give the label — use events or dated history.

### Spec to confirm (record in `project_state.md`)

```
Use case:        Churn (retail)
Label (1):       no non-returned purchase in [cutoff, cutoff + 60d)
Population:      >= 2 purchases in [cutoff - 180d, cutoff); no employees
Horizon / window: 60 / 180 days (sub-windows 30, 90)
Snapshots:       4, 60 days apart — seasonal retail, ~20% churn
Scoring cutoff:  run date
Cadence:         retrain monthly, score weekly
Expected rate:   ~15-25%
```

## 2. Snapshot (cutoff) design

```
 |<-- features: feature_lookback_days -->|<-- label: label_window_days -->|
 cutoff - lookback                     cutoff                    cutoff + horizon

run_date       = reference_date or session date
pred cutoff    = run_date
train cutoff k = run_date - spacing_days * k,  k = ceil(horizon/spacing) .. + n_train_snapshots - 1
```

Example — run 2026-10-19, horizon 60, spacing 60, 4 snapshots, window 180:

| split | cutoff | features from | label window |
|---|---|---|---|
| pred | 2026-10-19 | 2026-04-22 | — |
| train | 2026-08-20 | 2026-02-21 | → 2026-10-19 |
| train | 2026-06-21 | 2025-12-23 | → 2026-08-20 |
| train | 2026-04-22 | 2025-10-24 | → 2026-06-21 |
| train | 2026-02-21 | 2025-08-25 | → 2026-04-22 |

**History check (must pass):** `spacing_days × (ceil(horizon / spacing) + n_train_snapshots − 1) + feature_lookback_days` days of data (example: 420). Short → fewer snapshots first, then a shorter window; tell the user.

### Choosing the snapshots

No fixed default — decide from use case, label balance and history; give a one-line reason; confirm in the Phase 1 table. An entity appears once per snapshot (intended).

| Situation | Snapshots | Spacing |
|---|---|---|
| Thousands of positives at one cutoff, stable behavior | 1–2 | = horizon |
| Rare outcome (< ~1–2% or a few hundred positives) | 4–6 | = horizon |
| Seasonal business | Cover a year: `n × spacing ≥ 365` | = horizon |
| Long horizon (≥ 180 d) or short history | What the history check allows, often 1–2 | 30–60 (overlapping labels) |
| Behavior changed recently (product, pricing, tracking) | 1–2, recent only | = horizon |
| Lead scoring / short lifecycle | 2–4 | 30 d or the lead cycle |
| Renewal / contracts | 3–4, covering several cycles | = horizon |
| Short horizon (≤ 30 d), frequent scoring | 4–8 | = horizon |

Notes:
- The random test split mixes cutoffs; out-of-time check = §5 check 8 and `workflow-setup.md` §4 check 6.
- Ingestion lag of a few days shortens the latest label window slightly — schedule after the load; demos / stale data → `reference_date`.

### Leakage checklist

- Every feature filter has `event_time < cutoff_ts`, lifetime features included.
- Recency = `DATE_DIFF('day', last_event, cutoff_dt)`, never `current_date`.
- Profile: immutable or as-of-cutoff only. Current status, tier, flags and Parent Segment recency / lifetime attributes leak.
- Nothing from the label source inside the label window.
- Cross-sell: prior target-category purchases before the cutoff are fine.

## 3. Discovery for the design

Run the queries in `workflow-setup.md` §1. Record per source:

| Item | Example |
|---|---|
| Role | Label source / behavioral feature source / profile source |
| ID column, event-time column | `customer_id`, `time` or `TD_TIME_PARSE(order_date)` |
| Useful columns | Event type, amount, category, channel |
| Current-state columns | Status, tier, flags — exclude or rebuild as of cutoff |

## 4. SQL patterns

Template shape: `cutoffs` → `population` → feature CTEs → `label` → final SELECT. Every CTE carries `cutoff_date`; every join is on ID **and** `cutoff_date`.

### Population

```sql
-- Active customers: >= <min_events> events in the <active_days> before the cutoff (keep <active_days> <= feature_lookback_days)
population AS (
  SELECT c.cutoff_date, c.cutoff_dt, c.feature_start_ts, c.cutoff_ts, c.label_end_ts, e.<id_col> AS ${user_id_column}
  FROM cutoffs c
  JOIN <source_database>.<events_table> e
    ON e.time >= c.cutoff_ts - <active_days> * 86400 AND e.time < c.cutoff_ts
  WHERE TD_TIME_RANGE(e.time, '${scan_start}', '${scan_end}') AND e.<id_col> IS NOT NULL
  GROUP BY 1, 2, 3, 4, 5, 6
  HAVING COUNT(*) >= <min_events>
)
```

| Use case | Rule |
|---|---|
| Conversion | Seen in window and `NOT EXISTS` conversion with `conv.time < c.cutoff_ts` |
| Subscription churn | `start_ts < cutoff_ts AND (end_ts IS NULL OR end_ts >= cutoff_ts)` from dated history |
| Reactivation | `HAVING MAX(e.time) < c.cutoff_ts - <lapse_days> * 86400` |
| Lead scoring | Created before the cutoff, not closed before it |

### Label

```sql
label AS (
  SELECT DISTINCT c.cutoff_date, o.<id_col> AS ${user_id_column}, 1 AS ${target_column}
  FROM cutoffs c
  JOIN <source_database>.<outcome_table> o ON o.<time_col> >= c.cutoff_ts AND o.<time_col> < c.label_end_ts
  WHERE TD_TIME_RANGE(o.<time_col>, '${scan_start}', '${scan_end}')  -- AND <label filter>
)
-- final SELECT: CAST(COALESCE(l.${target_column}, 0) AS BIGINT) AS ${target_column}
```

Activity churn: `label` = entities **with** activity; final SELECT `CAST(CASE WHEN l.${user_id_column} IS NULL THEN 1 ELSE 0 END AS BIGINT)`. At scoring the target is then 1 for all — ignored, never read it.

### Feature CTE per source

```sql
<src>_features AS (
  SELECT c.cutoff_date, e.<id_col> AS ${user_id_column},
    COUNT_IF(e.time >= c.cutoff_ts - 30 * 86400)                   AS <src>_events_30d,
    COUNT_IF(e.time >= c.cutoff_ts - 90 * 86400)                   AS <src>_events_90d,
    COUNT(*)                                                        AS <src>_events_window,
    COUNT(DISTINCT TD_TIME_FORMAT(e.time, 'yyyy-MM-dd'))            AS <src>_active_days,
    SUM(IF(e.time >= c.cutoff_ts - 90 * 86400, e.<amount_col>, 0)) AS <src>_amount_90d,
    SUM(e.<amount_col>)                                             AS <src>_amount_window,
    DATE_DIFF('day', DATE(FROM_UNIXTIME(MAX(e.time))), c.cutoff_dt) AS <src>_days_since_last,
    COUNT(DISTINCT e.<category_col>)                                AS <src>_category_cnt,
    CAST(COUNT_IF(e.time >= c.cutoff_ts - 30 * 86400) AS DOUBLE)
      / NULLIF(COUNT_IF(e.time >= c.cutoff_ts - 90 * 86400), 0)     AS <src>_trend_30_90
  FROM cutoffs c
  JOIN <source_database>.<source_table> e ON e.time >= c.feature_start_ts AND e.time < c.cutoff_ts
  WHERE TD_TIME_RANGE(e.time, '${scan_start}', '${scan_end}')
  GROUP BY c.cutoff_date, c.cutoff_dt, c.cutoff_ts, e.<id_col>
)
```

| Source | Features (all before the cutoff) |
|---|---|
| Orders | Counts / spend per window, avg basket, days since last, purchase gap, category breadth, discount share, return rate |
| Web / app | Sessions, active days, page depth, key-page visits (pricing, cancel, support), days since last visit |
| Email | Sends, opens, clicks, open / click rate, days since last open, unsubscribes |
| Support | Tickets per window, open at cutoff, negative sentiment, days since last |
| Subscription | Tenure at cutoff, plan changes, downgrades, payment failures |
| Profile | Signup tenure, acquisition channel, region, age band — no current-state flags |

### Final SELECT

- List every feature (no `SELECT *`) — the list is the train / predict contract.
- Counts / amounts → `COALESCE(…, 0)`; recency / ratios → keep NULL.
- All-history tenure → profile signup / `first_seen` date (the scan starts at `scan_start`).
- Heavy source → feature table in a `_parallel` block in `data_prep.dig`, grouped by ID + `cutoff_date`.

```yaml
# data_prep.dig — before +create_input_table; join the tables in input_features.sql on (ID, cutoff_date)
+create_features:
  _parallel: true

  +f_<source1>:
    td>: sql/features_<source1>.sql
    create_table: classify_f_<source1>_${mode}

  +f_<source2>:
    td>: sql/features_<source2>.sql
    create_table: classify_f_<source2>_${mode}
```

## 5. Validate the input tables

After the first `data_prep` and every SQL change, before `workflow-setup.md` §4 checks 2–5. Show: check · value · pass / fail · action.

| # | Check | Pass |
|---|---|---|
| 1 | Cutoffs | Train: `n_train_snapshots` dates, latest + horizon ≤ run date. Pred: one = run date |
| 2 | Population per cutoff | Non-zero, ±30% across cutoffs; pred ≈ latest train cutoff |
| 3 | Label rate per cutoff | Both classes, minority ≥ 1%, stable, near the expectation |
| 4 | Duplicates | 0 repeated (ID, `cutoff_date`) |
| 5 | Parity | Same columns and types in both tables |
| 6 | Null / constant | No feature 100% NULL or constant; flag > 90% NULL |
| 7 | Leakage | No \|corr\| > 0.9 to the target; no current-state attributes |
| 8 | Drift | Pred means vs latest train cutoff: flag > 50% change |
| 9 | `columns_to_drop` | `time`, `session_id`, `cutoff_date` + every non-feature |

```sql
-- 1-3
SELECT cutoff_date, COUNT(*) AS n, SUM(<target_column>) AS positives, ROUND(AVG(CAST(<target_column> AS DOUBLE)), 4) AS label_rate
FROM <db>.<train_input_table> GROUP BY 1 ORDER BY 1;
SELECT cutoff_date, COUNT(*) AS n FROM <db>.<pred_input_table> GROUP BY 1;
-- 4
SELECT COUNT(*) AS dup_keys FROM (SELECT <user_id_column>, cutoff_date FROM <db>.<train_input_table> GROUP BY 1, 2 HAVING COUNT(*) > 1);
-- 5: tdx describe both tables
-- 6
SELECT AVG(IF(<feature> IS NULL, 1.0, 0.0)) AS null_rate, APPROX_DISTINCT(<feature>) AS distinct_values FROM <db>.<train_input_table>;
-- 7
SELECT CORR(CAST(<feature> AS DOUBLE), CAST(<target_column> AS DOUBLE)) AS corr FROM <db>.<train_input_table>;
-- 8
SELECT 'train_latest' AS src, AVG(CAST(<feature> AS DOUBLE)) AS mean_val FROM <db>.<train_input_table>
WHERE cutoff_date = (SELECT MAX(cutoff_date) FROM <db>.<train_input_table>)
UNION ALL SELECT 'pred', AVG(CAST(<feature> AS DOUBLE)) FROM <db>.<pred_input_table>;
```

| Symptom | Cause | Fix |
|---|---|---|
| Label rate ≈ 0% / 100% | Population or label filter wrong | Revisit both |
| Latest cutoff rate much lower | Data ends before the run date | `reference_date` = last loaded date |
| Fewer cutoffs than set / earliest nearly empty | History too short | Fewer snapshots or shorter window |
| Duplicates | Fan-out, or a CTE joined on ID only | One row per (ID, `cutoff_date`); join on both |
| Pred table empty | Source stopped, or population excludes recent entities | Check last event date, `reference_date` |
| Feature NULL in pred only | Source not refreshed | Confirm freshness or drop it |

## 6. Schedules

Ask (requirements 18–19); none for a test account. Pushing a schedule activates it — confirm first.

| Rule | Why |
|---|---|
| Score only after a successful training | No model under `model_name` → predict fails |
| Different cadences → schedule `train.dig` and `predict.dig`, not `classify.dig` | `classify.dig` always runs both |
| Train and score at different hours | Scoring would use the previous model mid-training |
| Retrain no more often than every `label_window_days / 2` | Labels change only as horizons mature |
| Daily scoring only if the business acts daily | Every run appends a full batch |

| Use case | `train.dig` | `predict.dig` |
|---|---|---|
| Churn / cross-sell, 30–60 d | `monthly>: 1,02:00:00` | `weekly>: Mon,06:00:00` |
| Lead scoring | `weekly>: Sun,02:00:00` | `daily>: 06:00:00` |
| Renewal, 90 d | `monthly>: 1,02:00:00` | `monthly>: 2,06:00:00` |

Uncomment the placeholders at the top of `train.dig` / `predict.dig` (or `classify.dig` for one cadence):

```yaml
# train.dig
timezone: UTC
schedule:
  monthly>: 1,02:00:00
_error:
  mail>: body.txt
  subject: Classifier Training failed - <Project Name>
  to: ['<alert address>']

# predict.dig
timezone: UTC
schedule:
  weekly>: Mon,06:00:00
_error:
  mail>: body.txt
  subject: Classifier Scoring failed - <Project Name>
  to: ['<alert address>']
```
