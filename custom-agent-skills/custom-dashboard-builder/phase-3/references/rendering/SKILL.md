---
name: fde-custom-dashboard-phase-3-rendering-html-client
description: Build interactive HTML Client dashboards with inlined data (Pattern A)
trigger_keywords: ["HTML Client", "embed dashboard", "inlined data", "single file dashboard"]
---

# Phase 3: Dashboard Rendering — HTML Client Only

**This phase has ONE rendering engine: HTML Client (Pattern A — data inlined into a single portable file).**

This skill uses only the HTML Client approach. No engine selection step.

## Quick Start

See **`./html-client/SKILL.md`** for:
- How to embed pre-aggregated data
- Chart.js inlining (no CDN)
- Filter implementation (dashboard + tab level)
- Optimization patterns (pre-aggregation, numeric coercion, refresh on demand)

## What is HTML Client?

- **Single file:** `dashboard.html` with all data inlined
- **Portable:** Works offline, shareable via email/zip
- **Self-contained:** No server, no API, no CDN calls
- **Fast:** Data pre-aggregated by `generate-data.js`

## Next Step

→ Open `./html-client/SKILL.md` to build your dashboard

---
