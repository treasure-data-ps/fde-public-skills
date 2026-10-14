# Phase 3: Testing Checklist & Troubleshooting

## Phase 3 Testing Checklist

Before moving to Phase 4/5, ensure all relevant tests passed:

### Data & Accuracy Tests
- [ ] Query 1 (overall metrics) matches Stage B / Phase 2 sample values
- [ ] Query 2-3 (dimension breakdowns) sum correctly
- [ ] No missing or duplicate rows in results
- [ ] Data freshness acceptable (last update recent)
- [ ] Exclusion rules properly applied
- [ ] Filters work (alone, in pairs, all together)
- [ ] Drill-down flows work end-to-end (if required)
- [ ] Export functionality works (if required)
- [ ] Tab state preserved when switching (if multi-tab)

### Error Handling Tests
- [ ] Query timeout (>30s) shows graceful error message
- [ ] Zero results shows "No data" (not broken)
- [ ] API error shows user-friendly message (not raw SQL)
- [ ] NULL values handled correctly (not "[object Object]")
- [ ] Loading spinner appears during query execution
- [ ] No crashes on invalid filter combinations

### Visual & Design Tests
- [ ] Dashboard matches Phase 1 mockup/wireframe
- [ ] Colors correct (KPI cards, charts, tables)
- [ ] Typography readable (titles, labels not too small)
- [ ] Layout has consistent spacing (not cramped)
- [ ] Charts render without errors (no blank charts)
- [ ] Legends clear and not overlapping
- [ ] Dark mode works (if required)
- [ ] No overlapping UI elements

### Filter & Interaction Tests
- [ ] Date filter works (7d, 30d, 90d, custom)
- [ ] Dimension filters work (single, multi-select)
- [ ] Filter combinations work (date + region + segment)
- [ ] Rapid filter changes don't break dashboard
- [ ] Empty result sets show "No data" gracefully
- [ ] "Select all" option works correctly
- [ ] Reset button clears all filters

