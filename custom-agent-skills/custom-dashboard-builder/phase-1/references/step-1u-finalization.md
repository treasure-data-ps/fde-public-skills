# Stage A: Validation & Finalization (Step 1u)

## Step 1u: Validate All Requirements & Get Approval

**Purpose:** Consolidate Stage A findings, get user approval, and prepare for Stage B (data discovery).

**Important Note:** `state.md` is created at the end of Stage A Step 1u (after user approval). Stage B then APPENDS to it with data discovery findings.

---

## Quality Gates (Must Pass All)

Before finalizing, check:

- ✅ **`guardrails-lite.md` read** — (`../../references/guardrails-lite.md`) — must have been read at session start
- ✅ All Setup steps answered (Setup-A through Setup-E)
  - `project_name` captured (determines `./<project_name>/` working directory)
  - `business_goal` captured
  - `target_platform` captured (informative only — does not change rendering)
  - `data_source_type` captured and `skip_workflow` flag set
  - `reference_resource_provided` + `resource_type` captured (Setup-E) — if `resource_type = .dash`, this checklist does not apply; see the `.dash` Special Case in `steps-1pre.md` for its own finalization/validation gate instead
- ✅ All core steps completed (1a–1o, 1p, plus conditionals)
- ✅ Metrics are user-defined with formulas (not generic labels)
  - Good: "Revenue = SUM of order amounts excluding refunds"
  - Bad: "Total Revenue"
- ✅ `timezone` explicitly set — not just "date range confirmed" (⚠️ CRITICAL)
- ✅ `benchmark_values` captured (metric expected ranges for Phase 2/4 sanity checks)
- ✅ `dashboard_theme` captured (`td-default` or custom brand colors/logo)
- ✅ `rendering_engine` recorded as `HTML Client` (fixed, from Step 1r-post)
- ✅ Dashboard Complexity Score Q1/Q2/Q3 individual values recorded; all 3 validation checks run (Q1 vs 1f, Q2 vs 1g, Q3 vs 1h) — conflicts resolved
- ✅ Path confirmed by user (Workflow vs Non-Workflow)
- ✅ If Workflow AND `skip_workflow ≠ true`: SINK DB, TD Project, Run Schedule captured
- ✅ Agent YES/NO decision explicitly recorded (not left blank)
- ✅ Stage A → Stage B bridging documented (flagged assumptions, data priorities, data quality concerns)
- ✅ All Stage A requirements consistent — NO `<REQUIRED>` fields left blank in `state.md`
- ✅ No contradictory requirements unresolved
  - Example: "Real-time" + "minimize cost" → Escalate: "Which is more important?"
  - Example: "10 years history" + "daily refresh" → Note: "Discuss archival strategy in Stage B"

**If any gate fails:** Return to relevant step, re-gather, re-validate, re-ask approval.

---

## User Approval (Stage A Requirements)

Before asking for approval, present the full requirements summary in a code block so the user can review everything in one place:

```
📋 Requirements Summary — <project_name>

Project Slug:         <project_name>
Platform:             <target_platform>
Rendering:            HTML Client (single portable dashboard.html)
Path:                 <Workflow | Non-Workflow>
Schedule:             <refresh_schedule or N/A>
Timezone:             <timezone>

Audience:
  <who accesses this dashboard>

Metrics (user-confirmed):
  • <Metric 1>: <formula>
  • <Metric 2>: <formula>
  • <Metric 3>: <formula>

Dimensions / Filters:
  • <Dimension 1>: <typical values>
  • <Dimension 2>: <typical values>

Date Range:
  Default: <default_date_range>
  Picker:  <yes | no>

Layout Preference:    <summary cards / tables / charts / numbers>
Historical Depth:     <e.g. 2 years>

Workflow (if applicable):
  SINK DB:            <sink_database>
  TD Project:         <td_project_name>

Agent:                <yes | no>  →  <agent_name if yes>

Dashboard Complexity Score:      Q1=<n> Q2=<n> Q3=<n>  Total=<n>/6
Assumptions to validate in Stage B:
  • <assumption 1>
  • <assumption 2>
```

**---  ↑ Review the summary above, then respond below  ↑  ---**

```
AskUserQuestion:
  header: "Requirements Approval"
  question: "Does the requirements summary above look correct?"
  options:
    - label: "✅ All correct — proceed to Stage B"
      description: "Everything looks accurate. Move to data discovery."
    - label: "⚠️ Metrics need changes"
      description: "One or more metric definitions or formulas are wrong."
    - label: "⚠️ Filters / dimensions need changes"
      description: "Dimensions, filter values, or date range need adjustment."
    - label: "⚠️ Other section needs changes"
      description: "Platform, path, schedule, audience, or something else needs fixing."
```

