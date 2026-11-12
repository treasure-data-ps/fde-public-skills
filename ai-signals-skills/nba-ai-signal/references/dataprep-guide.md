# NBA AI Signal — Data Prep Guide

How to turn the customer's data into the two model inputs: the **training log** (one row per past action with its reward and the context before it) and the **prediction input** (one row per customer with the context today). The output contract and variables are in the working copy's `sql/README.md`; config values in `workflow-setup.md` §2; how the model uses the input in `ai-signals-guide.md` §2.

| Term | Meaning |
|---|---|
| Action | One of the choices the business makes per customer: offer, campaign, message, content, channel, treatment |
| Action log | Where past decisions are recorded: campaign sends, offer assignments, coupon issues, journey steps, call-center treatments |
| Reward | What happened after the action, as a number: converted 1/0, redeemed 1/0, clicked 1/0, revenue |
| Context | What was known about the customer just before the action: activity, purchases, engagement, tenure, stable attributes |
| Anchor | The moment the context is measured at: the action time (training) or the run date (scoring) |

---

## 1. Define the use case

| Use case | Actions | Action log | Reward (window) |
|---|---|---|---|
| Offer selection | Offer types or discount levels (incl. "no offer" if logged) | Offer assignments / coupon issues | Redeemed or purchased (7–30 days) |
| Campaign / content choice | Campaign or content IDs or themes | Email / push / SMS sends | Clicked (1–3 days) or converted (7–14 days) |
| Channel choice | email, sms, push, call, ad | Sends per channel | Responded or converted (7–14 days) |
| Retention treatment | Treatments (call, discount, content, none) | Treatment log, CRM tasks | Retained / renewed (30–90 days) |
| Cross-sell | Product categories promoted | Recommendation or promotion log | Bought the promoted category (14–30 days) |

Rules:
- **Actions must be repeatable choices.** One action = one label in the log. Group fine-grained IDs (campaign ID → campaign type, offer code → offer family) to 2–100 labels with hundreds+ rows each. Actions that no longer exist are dropped or merged; new actions can't be recommended until they are in the log.
- **"No action" is an action** only if it is logged (a control group). Otherwise the model only chooses among the actions taken.
- **The log needs variation.** If one segment always got action A and another always B, the model can't learn what B would have done for the first segment. Check per action who received it (§3 query 2); a randomized test or rotation gives the most reliable result.
- **Reward = the business goal, as a number.** 0/1 is easiest to read; revenue works but outliers dominate (cap it). The reward must be observable for every logged action within `reward_window_days`.
- **Who is scored** at prediction: usually the customers eligible for the next decision (active, opted in, not excluded) — one row each.

## 2. Window design

```
training row:  [action time − feature_lookback_days, action time)   →  context
               [action time, action time + reward_window_days)       →  reward
actions used:  [run date − reward_window_days − train_window_days, run date − reward_window_days)
scoring row:   [run date − feature_lookback_days, run date)          →  context
```

| Window | First push | Change when |
|---|---|---|
| `reward_window_days` | Typical time from action to outcome (table §1) | The business definition of success differs |
| `train_window_days` | `180` | Actions or offers change often → `60`–`90`; few actions per day → `365` |
| `feature_lookback_days` | `90` | Slow buying cycles → `180`–`365` |

History check: data must start `reward_window_days + train_window_days + feature_lookback_days` before the run date. Shorter → reduce `train_window_days` first, then `feature_lookback_days`; or set `reference_date` for demo data that ends in the past.

### Leakage checklist

- No feature is measured at or after the anchor (`>= anchor_ts`) — that is the reward window.
- No feature records the outcome (redemption flag, order after the action, status changed by the outcome).
- No feature describes the action itself (campaign ID, offer value) — the action column is the decision; describing it twice leaks it into the context.
- Parent Segment attributes are today's values: only stable ones (region, acquisition source) as features; rebuild recency, totals and status from the behavior tables relative to the anchor.

## 3. Discovery

Queries and their actions: `workflow-setup.md` §1. The two that decide most: the **action mix** (rows, customers and reward rate per action — rare actions are merged or dropped) and the **assignment check** (whether every action reached a mix of customers).

## 4. SQL patterns

All patterns plug into `sql/input_features.sql`, measured relative to `anchor_ts` and joined on the user and `anchor_id`.

**Reward on the action log** (clicked, redeemed, order value recorded with the send):

```sql
-- in anchors (train branch), carry the reward column instead of the reward CTE
SELECT a.<id_col> AS ${user_column}, CAST(a.<action_col> AS VARCHAR) AS ${action_column},
       a.<action_time_col> AS anchor_ts, CAST(COALESCE(a.<reward_col>, 0) AS DOUBLE) AS log_reward
...
-- final SELECT: IF('${mode}' = 'train', an.log_reward) AS ${reward_column}
```

