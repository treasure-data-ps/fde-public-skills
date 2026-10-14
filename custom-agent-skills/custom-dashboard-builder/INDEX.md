# FDE TAIS Dashboard Builder — File & Folder Index

Directory of every file under `fde-tais-dashboard-builder/`. Load this when navigating the agent, not during phase execution.

Fully self-contained — no runtime dependency on `../shared/` or the private `fde-dashboard-solutions` template repo.

---

## Entry Points

| File | Purpose |
|------|---------|
| `SKILL.md` | Root entry point — engagement routing and phase reference |
| `INDEX.md` | This file — full directory of all files and folders |
| `README.md` | Human-readable overview of the agent's purpose and structure |
| `references/architecture-and-state.md` | **READ FIRST (after guardrails)** — 5-phase pipeline flow, `state.md` append-only pattern, resume logic |
| `references/guardrails-lite.md` | **LOAD FIRST** — mandatory rules for data integrity, database & queries, rendering, and agent prompts |

---

## Phase Workflow Files

| Phase | File | Steps | Key Output | Condition |
|-------|------|-------|-----------|-----------|
| **1** | `phase-1/SKILL.md` + `references/phase-1-walkthrough.md` | Stage A: 1a-1u, Stage B: 2a-2f (with Setup-E multi-select special cases) | Dashboard Complexity Score (0-6) + `state.md` created | Always |
| **2** | `phase-2/SKILL.md` + `references/phase-2-walkthrough.md` | 2a-2h (8 steps) | SINK tables deployed + validated | Score 4-6 only, optional |
| **3** | `phase-3/SKILL.md` + `references/phase-3-walkthrough.md` | 4a-4l (12 steps) | User-approved interactive `dashboard.html` | Always (after Phase 1 or 2) |
| **4** | `phase-4/SKILL.md` + `references/phase-4-walkthrough.md` | Track A (4a-0 to 4a-vii), Track B (4b-i to 4b-vi) | Reusable skill + Foundry agent | Optional |
| **5** | `phase-5/SKILL.md` + `references/phase-5-walkthrough.md` | 5b-pre-5d (4 steps) | 4 local markdown files + share step | Optional |

---

## Phase Checklist Files

Quick decision-guide checklists — read before the full guide when only a fast gate-check is needed.

| File | Purpose |
|------|---------|
**Quick Checklists:**
These are now embedded in each phase's `INSTRUCTIONS.md` file (not separate files).

- Phase 1 Quick Checklist: In `phase-1/INSTRUCTIONS.md` → Quick Checklist section
- Phase 2 Quick Checklist: In `phase-2/INSTRUCTIONS.md` → Quick Checklist section  
- Phase 3 Quick Checklist: In `phase-3/INSTRUCTIONS.md` → Quick Checklist section
- Phase 4 Quick Checklist: In `phase-4/INSTRUCTIONS.md` → Quick Checklist section
- Phase 5 Quick Checklist: In `phase-5/INSTRUCTIONS.md` → Quick Checklist section

---

## Phase-Specific References

### phase-1/references/ (merged Requirements + Data Discovery)

| File | What It Contains |
|------|-----------------|
| `step-0-verify-td-connection.md` | Verify tdx CLI installation and authentication (troubleshooting). |
| `steps-1pre.md` | Session setup questions and batch summary tables. |
| `steps-1a-1o.md` | Core requirement steps 1a-1j, 1o (iterative/rollback patterns). |
| `steps-1k-1n-optional.md` | Optional discovery steps 1k-1n, 1o-ext. |
| `steps-1p-1t.md` | Scoring questions and path decision table. |
| `step-1u-finalization.md` | Quality gates, user approval, state.md write. |
| `stage-b-database-discovery.md` | Database selection (HTML Client no-op step). |
| `stage-b-path-routing.md` | Path confirmation and routing logic (Phase 2 or 3). |
| `validation-queries.md` | SQL templates for metric/dimension validation. |
| `exit-checklist.md` | Mandatory exit gate before Phase 2/3 routing. |
| `confirmed-values-checkpoint.md` | Snapshot of confirmed metrics/dimensions/exclusions. |
| `workflow-notes.md` | Extended discovery and conflict resolution. |
| `INDEX.md` | Phase 1 references navigation index. |

### phase-2/references/ (Workflow deployment, optional)