**If changes needed:**
1. Return to relevant Stage A step and re-gather/clarify
2. Update `state.md` draft
3. Re-validate quality gates
4. Re-show the updated summary code block
5. Re-ask approval with the same AskUserQuestion

**Once approved:** Proceed to Stage B (data discovery).

---

## Storage & Tracking

### Write state.md

After user approval, write `state.md` locally in `./<project_name>/`. This file is the cross-phase context for the project — every phase reads and appends to it.

**No external template dependency** — write the block below directly (do not look for a template in any other repo):

```markdown
# <project_name> — Dashboard Project State

## Session Setup
- Project Slug: <project_name>
- Business Goal: <business_goal>
- Target Platform: <target_platform>
- Data Source Type: <data_source_type>
- skip_workflow: <false | true | partial | tbd>

## Requirements (Stage A)
- Metrics: <list with formulas>
- Dimensions/Filters: <list>
- Date Range: <default + picker>
- Timezone: <timezone>
- Layout: <preference>
- Historical Depth: <value>
- Benchmark Values: <value>
- Dashboard Theme: <td-default or custom>
- Rendering Engine: HTML Client
- Dashboard Complexity Score: Q1=<n> Q2=<n> Q3=<n> Total=<n>/6
- Path: <Workflow | Non-Workflow>
- Workflow Config (if applicable): SINK DB=<..>, TD Project=<..>, Schedule=<..>
- Agent: <yes/no>, Name=<..>

## Stage B → Phase N (appended by later phases)
```

**Before writing, verify:**
- Every `<REQUIRED>` field has a real value from Stage A
- If ANY `<REQUIRED>` field is missing → return to the relevant step, gather it, re-validate, re-ask approval
- `<OPTIONAL>` fields may be written as `TBD` — Stage B will fill them

**`<REQUIRED>` fields most commonly missed:**
- `Timezone` — ⚠️ CRITICAL; often forgotten when date range is collected
- `Benchmark Values` — required for Phase 2/4 sanity checks
- `Dashboard Theme` — required for Phase 3 render; even "td-default" must be explicitly set
- `Agent Requirement` — must be one of: "no agent" | "yes" | "not sure yet" (never blank)
- Q1/Q2/Q3 individual values — must be separate numbers, not just the total score
- `User-Confirmed Path` — recommended path is not enough; user confirmation must be recorded

---

## ⚠️ Common Mistakes to Avoid

### File & Folder Creation
- ❌ **Creating multiple `state.md` files** — One file per project, append all phases to it

### Documentation
- ❌ **`<REQUIRED>` fields left blank** — Every `<REQUIRED>` field must be filled; don't proceed if any are blank
- ❌ **Timezone not explicitly set** — Often forgotten; explicitly ask "What timezone for all dates?" (⚠️ CRITICAL)
- ❌ **Benchmark values not captured** — Needed for Phase 2/4 sanity checks ("Revenue should be roughly $X")

### Gates & Approval
- ❌ **Skipping quality gates** — All gates in "Quality Gates" section must pass before finalizing
- ❌ **Not showing requirements summary before approval** — Always present summary code block first, then AskUserQuestion
- ❌ **Proceeding without explicit user approval** — AskUserQuestion must return "All correct" before moving to Stage B

---

## Write state.md (Stage A Complete)

After the user approves, write `state.md` locally in the working directory:

```bash
mkdir -p ./<project_name>/
# Write full Stage A output (Session Setup + all requirements from 1a–1u) to:
# ./<project_name>/state.md
```

Include all fields from the Session Setup block in `steps-1pre.md` plus the business requirements gathered in Steps 1a–1u.

---

## Final Output (Stage A Complete)

- ✅ All Setup steps answered (Setup-A through Setup-E)
- ✅ All Stage A business requirements gathered and documented (or derived from a `.dash` resource, per the Special Case)
- ✅ Reference resources read and findings extracted
- ✅ Rendering engine recorded as HTML Client (no choice needed)
- ✅ Dashboard Complexity Score calculated (0-6) with path recommendation (Workflow vs Non-Workflow)
- ✅ `state.md` created locally at `./<project_name>/state.md` with Session Setup block + all requirements
- ✅ User sign-off on all Stage A requirements
- ✅ **Ready for Stage B (targeted data discovery)**

**Important Note:** `state.md` is created in Stage A. Stage B appends data discovery findings to the same file. Each later phase adds to the same file.

---

