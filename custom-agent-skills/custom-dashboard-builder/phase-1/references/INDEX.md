# Phase 1 References Directory (Stage A + Stage B)

This directory contains detailed, reusable patterns for Phase 1: Requirements Gathering (Stage A) & Data Discovery (Stage B).

**Main file:** `../requirements-gathering-guide.md` (the entry point — start here)

---

## Reference Files

### Stage A: Requirements Gathering

| File | Purpose |
|---|---|
| **[steps-1pre.md](steps-1pre.md)** | Session-setup questions (Setup-A through Setup-E). Includes two Special Cases: (1) `.dash`/Sisense export fast-track (converts file, prefills Stage A/B), (2) Treasure Insights datamodel API fast-track (fetches schema via API, prefills Stage A/B). Also includes AskUserQuestion templates and batch summary tables. |
| **[treasure-insights-api-integration.md](treasure-insights-api-integration.md)** | Treasure Insights Reporting API reference and extraction logic. Documents regional endpoints, authentication, datamodel endpoints, and how to extract metrics/dimensions/joins from API responses. Used by the Treasure Insights API Special Case. |
| **[steps-1a-1o.md](steps-1a-1o.md)** | Core requirements steps (1a–1o): metrics, dimensions, filters, date range, sharing, exclusions. Includes AskUserQuestion templates and iterative patterns. |
| **[steps-1k-1n-optional.md](steps-1k-1n-optional.md)** | Optional steps: mobile, compliance, data complexity, drill-down, CDP activation. |
| **[steps-1p-1t.md](steps-1p-1t.md)** | Dashboard Complexity Scoring (0-6), workflow config, agent config, Stage A→B bridging. Includes field capture tables and Stage A Quality Checklist. |
| **[step-1u-finalization.md](step-1u-finalization.md)** | User approval, quality gates, `state.md` creation (Step 1u — then appended by Stage B and subsequent phases). Includes end-of-Stage-A checklist. |

### Stage B: Data Discovery & Validation

| File | Purpose |
|---|---|
| **[stage-b-database-discovery.md](stage-b-database-discovery.md)** | Core discovery steps: database/table selection (2a-2b), time column discovery, metric/dimension discovery, filter scope classification, join key + compliance validation (2c-2e). |
| **[validation-queries.md](validation-queries.md)** | SQL patterns + 12-point Data Quality Gate (Go/No-Go template) run before routing to Phase 2 or Phase 3. |
| **[confirmed-values-checkpoint.md](confirmed-values-checkpoint.md)** | Write confirmed metric/dimension values to `state.md` once (Stage B), then reference in later phases — avoid re-querying. |
| **[workflow-notes.md](workflow-notes.md)** | Stage B edge cases: resume, large tables, conflict resolution, stale data, exclusion rules, joins, deliverables. |
| **[stage-b-path-routing.md](stage-b-path-routing.md)** | Path confirmation (Step 2f): update `state.md`, apply routing logic, route to Phase 2 or Phase 3. |
| **[exit-checklist.md](exit-checklist.md)** | Final gates before routing to Phase 2 or Phase 3. |

---

## How to Use These Files

### I'm starting a new Phase 1 — where do I start?
→ Open `steps-1pre.md` first — run the session-setup questions (Setup-A through Setup-E) before anything else. If Setup-E turns up a `.dash`/Sisense export, jump to the `.dash` Special Case in that same file instead of Stage A.

### I'm implementing Stage A requirements — where do I go after setup?
→ Open `../requirements-gathering-guide.md` (the main file with quick reference)

### I want to know HOW to ask a particular question
→ AskUserQuestion templates are inline in the relevant step file:
- Session setup questions → `steps-1pre.md`
- DB/table/metrics questions → `steps-1a-1o.md`
- Scoring, workflow, agent questions → `steps-1p-1t.md`
- Discovery/time-column/filter-scope questions → `stage-b-database-discovery.md`
- Batching rule + best practices → `../requirements-gathering-guide.md`

### I need detailed guidance for a specific step
→ Use the navigation below:
- **Setup-A to Setup-E (session setup + reference resources — multi-select):** See `steps-1pre.md`
- **`.dash`/Sisense Special Case (fast-track migration):** See `steps-1pre.md`
- **Treasure Insights API Special Case (datamodel schema fetch):** See `steps-1pre.md`
- **Combined Resources Path (`.dash` + datamodel ± workflow):** See `steps-1pre.md`
- **Steps 1a-1o (core requirements):** See `steps-1a-1o.md`
- **Steps 1k-1n (optional requirements):** See `steps-1k-1n-optional.md`
- **Steps 1p-1t (scoring & config):** See `steps-1p-1t.md`
- **Step 1u (finalization):** See `step-1u-finalization.md`
- **Steps 2a-2e (core discovery):** See `stage-b-database-discovery.md`
- **Step 2f (routing):** See `stage-b-path-routing.md`
- **Stage B exit gate:** See `exit-checklist.md`

