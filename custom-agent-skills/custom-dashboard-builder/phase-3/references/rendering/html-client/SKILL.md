---
name: fde-custom-dashboard-html-client
description: "INTERNAL — invoked by rendering index (phase-3/references/rendering/SKILL.md) only. Do not trigger directly. HTML Client rendering engine: self-contained .html files, no backend, shareable via email/Confluence. Uses generate-data.js for data injection."
---

# HTML Client-Side Dashboard Rendering Engine

**Platform:** Browser-based (all platforms)  
**Build time:** 10-25 minutes  
**Complexity:** Simple (HTML/CSS/JavaScript)  
**Best for:** Shareable reports, email delivery, Confluence embedding  
**Server requirement:** None (data must be fully inlined)

---

## Zero-Server Requirement: Two Deployment Patterns

### ⚠ Critical Design Rule

HTML Client = **zero server dependency**. Data must be fully inlined in the HTML at delivery time — but **never typed in manually**. `generate-data.js` is always the source of the data; the only question is whether it writes to a separate `data.json` file (Pattern B) or injects directly into the HTML (Pattern A).

**Pattern A — `generate-data.js` injects data inline (use when < 2MB):**

`generate-data.js` queries TD and writes the results directly into `dashboard.html` by replacing a placeholder comment, or produces the final single-file HTML:

```javascript
// generate-data.js
const data = await runQueries();
const dataBlock = `<script>var RAW = ${JSON.stringify(data)};</script>`;
const html = fs.readFileSync('dashboard-template.html', 'utf8')
               .replace('<!-- DATA_PLACEHOLDER -->', dataBlock);
fs.writeFileSync('dashboard.html', html);
```

The delivered `dashboard.html` is fully self-contained:
```html
<script>var RAW = { overview: [...], by_segment: [...] };</script>
<!-- rendering code reads RAW -->
```

✅ **Works by:**
- Double-click on local file
- Email attachment (recipients download & open)
- Confluence upload (download & open)
- Google Drive / cloud storage

**Pattern B — `generate-data.js` writes a separate `data.json` (only if > 2MB):**

```javascript
// generate-data.js
const data = await runQueries();
fs.writeFileSync('data.json', JSON.stringify(data));
```

The HTML fetches at runtime:
```html
<script>
  fetch('data.json')
    .then(r => r.json())
    .then(RAW => renderDashboard(RAW))
</script>
```

