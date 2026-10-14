# Phase 3: Build + Validate Interactive Dashboard

**Entry Point:** After Phase 1 (Requirements + Data Discovery) OR Phase 2 (Workflow, SINK tables deployed)
**Continuation:** Same session from preceding phase
**Output:** Live interactive `dashboard.html`, fully validated, tested, user-approved

---

## Pre-Phase 3 Checklist

- ✅ Phase 1 complete: database, tables, metrics, dimensions all validated with real sample values
- ✅ Phase 2 complete (if Workflow path): SINK tables deployed and validated
- ✅ Path confirmed: Non-Workflow (query source tables) OR Workflow (query SINK tables)
- ✅ `state.md` accessible — **read it at Phase 3 start** for exclusion rules, filter specs, metrics list, benchmark values, and any Phase 1/2 appended findings
- ✅ Platform access confirmed (tdx CLI authenticated)

**If resuming Phase 3:** Read `state.md` → find last completed step → open `references/steps.md` and jump directly to the next step.

**Chart colors:** Use the TD palette for any Chart.js series — `["#B4E3E3", "#ABB3DB", "#D9BFDF", "#F8E1B0", "#8FD6D4", "#828DCA", "#C69ED0", "#F5D389", "#6AC8C6", "#5867B8"]` — unless the user specified brand colors during Phase 1 (check "Visual Preferences" in `state.md`).

---

## Key Concept

- **Non-Workflow path:** Queries run against source tables (fresh, 5-10 sec)
- **Workflow path:** Queries run against pre-aggregated SINK tables (< 2 sec, scheduled freshness)

The key architectural difference is that Workflow path dashboards never touch source tables — all KPIs come from pre-computed SINK tables deployed in Phase 2. This means filter logic must be applied at SQL WHERE on SINK tables, not re-aggregated client-side.

---

## Architecture: Two-Tier Filter Pattern + Three Data Shapes (CRITICAL)

### Two-Tier Filter Architecture

**All Phase 3 dashboards must implement exactly two tiers:**

**Tier 1: Global Date Range Filter (F.start, F.end)**
- Source: `sink_overview_kpis` (daily grain, NO dimension columns)
- Scope: All KPI cards + trend chart globally
- Applies to: All tabs simultaneously
- Why: Date filtering requires daily or finer grain; impossible on pre-grouped dimension data

**Tier 2: Per-Tab Dimension Filters (FS.<tab>.<dimension>)**
- Source: Distinct values from each tab's SINK table
- Scope: Active tab's widgets only
- Applies to: Only the currently visible tab
- Why: Separates dimension aggregation (monthly grain, coarse) from date filtering (precise)

**Logic flow:**
```javascript
if (activeDimFilters.length === 0) {
  // No dimension filter → use daily overview data
  data = sink_overview_kpis.filter(r => r.date >= F.start && r.date <= F.end);
} else {
  // Dimension filter active → use monthly+dimension table (Shape S3, item below)
  data = sink_<tab>_monthly_dims.filter(r => 
    r.month >= F.start.slice(0,7) && 
    r.month <= F.end.slice(0,7) &&
    matchesDimFilters(r, FS.<tab>)
  );
}
```

### Three Required Data Shapes (Not Two!)

Every Phase 3 **must generate exactly three data shapes**. Missing the third is the most common architecture gap.

| Shape | Query Pattern | Use Case |
|-------|---------------|----------|
| **S1: Daily, no dims** | `SELECT date, SUM(revenue) FROM sink_daily GROUP BY date` | Date-filtered KPIs when no dimension filter active |
| **S2: All-time, with dims** | `SELECT category, SUM(revenue) FROM sink_daily GROUP BY category` | Breakdown charts; dimension filter only (no date range) |
| **S3: Monthly, with dims** ⭐ | `SELECT SUBSTR(date,1,7), category, SUM(revenue) FROM sink_daily GROUP BY 1,2` | **Respond to BOTH date + dimension filters simultaneously** |

**Shape S3 is what's typically missing.** Without it, KPI cards cannot update when users set both a date range AND a dimension filter.

**Query generation (ALL SHAPES REQUIRED):**
```javascript
const q1 = query_overview();                    // S1
const q2 = query_breakdown_category_alltime();  // S2
const q3 = query_breakdown_payment_alltime();   // S2
const q4 = query_sales_monthly_dims();          // S3 ← CRITICAL
const q5 = query_web_monthly_dims();            // S3 ← CRITICAL
const q6 = query_customers_monthly_dims();      // S3 ← CRITICAL

const results = await Promise.all([q1, q2, q3, q4, q5, q6]);
```

**See `phase-3-data-patterns.md` item 2** for cardinality estimation and LIMIT sizing for S3 queries.

---

