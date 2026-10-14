# Phase 3 Data Patterns — Query Design & Validation

Synthesized from production implementation. These patterns prevent silent failures and regressions.

---

## 0. Data Grain Must Match Phase 1 Filter Definitions (CRITICAL)

**Rule:** `generate-data.js` queries must fetch data at the **exact grain level of the filters approved in Phase 1**, and **all widgets must update consistently when ANY filter combination is applied**.

### Filter Placement: Dashboard-Level, Tab-Level, or Both

Filters can be configured three ways — **the choice depends on data and dashboard plan**, but the constraint is the same:

| Filter Config | Definition | Query Grain | Widget Behavior |
|---|---|---|---|
| **Dashboard-level only** | Single filter applies globally to ALL tabs/widgets | Must GROUP BY that dimension on ALL queries | Every widget filters by that dimension |
| **Tab-level only** | Each tab has independent filters; other tabs unaffected | Must GROUP BY per-tab dimensions on EACH tab's queries | Only widgets on active tab filter |
| **Both (mixed)** | Some filters global, some per-tab | Must GROUP BY both global + tab dimensions | Global filters affect all tabs; tab filters affect only active tab |

**Critical:** Whatever filter config is chosen, when filters are applied, ALL affected widgets must show the **same combination of values** — not partial data or cache misses.

### Why This Matters

Phase 1 approves:
- Which dimensions the dashboard filters on (e.g., Region, Product Category, Customer Segment)
- Where each filter lives (dashboard-level, tab-level, or both)
- Which KPIs are calculated (e.g., Total Revenue, Unit Count, Average Order Value)

Phase 3 must query at that **same grain**, or:
- ❌ KPIs show incorrect aggregates (over-counted or under-counted)
- ❌ Filters don't affect all widgets consistently
- ❌ Users see different numbers across widgets for the same filter selection
- ❌ Dashboard vs Phase 1 analysis numbers diverge

### Examples

| Phase 1 Approval | Required Query Grain | Widget Behavior When Filtered | Wrong Grain (Fails) |
|---|---|---|---|
| Dashboard-level: `[Region]` | `GROUP BY region` on ALL queries | All widgets show only selected region data | Querying without region → widgets show total across regions |
| Tab-level: `[Tab1: Region, Product]` | Tab1 queries: `GROUP BY region, product`; Tab2 unchanged | Tab1 filters by region AND product; Tab2 independent | Tab1 queries only `GROUP BY region` → Product filter changes nothing |
| Both: Dashboard `[Date]` + Tab `[Region]` | All: `GROUP BY DATE`; Tab1: also `GROUP BY region` | All tabs filter by date; Tab1 also filters by region | Missing date from Tab1 query → date filter doesn't work on Tab1 |

### How to Validate

Before writing `generate-data.js`:
1. **Read Phase 1 `state.md`** → extract confirmed filters and their placement (dashboard/tab/both)
2. **List every dimension** per location — e.g., dashboard: `[date]`, Tab1: `[region, product]`, Tab2: `[customer_segment]`
3. **Every query result must include those dimensions at minimum**
4. **Spot-check filter combinations:** 
   - Apply Region=West + Product=A, manually verify **ALL affected widgets** show the same row subset
   - If one widget shows West+A total and another shows a different total for the same filter, grain is wrong

---

## 1. Two-Tier Filter Architecture (REQUIRED)

All Phase 3 dashboards implement **two distinct filtering tiers**:

### Tier 1: Global Date Range (F.start, F.end)
- **Source:** `sink_overview_kpis` (daily granularity, NO dimension columns)
- **Scope:** All KPI cards + trend charts (global)
- **When:** Always active (default filter)
- **Why:** Date filtering requires daily or finer grain; dimension-grouped data loses date precision

### Tier 2: Per-Tab Dimension Filters (FS.<tab>.<dimension>)
- **Source:** Distinct values from each tab's SINK table
- **Scope:** Active tab's widgets only
- **When:** Optional; user-selected dimensions
- **Why:** Separates dimension aggregation (coarse) from date filtering (precise)

**Implementation rule:**
```javascript
if (activeDimFilters.length === 0) {
  // Path 1: Use overview (daily, all-time aggregate)
  data = sink_overview_kpis;
} else {
  // Path 2: Use monthly+dimension table (monthly, current filter context)
  data = sink_<tab>_monthly_dims;
}
```

---

## 2. Three Required Data Shapes (NOT TWO)

Every Phase 3 must generate exactly three data shapes. Generating only two is a design gap that appears mid-project.

