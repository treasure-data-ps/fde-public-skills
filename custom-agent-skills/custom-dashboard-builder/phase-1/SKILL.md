---
name: fde-tais-dashboard-builder-phase-1
description: |
  INTERNAL — Phase 1 only. Gather business requirements, validate against real data, calculate dashboard complexity (0-6), and route to Phase 2/3. Produces local state.md with requirements, data findings, and path decision.
---

# Phase 1: Requirements & Data Discovery (FDE TAIS Dashboard Builder)

> **Read in this order:**
> 1. `../INSTRUCTIONS.md` (master rules, load_order: 0)
> 2. `../references/execution-contract.md` (non-skippable execution gates)
> 3. `./INSTRUCTIONS.md` (Phase 1 rules, load_order: 1.1) — includes Quick Checklist
> 4. `./SKILL.md` (this file — full details)
> 5. `./references/phase-1-walkthrough.md` (step-by-step walkthrough)
> 6. `../references/guardrails-lite.md` (cross-phase guardrails)

**Phase Goal:** Gather business requirements (Stage A), validate them against real data (Stage B), calculate the Dashboard Complexity Score (0–6), decide Workflow vs Non-Workflow path, and get user approval — all in one session, with no Confluence and no git branching.
**Deliverable:** A local `state.md` file at `./<project-name>/state.md` containing the approved requirements, confirmed data findings, Dashboard Complexity Score, and path decision.

---

## Recommended Model

**This skill works with all Claude models.** Best default: **Claude Sonnet 5** (balanced cost/performance across all phases). Alternatives:
- **Haiku 4.5:** Fast iteration on requirements gathering (Phase 1)
- **Opus 4.7/4.8:** Complex Phase 4 agent development if needed

---

## 🔑 Append-Only Pattern (Critical for All Phases)

→ **state.md is append-only:** Each phase appends a new dated section at the bottom. See `../references/architecture-and-state.md` (The `state.md` Append-Only Pattern section) for details.

---

## Pre-Phase 1 Checklist

Before starting, confirm:

- ✅ Engagement type: new project or resuming existing `./<project-name>/`
- ✅ TD account accessible for data discovery
- ✅ If resuming: read `./<project-name>/state.md` and resume at "Next action" — don't re-ask answered questions

---

## Phase 1 Workflow: 2 Stages

### Stage A: Requirements Gathering

→ **See `./references/phase-1-walkthrough.md`** for the full step reference table and batching plan.

Run the session-setup questions (project name, business goal, platform, data source type) in one batch, then ask Setup-E (reference resources) as a separate call before gathering core requirements. **Setup-E is now MULTI-SELECT** — use `AskUserQuestion` with these options:
- `.dash` / Sisense export
- Treasure Insights datamodel
- Existing Treasure Data workflow
- Screenshots, mockups, SQL, or specifications
- None — starting fresh

If resources prefill answers, display the prefilled requirements and ask the user to confirm or correct them. Prefilling is not permission to skip mandatory questions.

**Special cases — Sisense/Treasure Insights exports, datamodels, and workflows:** If Setup-E turns up any of these, route to the appropriate special-case flow. Do not repeat already-prefilled questions, but do show and explicitly confirm every mandatory decision before Stage B/finalization. Instead follow the appropriate path in `./references/steps-1pre.md`:
- **`.dash` export alone** → "`.dash` / Sisense Special Case" — converts the file with `../references/dash_to_html.py`, prefills requirements and discovery
- **Treasure Insights datamodel alone** → "Treasure Insights API Special Case" — fetches schema via Reporting API with `../references/insights-api-helper.py`, prefills requirements and discovery
- **Multiple resources (`.dash` + datamodel ± workflow)** → "Combined Resources Path" — fetches datamodel, converts `.dash` file, cross-validates both, incorporates workflow metadata if present, then prefills Stage A/B with unified context

Special-case paths may prefill repetitive requirements, but they do not bypass the execution contract: show the prefilled answers, confirm every mandatory decision with the user, validate the live data, then route to Phase 2/3 based on the migration goal (Replicate / Replicate+improve / Modernize) and workflow selection.

→ **See `./references/steps-1a-1o.md`** for detailed guidance on core requirement steps
→ **See `./references/steps-1k-1n-optional.md`** for optional step details (only ask if relevant)

### Stage B: Data Discovery & Validation

Validate Stage A's requirements against real data: confirm the database/tables exist, discover the correct time column, infer/validate metrics and dimensions from live queries, classify filter scope, and run the Data Quality Gate before finalizing.

→ **See `./references/stage-b-database-discovery.md`** for the full data-discovery walkthrough (time column discovery, metric/dimension inference, filter scope classification, tab grouping)
→ **See `./references/validation-queries.md`** for the Data Quality Gate (Checks 1–12) and reusable SQL patterns
→ **See `./references/confirmed-values-checkpoint.md`** for how to record confirmed metric/dimension values once so later phases don't re-query them
→ **See `./references/workflow-notes.md`** for conflict-resolution and large-table performance handling

### Scoring & Path Decision (Steps 1p + 2f)

Combine the Dashboard Complexity Score (0–6) with the data-source constraint (pre-aggregated → can skip Phase 2/Workflow) to decide Workflow vs Non-Workflow.

