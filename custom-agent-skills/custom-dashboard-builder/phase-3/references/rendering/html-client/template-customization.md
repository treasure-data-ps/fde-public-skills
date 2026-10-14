---
name: html-client-template-customization
description: |
  Step-by-step guide to copy the HTML Client template and customize it for a new engagement. Covers template selection, generate-data.js setup, DATA_PLACEHOLDER injection, Pattern A size check, and validation.
---

# Template Customization: HTML Client Dashboard

**Goal:** Copy a canonical template → write `generate-data.js` to query TD and inject results → validate the generated `dashboard.html` opens with real data → never build from scratch or write data by hand.

**Timeline:** 30–60 minutes

---

## Step 1: Copy the Template

Templates are embedded locally in this skill — no external repo needed:

```bash
mkdir -p ./<project-name>/dashboards

# Pick the template that matches your Phase 1 layout:
#   kpi-dashboard.html           → 4 KPI cards + summary section
#   table-dashboard.html         → Sortable/searchable table + 4 summary KPIs
#   multi-chart-dashboard.html   → Line + Bar + Doughnut charts, KPI row

cp templates/kpi-dashboard.html \
   ./<project-name>/dashboards/dashboard-template.html
```

Rename it `dashboard-template.html`. The generated output will be `dashboard.html` — keep them separate so `generate-data.js` can always re-inject fresh data without overwriting the template.

Verify the template has the injection point before proceeding:

```bash
grep 'DATA_PLACEHOLDER' dashboard-template.html
# must print:  <!-- DATA_PLACEHOLDER -->
```

---

> **Styling:** Use the TD palette for any Chart.js series — `["#B4E3E3", "#ABB3DB", "#D9BFDF", "#F8E1B0", "#8FD6D4", "#828DCA", "#C69ED0", "#F5D389", "#6AC8C6", "#5867B8"]` — as the default. Override only if `state.md` specifies customer brand colors under "Visual Preferences".

---

## Step 2: Copy and Customize `generate-data.js`

Copy the canonical starter (embedded locally in this skill):

```bash
cp templates/generate-data.js \
   ./<project-name>/dashboards/generate-data.js
```

The starter contains a working `query()` helper and `num()` normalization function — do not rewrite them. Only change:

| What to change | Where in the file |
|----------------|------------------|
| DB env var name (if not SOURCE_DB / SINK_DB) | `var DB = process.env.SOURCE_DB ...` line |
| SQL table names and column names | `── Queries ──` section |
| RAW payload keys and values | `── Assemble RAW payload ──` section |
| `summary.source` string | Inside the RAW object |

### Check exact column names first

Before editing any SQL, run `tdx describe` to confirm every column name:

```bash
tdx describe <database>.<table>
```

Column names from TD must match exactly — including underscores, case, and abbreviations.

### Minimum edit: KPI dashboard

```javascript
// In the ── Queries ── section, replace the placeholder SQL:
var kpiRows = query(
  'SELECT' +
  '  SUM(purchase_amount)  AS total_revenue,' +  // ← replace with your column
  '  COUNT(*)              AS order_count,' +
  '  AVG(purchase_amount)  AS avg_order_value' +
  ' FROM acme_orders_sink' +                      // ← replace with your table
  ' LIMIT 1'
);

// In the ── Assemble RAW payload ── section:
var RAW = {
  kpis: [
    { label: 'Total Revenue',   value: num(kpi.total_revenue, 0),   format: 'currency' },
    { label: 'Orders',          value: num(kpi.order_count, 0),     format: 'number'   },
    { label: 'Avg Order Value', value: num(kpi.avg_order_value, 2), format: 'currency' },
    { label: 'Customers',       value: num(kpi.order_count, 0),     format: 'number'   }
  ],
  summary: {
    source:  DB + '.acme_orders_sink',  // ← replace with your table
    period:  'All time',
    records: num(kpi.order_count, 0),
    updated: new Date().toLocaleString()
  }
};
```

### The `num()` rule

TD returns all numeric columns as strings. Always wrap with `num()`:

```javascript
// ✅ correct
value: num(kpi.total_revenue, 0)   // rounds to integer
value: num(kpi.avg_order_value, 2) // rounds to 2 decimal places

// ❌ wrong — will show NaN or "$0" in the dashboard
value: kpi.total_revenue
value: parseFloat(kpi.total_revenue)  // loses rounding guarantee
```