| Shape | Grain | Query Example | Use Case |
|-------|-------|---------------|----------|
| **S1: Daily, no dims** | Daily per date | `sink_overview_kpis` | Date-filtered KPIs; no dimension active |
| **S2: All-time, with dims** | Single row per dim combo | `SELECT category, SUM(revenue) FROM sink_daily GROUP BY category` | Breakdown charts; no date filter needed |
| **S3: Monthly, with dims** ⭐ | Monthly per dimension combo | `SELECT SUBSTR(date,1,7), category, SUM(revenue) FROM sink_daily GROUP BY 1,2` | **Respond to BOTH date + dimension filters simultaneously** |

### Critical: Shape S3 is What's Missing

Without S3, KPI cards cannot respond to both filters at once. This gap was discovered mid-project in the retail implementation.

### Query Generation Pattern

```javascript
// Step 1: Overview + all-time breakdowns (always)
const q1 = query_overview();                    // S1
const q2 = query_breakdown_sales_alltime();     // S2: sales breakdown
const q3 = query_breakdown_web_alltime();       // S2: web breakdown

// Step 2: MONTHLY + DIMS (mandatory per tab) ⭐
const q4 = query_sales_monthly_dims();          // S3: sales tab
const q5 = query_web_monthly_dims();            // S3: web tab
const q6 = query_customers_monthly_dims();      // S3: customers tab

const results = await Promise.all([q1, q2, q3, q4, q5, q6]);
```

---

## 3. Monthly Query Cardinality — Pre-Calculate & Validate (REQUIRED)

### Estimation Formula

For each monthly+dimension query (S3):
```
Expected rows ≈ months × distinct_D1 × distinct_D2 × ... × distinct_DN

Example: Sales (category, payment_type, status)
  61 months × 12 categories × 4 payment_types × 3 statuses = 8,784 rows ✓

Example: Customers (tier, channel, income_tier, gender)
  61 months × 5 tiers × 7 channels × 5 income × 3 gender = 32,175 rows ❌ (TOO HIGH)
```

### LIMIT Setting Rule

**Set `LIMIT` to at least `2 × expected_rows`** as safety margin:

```sql
-- Correct
SELECT SUBSTR(date, 1, 7) as month, category, SUM(revenue)
FROM sink_sales_monthly
WHERE td_time_range(...)
GROUP BY 1, 2
ORDER BY month ASC
LIMIT 20000  -- expected: 8,784; 2× = 17,568 (rounded to 20K)
```

### Silent Truncation Check

Add post-query validation in `generate-data.js`:

```javascript
const result = await query(sql, LIMIT);
if (result.rows.length === LIMIT) {
  throw new Error(
    `⚠️ TRUNCATION DETECTED: Query returned exactly LIMIT (${LIMIT}) rows.\n` +
    `Most recent months may be missing.\n` +
    `Fix: Increase LIMIT or reduce dimensions.`
  );
}
```

**Document in state.md:**
```yaml
## Cardinality Audit
- Q4 (sales_monthly): expected 8,784 rows, LIMIT 20,000, actual 8,751 ✓
- Q5 (web_monthly): expected 12,000 rows, LIMIT 25,000, actual 11,893 ✓
- Q6 (customers_monthly): expected 6,000 rows, LIMIT 12,000, actual 5,997 ✓
```

---

## 4. Non-Additive Metrics — COUNT DISTINCT Handoff Rule (REQUIRED)

### The Problem

SINK columns with `COUNT DISTINCT` or `APPROX_DISTINCT` (e.g., `unique_sessions`, `unique_customers`) cannot be safely summed across rows.

**Example:** `unique_sessions` per (date, device_type, traffic_source)
- A session viewing both mobile AND desktop appears in TWO rows
- `SUM(unique_sessions)` overcounts by ~2× (double-counted)

### Phase 2 Responsibility

For EVERY `COUNT DISTINCT` column in any SINK table, Phase 2 **must document**:

```yaml
SINK Column: unique_sessions
Type: APPROX_DISTINCT(session_id) per (date, device_type, source, event_type)
Safe to SUM? NO
Why: Same session appears in multiple rows (one per device/source combo)

Phase 3 Handling:
  Option A: Use from overview_kpis (daily unique, no dims) ✓
  Option B: Query source directly (SELECT APPROX_DISTINCT at build time) ✓
  Option C: Show additive fallback + annotation (event_count instead) ✓
```

### Phase 3 Implementation

**Option A (Preferred):**
```javascript
// Use pre-deduplicated overview value
const uniqueCustomers = overviewData[0].unique_customers;
```

