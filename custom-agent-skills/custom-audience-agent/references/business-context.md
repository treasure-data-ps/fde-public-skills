<!--
PURPOSE OF THIS FILE
Customer business context the audience agent loads at the start of every session. It turns
raw parent-segment columns into business meaning: what the customer sells, what their terms
mean, which attributes matter, how segments are named, and what must never be surfaced.
Column-level schema facts (types, null ratios, table grain) belong in data-dictionary.md.

HOW TO USE
This is a generic template — never fill it in place. Setup mode (SKILL.md) copies it to
  agent_outputs/<customer_slug>/custom-audience-agent/business-context.md
and drafts each section from parent-segment exploration. The customer reviews the draft via
requirements.md; their answers are then distilled back into the copy.

AUTHORING RULES (for the filled copy)
- Reader is the agent, not the customer: terse, imperative, concrete.
  "Treat empty string as not enrolled", "Never output raw `email` values".
- Real column names in backticks, real enum values, aggregate stats only where useful.
- While a section is a draft, mark it [INFERRED — please confirm] or [NEEDS YOUR INPUT].
  Remove the markers once the customer has confirmed; drop sections left unanswered rather
  than guessing.
- Never paste raw customer records — column names, value lists and aggregates only.
- Keep each section to a few lines; this file is read on every session.
-->

# <Customer Name> — Business Context

## Business Model
<!-- 1–3 sentences: what is sold, main sales channels, key customer types, with the
channel/category column values the agent should map to.
Example: "Multi-category retailer. Categories (`category` values): Clothing, Home, Food.
Sales channels (`preferred_channel`): Online, In-Store, Mobile. Online is largest (~49%)." -->

## Business KPIs
<!-- 3–6 metrics that matter most, each tied to a column or calculation.
- LTV: `customers.<ltv_column>`, mean ~<value>
- Repeat purchase rate: customers with ≥2 rows in `behavior_<orders>` in the last 12 months
- Email engagement: opens / sends per campaign in `behavior_<email_events>` -->

## Key Terms
<!-- Customer jargon mapped to exact conditions.
- "VIP" → `<segment_column> = 'VIP'`. Distinct from `<loyalty_column>`.
- "Churned" → no row in `behavior_<transactions>` in the last <N> days.
- "New" → [NEEDS YOUR INPUT] cutoff (first 30 or 90 days?) -->

## Priority Attributes
<!-- 5–10 columns the agent should weight most, with values and gotchas.
- `<column>` (<type>) — <meaning>. Values: `<a>`, `<b>`, `<c>`.
- `<date_column>` (varchar) — stored as text. Use `TD_TIME_PARSE` before time arithmetic.
- `<tier_column>` — empty string = not enrolled, not missing data. -->

## Segment Naming Conventions
<!-- Prefixes/suffixes/folders the customer uses, from existing segment names.
If none: "Use descriptive Title Case names, e.g. 'VIP Customers - No Purchase 90 Days'." -->

## Exclusion Rules
<!-- Hard constraints — the agent treats these as non-negotiable.
- Never surface raw values of: `<email>`, `<first_name>`, `<last_name>`, `<phone>`. Counts or aggregates only.
- Exclude `<unsubscribe condition>` from any email-activation segment.
- Exclude test accounts: `<condition>`.
- Behavior tables out of scope: `<table>` (reason). -->

## Target Users & Tone
<!-- Who uses the agent (marketing, analytics, CS, executives) and any tone override.
Default: "Neutral, professional marketing analyst — concise, data-grounded." -->

## Output Preferences
<!-- Default output format and chart preferences.
Default: "Mixed — one-sentence summary first, table for top-N lists, chart for
distributions and trends. Brand palette: <hex list or 'none'>." -->

## SQL Templates (optional)
<!-- Recurring query patterns the customer wants reused. One block per template.
Use real table/column names; no LIMIT; no hard-coded dates.

### <template_name>
**Use when:** <one-line description of the question it answers>
```sql
SELECT ...
FROM customers c
JOIN behavior_<table> b ON c.cdp_customer_id = b.cdp_customer_id
WHERE TD_INTERVAL(b.<event_time_column>, '-90d')
```
Delete this section if the customer has no templates. -->