### Performance Tests
- [ ] Time-to-first-metric: < 1 second
- [ ] Time-to-interactive: < 3 seconds
- [ ] Time-to-all-data: < 5 seconds
- [ ] Each query < 5 seconds execution time
- [ ] Filter updates < 1 second
- [ ] No memory leaks (dashboard doesn't slow over time)

### Mobile & Responsive Tests (If Required)
- [ ] No horizontal scrolling at any breakpoint
- [ ] Mobile (375px): All content accessible, touch-friendly buttons
- [ ] Tablet (768px): Layout adjusts, no cramping
- [ ] Laptop (1366px): Charts/tables properly sized
- [ ] Desktop (1920px): Full layout without waste
- [ ] Filters accessible on mobile
- [ ] Text readable on mobile (>14px)
- [ ] Charts scale appropriately at each size

### User Experience Tests
- [ ] Dashboard title clear
- [ ] Filters labeled clearly
- [ ] KPI card labels descriptive
- [ ] Chart titles match metric names
- [ ] Data units clear (currency, percentage, count)
- [ ] Last updated timestamp visible
- [ ] No confusing/ambiguous terms

---

## Troubleshooting Phase 3 Issues

| Issue | Root Cause | Resolution |
|-------|-----------|------------|
| **Query error: "column not found"** | Typo or wrong table | Run `tdx describe database.table` to verify columns |
| **Dashboard returns 0 rows** | Filters too strict or wrong WHERE | Test query independently; check exclusion rules |
| **Metrics don't match Stage B / Phase 2 sample** | Query calculation wrong or data changed | Re-run the sample query; compare results |
| **Filter doesn't update dashboard** | Filter value not wired to a `RAW` key | Check the filter-switch logic wired in Step 4d |
| **Dashboard shows wrong date range** | WHERE date clause missing/wrong | Verify Query 1 has date filter applied |
| **Performance very slow (>10s)** | Large dataset or missing indexes | Reduce date range; add indexes; if Workflow path, verify SINK table pre-aggregation |
| **Dashboard looks broken/scrambled** | Data format wrong when injected into template | Re-run `generate-data.js`; check the JSON shape in Step 4d |
| **Filters cause "No data" results** | Filter conditions conflict or no matching data | Loosen filters, verify data exists for selected range |
| **Charts won't render** | Data format mismatch or charting library issue | Verify `RAW` data structure matches what the chart code expects |
| **Mobile layout broken** | Responsive CSS not applied | Check media queries; use browser dev tools to debug |
| **Export file empty** | Query returned 0 rows or export logic broken | Verify query returns data; check export implementation |
| **Loading spinner never disappears** | JS error thrown before render completed | Open browser console; check for a thrown error breaking the render flow |

---

## Common Anti-Patterns to Avoid

❌ **Don't query source tables in Workflow path**
- Defeats the purpose of Phase 2's pre-aggregation
- Query SINK tables instead (dashboard will be fast)

❌ **Don't skip data validation (Step 4f)**
- Delivering wrong numbers damages user trust
- Always spot-check against Stage B / Phase 2

❌ **Don't ignore error handling (Step 4d-Final)**
- Dashboard crashes on edge cases = support burden
- Handle timeouts, nulls, zero results gracefully

❌ **Don't test filters only with happy path**
- Test empty results, rapid changes, combinations
- Edge cases are where bugs hide

❌ **Don't assume mobile works**
- If Phase 1 asked for mobile, test on actual device or emulator
- Desktop layout often breaks on mobile

❌ **Don't type data directly into dashboard.html**
- `generate-data.js` is the only sanctioned source of data (Step 4d)
- Hand-typed numbers go stale the moment source data changes

---

## Quality Gates (MUST PASS ALL)

Before exiting Phase 3:

✅ **Pre-implementation checklist:** all items complete before starting
✅ **Data validation checklist:** all items passing (or documented exception)
✅ **Dashboard testing checklist:** all tests passing (or documented exception)
✅ **User feedback:** "Looks good!" before exiting Phase 3

---

## Manual Validation Checklist Template

Use this after the dashboard renders to verify all filters, widgets, and interactions work correctly. Adapt placeholders for your specific dashboard.

**Dashboard:** `[dashboard_filename.html]`

### Quick Start (20 minutes total)

1. Open dashboard in browser → Press `F12` → **Console** tab
2. Paste the auto-validation script below and press Enter
3. Work through the Manual Test Matrix

### Automated Validation (Browser Console)

```javascript
// Dashboard Auto-Validation
console.log("=== Dashboard Filter Logic Validation ===\n");

// Data structure check
const dataKeys = ['[TAB_1]', '[TAB_2]', '[TAB_3]', '[TREND_1]', '[TREND_2]'];
dataKeys.forEach(k => {
  const len = (RAW[k] || []).length;
  console.log(`✓ RAW.${k}: ${len} records`);
});

// Filter intersection logic example
const filterA = RAW.[TAB_1].filter(r => r.[DIMENSION_1] === '[VALUE_1]').length;
const filterB = RAW.[TAB_1].filter(r => r.[DIMENSION_2] === '[VALUE_2]').length;
const both = RAW.[TAB_1].filter(r =>
  r.[DIMENSION_1] === '[VALUE_1]' && r.[DIMENSION_2] === '[VALUE_2]'
).length;

console.log(`\nIntersection test ([TAB_1] tab):`);
console.log(`  ${[DIMENSION_1]}: ${filterA} records`);
console.log(`  ${[DIMENSION_2]}: ${filterB} records`);
console.log(`  Both: ${both} records`);
console.log(`  ✓ Intersection <= each filter: ${both <= Math.min(filterA, filterB) ? 'PASS' : 'FAIL'}`);

console.log("\n✅ Auto-validation complete!");
```

### Manual Test Matrix

| Test | Filter | Expected Behavior | Result |
|------|--------|-------------------|--------|
| T1.1 | [Dimension 1] → [Value 1] | [KPIs/widgets update] | ☐ PASS ☐ FAIL |
| T1.2 | [Dimension 2] → [Value 2] | [Specific widget updates] | ☐ PASS ☐ FAIL |
| T1.3 | [Dimension 1] + [Dimension 2] | Both filters apply (intersection) | ☐ PASS ☐ FAIL |
| T1.4 | Reset button | All filters → "all", full data restored | ☐ PASS ☐ FAIL |
| CT1 | Set filters on Tab 1, switch to Tab 2 | Tab 2 shows independent state | ☐ PASS ☐ FAIL |
| CT2 | Switch back to Tab 1 | Tab 1 still has original filters | ☐ PASS ☐ FAIL |
| E1 | Filter returns 0 rows | Table shows "No records" message | ☐ PASS ☐ FAIL |
| E2 | Filter returns 1 row | Table shows 1 row, KPIs compute correctly | ☐ PASS ☐ FAIL |
| E3 | No filters (all data) | Dashboard loads < 2 sec, scrolls smoothly | ☐ PASS ☐ FAIL |

### Console Debug Snippets

```javascript
// "Table shows wrong data" — check what's in the filtered set
const filterVal = document.getElementById('[filter-id]').value;
const filtered = RAW.[TAB].filter(r => r.[column] === filterVal || filterVal === 'all');
console.log(`Filtered rows: ${filtered.length}`, filtered[0]);

// "KPI card shows wrong number" — manually verify expected total
const rows = RAW.[TAB].filter(r => r.[dimension] === '[value]');
const total = rows.reduce((a, r) => a + r.[metric], 0);
console.log(`Expected [Metric]: ${total.toLocaleString()}`);
```

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
