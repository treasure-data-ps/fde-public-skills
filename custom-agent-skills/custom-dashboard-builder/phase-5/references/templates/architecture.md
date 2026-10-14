# [Dashboard Name] — Architecture & Technical Reference

**Project Slug:** `<project-name>`  
**Last Updated:** `<YYYY-MM-DD>`  
**Maintained By:** `<team/owner>`  
**Data Freshness:** `<daily/hourly/real-time>`

---

## Overview

This document describes the technical structure of the [Dashboard Name] dashboard, including data sources, metrics, transformations, and how to maintain it.

**Quick Facts:**
- **Type:** Interactive HTML dashboard (single portable file)
- **Data Source:** `<SOURCE_DB>` / `<SINK_DB>` (if Phase 2 workflow)
- **Update Frequency:** `<schedule>`
- **Location:** `./<project-name>/dashboards/dashboard.html`
- **Size:** `<Xmb>` (estimated)

---

## Data Architecture

### Source Data

| Database | Table | Purpose | Rows | Updated |
|----------|-------|---------|------|---------|
| `<SOURCE_DB>` | `<table_1>` | [Description] | ~X | [Frequency] |
| `<SOURCE_DB>` | `<table_2>` | [Description] | ~X | [Frequency] |

### SINK Data (if Phase 2 Workflow)

| Database | Table | Purpose | Built By | Schedule |
|----------|-------|---------|----------|----------|
| `<SINK_DB>` | `<sink_table>` | Pre-aggregated metrics | `./<project-name>/workflows/main.dig` | Daily 02:00 UTC |

**Workflow Location:** `./<project-name>/workflows/main.dig`  
**Incremental Strategy:** `<append-only / 1-day lookback / 7-day lookback>`

---

## Metrics & Calculations

### Core Metrics

| Metric | Formula | Source Table | Column | Exclusions |
|--------|---------|--------------|--------|-----------|
| `<Metric 1>` | SUM(`<column>`) | `<table>` | `<col>` | `<filter>` |
| `<Metric 2>` | COUNT(DISTINCT `<id>`) | `<table>` | `<id_col>` | None |
| `<Metric 3>` | AVG(`<column>`) | `<table>` | `<col>` | `<filter>` |

### Dimensions & Filters

| Dimension | Values | Filter Type | Default |
|-----------|--------|-------------|---------|
| `Date` | [365 days] | Date Range | Last 30 days |
| `Region` | US, EU, APAC, LATAM, EMEA | Multi-select | All |
| `Segment` | [8 values] | Multi-select | All |

---

## Dashboard Structure

### Tabs & Widgets

**Tab 1: [Name]**
- Widget 1: [Type] — [Metric 1] by [Dimension]
- Widget 2: [Type] — [Metric 2] trend
- KPI Card: [Metric 3]

**Tab 2: [Name]**
- Widget 1: [Type] — [Metric 1] comparison
- Table: [Description] — [Row limit] rows

### Filter Hierarchy

**Global Filters** (affect all tabs):
- Date Range
- Region
- Segment Status

**Tab-Specific Filters:**
- Tab 2: Category (multi-select)

---

## Performance Characteristics

| Aspect | Value | Notes |
|--------|-------|-------|
| Query Time | ~X seconds | For [date range] |
| HTML File Size | ~Xmb | Inline data, self-contained |
| Load Time (browser) | ~X seconds | Initial render |
| Update Frequency | [Daily/Hourly/Real-time] | Via Phase 2 workflow or manual refresh |

---

## Data Quality & Known Limitations

### Exclusion Rules

```sql
WHERE
  status != 'test'
  AND created_at IS NOT NULL
  AND <other filters>
```

### Known Issues

1. **[Issue]:** [Description]  
   - Impact: [X] records excluded
   - Workaround: [If applicable]

2. **[Issue]:** [Description]
   - Impact: [X] records excluded
   - Workaround: [If applicable]

---

## Maintenance

### Manual Refresh (Non-Workflow Path)

```bash
cd ./<project-name>/dashboards
SOURCE_DB=<source_db> SINK_DB=<sink_db> node generate-data.js
# Output: dashboard.html (ready to share)
```

### Workflow Refresh (Phase 2 Path)

Workflow runs automatically per schedule. Manual trigger:

```bash
cd ./<project-name>/workflows
td workflow run <workflow-name> --project <project-name>
```

### Deployment

To re-deploy updated dashboard:

```bash
# Phase 3 rebuild
cd ./<project-name>/dashboards
SOURCE_DB=<db> SINK_DB=<db> node generate-data.js

# Or Phase 4 skill rebuild
cd ~/.claude/skills/<skill-name>
npm run build
```

---

## Related Documentation

- **Usage Guide:** `usage_guide.md` — How to use the dashboard
- **Runbook:** `runbook.md` (internal) — Maintenance procedures
- **Access & Ownership:** `access_ownership.md` (internal) — Who maintains this, escalation

---

## Questions?

See the **Usage Guide** for FAQs, or contact the maintainer listed at the top of this document.

---

**Version:** 1.0.0  
**Created:** `<date>`  
**Last Modified:** `<date>`