→ **See `./references/steps-1p-1t.md`** for the scoring questions and field-capture tables
→ **See `./references/stage-b-path-routing.md`** for the canonical routing table (single source of truth for path decisions)

**Canonical routing (score 0–6):**

| Score | Path |
|---|---|
| 0–2 | Non-Workflow → skip straight to Phase 3 (Build Dashboard) |
| 3 | Ask user: "Quick build (Phase 3 directly) or scheduled refresh (Phase 2 Workflow first)?" |
| 4–6 | Workflow recommended → Phase 2, then Phase 3 |

If the data source is pre-aggregated (`skip_phase_3` in the old numbering, i.e. Phase 2/Workflow not needed here), route straight to Phase 3 regardless of score.

---

## Finalization: Write `state.md` and Get Approval

1. **Ask for a project name** if not already collected (short, lowercase with hyphens — e.g. `acme-campaign-perf`). Use `./<project-name>/` as the working directory for everything this skill produces.

2. **Create the working directory and write `state.md`:**

   ```bash
   mkdir -p ./<project-name>
   cat > ./<project-name>/state.md << 'EOF'
   # <Project Slug> — Dashboard State

   ## Phase 1 — Session Setup (<YYYY-MM-DD>)
   - Business goal: <one sentence>
   - Platform: <Treasure Work / Treasure AI Studio>
   - Data source type: <Raw/Transactional / Pre-aggregated / Snapshot / Mixed>

   ## Phase 1 — Requirements
   - Metrics: <list>
   - Dimensions: <list>
   - Filters: <list, with scope classification>
   - Date range / timezone: <...>
   - Exclusion rules: <SQL or description>

   ## Phase 1 — Data Discovery
   - Database.Table(s): <...>
   - Time column: <column, business-event or insert-time>
   - Confirmed metric definitions: <...>
   - Confirmed dimension values: <...>
   - Data Quality Gate: <Pass/Fail summary>

   ## Phase 1 — Dashboard Complexity Score & Path
   - Q1 (frequency): <0-2>
   - Q2 (history): <0-2>
   - Q3 (audience): <0-2>
   - Total: <0-6>
   - Path decision: <Workflow / Non-Workflow> — <reasoning>

   ## Next action
   - <Phase 2 (Workflow) or Phase 3 (Build Dashboard) — be specific about what to run next>
   EOF
   ```

3. **Quality gate before approval:**
   - All core requirements (1a–1j, 1o) captured
   - Data Discovery findings don't contradict Stage A requirements (if they do, resolve and note the trade-off in `state.md`)
   - Dashboard Complexity Score calculated and path decision made
   - Data Quality Gate checks pass (or failures are explicitly acknowledged)

4. **Get user approval** via `AskUserQuestion`: "Does this capture your requirements and the confirmed data findings?"

→ See `./references/step-1u-finalization.md` and `./references/exit-checklist.md` for the full validation checklist and error-handling guidance.

---

## Phase 1 Deliverables (End of Phase 1)

- ✅ Project name recorded — used for the working directory `./<project-name>/`
- ✅ Platform + data source type confirmed
- ✅ Core requirements gathered (metrics, dimensions, filters, date range, sharing, exclusions)
- ✅ Database/tables confirmed to exist; time column identified
- ✅ Metrics and dimensions validated against live data
- ✅ Filter scope classified (dashboard-level / tab-level / widget-level)
- ✅ Data Quality Gate run (Checks 1–12)
- ✅ Dashboard Complexity Score calculated (0–6) and path decision made
- ✅ `./<project-name>/state.md` created with all of the above
- ✅ User approved the plan
- ✅ Ready for Phase 2 (Workflow, if chosen) or Phase 3 (Build Dashboard)

---

## Quick Reference: Which File?

| Question | Reference |
|---|---|
| Session setup + core requirements questions | `./references/steps-1a-1o.md` |
| Optional requirements (mobile, compliance, drill-down)? | `./references/steps-1k-1n-optional.md` |
| Dashboard Complexity Scoring + path decision logic | `./references/steps-1p-1t.md`, `./references/stage-b-path-routing.md` |
| Database/table/time-column/metric/dimension discovery | `./references/stage-b-database-discovery.md` |
| Filter scope classification rules | `./references/stage-b-database-discovery.md` (Step 2d-filter) |
| Data Quality Gate (12 checks) + SQL patterns | `./references/validation-queries.md` |
| Avoiding redundant re-querying in later phases | `./references/confirmed-values-checkpoint.md` |
| Conflict resolution, large-table performance | `./references/workflow-notes.md` |
| Final validation + approval flow | `./references/step-1u-finalization.md`, `./references/exit-checklist.md` |
| Directory index of all Phase 1 reference files | `./references/INDEX.md` |

---

## Next Phase

### ➡ Move to Phase 2 (Workflow — optional) or Phase 3 (Build Dashboard)

**Condition:** Phase 1 requirements + data discovery approved, `state.md` created.

**What happens next:**
- If path decision = Workflow → go to Phase 2 to deploy a scheduled `.dig` workflow, then Phase 3
- If path decision = Non-Workflow (or pre-aggregated data source) → skip straight to Phase 3
- Phase 3 reads `./<project-name>/state.md` for confirmed metrics, dimensions, and data source details — no re-asking needed

---

**Version:** 1.0.0
**Last Updated:** 23 July 2026
**Author:** FDE Team
