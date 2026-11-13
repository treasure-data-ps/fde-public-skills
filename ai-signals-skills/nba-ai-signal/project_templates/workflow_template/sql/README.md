# Input SQL

`data_prep.dig` runs three queries in both modes:

| # | File | Writes | Edit |
|---|---|---|---|
| 1 | `touchpoints_union.sql` | `${touchpoints_table}_raw` — every source in one event schema | **Project code** — one block per source, rewritten for every project |
| 2 | `touchpoints.sql` | `${touchpoints_table}` — channel per event, sequential touches, conversions | Fixed logic; only the channel rules are extended for customer-specific UTM values |
| 3 | `input_features.sql` | `train_input_table` / `pred_input_table` | Anchors, reward and output contract fixed; context features adapted (per-channel columns from discovery) |

The template files are **example structures** — the workflow cannot run until every `<...>` placeholder is replaced. Patterns per decision type and source: the skill's `references/dataprep-guide.md`.

## 1. Union contract (`touchpoints_union.sql`)

One `UNION ALL` block per source, every block with these columns in this order:

| Column | Rule |
|---|---|
| `${user_column}` | Customer ID, the same ID in every block (join through a lookup table if a source uses another key); never NULL |
| `event_ts` | UNIX seconds `BIGINT` (`TD_TIME_PARSE(<col>)` for text timestamps) |
| `src_name` | Short source label: `web`, `email`, `app`, `push`, `sms`, `call_center`, `orders` … — `action_sources` filters on it |
| `event_type` | What happened (`pageview`, `email_click`, `app_session`, `order` …) |
| `url`, `referrer` | Web only: page URL and referrer; NULL elsewhere |
| `utm_medium`, `utm_source`, `utm_campaign` | Lower-cased traffic-source values: `url_extract_parameter(<url>, 'utm_medium')`, falling back to the referrer URL, or an explicit traffic-source / medium column; NULL when absent |
| `channel_hint` | The channel when the source itself is one (`email`, `app`, `sms`, `push`, `call_center`); NULL for web, so the channel comes from the UTM / referrer |
| `campaign` | Campaign or content name of the event (`utm_campaign`, email campaign) or NULL — the action for `nba_type: campaign` |
| `action_label` | Any other decision label (offer, treatment, content) or NULL — the action for `nba_type: custom` |
| `is_conversion` | `1` for conversion events (orders, sign-ups, bookings) — they become the reward, never a touch; `0` otherwise |
| `conversion_value` | Value of a conversion (order total) or NULL — the reward for `reward_type: value` |

Filter each block with `TD_TIME_RANGE(<time_col>, '${scan_start}', '${scan_end}')`, drop NULL IDs, and keep only customer-relevant events (no bots, internal traffic, email bounces).

## 2. Sequential touchpoints (`touchpoints.sql`)

1. **Channel per event:** `channel_hint` → the UTM rules (medium, then source) → an external referrer host (search engine → `organic_search`, social network → `social`, webmail → `email`, any other site → `referral`); the site's own host (internal navigation) is no signal.
2. **Session inheritance:** an event without a signal takes the latest signal of its source session — internal pageviews keep the landing page's channel, a new UTM or external referrer mid-session switches it; a session without any signal is `direct`.
3. **Sequential touches:** all sources of a customer in time order; consecutive events in the same channel within `session_gap_minutes` are one touch, a channel change or a longer gap starts the next touch.
4. **Conversions** are separate rows (`is_conversion = 1`).

Output columns: `${user_column}`, `touch_ts`, `touch_end_ts`, `channel`, `campaign`, `action_label`, `src_name`, `event_type`, `events_in_touch`, `is_conversion`, `conversion_value`.

Map customer-specific UTM values in the CASE of the `signals` CTE (e.g. `WHEN utm_medium IN ('aff', 'cj') THEN 'affiliate'`); any unmapped medium is kept as its own cleaned value and grouped as `other` later when rare (`min_action_share`).

