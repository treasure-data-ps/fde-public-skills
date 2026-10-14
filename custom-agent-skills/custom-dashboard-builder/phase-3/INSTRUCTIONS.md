---
name: phase-3-instructions
description: Phase 3 specific instructions for interactive dashboard building
priority: HIGH
load_order: 1.3
---

# Phase 3 Instructions — Build Interactive Dashboard

**Read this BEFORE `./SKILL.md`.**

**Phase 3 is MANDATORY for all projects (after Phase 1, optionally Phase 2).**

---

## Phase 3 Goal

Build a single portable `dashboard.html` file that:
- Queries either SINK tables (Phase 2 output) or source tables directly
- Renders interactive filters, charts, and KPI cards
- Opens standalone in a browser (no server required)
- Contains all data inlined (no separate API calls)

**Deliverable:** 
- User-approved interactive `dashboard.html`
- state.md appended with Phase 3 results

---

## Pre-Build Setup

**Before starting dashboard build, re-read styling reference:**
- **`../references/treasure-data-theme.md`** — Brand colors, fonts, component styles (396 lines)

---

## Pre-Execution Validation (Checkpoint)

**Cannot execute Phase 3 without validating:**

From `state.md` Phase 1 section, verify:
- ✅ Phase 1 marked ✅ Complete
- ✅ KPIs documented are still relevant
- ✅ Data sources accessible (database, tables still exist)

From `state.md` Phase 2 section (if applicable), verify:
- ✅ Phase 2 marked ✅ Complete (if Workflow path chosen)
- ✅ SINK tables created and populated

**Runtime validation before rendering:**
```bash
# If Phase 2 (Workflow path):
tdx describe <SINK_DB>.<SINK_table>
SELECT COUNT(*) FROM <SINK_DB>.<SINK_table>  # Verify populated

# If Phase 2 skipped (Non-Workflow path):
tdx describe <SOURCE_DB>.<source_table>
SELECT COUNT(*) FROM <SOURCE_DB>.<source_table>  # Verify data exists
```

**If ANY validation FAILS:**
→ STOP: "Data source validation failed: [reason]"
→ User action: Verify workflow ran (if Phase 2), or confirm source data accessible

---

## Quick Checklist (Quick Reference)

**Pre-Phase-3 Gate**
- [ ] Phase 1 complete (database, tables, metrics, dimensions validated)
- [ ] Phase 2 skipped OR complete (SINK tables ready if done)
- [ ] state.md updated with all findings
- [ ] Rendering engine: HTML Client
- [ ] Path confirmed: query source tables OR query SINK tables

**Dashboard Build Steps**
- [ ] 4b: Write SQL for each widget/KPI (< 5s target)
- [ ] 4c: Build HTML structure (filters, widgets, tabs)
- [ ] 4d: Write generate-data.js, customize queries
- [ ] 4e: Render, validate (open in browser, check for data)
- [ ] 4e-VALIDATE: **Completeness check** (all tabs/filters/widgets from Phase 1 plan present?) ← NEW GATE
- [ ] 4f-4l: Validate data accuracy, test filters, check performance

**Quality Gate (Before Approval)**
- [ ] **Dashboard completeness validated** (all tabs/filters/widgets from Phase 1 plan present) ← GATE 1
- [ ] **Filter architecture correct** (two-tier pattern: global date + per-tab dimensions) 
  - [ ] Date filter wired to all KPI cards + trend chart
  - [ ] Dimension filters wired to active tab widgets only
  - [ ] Cross-filter rule applied (breakdown charts exclude own dimension)
- [ ] **Filter granularity validated** (filter options match Phase 1 plan) ← GATE 2a
- [ ] **Filter scope & binding tested** (filters work independently + in combination) ← GATE 2b
- [ ] **All three data shapes generated** (daily-nodim, all-time-dim, monthly-dim) ← NEW
  - [ ] Breakdown charts respond to BOTH date + dimension filters
- [ ] **Monthly cardinality validated** (no silent truncation; LIMITs set to 2× expected rows)
- [ ] **Non-additive metrics handled** (COUNT DISTINCT columns documented + properly sourced)
- [ ] **Payload budget pre-calculated** (documented in state.md; < 2 MB total)
- [ ] **Known limitations annotated** (all limited widgets have .widget-note)
- [ ] **Spot-checks passed** (3+ KPIs verified ±0.1% accuracy against SOURCE data) ← GATE 3
- [ ] **Filter combos tested** (2–3 random dimension + date filter combinations verified) ← GATE 3b
- [ ] All metrics match Phase 1/2 confirmed values
- [ ] Performance acceptable (queries < 5s, load < 5s)
- [ ] No console errors (F12 → Console)
- [ ] Responsive design tested (if required)

**Customer Approval**
- [ ] Show dashboard summary to user
- [ ] Get approval: "Does this meet your needs?"
- [ ] If NO → iterate, re-test, re-ask
- [ ] If YES → record sign-off, proceed to Phase 4/5 or close

**Post-Approval**
- [ ] Update state.md: "Phase 3 — Complete"
- [ ] Optionally proceed to Phase 4 (automation/agent)
- [ ] Optionally proceed to Phase 5 (handoff docs)
- [ ] Or close out and share dashboard.html

---

---

## ✅ Before You Proceed: Required Reads

**Before executing Phase 3 dashboard build (step 3a), read these reference files IN THIS ORDER:**
1. **`../references/treasure-data-theme.md`** — Brand colors, fonts, component styles (if not already read in root SKILL.md)
2. **`./references/filter-architecture.md`** — Complete filter design patterns, cross-tab filter logic, dimension interaction rules (763 lines) — **READ BEFORE building filters**
3. **`./references/rendering/html-client/html-dashboard-patterns.md`** — Standard HTML dashboard patterns and component structure (22K)
4. **`./references/rendering/html-client/templates/generate-data.js`** — Reference data generation script template (243 lines) — **READ BEFORE writing your generate-data.js**

**Why these reads matter:**
- `filter-architecture.md` prevents filter granularity mismatches (month vs daily), tab-scope binding issues, and COUNT DISTINCT edge cases
- `html-dashboard-patterns.md` prevents re-inventing HTML structure; templates already encode responsive design, error handling, and performance optimization
- `generate-data.js` template prevents custom fan-out guards, querySrc patterns, and size-detection logic already built into the reference

