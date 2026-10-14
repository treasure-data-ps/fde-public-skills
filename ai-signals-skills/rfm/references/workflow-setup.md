# RFM Customer Segmentation — Workflow Setup

Use with `../../shared/push_pattern_td_workflows.md` (copy, gates, push, run). Two other files are the source of truth — read both in the working copy before editing anything:

- `<workdir>/README.md` — workflow structure, what every parameter does and how to choose it, outputs, customization points
- `<workdir>/config/input_params.yml` — exact parameter names, nesting and syntax (edit this file in place; keep every key)

`<workdir>` = `agent_outputs/<customer_slug>/rfm/workflow`. This file adds only what the template can't: how to pick values from the customer's data, RFM deploy details, and the output checks.

---

## 1. Map Phase 1 tables to sources

Each confirmed activity table becomes one entry in `aggregate_metrics_tables`. Replace the template's example entries; remove the ones the customer doesn't have. Every source adds to Recency and Frequency; only sources with a real `order_amount` add to Monetary.

| Source type | Adds to | `order_amount` | `context_col` | Must-have filter |
|---|---|---|---|---|
| Web / pageviews | R, F | `0.0` | Page title or path | Bots / internal traffic if present |
| Email events | R, F | `0.0` | Campaign name | Keep engagement only (open, click, reply, conversion, form); exclude send, delivered, bounce, spam |
| CRM / sales / support | R, F | `0.0` | Topic or type | Exclude internal / test records |
| Orders / purchases / services | R, F, **M** | Revenue column | Item or product name | Only valid statuses — exclude cancelled, returned, refunded |
| Other one-to-many activity (app, store, loyalty, reviews) | R, F | `0.0` (or revenue if it carries a value) | Best categorical column | Non-null profile ID |

Rules:
- **Event time:** TD's `time` column is often the load time. Use the real event column when there is one (`TD_TIME_PARSE(<col>)` if it is a string) — Recency is computed from `unixtime_col`. Check: `SELECT MIN(time), MAX(time)` vs. the event column; if `time` spans a few days but the events span months, use the event column.
- **Profile ID:** every source must carry the ID the Parent Segment joins on. Set each source's `join_key` to its own column name; `globals.canonical_id` is the name the output uses.
- **Frequency counts rows.** A table with one row per order line counts every line as a touchpoint, and a page-load table counts every page. Accept it (say so in the docs) or set `query_type: custom` and aggregate in `sql/union_src_tables/<name>.sql`.
- **No monetary source:** if the customer has no order or revenue data, set `order_amount: 0.0` everywhere and tell the user `m_quartile` and the M-driven segments will not be meaningful.
- **Quotes:** string literals inside `custom_filter` use doubled single quotes, as in the template.

### Discovery queries

Run with `tdx query` against the source database. Replace `<id>`, `<status_col>` etc. with the real column names from `tdx describe`.

Profile ID coverage per source (NULL IDs are dropped from scoring):

```sql
SELECT COUNT(*) AS total_rows, COUNT(<id>) AS rows_with_id, APPROX_DISTINCT(<id>) AS profiles
FROM <source_database>.<table>
```

Event types and statuses (email, CRM, orders) — decide the `custom_filter`:

```sql
SELECT <event_type_or_status_col>, COUNT(*) AS n
FROM <source_database>.<table>
GROUP BY 1 ORDER BY 2 DESC
```

Order value column — decide `order_amount`:

```sql
SELECT COUNT(*) AS orders, COUNT_IF(<amount_col> > 0) AS with_value,
       ROUND(AVG(<amount_col>), 2) AS avg_value, MAX(<amount_col>) AS max_value
FROM <source_database>.<orders_table>
```

Data date range (decides the time filter — §2):

```sql
SELECT TD_TIME_FORMAT(MIN(<event_time>), 'yyyy-MM-dd') AS first_event,
       TD_TIME_FORMAT(MAX(<event_time>), 'yyyy-MM-dd') AS last_event
FROM <source_database>.<table>
```

Record the column names and findings in `project_state.md` (Phase 1) — they are needed again in Phase 4.

## 2. Choose the other values

| Decision | Rule |
|---|---|
| Scoring model | `globals.model_type: ai_signals` (default). Switch to `custom` if the AI Signals batch API is not available to the account or the `td.apikey` secret cannot be set; record the choice in `project_state.md` |
| Time filter | First setup: all history (`apply_time_filter: 'no'` everywhere) unless the requirements ask for a window. Rolling window → `interval` with a `lookback_period` long enough to see repeat purchases (6–24 months). Data that ends before today (demo, backfill, paused feed) → `range` covering the data, because `interval` counts back from the run time. Set `apply_time_filter` the same on every source and on the top-level label |
| Recency on stale data | Recency is days since the last event, counted from the run time. On stale data every profile has a large recency, but quartiles are relative, so `r_quartile` still ranks profiles — say so in `project_state.md` and the docs |
| `context_col` | Every source needs one; pick the most useful categorical column (title, item, campaign, topic). Never leave it blank |
| `num_bins` | Keep `10`. It only changes the dashboard histograms — tell the user it does not change the 1–4 scores |
| Failure email | Uncomment the `_error` block in `rfm_launch.dig` and set the address from the requirements, or leave it commented if none is given. Put the customer name in `subject` |