## Build+Validate Loop

```
4b-4e: Build (queries -> structure -> connect -> render)
  |
4f: Validate data accuracy  --X FAIL --> back to 4b (re-query)
  |
4g: Test filters             --> FAIL --> back to 4d (re-connect)
  |
4h-4i: Performance, Feedback --> Issues --> back to:
    4b - wrong queries | 4c - wrong structure | 4d - broken data
    4e - render failure | 4g - filter bug
  |
4j-4l: Document, Mobile (if required), Load UX (if needed)
  |
Final: User Approval (Step 4i)
  -> Approved -> Phase 4 (Automate & Deploy) or Phase 5 (Handoff Documentation), both optional
  -> Changes -> loop back
```

(Step 4a from the original build loop is a no-op in the lite skill — the rendering engine is always HTML Client, nothing to confirm.)

---

## How to Execute

> **All user-facing questions in this phase use `AskUserQuestion`** — never plain text lists.
> Provide 2–4 pre-populated options. Mark recommended with `(Recommended)`. Batch up to 4 questions per call.

**Template source (embedded locally, no external repo needed):** `references/rendering/html-client/templates/`

Copy the standard template into your project:

```bash
mkdir -p ./<project-name>/dashboards

cp references/rendering/html-client/templates/dashboard.template.html \
   ./<project-name>/dashboards/dashboard-template.html

cp references/rendering/html-client/templates/generate-data.js \
   ./<project-name>/dashboards/generate-data.js
```

Then customize `generate-data.js` with the confirmed tables/columns from Phase 1/2, and update the `<h1>` title in `dashboard-template.html`. See `references/rendering/html-client/template-customization.md` for the full walkthrough.

**All templates include Chart.js inline — no external dependencies, works offline.**

**Now proceed to execute steps in [`references/steps.md`](references/steps.md)** — all steps 4b through Phase Exit are in one linear file. Use the quick-jump table at the top to land on the right step.

Steps 4k (mobile) and 4l (load UX) are conditional — the step headers flag when to run them.

---


---


---

## Visual Consistency: Dimension Colors Across Widgets

**Rule:** All widgets displaying the same dimension (e.g., `booking_channel: web, online, phone`) must use the **same color** for that value everywhere.

### Treasure Data Theme Colors (Default)

Use this palette unless the user specified brand colors in Phase 1 Step 1d:

```javascript
const TD_PALETTE = [
  "#B4E3E3",  // Teal
  "#ABB3DB",  // Lavender
  "#D9BFDF",  // Mauve
  "#F8E1B0",  // Peach
  "#8FD6D4",  // Cyan
  "#828DCA",  // Purple
  "#C69ED0",  // Pink
  "#F5D389",  // Gold
  "#6AC8C6",  // Turquoise
  "#5867B8"   // Royal Blue
];
```

### Example: Booking Channel

If KPI cards show booking channels and the trend chart also shows them:

| Channel | Color (all widgets) |
|---------|------------------|
| web | #B4E3E3 (Teal) |
| online | #ABB3DB (Lavender) |
| phone | #D9BFDF (Mauve) |

**Implementation:** Define the color map once in `generate-data.js`, then reference it in all chart configs and filter displays.

### Custom Brand Colors

If Phase 1 Step 1d captured custom brand colors:
1. Replace the TD_PALETTE array with user colors
2. Assign dimensions to colors in the same order across all widgets
3. Document the mapping in `state.md` (Phase 3 section)



---

## Date Granularity — User's Choice (Not a Default Optimization)

**Important:** Date granularity is a **business decision**, not a performance optimization. Choose based on what your dashboard needs to display, not on payload size.

**Available options:**

| Granularity | SQL Pattern | Payload per 1K rows | Use when |
|---|---|---|---|
| **Second** | `date` as-is | ~19 KB | Minute-level tracking needed |
| **Minute** | `SUBSTR(date, 1, 16)` | ~16 KB | Event-level diagnostics |
| **Hour** | `SUBSTR(date, 1, 13)` | ~13 KB | Hourly KPIs |
| **Day** | `SUBSTR(date, 1, 10)` | ~10 KB | Daily trends, drill-down needed |
| **Month** | `SUBSTR(date, 1, 7)` | ~7 KB | Monthly aggregations |
| **Year** | `SUBSTR(date, 1, 4)` | ~4 KB | Annual reporting |

**DO NOT truncate just to reduce payload size.** Choose the granularity your dashboard actually needs.

### Examples (Choose Based on Dashboard Needs)

