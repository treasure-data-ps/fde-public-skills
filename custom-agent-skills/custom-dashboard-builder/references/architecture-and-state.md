# FDE TAIS Dashboard Builder — Pipeline Architecture & `project_state.md` Pattern

## 5-Phase Pipeline

```
Phase 1: Requirements + Data Discovery (+ business context, data dictionary, requirements doc)
  ↓
  ├─→ Score 0-2, or pre-aggregated source ──────────────┐
  ├─→ Score 3 → ask: workflow first, or build directly? │
  └─→ Score 4-6 → Phase 2: Workflow (SINK tables) ──────┤
                                                         ↓
                                   Phase 3: Build Dashboard (approved by the user)
                                                         ↓
                                   Phase 4: Dashboard Agent → .claude/skills/<project_slug>-dashboard-agent/
                                                         ↓
                                   Phase 5: Evaluation → production-ready (+ optional handoff docs)
```

| Phase | Mandatory? | Output |
|-------|-----------|--------|
| **1** | ✅ Always | Score (0-6) + path decision + `project_state.md`; `business-context.md`, `data-dictionary.md`, `requirements.md` |
| **2** | 🟡 Optional (Score 4-6 recommended) | SINK tables + workflow schedule (`workflows/`) |
| **3** | ✅ Always | Approved `dashboard.template.html` + `generate-data.js` + `dashboard.html` (`dashboards/`) |
| **4** | ✅ Always | Dashboard agent installed; `metrics-catalog.md`, `sql-templates.md` |
| **5** | ✅ Always (docs optional) | `eval.md` rounds to the production bar; finalized agent; `docs/` if chosen |

## Where Everything Lives

```
<Work Folder>/
├── agent_outputs/                  # git-ignored ("*")
│   └── <project_slug>/
│       ├── project_state.md        # header + Phase Ledger (below)
│       ├── business-context.md     # master copies of the agent's knowledge files
│       ├── data-dictionary.md
│       ├── metrics-catalog.md
│       ├── sql-templates.md
│       ├── requirements.md         # customer questionnaire
│       ├── workflows/              # Phase 2 copy of project_templates/workflow_template/
│       ├── dashboards/             # dashboard.template.html, generate-data.js (masters), dashboard.html (generated)
│       ├── agent_build/<name>/     # staging build of the agent (+ .prev-<timestamp> installs)
│       ├── eval.md                 # test plan + results per round
│       └── docs/                   # optional handoff docs
└── .claude/skills/<project_slug>-dashboard-agent/   # the installed agent (own .gitignore "*")
```

## `project_state.md`

One file per project. Two parts:

1. **Header — rewritten at every update:** Solution (`dashboard-builder`), Current phase, Next Action, Last updated.
2. **Phase Ledger — append-only:** one dated section per phase step, never edited afterwards. Every phase reads the whole ledger for earlier decisions.

```markdown
# Project State — <Project Name>

**Solution:** dashboard-builder
- **Current phase:** 3 — dashboard
- **Next Action:** Build the dashboard from SINK tables agg_bookings_*; spot-check 3 KPIs
- **Last updated:** 2026-07-24

---
## Phase Ledger (append-only — never edit earlier sections)

## Phase 1 — Session Setup (2026-07-22)
- Business goal: Track weekly booking volume and ARPU by destination
- Data source type: Raw/Transactional

## Phase 1 — Requirements / Data Discovery / Score & Path
- Metrics: Bookings (count), Revenue (SUM), ARPU (SUM/COUNT)
- Time column: event_time (business event), UTC
- Score: 6/6 — Workflow path
- Business context drafted + reviewed 2026-07-22; requirements sent 2026-07-22

## Phase 2 — Workflow Deployment (2026-07-23)
- Workflow project: travel_dashboard_wf · SINK database: dashboard_aggregates · Schedule: daily 08:00 UTC

## Phase 3 — Dashboard Build (2026-07-24)
- Masters: dashboards/dashboard.template.html, dashboards/generate-data.js · KPI spot-checks: 3/3 within tolerance · approved

## Phase 4 — Dashboard Agent (2026-07-25)
- Installed: .claude/skills/travel-dashboard-dashboard-agent/ · build checks passed

## Phase 5 — Evaluation (2026-07-26)
- Round 1: 8/10 (TC-06 compliance fail → business-context fix) · Round 2: 10/10 · finalized
```

### Rules

- Never rewrite or delete ledger sections — append a new dated block, including corrections (`## RECOVERY: <date> — revisited <decision>`).
- Always update the header in the same write, so a new session knows where to resume.
- If `project_state.md` is missing or corrupted, stop and ask the user to recover it.

## Resuming

1. List `agent_outputs/*/project_state.md`; keep those with **Solution:** `dashboard-builder`; confirm the project.
2. Read the header, then the whole ledger.
3. Resume at the header's Next Action — do not re-run earlier phases or re-ask answered questions.

## Single-session vs. multi-session

Both work the same way: one engagement folder, one `project_state.md`. A new session reads the file and continues; the ledger grows with each session.

## Local Only

- All artifacts are files in the Work Folder; nothing is uploaded or hosted.
- The dashboard is one portable `dashboard.html` (HTML Client) — no server.
- Treasure Data objects (workflows, SINK tables) are created only in Phase 2, after the approval gate.
