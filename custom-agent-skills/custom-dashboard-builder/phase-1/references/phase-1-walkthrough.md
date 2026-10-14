# Phase 1: Requirements & Data Discovery

---

## ⛔ Step 0: Verify Treasure Data Connection (ALWAYS FIRST)

**Before anything else:** Confirm TD auth is set up and working.

Run:
```bash
tdx databases
```

Should list your databases. If it fails with 401/403/not found, see [`references/step-0-verify-td-connection.md`](references/step-0-verify-td-connection.md) for troubleshooting.

**If this step fails, everything else will fail.** Do not proceed to Session Setup until `tdx databases` succeeds.

---


**Deliverable:** `./<project-name>/state.md` with approved requirements, confirmed data findings, Dashboard Complexity Score (0-6), and path decision
**Location:** Single merged phase — runs before Phase 2 (Workflow, optional) and Phase 3 (Build Dashboard)

---

## Phase 1: Quick Reference — Stages

| Stage | Topic | Required? | Details |
|---|---|---|---|
| **Session Setup** | | | |
| Setup-A | Project name | ✅ Always | Short lowercase with hyphens name; becomes the working directory `./<project-name>/` |
| Setup-B | Business goal / dashboard purpose | ✅ Always | One sentence — what decision does this dashboard support? |
| Setup-C | Target platform | ✅ Always | Treasure Work / Treasure AI Studio — gates sharing constraints (rendering is always HTML Client in lite) |
| Setup-D | Data source type | ✅ Always | Raw/Transactional vs Pre-aggregated vs Snapshot — determines whether Phase 2 (Workflow) can be skipped |
| Setup-E | Reference resources | ✅ Always | Existing dashboard/spec to replicate? If a `.dash`/Sisense/Treasure Insights export is provided, jump to the `.dash` Special Case in `steps-1pre.md` instead of Stage A |
| **Stage A: Core Requirements (1a-1j, 1o — Always Ask)** | | | See [`steps-1a-1o.md`](references/steps-1a-1o.md) |
| 1a | Purpose, Business Context & Success Criteria | ✅ | Dashboard purpose, prior art, success metric, audience + technical depth |
| 1b | Metrics + Top Questions + Business Glossary | ✅ | 5-10 KPIs with formulas, top 3-5 analytical questions, glossary |
| 1c+1d | Dimensions, Filters, Layout & Interactions | ✅ | Drill-down dimensions, filter list, layout preference |
| 1e+1f | Date Range, Timezone, Refresh & Freshness | ✅ | Default range, timezone (⚠️ critical), acceptable freshness/latency |
| 1g | Historical Data Depth | ✅ | How far back? Retention period? |
| 1o | Exclusion Rules & Data Quality | ✅ Always | Exclusions (SQL format), null handling — validated in Stage B |
| **1h + 1j — Sharing & Alerts** | | ✅ Customer-facing / ⚠️ internal | See [`steps-1a-1o.md`](references/steps-1a-1o.md) |
| 1h | Sharing, Access, Target Users & Downstream Consumers | ✅ Customer-facing | Who accesses? Technical depth? Sensitive data? Export needs merged in here |
| 1j | Alert/Threshold Notifications | ⚠️ | Alert conditions, delivery, recipients |
| **Optional (Ask Only If Relevant)** | | ⚠️ | See [`steps-1k-1n-optional.md`](references/steps-1k-1n-optional.md) |
| 1k | Mobile/Responsive Design | ⚠️ | Ask only if mobile use case likely |
| 1l | Compliance, Governance & Data Sensitivity | ⚠️ | Ask only if sensitive data flagged in 1h |
| 1m | Data Source Complexity + Canonical ID | ⚠️ | Ask only if multi-database joins likely |
| 1n | Drill-Down Depth | ⚠️ | Ask only if dimensions suggest multi-level drill-down |
| **Stage B: Data Discovery & Validation** | | ✅ Always | See [`stage-b-database-discovery.md`](references/stage-b-database-discovery.md) |
| 2a | Select/confirm database | ✅ | `tdx databases` if not already known |
| 2b | Discover/confirm tables + time column | ✅ | Includes business-event-datetime vs insert-time detection |
| 2c | Discover/validate metrics | ✅ | Aggregation queries confirm Stage A's assumed metrics |
| 2d | Discover/validate dimensions + classify filter scope | ✅ | DISTINCT value queries, cardinality checks, filter scope map |
| 2e | (Rendering engine is fixed to HTML Client in lite — no decision needed here) | — | — |
| Data Quality Gate | Checks 1–12 before finalizing | ✅ Always | See [`validation-queries.md`](references/validation-queries.md) |
| **Scoring & Path Decision** | | ✅ Always | See [`steps-1p-1t.md`](references/steps-1p-1t.md), [`stage-b-path-routing.md`](references/stage-b-path-routing.md) |
| 1p | Dashboard Complexity Scoring (0-6 model) | ✅ Always | 3 questions → path logic (score + data source) → Workflow vs Non-Workflow |
| 1q | Workflow Configuration | 🔧 If score 4-6 | SINK DB, project name, run schedule — used by Phase 2 |
| 1r | Agent/Skill Configuration | 🔧 Optional | Only if Phase 4 Track A/B is anticipated |
| **Finalization** | Validate & get approval, write `state.md` | ✅ Always | See [`step-1u-finalization.md`](references/step-1u-finalization.md) |