## 3. Output contract (`input_features.sql`)

| Column | Train (`mode = train`) | Pred (`mode = pred`) |
|---|---|---|
| `session_id` | `'${session_id}'` (in `exclude_columns`) | same |
| `${user_column}` | One row per **decision touch** (a customer appears once per decision); never NULL | **Exactly one row per customer** — every customer with a touch in the `feature_lookback_days` before the run date (`predict.dig` stops on repeats) |
| `${action_column}` | The decision label per `nba_type`, `VARCHAR`; rare ones → `other`; 2–100 distinct values | `NULL` |
| `${reward_column}` | `1.0` / `0.0` (or the converted value) for conversions in `[touch time, reward end)` | `NULL` |
| `${timestamp_column}` | Touch time, UNIX seconds `BIGINT` | The run date, UNIX seconds |
| Features | **Numeric** context known **before** the touch: touch counts, recency, per-channel counts, daypart shares, conversions, contact pressure | The same columns, names and types, known before the run date |

The model has no categorical encoding: every feature is a number or a 0/1 flag. Every other non-feature column goes into `exclude_columns` in `config.yml` (the user, action, reward and timestamp columns and `time` are excluded automatically).

**Decision touches and actions:**

| `nba_type` | Action of a decision touch | Typical `action_sources` |
|---|---|---|
| `channel` | `channel` of the touch | `''` — every engagement across web, email, app … |
| `time` | Local time slot of `touch_ts` in `local_timezone`: `daypart` (morning 6–11, afternoon 12–17, evening 18–23, overnight 0–5), `hour` (`00h`…`23h`) or `dow_daypart` (`mon_morning` …) | The sends the business times, e.g. `email` with send events in the union |
| `campaign` | `campaign` of the touch | The sources that carry campaigns, e.g. `email|web` |
| `custom` | `action_label` of the touch | The source that logs the decision (offer assignments …) |

**Reward window:** `[touch time, touch time + reward_window_days)`, ending earlier at the customer's next decision touch with `reward_attribution: next_touch` (last-touch credit — the default, since touches are frequent); `window` credits every touch in the window.

## Variables

Set in `config.yml` (DECISION, TOUCHPOINTS, DATA PREP, DERIVED) and `data_prep.dig`:

| Variable | Train | Pred |
|---|---|---|
| `${mode}` | `train` | `pred` |
| `${run_date}` | `reference_date`, or the session date when empty | same |
| `${train_start}` … `${train_end}` | Decision touches in this range: `run_date − reward_window_days − train_window_days` … `run_date − reward_window_days` | not used |
| `${scan_start}` | `train_start − feature_lookback_days` | `run_date − feature_lookback_days` |
| `${scan_end}` | run date + 1 day | same |
| `${nba_type}`, `${time_grain}`, `${local_timezone}`, `${action_sources}`, `${min_action_share}`, `${reward_attribution}`, `${reward_type}`, `${session_gap_minutes}`, `${touchpoints_table}` | config values | same |

## Rules

- One feature file for both modes, so the feature columns are always identical; the `anchors` CTE is the only place the modes differ.
- Every feature is measured relative to `anchor_ts` (the touch time or the run date): `>= anchor_ts − lookback AND < anchor_ts`. Nothing at or after the anchor.
- Join every feature CTE on the user **and** `anchor_id`.
- Per-channel feature columns are literal: set them to the top channels of discovery query 3 (`workflow-setup.md` §1), named `touches_<channel>`.
- `COALESCE` count-type features to 0 after a `LEFT JOIN`; leave recency and share features NULL when there is no history (the model imputes them).
- Parent Segment attributes hold **today's** values — use only stable ones (region, acquisition source) as features, joined in `input_features.sql`.
- Digdag renders every `${…}` before the query runs, including inside SQL comments — use only the variables above.