---

---


## ⚠️ Blocking Phase 3 Gate

Before declaring the dashboard complete, verify the Phase 3 section of `../references/execution-contract.md`: completeness, standalone HTML, 3+ source KPI spot-checks, filter-combination tests, and explicit user approval. A draft review is not final approval.

## Phase 3 Specific Rules (In Addition to Universal Rules)

### Rule P3-1: Query Source Decision

Before writing any Phase 3 query, decide:

**Option A: Query SINK Tables (Phase 2 completed)**
```sql
-- Phase 2 created pre-aggregated SINK tables
SELECT * FROM <db>.<project_name>_sink_revenue
WHERE date >= '2026-07-01'
ORDER BY date DESC
```
✅ **Advantages:** Fast, pre-aggregated, optimized
❌ **Constraints:** Depends on Phase 2 completing successfully

**Option B: Query Source Tables Directly (Phase 2 skipped)**
```sql
-- Phase 3 does the aggregation on-the-fly
SELECT 
  DATE(event_time) AS date,
  region,
  SUM(revenue) AS total_revenue
FROM source_events
WHERE event_time >= CURRENT_DATE - INTERVAL 30 DAY
GROUP BY DATE(event_time), region
ORDER BY date DESC, region
```
✅ **Advantages:** No Phase 2 setup needed
❌ **Constraints:** Slower if high-volume data, may need query optimization

**Decision tree:**
```
Phase 2 completed?
  YES → Use SINK tables (faster)
  NO  → Query source tables directly (slower, but works)
```

---

### Rule P3-2: Query Execution & Data Validation

For every query used in dashboard:

- [ ] Execute manually first: `tdx query -f query.sql -d <database>`
- [ ] Verify results:
  - Are there rows returned? (not empty)
  - Do columns match what template expects?
  - Are numbers reasonable (not 0 or extreme)?
  - Do dates/timestamps look correct?

**Test queries before rendering:**
```bash
# Test the KPI query
tdx query --output json << 'EOF'
SELECT SUM(revenue) AS total_revenue FROM sales_table
WHERE date >= '2026-07-01'
EOF

# Expected output: {"total_revenue": 1234567.89}
# If output is null or 0, debug before rendering
```

---

### Rule P3-3: Dashboard Data Flows Through Node, Never AI

**Pattern (MANDATORY):**
```bash
# ✅ RIGHT: data → node script → dashboard.html
tdx query --output json --limit 1000 < query.sql | node render.js

# ❌ WRONG: data → AI context
# I would read the query output directly from /tmp/results.json
```

**Why:** Query results contain customer data (emails, IDs, financial info). Data must never pass through AI context. The rendering script processes it safely.

---

### Rule P3-3a: Dashboard Completeness Validation (BEFORE SPOT-CHECK)

**⚠️ CRITICAL: After rendering, validate dashboard matches Phase 1 plan. CANNOT spot-check until structure is complete.**

**Explicit Approval Gate (After rendering):**

Before proceeding to spot-checks, ask the user explicitly:

```
Does this draft look good? Shall I create the skill?

Dashboard summary:
  - Tabs: [X] | Filters: [Y] | Widgets: [Z]
  - Data size: [Xmb] | Load time: [Ys]
  - All spot-checks ready to run

To proceed, please confirm: "Yes, looks good"
```

Only after explicit confirmation proceed to completeness checks.

**Step 1: Extract dashboard plan from state.md (Phase 1)**

From `state.md` → "Dashboard Plan Summary" section, list:
- Tabs planned
- Filters planned (global + tab-specific)
- Widgets planned (chart types, metrics, dimensions)

**Example from Phase 1 plan:**
```yaml
### Dashboard Plan Summary

Tabs: 3
  - Tab 1: KPI Overview (4 cards: Revenue, Customers, AOV, Churn)
  - Tab 2: Analysis (3 charts: Revenue trend, Customer by region, Churn by segment)
  - Tab 3: Data Explorer (Orders table with search)

Global Filters: Date Range, Region (6 values), Status (2 values)

Tab 1 Filters: None (just global)
Tab 2 Filters: Category (8 values) - tab-specific only
Tab 3 Filters: Search box + Sort

Widgets:
  - KPI Card: Total Revenue (SUM(amount))
  - KPI Card: Customer Count (COUNT(DISTINCT customer_id))
  - KPI Card: AOV (AVG(amount))
  - KPI Card: Churn Rate (COUNT(churned) / COUNT(*))
  - Line Chart: Revenue by date (SUM(amount) trend)
  - Bar Chart: Revenue by region (SUM(amount) grouped)
  - Pie Chart: Churn by segment (COUNT(churned) grouped)
  - Table: Orders (all columns, searchable)
```

**Step 2: Open rendered dashboard.html in browser**

Manually check (do NOT run code, just look):
- [ ] All tabs present? (Count them: Tab 1, Tab 2, Tab 3...)
- [ ] All filters visible? (Click each filter: does it exist? Does it have options?)
- [ ] All widgets rendered? (Do you see 4 KPI cards? 3 charts? 1 table?)
- [ ] All chart types correct? (Line chart is line, not bar? Pie chart is pie, not line?)
- [ ] Filter options populated? (Region filter shows 6 options? Category shows 8?)

**Step 3: Create validation checklist**