---

---

## ℹ️ Phase 1 Step Numbering Reference

Phase 1 has two stages with continuous step numbering:

| Stage | Steps | File |
|---|---|---|
| **Stage A** | 1a-1u | This guide |
| **Stage B** | 2a-2f (+ sub-steps) | `references/stage-b-database-discovery.md` |

**Stage B breakdown:**
- 2a: Discover & select database
- 2b: Discover & confirm tables
- 2c: Discover metrics & infer definitions
- 2d: Discover dimensions & infer definitions
- 2d-filter: Classify filter scope
- 2d-ext: Propose tab grouping
- 2e: Rendering (HTML Client, no-op)
- 2e-join: Validate join keys
- 2e-pii: Compliance & PII handling

---


## How to Execute Phase 1

### Session Setup (ask before anything else)

Batch project name, business goal, platform, and data source type into a single `AskUserQuestion` call (Setup-A–D). These four answers gate everything downstream: data source type may skip Phase 2, platform affects sharing guidance.

Then ask Setup-E (reference resources) as its own call. If the user provides a `.dash`/Sisense/Treasure Insights export, route to the `.dash` Special Case in `./steps-1pre.md` — it fast-tracks Stage A/B by deriving requirements and data discovery directly from the export.

### ⚠️ Non-Skippable Questionnaire Gate (Rule P1-0)

This walkthrough does not replace the mandatory-question rule in `../INSTRUCTIONS.md`. Use `AskUserQuestion` for Setup-A through Setup-E and every mandatory 1a–1o group. Record each answer (or a refusal reason) in `state.md` and the execution contract before moving to the next batch. Do not infer an answer from context.

Before scoring or routing, confirm the three-level filter hierarchy from Rule P1-2b and complete the HTML Client data-size check in `html-client-data-limits.md`. The Phase 1 gate is incomplete until the execution-contract checklist is complete.

### Stage A: Ask Business Requirements Questions Using AskUserQuestion

**Never ask plain text questions.** Use `AskUserQuestion` with 2-4 pre-populated options.

**Core rule — AskUserQuestion best practices:**

| DO | DON'T |
|---|---|
| Show findings as markdown FIRST (table, list), then ask | Ask without discovering first |
| Provide 2–4 pre-populated options | Present plain text questions |
| Mark recommended option with `(Recommended)` | Assume defaults (databases, schedules, etc.) |
| Batch up to 4 questions per call | Batch more than 4 questions per call |
| Include a 1-line description for each option | Use vague labels ("Yes/No", "Option 1/2") |
| Ask Dashboard Complexity Scoring Q1–Q3 BEFORE building the dashboard | Wait until after delivery to ask scoring |

**Recommended batch structure (aim for ~6-7 total AskUserQuestion calls across all of Phase 1):**