❌ **Does NOT work in:**
- Double-click (CORS blocks file:// fetches)
- Email attachment (data.json lost)
- Confluence (can't host data.json separately)

✅ **Only works with:**
- Web server (Nginx, Node.js, etc.)
- Same directory with explicit server (`npx serve .`)

**Rule (Lite):** Pattern A is the only sanctioned pattern in the lite skill — a single portable `dashboard.html` with data inlined. Pattern B (separate `data.json`, server-hosted) is **out of scope for lite** — it breaks the "double-click and open" portability guarantee this skill promises. If a dataset genuinely exceeds 2MB, flag it to the user as an exception rather than silently switching patterns. In all cases, `generate-data.js` is the only source of data — never write data values into `dashboard.html` by hand.

---

## Templates

Templates are embedded locally — no external repo needed:
`./templates/` (`kpi-dashboard.html`, `table-dashboard.html`, `multi-chart-dashboard.html`, `generate-data.js`, `render.js`, `README.md`)

---

## Quick Start

> **`generate-data.js` is mandatory for every HTML Client dashboard.** It is the only sanctioned way to populate `data.json` — never inline query results manually or hardcode data values in the HTML.

1. **Copy template** — Pick one of 3 templates (KPI, Table, Multi-Chart) from `./templates/` (embedded locally in this skill)
2. **Write `generate-data.js`** — Query script that runs `tdx query` and writes `data.json`. This file is **required**; the dashboard will not have real data without it.
3. **Run `generate-data.js`** — `node generate-data.js` → produces `data.json`
4. **Serve and open** — `npx serve .` → open `http://localhost:3000` (or use `preview_document` in Treasure Work)
5. **Validate** — confirm charts/tables show real data
6. **Share** — zip `dashboard.html` + `render.js` + `data.json` and send

---

## Available Templates

### 1. KPI Dashboard (`kpi-dashboard.html`)

**Use when:** Simple metrics overview, shareable report  
**Best for:** Executive summary, email distribution  
**Build time:** 10 minutes  
**File size:** ~207KB (includes inlined Chart.js)  
**Contains:**
- 4 KPI cards with trend indicators
- Summary information section
- Responsive grid layout
- Fully embedded, no backend needed

---

### 2. Table Dashboard (`table-dashboard.html`)

**Use when:** Data exploration with sorting and filtering  
**Best for:** Customer data, detailed records  
**Build time:** 15 minutes  
**File size:** ~209KB (includes inlined Chart.js)  
**Contains:**
- Sortable, searchable data table
- Status filter dropdown
- Full-text search
- CSV export button
- 4 summary metric cards
- Click column headers to sort

---

### 3. Multi-Chart Dashboard (`multi-chart-dashboard.html`)

**Use when:** Comprehensive analysis with multiple visualizations  
**Best for:** Executive reviews, comprehensive reporting  
**Build time:** 20 minutes  
**File size:** ~208KB (includes inlined Chart.js)  
**Contains:**
- 4 KPI metric cards
- Line chart (dual-axis: sales + orders)
- Bar chart (by region)
- Doughnut/pie chart (distribution)
- Horizontal bar chart (top customers)
- All charts responsive to window resize

---

## Key Advantages

✅ **Self-contained** — One .html file, no dependencies  
✅ **Shareable** — Email, Confluence, Google Drive  
✅ **Works offline** — No internet required after download  
✅ **Fast** — No server roundtrips, instant filtering  
✅ **Browser-native** — Works in all modern browsers  
✅ **Print-friendly** — Generate PDF from browser  
✅ **No build process** — Just open in browser  

---

## How to Customize

### 1. Update Dashboard Title
Find this line in `dashboard.html`:
```html
<h1>KPI Dashboard</h1>
```
Change to your title — this is the only line to edit in `dashboard.html` between customers.

### 2. Update Data — via `generate-data.js` (mandatory)
**Do not manually edit data values in `dashboard.html` or `render.js`.**
`generate-data.js` is the single entry point for all data changes. Update `SOURCE_DB` / `SINK_DB` env vars and re-run:
```bash
SOURCE_DB=new_db SINK_DB=new_sink node generate-data.js
```
This regenerates `data.json` with fresh query results. `render.js` picks it up automatically on next page load.

### 3. Update Chart / Table Structure
To add a new chart or table, edit `render.js` — add a new `makeChart()` or `makeBars()` call referencing a new key in `data.json`. Then add the corresponding `<canvas>` or `<div>` to `dashboard.html`.

### 4. Change Colors
Find the CSS variables at the top of `dashboard.html`:
```css
:root {
  --primary: #3b82f6;      /* Blue */
  --success: #10b981;      /* Green */
  --warning: #f59e0b;      /* Orange */
  --danger: #ef4444;       /* Red */
}
```

Update colors (use hex codes).

---

## Data Format Reference

### KPI Dashboard Data

```javascript
{
  metrics: {
    metric1: 1500000,
    metric2: 4500,
    metric3: 333.33,
    metric4: 12.5
  }
}
```

### Table Dashboard Data

```javascript
const allData = [
  { 
    id: 1, 
    name: 'Customer Name', 
    revenue: 145000, 
    orders: 25, 
    status: 'Active' 
  }
];
```

### Chart Dashboard Data

```javascript
{
  labels: ['Jan', 'Feb', 'Mar', ...],
  datasets: [{
    label: 'Sales',
    data: [50000, 48000, 52000, ...]
  }]
}
```

---

## Deployment Options

### Email
- Download .html file
- Attach to email
- Recipients open in browser
- Works offline

### Confluence
1. Go to Confluence page
2. Click "Insert" → "Attachments"
3. Upload .html file
4. Share page URL
5. Recipients download and open

### Web Server
1. Upload .html to server
2. Share URL: `https://yourserver.com/dashboards/sales.html`
3. Recipients open in browser

### Cloud Storage
1. Upload to Google Drive / OneDrive / Dropbox
2. Share link
3. Recipients download and open

---

## Browser Compatibility

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | Latest | ✅ Full |
| Firefox | Latest | ✅ Full |
| Safari | Latest | ✅ Full |
| Edge | Latest | ✅ Full |
| IE 11 | - | ⚠️ Limited (no ES6) |

---

## Performance Tips

1. **Limit table rows** — Keep < 5000 rows for fast filtering
2. **Optimize data size** — Remove unnecessary fields
3. **Minify HTML** — Use online minifiers to reduce file size
4. **Compress images** — If adding logos
5. **Cache in browser** — Users can save .html locally

---

## Testing Checklist

- [ ] **`generate-data.js` exists** and produces `data.json` without errors (`node generate-data.js`)
- [ ] Open .html in browser (works offline?)
- [ ] Charts render correctly
- [ ] Filters work (click, type, select)
- [ ] Sorting works (click headers)
- [ ] CSV export downloads
- [ ] Mobile layout responsive
- [ ] No console errors (F12 → Console)
- [ ] Print to PDF works
- [ ] File size < 1MB (for email)

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Chart not showing | Data format wrong | Check dataset labels match data |
| Sorting not working | Column index wrong | Verify onclick handler passes correct index |
| Filters broken | Variable names mismatch | Check HTML id vs JavaScript querySelector |
| Mobile layout broken | CSS media query issue | Verify mobile breakpoints in CSS |
| CSV export not working | Blob API not supported | Test in modern browser (IE11 won't work) |

---

## File Size Optimization

If .html file is too large:

1. **Remove unused template code** — Delete chart divs you don't need
2. **Reduce sample data** — Limit rows to essential data
3. **Minify CSS/JS** — Use online tools
4. **Chart.js is inlined directly in the HTML** (not loaded via CDN) so the file works fully offline; this adds a fixed ~200 KB but is not itself optimizable without breaking offline support
5. **Remove comments** — Clean up developer comments

---

## Security Notes

⚠️ **Data Privacy:**
- HTML files can be saved locally
- Don't include highly sensitive data
- Users should delete after use

⚠️ **XSS Protection:**
- Use `textContent` instead of `innerHTML` for dynamic content
- Sanitize any user input

⚠️ **CORS:**
- If fetching data from API, API must allow CORS
- Or embed data directly in HTML (safer)

---

## Next Steps

→ **[getting-started.md](getting-started.md)** — Step-by-step: copy template → write `generate-data.js` → run → validate. Start here every engagement.

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