```javascript
// Daily granularity — shows trends day-by-day
// User can see which specific day had the spike
var trendRows = query(
  'SELECT SUBSTR(date, 1, 10) AS day, SUM(revenue) AS revenue FROM sales ' +
  'GROUP BY SUBSTR(date, 1, 10) ORDER BY day DESC LIMIT 90'
  // ~900 rows × 10 bytes = 9 KB dates
);

// Monthly granularity — shows 12-month view
// User trades daily detail for cleaner yearly view
var trendRows = query(
  'SELECT SUBSTR(date, 1, 7) AS month, SUM(revenue) AS revenue FROM sales ' +
  'GROUP BY SUBSTR(date, 1, 7) ORDER BY month DESC LIMIT 24'
  // ~24 rows × 7 bytes = 0.2 KB dates (but loses daily detail)
);

// Full precision — needed for real-time or exact timestamps
var trendRows = query(
  'SELECT date, SUM(revenue) AS revenue FROM sales ' +
  'WHERE date >= CURRENT_DATE - 7 ' +
  'GROUP BY date ORDER BY date DESC'
  // Full ISO-8601 dates (19 bytes each)
);
```

### Decision Framework

Ask yourself:
- **What level of detail does the user need?** (day, month, year, hour?)
- **Can they drill down or are they viewing aggregates only?** (daily = drillable; monthly = cannot drill)
- **Is the dashboard real-time or historical?** (real-time = seconds/minutes; historical = days/months)

**If unsure, keep full date precision.** You can always optimize later if payload size becomes an issue.

---

---

## Multi-Level Filters: Dashboard + Tab Filters (Pre-Aggregate Strategy)

**Goal:** Zero re-queries, all filtering client-side, instant experience

### Architecture: Pre-Aggregate by All Filter Dimensions

**Embed once:** Pre-aggregated data grouped by BOTH dashboard dimensions AND tab dimensions. Then filter client-side only.

```
Dashboard Dimensions: date, region
Tab 1 Dimensions: product, channel
Tab 2 Dimensions: status, segment

    ↓
Embed single pre-agg dataset (all combinations in GROUP BY)
    ↓
Dashboard filter change → Filter embedded data (instant, no query)
Tab filter change → Filter embedded data (instant, no query)
```

### SQL Query Structure

```sql
SELECT
  date,                              -- Dashboard filter dimension
  region,                            -- Dashboard filter dimension
  product,                           -- Tab 1 filter dimension
  channel,                           -- Tab 1 filter dimension
  status,                            -- Tab 2 filter dimension
  segment,                           -- Tab 3 filter dimension
  COUNT(*) as n,                     -- Metric
  SUM(revenue) as r                  -- Metric
FROM sales_fact
GROUP BY 1, 2, 3, 4, 5, 6
LIMIT 10000
```

**Result:** 2,000-5,000 rows (only actual combinations in data, not all theoretical combinations)

### Implementation: generate-data.js

```javascript
// 1. Embed: Pre-aggregated by all dashboard + tab dimensions
var RAW = query(
  'SELECT date, region, product, channel, status, segment, ' +
  '       COUNT(*) as n, SUM(revenue) as r ' +
  'FROM sales_fact ' +
  'WHERE date >= ' + minDate + ' ' +
  'GROUP BY 1,2,3,4,5,6 LIMIT 10000'
);

// 2. Client-side: Filter by dashboard criteria
function applyDashboardFilters(rows, filters) {
  return rows.filter(row =>
    row.date >= filters.startDate &&
    row.date <= filters.endDate &&
    row.region === filters.region
  );
}

// 3. Client-side: Aggregate for Tab 1 (Revenue by Product+Channel)
function revenueByProductChannel(filteredRows) {
  const agg = {};
  filteredRows.forEach(row => {
    const key = row.product + '|' + row.channel;
    if (!agg[key]) agg[key] = { product: row.product, channel: row.channel, n: 0, r: 0 };
    agg[key].n += row.n;
    agg[key].r += row.r;
  });
  return Object.values(agg);
}

// 4. Client-side: Aggregate for Tab 2 (Orders by Status+Segment)
function ordersByStatusSegment(filteredRows) {
  const agg = {};
  filteredRows.forEach(row => {
    const key = row.status + '|' + row.segment;
    if (!agg[key]) agg[key] = { status: row.status, segment: row.segment, n: 0 };
    agg[key].n += row.n;
  });
  return Object.values(agg);
}

// 5. User filters on Tab 1: product="Laptop"
function filterTab1ByProduct(rows, productFilter) {
  return rows.filter(row => row.product === productFilter);
}
```

### Workflow

```
1. User opens dashboard
   ↓
2. Query embedded data (pre-agg by date/region/product/channel/status/segment)
   ↓
3. Embed into dashboard.html (all data loaded once)
   ↓
4. User changes DASHBOARD filter (date range / region)
   → Apply filter on RAW in memory (instant)
   → Re-aggregate each tab (instant)
   → Update charts (instant)
   ↓
5. User changes TAB filter (product / status)
   → Apply filter on already-filtered data (instant)
   → Re-aggregate that tab only (instant)
   → Update that tab's charts (instant)
```