| Batch | Topic | Questions | Condition | Why Grouped |
|---|---|---|---|---|
| **Batch 1** | Session setup | Project name, business goal, platform, data source type | ✅ Always | Gates everything downstream |
| **Batch 1b** | Reference resources | Existing dashboard/mockup/spec? | ✅ Always | Determines fast-track path vs normal flow |
| **Batch 2** | Core requirements Phase 1 | Metrics, KPIs (what to measure) | ✅ Always | First core requirement |
| **Batch 3** | Dashboard structure + dimensions + filters + layout | **Dashboard structure** (tabs, visualizations, filters, drill-down, performance) + Dimensions + Filters + Layout preferences + Branding | ✅ Always | **⚠️ MANDATORY - ALL 5 structure batches required** — Related discovery; structure informs metrics/dimensions alignment |
| **Batch 4** | Temporal + sharing | Date range, timezone, refresh, sharing/access | ✅ Always | Related; timezone often forgotten |
| **Batch 5** | Data discovery confirmation | Database/table confirmation, time column, metric/dimension validation results | ✅ Always | After running discovery queries — confirm what was found |
| **Batch 6** | Dashboard Complexity Scoring | Q1, Q2, Q3 (can be 1 call with 3 questions) | ✅ Always | Drives path decision |
| **Batch 7** | Path confirmation | Workflow vs Non-Workflow (only if score = 3) | ⚠️ If score = 3 | Final gate before writing `state.md` |

---

**End-to-end Phase 1 flow:**

```
## Session Setup — Batch 1
  project name, business goal, platform, data source type

## Reference Resources — Batch 1b
  Existing dashboard/mockup/spec?
  
  IF resources found (.dash, datamodel, specs):
    → Route to the appropriate Special Case path (steps-1pre.md)
    → Show all prefilled mandatory answers and obtain explicit confirmation; do not silently skip them
    
  IF "None — starting fresh":
    → Proceed to Stage A (standard flow)

## Stage A: Core Requirements — Batch 2 (steps-1a-1o.md)
  Step 1a: Dashboard purpose & success criteria
  
## Stage A: Dashboard Structure + Requirements — Batch 3 (steps-1a-1o.md, Step 1c+1d)
  ⚠️ MANDATORY: 5 Dashboard Structure Questionnaire Batches (ask first, before detailed discovery)
    • Batch 1: Tabs/Organization (single page / 2-3 tabs / 4+ tabs / drill-down)
    • Batch 2: Visualization types (KPI cards, trends, comparisons, distributions, tables, heatmaps)
    • Batch 3: Filter & interactivity (static / global / per-section / advanced)
    • Batch 4: Drill-down depth (summary / one level / multiple / detailed table)
    • Batch 5: Performance targets (daily / multiple daily / hourly / live)
  
  Then: Dimensions, filters, layout preferences, branding

## Stage A: Temporal + Sharing — Batch 4 (steps-1a-1o.md)
  date range, timezone, refresh, sharing/access

## Stage B: Data Discovery — stage-b-database-discovery.md
  Step 1: tdx databases → confirm database (skip if already known from Stage A)
  Step 2: tdx tables --in <db> (list tables) → tdx describe <db>.<table> per table (describe rejects wildcards) → confirm tables → identify time column
  Step 3: Run aggregation queries → validate metrics against Stage A assumptions
  Step 4: Run DISTINCT-value queries → validate dimensions, classify filter scope
  Step 5: Data Quality Gate (validation-queries.md, Checks 1-12)
  → Batch 4: present findings, confirm any conflicts with Stage A

## Scoring & Path Decision — steps-1p-1t.md, stage-b-path-routing.md
  Batch 5: Dashboard Complexity Scoring
    Q1: How often viewed? (0-2 pts)
    Q2: Need historical trends? (0-2 pts)
    Q3: How many users? (0-2 pts)
    → Subtotal: 0-6 pts
    
  Batch 6 (if score = 3): Path confirmation
    User chooses: Quick build (Phase 3 directly) or Workflow first (Phase 2 then Phase 3)
  
  Path decision: score 0-2 or pre-aggregated → Non-Workflow (Phase 3 directly)
                 score 3 → Batch 6: ask user to choose
                 score 4-6 → Workflow (Phase 2, then Phase 3)

## Finalization — step-1u-finalization.md
  Write ./<project-name>/state.md
  User approval → AskUserQuestion: "Does this capture your requirements and confirmed data findings?"
  Proceed to Phase 2 (if Workflow) or Phase 3 (if Non-Workflow)
```

