# Filter Architecture Patterns

Design patterns for dashboard filters in HTML Client dashboards — a single portable `dashboard.html` file with no backend, no live queries at runtime.

---

## Golden Rules: BEFORE You Build ANY Filters

### Rule 1: Design Filter Architecture BEFORE Coding

**Anti-pattern:** Build dashboard → Test → Realize filters don't work → Remove filters

**Correct Pattern:** Design → Query real data → Validate → Build

```
❌ WRONG Timeline:
Week 1: Build dashboard with all filters
Week 2: Test - Status works, but Status+Channel broken
Week 3: Remove Channel filter to "fix" it
Result: Features removed, wasted effort, rebuilt later

✅ RIGHT Timeline:
Week 1: Query all filter combinations
Week 2: Validate combinations exist in database
Week 3: Build dashboard with working filters
Week 4: Iterate based on user feedback (not rework)
```

**Why this matters:**
- Architectural decisions made upfront
- All filter combinations verified before code
- No surprises during implementation

---

### Rule 2: Don't Remove Filters to Simplify

**If a filter doesn't work, FIX it—don't delete it.**

**Red flags - Stop immediately if you hear:**
- "This dashboard is getting too complex"
- "Let's focus on just one filter"
- "We can add the others later"
- "I removed X filter because it was breaking"

**Reality:**
- Promising features in design then removing = broken trust
- "Later" usually means never
- One filter is often insufficient for analysis
- Removing filters masks architectural problems

**Solution - Fix the architecture, not the feature:**
- If too many filters → simplify the UI (collapsible sections, tabs)
- If performance issues → pre-aggregate more in `generate-data.js`, not remove filters
- If confusing → add help text, not remove functionality
- If broken → fix the data structure or query logic

---

### Rule 3: Every Filter Must Have Database Support

**Before adding a filter to the UI, verify it's queryable:**

```sql
-- If you want a "Region" filter, this query must work:
SELECT region, COUNT(*), SUM(amount)
FROM bookings
GROUP BY region
-- Must return: US, EU, APAC, LATAM (all regions users need)

-- If you want "Status + Channel" filters together, test:
SELECT status, channel, COUNT(*), SUM(amount)
FROM bookings
GROUP BY status, channel
-- Must return: All combinations with non-zero data
```

**Don't assume combinations exist:**
```sql
-- Status = "Pending" exists? ✓
SELECT COUNT(*) FROM bookings WHERE status = 'Pending'

-- Status = "Pending" + Channel = "Web" exists? Must test!
SELECT COUNT(*) FROM bookings 
WHERE status = 'Pending' AND channel = 'Web'
-- If this returns 0 → This combination doesn't exist!
-- Must document or provide different UI
```

---

## Three-Level Filter Hierarchy (ALL STACKABLE)

Dashboard filters operate at three levels, all of which can be applied simultaneously and stacked via AND logic.

### Level 1: Global Filters (Apply to ALL Widgets Across ALL Tabs)

- **Scope:** Every widget on every tab
- **Examples:** Date Range, Region, Company
- **Query impact:** Added to WHERE clause on all queries
- **When to use:** Filters users want to apply universally (time, organization, status)

```javascript
// Global filter applied to all data
const baseData = RAW.detail.filter(r =>
  r.date >= globalDateStart && r.date <= globalDateEnd &&
  (globalRegion === 'all' || r.region === globalRegion)
);

// Both widgets on Tab 1 use baseData
const tab1Widget1 = baseData.filter(...tab filters...).filter(...widget filters...);
const tab1Widget2 = baseData.filter(...tab filters...).filter(...widget filters...);

// Both widgets on Tab 2 use same baseData
const tab2Widget1 = baseData.filter(...tab filters...).filter(...widget filters...);
```

### Level 2: Tab Filters (Apply to ALL Widgets WITHIN That Tab ONLY)

- **Scope:** Only widgets on that specific tab
- **Examples:** Tab 1: Category | Tab 2: Customer Segment | Tab 3: Product Type
- **Query impact:** Added to WHERE clause only for that tab's queries
- **Other tabs:** Completely unaffected by this tab's filters
- **When to use:** Filters specific to a tab's analysis domain

