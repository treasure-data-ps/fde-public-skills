---
name: phase-3-steps
description: All Phase 3 steps in a single linear file — queries, structure, data connection, error handling, rendering, validation, filter testing, performance, feedback, documentation, mobile, load UX, approval
metadata:
  type: project
---

# Phase 3: All Steps (4b → Phase Exit)

**Quick jump:**
| Step | Topic | Conditional? |
|------|-------|-------------|
| [4b-pre](#step-4b-pre-verify-sink--source-table-columns--mandatory-gate) | ⛔ SINK/source column verification | — |
| [4b](#step-4b-generate-dashboard-query-scaffolding) | Generate query scaffolding | — |
| [4c](#step-4c-build-dashboard-structure) | Build dashboard structure + tooltips | — |
| [4d](#step-4d-write-generate-datajs-connect-data) | Write generate-data.js, connect data | — |
| [4d-Final](#step-4d-final-error-handling-setup) | Error handling & edge cases | — |
| [4e](#step-4e-render-dashboard) | Render dashboard | — |
| [4f](#step-4f-validate-data-accuracy) | ⛔ Validate data accuracy (CRITICAL gate) | — |
| [4g](#step-4g-test-filter-interactions) | Test filter interactions | — |
| [4h](#step-4h-performance-check) | Performance check | — |
| [4i](#step-4i-get-user-feedback) | Get user feedback + approval loop | — |
| [4j](#step-4j-document-dashboard-parameters) | Document dashboard parameters | — |
| [4k](#step-4k-test-mobile--responsive-design) | Mobile & responsive design testing | ⚠️ Only if Phase 1 required mobile |
| [4l](#step-4l-initial-load-performance--ux) | Initial load performance & UX | ⚠️ Only if Step 4h found slow queries |

**Note:** Step 4a (confirm rendering engine) from the original build loop is a no-op in this lite skill — the rendering engine is always HTML Client, nothing to confirm. Numbering keeps the 4b start to avoid renumbering every cross-reference in this skill.

**Resume gate:** If resuming mid-Phase 3, read `state.md` to find the last completed step, then jump directly to the next step. Do not restart from 4b.

---

## Step 4b-pre: Verify SINK / Source Table Columns ⛔ MANDATORY GATE (3-5 min)

**What to do — before writing a single query:**
- Confirm every table the dashboard will query actually exists
- Confirm exact column names for every metric and dimension
- Wrong column names cause blank charts and NaN KPIs — catching this now saves 2–4 hours

**Workflow path (SINK tables, if Phase 2 was run):**
```bash
# 1. List SINK tables
tdx show tables --in <sink_database>

# 2. For EACH table you plan to query, get column names
tdx describe <sink_db>.<sink_table>
# e.g.: tdx describe automotive_sink.automotive_fact_service

# 3. Spot-check one row to confirm column names resolve
tdx --json query -d <sink_db> "SELECT * FROM <sink_table> LIMIT 1" 2>/dev/null
```

**Non-Workflow path (source tables, if Phase 2 was skipped):**
```bash
tdx show tables --in <source_database>
tdx describe <source_db>.<fact_table>
tdx --json query -d <source_db> "SELECT * FROM <fact_table> LIMIT 1" 2>/dev/null
```

**Gate:** Cross-check every column name against Stage B's confirmed metric and dimension definitions (or Phase 2's SINK schema, if run). If any column is missing, loop back to Phase 2 (Workflow) or ask the user (Non-Workflow).

**Output:** Confirmed column name map — paste actuals into a comment at the top of your query file:
```
# Confirmed columns: service_count, total_service_revenue, avg_csat_score, customer_count
# Table: automotive_sink.automotive_fact_service
```

---

## Step 4b: Generate Dashboard Query Scaffolding (5-8 min)

**What to do:**
- Create templated SQL queries for all dashboard visualizations
- Parameterize for dynamic filters
- Test locally before rendering

### Query 1: Overall Metrics (No Grouping)
```sql
SELECT 
  {metric1_formula} as metric1_label,
  {metric2_formula} as metric2_label,
  MIN(data_date) as data_start,
  MAX(data_date) as data_end,
  MAX(data_date) as last_updated
FROM {fact_table}
WHERE {filters_from_stage_b} AND {exclusion_rules_from_stage_a}
```

> **Static dashboards:** `data_start` / `data_end` are mandatory — users must know what date range the data covers since there is no live filter to indicate freshness. Always surface both in the dashboard header (see Step 4c).

### Query 2: Metrics by Primary Dimension
```sql
SELECT 
  {dimension1_column} as dimension1,
  {metric1_formula} as metric1_label,
  COUNT(*) as row_count
FROM {fact_table}
WHERE {filters_from_stage_b} AND {exclusion_rules_from_stage_a}
GROUP BY {dimension1_column}
ORDER BY metric1_label DESC
LIMIT 1000
```

### Query 3: Metrics by Secondary Dimension (if requirements had 2+ dimensions)
```sql
SELECT 
  {dimension2_column} as dimension2,
  {metric1_formula} as metric1_label
FROM {fact_table}
WHERE {filters_from_stage_b} AND {exclusion_rules_from_stage_a}
GROUP BY {dimension2_column}
ORDER BY metric1_label DESC
```

### Query 4: Time Series (if requirements had date requirements)
```sql
SELECT 
  DATE({date_column}) as date,
  {metric1_formula} as metric1_label,
  COUNT(*) as row_count
FROM {fact_table}
WHERE {filters_from_stage_b} AND {exclusion_rules_from_stage_a}
GROUP BY DATE({date_column})
ORDER BY date ASC
```

### Query 5: Dimension Dropdown Options (for filter controls)
```sql
SELECT DISTINCT {dimension_column}
FROM {fact_table}
WHERE {dimension_column} IS NOT NULL AND {filters_from_stage_b}
ORDER BY {dimension_column}
LIMIT 5000
```

**Critical Rules:**
- **Non-Workflow:** Query source tables directly (fact/dimension)
- **Workflow:** Query SINK tables (NOT source tables — defeats pre-aggregation)
- Always include Stage B filters + Stage A exclusion rules
- Use table aliases (e.g., `c.region` not just `region`)
- Test queries BEFORE moving to Step 4c
- **⚠️ MANDATORY: Always add `--limit` flag to `tdx query` — defaults to 40 rows with no warning**
- **⚠️ MANDATORY: Always redirect stderr with `2>/dev/null` to prevent progress output corrupting JSON**
- **⚠️ MANDATORY: Use `tdx --json query` (global flag before subcommand) — `tdx query --json` or `-o json` do NOT work**

**Actions:**
1. Build Query 1 from Stage B's confirmed metrics
2. Build Query 2-3 from Stage B's confirmed dimensions
3. Build Query 4 (if requirements needed time series)
4. Build Query 5 for each dimension (filter dropdowns)
5. **Column names already verified in Step 4b-pre — use confirmed names, never guess**
6. Test each query:
   ```bash
   tdx --json query -d <database> "<SQL>" --limit 5000 2>/dev/null > /tmp/file.json
   ```
7. Verify results match Stage B / Phase 2 sample values

**Output:** 5 production-ready SQL query templates + column names verified

---

## Step 4c: Build Dashboard Structure (5-10 min)

**What to do:**
- Create the HTML Client dashboard skeleton with all UI components
- Write tooltip definitions for every widget before wiring data
- No data yet — just structure

**Static dashboard rule:** Every dashboard must include a **Data Range banner** in the header — showing `data_start` → `data_end` and `last_updated`. This is the only way users know what period the data covers since there is no live "as of" indicator otherwise.

**Widget tooltip rule:** Every KPI card and chart must include a small `ⓘ` icon that users can hover to see a plain-English definition of the metric and how it is calculated. Keep it to 1-2 sentences max per widget.

**Tooltip content structure (write for every widget before Step 4d):**

| Widget | definition | calculation |
|--------|-----------|-------------|
| Churn Rate | % of customers who did not renew within the period | `churned_count / total_customers * 100` |
| Total Revenue | Sum of all completed transaction amounts | `SUM(amount) WHERE status != 'cancelled'` |
| Unique Customers | Count of distinct customer IDs with at least one event | `APPROX_DISTINCT(customer_id)` |

**HTML Client structure:**
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    .info-tooltip-wrapper { position: relative; display: inline-block; margin-left: 4px; cursor: default; }
    .info-icon { font-size: 12px; color: #888; font-style: normal; }
    .tooltip-box {
      display: none; position: absolute; bottom: 125%; left: 50%; transform: translateX(-50%);
      background: #333; color: #fff; padding: 6px 10px; border-radius: 4px;
      font-size: 12px; max-width: 260px; white-space: normal; z-index: 100;
    }
    .info-tooltip-wrapper:hover .tooltip-box { display: block; }
  </style>
</head>
<body>
  <div class="dashboard">
    <h1>Dashboard Title</h1>
    <div class="data-range-banner"><!-- populated by JS from data_start/data_end --></div>
    <div class="kpis">
      <div class="kpi-card">
        <h3>Total Customers
          <span class="info-tooltip-wrapper">
            <i class="info-icon">ⓘ</i>
            <div class="tooltip-box">Count of distinct customers active in the period. Calculated as APPROX_DISTINCT(customer_id) excluding test accounts.</div>
          </span>
        </h3>
        <span id="total-customers">–</span>
      </div>
    </div>
    <div class="charts">
      <h3>Revenue by Region
        <span class="info-tooltip-wrapper">
          <i class="info-icon">ⓘ</i>
          <div class="tooltip-box">SUM(amount) for completed transactions grouped by region. Excludes cancelled and test orders.</div>
        </span>
      </h3>
      <!-- chart -->
    </div>
  </div>
</body>
</html>
```

**Actions:**
1. Copy the base template from `references/rendering/html-client/templates/` (kpi / table / multi-chart) matching the requirements' layout
2. **Write tooltip text for every widget** (definition + calculation) — do this now, before Step 4d
3. Define all dashboard sections (filters, KPI cards, charts, tables)
4. Add data range banner
5. Add placeholder markup (`<!-- DATA_PLACEHOLDER -->`, replaced in Step 4d)
6. Style for readability

**Output:** Dashboard skeleton with tooltip definitions on every widget, data range banner in place

---

## Step 4d: Write generate-data.js, Connect Data (10-15 min)

**What to do:**
- Execute ALL queries against SINK/source tables via `generate-data.js`
- Embed results as JSON, inlined directly into `dashboard.html`
- Wire filter state in the page's JS to switch between pre-fetched data sets

> ⚠️ **Critical rule: data is NEVER typed directly into `dashboard.html` or `dashboard-template.html`.** `generate-data.js` is the only sanctioned source of data — it queries TD via `tdx --json query` and injects the results inline, replacing `<!-- DATA_PLACEHOLDER -->` in the template.

> ⚠️ **Filters must apply at the SQL WHERE clause — never client-side re-aggregation.**
> Post-filtering client-side requires loading the entire fact table into the browser.
> Instead: pre-query each filter combination in `generate-data.js`, embed results as separate JSON keys, switch on filter state in the page's plain JS.

**Step 1 — Execute queries per filter combination:**
```bash
tdx --json query -d <sink_db> "SELECT destination, SUM(total_bookings) as b, ROUND(SUM(total_revenue)/1000,1) as r
FROM travel_fact_bookings
WHERE loyalty_tier = 'Gold'
GROUP BY destination ORDER BY r DESC LIMIT 8" 2>/dev/null

# Also query "All" (no filter) as the default
tdx --json query -d <sink_db> "SELECT destination, SUM(total_bookings) as b, ROUND(SUM(total_revenue)/1000,1) as r
FROM travel_fact_bookings
GROUP BY destination ORDER BY r DESC LIMIT 8" 2>/dev/null
```

**Step 2 — `generate-data.js` compacts results into a single RAW object, keyed by filter value:**

```javascript
// generate-data.js
const { execSync } = require('child_process');
const fs = require('fs');

const SOURCE_DB = process.env.SOURCE_DB || '<source_db>';
const SINK_DB   = process.env.SINK_DB   || '<sink_db>';

function query(db, sql) {
  return JSON.parse(
    execSync(`tdx --json query -d "${db}" "${sql.replace(/"/g, '\\"')}" 2>/dev/null`,
             { encoding: 'utf8' })
  );
}

async function main() {
  const overview   = query(SINK_DB, 'SELECT metric_name, metric_value FROM <fact_table> LIMIT 100');
  const by_segment = query(SINK_DB, 'SELECT segment, COUNT(*) AS count FROM <fact_table> GROUP BY segment ORDER BY count DESC');

  // One key per filter value — "All" (no filter) is always required as the default
  const dest_by_loyalty_tier = {
    All:  query(SINK_DB, 'SELECT destination, SUM(total_bookings) AS b, ROUND(SUM(total_revenue)/1000,1) AS r FROM travel_fact_bookings GROUP BY destination ORDER BY r DESC LIMIT 8'),
    Gold: query(SINK_DB, "SELECT destination, SUM(total_bookings) AS b, ROUND(SUM(total_revenue)/1000,1) AS r FROM travel_fact_bookings WHERE loyalty_tier = 'Gold' GROUP BY destination ORDER BY r DESC LIMIT 8"),
  };

  const data = { overview, by_segment, dest_by_loyalty_tier };
  const dataBlock = `<script>var RAW = ${JSON.stringify(data)};<\/script>`;

  const template = fs.readFileSync('dashboard-template.html', 'utf8');
  const html = template.replace('<!-- DATA_PLACEHOLDER -->', dataBlock);
  fs.writeFileSync('dashboard.html', html);
  console.log(`✅ dashboard.html written (${Buffer.byteLength(html, 'utf8')} bytes)`);
}
main().catch(err => { console.error(err); process.exit(1); });
```

Run it:
```bash
SOURCE_DB=<source_db> SINK_DB=<sink_db> node generate-data.js
# ✅ dashboard.html written (142847 bytes)
```

**Step 3 — Switch on filter state in the page's plain JS (embedded in `dashboard-template.html`):**
```javascript
// ✅ CORRECT — all data pre-fetched by generate-data.js, embedded as RAW constants
function renderDestinations(filterValue) {
  const dests = RAW.dest_by_loyalty_tier[filterValue] || RAW.dest_by_loyalty_tier["All"];
  // ...update DOM/chart from dests
}

document.getElementById('loyalty-filter').addEventListener('change', (e) => {
  renderDestinations(e.target.value);
});

// ❌ WRONG — fetching at runtime requires a server; breaks the double-click-to-open promise
// fetch('/api/query?tier=Gold').then(...)
```

**Filter Implementation Rule:**
- Each selectable filter value = one pre-queried JSON key in `RAW`
- `"All"` = no-filter baseline query (always required)
- Filter dropdown `onchange` → look up the matching `RAW` key → re-render — no DB call at runtime
- Multi-select → pre-query the combinations you need, or pass an array of values to a `WHERE IN` clause when generating that key

**Data Freshness Display:**
- Extract `MAX(data_date)` from Query 1
- Display "Last updated: 2026-06-10 14:23:00"

### Payload size budget (Pattern A)

`generate-data.js` injects the full RAW payload inline into `dashboard.html` — this is what keeps the file a single portable artifact (double-click to open, email as an attachment, no server required). Use the tiered budget (see `html-dashboard-patterns.md` → "Data Size Budget & Optimization"): under 500KB is ideal, up to 2MB is acceptable, beyond 2MB requires action:

1. Pre-aggregate more in SQL (`GROUP BY` instead of row-level) to reduce row count.
2. Drop unused columns from the RAW payload.
3. If the dataset genuinely cannot fit under 2MB, flag this to the user as an exception. A server-hosted `data.json` pattern exists technically, but it breaks the "double-click and open" portability this skill promises — treat it as a last resort to raise with the user, not a routine choice to make silently.

### After running generate-data.js

```bash
# Validate output
node generate-data.js
# ✅ Check: non-empty JSON written
# ✅ Spot-check: one metric in RAW matches a manual tdx query result
# ✅ Open dashboard.html in browser (or preview_document) — charts show real numbers
```

**Output:** `dashboard.html` — fully self-contained, ready for validation in Step 4e

---

## Step 4d-Final: Error Handling Setup (3 min)

**What to do:**
- Ensure dashboard gracefully handles errors before rendering to user

**1. Query Timeout:**
```
If query > 30 seconds:
  → Display: "Query taking longer than expected. Try narrower date range."
  → Show cached/previous result as fallback
```

**2. Zero Results:**
```
If filter combination returns 0 rows:
  → Display: "No data found for selected filters."
  → Don't show broken charts or undefined values
```

**3. API/Database Errors:**
```
Network error → "Unable to connect to database. Please try again."
Invalid query → "Query error. Contact support with error code: [ID]"
Permission denied → "You don't have access to this data."
Always show user-friendly message, not raw SQL error
```

**4. Null/Missing Values:**
```
NULL dimensions → Exclude or show as "[Unknown]"
NULL metrics → Show as "–" or "0" (depending on context)
```

**5. Loading States:**
```
While the page's JS renders widgets from RAW → show a progress bar or brief loading state
Since data is inlined (no runtime fetch), this should resolve in well under a second
```

**Output:** Error handling configured, dashboard won't crash

---

## Step 4e: Render Dashboard (5-8 min)

**What to do:**
- Execute all queries against Treasure Data
- Transform results into dashboard format
- Render final dashboard with visual validation

**Actions:**

1. **Execute all queries in parallel** (Query 1-5) with timeout protection

2. **Transform query results:**
```json
{
  "metrics": {
    "total_customers": 12432,
    "churned_count": 1850,
    "churn_rate_pct": 14.87,
    "data_start": "2024-01-01",
    "data_end": "2026-06-10",
    "last_updated": "2026-06-10"
  },
  "by_region": [
    { "region": "North America", "total_customers": 6500, "churned_count": 1200 }
  ],
  "region_options": ["North America", "Europe", "APAC", "Australia"]
}
```

> `data_start` and `data_end` must always be present in the metrics payload. The data range banner reads from these fields.

3. **Render dashboard:** Generate `dashboard.html` via `generate-data.js` (Step 4d) and open it directly in a browser, or via `preview_document`.

4. **Visual design validation (CRITICAL):**
   - Colors correct? Typography readable? Layout consistent?
   - Charts render without errors? (no blank charts, misaligned axes?)
   - Dark mode works? (if requirements specified it)
   - **Data range banner present in header?** (`data_start` → `data_end` + `last_updated` visible)
   - **Every widget has an `ⓘ` tooltip?** Hover each one — definition and calculation must appear

5. **Verify functional requirements:**
   - "KPI cards at top" → Present?
   - "Charts for trending" → Visible?
   - "Drill-down by region" → Works?
   - "Mobile responsive" → Tested in Step 4k

6. **Headless validation via jsdom (optional but recommended):**

   **When to use:** If you can't open a real browser, or want deterministic validation before user review. This catches two classes of bugs: (1) missing `--limit` in queries (rows silently truncated); (2) cascading tab failures (one tab's error aborts the rest).

   **Setup (one-time):**
   ```bash
   # Create a temporary npm project with jsdom
   mkdir -p /tmp/dashboard-validate && cd /tmp/dashboard-validate
   npm init -y
   npm install jsdom
   ```

   **Validation script (save as `validate.js`):**
   ```javascript
   const fs = require('fs');
   const { JSDOM } = require('jsdom');

   // Read your generated dashboard.html
   const html = fs.readFileSync('/path/to/dashboard.html', 'utf8');
   
   // Parse with jsdom (headless browser simulation)
   const dom = new JSDOM(html);
   const window = dom.window;
   
   // Capture console errors (will show cascading failures)
   let errors = [];
   const originalError = window.console.error;
   window.console.error = function(...args) {
     errors.push(args.join(' '));
     originalError.apply(window.console, args);
   };

   // Execute the page's <script> tags
   dom.runVMScript(new (require('vm')).Script(html.match(/<script[^>]*>[\s\S]*?<\/script>/g)?.join('') || ''));

   // Check for errors
   if (errors.length > 0) {
     console.log('❌ ERRORS FOUND:');
     errors.forEach(e => console.log(`  - ${e}`));
     process.exit(1);
   } else {
     console.log('✅ No console errors detected');
   }

   // Verify KPI text rendered (basic check)
   const kpiCount = dom.window.document.querySelectorAll('[class*="kpi"]').length;
   console.log(`📊 Found ${kpiCount} KPI elements`);
   ```

   **Run validation:**
   ```bash
   node validate.js
   ```

   **Interpretation:**
   - ✅ `No console errors detected` → HTML and JS loaded correctly
   - ❌ `TypeError: Cannot read property 'innerHTML' of null` → Tab initialization failed (cascading failure — wrap tab IIFEs in try/catch)
   - ❌ `Cannot read property 'rows' of undefined` → Query result was undefined (usually missing `--limit` → truncated to 0 rows)
   - `HTMLCanvasElement.getContext('2d') is not implemented` → Expected (jsdom has no real Canvas backend); ignore unless blocking functionality

   **Caveat:** jsdom does NOT have a real Canvas backend, so Chart.js chart-creation will fail with "Not implemented". This is expected noise — only non-chart errors (missing data, cascading failures, NaN in KPI text) are meaningful signals.

**Output:** Visually validated interactive dashboard delivered to user

⛔ **DO NOT open the dashboard for the user, or ask for approval yet.**
Step 4f (data accuracy gate) and Step 4g (filter interaction test) MUST both pass first.
The rendered dashboard is for your validation only until both gates are complete.

---

## Step 4f: Validate Data Accuracy ⛔ CRITICAL GATE (5-10 min)

**What to do:**
- Cross-check dashboard values against Stage B / Phase 2 validation
- Ensure no data corruption or query mistakes
- STOP if discrepancies found

### 1. Compare KPI Totals
```
Dashboard shows: "Total Customers: 12,432"
Stage B's confirmed sample query result was: "COUNT(*) = 12,432" ✓

If mismatch:
  → Return to Step 4b (wrong WHERE clause or exclusion rule)
```

### 2. Compare Dimension Breakdown
```
Dashboard "By Region":
  - North America: 6,500
  - Europe: 3,200
  - APAC: 2,500
  - Australia: 232
  - Sum: 12,432 ✓ (matches total)

If sum ≠ total: Investigate NULL values, join issues, or missing filter
```

### 3. Spot-Check Drill-Down
```
Click "North America" in dashboard
Manually run: SELECT ... WHERE region = 'North America'
Dashboard shows: 1,200 churned
Query result shows: 1,200 churned ✓
```

### 4. Verify No Duplication or Loss — Including JOIN Fan-Out Check
```
If fewer rows: Aggregation working correctly ✓
If more rows: Investigate duplicate rows (join issue) ✗
```

**Mandatory for any SINK built with a JOIN:** Run these two counts before accepting results:
```sql
SELECT COUNT(*) FROM base_table b LEFT JOIN other_table o ON b.id = o.id  -- with join
SELECT COUNT(*) FROM base_table                                            -- without join
```

If joined_count > base_count: you have fan-out. Every SUM() is inflated by the ratio.
Fix: pre-aggregate the many-side table into a subquery keyed on the join key BEFORE joining.

Past incident: transactions LEFT JOIN transactions_items (avg 1.59 items/order) inflated
SUM(amount) by 1.59x — SINK showed $6.86M vs source $4.32M. COUNT(DISTINCT) was correct
because DISTINCT is fan-out-safe, but SUM is not.

### 5. If Discrepancies Found
```
STOP dashboard iteration
Review Step 4b queries for errors:
  - Wrong grouping? Missing WHERE conditions? Join explosion?
Fix queries → re-execute → re-validate
```

**Output:** Data accuracy certified ✓ OR issues found → return to Step 4b

---

## Step 4g: Test Filter Interactions (5-10 min)

**What to do:**
- Ensure all filters work independently and in combination
- Test drill-down flows
- Test edge cases

### 1. Date Range Filter
```
Set to "Last 7 days" → Dashboard updates
Set to "Last 90 days" → Dashboard shows more data
✓ Verify metrics trend in expected direction (older = more data)
```

### 2. Dimension Filters
```
Select "North America" → Dashboard shows only NA data
✓ Verify KPI totals change when filter applied
```

### 3. Multi-Select Filters
```
Select [North America, Europe] → Dashboard shows combined data
✓ Verify metrics sum to combined total
```

### 4. Multi-Filter Combination Spot-Check (mandatory before Step 4i)
Pick at least 2 combinations that cross dimensions. Run same WHERE against SINK AND source:

```bash
tdx query "SELECT SUM(total_revenue), SUM(order_count) FROM sink_db.sink_table
           WHERE category = 'X' AND channel = 'Y'"
           
tdx query "SELECT ROUND(SUM(amount),2), COUNT(DISTINCT order_id) FROM source_db.transactions
           WHERE category = 'X' AND channel = 'Y'"
```

Values must match to the cent. If not: fan-out, wrong grain, or filter not applied at SQL layer.
Also verify: KPI cards update visually when filters change. A common failure is KPI cards that
always read pre-aggregated all-time totals regardless of the active filter selection.

### 5. Drill-Down Flows (if requirements needed it)
```
Click dimension value in chart
✓ Dashboard updates for that dimension only
✓ "Reset drill-down" / "Back" button returns to full view
✓ Drill-down works through 2+ levels (if required)
```

### 6. Date + Region Together
```
Set date to "Last 7 days" AND region to "North America"
Manually run query with both conditions
✓ Dashboard matches manual query
```

### 7. All Filters Together
```
Set date AND region AND segment
✓ Dashboard shows intersection of all conditions
```

### 8. Empty Result Set
```
Filter to a region with 0 results
✓ Dashboard shows "No data" or 0 in metrics (from Step 4d-Final)
✓ Should NOT crash or show error
```

### 9. All Values Selected
```
Select ALL regions
✓ Dashboard shows total (same as no filter applied)
```

### 10. Rapid Filter Changes
```
Click filter rapidly, selecting different values in quick succession
✓ Dashboard handles without freezing
✓ Last selection is displayed (no race conditions)
```

### 11. Tab Switching (if multi-tab)
```
Set filters on Tab 1 → Switch to Tab 2
✓ Filters persist
✓ Switch back: Same filters still active
```

### 12. Export (if requirements needed it)
```
Click export button
✓ CSV/PDF downloads correctly
✓ Data matches dashboard (correct metrics, right filters applied)
```

**Output:** All filter combinations working, edge cases handled, drill-down flows validated

---

## Step 4h: Performance Check (3-5 min)

**What to do:**
- Measure query execution times
- Identify performance bottlenecks
- Establish performance baseline

### Measure Initial Load Time
```
Target: < 5 seconds for initial load
Record: _____ seconds
```

### Measure Query Times Individually
```
Query 1 (overall metrics):  _____ seconds (target: < 3 sec)
Query 2 (by dimension):     _____ seconds (target: < 3 sec)
Query 4 (time series):      _____ seconds (target: < 3 sec)
```

### Measure Filter Update Performance
```
Change date filter from "90d" to "30d"
Time from click to update: _____ seconds (target: < 1 second)
```

### If Queries Exceed 5 Seconds
```
- Check if WHERE filters have indexes on date, region, etc.
- Reduce date range
- Use APPROX_DISTINCT() instead of COUNT(DISTINCT)
- Reduce LIMIT if returning too many rows
- Flag for future: "Consider the Workflow path (Phase 2) if performance becomes critical"
```

### Document Performance Baseline
```
Query 1: __ sec | Query 2: __ sec | Query 4: __ sec
Filter update: __ms | Initial load: __ sec
```

**Output:** Performance baseline documented

---

## Step 4i: Get User Feedback + Approval Loop (5-10 min)

**What to do:**
- Share dashboard with user
- Collect feedback
- Issues → loop back; approval → proceed to 4j

**Before rebuilding (if major rework): Create widget inventory first.**

```
Tab: Overview
  ✓ KPI card: Total Revenue
  ✓ KPI card: Total Bookings
  ✓ Chart: Revenue by Segment (bar)
  ✓ Filter: Date Range
  ...
```

After rebuild, diff against inventory — missing widgets must be restored before sharing.
(Silent widget drops are the #1 cause of "where did that chart go?" feedback.)

### Share Dashboard

Before asking for approval, present a dashboard summary in a code block:

```
🎨 Dashboard Ready — <Project Name>

Tabs / Sections:  <list all tabs or panels>
KPI Cards:        <list all KPI metric names>
Charts:           <list all chart names and types>
Filters:          <list all filter controls>
Date Range:       <default_range> | picker: <yes | no>

Data source:      <SINK database | source tables>
Query time:       ~<N>s  |  Filter response: ~<N>ms
Data as of:       <last_updated>

Validated against Stage B / Phase 2 spot-checks:  <✅ Yes | ⚠️ delta>
```

**---  ↑ Review the summary above, then respond below  ↑  ---**

```
AskUserQuestion:
  header: "Approve Dashboard"
  question: "Does the summary look correct?"
  options:
    - label: "✅ Approve"
      description: "All metrics and filters correct."
    - label: "❌ Numbers wrong"
      description: "Metrics unexpected. Validate accuracy."
    - label: "➕ Missing"
      description: "Add missing metric or chart."
    - label: "🔧 Adjust"
      description: "Tweak filters or visual design."
```

### Common Feedback Patterns
```
"The numbers look high"     → Loop back to Step 4f (validate accuracy)
"Can you add [metric]?"     → Loop back to Steps 4c/4d (re-query)
"Change date range default" → Loop back to Step 4d (update query params)
"Rename [chart title]"      → Loop back to Step 4e (re-render)
"Perfect, looks great!"     → Proceed to Step 4j → Phase 4 or Phase 5
```

### Record User Feedback
```
Categorize into:
  - "Fix for Phase 3" (blocking — must resolve before exit)
  - "Nice to have" (after user satisfied — can defer to Phase 4/5)

If fixes needed:
  - Loop back to appropriate step
  - If major rebuild: use widget inventory (Step 4i pre-rebuild check above)
  - Re-validate after fix
  - Return to Step 4i for re-approval
```

**Output:** User approved → proceed OR issues found → loop back to fix

---

## Step 4j: Document Dashboard Parameters (3-5 min)

**What to do:**
- Record technical details for future reference and Phase 4/5 handoff

**Document Template (write to `state.md` — append, do not rebuild):**

```markdown
## Phase 3: Dashboard Build Complete

**Project:** [project-name]
**Date Approved:** [Today]
**Rendering Engine:** HTML Client
**Path:** [Non-Workflow | Workflow]

### Dashboard Overview
- KPIs: [list]
- Filters: [list]
- Charts: [list]
- Table: [yes/no]

### Source Data
- Database: [database_name]
- Fact Table: [table_name] ([row_count] rows)
- Dimension Tables: [list or None]
- Date Range: Last 90 days

### Metrics (with formulas)
- Metric 1: [formula]
- Metric 2: [formula]

### Dashboard Artifact
- **Type:** HTML Client (single portable file)
- **Location:** ./<project-name>/dashboards/dashboard.html

### Exclusion Rules Applied
- [rule 1 from Stage A]
- [rule 2 from Stage A]

### Validation Results
- Data accuracy: ✅ All KPIs match Stage B / Phase 2 spot-checks
- Filter tests: ✅ Independence + combinations + edge cases passed
- Performance: ✅ Load [N]s, queries [N]s, filter response [N]ms
- Mobile: ✅ Tested (or N/A)
- User approval: ✅ Approved on [date]

### Query Performance Baseline
- Overall metrics: [X] sec
- By dimension: [X] sec
- Time series: [X] sec
- Filter update: [X] ms
- Initial load: [X] sec

### Next Step
[Phase 4 (Automate & Deploy) / Phase 5 (Handoff Documentation) / Close]

### User Feedback (Step 4i)
[Will be filled in after approval]
```

**Output:** Dashboard parameters documented

---

## Step 4k: Test Mobile & Responsive Design (5-8 min) ⚠️ Conditional

**When to run:**
- Requirements specified: "Mobile responsive design needed" or "Accessed on mobile devices"

**If mobile support NOT required:**
- Skip this step
- Document in deployment-checklist.md: "Desktop-only dashboard; not tested on mobile"

**Test Matrix (Viewport Sizes):**

| Device | Viewport | Browser |
|---|---|---|
| **Desktop** | 1920×1080 | Chrome, Firefox, Safari |
| **Tablet** | 768×1024 (iPad portrait) | Chrome, Safari |
| **Mobile** | 375×667 (iPhone SE) | Chrome, Safari |
| **Mobile** | 412×915 (Android) | Chrome, Firefox |

**Test on Desktop (1920x1080):**
```
✓ Fully visible without horizontal scrolling
✓ All charts, tables, filters visible
✓ Spacing comfortable (not cramped)
```

**Test on Tablet (768x1024):**
```
✓ Layout stacks vertically
✓ KPI cards stack in 1-2 columns (not 4)
✓ Charts scale to fit width
✓ No horizontal scrolling
```

**Test on Mobile (375x667 and 412x915):**
```
✓ Dashboard usable on small screen
✓ All elements touch-friendly (44px+ tap target)
✓ Charts/tables scroll vertically, not horizontally
✓ Text readable (not too small <14px)
```

**Testing Procedure:**

1. **Open DevTools → Device Toolbar (F12 → toggle device toolbar)**
2. **Test each breakpoint:** Select device from dropdown → Dashboard auto-resizes. Verify: charts are readable, no horizontal overflow, filters are accessible.
3. **Test interactions (per breakpoint):**
   - [ ] Can you click a filter dropdown without scroll?
   - [ ] Do charts render without overlap?
   - [ ] Is text readable (minimum 14px)?
   - [ ] Are buttons/inputs large enough to tap (44×44px)?

**Common Mobile Issues:**
- ❌ Horizontal scrolling at any screen size
- ❌ Text too small (<14px on mobile)
- ❌ Buttons too small (<44px touch target)
- ❌ Charts cramped or unreadable
- ❌ Chart legend covering data

**Fixing Issues:**

**Issue: Content too wide (horizontal scroll)**
```css
/* In dashboard.html <style> section */
body { max-width: 100vw; overflow-x: hidden; }
.container { width: 100%; }
```

**Issue: Buttons too small**
```css
button { min-width: 44px; min-height: 44px; padding: 10px 16px; }
```

**Issue: Chart overlap on mobile**
```javascript
// In generate-data.js, reduce chart data on mobile
var chartRows = window.innerWidth < 768 ? 5 : 20;  // Fewer lines on mobile
```

Testing approach: Chrome/Firefox F12 → device toolbar. Test breakpoints: 1920px, 1366px, 768px, 375px, 412px.

**Acceptance Criteria:**

- [ ] All test matrix breakpoints tested (4 device types)
- [ ] No horizontal scrolling needed
- [ ] All text readable at minimum 14px
- [ ] All touch targets ≥ 44×44px
- [ ] Charts render without overlap

**Output:** Mobile responsiveness validated

---

## Step 4l: Initial Load Performance & UX (3 min) ⚠️ Conditional

**When to run:**
- Step 4h found slow queries (> 5 seconds)
- Requirements mentioned "must load in under X seconds"
- Dashboard has many charts/tables

### Time-to-First-Metric
```
Time from page load to first KPI card displayed
Target: < 1 second
```

### Time-to-Interactive
```
Time from page load to filters become clickable
Target: < 3 seconds
```

### Time-to-All-Data
```
Time from page load to all charts/tables fully rendered
Target: < 5 seconds
```

### UX During Load
```
✓ Loading spinner appears within 500ms?
✓ Progress communicated? ("Loading dashboard... 2/5 queries complete")
✓ Page feels responsive (not frozen)?
```

Since data is inlined into `dashboard.html` (Pattern A), load time should be dominated by browser render/parse time rather than any query — if load feels slow, check payload size (Step 4d's Payload Size Budget) before anything else.

### If Any Metric Exceeds Target
```
Review Step 4h analysis
Consider: Reduce date range, pre-aggregate more in SQL, trim payload size
Flag for Phase 4/5: "Performance optimization needed"
```

**Output:** Initial load performance established

---

## Phase 3 Exit: Update state.md

After user approves (Step 4i "Perfect, looks great!"), append to `state.md`:

```markdown
## Phase 3: Dashboard Build Complete

**Project:** [project-name]  **Date:** [Today]  **Engine:** HTML Client

Dashboard: [N] KPIs, [N] filters, [N] charts
Validation: ✅ Accuracy | ✅ Filters | ✅ Performance | ✅ User approved [date]
Performance: Load [N]s | Queries [N]s | Filter response [N]ms

**Status:** Phase 3 — Complete
**Next Action:** Phase 4 (Automate & Deploy) OR Phase 5 (Handoff Documentation) OR close out
```

Save `state.md` locally before routing to the next phase.

---

## Quality Gates (MUST PASS ALL before exiting Phase 3)

✅ All 5 queries validated locally — correct data before embedding  
✅ Dashboard structure matches requirements layout preference  
✅ All filters wired + error states handled  
✅ Dashboard renders with real data — no blank components  
✅ Data range banner present in header  
✅ Every widget has ⓘ tooltip — definition + calculation visible on hover  
✅ **Data accuracy validated** (Step 4f: dashboard KPIs match Stage B / Phase 2 spot-checks)  
✅ All filters tested — independently, in combination, edge cases  
✅ Performance baseline recorded — all queries < 5 sec  
✅ **User approved** (Step 4i: feedback collected and resolved)  
✅ Technical parameters documented in `state.md` (Step 4j)  
✅ Mobile tested (if required) (Step 4k)  
✅ `state.md` updated (append only)  

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team

---