---

## Step 3: Run `generate-data.js`

```bash
SOURCE_DB=your_database node generate-data.js
```

Expected output:

```
Querying your_database...
Payload size: 14.2 KB
Written: /path/to/dashboard.html (62 KB)
Open: open dashboard.html
```

If you see `ERROR: Set SOURCE_DB or SINK_DB environment variable` — you forgot the env var prefix.

If you see a tdx error — the SQL has wrong table or column names. Fix and re-run.

---

## Step 4: Confirm Pattern A Size Budget

`generate-data.js` writes the data directly into `dashboard.html` via the `<!-- DATA_PLACEHOLDER -->` injection point:

```
dashboard-template.html + <script>var RAW = {...};</script>  →  dashboard.html
```

The delivered `dashboard.html` is fully self-contained. Recipients double-click to open — no server needed. This is the only sanctioned pattern in the lite skill.

**Target: stay under 2MB.** If the payload is approaching or exceeding that:

1. Pre-aggregate more in SQL (GROUP BY instead of row-level) to reduce row count.
2. Drop unused columns from the RAW payload.
3. If the dataset genuinely cannot fit, flag this to the user as an exception — a server-hosted `data.json` pattern exists but breaks the "double-click and open" portability this skill promises, so treat it as a last resort rather than a routine choice.

---

## Step 5: Open and Validate

```bash
open dashboard.html
# or: preview_document dashboard.html  (in Treasure Work)
```

**Spot-check checklist:**

```
□ KPI values show real numbers (not dashes or zeros)
□ Charts display real data with your actual dimension values on axes
□ Table rows show real records (not "Acme Corp" / "Tech Inc" sample data)
□ Summary section shows correct database + table name
□ No console errors  (F12 → Console)
□ Numbers match a manual tdx spot-check (run same query in tdx, compare)
□ File is under 2MB  (for email delivery)
```

Common causes of flat zeros / NaN:
- String columns not wrapped with `num()` — most common
- RAW key name in the template doesn't match what `generate-data.js` assembled
- Query returned 0 rows (check table name and database)

---

## Step 6: Update the Dashboard Title

The only line that should be edited directly in `dashboard-template.html` between engagements is the title:

```html
<!-- BEFORE -->
<h1>KPI Dashboard</h1>

<!-- AFTER -->
<h1>Acme Corp — Revenue Overview</h1>
```

After changing the title, re-run `generate-data.js` to regenerate `dashboard.html`.

---

## Step 7: Deliver

The generated `dashboard.html` is fully self-contained. Delivery options:

| Method | Steps |
|--------|-------|
| Email | Attach `dashboard.html` |
| Confluence | Upload as attachment to the page, share page URL |
| Google Drive / OneDrive | Upload, share link — recipients download and open |
| Web server | Upload to static host, share URL |

---

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| KPIs show `$0` or `NaN` | `num()` missing on numeric field | Wrap every numeric TD column with `num()` |
| `<!-- DATA_PLACEHOLDER -->` not replaced | Forgot to re-run `generate-data.js` after editing template | Run `node generate-data.js` again |
| `ERROR: dashboard-template.html missing <!-- DATA_PLACEHOLDER -->` | Template renamed or placeholder removed | Check template filename matches `TEMPLATE_PATH` in generate-data.js |
| `tdx: command not found` | tdx not in PATH for Node child_process | Use full path in query(): `execSync('/usr/local/bin/tdx ...')` |
| Query returns 0 rows | Wrong table or database name | Run `tdx describe <db>.<table>` — confirm names |
| File approaching 2MB | Too many rows in RAW | Pre-aggregate in SQL (GROUP BY instead of row-level) |
| Charts blank but no console error | RAW key name mismatch | Template reads `RAW.by_region`; confirm `generate-data.js` assembles that exact key |

---

## References

- `SKILL.md` — rendering engine overview, Pattern A rules
- `getting-started.md` — step-by-step from zero to first dashboard
- `html-dashboard-patterns.md` — multi-tab, filter, chart type patterns
- `config-schema.md` — RAW object shape for each template
- `../../steps.md` → Step 4c (template selection), Step 4d (data connection), Step 4e (render)

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