```javascript
// Global filter + Tab filter (only for Tab 2)
const tab2Data = baseData.filter(r =>
  r.category === tab2SelectedCategory  // Tab-level filter
);

// All Tab 2 widgets use tab2Data
const tab2Widget1 = tab2Data.filter(...widget1 filters...);
const tab2Widget2 = tab2Data.filter(...widget2 filters...);

// Tab 1 & Tab 3 unaffected by tab2SelectedCategory
const tab1Data = baseData.filter(...);  // No category filter
const tab3Data = baseData.filter(...);  // No category filter
```

### Level 3: Widget Filters (Apply to ONLY That Single Widget — EMBEDDED, NOT EXPOSED)

- **Scope:** Only that one widget
- **CRITICAL: Embedded in widget config, NOT shown as separate interactive controls**
- **Examples:** 
  - KPI card: "exclude cancelled orders" (embedded rule)
  - Chart: "only show revenue > $100" (embedded rule)
  - Table: "hide test accounts" (embedded rule)
- **NOT exposed to users as:** Dropdown filters, checkboxes, or date pickers
- **Query impact:** Added to WHERE clause only for that widget's query
- **Other widgets:** Completely unaffected by this widget's filter
- **When to use:** Widget-specific business rules or exclusions (not user-selectable options)
- **Why embedded?** Prevents confusion — users only see global + tab filters in the UI. Widget rules are configuration, not interactive filters.

```javascript
// Global + Tab + Widget filters (all three levels)
// But widget filters are EMBEDDED in generate-data.js, not exposed as UI controls

// Widget 1: KPI card (embedded rule: exclude cancelled)
const widget1Data = tab2Data.filter(r =>
  r.status !== 'cancelled'  // Widget-level filter (EMBEDDED, not shown to user)
);

// Widget 2: Chart (embedded rule: only high-value transactions)
const widget2Data = tab2Data.filter(r =>
  r.amount > 1000  // Widget-level filter (EMBEDDED, not shown to user)
);

// Widget 3: Table (no widget filter — uses all tab data)
const widget3Data = tab2Data;
```

**What users see in the UI:**
```
┌─────────────────────────────────────────────┐
│  🌍 Global Filters (visible, interactive)   │
│  [ Date: Jul 2026 ] [ Region: US ]          │
└─────────────────────────────────────────────┘
│
│  Tab 1 | Tab 2 [✓] | Tab 3
│
│  ┌──────────────────────────────────────────┐
│  │ Tab 2 Filters (visible, interactive)     │
│  │ [ Category: Electronics ]                 │
│  └──────────────────────────────────────────┘
│
│  ┌──────────────────┐  ┌──────────────────┐
│  │ Widget 1: KPI    │  │ Widget 2: Chart  │
│  │ (hidden rule:    │  │ (hidden rule:    │
│  │  no cancelled)   │  │  amount > $1000) │
│  └──────────────────┘  └──────────────────┘
│
│  ┌──────────────────────────────────────────┐
│  │ Widget 3: Table (no special rules)       │
│  └──────────────────────────────────────────┘
```

**What's NOT in the UI:**
- ❌ No "Widget Status" dropdown
- ❌ No "Widget Amount" slider
- ❌ Widget rules are configuration, not interactive controls
- ✅ Users only interact with Global + Tab filters

### Filter Stacking: Combining All Three Levels

All three levels stack via AND logic — users can apply filters at any/all levels simultaneously.

**Example: Complex Filter Stack**
```javascript
const filteredData = RAW.detail
  // Level 1: Global filters (Date + Region)
  .filter(r => r.date >= globalDateStart && r.date <= globalDateEnd && r.region === globalRegion)
  // Level 2: Tab filter (Category)
  .filter(r => r.category === tab2SelectedCategory)
  // Level 3: Widget filter (Status exclusion)
  .filter(r => r.status !== 'cancelled');

// Result: Show revenue for selected date, region, AND category, AND exclude cancelled
```

**Query impact:** WHERE clause becomes:
```sql
WHERE date >= '2026-07-01' 
  AND date <= '2026-07-31' 
  AND region = 'US' 
  AND category = 'Electronics' 
  AND status != 'cancelled'
```