**Option B (if not in overview):**
```javascript
// Query source directly at build time
const result = await tdx_query(`
  SELECT APPROX_DISTINCT(customer_id) as unique_customers
  FROM retail_large_dataset.email_events
  WHERE date BETWEEN '${start}' AND '${end}'
`);
```

**Option C (fallback):**
```javascript
// Show additive metric with annotation
renderKPI({
  title: 'Email Opens',
  value: summedOpenCount,
  note: '(additive; unique customers cannot be filtered by segment)'
});
```

### Validation Checklist

- [ ] All `COUNT DISTINCT` columns documented in Phase 2 state.md
- [ ] Phase 3 explicitly chooses handling (A/B/C above)
- [ ] Non-additive columns never summed across dimension filters
- [ ] Fallback metrics clearly annotated

---

## 5. Non-Workflow vs Workflow Query Patterns

### Non-Workflow Path (Skipped Phase 2)
Query source tables directly with proper filtering:

```sql
SELECT destination, COUNT(*) as bookings, SUM(amount) as revenue
FROM <source_db>.<source_table>
WHERE td_time_range(event_time, '2026-06-23', '2026-07-23')  -- Partition pruning first
  AND status != 'Cancelled'                                   -- Then business logic
GROUP BY destination
ORDER BY revenue DESC
LIMIT 1000
```

### Workflow Path (Ran Phase 2)
Query pre-aggregated SINK tables (star schema):

```sql
SELECT destination, SUM(bookings) as bookings, SUM(revenue) as revenue
FROM <sink_db>.<sink_table>
WHERE date BETWEEN '2026-06-23' AND '2026-07-23'
  AND loyalty_tier = '${filter_loyalty_tier}'
GROUP BY destination
ORDER BY revenue DESC
LIMIT 1000
```

**Critical rule:** Apply ALL filters at SQL `WHERE` clause (not client-side post-fetch). This respects the Phase 2 SINK contract and maintains row-level accuracy.

---

## 6. Cross-Filter Pattern for Breakdown Charts (REQUIRED)

Breakdown charts must exclude their own dimension from active filters. Otherwise, selecting a value collapses the chart to a single bar.

### Wrong Pattern
```javascript
// Category chart filtered by all dimensions INCLUDING category
function renderCategoryChart(data, filters) {
  return data.filter(row =>
    (!filters.category || row.category === filters.category) &&  // ❌ Collapses chart
    (!filters.payment || row.payment === filters.payment) &&
    (!filters.status || row.status === filters.status)
  );
  // Selecting category=Electronics → Chart shows only 1 bar
}
```

### Correct Pattern
```javascript
// Category chart filtered by payment + status, but NOT category
function renderCategoryChart(data, filters, chartDim) {
  return data.filter(row =>
    (!filters.payment || row.payment === filters.payment) &&      // ✓ Active
    (!filters.status || row.status === filters.status) &&          // ✓ Active
    (!filters.category || row.category === filters.category)       // ✓ Optional (explicit request)
  );
  // Chart shows full category distribution given payment/status filters
}
```

**Rule:** Each breakdown chart filters by (date range + all active dims EXCEPT its own dimension).

---

## 7. Payload Budget — Pre-Calculate Before Generating (REQUIRED)

### Estimation

**Before generating S3 (monthly+dimension) queries:**

```
Estimated monthly data size = (expected_rows) × 40 bytes/row

Example:
  sales_monthly: 8,784 rows × 40 = ~351 KB
  web_monthly: 12,000 rows × 40 = ~480 KB
  customers_monthly: 6,000 rows × 40 = ~240 KB
  
  Total new: ~1,071 KB
  Current payload: 524 KB
  Projected total: 1,595 KB (acceptable < 2 MB)
```

### Budget Limits

- **< 1.5 MB:** Optimal; proceed
- **1.5–2 MB:** Acceptable; document and proceed
- **> 2 MB:** STOP; split dashboard or reduce dimensions

### Document in state.md

```yaml
## Payload Budget
- Overview KPIs (Q1): ~180 KB
- All-time breakdowns (Q2-Q3): ~50 KB
- Monthly+dimension queries (Q4-Q6): ~1,071 KB
- HTML/JS boilerplate: ~80 KB
- Total: ~1,381 KB (compresses to ~280 KB gzipped)
```

---

## 8. Known Limitations — Annotation Pattern (REQUIRED)

### Rule

For any widget where data is intentionally limited (all-time only, non-date-filterable, approximation):

