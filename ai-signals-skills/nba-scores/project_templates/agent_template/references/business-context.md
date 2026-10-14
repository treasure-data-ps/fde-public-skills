# NBA Engagement Scores — Business Context

Use this document to interpret NBA scores, flags, and dashboard metrics in the context of how the workflow logic actually works. For table schemas, see `data-dictionary.md`.

---

## What the NBA Workflow Produces

For every unique profile in the customer's data, the workflow writes one row of NBA scores into `nba_combined_metrics_final`. The workflow is run periodically (usually monthly) and each run is identified by a `session_id`.

The NBA outputs span three groups:

* **Affinity scores** (sections 1–2) — multi-valued per-channel and per-daypart engagement scores.
* **Profile-level flags** (sections 3–8) — six boolean flags describing recency, engagement, and audience-segment membership. ALL six are produced by every run and ALL six matter when summarizing.
* **Per-event signal** (section 9) — `conversion_flag` from source data, surfaced both at the event level and aggregated up to a profile-level flag.

### 1. Next Best Channel (NBC)

**Question it answers:** "Which marketing channel is this profile most likely to engage with?"

**How it's built:**
1. Every event in the unioned activity table is tagged with a `channel` (via UTM parsing on web data, hardcoded labels for email / sales-rep / order events, regex rules for known ad channels).
2. For each profile, count or aggregate activity per channel.
3. Apply the configured `scoring_logic` (`percentile`, `quartile`, or `minmax`) to convert raw counts into a comparable score per channel.

**Output columns** in the dashboard:
- `metric_name` like `next_best_channel_social`, `next_best_channel_email`, `next_best_channel_search`, `next_best_channel_paid_search`, etc.
- `metric_value` is the score / bucket. Format depends on `scoring_logic`:
  - `percentile` → numeric percentile (e.g. `"0.92"`)
  - `quartile` → bucket label (`"1"`, `"2"`, `"3"`, `"4"`)
  - `minmax` → 0-1 scaled value

### 2. Next Best Time (NBT)

**Question it answers:** "What time of day is this profile most likely to engage?"

**How it's built:**
1. Every event timestamp is bucketed into one of four (configurable) dayparts based on `time_hour`:
   - `morning` (6 AM – 11:59 AM)
   - `afternoon` (12 PM – 5:59 PM)
   - `evening` (6 PM – 11:59 PM)
   - `overnight` (12 AM – 5:59 AM)
2. For each profile, count activity per daypart.
3. Apply the same `scoring_logic` as NBC.

**Output columns:** `metric_name` like `next_best_time_morning`, `next_best_time_evening`, etc.

**Timezone alignment:** The workflow shifts UTC timestamps by `timeshift_hours` (added or subtracted via `timeshift_change`) before bucketing. This matters when interpreting scores — "evening" means evening **in the customer's marketing timezone**, not UTC.

### 3. Cart Abandon Flag

**Question it answers:** "Did this profile add something to cart in the last N days without purchasing?"

**How it's built:**
- Look in the unioned activity table for events matching `abandon_regexp` (default: `event_type` containing both `'add'` and `'cart'`).
- Track each profile's `last_cart_add_date` (most recent add-to-cart event) and `last_purchase_date`.
- Flag = `1` if `last_cart_add_date > last_purchase_date` AND `last_cart_add_date` is within `event_lookback` days. Otherwise `0`.

**Output column:** `metric_name = 'cart_abandon_flag'`, `metric_value` is `'0'` or `'1'`.

**Common tuning:** If the customer's add-to-cart event is named differently (e.g., `basket_add`, `cart_item_added`), update `abandon_regexp` and `abandon_regexp_string` in `next_best_campaign`. If `event_lookback` is too long, you'll over-flag people who eventually converted weeks later; too short and you'll under-flag genuine abandonment.

### 4. New Visitor Flag

**Question it answers:** "Is this a recently-acquired profile that we haven't engaged with yet?"

**How it's built:** All three conditions must be true:
1. `ad_engagement_flag = 0` — has never engaged on a paid/ad channel matching `ad_engagement_logic`
2. `conversion_flag = 0` — has never converted
3. First visit ≤ `new_customers_days` ago

**Output column:** `metric_name = 'new_visitor_flag'`, `metric_value` is `'0'` or `'1'`.

**Why these conditions?** This isn't just "first-time visitor" — it specifically targets organic, low-engagement, unconverted profiles. Useful for "welcome series" campaigns where you don't want to spam someone who arrived via ad clicks (already heavily targeted) or already-converted profiles.

### 5. Ad Engagement Flag

**Question it answers:** "Has this profile ever engaged with paid/ad channels in the data window?"

**How it's built:** `MAX(IF(channel IN <ad_engagement_logic>, 1, 0))` per profile across all events. The `ad_engagement_logic` config defaults to `channel IN ('paid search', 'tiktok', 'web ads', 'dsp_rtb', 'maddict', 'call center', 'others', 'display')`.

**Output column:** `metric_name = 'ad_engagement_flag'`, `metric_value` is `'0'` or `'1'`.

**Marketing meaning:** Lifetime indicator. Use to separate ad-responsive audiences from organic-only audiences. Combined with `new_visitor_flag` to identify cold leads.

### 6. Recent Ad Engagement Flag

**Question it answers:** "Has this profile engaged with paid/ad channels recently?"