```yaml
### Dashboard Completeness Check

**Tabs:**
- [ ] Tab 1: KPI Overview — present, clickable, shows 4 cards ✓
- [ ] Tab 2: Analysis — present, clickable, shows 3 charts ✓
- [ ] Tab 3: Data Explorer — present, clickable, shows table ✓

**Global Filters:**
- [ ] Date Range — present, functional ✓
- [ ] Region — present, shows 6 options (US, EU, APAC, LATAM, EMEA, Internal) ✓
- [ ] Status — present, shows 2 options (Active, Inactive) ✓

**Tab 1 Widgets (KPI Overview):**
- [ ] Revenue card — visible, title correct, value displays ✓
- [ ] Customer card — visible, title correct, value displays ✓
- [ ] AOV card — visible, title correct, value displays ✓
- [ ] Churn Rate card — visible, title correct, value displays ✓

**Tab 2 Widgets (Analysis):**
- [ ] Revenue Trend (Line chart) — visible, lines render, x-axis shows dates ✓
- [ ] Revenue by Region (Bar chart) — visible, bars render, 6 regions shown ✓
- [ ] Churn by Segment (Pie chart) — visible, pie slices render, 3 segments shown ✓

**Tab 2 Filters (Category):**
- [ ] Category filter — present, shows 8 options (Electronics, Clothing, ...) ✓

**Tab 3 Widgets (Data Explorer):**
- [ ] Orders table — visible, headers present, data rows visible ✓
- [ ] Search box — present, functional (type, see rows filter) ✓
- [ ] Sorting — column headers clickable (test one: click "Date", rows reorder) ✓

**Status:** ✅ All items present / ⚠️ [missing items] / ❌ [blocker items]
```

**Step 4: Compare to plan**

**If ALL items ✓:**
- Document in state.md: "Dashboard completeness check: PASSED"
- Proceed to Rule P3-4 (spot-check KPIs)

**If ANY item ⚠️ or ❌:**
- **STOP** — do not proceed to spot-check
- Identify missing filter/widget/tab
- Return to phase-3/SKILL.md and add the missing element
- Re-render dashboard.html
- Re-run completeness check
- Repeat until all items ✓

**Examples of failures (STOP and fix):**
```
❌ FAIL: Region filter missing
  → User planned "Region filter (6 values)"
  → Dashboard has no region filter
  → Must add to generate-data.js before re-rendering

❌ FAIL: Tab 2 "Category filter" not present
  → Plan said "Tab-specific Category filter"
  → Only global filters visible
  → Must add tab-scoped filter to dashboard.html

❌ FAIL: Pie chart shows only 2 segments instead of 3
  → Plan said "Churn by segment (3 segments)"
  → Dashboard shows only 2 segments
  → Data issue? Missing segment in query
  → Debug query, re-render

❌ FAIL: Search box not working
  → Plan said "Data Explorer tab with search"
  → Table loads but search box inactive
  → JavaScript error? Check browser console
  → Fix render.js, re-render
```

**Why:** Users identify missing filters and widgets AFTER approval, forcing rework. Catch this BEFORE spot-checking saves 1-2 rework cycles.

**Past incident:** Dashboard rendered without the "Region" filter that was in the plan. User asked for it as a change request. Entire dashboard iteration wasted.

---

### Rule P3-4: Spot-Check at Least 3 KPIs After Rendering (ENFORCEMENT)

**⚠️ CRITICAL: CANNOT approve dashboard without 3+ KPI spot-checks passing.**

**⚠️ IMPORTANT: Always validate against SOURCE data, NOT SINK data**

If Phase 2 created SINK tables:
- Dashboard queries the SINK tables (pre-aggregated)
- But spot-checks MUST query the original SOURCE tables (ground truth)
- This validates that Phase 2 workflow created the right aggregations AND Phase 3 queries the right data

**Why:** If you validate against SINK data, you only verify consistency — not correctness. You miss bugs in Phase 2 aggregations. The source data is the "source of truth."

**Step 1: Render dashboard.html**

**Step 2: Spot-check exactly 3 KPIs against SOURCE data**

For each KPI, run database query AGAINST SOURCE TABLES and compare:

```
KPI #1: Total Revenue
  Dashboard shows: $4.5M
  Query: SELECT SUM(amount) FROM revenue_table WHERE date >= '2026-07-01'
  DB result: $4,500,000
  Match? ✓ PASS (exactly equal)

KPI #2: Unique Customers
  Dashboard shows: 15,240
  Query: SELECT COUNT(DISTINCT customer_id) FROM customers WHERE active = true
  DB result: 15,240
  Match? ✓ PASS (exactly equal)

KPI #3: Conversion Rate
  Dashboard shows: 3.2%
  Query: SELECT COUNT(converted) / COUNT(*) FROM events WHERE date >= '2026-07-01'
  DB result: 0.032 (3.2%)
  Match? ✓ PASS (exactly equal)
```

**Step 3: Check results**
- All 3 KPIs match (exactly, not approximately)? → Proceed ✓
- Any KPI is 1% off or more? → **STOP immediately** ✗

**Step 4: If any spot-check fails**
- **Do not proceed** to user approval
- Debug immediately:
  - Query: Is the WHERE clause correct?
  - Aggregation: Is GROUP BY logic correct?
  - Join: Is there fan-out inflation?
  - Time column: Is the date filter right?
- Fix the issue
- Re-render dashboard
- Re-run all 3 spot-checks
- Repeat until all pass

**Step 5: Only after all 3 pass**
- Present dashboard for user approval
- Document spot-check results in state.md

**If user says "the numbers are close enough":**
> "I cannot approve dashboard with any KPI off by 1% or more. Even small errors compound and destroy trust when customers use it.
>
> Found mismatch:
> - Dashboard: [value]
> - Database: [value]
> - Difference: [%]
>
> I will debug and fix this before presenting for approval."

**Why:** Small data errors destroy trust. If customers spot-check and find mismatches, the entire dashboard loses credibility. Phase 3 requires exact matching.

---

### Rule P3-4b: Test 2–3 Random Filter Combinations Against SOURCE Data (ENFORCEMENT)

**⚠️ CRITICAL: Before finalizing dashboard, test filter combinations in real-world scenarios.**

After KPI spot-checks pass, test 2-3 random filter combinations to ensure filters work correctly together and with date ranges.

**Step 1: Pick 2–3 random filter combos**

Pick realistic combinations that users might try:

**Example 1: Dimension + Date Filter**
```
Filter combo: Region = "US West" + Date = "Last 30 days"
Dashboard shows: Revenue = $245K, Customers = 1,250
Query against SOURCE: 
  SELECT SUM(amount), COUNT(DISTINCT customer_id) 
  FROM source_transactions 
  WHERE region = 'US West' 
    AND date_column >= CURRENT_DATE - INTERVAL 30 DAY
Result: Revenue = $245K, Customers = 1,250 ✓ MATCH
```

