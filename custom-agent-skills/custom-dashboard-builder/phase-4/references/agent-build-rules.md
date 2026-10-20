# Phase 4 Reference — Dashboard Agent Build Rules

Rules for the `generate-data.js` and `dashboard.template.html` that go into the dashboard agent (copied from the approved Phase 3 master copies in `agent_outputs/<project_slug>/dashboards/`). Check them before the build (Phase 4 Step 1) — they are what makes the agent's one-command refresh reliable. The same rules apply when the installed agent adds a metric.

## One-command refresh, no questions

The agent must refresh the dashboard with one command and never ask for configuration:

- Database names, table names, queries, date logic and the template path are **hardcoded** in `generate-data.js` (databases also accepted as `SOURCE_DB` / `SINK_DB`, with the confirmed values as defaults).
- No `TODO`, `your_database`, `<placeholder>` or "edit this value" left in `generate-data.js`, the template or the agent's `SKILL.md`.
- Output and template paths come from `DASHBOARD_OUTPUT` / `DASHBOARD_TEMPLATE` (the agent sets them) — never written into the skill folder.

### Inline-Only Policy: No External Data Files

**Dashboards are self-contained.** All data is inlined directly into `dashboard.html`:

**What this means:**
- ✅ Single `dashboard.html` file with embedded data
- ✅ No separate `data.json` dependency
- ✅ Total file size < 2 MB (enforced by Phase 3 hard stop)
- ✅ Works offline, no fetch() calls needed

**If you see references to `data-caching-strategy.md` or external JSON:**
These are deprecated — all dashboards use inline embedding, and the shipped `generate-data.js` enforces it.

**Checklist:**
- [ ] `generate-data.js` inlines data directly (no `data.json` file written)
- [ ] Total `dashboard.html` size < 2 MB
- [ ] If > 2 MB: `generate-data.js` exits with error message, directing you to optimize queries
- [ ] All queries optimized (pre-aggregate, narrow time window, drop unused columns)
- [ ] Template reads inline `RAW` variable (no `fetch()` needed)

---

**FIRST STEP — Column Name Audit (2 minutes, prevents 2+ hours debugging):**

```bash
tdx show tables --in <database>
tdx describe <db>.<table>
tdx query -d <db> "SELECT <column_name> FROM <table> LIMIT 1"
```

**Common mistakes this catches:**
- Template expects `customer_count` → table has `total_customers` or `num_customers`
- Template expects `total_revenue` → table has `service_revenue` or `revenue_amount`
- Query references a column that doesn't exist (returns an error)

**Checklist:**
- [ ] Run `tdx describe <table>` and copy exact column names
- [ ] Cross-check against `project_state.md` metrics list
- [ ] Sample each column: `SELECT <col> FROM <table> LIMIT 1`

---

**Snapshot Table Date Column Check (1 minute, prevents silent wrong results):**

Some tables are **snapshots** — they hold the latest state of each entity and have **no date column**. A `WHERE date BETWEEN ...` filter on such a table either errors or silently returns zero rows.

```bash
tdx describe <db>.<table>
# Look for: date, created_at, time, event_date, transaction_date, etc.
```

| Table type | Has date column? | Action |
|---|---|---|
| Fact / transactional table | Yes | Safe to add a date filter |
| Snapshot / reference table | No | **Omit the date filter entirely** |
| Snapshot with `td_client_time` | Only a system column | Omit date filter — `td_client_time` is ingestion time, not business date |

```sql
-- ❌ WRONG: a geography snapshot table has no date column
SELECT region, state FROM sink_geography
WHERE date >= '2024-01-01' AND date <= '2024-12-31';   -- error or 0 rows

-- ✅ CORRECT: no filter needed
SELECT region, state FROM sink_geography;
```

**Checklist:**
- [ ] For every table, run `tdx describe` and confirm a date column exists before writing a date `WHERE` clause
- [ ] Snapshot tables: omit the date filter, note "snapshot — no date filter" as a comment

---

**`tdx query` Row Limit (non-negotiable — prevents silent data truncation):**

By default, `tdx query` silently truncates display output to ~40 rows. Without an explicit limit, `generate-data.js` may build the dashboard on partial data with no error or warning.

```bash
# ❌ WRONG: silently returns ~40 rows even if the table has 5,000+
tdx query -d <db> "SELECT * FROM sink_sales" --format json

# ✅ CORRECT: explicit safe limit
tdx query -d <db> "SELECT * FROM sink_sales" --format json --limit 10000
```

Guidance: small dimension/snapshot tables → `--limit 1000`; fact/transaction tables → `--limit 50000`; default when unsure → `--limit 10000`.