**Minimal push (Phase 3, before requirements come back):** real sources, IDs, timestamps, order amounts, context columns and filters from Phase 1; the time filter per the rule above; `model_type` per the rule above; template values for everything else; schedule and failure email left commented. Note every assumed value in `project_state.md` as "default — confirm in requirements".

## 3. Deploy details

| Item | Value |
|---|---|
| Default project name | `rfm_ais` (from `tdx.json`) |
| Entry point | `rfm_launch` |
| Secrets | `td.apikey` when `model_type: ai_signals` — the user sets it before the first run: `! tdx wf secrets set <project> td.apikey=<master API key>`. Never ask for or handle the key yourself. None for `custom` |
| Schedule | Commented out in `rfm_launch.dig`. Ask whether the customer wants scheduled runs; leave it commented for a test account |
| Sink database | Created by the first step of `rfm_launch.dig` (`+create_sink_database`, `td_ddl>`) if missing. Keep that step and the `td: database:` export above it — `td_ddl>` in the launch file fails with "Parameter 'database' is required" without it. If the project owner can't create databases, the user creates it in the TD Console before the first run |

Push and run with the shared pattern (`tdx wf push -y` from `<workdir>`, `tdx wf run rfm_ais.rfm_launch` after asking).

## 4. Validate

Run after every run (Phase 3 and Phase 4). Replace `<db>` with `globals.sink_database`, `<id>` with `globals.canonical_id`, `<out>` with `output_table`, `<in>` with `input_table`, `<union>` with `union_activity_table`. Record the results in `project_state.md`.

**1. Output table populated, one row per profile, matches the input**

```sql
SELECT (SELECT COUNT(*) FROM <db>.<out>) AS out_rows,
       (SELECT COUNT(DISTINCT <id>) FROM <db>.<out>) AS out_profiles,
       (SELECT COUNT(DISTINCT <id>) FROM <db>.<in>) AS in_profiles
```
Pass: `out_rows = out_profiles = in_profiles > 0`. `out_rows` a multiple of `in_profiles` means scores were appended to an old table — check the scoring step. Compare `out_profiles` with the Parent Segment size: a large gap means ID mismatches or over-tight filters.

**2. Scores and segments are populated and spread**

```sql
SELECT COUNT(*) AS total, COUNT(r_quartile) AS has_r, COUNT(f_quartile) AS has_f,
       COUNT(m_quartile) AS has_m, COUNT(rfm_segment) AS has_segment
FROM <db>.<out>;

SELECT r_quartile, f_quartile, m_quartile, COUNT(*) AS n
FROM <db>.<out> GROUP BY 1, 2, 3 ORDER BY n DESC LIMIT 20;
```
Pass: all score columns non-null on every row; each quartile 1–4 appears for R and F. A single dominant `m_quartile` usually means no monetary source (§1) — expected only if the customer has no order data. Many ties on frequency (e.g. most profiles with 1 touchpoint) push profiles into few quartiles — report it.

**3. Segment mix is plausible**

```sql
SELECT rfm_segment, segment_size, population_percent
FROM <db>.<stats_table> ORDER BY segment_size DESC
```
Pass: several segments appear; the `ALL` row's `segment_size` equals `out_profiles`; no single segment holds almost everyone.

**4. Every source contributed**

```sql
SELECT source, COUNT(*) AS profiles, SUM(total_touchpoints) AS touchpoints,
       ROUND(SUM(total_spend), 2) AS spend, MIN(recency_days) AS min_recency, MAX(recency_days) AS max_recency
FROM <db>.<union> GROUP BY 1 ORDER BY 2 DESC
```
Pass: one row per configured source with `profiles > 0`; `spend > 0` only on monetary sources; recency values are non-negative and plausible for the data range.

**5. Dashboard tables have this run**

```sql
SELECT session_id, COUNT(*) AS sources, MAX(model_type) AS model_type
FROM <db>.<stats_table>_model_params GROUP BY 1 ORDER BY 1 DESC LIMIT 3;

SELECT COUNT(*) AS histogram_rows FROM <db>.<stats_table>_histogram;
```
Pass: the latest session has one `_model_params` row per configured source and the configured `model_type`; the histogram table has rows.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Table not found` / `Column not found` in the union step | Wrong `src_table`, column name or blank `context_col` | `tdx describe` the source; fix the entry |
| Scoring step fails with 401/403 | `td.apikey` secret missing or wrong (`ai_signals`) | User sets the secret (§3) and re-runs; or switch to `custom` |
| `<out>` empty | Run failed before or during scoring | `tdx wf attempt <id> tasks`, then `logs +<failed task>` |
| A source missing from `<union>` | 0 rows after `custom_filter` + time filter | Run the source's filter as a `COUNT(*)`; widen the window or filter |
| `m_quartile` the same for almost everyone | No monetary source, or `order_amount: 0.0` on the order source | Set the revenue column on the order source |
| Output much smaller than the Parent Segment | Different ID across sources or NULL IDs | Check `join_key` per source and NULL rates |
| Trino memory error | Window too long for the data volume | Shorten `lookback_period` (or the `range`) and re-run |