**Example 2: Multiple Dimensions + Date**
```
Filter combo: Category = "Electronics" + Status = "Completed" + Date = "Last 90 days"
Dashboard shows: Total Orders = 3,420
Query against SOURCE:
  SELECT COUNT(*) 
  FROM source_orders 
  WHERE category = 'Electronics' 
    AND status = 'Completed' 
    AND order_date >= CURRENT_DATE - INTERVAL 90 DAY
Result: 3,420 ✓ MATCH
```

**Example 3: Edge Case: All Filters Applied**
```
Filter combo: Region = "EMEA" + Product = "Premium" + Customer_Segment = "Enterprise" + Date = "Last 180 days"
Dashboard shows: Revenue = $1.2M
Query against SOURCE:
  SELECT SUM(amount) 
  FROM source_transactions 
  WHERE region = 'EMEA' 
    AND product_tier = 'Premium' 
    AND segment = 'Enterprise' 
    AND date_column >= CURRENT_DATE - INTERVAL 180 DAY
Result: $1.2M ✓ MATCH
```

**Step 2: Verify each combo**
- [ ] Dashboard numbers match SOURCE query results (exactly)
- [ ] Focus on: dimension combinations + date ranges
- [ ] All 2–3 combos pass? → Proceed ✓
- [ ] Any combo fails? → **STOP and debug** ✗

**Step 3: If any combo fails**
- Debug filter logic (is WHERE clause applied correctly?)
- Check dimension grain (are you grouping by the right columns?)
- Verify date range boundaries (off-by-one errors?)
- Check join keys (is filter applied to correct table?)
- Re-render and re-test

**Why:** KPI spot-checks verify individual metrics. Filter combo tests verify that dimensions and dates work together. Filters are how users interact with dashboards — they must be correct under real-world usage patterns.

**Past incident:** Dashboard showed correct total revenue (KPI passed), but filtered by "Region=North" showed $50K instead of $47K. Bug: filter applied to orders table but revenue was summed from order_items (fan-out). Combo test would have caught this immediately.

---

### Rule P3-5: Dashboard Must Open Standalone in Browser

**Test before calling complete:**

```bash
# ✅ RIGHT: opens without server
open dashboard.html  # Browser opens it directly

# ❌ WRONG: requires server
# "You need to run 'npm start' to view this"
```

**Why:** The entire value of HTML Client is portability. If it needs a server, the build is wrong.

---

### Rule P3-6: Interactive Elements Must Be Tested

After rendering, manually test:

- [ ] Filters work (e.g., clicking "region" dropdown changes data)
- [ ] Charts respond to filter changes
- [ ] Page loads without errors (browser console)
- [ ] Numbers update correctly when filters change

**Test sequence:**
```
1. Open dashboard.html in browser
2. Filter: region = "US" → verify table updates
3. Filter: date = "last 7 days" → verify chart updates
4. Clear all filters → verify data returns to full view
5. Check browser console (F12) → no red errors
```

---

### Rule P3-6a: HTML Template Validation (AFTER EVERY EDIT)

**⚠️ CRITICAL: After any edit to `dashboard.html`, validate structure immediately.**

**Validation checks (must pass):**

```bash
# Check for duplicate closing tags
grep -c '</body>' dashboard.html   # must be exactly 1
grep -c '</html>' dashboard.html   # must be exactly 1
grep -c '<script>' dashboard.html  # should match number of </script> closes

# Check for malformed tags
grep -E '</body>.*</body>|</html>.*</html>' dashboard.html  # must return nothing

# Check file is valid HTML
echo "File size: $(wc -c < dashboard.html) bytes"
```

**If any check fails:**
```bash
# Find the duplicate
grep -n '</body>' dashboard.html
grep -n '</html>' dashboard.html

# Fix by removing duplicates (manual edit)
```

**Why:** Duplicate closing tags render as visible text on the dashboard. Caught in Phase 3 prevents user confusion.

**Automate this check:**
```yaml
# Add to Phase 3 workflow
+validate_template:
  sh>: |
    body_count=$(grep -c '</body>' dashboard.html)
    html_count=$(grep -c '</html>' dashboard.html)
    if [ "$body_count" -ne 1 ] || [ "$html_count" -ne 1 ]; then
      echo "ERROR: Template has duplicate closing tags"
      exit 1
    fi
    echo "✓ Template validation passed"
```

---

### Rule P3-6b: Filter Edge Cases — Specification Before Build

**⚠️ REQUIRED: Before Phase 3 build, capture edge case behaviors in state.md.**

For each filter, document what happens in edge cases:

1. **Filter returns no results:**
   - Show "No data available"? OR
   - Show "—" (dash)? OR
   - Show last valid data with a warning?

2. **COUNT DISTINCT with filter applied:**
   - Show adjusted count? OR
   - Show "—" (not calculable)? OR
   - Show estimate with confidence label?

3. **Multiple conflicting filters:**
   - Show intersection (all filters applied)? OR
   - Show OR logic (any filter)? OR
   - Revert to unfiltered view?

**Capture in state.md (from Phase 1):**
```yaml
### Filter Edge Case Behaviors

**Filter: Region**
- No results returned: Show "No data available for selected region"
- Applied to COUNT(DISTINCT customer_id): Show adjusted count
- Multiple regions: Show intersection (AND logic)

**Filter: Date Range**
- Out-of-range dates: Show "Date range outside available data (2020-2026)"
- Single day requested: Show daily aggregate (not hourly drill-down)
- Overlapping ranges: Show intersection

**Filter: Customer Segment**
- Empty segment: Show "No customers in this segment"
- Applied to Revenue: Show revenue for segment only
- Multiple segments: Show totals per segment, not combined
```

**In Phase 3 queries, implement edge case handling:**
```sql
-- Example: Check if filter returns 0 rows
SELECT COUNT(*) AS count, SUM(revenue) AS revenue
FROM events
WHERE region = ? -- user-selected filter
  AND date >= ? AND date <= ?;

-- If count = 0, dashboard should display "—" or warning, not error
```

**Why:** Prevents "No data" errors confusing users. Better to specify behavior upfront.

---

### Rule P3-6c: Filter Scope & Binding — ALL Affected Widgets Must Update (ENFORCEMENT)

