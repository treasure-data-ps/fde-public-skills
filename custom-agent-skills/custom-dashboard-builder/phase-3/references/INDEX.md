# Phase 3 References Directory

This directory contains detailed, reusable patterns for Phase 3: Build + Validate Interactive Dashboard.

**Main file:** `../build-interactive-dashboard-guide.md` (the entry point — start here)

---

## Reference Files

| File | Purpose |
|---|---|
| **[steps.md](steps.md)** | All steps 4b–4l: query scaffolding, structure, data connection, rendering, validation, filters, performance, approval. |
| **[query-patterns-for-dashboards.md](query-patterns-for-dashboards.md)** | SQL patterns for dashboard queries: KPI totals, time series, top-N rankings, filtering, joins, performance. |
| **[testing-troubleshooting.md](testing-troubleshooting.md)** | Testing checklist, troubleshooting guide, common anti-patterns, quality gates. |
| **[filter-architecture.md](filter-architecture.md)** | Filter design patterns, row-level vs pre-aggregated architecture, Golden Rules. |
| **[phase-3-data-patterns.md](phase-3-data-patterns.md)** | Non-Workflow vs Workflow path SQL patterns, build loop stages, data accuracy handling. |
| **[rendering/](rendering/SKILL.md)** | HTML Client rendering engine: templates, patterns, deployment, customization. |

---

## How to Use These Files

### I'm implementing Phase 3 — where do I start?
→ Open `../build-interactive-dashboard-guide.md` (the main file with quick reference)

### I need detailed guidance for a specific step
→ Open [`steps.md`](steps.md) — all steps 4b through Phase Exit are in one file. Jump directly to the step header (e.g., `## Step 4f`).

### I need to test or troubleshoot
→ See [`testing-troubleshooting.md`](testing-troubleshooting.md)

### I want to understand Phase 3 architecture and workflow
→ See "Key Concept" section in `../build-interactive-dashboard-guide.md` for Non-Workflow vs Workflow path architecture and the build+validate loop. (That routing decision is made in Phase 1's scoring rubric — by Phase 3, the path is already confirmed.)

---

## Quick Navigation by Step

| Step | File |
|---|---|
| **All steps 4b–4l** | **`steps.md`** |
| Testing & Troubleshooting | `testing-troubleshooting.md` |
| SQL query patterns for dashboard build | `query-patterns-for-dashboards.md` |
| Rendering engine (HTML Client) | `rendering/SKILL.md` |

---

## Key Principles

- **Main file is a quick reference** with step overview and links to deep dives
- **References are modular** — each file is self-contained and progressively detailed
- **Build+validate loop** — Phase 3 iterates until dashboard is satisfactory
- **Data accuracy first** — Step 4f validation is a critical gate (must pass before continuing)
- **User approval required** — Step 4i feedback must be positive to exit Phase 3

---

## Phase 3 Output Summary

At end of Phase 3, user receives:
- ✅ Live interactive dashboard (`dashboard.html`)
- ✅ All filters working correctly
- ✅ Data accuracy certified
- ✅ Performance baseline established
- ✅ Mobile/responsive validated (if required)
- ✅ User satisfied
- ✅ Technical documentation complete (recorded in `state.md`)

**Dashboard is ready for optional Phase 4 (automate & deploy) or Phase 5 (handoff documentation)**

---

## Related Files

- `../../phase-1/requirements-gathering-guide.md` — Phase 1 output (database, tables, metrics, dimensions)
- `../../phase-2/deploy-workflow-guide.md` — Phase 2 output (SINK tables, workflow scheduled, if used)
- `../build-interactive-dashboard-guide.md` — This phase (dashboard building)

---

## Phase 3 Testing Checklists

Comprehensive testing checklists included in `testing-troubleshooting.md`:
- Data & accuracy tests
- Error handling tests
- Visual & design tests
- Filter & interaction tests
- Performance tests
- Mobile & responsive tests (conditional)
- User experience tests

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