→ **See [`steps-1a-1o.md`](references/steps-1a-1o.md)** for core requirement AskUserQuestion templates
→ **See [`stage-b-database-discovery.md`](references/stage-b-database-discovery.md)** for data discovery walkthrough, time column detection, filter scope rules
→ **See [`steps-1p-1t.md`](references/steps-1p-1t.md)** and [`stage-b-path-routing.md`](references/stage-b-path-routing.md) for scoring + routing templates

---

## Key Reference Materials

| I want to... | See... |
|---|---|
| Ask core requirement questions correctly | [`steps-1a-1o.md`](references/steps-1a-1o.md) |
| Ask optional requirements (mobile, compliance, drill-down) | [`steps-1k-1n-optional.md`](references/steps-1k-1n-optional.md) |
| Understand time column discovery, metric/dimension validation | [`stage-b-database-discovery.md`](references/stage-b-database-discovery.md) |
| Run the Data Quality Gate | [`validation-queries.md`](references/validation-queries.md) |
| Avoid re-querying the same values in later phases | [`confirmed-values-checkpoint.md`](references/confirmed-values-checkpoint.md) |
| Understand Dashboard Complexity Scoring & path decision | [`steps-1p-1t.md`](references/steps-1p-1t.md), [`stage-b-path-routing.md`](references/stage-b-path-routing.md) |
| Handle conflicts between Stage A assumptions and Stage B data reality | [`workflow-notes.md`](references/workflow-notes.md) |
| Write `state.md` and get final approval | [`step-1u-finalization.md`](references/step-1u-finalization.md), [`exit-checklist.md`](references/exit-checklist.md) |
| See all reference files at once | [`references/INDEX.md`](references/INDEX.md) |

---

## Dashboard Complexity Scoring (Quick Summary)

| Metric | Q1: Frequency | Q2: History | Q3: Audience | Score | Path |
|---|---|---|---|---|---|
| Points | 0-2 | 0-2 | 0-2 | 0-6 | Recommendation |
| Examples | Daily (2) | Trends needed (2) | Customer-facing (2) | **6 pts** | **Workflow** ✓ |
| Examples | Weekly (1) | Maybe (1) | Internal (1) | **3 pts** | **Ask user** — "Quick build (Phase 3 now) or scheduled refresh (Phase 2 first)?" |
| Examples | Rarely (0) | No (0) | Just me (0) | **0 pts** | **Non-Workflow** ✓ |

→ For full scoring logic, see [`steps-1p-1t.md`](references/steps-1p-1t.md) and [`stage-b-path-routing.md`](references/stage-b-path-routing.md)

---

## Phase 1 Workflow Notes

### Phase 1 is Iterative
Users can revisit any step before approving. Minor changes proceed with a caveat noted in `state.md`; major changes (e.g. metric definition changes) should be re-confirmed before moving on.

### Stage A → Stage B Continuity
Stage A gathers assumptions; Stage B validates them against real data in the same session. If Stage B finds a conflict (e.g. a metric Stage A assumed doesn't exist, or cardinality is much higher than expected):
1. Identify the conflict explicitly
2. Ask the user which is authoritative — the original ask, or the data reality
3. Note the resolution in `state.md` under Data Discovery
4. Continue — no need to redo Stage A from scratch

### Handle Contradictions
When requirements conflict (e.g. "Real-time" + "Minimize cost"):
1. Identify explicitly
2. Ask: "Which is more important?"
3. Propose a compromise if needed
4. Note the trade-off decision in `state.md`

→ **See [`steps-1a-1o.md`](references/steps-1a-1o.md)** for full iterative patterns and rollback scenarios

---

## At End of Phase 1

→ **See `../SKILL.md` Phase 1 Deliverables section** for the canonical end-of-phase checklist.

---

## Reference Directory

All detailed guidance lives in: `./references/`

→ **Start with [`references/INDEX.md`](references/INDEX.md)** for a quick directory of all files and their purposes.

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
