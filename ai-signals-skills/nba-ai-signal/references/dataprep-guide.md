# NBA AI Signal — Data Prep Guide

How to turn the customer's data into the model inputs for any next best action — channel, time, campaign or a custom action. The pipeline is the same for every decision type:

```
sources (web, email, app, sms, call center, orders …)
  → sql/touchpoints_union.sql   one event schema, UTM / traffic source extracted        → <touchpoints_table>_raw
  → sql/touchpoints.sql         channel per event, session inheritance, sequential touches → <touchpoints_table>
  → sql/input_features.sql      decision touches + action (nba_type) + reward + context  → train_input_table / pred_input_table
```

Contracts and variables: the working copy's `sql/README.md`; config values: `workflow-setup.md` §2; how the model uses the input: `ai-signals-guide.md` §2.

| Term | Meaning |
|---|---|
| Event | One row of a source: a pageview, an email click, an app session, an order |
| Touch | Consecutive events of one customer in the same channel within `session_gap_minutes` — the unit the model decides on |
| Decision touch | A touch that counts as a decision (every touch, or only those from `action_sources`) — one training row |
| Action | The label of a decision touch per `nba_type`: its channel, local time slot, campaign or custom label |
| Reward | What happened after the decision touch: converted 1/0, or the converted value |
| Context | What was known about the customer just before the touch: touch history, channel mix, time-of-day profile, conversions |

---

## 1. Choose the decision

| `nba_type` | The model answers | Decision touches (`action_sources`) | Action | Reward (window) |
|---|---|---|---|---|
| `channel` | Through which channel to reach the customer | `''` — every touch across web, email, app, SMS, ads … | The touch's channel | Conversion until the next touch (`next_touch`) or 7–14 days |
| `time` | When to send (daypart, hour, day × daypart) | The sends the business times — `email_send`, `push_send` | Local time slot of the touch (`time_grain`, `local_timezone`) | Open / click (1–2 days) or conversion (3–7 days) |
| `campaign` | Which campaign or content to send | Sends or ad clicks that carry a campaign — `email_send`, `web` | The touch's `campaign` | Conversion (7–14 days) |
| `custom` | Which offer / treatment / content | The decision log's source (offer assignments, treatments) | The touch's `action_label` | Redemption / purchase / retention (7–90 days) |

Rules:
- **2–100 actions with hundreds+ rows each.** Rare channels, mediums or campaigns are grouped as `other` by `min_action_share`; group campaign IDs to themes in the union when there are hundreds.
- **The model only chooses among actions that happened.** A channel or time slot the business never used can't be recommended.
- **The log needs variation.** If one segment always got email and another always SMS, the model can't learn what SMS would have done for the first. Check per action who received it (`workflow-setup.md` §1 query 5).
- **Time decisions need business-timed sends.** The time of a customer's own visits is the customer's choice, not the business's; use send events as decision touches and the engagement after them as the reward. With engagement-only data, say so — the result describes when customers are active, not when to send.
- **Several decisions** (channel and time) are separate projects with their own `nba_type`, `model_name` and sink database.

## 2. Window design

```
decision touch:  [touch time − feature_lookback_days, touch time)          → context
                 [touch time, min(touch time + reward_window_days, next decision touch))  → reward (next_touch)
decisions used:  [run date − reward_window_days − train_window_days, run date − reward_window_days)
scoring row:     [run date − feature_lookback_days, run date)               → context
```

| Window | First push | Change when |
|---|---|---|
| `reward_window_days` | Per decision (table §1) | The business definition of success differs |
| `reward_attribution` | `next_touch` | Sparse touches (a send a week) → `window` |
| `train_window_days` | `180` | Channels or campaigns change often → `60`–`90`; few touches per day → `365` |
| `feature_lookback_days` | `90` | Slow buying cycles → `180`–`365` |
| `session_gap_minutes` | `30` | Multi-device or slow journeys → `60` |

History check: data must start `reward_window_days + train_window_days + feature_lookback_days` before the run date. Shorter → reduce `train_window_days` first, then `feature_lookback_days`; or set `reference_date` for demo data that ends in the past.

### Leakage checklist