| File | What It Contains |
|------|-----------------|
| `workflow-setup-configure.md` | Setup, configure params, customize SQL. |
| `workflow-deployment-validate.md` | Review, deploy, validate SINK tables. |
| `td-time-functions.md` | Time filter patterns (td_scheduled_time, td_time_range). |
| `incremental_update_patterns.md` | Append-only, 1-day, 7-day lookback modes. |
| `input_params_examples.md` | input_params.yaml worked examples. |
| `testing-troubleshooting.md` | Common failures and resolution steps. |
| `pre-deployment-checklist.md` | Mandatory pre-push checklist. |
| `INDEX.md` | Phase 2 references navigation index. |
| `workflow-templates/` | Embedded .dig templates and SQL (copy to ./<project-name>/workflows/). |

### phase-3/references/ (Build Dashboard, HTML Client only)

| File | What It Contains |
|------|-----------------|
| `steps.md` | All steps 4b-pre through 4l (includes SINK gate, generate-data.js). |
| `query-patterns-for-dashboards.md` | Parallel queries, column selection, SINK optimization. |
| `filter-architecture.md` | 5 filter types and wiring patterns. |
| `testing-troubleshooting.md` | Testing, troubleshooting, anti-patterns, quality gates. |
| `INDEX.md` | Phase 3 references navigation index. |

#### phase-3/references/rendering/

| Path | What It Contains |
|------|-----------------|
| `SKILL.md` | HTML Client engine details. |
| `html-client/SKILL.md` | HTML Client only — Pattern A (inlined data, single file). |
| `html-client/config-schema.md` | Config schema for HTML Client dashboards. |
| `html-client/getting-started.md` | Getting-started walkthrough. |
| `html-client/html-dashboard-patterns.md` | Common dashboard patterns. |
| `html-client/html-deployment-guide.md` | Deployment guidance. |
| `html-client/template-customization.md` | Customize generate-data.js and templates. |
| `html-client/templates/` | Dashboard templates and utilities (copy to ./<project-name>/dashboards/). |

### phase-4/references/ (Automate & Deploy)

| File | What It Contains |
|------|-----------------|
| `INDEX.md` | Phase 4 references navigation index. |
| `README.md` | Phase 4 quick navigation. |
| `track-a-automation.md` | Skill extraction (steps 4a-0 to 4a-vii): knowledge package, definition, queries, validation, packaging. |
| `track-b-ai-agent.md` | Agent deployment (steps 4b-i to 4b-vi): capability choice, knowledge bases, Foundry deploy, validation. |
| `templates/` | Knowledge-base and agent-prompt templates (copy and fill). |

### phase-5/ (Handoff Documentation)

Phase 5 has no `references/` subfolder — handoff guide is self-contained with embedded templates.

---

## Root-Level References

| File | What It Contains |
|------|-----------------|
| `references/architecture-and-state.md` | 5-phase flow, skip rules, state.md append-only pattern, multi-session workflows. |
| `references/guardrails-lite.md` | Data integrity, database/queries, HTML Client rules, requirements, agent prompts. |
| `references/treasure-data-theme.md` | **Treasure Data default theme:** CSS variables, chart palette, component styling, custom brand override. Used in Phase 3 dashboard build. |
| `references/dash_to_html.py` | Sisense .dash to render.js + HTML converter (Python stdlib, no deps). Phase 1 `.dash` Special Case. |
| `references/insights-api-helper.py` | Treasure Insights Reporting API schema extractor (fetches datamodel, extracts metrics/dimensions/joins). Phase 1 Treasure Insights API Special Case. |
| `phase-1/references/treasure-insights-api-integration.md` | Treasure Insights API reference (endpoints, auth, extraction logic). Companion to insights-api-helper.py. |

---

## Local Working-Directory Convention

Every phase writes into a single flat project folder created during Phase 1 session setup:

```
./<project-name>/
├── state.md               (single source of truth, append-only)
├── workflows/              (only if Phase 2 run)
├── dashboards/
│   ├── dashboard.html
│   ├── generate-data.js
│   └── render.js
├── skills/                 (only if Phase 4 Track A run)
├── agents/                  (only if Phase 4 Track B run)
└── docs/                    (only if Phase 5 run)
```

---

**Version:** 1.0.0
**Last Updated:** 23 July 2026
**Author:** FDE Team