### Payload Size

| Scenario | Rows | Per-row | Payload | Re-query? |
|---|---|---|---|---|
| Pre-agg (all dims) | 3,000 | 80 bytes | 240 KB | ❌ No |
| Full row-level | 10,000 | 120 bytes | 1,200 KB | ❌ No (too large!) |
| Pre-agg per-tab | 150 | 80 bytes | 12 KB | ✅ Yes (on dashboard change) |

**Sweet spot:** Pre-aggregate by all dimensions = instant filtering + a payload comfortably within the ideal tier (see "Payload Size Budget" below)

### Numeric Coercion

To keep payload within the ideal (< 500KB) tier, use IDs instead of strings:

```javascript
// ❌ Strings (120 bytes per row)
{date: "2026-07-16", region: "North America", product: "Premium Laptop", channel: "Online", status: "completed", n: 1, r: 499.99}

// ✅ IDs (60 bytes per row)
{date: "2026-07-16", rid: 1, pid: 5, chid: 2, sid: 1, n: 1, r: 499.99}

// Map IDs → Display names
var regions = {1: "North America", 2: "Europe", 3: "APAC"};
var products = {5: "Premium Laptop", 6: "Budget Tablet", ...};
var channels = {2: "Online", 3: "Retail", ...};
```

### Refresh: Re-Query on User Request

**Allow users to manually refresh** for fresh data without constant server polling.

```html
<!-- Add refresh button to dashboard.html -->
<button id="refreshBtn" onclick="refreshData()">🔄 Refresh Data</button>
<span id="lastRefresh">Last updated: just now</span>
```

```javascript
// Client-side: Refresh handler
async function refreshData() {
  document.getElementById('refreshBtn').disabled = true;
  document.getElementById('refreshBtn').textContent = '⏳ Refreshing...';
  
  try {
    // Re-query server with same filter dimensions
    var newRAW = await query(
      'SELECT date, region, product, channel, status, segment, ' +
      '       COUNT(*) as n, SUM(revenue) as r ' +
      'FROM sales_fact ' +
      'WHERE date >= ' + minDate + ' ' +
      'GROUP BY 1,2,3,4,5,6 LIMIT 10000'
    );
    
    // Replace embedded data
    RAW = newRAW;
    
    // Re-apply current filters and update charts
    var filtered = applyAllFilters(RAW);
    updateAllTabs(filtered);
    
    // Update timestamp
    document.getElementById('lastRefresh').textContent = 
      'Last updated: ' + new Date().toLocaleTimeString();
    
  } catch (error) {
    alert('❌ Refresh failed: ' + error.message);
  } finally {
    document.getElementById('refreshBtn').disabled = false;
    document.getElementById('refreshBtn').textContent = '🔄 Refresh Data';
  }
}
```

**When to offer refresh:**
- Dashboard with real-time data (refresh every 5-10 min, or on-demand)
- Dashboard with daily/weekly snapshots (refresh daily at 2am, or on-demand)
- Dashboard with manual report uploads (refresh after user confirms upload)

**Typical patterns:**
- Manual refresh button (always available)
- Auto-refresh toggle (5/10/30 min intervals)
- Timestamp + "Refresh" link

---

### Benefits

✅ **Zero re-queries** — all data embedded once  
✅ **Instant filtering** — all operations in-memory  
✅ **Optimal payload** — within the ideal < 500KB tier (pre-agg by dims, numeric IDs)  
✅ **Simple client logic** — just filter + aggregate  
✅ **Works offline** — once loaded, no server needed  

---

---

### JSON Parsing Approaches: File I/O vs Regex

The template uses **file I/O** to embed data; Phase 4 documentation mentions **regex parsing**. Both work depending on your data flow.

**Approach A (Phase 3 template uses): File I/O**

```javascript
// Read pre-generated JSON file
var rawJSON = fs.readFileSync('./data.json', 'utf8');
var RAW = JSON.parse(rawJSON);

// Embed into HTML as inline variable
var htmlContent = `
  <script>
    var RAW = ${JSON.stringify(RAW)};
  </script>
`;
fs.writeFileSync('./dashboard.html', htmlContent);
```

**When to use:** You have a `.json` file that was pre-created by `generate-data.js`

---

**Approach B (Phase 4 mentions): Regex JSON Parsing**

```javascript
// Extract JSON from query output using regex
var queryOutput = execSync('tdx query ...').toString();
var jsonMatch = queryOutput.match(/\{[^}]+\}/);
var RAW = JSON.parse(jsonMatch[0]);
```