**Checklist:**
- [ ] Every `tdx query` call includes `--limit <N>`
- [ ] Every `executeQuery()` call in `generate-data.js` includes an explicit limit
- [ ] Row count spot-checked against `SELECT COUNT(*) FROM <table>`

---

**CLI Output JSON Parsing (prevents wrong parse):**

`tdx` prepends status lines before the JSON array:
```
- Executing query...
✔ Query completed: [Job ID: 3173...]
[{"col": "val"}, ...]
```

`raw.find('[')` matches `[Job ID: 3173...]`, not the real array. Use a regex instead:

```javascript
// ❌ WRONG
const jsonStr = raw.slice(raw.indexOf('['));

// ✅ CORRECT
const match = raw.match(/\[\s*\{/);
const jsonStr = match ? raw.slice(match.index) : '[]';
```

**Checklist:**
- [ ] All `tdx` output parsing in `generate-data.js` uses `\[\s*\{` — not `indexOf('[')` or `.find('[')`

---

**KPI Query Grain Design (prevents over-aggregated / mismatched totals):**

| Pattern | Grain | When to use |
|---|---|---|
| **Pre-aggregated KPI** | Single row (e.g. `total_orders: 648`) | Static KPI cards — no client-side filtering |
| **Full dimensional** | Row per `date × channel × category × segment` | Client-side JS filtering — the JS aggregates |

If the dashboard has client-side filter dropdowns, the query must fetch the full dimensional grain, not a collapsed total.

```sql
-- ❌ WRONG for client-side filtering: returns 1 aggregated row
SELECT COUNT(*) AS total_orders, SUM(revenue) AS total_revenue
FROM sink_sales WHERE date BETWEEN ... AND ...;

-- ✅ CORRECT: full grain, JS filters client-side by any combination
SELECT order_date, channel, category, customer_segment,
       COUNT(*) AS orders, SUM(revenue) AS revenue
FROM sink_sales
GROUP BY order_date, channel, category, customer_segment;
```

**Checklist:**
- [ ] For each query: does the dashboard filter client-side (JS) or server-side (new query per filter)?
- [ ] Client-side filtered charts: queries return the full dimensional grain
- [ ] Pre-aggregated KPI cards with no filter: single-row aggregation is fine

---

**Table Grain Assessment (1 minute, impacts payload size):**

```javascript
// Table metadata (comment at top of generate-data.js)
// Table built at: customer_id, vehicle_model, region, service_type, fuel_type (5 dims)
// Dashboard filters on: customer_id, vehicle_model, region, service_type (4 dims)
// Action: GROUP BY only the 4 filter dimensions to avoid row fan-out

// ❌ WRONG: returns full table grain (6,619 rows, 1.4 MB payload)
SELECT * FROM fact_customer_overview;

// ✅ CORRECT: aggregate on filter dimensions only (2,240 rows, 600 KB)
SELECT customer_id, vehicle_model, region, service_type,
       SUM(revenue), AVG(rating), COUNT(*)
FROM fact_customer_overview
GROUP BY customer_id, vehicle_model, region, service_type;
```

**Checklist:**
- [ ] Identify all table dimensions vs. dashboard filter dimensions
- [ ] If the table has extra dimensions, GROUP BY only the ones the dashboard filters on

---

**Column Selection Audit (2 minutes, impacts payload size):**

```javascript
// Template usage map (document in generate-data.js)
// Template reads: customer_id, vehicle_model, total_revenue, avg_rating
// ✅ INCLUDE only these
// ❌ EXCLUDE unused columns: fuel_type, vehicle_type, tickets_resolved, status
```

**Checklist:**
- [ ] Scan `dashboard.html` for every data key it references
- [ ] `generate-data.js` fetches only those columns
- [ ] Remove "might be useful later" columns

---

**Parallel Queries (non-negotiable):**

`generate-data.js` must use `Promise.all()` for all queries:

```javascript
// ❌ WRONG: sequential (~5 seconds)
const metric1 = await executeQuery('SELECT SUM(revenue) FROM fact');
const metric2 = await executeQuery('SELECT COUNT(*) FROM fact');

// ✅ CORRECT: parallel (~1 second)
const [metric1, metric2] = await Promise.all([
  executeQuery('SELECT SUM(revenue) FROM fact'),
  executeQuery('SELECT COUNT(*) FROM fact'),
]);
```

---

**Performance floor (1 minute, prevents wasted optimization):**

- `tdx query` execution → ~0.5 second floor per query
- Browser rendering (HTML Client) → ~0.5 second floor

**Rule:** once total query time approaches ~0.5-1s, stop optimizing SQL — rendering cost dominates from there.

**Checklist:**
- [ ] Measure total query time with all queries in parallel
- [ ] If total < 0.5s: optimization is complete
- [ ] If total > 2s: re-check grain, column selection, and parallelization
