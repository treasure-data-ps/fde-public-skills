# Getting Started: Create Your First HTML Client Dashboard

**Complete step-by-step guide to building a self-contained HTML dashboard.**

---

## Overview

HTML Client = one `.html` file with data embedded at generation time. No server, no dependencies.

**How it works:**

```
<skill_dir>/project_templates/dashboard_template/   ← shipped with this skill
  dashboard.template.html       ← layout + rendering code (no data)
  generate-data.js               ← queries TD → injects data into HTML
agent_outputs/<project_slug>/dashboards/
  dashboard.html                 ← generated output (template + data merged)
```

`generate-data.js` runs `tdx query` commands, collects results, and writes them into `dashboard.html` by replacing a `<!-- DATA_PLACEHOLDER -->` comment in the template. The delivered file is fully self-contained.

**Timeline:** 30–60 minutes

---

## Step 1: Copy the Template

The template ships with this skill. Copy it into the project:

```bash
mkdir -p agent_outputs/<project_slug>/dashboards
cp "<skill_dir>/project_templates/dashboard_template/dashboard.template.html" agent_outputs/<project_slug>/dashboards/dashboard.template.html
```

The template contains a `<!-- DATA_PLACEHOLDER -->` comment where `generate-data.js` will inject the data block. Leave this comment in place.

---

## Step 2: Write `generate-data.js`

This is the only place that touches data. It runs TD queries and injects results into the template.

```javascript
const { execSync } = require('child_process');
const fs = require('fs');

// ─── Config ─────────────────────────────────────────────────────────────────
const SOURCE_DB = process.env.SOURCE_DB || 'your_idu_output_db';

// ─── Query helper ────────────────────────────────────────────────────────────
function query(sql) {
  const escaped = sql.replace(/"/g, '\\"');
  const result = execSync(
    `tdx --json query -d "${SOURCE_DB}" "${escaped}" 2>/dev/null`,
    { encoding: 'utf8' }
  );
  return JSON.parse(result);
}

// ─── Numeric normalization ────────────────────────────────────────────────────
function num(v, decimals = 2) {
  return Math.round(parseFloat(v || 0) * 10 ** decimals) / 10 ** decimals;
}

// ─── Run queries ──────────────────────────────────────────────────────────────
async function main() {
  const overview = query(`
    SELECT metric_name, metric_value
    FROM your_summary_table
    LIMIT 100
  `).map(r => ({ ...r, metric_value: num(r.metric_value) }));

  const by_segment = query(`
    SELECT segment, COUNT(*) AS count
    FROM your_table
    GROUP BY segment
    ORDER BY count DESC
  `).map(r => ({ ...r, count: num(r.count, 0) }));

  // ─── Inject into template ───────────────────────────────────────────────────
  const data = { overview, by_segment };
  const dataBlock = `<script>var RAW = ${JSON.stringify(data)};<\/script>`;

  const template = fs.readFileSync('dashboard.template.html', 'utf8');
  const html = template.replace('<!-- DATA_PLACEHOLDER -->', dataBlock);
  fs.writeFileSync('dashboard.html', html);

  console.log(`✅ dashboard.html written (${Buffer.byteLength(html, 'utf8')} bytes)`);
}

main().catch(err => { console.error(err); process.exit(1); });
```

**Rules:**
- Never write data values directly into `dashboard.html` or the template
- Always use `num()` to normalize string-numbers coming out of TD queries
- Keep compact JSON (no `indent` flag) — reduces file size by ~30%

---

## Step 3: Run `generate-data.js`

```bash
SOURCE_DB=your_idu_output_db node generate-data.js
# ✅ dashboard.html written (142847 bytes)
```

**Payload size budget (tiered):** under 500KB inline is ideal (fast load, easiest to share); up to 2MB inline is acceptable (modern browsers handle it fine); beyond 2MB, switch to Pattern B — write `data.json` separately instead of inlining. See `html-dashboard-patterns.md` → "Data Size Budget & Optimization" for the full tiered guidance and the Pattern B snippet.

---

## Step 4: Open and Validate

```bash
# Simplest — just open in browser (works offline, no server needed)
open dashboard.html

# Or use preview_document in Treasure Work
preview_document dashboard.html
```

**Spot-check checklist:**

```
□ Charts/KPIs show real numbers (not dashes or zeros)
□ No console errors (F12 → Console)
□ Data matches a manual tdx query spot-check
□ File is under 500KB ideally, under 2MB acceptable (email-safe)
```

If charts are flat at 0: the most common cause is string numbers — verify `num()` normalization is applied to every numeric field.

---

## Step 5: Where the Dashboard Lives

The generated `dashboard.html` is fully self-contained and stays in `agent_outputs/<project_slug>/dashboards/` in the Work Folder. Open it from there; download it to share it like any other file. No server, upload or hosting step.

---

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| KPIs show NaN / $0 | String numbers from TD | Apply `num()` to all numeric fields |
| `dashboard.html` not updated | Forgot to re-run `generate-data.js` | Run `node generate-data.js` again |
| File > 2MB | Too many rows inlined | Switch to Pattern B or pre-aggregate |
| Charts blank but no error | Missing key in `RAW` | Check `dashboard.template.html` for expected key names |
| `tdx: command not found` | tdx CLI not in PATH | Ensure tdx is installed and authenticated |

---

## References

- `html-dashboard-patterns.md` — Pattern A vs Pattern B deep dive, UI components, filters, chart types
- `SKILL.md` — rendering engine overview and template locations

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