**When to use:** Extracting JSON from CLI query output or text logs (avoids intermediate `.json` file)

---

**Which to choose:**

| Scenario | Use | Why |
|---|---|---|
| Generate data once, embed in HTML | **File I/O (A)** | Simpler, safer, easier to debug |
| Extract from live query output | **Regex (B)** | No intermediate files, real-time |
| Dashboard already has data.json | **File I/O (A)** | Don't reinvent; use what exists |

Both are valid; use whichever fits your workflow.

---



### Phase 2 SINK Patterns Reference

**If Phase 2 workflow was used**, your dashboard queries read from pre-aggregated SINK tables.

**Pattern A: Separate SINK tables per metric**
```
SINK_DB.kpi_daily (KPIs by date)
SINK_DB.breakdown_product (by product)
SINK_DB.breakdown_region (by region)
```
→ **Query in Phase 3:** Join these tables on date, or query each separately

**Pattern B: Pre-computed distinct counts**
```
SINK_DB.fact_deduped (rows without duplicates)
```
→ **Query in Phase 3:** COUNT(DISTINCT user_id) returns accurate customer count (no re-counting needed)

**Risk: Double-counting**
- ❌ WRONG: `SELECT COUNT(DISTINCT user_id) FROM kpi_daily` (users already pre-aggregated)
- ✅ RIGHT: `SELECT user_count FROM kpi_daily` (use pre-computed column)

**Check your workflow:** Look at `./<project-name>/workflows/queries/*.sql` to see which pattern was used.

---


## Performance & Payload Optimization (Phase 3)

**Payload size budget (tiered — canonical policy, see `references/rendering/html-client/html-dashboard-patterns.md` → "Data Size Budget & Optimization"):**

```
< 500KB total   → inline directly (fast load, shareable) — IDEAL
500KB – 2MB     → acceptable (modern browsers handle)
> 2MB           → ❌ HARD STOP — requires SQL optimization, not a fallback path
```

**Most dashboards are already optimized.** If your dashboard is slow or the HTML file is outside the ideal tier, work through the checklist below.

### Optimization Checklist

