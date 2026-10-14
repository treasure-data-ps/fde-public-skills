<!--
PURPOSE OF THIS FILE
Schema facts for the customer's parent segment, so the agent can pick the right table,
column and time field without re-exploring every session. Business meaning and rules belong
in business-context.md; this file is about structure and data quality.

HOW TO USE
This is a generic template — never fill it in place. Setup mode (SKILL.md) copies it to
  agent_outputs/<customer_slug>/custom-audience-agent/data-dictionary.md
and fills it from:
  tdx ps desc "<Parent Segment>" -o agent_outputs/<customer_slug>/custom-audience-agent/schema.json
  null-ratio and distinct-value queries (tdx query -d <output_database> "...")
  tdx sg list -r --parent-segment "<Parent Segment>" --max-depth 3
Refresh it when the parent segment gains or loses attributes/behaviors.

AUTHORING RULES (for the filled copy)
- One row per column. Include every customers column; for wide behavior tables list the
  key columns and note "other columns: see schema.json".
- Null % from: SELECT 1.0 - COUNT(col)*1.0/COUNT(*) FROM customers
- Values: up to ~8 distinct values for low-cardinality columns; range/mean for numerics.
- Flag gotchas in Notes: varchar dates, empty strings, arrays, PII, constant columns.
- Never paste raw customer records.
-->

# <Customer Name> — Data Dictionary

## Parent Segment
| Field | Value |
|---|---|
| Parent segment | `<Parent Segment Name>` (ID `<parent_id>`) |
| Output database | `cdp_audience_<parent_id>` |
| Profiles | <count> |
| Join key | `cdp_customer_id` (present in `customers` and every `behavior_*` table) |
| Schema snapshot | `schema.json` (same folder), taken <YYYY-MM-DD> |

## Attributes — `customers` (one row per profile)
| Column | Type | Null % | Values / range | Notes |
|---|---|---|---|---|
| `cdp_customer_id` | varchar | 0% | — | Join key |
| `<column>` | <type> | <n>% | `<a>`, `<b>`, `<c>` | <gotcha, e.g. "empty string = not enrolled"> |
| `<date_column>` | varchar | <n>% | `YYYY-MM-DD` | Text date — use `TD_TIME_PARSE` |
| `<array_column>` | array(varchar) | <n>% | — | Use `CROSS JOIN UNNEST`; never `ARRAY_CONTAINS` |
| `<email>` | varchar | <n>% | — | PII — never output raw values |

## Behaviors — `behavior_<name>` (one row per event)
<!-- One subsection per behavior table. -->

### `behavior_<name>`
- **Grain:** one row per <event / order / ticket>
- **Event time column:** `<column>` (unix seconds | varchar). <!-- Check this: the TD `time`
  column is often the load time, identical on every row — confirm before using it. -->
- **Rows / date range:** <count>, <min date> – <max date>

| Column | Type | Values / range | Notes |
|---|---|---|---|
| `<column>` | <type> | `<a>`, `<b>` | <note> |

## Existing Segments
<!-- From tdx sg list -r. Folder → segments (size). Used for reuse via include/exclude. -->
- `<Folder>/` — `<Segment>` (<size>), `<Segment>` (<size>)
- (top level) — `<Segment>` (<size>)

## Data Quality Notes
<!-- Anything that changes how queries must be written.
- `<column>` is <n>% null — exclude nulls from aggregations; >70% null: avoid.
- `time` in behavior tables is load time; use `<event_time_column>` for recency.
- Data ends <date> — "last 3 months" means relative to that, not today. -->
