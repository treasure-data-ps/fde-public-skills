# [Dashboard Name] — Usage Guide

**Project Slug:** `<project-name>`  
**Last Updated:** `<YYYY-MM-DD>`  
**For Questions:** Contact `<support-contact>`

---

## Getting Started

### Opening the Dashboard

The dashboard is a single HTML file — no installation required:

**Option 1: Local File**
```
Double-click: ./<project-name>/dashboards/dashboard.html
```

**Option 2: Web Server**
```bash
cd ./<project-name>/dashboards
python3 -m http.server 8000
# Open: http://localhost:8000/dashboard.html
```

**Option 3: Email/Share**
Send `dashboard.html` directly — it works offline and on any device.

---

## Dashboard Overview

### What You'll See

**[Tab 1 Name]**
- Executive summary of key metrics
- KPI cards show [Metric 1], [Metric 2], [Metric 3]
- Trend chart showing last 30 days of [Metric 1]

**[Tab 2 Name]**
- Detailed breakdown by [Dimension]
- Comparison view of [Metric 1] vs [Metric 2]
- Interactive table with [description]

---

## Using Filters

### Filter Types

| Filter | Purpose | How to Use |
|--------|---------|-----------|
| **Date Range** | Adjust time window | Click dropdown, select preset or custom range |
| **Region** | Filter by geography | Multi-select: check one or more regions |
| **Segment** | Filter by customer tier | Multi-select: check one or more segments |

### Filter Examples

**Example 1: Last 7 Days, US Only**
1. Date Range → "Last 7 days"
2. Region → Select "US" (uncheck others)
3. Dashboard updates automatically

**Example 2: Compare All Regions, Last Quarter**
1. Date Range → "QTD"
2. Region → Leave all checked
3. View "Revenue by Region" chart to compare

### Important Notes

- **Filters apply to all charts** (Tab 1 and Tab 2)
- **Updates are instant** — no manual refresh needed
- **Clear filters** by refreshing the page

---

## Reading the Metrics

### Key Metrics Explained

**[Metric 1]: [Full Description]**
- Formula: SUM([column]) from [table]
- Excludes: [filter conditions]
- Updated: [frequency]
- Example: "Total Revenue is the sum of all sales transactions in USD, excluding test orders"

**[Metric 2]: [Full Description]**
- Formula: COUNT(DISTINCT [column]) from [table]
- Excludes: [filter conditions]
- Updated: [frequency]
- Example: "Unique Customers is the count of distinct customer IDs with at least one transaction"

**[Metric 3]: [Full Description]**
- Formula: [calculation]
- Excludes: [filter conditions]
- Updated: [frequency]
- Example: "Average Order Value is revenue divided by order count"

### What These Numbers Mean

- **[Metric 1] = $4.5M:** Total revenue for selected date range and filters
- **[Metric 2] = 15K:** Number of unique customers
- **[Metric 3] = $300:** Average spend per customer

---

## Common Tasks

### Task 1: Check Revenue by Region

1. Go to **Tab 2: Regional Breakdown**
2. Leave Region filter as "All"
3. Chart shows revenue for each region (US, EU, APAC, LATAM, EMEA)
4. Click on a bar to compare with others

### Task 2: Spot Trends Over Time

1. Go to **Tab 1: Overview**
2. Look at "Revenue Trend" line chart
3. Adjust Date Range filter to zoom in/out
4. Rising line = growth, flat line = stable, dropping line = decline

### Task 3: Segment Analysis

1. Go to **Tab 2: Segment Deep Dive**
2. Segment filter → Select "Premium" customers only
3. Compare their metrics to overall (use second browser tab for side-by-side)

### Task 4: Export Data

Dashboard supports export:
- **Screenshot:** Press Ctrl+P / Cmd+P → Print to PDF
- **Copy Table:** Select table → Ctrl+C / Cmd+C → Paste into Excel
- **Raw HTML:** Share the file directly via email

---

## Troubleshooting

### Problem: Numbers Look Wrong

**Check 1: Filter Settings**
- Date range might be too narrow (e.g., "Last 7 days" vs "Last 30 days")
- Region filter might exclude relevant data
- Try clearing all filters and refreshing

**Check 2: Data Freshness**
- Dashboard is updated [daily/hourly]
- Last updated: See the footer of the dashboard
- If data looks stale (> 1 day old), contact support

**Check 3: Browser Issues**
- Clear browser cache: Ctrl+Shift+Delete / Cmd+Shift+Delete
- Try a different browser (Chrome, Firefox, Safari)

### Problem: Dashboard Won't Open

**Solution 1:** Open in a different browser  
**Solution 2:** Copy the file to a local folder and try again  
**Solution 3:** Try from a web server:
```bash
python3 -m http.server 8000
# Open http://localhost:8000/dashboard.html
```

### Problem: Filters Not Working

- Refresh the page (F5 or Cmd+R)
- Try clearing one filter at a time to isolate the issue
- Check browser console for errors (F12 → Console)

---

## FAQs

**Q: Can I modify the dashboard?**  
A: The dashboard is read-only. To add metrics or change filters, contact [maintainer-name].

**Q: How often is the data updated?**  
A: [Daily at 2 AM UTC / Hourly / Real-time]. See "Data Freshness" section above.

**Q: Can I share this dashboard?**  
A: Yes! Email the `dashboard.html` file. It works on any device without installation.

**Q: Where does the data come from?**  
A: `<SOURCE_DB>.<table>` (or `<SINK_DB>.<sink_table>` if using a pre-aggregated workflow). See "Architecture" document for details.

**Q: Why do numbers differ from [other_system]?**  
A: Possible reasons:  
- Different date ranges or filters  
- Different exclusion rules (e.g., test orders)  
- Different aggregation logic  
- Timing: other system updated on different schedule  
Contact support for clarification.

**Q: How do I report a bug?**  
A: Email `<support-contact>` with:  
- Screenshot of the issue
- What filter(s) you were using
- Expected vs actual result

---

## Data Dictionary

### Available Dimensions

| Dimension | Values | Count |
|-----------|--------|-------|
| Region | US, EU, APAC, LATAM, EMEA, Internal | 6 |
| Segment | Premium, Standard, Trial | 3 |
| Category | [list all 8+] | 8+ |

### Time Zones & Dates

- **Dashboard Timezone:** UTC (all dates/times in UTC)
- **Default Date Range:** Last 30 days rolling
- **Historical Data:** Back to `<YYYY-MM-DD>`
- **Cutoff Time:** Daily snapshot at 02:00 UTC

---

## Support & Escalation

### L1: Usage Questions (General Support)
- Email: `<support-contact>`
- Response Time: 1 business day
- Examples: "How do I filter by Region?", "What does this metric mean?"

### L2: Data Issues (Accuracy/Discrepancies)
- Email: `<data-team-contact>`
- Response Time: 1-2 business days
- Examples: "Revenue is off by $100K", "Customers count looks wrong"

### L3: Platform/Technical (Escalation)
- Email: `<platform-team-contact>`
- Response Time: 2-3 business days
- Examples: "Dashboard won't open", "File is corrupted"

---

## Related Documents

- **Architecture & Technical Reference:** `architecture.md` — How the dashboard works
- **Runbook** (internal): Maintenance procedures and troubleshooting
- **Access & Ownership** (internal): Who maintains this and how to get access

---

**Need more help?** Contact `<support-contact>` with your question.

---

**Version:** 1.0.0  
**Created:** `<date>`  
**Last Modified:** `<date>`