| Step | What | Impact |
|------|------|--------|
| **1. Pre-aggregate** | GROUP BY filter dimensions only (not raw data) | 10K rows → 100-200 rows (95% reduction); biggest win, ~90% payload reduction |
| **2. Choose date granularity** | Use the granularity your dashboard needs (don't truncate by default) | Day = 10 bytes/row; Month = 7 bytes/row; trade precision for size only if needed |
| **3. Numeric coercion** | Parse `"1234.56"` → `1234.56` in generate-data.js | -3 bytes per numeric × 10K values = -30 KB |
| **4. SELECT only used columns** | No unused fields in final JSON | -50 bytes per unused column × 1K rows = -50 KB |
| **5. LIMIT enforcement** | All queries include `LIMIT 10000` (user can override) | Prevents OOM; user controls truncation |
| **6. Enable gzip when serving** | `npx serve --compress` or nginx gzip | HTML compresses ~500+ KB → 60-70 KB (87% reduction) — only applies if serving over network, not needed for double-click/email delivery |

### Example: Optimized Query Pattern

```javascript
// ❌ WRONG: Raw data, all columns, no aggregation
var data = query(
  'SELECT date, channel, type, status, revenue, customer_id, order_id, device, region, ' +
  '       source, utm_campaign, utm_medium, notes FROM orders'
  // Result: 50,000 rows × 15 columns = 500+ KB JSON, bloated
);

// ✅ RIGHT: Pre-aggregated, selective columns, short names
var data = query(
  'SELECT SUBSTR(date, 1, 7) AS m, channel AS ch, type AS ty, status AS st, ' +
  '       SUM(revenue) AS r, COUNT(*) AS n ' +
  'FROM orders ' +
  'WHERE date >= CURRENT_DATE - 90 ' +
  'GROUP BY 1, 2, 3, 4 ' +
  'ORDER BY m DESC ' +
  'LIMIT 500'
  // Result: 200 rows × 6 columns = 15 KB JSON, gzips to <5 KB
).map(shortField);  // ← apply FIELD_MAP (ch/ty/st/etc)
```

### Payoff Math

| Optimization | Savings | Cost |
|---|---|---|
| Pre-aggregation (10K → 200 rows) | 475 KB | Re-aggregate on filter change |
| Date truncation (full → month) | 30 KB | Lose daily granularity (acceptable for KPIs) |
| Short field names | 24 KB | Must update dashboard.html field references |
| Numeric coercion | 30 KB | Slight JS overhead at render time |
| Column selection | 50 KB | Must identify unused fields |
| **Total** | **~600 KB → 20 KB** | **70% size reduction** |

### When to Use Each

**Use heavy optimization (all 6):**
- Mobile/slow networks
- Email distribution
- Offline viewing
- File size critical

**Use light optimization (1-3):**
- Fast networks
- Dashboard embedded in app
- Real-time updates acceptable

### Data Truncation Warning: 10,000 Row Hard Limit

**Critical:** `generate-data.js` has a **hard limit of 10,000 rows per query** to prevent memory overload in large dashboards.

```javascript
// In generate-data.js
var limit = (limitRows === undefined) ? 10000 : limitRows;
```

- **Default:** 10,000 rows per query
- **For 100K+ row queries:** Data silently truncates — dashboard shows incomplete data
- **For pre-aggregated queries:** Usually fine (Phase 3 pre-aggregation often < 200 rows)

**Affects queries like:** non-aggregated fact tables (1M+ rows), customer transaction history without time boundaries, raw event streams.

**Does NOT affect (safe):** pre-aggregated rollups (100-500 rows), time-bounded queries (daily/weekly windows), filtered datasets.

**Override the limit per-query:**

```javascript
// ✅ Increase limit for this query only
var largeResult = query(
  "SELECT * FROM million_row_table WHERE date >= CURRENT_DATE - 30",
  100000  // ← override default 10,000 limit
);

// ✅ Or remove limit entirely (CAREFUL — memory risk)
var hugeResult = query(
  "SELECT * FROM events_table",
  null  // ← no limit; will load ALL rows or OOM
);
```

**Before deployment, verify:**
- [ ] All queries tested with real customer data volume
- [ ] Row counts confirmed < 10,000 (or limit overridden deliberately)
- [ ] Dashboard still renders with max expected data
- [ ] Memory usage monitored on target machine
- [ ] Pre-aggregation applied where possible (recommended: 100-500 rows)

**Recommendation:** Always pre-aggregate by filter dimensions (see "Pattern: Pre-Aggregate by Filter Dimensions" earlier in this guide). This naturally keeps row counts in the 100-500 range, eliminating truncation risk entirely.

### Pre-Aggregate by Filter Dimensions (Biggest Win)

If your dashboard shows **overview filters** (e.g., channel, type, status, date) but you're returning thousands of individual detail rows:

- **Before:** 3,749 rows → 500+ KB payload → slow to load
- **After:** Pre-aggregate to unique filter combinations → ~100-200 rows → 50 KB payload

See [`references/query-patterns-for-dashboards.md`](references/query-patterns-for-dashboards.md) → "Pattern: Pre-Aggregate by Filter Dimensions" for exact SQL.

### Chart.js Is Inlined, Not Loaded via CDN

Chart.js is inlined directly inside each template's HTML (no `<script src="...cdn...">` tag, no external network request). This keeps the dashboard fully self-contained and working offline. It adds a fixed ~200 KB to every dashboard.html — this is expected and not itself reducible without breaking offline support. There is no CDN script to `defer`; no action is needed here.

### Enable Gzip When Serving the Dashboard

If serving via network (npx serve, nginx) rather than double-clicking or emailing the file directly:

```bash
# With serve
npx serve --compress ./<project-name>/dashboards/

# Result: HTML compresses from 500+ KB → 60-70 KB (87% reduction)
```

See [`references/rendering/html-client/html-deployment-guide.md`](references/rendering/html-client/html-deployment-guide.md) → "Performance Optimization: Enable Gzip Compression" for full setup. This step is optional — it only applies to the fallback server-hosting path, not the default double-click/email delivery.

### Profiling Tools

**Scenario:** Dashboard loads slowly on first render.

| Tool | What it shows | How to use |
|---|---|---|
| **Browser DevTools → Performance tab** | Page load timeline, JavaScript execution | Chrome/Firefox: F12 → Performance → Record → Reload → Analyze |
| **Browser DevTools → Network tab** | File sizes, load times per asset | F12 → Network → Reload; sort by size/time |
| **generate-data.js timing** | Query execution time + data size | Add `console.time()` / `console.timeEnd()` around query() call |

**Optimization checklist:**

- [ ] **Query time:** Is `generate-data.js` query slow (> 5s)? Optimize SQL with pre-aggregation
- [ ] **Data size:** Is embedded JSON outside the ideal tier (> 500 KB)? Apply numeric coercion (IDs instead of strings)
- [ ] **Chart rendering:** Does Chart.js take > 2s to render? Reduce rows per dataset (LIMIT 100)
- [ ] **Filter updates:** Does dashboard hang when user changes filters? Profile in DevTools; likely need client-side optimization
- [ ] **Bundle size:** Is dashboard.html > 1 MB? Inlined Chart.js adds ~200 KB; acceptable if queries are fast and total stays within the 2MB acceptable tier

**Quick wins:**

1. **Before:** Full string data (product: "Premium Laptop")
   **After:** Numeric IDs (product_id: 5) → 50% smaller payload

2. **Before:** Raw 10K rows
   **After:** Pre-agg to 100-500 rows → 20x faster rendering

**Typical performance profile (good):**

- Query time: 2-3s
- Data size: 100-200 KB (after coercion)
- Chart render: < 1s
- **Total page load: < 5s** ✅

**If > 10s total load time:** Debug using profiling tools above; likely culprit is query time or data size.

---


## Quality Gates — 22-Point Implementation Checklist (ALL must pass)

### Architecture & Data Integrity (Items 1-12 from phase-3-query-and-filter-design.md)

- [ ] **Filter Architecture (Item 1):** Two-tier pattern fully wired
  - [ ] Global date range (F.start, F.end) affects all KPI cards + trend chart
  - [ ] Per-tab dimension filters (FS.<tab>.<dim>) affect active tab only
  - [ ] Code path switches between overview (no dims) and monthly+dims (dims active)

- [ ] **All Three Data Shapes Generated (Item 2):**
  - [ ] S1: Daily, no dimensions (sink_overview_kpis)
  - [ ] S2: All-time with dimensions (breakdown queries)
  - [ ] S3: Monthly + dimensions (monthly+dim queries for responsive date+dimension filtering)

- [ ] **Monthly Query Cardinality Validated (Item 3):**
  - [ ] Expected rows calculated for each S3 query
  - [ ] LIMIT set to ≥ 2× expected rows
  - [ ] Post-query check: no query returned exactly LIMIT (no truncation)
  - [ ] Cardinality audit documented in state.md

- [ ] **Cross-Filter Pattern Applied (Item 4):**
  - [ ] Each breakdown chart excludes its own dimension from active filters
  - [ ] Selecting category shows full category distribution (not collapsed to 1 bar)

- [ ] **Breakdown Charts Respond to Date Filter (Item 5):**
  - [ ] All breakdown charts use Shape S3 (monthly+dim), not all-time data
  - [ ] Date range changes update breakdown charts (not static)

- [ ] **Non-Additive Metrics Handled (Item 6):**
  - [ ] All COUNT DISTINCT columns documented with Phase 3 handling choice
  - [ ] If summed across dimensions: using overview OR source query OR fallback metric
  - [ ] Never blind SUM(unique_customers) across dimensional breakdowns

- [ ] **Payload Budget Pre-Calculated (Item 7):**
  - [ ] Estimated row counts × 40 bytes/row for all S3 queries
  - [ ] Total projected payload < 2 MB
  - [ ] Documented in state.md

- [ ] **Known Limitations Annotated (Item 8):**
  - [ ] Every limited widget has .widget-note (all-time only, non-date-filterable, approximation)
  - [ ] Annotation explains limitation and why

- [ ] **State.md Phase 3 Block Appended (Item 9):**
  - [ ] Query plan (all Q1–QN with row counts)
  - [ ] Payload size documented
  - [ ] Filter architecture summary
  - [ ] Known limitations list

- [ ] **Special Characters in Templates (Item 10):**
  - [ ] All non-ASCII in JavaScript strings use Unicode escapes (\uXXXX)
  - [ ] ÷, →, —, ×, &, ≈ all properly escaped

- [ ] **Dimension Combination Handling (Item 11):**
  - [ ] If monthly+dim cardinality > 5K: options presented + chosen approach documented
  - [ ] Trade-offs explained in state.md

- [ ] **Overview Path Documented (Item 12):**
  - [ ] Explicit documentation: overview used for date-only path; separate paths when filters active

### Code Implementation (Items 13-22 from phase-3-implementation-checklist.md)

- [ ] **Spot-Check Date Window Correct (Item 13):**
  - [ ] Window matches Phase 1 baseline exactly (not rolling 30 days)
  - [ ] Verified: dateEnd - 30 days = same window as Phase 1

- [ ] **Spot-Check Expected Values (Item 14):**
  - [ ] Values read from state.md (not hardcoded literals)
  - [ ] Or using all-time stable metrics (monotonically increasing)

- [ ] **Hidden Tab Charts Render Correctly (Item 15):**
  - [ ] Charts on hidden tabs re-rendered on switch (visibility issue fixed)
  - [ ] Or use visibility:hidden instead of display:none

- [ ] **No Dead Data in Payload (Item 16):**
  - [ ] No unused SINK columns included in RAW mapping
  - [ ] Or documented in comment why included but unused

- [ ] **Tab Filters Symmetric (Item 17):**
  - [ ] All SINK dimension columns have filter dropdowns
  - [ ] Not missing filters on one tab that exist on another

- [ ] **Filter-Active Indicator on Tabs (Item 18):**
  - [ ] Tab buttons show visual indicator (dot/badge) when that tab has active filters
  - [ ] Indicator updates on every filter change

- [ ] **Table Row Limits Transparent (Item 19):**
  - [ ] Every table shows "top N of M" in header
  - [ ] LIMIT is configurable constant (not magic number)
  - [ ] User sees they're viewing a ranked subset

- [ ] **Schema Validation at Build Time (Item 20):**
  - [ ] Required columns validated after Q1 runs
  - [ ] Build fails fast with clear error if schema mismatch
  - [ ] Not silently coercing undefined to 0

- [ ] **Offline Capability (Item 21):**
  - [ ] Chart.js inlined (true offline) OR
  - [ ] Clear disclaimer about CDN dependency

- [ ] **Render Optimization (Item 22):**
  - [ ] Only active tab re-rendered on filter changes
  - [ ] Not re-rendering all 4 tabs (wasteful)

### Standard Quality Gates

- [ ] Dashboard structure matches Phase 1 layout
- [ ] All filters wired + error states handled
- [ ] Renders with real data — no blank components
- [ ] Data range banner present (showing actual date window)
- [ ] Every widget has tooltip with definition + calculation
- [ ] **Data accuracy validated** — 3+ KPIs match Phase 1/2 spot-checks ±0.1%
- [ ] All filters tested — independence, combinations, edge cases
- [ ] Performance baseline recorded — queries < 5 sec, load < 5 sec
- [ ] No console errors (F12 → Console)
- [ ] **User approved** — feedback resolved
- [ ] Mobile tested (if Phase 1 required)
- [ ] `state.md` updated with Phase 3 block (append only)

---

## Key Reference Materials

| I want to... | See... |
|---|---|
| **Copy dashboard templates** | `references/rendering/html-client/templates/` (see How to Execute block above for exact `cp` commands) |
| **Execute any Phase 3 step** | [`references/steps.md`](references/steps.md) |
| **Run testing checklist** | [`testing-troubleshooting.md`](references/testing-troubleshooting.md) |
| **Troubleshoot blank/wrong dashboard** | [`testing-troubleshooting.md`](references/testing-troubleshooting.md) |
| **Understand Non-Workflow vs Workflow architecture** | "Key Concept" section above (this file) |
| **See all reference files** | [`references/INDEX.md`](references/INDEX.md) |
| **HTML Client engine details** | [`references/rendering/html-client/SKILL.md`](references/rendering/html-client/SKILL.md) |

---

## Phase 3 Deliverable

At end of Phase 3, user receives:

✅ **Live interactive dashboard** (`dashboard.html`, opens in any browser)
✅ **Error handling configured** (timeouts, nulls, zero results)
✅ **Visual design validated** (matches Phase 1 mockup)
✅ **All filters working correctly** (date, dimensions, combinations, drill-down)
✅ **Data accuracy certified** (spot-checked against Phase 1/2)
✅ **Performance baseline established** (queries < 5 sec, load < 5 sec)
✅ **Mobile/responsive validated** (if Phase 1 required)
✅ **User satisfied** (approved or looped back to fix)
✅ **Technical documentation** (parameters recorded in `state.md`)

**→ Ready for optional Phase 4 (automate & deploy) or Phase 5 (handoff documentation)**

---


### ℹ️ Self-Contained: No Server or Hosting Required

**dashboard.html is completely self-contained:**

✅ All data is inlined (no external queries)  
✅ All code is inlined (no external scripts or CDN calls)  
✅ Works offline once downloaded  
✅ No authentication or credentials needed at runtime  

**How to use:**
- **Desktop:** Double-click `dashboard.html` to open in browser
- **Team share:** Email the file, recipient double-clicks to open
- **Archive:** ZIP it with supporting docs (knowledge/, deployment-checklist.md)
- **Version control:** Commit to Git as a binary artifact

**NOT required:**
- ❌ Web server (Nginx, Apache, Node.js)
- ❌ Database connection at runtime
- ❌ Hosting platform (Heroku, Vercel, AWS)
- ❌ CI/CD pipeline for deployment

**If you DO want a server:** `npx serve .` is optional for local testing/sharing, but not necessary for production use.

---


## Next Phase

### ➡ Route to Phase 4 (Optional)
**Track A:** reusable skill extraction wanted → package the HTML Client artifacts
**Track B:** AI agent scoped in Phase 1 → deploy Foundry agent
**Next:** `../phase-4/automate-deploy-guide.md`

### ➡ Route to Phase 5 (Optional)
**Condition:** User wants local handoff docs
**Next:** `../phase-5/handoff-documentation-guide.md`

### ➡ Close (if no Phase 4/5)
Mark engagement complete, share the final `dashboard.html`.

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