**⚠️ CRITICAL: When a filter is applied, ALL widgets that should be affected MUST update. Filters that don't change data = broken dashboard.**

**Step 1: Define filter scope in Phase 1 plan (from state.md)**

For EACH filter, document which widgets it affects:

```yaml
### Filter Scope Definition

**Global Filter: Date Range**
- Affects: [list all widgets that use this filter]
  * KPI: Total Revenue (recalculate for date range)
  * Chart: Revenue Trend (filter data to date range)
  * Chart: Revenue by Region (filter data to date range)
  * Table: Orders (show only orders in date range)
- Does NOT affect: [widgets independent of date]
  * KPI: All-Time Customer Count (not filtered by date)

**Global Filter: Region**
- Affects:
  * KPI: Revenue (filter to region)
  * Chart: Revenue Trend (show only selected region)
  * Chart: Revenue by Region (show only selected region)
  * Chart: Churn by Segment (show only selected region)
  * Table: Orders (show only orders from region)
- Does NOT affect:
  * Chart: Revenue by Region (but NOW shows only selected region)

**Tab 2 Filter: Category** (tab-specific)
- Affects: Only widgets on Tab 2
  * Chart: Revenue Trend (filter to category)
  * Table: Products (show only category products)
- Does NOT affect: Tab 1 or Tab 3
```

**Step 2: Test each filter (MANUAL IN BROWSER)**

For EACH filter, test that it updates ALL affected widgets:

```
Filter: Date Range = "Last 7 Days"
  
Before filter:
  - Revenue card shows: $4.5M (all-time)
  - Revenue Trend chart shows: 365 days of data
  - Table shows: 1.2M orders (all-time)

After applying filter:
  - Revenue card shows: $500K ✓ (updated to 7 days)
  - Revenue Trend chart shows: 7 days only ✓ (x-axis changed)
  - Table shows: 15K orders ✓ (updated to 7 days)

✓ PASS: All affected widgets updated
✗ FAIL: If any widget didn't update (e.g., Revenue card still shows $4.5M)
```

**Test sequence (REQUIRED):**

```
1. Open dashboard in browser
2. Note all widget values: [KPI cards, chart data, table row count]
3. Apply Filter 1 (e.g., Region = "US")
   → Manually inspect each widget
   → Does it reflect the filter? (Numbers changed? Data filtered?)
   → Check EVERY affected widget listed in Phase 1 plan
4. If ANY widget didn't update → ✗ FAIL (stop, debug)
5. If ALL affected widgets updated → ✓ PASS
6. Clear filter (reset to all data)
7. Apply Filter 2 (e.g., Date Range = "Last 30 days")
   → Repeat inspection
8. Repeat for ALL filters
9. Test filter combinations (e.g., Region=US + Date=Last 7 days)
   → All affected widgets should show intersection
```

**Step 3: If filter doesn't update a widget (✗ FAIL)**

Common causes + fixes:

| Problem | Cause | Fix |
|---------|-------|-----|
| KPI card not updating | Query doesn't have WHERE clause for filter | Add `WHERE region = ${selected_region}` to SQL |
| Chart not updating | Filter not passed to chart data query | Pass filter value to chart data array query |
| Table not updating | Search/filter JS not wired to filter select | Add event listener: `filterSelect.addEventListener('change', refilterTable)` |
| Filter works on one tab, not another | Filter is global, but one tab has separate query | Ensure both tab queries include the filter |
| Data changes but numbers are wrong | Filter is applied, but calculation is wrong | Check aggregation logic: is it SUM(all filtered) or SUM(per-filter-value)? |