```html
<!-- Widget rendered -->
<div id="income-chart"></div>

<!-- Immediately followed by annotation -->
<div class="widget-note">
  ⓘ Income data shown at all-time aggregate level
  (monthly aggregation would exceed cardinality budget — request separately if needed)
</div>
```

### CSS

```css
.widget-note {
  font-size: 0.85em;
  color: #666;
  margin-top: 8px;
  padding: 8px;
  background: #f5f5f5;
  border-left: 3px solid #ff9800;
}
```

---

## 9. Schema Validation at Build Time (REQUIRED)

### The Problem

If a SINK column name changes between Phase 2 and Phase 3, all queries return undefined → `num()` coerces to 0 → silent all-zeros dashboard.

### The Fix

Add validation immediately after Q1 runs:

```javascript
const requiredCols = {
  overview: ['date', 'order_count', 'net_revenue', 'email_sends'],
  sales_daily: ['category', 'payment', 'status', 'revenue', 'order_count'],
  web_daily: ['device', 'source', 'event_type', 'pageviews', 'sessions'],
  customers_daily: ['tier', 'channel', 'revenue']
};

function validateSchemas(results) {
  Object.entries(requiredCols).forEach(([query, cols]) => {
    const row = results[query]?.[0] || {};
    const missing = cols.filter(c => !(c in row));
    if (missing.length) {
      throw new Error(
        `SCHEMA MISMATCH in '${query}':\n` +
        `Missing: [${missing.join(', ')}]\n` +
        `Available: [${Object.keys(row).join(', ')}]\n` +
        `Phase 2 schema changed. Update column names and rebuild.`
      );
    }
  });
}

// Call before RAW assembly
validateSchemas(allQueryResults);
```

---

## 10. Build Loop with Quality Gates

```
STAGE 1: BUILD (Steps 4b-4d)
├─ 4b: Generate queries (all three shapes: S1, S2, S3)
├─ 4c: Build dashboard structure (filters, tabs, widgets)
└─ 4d: Write generate-data.js, connect queries, test run

STAGE 2: VALIDATE (Steps 4e-4h)
├─ 4e: Schema validation (item 9) — STOP if FAIL
├─ 4f: Cardinality validation (item 3) — STOP if truncated
├─ 4g: Spot-check accuracy against Phase 1/2 baselines (items 13-14)
└─ 4h: Filter interaction testing (cross-filter pattern, item 6)

STAGE 3: APPROVE & DOCUMENT (Steps 4i-4l)
├─ 4i: User approval
├─ 4j: Update state.md (Phase 3 block with all metadata)
├─ 4k: Mobile/responsive testing (if required)
└─ 4l: Performance baseline + sign-off
```

Each stage has a quality gate — **cannot proceed until gate passes**.

---

## Handling Discrepancies

**When dashboard values differ from Phase 1 spot-checks:**

1. ✓ Verify date window matches Phase 1 baseline (not rolling 30-day; exact dates)
2. ✓ Check query definitions are identical (same columns, same filters, same grain)
3. ✓ Verify aggregation method (SUM vs COUNT vs DISTINCT)
4. ✓ Confirm SINK schema matches expected columns (run schema validation from item 9)
5. ✓ Check dimension filtering applied consistently across Phase 1 and Phase 3
6. If still unresolved: Document as open item in `state.md` + flag during approval (step 4i)

---

## Implementation Checklist

Before handing off Phase 3:

- [ ] **1. Filters:** Two-tier pattern wired (global date + per-tab dimensions)
- [ ] **2. Shapes:** All three shapes generated (S1, S2, S3)
- [ ] **3. Cardinality:** Expected rows calculated; LIMIT set to 2×; no truncation
- [ ] **4. Non-Additive:** All COUNT DISTINCT documented; handling chosen (A/B/C)
- [ ] **5. Cross-Filter:** Breakdown charts exclude own dimension
- [ ] **6. Payload:** Pre-calculated and documented (< 2 MB)
- [ ] **7. Limitations:** All limited widgets annotated with .widget-note
- [ ] **8. Schema:** Validation passes; required columns present
- [ ] **9. Spot-Check:** Date window matches Phase 1; expected values from state.md
- [ ] **10. Spot-Check:** No hardcoded baselines (read from state.md or all-time metrics)

---

**See also:**
- `phase-3-query-and-filter-design.md` — All 12 architectural patterns detailed
- `phase-3-implementation-checklist.md` — Code-specific pitfalls (items 13-22)

---

**Version:** 2.0.0 (Production-Validated, All 22 Patterns Integrated)
**Last Updated:** 23 July 2026
**Author:** FDE Team