### Design Principle: Always Ask "Can These Be Stacked?"

During Phase 1 Step 1c (Filter Design):
- Always assume filters CAN be applied simultaneously
- Verify filter combinations in database (don't assume they exist)
- Document which combinations are meaningful vs rare

---

## CRITICAL: Data Architecture for Filters — Row-Level vs Pre-Aggregated

⚠️ **The single most important decision before building a filtered dashboard is whether `generate-data.js` embeds row-level detail data or pre-aggregated constants.**

### When to Use Each Pattern

| Requirement | Use | Data Structure | Re-slice on Filter Change |
|-------------|-----|-----------------|--------------------------|
| **No filters; read-only summary** | Pre-aggregated constants | `{total_customers: 1000, segments: ['Gold', 'Silver']}` | ❌ No — display is static |
| **Dashboard has ANY filter** | Row-level data | `[{cust_id: 1, segment: 'Gold', revenue: 100}, ...]` | ✅ Yes — re-aggregate on every filter change |

### Anti-Pattern: Embedded Pre-Aggregated with Filters

**This SILENTLY BREAKS filters:**

```javascript
// ❌ WRONG — Data pre-aggregated per filter, independently
const RAW = {
  // Pre-aggregated by segment only
  by_segment: [
    {segment: 'Gold', revenue: 150000},
    {segment: 'Silver', revenue: 80000}
  ],
  // Pre-aggregated by churn only
  by_churn: [
    {churn_risk: 'High', revenue: 100000},
    {churn_risk: 'Low', revenue: 130000}
  ]
};

// Filter for segment='Gold' works ✓
// Filter for churn='High' works ✓
// Filter for segment='Gold' + churn='High' DOESN'T WORK ❌
// Because there's no intersection data — can't re-aggregate
```

### Correct Pattern: Row-Level Data with Client-Side Re-Aggregation

**When the dashboard has filters, `generate-data.js` should embed row-level data:**

```javascript
// ✅ CORRECT — Row-level data with ALL filter dimensions
const RAW = {
  detail: [
    {cust_id: 1, segment: 'Gold', churn_risk: 'Low', revenue: 100},
    {cust_id: 2, segment: 'Gold', churn_risk: 'High', revenue: 150},
    {cust_id: 3, segment: 'Silver', churn_risk: 'Low', revenue: 80},
    {cust_id: 4, segment: 'Silver', churn_risk: 'High', revenue: 50},
    // ... all raw rows from SINK/source table
  ]
};

// Filter state
var filterSegment = 'all', filterChurn = 'all';

// Re-aggregate on every filter change
function updateDashboard() {
  // Start with FULL detail array
  let rows = RAW.detail;
  
  // Apply BOTH filters
  if (filterSegment !== 'all') rows = rows.filter(r => r.segment === filterSegment);
  if (filterChurn !== 'all') rows = rows.filter(r => r.churn_risk === filterChurn);
  
  // Re-compute ALL metrics from filtered rows
  const totalRevenue = rows.reduce((sum, r) => sum + r.revenue, 0);
  const bySegment = rows.reduce((acc, r) => {
    acc[r.segment] = (acc[r.segment] || 0) + r.revenue;
    return acc;
  }, {});
  
  renderCards({total: totalRevenue});
  renderChart(bySegment);
}
```

### Data Size Guidelines

| Data Volume | Recommendation | Storage Method |
|-------------|----------------|------------------|
| < 5,000 rows | Embed all rows directly in `dashboard.html` | JSON constants injected by `generate-data.js` |
| 5,000–50,000 rows | Embed in optimized format (numbers only, no strings) | Compressed/columnar JSON |
| > 50,000 rows | Pre-aggregate more in SQL — don't embed raw rows | See Payload Size Budget in `steps.md` Step 4d |

**For HTML Client dashboards:** SINK/source tables typically deliver 100–5,000 rows per query. Use row-level embedding with pre-aggregated totals as a fallback for KPI cards:

```javascript
const RAW = {
  // Pre-validated grand total from Stage B / Phase 2 (NOT computed client-side)
  totals: {
    unique_customers: 5420,
    total_revenue: 2840000
  },
  // Row-level detail data (for filter re-slicing)
  detail: [
    {segment: 'Gold', customer_id: 1001, revenue: 450},
    {segment: 'Gold', customer_id: 1002, revenue: 320},
    // ... all ~5000 rows
  ]
};

// KPI cards: Use totals when no filter is active
// Charts: Re-aggregate from detail when filters change
```

---

## Pre-Code Design Phase (CRITICAL)

**Before writing ANY code, answer these questions:**

### Question 1: How many filters?

List every filter user will need:
```
Filter 1: Status (Completed, Pending, Cancelled, Failed) = 4 values
Filter 2: Channel (Web, App, Phone, Agent) = 4 values
Filter 3: Type (Flight, Hotel, Package, CarRental) = 4 values
Filter 4: Loyalty (Platinum, Gold, Silver, Member, None) = 5 values

Total Combinations = 4 × 4 × 4 × 5 = 320
```

**Decision based on combinations:**
- **< 1,000 combinations, < 5,000 detail rows** → Embed the full detail array in `dashboard.html`, filter client-side ✓ (the standard HTML Client pattern)
- **Larger than that** → Pre-aggregate harder in `generate-data.js` (fewer dimensions, coarser grouping) before embedding — a static file has no server to fall back on

---

### Question 2: Do filters work independently?

```
✅ YES - "Show Status=Completed alone" works
✅ YES - "Show Channel=Web alone" works
✅ YES - "Show Status=Completed + Channel=Web" works

❌ NO - Status filter works but breaks when Channel added
❌ NO - Removing filters makes other filters work again
```

If combinations don't work in database queries, they won't work in UI.

---

### Question 3: Are they properly joined in the database?

```sql
❌ WRONG - Query dimensions separately:
SELECT status, COUNT(*) FROM bookings GROUP BY status
SELECT channel, COUNT(*) FROM bookings GROUP BY channel
-- Can't combine results meaningfully

✅ RIGHT - Query all dimensions together:
SELECT status, channel, COUNT(*)
FROM bookings
GROUP BY status, channel
-- Can filter any combination
```

---

### Question 4: Will this scale?

```
Detail rows < 5,000?   → Embed full detail array, filter client-side
Detail rows 5k-50k?    → Embed in a compact/numeric-only format
Detail rows > 50k?     → Pre-aggregate harder in SQL before embedding
```

---

## Core Filter Types

All examples below are vanilla HTML/JS — the only rendering target for this skill. Data is always pre-embedded by `generate-data.js`; there is no live query at runtime.

### 1. Single-Select Filter (Dropdown)

**Use case:** Choose one value (region, product, year)

```html
<select id="region-filter" onchange="updateDashboard()">
  <option value="US" selected>US</option>
  <option value="EU">EU</option>
  <option value="APAC">APAC</option>
  <option value="LATAM">LATAM</option>
</select>
```

---

### 2. Multi-Select Filter

**Use case:** Choose multiple values (multiple regions, products)

```html
<select id="regions-filter" multiple onchange="updateDashboard()">
  <option value="US" selected>US</option>
  <option value="EU" selected>EU</option>
  <option value="APAC">APAC</option>
  <option value="LATAM">LATAM</option>
</select>

<script>
function getSelectedRegions() {
  return Array.from(document.getElementById('regions-filter').selectedOptions).map(o => o.value);
}

function updateDashboard() {
  const regions = getSelectedRegions();
  const rows = RAW.detail.filter(r => regions.includes(r.region));
  renderDashboard(rows);
}
</script>
```

---

### 3. Date Filter

**Use case:** Choose a date range

```html
<input type="date" id="start-date" onchange="updateDashboard()">
<input type="date" id="end-date" onchange="updateDashboard()">

<script>
function updateDashboard() {
  const start = document.getElementById('start-date').value;
  const end = document.getElementById('end-date').value;
  const rows = RAW.detail.filter(r => r.date >= start && r.date <= end);
  renderDashboard(rows);
}
</script>
```

---

### 4. Search/Type-Ahead Filter

**Use case:** Search for customer, product, or ID within the already-embedded detail array

```html
<input type="text" id="search-box" placeholder="Search customers..." oninput="updateDashboard()">

<script>
function updateDashboard() {
  const term = document.getElementById('search-box').value.trim().toLowerCase();
  const rows = term
    ? RAW.detail.filter(r => r.customer_name.toLowerCase().includes(term))
    : RAW.detail;
  renderDashboard(rows);
}
</script>
```

**Note:** Because there is no backend, search only matches rows already embedded in `RAW.detail` — it is not a live database search. If the detail array is too large to embed (see Data Size Guidelines above), pre-aggregate harder in `generate-data.js` rather than trying to add server-side search to a static file.

---

### 5. Slider Filter

**Use case:** Select a range of numeric values (price, quantity)

```html
<input type="range" id="price-min" min="0" max="1000" value="0" oninput="updateDashboard()">
<input type="range" id="price-max" min="0" max="1000" value="1000" oninput="updateDashboard()">
<span id="price-range-label"></span>

<script>
function updateDashboard() {
  const min = Number(document.getElementById('price-min').value);
  const max = Number(document.getElementById('price-max').value);
  document.getElementById('price-range-label').textContent = `$${min} – $${max}`;
  const rows = RAW.detail.filter(r => r.price >= min && r.price <= max);
  renderDashboard(rows);
}
</script>
```

---

## Filter Architecture Patterns

### Pattern 0: HTML Client Detail Array Pattern (CRITICAL for Stacking)

**The standard pattern for any HTML Client dashboard with 2+ filters**

❌ **WRONG — filters don't stack:**
```javascript
// Each filter reads its own pre-aggregated array
const RAW = {
  by_segment: [
    {segment: 'Premium', revenue: 150000},
    {segment: 'Standard', revenue: 80000}
  ],
  by_churn: [
    {churn_risk: 'High', revenue: 100000},
    {churn_risk: 'Low', revenue: 130000}
  ]
};

// Selecting segment='Premium' AND churn='High' doesn't intersect!
// Each reads its own array, ignoring the other filter
```

✅ **CORRECT — single detail array with ALL filter dimensions:**
```javascript
// ONE detail-level array with ALL filter columns
const RAW = {
  detail: [
    {segment: 'Premium', churn_risk: 'High', make: 'Toyota', revenue: 45000},
    {segment: 'Premium', churn_risk: 'Low', make: 'Honda', revenue: 60000},
    {segment: 'Standard', churn_risk: 'High', make: 'Toyota', revenue: 25000},
    // ... every combination of filter dimensions
  ]
};

// Filter implementation:
let filterSegment = 'all', filterChurn = 'all', filterMake = 'all';

function updateDashboard() {
  // ALWAYS filter from detail array FIRST
  const rows = RAW.detail.filter(r =>
    (filterSegment === 'all' || r.segment === filterSegment) &&
    (filterChurn === 'all' || r.churn_risk === filterChurn) &&
    (filterMake === 'all' || r.make === filterMake)
  );
  
  // Re-compute ALL KPIs, charts, tables from filtered rows
  const totalRevenue = rows.reduce((sum, r) => sum + r.revenue, 0);
  const bySegment = rows.reduce((acc, r) => {
    acc[r.segment] = (acc[r.segment] || 0) + r.revenue;
    return acc;
  }, {});
  
  renderDashboard(totalRevenue, bySegment, rows);
}

// Filter state changes trigger full re-render
```

**Why this matters:**
- Pre-aggregating by filter breaks combinations (Segment=Premium + Churn=High intersection disappears)
- A single detail array lets ANY filter combination work by design
- Never pre-aggregate per-filter for HTML Client dashboards

---

### Pattern 1: Independent Filters

Filters don't depend on each other — all filter against the same `RAW.detail` array.

```
┌─ Region ──────┐
│ [US  EU APAC] │
└────────────────┘

┌─ Product ─────┐
│ [A  B  C  D]  │
└────────────────┘

┌─ Date Range ──┐
│ [2026-01-01 to 2026-06-09] │
└────────────────┘

Filter: RAW.detail.filter(r => regions.includes(r.region) && products.includes(r.product) && r.date >= start && r.date <= end)
```

---

### Pattern 2: Cascading Filters

Filter options depend on previous selections. Since there is no live query, cascading options must be pre-computed from `RAW.detail` in JS.

```
┌─ Region ──────────┐
│ [US EU APAC LATAM]│
└────────────────────┘
         ↓
    (user selects US)
         ↓
┌─ States ──────────────────────┐
│ [CA TX NY FL ... ] (US only)   │
└────────────────────────────────┘
```

```javascript
function updateStateOptions(region) {
  // Derive distinct states for this region from the embedded detail array —
  // never a live query, since dashboard.html has no database connection
  const states = [...new Set(RAW.detail.filter(r => r.region === region).map(r => r.state))].sort();
  const select = document.getElementById('state-filter');
  select.innerHTML = states.map(s => `<option value="${s}">${s}</option>`).join('');
}

document.getElementById('region-filter').addEventListener('change', e => {
  updateStateOptions(e.target.value);
  updateDashboard();
});
```

---

### Pattern 3: Default Filters (Pre-filtered)

Dashboard loads with filters already applied.

```javascript
// Example: "Last 30 days" is default
let filters = {
  dateStart: RAW.meta.data_end_minus_30d,  // pre-computed by generate-data.js
  dateEnd: RAW.meta.data_end,
  region: 'all',
  status: 'completed'
};

function applyDefaultFilters() {
  document.getElementById('start-date').value = filters.dateStart;
  document.getElementById('end-date').value = filters.dateEnd;
  updateDashboard();
}
```

---

### Pattern 4: Quick Filters (Presets)

Pre-built filter combinations for common use cases.

```javascript
const quickFilters = {
  'Last 30 Days':  { dateStart: RAW.meta.data_end_minus_30d, dateEnd: RAW.meta.data_end },
  'Completed Only': { status: 'completed' },
  'Top Regions':   { regions: ['US', 'EU', 'APAC'] }
};

function applyQuickFilter(name) {
  Object.assign(filters, quickFilters[name]);
  updateDashboard();
}
// <button onclick="applyQuickFilter('Last 30 Days')">Last 30 Days</button>
```

---

### Pattern 5: Filter State Persistence

Remember filter selections when navigating tabs.

```javascript
var filters = {
  region: 'US',
  product: 'A',
  dateStart: '2026-01-01',
  dateEnd: '2026-06-09'
};

function switchTab(tabName) {
  // Filters persist in the shared `filters` object
  showTab(tabName);
  // Re-apply filters to the newly-shown tab's widgets
  updateTabData(tabName, filters);
}
```

---

## Filter Design Checklist

For EACH filter in dashboard:

- [ ] **Purpose clear** — Why does this filter exist?
- [ ] **Default value set** — What's the sensible default?
- [ ] **Mutually exclusive?** — Can filters conflict?
- [ ] **Cascading?** — Does this filter depend on another?
- [ ] **Performance** — Filter change updates in < 1 second? (should be near-instant — no runtime query)
- [ ] **Error handling** — What if filter returns no data?
- [ ] **Empty state** — How does dashboard handle zero results?
- [ ] **Labels clear** — Is it obvious what this filter does?

---

## Common Filter Mistakes

### Too many filters
```
[Region] [Product] [Date] [Status] [Segment] [Channel] [Cohort] ...
```
**Problem:** Users overwhelmed  
**Fix:** 3-5 filters max

---

### Filters that don't work
```javascript
// ❌ BAD - filter UI exists but the handler never re-renders
document.getElementById('region-filter').addEventListener('change', e => {
  // forgot to call updateDashboard()!
});

// ✅ GOOD - filter change re-filters RAW.detail and re-renders
document.getElementById('region-filter').addEventListener('change', e => {
  filters.region = e.target.value;
  updateDashboard();
});
```

---

### No default value
**Problem:** Dashboard loads showing all data at once (visually noisy)
**Fix:** Always set a default (e.g., last 30 days) and apply it on page load

---

### Conflicting filters
```javascript
// ❌ BAD
startDate = '2026-06-09'
endDate = '2026-01-01'  // Before start!

// ✅ GOOD - validate
if (endDate < startDate) {
  [startDate, endDate] = [endDate, startDate];
  showWarning('Dates swapped');
}
```

---

### Filter doesn't persist on tab switch
```javascript
// ❌ BAD - filters reset when switching tabs
function switchTab(tab) {
  filters = {}; // RESET!
  renderTab(tab);
}

// ✅ GOOD - preserve filters
function switchTab(tab) {
  renderTab(tab, filters); // Pass filters through
}
```

---

## Filter Performance Optimization

Since all data is pre-embedded by `generate-data.js`, filter changes should always be near-instant (client-side array filtering, no network round-trip). If a filter feels slow:

### Detail array too large
```javascript
// ❌ BAD — re-scanning 50,000 rows on every keystroke of a search box
document.getElementById('search-box').addEventListener('input', updateDashboard);

// ✅ GOOD — debounce, and/or pre-aggregate the detail array smaller in generate-data.js
let debounceTimer;
document.getElementById('search-box').addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(updateDashboard, 150);
});
```

### Cascading filter options recomputed every render
```javascript
// ❌ BAD - recompute distinct states from scratch on every filter change
function updateStateOptions(region) {
  const states = [...new Set(RAW.detail.filter(r => r.region === region).map(r => r.state))];
  // ...
}

// ✅ GOOD - pre-compute the region→states map once in generate-data.js, embed it directly
const statesByRegion = RAW.meta.states_by_region; // {'US': ['CA','TX',...], ...}
function updateStateOptions(region) {
  renderStateOptions(statesByRegion[region] || []);
}
```

---

## Filter Client-Side Patterns (JS array filtering, no SQL at runtime)

### Single-Select Filter
```javascript
const rows = region === 'all' ? RAW.detail : RAW.detail.filter(r => r.region === region);
```

### Multi-Select Filter
```javascript
const rows = RAW.detail.filter(r => selectedProducts.includes(r.product));
```

### Date Range Filter
```javascript
const rows = RAW.detail.filter(r => r.date >= startDate && r.date <= endDate);
```

### Combined Filters
```javascript
const rows = RAW.detail.filter(r =>
  (regions.length === 0 || regions.includes(r.region)) &&
  (products.length === 0 || products.includes(r.product)) &&
  r.date >= startDate && r.date <= endDate &&
  (status === 'all' || r.status === status)
);
```

---

## Filter State Management

```html
<div class="filters">
  <select id="region" onchange="updateDashboard()">
    <option value="all">All Regions</option>
    <option value="US">US</option>
    <option value="EU">EU</option>
  </select>

  <input type="date" id="startDate" onchange="updateDashboard()">
  <input type="date" id="endDate" onchange="updateDashboard()">
</div>

<script>
var filters = { region: 'all', startDate: RAW.meta.data_start, endDate: RAW.meta.data_end, status: 'all' };

function updateDashboard() {
  filters.region = document.getElementById('region').value;
  filters.startDate = document.getElementById('startDate').value;
  filters.endDate = document.getElementById('endDate').value;

  const rows = RAW.detail.filter(r =>
    (filters.region === 'all' || r.region === filters.region) &&
    r.date >= filters.startDate && r.date <= filters.endDate
  );
  renderCharts(rows);
}
</script>
```

---

## When to Use Each Filter Type

| Filter Type | Data | Example | Rendering Time |
|-------------|------|---------|-----------------|
| Dropdown | Static or small | Region, Status | Instant |
| Multi-Select | Static or small | Multiple regions | < 100ms |
| Date Range | Embedded detail array | Date range | < 100ms |
| Search | Embedded detail array | Customer name | < 100ms (debounce if array is large) |
| Slider | Numeric range | Price range | < 100ms |

---

## Testing Filters

For EACH filter (reference: `testing-troubleshooting.md`):

- [ ] Filter alone works
- [ ] Filter with another works
- [ ] All filters together work
- [ ] Filter reset returns to initial
- [ ] Empty results shows message
- [ ] Filter persists on tab switch
- [ ] Filter state preserved across page reloads
- [ ] Performance acceptable (near-instant — no runtime query)

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
