---
name: fde-tais-dashboard-builder-phase-1
description: |
  Dashboard builder sub-file — Phase 1 only. Gather business requirements, validate against real data, calculate dashboard complexity (0-6), and route to Phase 2/3. Produces local project_state.md with requirements, data findings, and path decision.
---

# Phase 1: Requirements & Data Discovery (FDE TAIS Dashboard Builder)

> **Read in this order:**
> 1. `../INSTRUCTIONS.md` (master rules, load_order: 0)
> 2. `../references/execution-contract.md` (non-skippable execution gates)
> 3. `./INSTRUCTIONS.md` (Phase 1 rules, load_order: 1.1) — includes Quick Checklist
> 4. `./SKILL.md` (this file — full details)
> 5. `./references/phase-1-walkthrough.md` (step-by-step walkthrough)
> 6. `../references/guardrails-lite.md` (cross-phase guardrails)

**Phase Goal:** Gather business requirements (Stage A), validate them against real data (Stage B), calculate the Dashboard Complexity Score (0–6), decide Workflow vs Non-Workflow path, and get user approval — all in one session, with local files only.
**Deliverable:** A local `project_state.md` file at `agent_outputs/<project_slug>/project_state.md` containing the approved requirements, confirmed data findings, Dashboard Complexity Score, and path decision.

---

## 🔑 Append-Only Pattern (Critical for All Phases)

→ **project_state.md is append-only:** Each phase appends a new dated section at the bottom. See `../references/architecture-and-state.md` (The `project_state.md` Append-Only Pattern section) for details.

---

## Pre-Phase 1 Checklist

Before starting, confirm:

- ✅ Engagement type: new project or resuming existing `agent_outputs/<project_slug>/`
- ✅ TD account accessible for data discovery
- ✅ If resuming: read `agent_outputs/<project_slug>/project_state.md` and resume at "Next action" — don't re-ask answered questions

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
- **`.dash` export alone** → "`.dash` / Sisense Special Case" — converts the file with `<skill_dir>/tools/dash_to_html.py`, prefills requirements and discovery
- **Treasure Insights datamodel alone** → "Treasure Insights API Special Case" — fetches schema via Reporting API with `<skill_dir>/tools/insights-api-helper.py`, prefills requirements and discovery
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

## Finalization: Write `project_state.md`, Get Approval, Draft the Business Context

1. **Project name** — if not already collected (Setup-A), ask for it: short, lowercase with hyphens (e.g. `acme-campaign-perf`). It is the `<project_slug>`; the dashboard agent will be `<project_slug>-dashboard-agent`.

2. **Bootstrap and write `project_state.md`.** Bootstrap `agent_outputs/` once (`<skill_dir>/../shared/local_outputs.md` Step 1 — `agent_outputs/.gitignore` with `*`), then write the file with the header and the first ledger sections:

   ```bash
   mkdir -p agent_outputs && { [ -f agent_outputs/.gitignore ] || printf '*\n' > agent_outputs/.gitignore; }
   mkdir -p agent_outputs/<project_slug>
   ```

   ```markdown
   # Project State — <Project Name>

   **Solution:** dashboard-builder
   - **Current phase:** <1 — requirements + discovery | 2 — workflow | 3 — dashboard | 4 — dashboard agent | 5 — evaluation | complete — agent live>
   - **Next Action:** <one sentence>
   - **Last updated:** <YYYY-MM-DD>

   ---
   ## Phase Ledger (append-only — never edit earlier sections)

   ## Phase 1 — Session Setup (<YYYY-MM-DD>)
   - Business goal: <one sentence>
   - Data source type: <Raw/Transactional / Pre-aggregated / Snapshot / Mixed>

   ## Phase 1 — Requirements
   - Metrics: <list with formulas>
   - Dimensions: <list>
   - Filters: <list, with scope classification>
   - Date range / timezone: <...>
   - Exclusion rules: <SQL or description>
   - Dashboard agent scope: <Step 1r list>

   ## Phase 1 — Data Discovery
   - Database.Table(s): <...>
   - Time column: <column, business-event or insert-time>
   - Confirmed metric definitions: <...>
   - Confirmed dimension values: <...>
   - Data Quality Gate: <Pass/Fail summary>

   ## Phase 1 — Dashboard Complexity Score & Path
   - Q1 (frequency): <0-2> · Q2 (history): <0-2> · Q3 (audience): <0-2> · Total: <0-6>
   - Path decision: <Workflow / Non-Workflow> — <reasoning>
   ```

   The header (Current phase, Next Action, Last updated) is rewritten at every update; the ledger below it is append-only (`../references/architecture-and-state.md`).

3. **Quality gate before approval:**
   - All core requirements (1a–1j, 1o) captured
   - Data Discovery findings don't contradict Stage A requirements (if they do, resolve and note the trade-off in `project_state.md`)
   - Dashboard Complexity Score calculated and path decision made
   - Data Quality Gate checks pass (or failures are explicitly acknowledged)

4. **Get user approval** via `AskUserQuestion`: "Does this capture your requirements and the confirmed data findings?"

5. **Business context, data dictionary, requirements doc** — `./references/step-1v-business-context.md`: draft `business-context.md` (markers) and `data-dictionary.md`, one review question, write `requirements.md` and give its path. Do not wait for the customer's answers.

→ See `./references/step-1u-finalization.md` and `./references/exit-checklist.md` for the full validation checklist and error-handling guidance.

---

## Phase 1 Deliverables (End of Phase 1)

- ✅ Project name recorded — `<project_slug>`, working directory `agent_outputs/<project_slug>/`
- ✅ Data source type confirmed
- ✅ Core requirements gathered (metrics, dimensions, filters, date range, sharing, exclusions)
- ✅ Database/tables confirmed to exist; time column identified
- ✅ Metrics and dimensions validated against live data
- ✅ Filter scope classified (dashboard-level / tab-level / widget-level)
- ✅ Data Quality Gate run (Checks 1–12)
- ✅ Dashboard Complexity Score calculated (0–6) and path decision made
- ✅ `agent_outputs/<project_slug>/project_state.md` created with all of the above
- ✅ User approved the plan
- ✅ `business-context.md` (markers) and `data-dictionary.md` drafted and reviewed; `requirements.md` written and its path given (Step 1v)
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
| Business context, data dictionary, requirements doc | `./references/step-1v-business-context.md` |

---

## Next Phase

### ➡ Move to Phase 2 (Workflow — optional) or Phase 3 (Build Dashboard)

**Condition:** Phase 1 requirements + data discovery approved, `project_state.md` created.

**What happens next:**
- If path decision = Workflow → go to Phase 2 to deploy a scheduled `.dig` workflow, then Phase 3
- If path decision = Non-Workflow (or pre-aggregated data source) → skip straight to Phase 3
- Phase 3 reads `agent_outputs/<project_slug>/project_state.md` for confirmed metrics, dimensions, and data source details — no re-asking needed

---

**Version:** 1.0.0
**Last Updated:** 23 July 2026
**Author:** FDE Team