## End-of-Stage A Checklist

### Core Requirements

- [ ] Dashboard purpose and success criteria documented
- [ ] All metrics confirmed with **user-defined formulas** (not generic labels)
- [ ] Metric groups + top 3-5 analytical questions captured
- [ ] `benchmark_values` captured (top metric expected ranges — used in Stage B sanity check and Phase 4 validation)
- [ ] Business glossary captured (domain terms, abbreviations, column value meanings)
- [ ] All dimensions confirmed with typical values + unique value estimates
- [ ] All filters mapped with types and dependencies identified
- [ ] Layout preference documented (summary cards vs tables, charts vs numbers)
- [ ] `dashboard_theme` captured — `td-default` OR custom `{ primary_color, secondary_color, logo_url, logo_background }`
- [ ] `proposed_tabs` captured — tab names from customer input, or `TBD`
- [ ] Default date range + date picker capability confirmed
- [ ] **`timezone` explicitly confirmed** (⚠️ CRITICAL — not just "date range confirmed")
- [ ] Core lookback window (metric calculation window) documented
- [ ] Data freshness SLA + acceptable lag documented
- [ ] Historical data depth and retention period confirmed
- [ ] Step 1h (Sharing/Access) completed — access audience, user role, technical depth, data sensitivity flag, downstream consumers
- [ ] Exclusion rules documented in SQL format (or "None" / "TBD for Stage B")
- [ ] Data quality handling rules documented

### Optional Sections (if triggered)

- [ ] Mobile/responsive design requirements (Step 1k — if mobile use case)
- [ ] Compliance & governance requirements (Step 1l — if sensitive data flagged)
- [ ] Data source complexity + canonical ID + IDU status (Step 1m — if multi-table joins)
- [ ] Drill-down depth requirements (Step 1n — if multi-level dimensions)
- [ ] CDP activation intent (Step 1o-ext — if pre-aggregated/Parent Segment source)

### Configuration Sections

- [ ] **`rendering_engine` recorded as `HTML Client`** — fixed, no selection needed (Step 1r-post)
- [ ] **Workflow path (if Score 4-6 AND `skip_workflow ≠ true`):**
  - [ ] SINK database name documented
  - [ ] Treasure Data workflow project name confirmed
  - [ ] Aggregation run schedule selected
  - [ ] Refresh frequency confirmed
- [ ] **Agent configuration (Step 1r — agent YES/NO must be recorded, not left blank):**
  - [ ] Agent requirement decision recorded — one of: "no agent" | "yes" | "not sure"
  - [ ] If agent = yes: agent name, capabilities captured
- [ ] **Stage A → Stage B bridging documented (Step 1s):**
  - [ ] Flagged assumptions listed (or "None")
  - [ ] Data discovery priorities listed (or "Standard discovery")
  - [ ] Known data quality concerns listed (or "None")
- [ ] Custom requirements (Step 1t — if applicable):
  - [ ] All project-specific questions answered
  - [ ] Dependencies and follow-up actions documented

### Final Deliverables

- [ ] Dashboard Complexity Score calculated: 0-6 (Q1 + Q2 + Q3 values recorded)
- [ ] Path recommendation confirmed (Workflow vs Non-Workflow) + user-approved
- [ ] All Stage A requirements approved by user
- [ ] **`state.md` filled — no `<REQUIRED>` fields left blank**
- [ ] Ready to move to Stage B (targeted data discovery)

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team

---

## ⚠️ Error Recovery: Revisiting Phase 1 Mid-Project

**Scenario:** User discovers in Phase 2/3 that a Phase 1 decision was wrong (wrong table, wrong metric, wrong filter scope).

**Recovery path:**

1. **Identify what changed:**
   - Which Phase 1 decision is wrong? (metric definition, table, filter scope, etc.)
   - What's the impact? (whole dashboard broken, one metric affected, etc.)

2. **Update state.md:**
   ```markdown
   ## RECOVERY: [Date] — Revisited Phase 1 decision
   
   **Issue:** [What was wrong]
   **Original decision:** [What was chosen]
   **Corrected decision:** [New choice + rationale]
   **Affected Phase 1 step:** [e.g., Step 1d — metric definitions]
   ```

3. **Restart affected downstream phases:**
   - **Metric definition wrong** → Restart Phase 2 (workflow SQL) or Phase 3 (queries)
   - **Table wrong** → Restart Phase 2 (data source) or Phase 3 (queries)
   - **Filter scope wrong** → Restart Phase 3 (filter architecture)

4. **Do NOT redo Phase 1 from scratch** — only revalidate the specific decisions that changed.

---