**How it's built:** Tracks each profile's `last_ad_engagement_date` (most recent event on a channel matching `ad_engagement_logic`). Flag = `1` if `last_ad_engagement_date` is within `event_lookback` days. Otherwise `0`.

**Output column:** `metric_name = 'recent_ad_engagement_flag'`, `metric_value` is `'0'` or `'1'`.

**Marketing meaning:** Action-ready signal. Profiles flagged here are warm — already responding to ads in the recency window, ideal for retargetting. The difference between `ad_engagement_flag` (lifetime) and `recent_ad_engagement_flag` (recency) tells you who's actively responsive vs. who's gone cold.

### 7. Recent Purchase Flag

**Question it answers:** "Has this profile converted recently?"

**How it's built:** Tracks each profile's `last_purchase_date` (most recent event matching `conversion_logic`). Flag = `1` if `last_purchase_date` is within `event_lookback` days. Otherwise `0`.

**Output column:** `metric_name = 'recent_purchase_flag'`, `metric_value` is `'0'` or `'1'`.

**Marketing meaning:** Suppression / upsell signal. Profiles flagged here just converted — exclude from acquisition campaigns, target with cross-sell or post-purchase nurture. Distinct from `conversion_flag` which captures *any* conversion in the data window (lifetime), not just recent.

### 8. No Ads or Purchases Flag

**Question it answers:** "Has this profile never engaged with paid channels and never converted?"

**How it's built:** `IF(ad_engagement_flag = 0 AND conversion_flag = 0, 1, 0)` per profile.

**Output column:** `metric_name = 'no_ads_or_purchases_flag'`, `metric_value` is `'0'` or `'1'`.

**Marketing meaning:** The "cold" or "dormant" audience. Different from `new_visitor_flag` (which adds a recency requirement) — these profiles may have been around a long time but never engaged with ads or converted. Candidates for re-activation campaigns, organic-channel nurture, or audience cleanup.

### 9. Conversion Flag (per-event signal AND profile-level flag)

**Question it answers:** "Did this profile complete a defined conversion event in the data window?"

**How it's built:** During the union step, every source-table row gets tagged with a `conversion_flag`:
- Pageviews: `IF(REGEXP_LIKE(td_path, 'thank|download|order-received'), 1.0, 0.0)` (or whatever pattern was configured)
- Email events: `0.0`
- Sales-rep interactions: `0.0`
- Orders: `1.0` (filtered to valid statuses)

Per-profile, the dashboard's `converted_users` column counts how many profiles have at least one row with `conversion_flag > 0` in the relevant filter.

---

## How `scoring_logic` Affects Interpretation

| Strategy | Score format | "Top engagement" means | Best for |
|----------|--------------|------------------------|----------|
| `percentile` | Continuous 0-1 | Score ≥ `0.75` (top quartile by percentile rank) | Smooth distribution, granular targeting |
| `quartile` | Discrete `1`-`4` | `metric_value = '4'` | Marketers who want simple "top quartile only" segments |
| `minmax` | Continuous 0-1 (Hivemall scaled) | Score ≥ `0.75` | Heavily skewed activity distributions where a few power users dominate |

When summarizing distributions, ALWAYS check which `scoring_logic` was used (from `nba_dash_model_metrics`) before interpreting `metric_value` — `'4'` in quartile mode is the top engagement bucket; `'4'` in percentile mode would be a parsing error.

---

## How Run Config Drives What You See

The `nba_dash_model_metrics` table snapshots every config knob used for a given run. The most consequential ones for interpreting the dashboard:

| Config knob | What changes if you tune it |
|-------------|----------------------------|
| `scoring_logic` | Whole shape of distribution changes (continuous vs bucketed) |
| `time_filter_type` + `lookback_period` / date range | Which events feed the score — shorter window → fresher but noisier |
| `event_lookback_days` | Cart-abandon flag rate (longer = higher rate) |
| `new_customers_days` | New-visitor flag rate (longer window = higher rate) |
| `ad_engagement_logic` | What channels disqualify a profile from being "new" |
| `abandon_regexp` | Which events count as add-to-cart for cart-abandon |
| `topk_values` | How many distinct channels keep their name vs collapse to `'others'` |

**Practical rule:** When the user notices a metric changed run-over-run, ALWAYS pull the corresponding config column from both runs before attributing the change to real audience behavior. Most "weird" run-to-run changes are config changes.

---

## What This Workflow Does NOT Do

Be explicit when the user asks something the dashboard tables can't answer:

- **No revenue forecasting** — `total_spend` exists in `nba_dash_source_tables`, but it's a description of source-data volume, not a predicted ROI. Never project ROI from NBA scores.
- **No multi-touch attribution** — NBA scores measure per-profile affinity, not channel contribution to conversions. For attribution, route to MTA.
- **No per-event detail** — the dashboard tables are aggregated. To see individual events, query the source tables directly.
- **No real-time scoring** — scores come from the most recent batch run. `nba_combined_metrics_final` is only as fresh as the last `nba_eng_launch.dig` execution.
- **No causal inference** — high engagement on a channel doesn't mean engagement was caused by that channel. Profiles get a "Next Best Channel: social" tag because they engage most there, not because social drives them to convert.

If a question requires any of the above, say what the table can show vs what's actually being asked, and recommend the alternative skill or analysis path.