### I want to understand Stage A/B workflow and edge cases
→ See `steps-1a-1o.md` (iterative patterns, contradictions, continuity) and `workflow-notes.md` (Stage B edge cases, conflict resolution)

---

## Quick Navigation by Step

| Step | File |
|---|---|
| **Setup-A. Project name** | `steps-1pre.md` |
| **Setup-B. Business goal** | `steps-1pre.md` |
| **Setup-C. Target platform** | `steps-1pre.md` |
| **Setup-D. Data source type** | `steps-1pre.md` |
| **Setup-E. Reference resources / `.dash` detection** | `steps-1pre.md` |
| 1a. Purpose + Business Model + Prior Art + Success Metric | `steps-1a-1o.md` |
| 1b. Metrics + Top Questions + Glossary | `steps-1a-1o.md` |
| 1c. Dimensions + Output Preferences | `steps-1a-1o.md` |
| 1d. Filters | `steps-1a-1o.md` |
| 1e. Date Range + Lookback Window + Timezone | `steps-1a-1o.md` |
| 1f. Data Freshness | `steps-1a-1o.md` |
| 1g. Historical Depth | `steps-1a-1o.md` |
| 1h. Sharing + Access + Target Users + Data Sensitivity | `steps-1a-1o.md` |
| 1i. Export/Download + Downstream Consumers | `steps-1a-1o.md` |
| 1j. Alerts/Thresholds | `steps-1a-1o.md` |
| 1k. Mobile (optional) | `steps-1k-1n-optional.md` |
| 1l. Compliance + Data Sensitivity | `steps-1k-1n-optional.md` |
| 1m. Data Complexity + Canonical ID + IDU Status | `steps-1k-1n-optional.md` |
| 1n. Drill-Down (optional) | `steps-1k-1n-optional.md` |
| 1o-ext. CDP Activation Intent (optional, pre-aggregated sources) | `steps-1k-1n-optional.md` |
| 1o. Exclusion Rules | `steps-1a-1o.md` |
| 1p. Dashboard Complexity Scoring | `steps-1p-1t.md` |
| 1q. Workflow Config (if score 4-6 AND skip_workflow ≠ true) | `steps-1p-1t.md` |
| 1r. Agent Config (optional) | `steps-1p-1t.md` |
| 1r-post. Rendering (fixed — HTML Client, no question) | `steps-1p-1t.md` |
| 1s. Stage A→B Bridging | `steps-1p-1t.md` |
| 1t. Solution-Specific | `steps-1p-1t.md` |
| 1u. Validation & Finalization | `step-1u-finalization.md` |
| 2a. Database Discovery | `stage-b-database-discovery.md` |
| 2b. Table Discovery + Time Column Discovery | `stage-b-database-discovery.md` |
| 2c. Metric Discovery & Inference | `stage-b-database-discovery.md` |
| 2d. Dimension Discovery & Inference | `stage-b-database-discovery.md` |
| 2d-filter. Filter Scope Classification | `stage-b-database-discovery.md` |
| 2d-ext. Tab Grouping Proposal | `stage-b-database-discovery.md` |
| 2e. Rendering Confirmation (fixed — HTML Client, no-op) | `stage-b-database-discovery.md` |
| 2f. Path Routing Decision | `stage-b-path-routing.md` |
| Stage B Exit Checklist | `exit-checklist.md` |

---

## Key Principles

- **Session setup is always first** — run `steps-1pre.md` before any business requirements; those 4 answers gate everything downstream
- **Rendering is fixed** — HTML Client is the only engine in this lite skill; it's recorded automatically, never asked about
- **Pre-aggregated data skips Phase 2** — `skip_workflow = true` from Setup-D overrides Dashboard Complexity Score routing
- **AskUserQuestion is mandatory** — never ask questions as plain text lists; templates are inline in each step file (see `steps-1pre.md`, `steps-1a-1o.md`, `steps-1p-1t.md`, `stage-b-database-discovery.md`)
- **Stage A and Stage B are one continuous phase** — Stage A gathers business requirements; Stage B validates against real data, in the same session (see iterative patterns in `steps-1a-1o.md`)
- **Single session, self-serve** — no engineer confirmation gate, no async customer clarification loop; every open question is resolved directly with the user in-session
- **state.md is the single source of truth** — created in Step 1u, appended by Stage B and every subsequent phase; no Confluence, no git commits

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