**Reward window ends at the next action** (several actions in a row would otherwise all get credit):

```sql
anchors_w AS (
  SELECT *, LEAST(anchor_ts + ${reward_window_days} * 86400,
                  COALESCE(LEAD(anchor_ts) OVER (PARTITION BY ${user_column} ORDER BY anchor_ts), 9999999999)) AS reward_end_ts
  FROM anchors_n
)
-- reward CTE: o.<outcome_time_col> >= an.anchor_ts AND o.<outcome_time_col> < an.reward_end_ts
```

**Revenue reward, capped:**

```sql
SELECT an.${user_column}, an.anchor_id, LEAST(SUM(o.<amount_col>), <cap>) AS ${reward_column}
```

**Monetary and purchase context:**

```sql
SUM(o.<amount_col>)                                   AS spend_lookback,
COUNT(DISTINCT o.<order_id_col>)                      AS orders_lookback,
(an.anchor_ts - MAX(o.<order_time_col>)) / 86400      AS days_since_last_order
```

**Engagement context** (email, push): opens / clicks in the window, click rate `IF(sends > 0, clicks * 1.0 / sends)`.

**Response to past actions** (strong context for bandits): earlier rewards of the same customer, before the anchor only:

```sql
past_response AS (
  SELECT an.${user_column}, an.anchor_id,
         COUNT(*) AS past_actions, AVG(IF(o2.<id_col> IS NULL, 0.0, 1.0)) AS past_response_rate
  ...  -- prior actions in [anchor_ts − lookback, anchor_ts) with their own outcome known before anchor_ts
)
```

**Stable profile attributes as numbers:**

```sql
IF(p.<tier_col> = 'gold', 1, 0)          AS tier_gold,
DATE_DIFF('day', DATE(FROM_UNIXTIME(p.<signup_ts>)), DATE(FROM_UNIXTIME(an.anchor_ts))) AS tenure_days
```

Scoring population variants (pred branch of `anchors`): active in the last N days (`EXISTS` on the activity table), opted in for the channel, not in a suppression list, Parent Segment `customers`.

## 5. Validate the input tables

Run after `data_prep` (or when `+assert_*` fails). `<db>` = `sink_database`.

```sql
-- 1. training log: rows, actions, reward per action
SELECT <action_column> AS action, COUNT(*) AS n_rows, COUNT(DISTINCT <user_column>) AS users,
       ROUND(AVG(<reward_column>), 4) AS avg_reward, COUNT_IF(<reward_column> > 0) AS rewarded
FROM <db>.<train_input_table> GROUP BY 1 ORDER BY 2 DESC

-- 2. scoring input: one row per customer
SELECT COUNT(*) AS n_rows, COUNT(DISTINCT <user_column>) AS users FROM <db>.<pred_input_table>

-- 3. feature ranges in both modes (same columns, plausible values)
SELECT 'train' AS m, AVG(events_cnt), AVG(days_since_last_event), COUNT_IF(days_since_last_event IS NULL) * 1.0 / COUNT(*) FROM <db>.<train_input_table>
UNION ALL SELECT 'pred', AVG(events_cnt), AVG(days_since_last_event), COUNT_IF(days_since_last_event IS NULL) * 1.0 / COUNT(*) FROM <db>.<pred_input_table>
```

| Symptom | Cause | Fix |
|---|---|---|
| An action has few rows or no rewards | Rare or retired action | Merge into a family or drop it from the log |
| > 100 actions | IDs instead of types | Group in the `anchors` CTE |
| Reward rate near 0 or 1 everywhere | Wrong outcome join or window | Check the outcome table, ID join and `reward_window_days` |
| Scoring rows ≠ customers | Duplicates in the population source | `DISTINCT`, or pick one row per customer |
| Feature means differ a lot between train and pred | Context measured differently, or a time-dependent feature (calendar date, cumulative totals) | Measure relative to `anchor_ts` only |
| Training rows far fewer than expected | `train_end` excludes recent actions by design (reward window), or `reference_date` stale | Expected; widen `train_window_days` |

## 6. Schedules

| Cadence | Setup |
|---|---|
| One cadence (retrain each time) | Schedule in `nba_ais.dig` — weekly is a good default |
| Retrain rarely, recommend often | `train.dig` monthly (or weekly when actions change fast), `predict.dig` daily or before each campaign; leave `nba_ais.dig` unscheduled |

Recommendations are only as fresh as the context: score shortly before the action is sent. Retrain when the action set changes, after a big campaign or season, or when the policy value vs logged reward moves between runs.