**Debug checklist (if filter doesn't work):**

```bash
# 1. Check browser console (F12 → Console)
#    - Any JavaScript errors? (red ✗ in console?)
#    - Log filter value: console.log('Filter value:', filterValue)

# 2. Check HTML
#    - Is the filter element present? (inspect element)
#    - Is there an onChange handler? (check <select> tag)

# 3. Check JavaScript
#    - Does the filter-change function exist?
#    - Does it re-query data or re-filter existing data?
#    - Does it call the render/update function?

# 4. Check SQL queries
#    - Does the query have WHERE clause for filter?
#    - Example: SELECT SUM(revenue) FROM orders WHERE region = ?
#    - Or is it SELECT SUM(revenue) FROM orders (no filter)?
```

**Step 4: Document in state.md**

```yaml
### Interactive Filter Testing

**Filter: Region (Global)**
- Test: Click Region = "US"
  * Revenue card: $2.1M → ✓ Updated
  * Revenue Trend: Data filtered to US → ✓ Updated
  * Revenue by Region: Shows only US → ✓ Updated
  * Orders table: Shows 45K orders (US only) → ✓ Updated
  * Status: ✅ PASS (all affected widgets updated)

**Filter: Date Range (Global)**
- Test: Click Date Range = "Last 30 days"
  * Revenue card: $500K → ✓ Updated
  * Revenue Trend: Shows 30 days only → ✓ Updated
  * Orders table: Shows 12K orders (30 days) → ✓ Updated
  * Status: ✅ PASS (all affected widgets updated)

**Combined: Region=US + Date Range=Last 30 days**
- Revenue card: $125K → ✓ Updated (intersection of both filters)
- Revenue Trend: US data, 30 days only → ✓ Updated
- Orders table: 2K orders (US + 30 days) → ✓ Updated
- Status: ✅ PASS (all filters work together)
```

**Why:** Filters that don't update data destroy dashboard trust. User applies Region filter, sees old numbers, assumes dashboard is broken. Catch this BEFORE user approval.

**Past incident:** Region filter present but didn't update Revenue trend chart. Chart showed global revenue regardless of filter selection. User discovered during first use. Dashboard credibility lost.

---

### Rule P3-6d: Filter Granularity & Tab-Scoped Filter Application (ENFORCEMENT)

**⚠️ CRITICAL: (1) Filter options must match Phase 1 plan granularity, (2) Tab-level filters must apply to ALL widgets on that tab**

**Part A: Filter Granularity Must Match Plan**

**Example mismatch:**
```
Phase 1 Plan: Date filter = Monthly (12 options: Jan, Feb, Mar...)
Dashboard rendered: Date filter = Daily (365 options: Jan 1, Jan 2...)
❌ MISMATCH: Plan said MONTH, dashboard shows DAY
```

**Validation: Verify filter options match Phase 1 granularity**

```yaml
### Filter Granularity Check

Filter: Date Range
  Planned: Month (12 options)
  Dashboard: ✅ Month (Jan 2026, Feb 2026, Mar 2026...)
  Status: ✅ PASS

Filter: Region
  Planned: 6 regions (US, EU, APAC, LATAM, EMEA, Internal)
  Dashboard: ✅ 6 regions exactly
  Status: ✅ PASS

Filter: Category
  Planned: 8 product categories
  Dashboard: ✅ 8 categories exactly
  Status: ✅ PASS

Filter: Traffic Source (on Tab 2)
  Planned: 5 sources (Organic, Paid Search, Social, Email, Direct)
  Dashboard: ❌ 50 sources (too granular, not grouped)
  Status: ❌ FAIL — aggregation is wrong
```

**If granularity doesn't match (❌ FAIL):**
- STOP — do not proceed
- Fix: Update SQL aggregation
  ```sql
  -- WRONG: Too granular
  SELECT traffic_source, SUM(revenue) FROM events GROUP BY traffic_source
  -- Shows 50 individual sources
  
  -- RIGHT: Match plan
  SELECT CASE traffic_source 
    WHEN 'google' THEN 'Organic'
    WHEN 'facebook_ad' THEN 'Social'
    ... 
  END as traffic_source, SUM(revenue) FROM events GROUP BY traffic_source
  -- Shows 5 grouped sources
  ```
- Re-render dashboard
- Re-validate granularity matches

---

**Part B: Tab-Level Filters MUST Apply to ALL Tab Widgets**

**The problem:** Tab filter (Category, Campaign, Loyalty Tier) only affects SOME widgets on the tab, not others.

**Example:**
```
Tab 2: Campaign Analysis
  Filters: Campaign (dropdown), Traffic Source (dropdown)
  Widgets:
    - Campaign Revenue chart
    - Campaign ROI chart
    - Campaign Performance table

❌ BUG: Campaign filter only updates Campaign Revenue chart
  - Campaign filter applied: Campaign = "Email Campaign 1"
  - Campaign Revenue chart: Updated to $500K ✓
  - Campaign ROI chart: Still shows all campaigns, $4.5M ❌
  - Campaign Performance table: Still shows 45 campaigns ❌

✅ CORRECT: Campaign filter should update ALL widgets
  - Campaign filter applied: Campaign = "Email Campaign 1"
  - Campaign Revenue chart: $500K ✓
  - Campaign ROI chart: $500K (only Email Campaign 1) ✓
  - Campaign Performance table: Only Email Campaign 1 rows ✓
```

**Validation: Test tab filters on all tab widgets**

**Test matrix for Tab 2 (Campaign Analysis):**

```
Baseline (no tab filters):
  - Campaign Revenue: $4.5M (all campaigns) ✓
  - Campaign ROI: 2.1% (avg across all) ✓
  - Campaign Performance table: 45 rows ✓

Apply: Campaign = "Email Campaign 1"
  - Revenue chart: $500K ✓ UPDATED
  - ROI chart: 3.2% ✓ UPDATED
  - Table: 1 row (Email Campaign 1 only) ✓ UPDATED
  Status: ✅ PASS (all 3 widgets filtered)

Apply: Campaign + Traffic Source = "Organic"
  - Revenue: $125K ✓ (Email Campaign 1 + Organic)
  - ROI: 4.1% ✓ (Email Campaign 1 + Organic)
  - Table: 1 row ✓ (intersection)
  Status: ✅ PASS (combined tab filters work)

Apply: Campaign + Traffic Source + Global Date = "Last 7 Days"
  - Revenue: $50K ✓ (Email + Organic + Last 7d)
  - ROI: 4.5% ✓ (Email + Organic + Last 7d)
  - Table: Filtered ✓ (3-way intersection)
  Status: ✅ PASS (tab + global filters work together)
```

**If tab filter doesn't apply to all tab widgets (❌ FAIL):**

```
Example failure:
  Apply: Campaign = "Email Campaign 1"
  - Revenue chart: $500K ✓ (updated)
  - ROI chart: $4.5M ❌ (NOT updated)
  - Table: 45 rows ❌ (NOT updated)
  
  Root cause: Campaign filter only bound to revenue query, not ROI or table

Fix: Ensure EVERY tab widget query includes the tab filter:

  1. Campaign Revenue query:
     SELECT ... WHERE campaign_id = ${campaignId}

  2. Campaign ROI query (was missing this):
     SELECT ... WHERE campaign_id = ${campaignId}  ← ADD THIS

  3. Campaign Performance table query (was missing this):
     SELECT ... WHERE campaign_id = ${campaignId}  ← ADD THIS

Debug in browser console:
  - Is campaign_id captured? console.log('Campaign:', campaignId)
  - Are all 3 queries updated? Check SQL in render function
  - Does refilter() call all 3 update functions?
```

**Test matrix for Tab 3 (Loyalty Segments):**

```
Apply: Loyalty Tier = "VIP"
  - Revenue by Loyalty chart: $2M (VIP only) ✓
  - Loyalty Count: 50K (VIP count) ✓
  - Customer table: Only VIP rows ✓
  Status: ✅ PASS

Apply: Loyalty Tier + Category = "Electronics"
  - Revenue: $800K (VIP + Electronics) ✓
  - Count: 20K (VIP + Electronics) ✓
  - Table: Intersection rows ✓
  Status: ✅ PASS (2 tab filters work)

Apply: Loyalty + Category + Global Date + Region
  - All widgets: ✅ 4-way filter intersection applied
  Status: ✅ PASS (all filters work together)
```

**Documentation in state.md:**

```yaml
### Tab Filter Validation

**Tab 2: Campaign Analysis (Global: Date, Region)**

Tab filters: Campaign, Traffic Source

Test 1: Campaign filter alone
  - Campaign Revenue: ✅ Filtered to selected
  - Campaign ROI: ✅ Filtered to selected
  - Performance table: ✅ Filtered to selected
  Status: ✅ PASS (all 3 widgets updated)

Test 2: Campaign + Traffic Source
  - Revenue: ✅ Intersection
  - ROI: ✅ Intersection
  - Table: ✅ Intersection
  Status: ✅ PASS

Test 3: Campaign + Traffic Source + Global Date + Region
  - All: ✅ 4-way filter works
  Status: ✅ PASS

**Tab 3: Loyalty Segments (Global: Date, Region)**

Tab filters: Loyalty Tier, Category

Test 1: Loyalty Tier = "VIP"
  - Revenue by Loyalty: ✅ Updated
  - Loyalty Count: ✅ Updated
  - Customer table: ✅ Updated
  Status: ✅ PASS

Test 2: Loyalty Tier + Category
  - All: ✅ 2-way intersection
  Status: ✅ PASS

Test 3: Loyalty + Category + Global filters
  - All: ✅ 4-way intersection
  Status: ✅ PASS
```

**Why Part A (Granularity mismatch):** Plan says "month", dashboard shows "day" → user confusion, performance issues, doesn't match what was agreed

**Why Part B (Tab filter scope):** Tab filter affects 1 widget but not others → inconsistent behavior, wrong data interpretation, dashboard appears broken

**Past incidents:**
1. Plan: "Category filter (8 options)" → Dashboard: "365 daily options" → User confused
2. Tab 2 Campaign filter only updated Revenue chart, not ROI chart or table → Dashboard seemed broken → User lost trust

---

### Rule P3-7: Join Validation Results (From Phase 2)

If Phase 2 was completed, join validation was done. If Phase 2 was skipped:

- [ ] Verify join does NOT fan-out (row count after join ≤ 2× before)
- [ ] If fan-out detected, pre-aggregate many-side BEFORE querying

**Check (Phase 3 only if Phase 2 skipped):**
```sql
-- Count rows before join
SELECT COUNT(*) FROM table_a;  -- 1,000 rows

-- Count rows after join
SELECT COUNT(*) FROM table_a a
JOIN table_b b ON a.id = b.a_id;  -- Should be ≤ 2,000 rows

-- If result > 2,000, you have fan-out → pre-aggregate table_b first
```

---

### Rule P3-8: Rendering Must Use Node.js Scripts

All file I/O and template rendering must use Node.js:

**Pattern:**
```javascript
// generate-data.js — fetch query results
const results = await tdxQuery(querySQL);
fs.writeFileSync('data.json', JSON.stringify(results));

// render.js — inject data into HTML template
const data = JSON.parse(fs.readFileSync('data.json'));
const html = template.replace('{{DATA}}', JSON.stringify(data));
fs.writeFileSync('dashboard.html', html);
```

**Never:**
- Use Python for file I/O (not the standard)
- Let AI read raw query results (data flows script-only)

---

### Rule P3-9: Theme & Branding (Treasure AI 2026)

Dashboard must use official Treasure AI 2026 branding:

- **Primary colors:** Dark 2 (#2D40AA), Accent 1 (#847BF2), Light 1 (#FFFFFF)
- **Accessibility:** WCAG AA minimum (AAA preferred)
- **Typography:** Poppins (headers), Manrope (body)

See: `../references/treasure-data-theme.md`

---

### Rule P3-10: State.md Append

Append Phase 3 results to state.md (updated in Phase 2 or created in Phase 1):

```yaml
---

## Phase 3 — Build Interactive Dashboard
**Date:** [date]
**Status:** ✅ Complete

### Dashboard Details

- **File:** dashboard.html
- **Size:** [Xmb]
- **Data Inlined:** ✓ (self-contained)
- **Filters:** [list, e.g., "region", "date_range"]
- **Charts:** [list of viz types]
- **KPIs:** [list]

### Data Sources

- Query 1: Revenue by region
  - Source: [SINK table or source table]
  - Rows returned: [N]
  - Last updated: [timestamp]
  
- Query 2: Customer trends
  - Source: [table]
  - Rows returned: [N]
  - Last updated: [timestamp]

### Spot-Check Validation

- [ ] KPI 1: [metric name] = [value] ✓ (verified against DB)
- [ ] KPI 2: [metric name] = [value] ✓ (verified against DB)
- [ ] KPI 3: [metric name] = [value] ✓ (verified against DB)

### Testing Results

- [ ] HTML opens standalone (no server needed)
- [ ] Filters work correctly
- [ ] Charts update when filters change
- [ ] Browser console shows no errors
- [ ] Page loads in <3s on typical connection

### User Approval

- Dashboard approved: YES
- Feedback: [list any requested changes]

---

## Next Action

1. ✓ Phase 3 complete (dashboard ready)
2. Optional: Phase 4 (automation + agents)
3. Optional: Phase 5 (handoff documentation)
4. Or: Go live with dashboard
```

---

## Phase 3 Pre-Flight Checklist

**Before starting Phase 3, verify:**

### Prerequisites
- [ ] Dashboard Complexity Score available from Phase 1
- [ ] state.md exists from Phase 1 (+ Phase 2 if applicable)
- [ ] All requirements + data findings documented

### Query Readiness
- [ ] Decision made: use SINK tables or source tables directly?
- [ ] Queries written for each dashboard element (KPIs, charts, filters)
- [ ] Queries tested manually (`tdx query -f query.sql -d <database>`)
- [ ] Results verified (not empty, numbers reasonable)

### Dashboard Scope
- [ ] KPIs defined (what metrics to show)
- [ ] Filters defined (what dimensions to slice by)
- [ ] Charts/visualizations planned
- [ ] Layout planned (tabs, sections, etc.)

### Rendering Setup
- [ ] Node.js scripts ready (generate-data.js, render.js)
- [ ] HTML template ready
- [ ] Treasure AI 2026 theme applied
- [ ] Data will not pass through AI context (confirmed)

---

## Phase 3 Decision Tree

```
START Phase 3: Build Interactive Dashboard
    ↓
Verify prerequisites from Phase 1/2
    ↓
Decide: SINK tables (Phase 2 done) or source tables (Phase 2 skipped)?
    ↓
Write queries for each dashboard element
    ↓
Execute each query manually (tdx query)
    ↓
Verify: results not empty, numbers reasonable
    ↓
Execute Node.js pipeline: query → render.js → dashboard.html
    ↓
Open dashboard.html in browser (standalone, no server)
    ↓
Test: filters work, charts update, no errors
    ↓
Spot-check 3+ KPIs against database
    ↓
All checks pass?
    YES ↓ → User approval
    NO  ↓ → Debug (data issue? rendering issue? query issue?)
    ↓
User approves?
    YES ↓ → Append Phase 3 results to state.md
    NO  ↓ → Gather feedback, adjust, re-test
    ↓
END Phase 3
```

---

## Common Phase 3 Blocks

### "The dashboard is slow to load"
**Response:**
> "Let's check: (1) Are queries already fast? (tdx query -f query.sql -d <database> — time it), (2) Is the HTML too large? (check file size), (3) Are there too many data rows? (limit to most recent 1000, or use SINK tables from Phase 2 for pre-aggregation)"

### "The chart shows the wrong data"
**Response:**
> "Let me verify: (1) Run the query manually to see what it returns, (2) Check if filters are applying correctly, (3) Verify the template is reading the right column from the query result. Common issue: column name mismatch between query and template."

### "I want the dashboard to update in real-time"
**Response:**
> "Phase 3 builds a static dashboard (data at build time). For live data, we'd need: (1) Phase 2 workflow refreshing SINK tables on schedule, or (2) Phase 4 Foundry agent for real-time queries. Which makes sense for your use case?"

### "Can I share this dashboard with others?"
**Response:**
> "Yes! Since dashboard.html is self-contained (all data inlined), you can: (1) Email the file directly, (2) Host it on any web server, (3) Upload to a shared drive. No setup needed on recipient's end — just open in browser."

---

## Phase Progression Gate (CANNOT Skip)

**⚠️ CRITICAL: Before proceeding to Phase 4 (optional), verify:**

- [ ] Phase 1 marked COMPLETE in state.md
- [ ] Phase 2 marked COMPLETE in state.md (if applicable)
- [ ] Dashboard HTML file exists and opens standalone
- [ ] All filters tested and work correctly
- [ ] All charts render without errors
- [ ] 3+ KPI spot-checks PASSED (all exactly matching)
- [ ] User explicitly approved dashboard (not just "looks good")
- [ ] state.md appended with Phase 3 results:
  - Dashboard file size and location
  - Queries executed (with row counts)
  - Spot-check results (3 KPIs, all matching)
  - User approval captured
  - "Next Action" pointer (Phase 4 optional or Phase 5)

**If ANY item is missing or spot-checks failed:**
> "Cannot proceed. Phase 3 incomplete.
> Missing/Failed: [specific item]
> Please complete before moving forward."

**Only after all items verified:**
- Append "Phase 3 COMPLETE" to state.md
- If user wants Phase 4: proceed to phase-4/INSTRUCTIONS.md
- If user wants Phase 5 or close: proceed to phase-5/INSTRUCTIONS.md
- Or project is complete

---

## After Phase 3 Completes (Rule 0: Phase Auto-Advance)

**If dashboard is approved (IMMEDIATE OFFER, ONE QUESTION):**

**Say this (EXACT SCRIPT):**
```
✅ Phase 3 Complete — Dashboard approved and ready

### Summary
[tabs] | [metrics] | [filters] | [data size] | [load time]
All spot-checks passed (±0.1% accuracy)

### Next: What's next?

**Option A (Recommended):** Phase 4A — Extract a Reusable Skill
→ Turn this dashboard into a Claude skill for future projects
→ Time: 1 hour
→ Benefit: Next similar dashboard builds 10× faster

**Option B:** Phase 4B — Deploy Conversational Agent
→ Create a Foundry agent for natural language queries
→ Time: 1.5 hours
→ Benefit: Users ask "Revenue by region?" instead of opening filters

**Option C:** Phase 5 — Documentation & Handoff
→ Create runbooks, access guides, and architecture docs
→ Time: 1 hour
→ Benefit: Support team can troubleshoot without escalating

**Option D:** Close engagement
→ Dashboard is ready to share as-is

**→ Which? (A/B/C/D)**
```

**Then wait for ONE answer and proceed immediately (no second approval):**
- User says A → Start Phase 4 Track A
- User says B → Start Phase 4 Track B
- User says C → Start Phase 5
- User says D → "Dashboard is ready. Closing engagement."

**If dashboard needs rework:**
```
✗ Phase 3 Not Approved → Gather Feedback

What needs to change?
  - [requested change 1]
  - [requested change 2]

Adjusting and re-testing...
```

**Why:** Phase 3 is optional→required junction. Must present Phase 4 immediately after approval, not wait for "what's next?"

---

## After Phase 3: What's Next?

**Phase 3 COMPLETE → Dashboard Ready**

You now have a working, user-approved dashboard. What happens next depends on what the user needs:

### Option A: Phase 4 Track A — Create Reusable Skill ✅ (Recommended)
- Package this dashboard as a skill in `~/.claude/skills/` (available across all sessions)
- Next similar dashboard builds 10× faster (reusable templates, queries, patterns)
- Optional: zip and share with team
- Time: ~1 hour
- → Read `./phase-4/SKILL.md`

### Option B: Phase 4 Track B — Deploy Conversational Agent ✅
- Add a Foundry AI agent that answers questions about the dashboard data
- Users can ask: "What's driving revenue? Which regions perform best?"
- Agent handles natural language → SQL translation
- Time: ~1-2 hours
- → Read `./phase-4/SKILL.md`

### Option C: Phase 5 — Handoff Documentation ✅
- Create 4 markdown files (Architecture, Usage Guide, Runbook, Access/Ownership)
- Enables team to maintain dashboard independently
- Time: ~30-60 minutes
- → Read `./phase-5/SKILL.md`

### Option D: Close Engagement ✅
- Dashboard is ready and deployed
- No additional automation or documentation needed
- User can share `dashboard.html` directly with stakeholders
- Project complete

**Next step:** Ask the user: "A, B, C, or D?" — then proceed immediately to the selected phase.

---

**Version:** 1.0.0
**Last Updated:** 27 July 2026
**Load Order:** 1.3 (read after Phase 1-2 INSTRUCTIONS.md)