- No feature is measured at or after the anchor (`>= anchor_ts`) — that is the reward window.
- No feature records the outcome (a conversion flag inside the touch, an order after it).
- No feature describes the action itself (the touch's channel, campaign or hour as a feature) — the action column is the decision.
- Parent Segment attributes are today's values: only stable ones (region, acquisition source) as features.

## 3. The touchpoint union and channel extraction

One block per source in `sql/touchpoints_union.sql`, every block in the union contract (`sql/README.md` §1). How to fill the traffic-source columns per source type:

| Source | `src_name` | `channel_hint` | `utm_medium` / `utm_source` / `utm_campaign` | `campaign` |
|---|---|---|---|---|
| Web pageviews with UTM in the URL | `web` | NULL | `url_extract_parameter(<url>, 'utm_medium')` … — fallback `url_extract_parameter(<referrer>, …)` | `utm_campaign` |
| Web with explicit traffic-source columns (GA-style `traffic_source`, `medium`, `source`) | `web` | NULL | Those columns, lower-cased | The campaign column |
| Web with only a referrer | `web` | NULL | NULL — the referrer host classifies the session (`touchpoints.sql`) | NULL |
| Email events (opens, clicks) | `email` | `'email'` | `'email'`, the ESP | Email campaign name |
| Email / push / SMS sends (the business's decisions) | `email_send`, `push_send`, `sms_send` | `'email'`, `'push'`, `'sms'` | — | Campaign name |
| App sessions / events | `app` | `'app'` (or `'push'` for push opens) | Deep-link UTM if present | Deep-link campaign |
| Call center, stores, sales reps | `call_center`, `store` | `'call_center'`, `'store'` | — | Topic / reason, if any |
| Ad clicks / impressions logs | `ads` | NULL | The platform's medium / source fields | Ad campaign |
| Orders, sign-ups, bookings | `orders` | NULL | NULL | Coupon / promo, if any; `is_conversion = 1`, `conversion_value` = order total |

UTM handling, in the union:
- Lower-case and trim every extracted value; `TRY(url_extract_parameter(…))` returns NULL for broken URLs. Encoded values (`email%20blast`) are decoded with `url_decode` if discovery shows them.
- UTM present on any page of a visit counts — a mid-session UTM or external referrer starts the new channel, later internal pageviews inherit it (`touchpoints.sql`).
- Paid platforms often set `utm_source` only (`facebook`, `google`) — the source rules cover them.

Channel rules, in the `signals` CTE of `touchpoints.sql` — extend only with the customer's own values from discovery query 3:

| Signal | Channel |
|---|---|
| `channel_hint` | As given |
| medium `email`, `newsletter`, `crm` / source an ESP | `email` |
| medium `sms`, `push` | `sms`, `push` |
| medium `affiliate`, `partner` | `affiliate` |
| medium or source a social network | `paid_social` with `cpc` / `cpm` / `paid`, else `social` |
| medium `cpc`, `ppc`, `paid_search`, `sem` | `paid_search` |
| medium `display`, `banner`, `cpm`, `programmatic`, `video` | `display` |
| medium `referral` / `organic` | `referral` / `organic_search` |
| any other medium | the medium, cleaned (`[^a-z0-9]` → `_`) — grouped as `other` if rare |
| no UTM, external referrer: webmail / search engine / social network / other site | `email` / `organic_search` / `social` / `referral` |
| no signal in the session | `direct` |

Sequencing: all sources of a customer in time order; consecutive events in the same channel within `session_gap_minutes` become one touch (`events_in_touch` counts them), a channel change starts the next touch — so an email click followed by the pageviews it opened is one `email` touch, and a later paid-search visit is the next touch. Conversions stay separate rows and never break or merge touches.

## 4. SQL patterns (`input_features.sql`)

All patterns are measured relative to `anchor_ts` and joined on the user and `anchor_id`.

**Per-channel context** — one literal column per top channel from discovery query 3:

```sql
COUNT_IF(t.channel = 'paid_search')                     AS touches_paid_search,
MAX(IF(t.channel = 'email', t.touch_ts))                AS last_email_ts,   -- → days_since_last_email
```

**Last channel before the decision** as 0/1 flags (numeric only):

```sql
IF(element_at(ARRAY_AGG(t.channel ORDER BY t.touch_ts DESC), 1) = 'email', 1, 0) AS last_channel_email
```

**Response by channel** (strong context for channel NBA): conversions within N days after earlier touches of a channel, before the anchor only.

**Time-of-day profile** (for time NBA, shipped): `share_morning`, `share_afternoon`, `share_evening`, `share_weekend`; add `share_<hour block>` for `hour` grain.

**Monetary context:** `conversion_value_sum`, `conversions_cnt`, `days_since_last_conversion` (shipped); average order value `IF(cnt > 0, sum / cnt)`.

**Revenue reward, capped** — cap `conversion_value` in the orders block of the union: `LEAST(o.<amount>, <cap>)`.

**Stable profile attributes as numbers** — join the profile table in `input_features.sql`:

```sql
IF(p.<tier_col> = 'gold', 1, 0)                                                         AS tier_gold,
DATE_DIFF('day', DATE(FROM_UNIXTIME(p.<signup_ts>)), DATE(FROM_UNIXTIME(an.anchor_ts)))  AS tenure_days
```

**Scoring population variants** (pred branch of `anchors`): customers with a touch in the lookback (shipped), opted in for the channel, not in a suppression list, Parent Segment `customers` (one row each).

## 5. Validate the input tables

Run after `data_prep` (or when `+assert_*` fails). `<db>` = `sink_database`, `<tp>` = `touchpoints_table`.

```sql
-- 1. union: rows per source and UTM coverage of web
SELECT src_name, COUNT(*) AS events, COUNT(DISTINCT <user_column>) AS users,
       ROUND(AVG(IF(utm_medium IS NOT NULL OR utm_source IS NOT NULL, 1.0, 0.0)), 3) AS utm_share
FROM <db>.<tp>_raw GROUP BY 1 ORDER BY 2 DESC

-- 2. touches: channel mix and events per touch
SELECT channel, COUNT(*) AS touches, ROUND(AVG(events_in_touch), 1) AS events_per_touch
FROM <db>.<tp> WHERE is_conversion = 0 GROUP BY 1 ORDER BY 2 DESC

-- 3. training log: rows and reward per action
SELECT <action_column> AS action, COUNT(*) AS n_rows, COUNT(DISTINCT <user_column>) AS users,
       ROUND(AVG(<reward_column>), 4) AS avg_reward
FROM <db>.<train_input_table> GROUP BY 1 ORDER BY 2 DESC

-- 4. scoring input: one row per customer
SELECT COUNT(*) AS n_rows, COUNT(DISTINCT <user_column>) AS users FROM <db>.<pred_input_table>
```

| Symptom | Cause | Fix |
|---|---|---|
| `direct` holds most web touches | UTM not extracted (wrong column, values in another parameter or column), or referrer missing | Check the raw URLs; use the traffic-source column or the referrer URL fallback |
| Many unknown channels from mediums | Customer-specific UTM values | Add rules in `touchpoints.sql`; or raise `min_action_share` |
| `events_per_touch` ≈ 1 for web | `session_gap_minutes` too small, or channel flips between pageviews | Raise the gap; check that internal referrers are the site's own host |
| One touch per customer per day across channels | Sources share one channel by mistake (`channel_hint` on web) | Leave `channel_hint` NULL for web |
| An action has few rows or no rewards | Rare or retired action | Group it (`min_action_share`, campaign themes) or drop it |
| > 100 actions | Campaign IDs / hours × days | Group in the union; coarser `time_grain` |
| Reward near 0 everywhere | Conversion source missing or `is_conversion` not set; `next_touch` with very frequent touches | Check the orders block; try `window` with a shorter `reward_window_days` |
| Scoring rows ≠ customers | Duplicates in a population source | `DISTINCT`, one row per customer |
| Feature means differ a lot between train and pred | Context measured differently | Measure relative to `anchor_ts` only |

## 6. Schedules

| Cadence | Setup |
|---|---|
| One cadence (retrain each time) | Schedule in `nba_ais.dig` — weekly is a good default |
| Retrain rarely, recommend often | `train.dig` monthly (weekly when channels or campaigns change fast), `predict.dig` daily or before each send; leave `nba_ais.dig` unscheduled |

Recommendations are only as fresh as the context: score shortly before the decision is used. Retrain when the action set changes (new channel, campaign set, offers), after a big campaign or season, or when the policy value vs logged reward moves between runs.
