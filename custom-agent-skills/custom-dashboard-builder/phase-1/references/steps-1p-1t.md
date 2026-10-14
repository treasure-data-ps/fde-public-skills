# Stage A: Dashboard Complexity Scoring & Configuration Steps (1p-1t)

## Step 1p: Dashboard Complexity Scoring + Path Decision (Complete)

This step combines THREE inputs to determine the final path to Stage B / Phase 2:
1. **Dashboard Complexity Score** (business need for scheduled workflow vs quick build)
2. **Platform** (informative — always renders HTML Client)
3. **Data Source Constraint** (affects Phase 2 Workflow skip flag)

---

### Step 1-val: Related Requirements Validation (Before Scoring)

**Purpose:** Catch misalignments between complexity questions and related requirement steps BEFORE scoring.

**Validation Checks:**

| Related Pair | Check | If Misaligned |
|--------------|-------|---------------|
| **Q1 (View Frequency) ↔ Step 1f (Data Freshness)** | If Q1=Daily+ AND 1f=Weekly lag → Contradiction | Ask: "You view daily but data is weekly. Need fresher data or is weekly okay?" |
| **Q2 (Trends Critical) ↔ Step 1g (Historical Depth)** | If Q2=Yes AND 1g < 12 months → Contradiction | Ask: "Trends need 12+ months history. Do you have that much data available?" |
| **Q3 (Audience Scope) ↔ Step 1h (Target Users)** | If Q3=Just me BUT 1h lists internal team or customer stakeholders → Contradiction | Ask: "You said just you, but requirements show broader access. Confirm actual audience scope." |

**Action:** Flag misalignments; resolve via user clarification before proceeding to scoring.

---

### Dashboard Complexity Scoring Questions (Q1-Q3)

Ask 3 questions to calculate the 0–6 score:

#### Question 1: Viewing Frequency

```
AskUserQuestion:
  question: "How often will this dashboard be viewed?"
  header: "Viewing frequency"
  multiSelect: false
  options:
    - label: "One-time or rarely (< once a week)"
      description: "Ad-hoc analysis, not recurring (0 pts)"
    - label: "Few times per month"
      description: "Occasional reference (0 pts)"
    - label: "Once a week"
      description: "Regular but not daily (1 pt)"
    - label: "Multiple times a week or daily (Recommended)"
      description: "Frequent access, operational need (2 pts)"
```

- One-time or rarely (< once a week) → **0 pts**
- Few times per month → **0 pts**
- Once a week → **1 pt**
- Multiple times per week or daily → **2 pts**

#### Question 2: Historical Data Needs / Trends Critical

```
AskUserQuestion:
  question: "Do you need to track this data historically over time?"
  header: "Historical data"
  multiSelect: false
  options:
    - label: "No, just current snapshot"
      description: "Only care about today's numbers (0 pts)"
    - label: "Maybe, would be nice"
      description: "Interested but not critical (1 pt)"
    - label: "Yes, absolutely (Recommended)"
      description: "Need to see trends over days/weeks/months (2 pts)"
```

- No, just current snapshot → **0 pts**
- Maybe, would be nice → **1 pt**
- Yes, absolutely (need trends) → **2 pts**

#### Question 3: Audience Scope / User Type

**Note:** If Step 1h has already been asked, pull the answer from there — do not ask again. Q3 maps directly to Step 1h's "who accesses" answer: "Just me" = 0 pts, "Internal team" = 1 pt, "Customer-facing / external users" = 2 pts. Only ask this AskUserQuestion if Step 1h was skipped.

```
AskUserQuestion:
  question: "Who will use this dashboard?"
  header: "Audience scope"
  multiSelect: false
  options:
    - label: "Just me"
      description: "Personal / exploratory use only (0 pts)"
    - label: "Internal team"
      description: "Shared within an internal team (1 pt)"
    - label: "Customer-facing / external users (Recommended)"
      description: "Viewed by customer stakeholders or external audiences (2 pts)"
```

- Just me → **0 pts**
- Internal team → **1 pt**
- Customer-facing / external users → **2 pts**

**Subtotal Dashboard Complexity Score:** Sum of Q1, Q2, Q3 → **0-6 points**

**Score indicates:** Business need for a scheduled Phase 2 (Workflow) vs a quick direct build in Phase 3

---

### Input 2: Data Source Constraint Check

**Recall from Setup-D:** What is the data source type?

**Constraint Rules:**

| Data Source | Phase 2 (Workflow) Can Skip? | Skip Flag |
|-------------|------------------------------|-----------|
| **Raw / transactional** | No | `skip_workflow = false` — use Dashboard Complexity Score normally |
| **Pre-aggregated** | ✅ YES | `skip_workflow = true` — skip Phase 2 regardless of score |
| **Mix** | Partial | `skip_workflow = partial` — decide per-metric in Stage B |
| **Not sure** | TBD | `skip_workflow = tbd` — resolve in Stage B |

**Decision:** If data source = Pre-aggregated → Phase 2 **can skip** (set `skip_workflow = true`)

---

### Combined Path Decision

| Dashboard Complexity Score | Data Source | **Final Path** | **Reason** |
|-----------------|-------------|---|---|
| 0-2 | Any | **Non-Workflow** | Low business need; skip Phase 2, go straight to Phase 3 |
| 3 | Raw/Mix/TBD | **Customer chooses** | Medium need; flexible |
| 3 | Pre-aggregated | **Non-Workflow** | Data already aggregated; skip Phase 2 |
| 4-6 | Pre-aggregated | **Non-Workflow** | High need BUT data pre-aggregated |
| 4-6 | Raw/Mix/TBD | **Workflow** | High need + raw data; run Phase 2 before Phase 3 |

**Output:** Final path recommendation (Workflow / Non-Workflow / Customer chooses)

---

### Explicitly Ask User: Path Confirmation

**Present the combined recommendation to the user:**

```
Question: "Based on your Dashboard Complexity Score and data source:
- Score: X/6
- Data Source: [Raw / Pre-aggregated / Mix]

Recommended path: [Workflow / Non-Workflow / Your Choice]

Does this match your expectations?"

Options:
  - "Yes, proceed with [Workflow / Non-Workflow] path"
  - "I'd prefer the other path" (only for score 3)
  - "Need to reconsider requirements"
```

**If score 3 and user chooses alternative path:**
- **Workflow:** "Understand. You want scheduled refresh. We'll run Phase 2 (Workflow) first."
- **Non-Workflow:** "Understand. You prefer a quick build. We'll skip Phase 2 and build directly in Phase 3."

**Output:** User-confirmed path + justification documented

---

## Step 1q: Workflow Configuration (Workflow Path Only — Score 4-6 AND `skip_workflow` ≠ true)

**Only execute if BOTH are true:**
1. Final path = **Workflow** (from Step 1p logic table)
2. `skip_workflow` flag is NOT `true`

**If `skip_workflow = true`:** Skip this step entirely. The data source is already aggregated — no workflow needed regardless of score. Note in `state.md`: `"Phase 2 (Workflow) skipped: data source is pre-aggregated."`

**AskUserQuestion — Workflow Configuration (batch 3 questions):**

```
AskUserQuestion:
  questions:
    - question: "Where should we store aggregated dashboard data?"
      header: "SINK database"
      multiSelect: false
      options:
        - label: "New dedicated database (Recommended)"
          description: "e.g. <project_name>_dashboard — keeps output isolated and easy to find"
        - label: "Same as source database"
          description: "Write SINK tables back into the source database"
        - label: "Other"
          description: "Specify a different sink database"

    - question: "What should we name the TD Workflow project?"
      header: "Workflow project"
      multiSelect: false
      options:
        - label: "Use project name (Recommended)"
          description: "e.g. <project_name>-dashboard-workflow"
        - label: "Existing project"
          description: "Use an existing workflow project"
        - label: "Not sure"
          description: "I'll create and name it for you"

    - question: "How often should the workflow refresh?"
      header: "Refresh schedule"
      multiSelect: false
      options:
        - label: "Daily, 2:00 AM UTC (Recommended)"
          description: "Off-hours, results ready for morning review"
        - label: "Weekly"
          description: "Run every Monday at 2:00 AM UTC"
        - label: "Custom"
          description: "I'll specify a different schedule/time"
```

**DO NOT:** Assume the user has an existing workflow project; skip SINK database selection; recommend real-time scheduling.

**Output:** SINK database name + TD Workflow project name + refresh schedule — recorded in `state.md`, used directly by Phase 2.

---

## Step 1r: LLM Agent Configuration (Optional — Track B Companion Agent)

**Note:** Phase 4 (Automate & Deploy) includes both Track A (skill packaging) and Track B (Foundry agent). This step configures whether Track B runs. Track A is independent and always available regardless of this answer.

```
AskUserQuestion:
  question: "Would you like a companion LLM agent for this dashboard?"
  header: "Agent deployment"
  multiSelect: false
  options:
    - label: "No, dashboard only (Recommended)"
      description: "Focus on the dashboard, no agent needed"
    - label: "Yes, add an agent"
      description: "Agent answers questions about dashboard data"
    - label: "Not sure"
      description: "Decide later, in Phase 4"
```

**If YES, ask for agent configuration (batch 2 questions):**

```
AskUserQuestion:
  questions:
    - question: "What should we call the agent? (e.g. 'Sales Dashboard Assistant')"
      header: "Agent name"
      multiSelect: false
      options:
        - label: "I'll type the agent name"
          description: "Short human-readable name — no special characters"
        - label: "Generate from project purpose"
          description: "I'll suggest a name based on the business goal from Setup-B"

    - question: "Any specific agent capabilities needed?"
      header: "Agent capabilities"
      multiSelect: true
      options:
        - label: "No special capabilities (Recommended)"
          description: "Keep it simple — answer questions about the dashboard data"
        - label: "Trend analysis"
          description: "Identify patterns and anomalies"
        - label: "Ad-hoc queries"
          description: "Run custom SQL queries"
```

**Output:** `agent_requirement` (no / yes / not sure — never blank) + `agent_name` + `agent_capabilities` — recorded in `state.md`, used by Phase 4 Track B.

**DO NOT:** Push an agent if user says "no"; require agent configuration unless the user wants one.

---

## Step 1r-post: Rendering Engine

**Rendering is always HTML Client** in this lite skill — a single, portable, self-contained `dashboard.html` with data inlined at build time. No question is needed and no other engine is available.

Record automatically: `rendering_engine = HTML Client` — written to `state.md`.

---

## Step 1s: Stage A → Stage B Bridging (Optional — If Clarification Needed)

**Purpose:** Identify unknowns from Stage A that Stage B (data discovery) should prioritize.

**Key actions:**
1. Review Stage A requirements for any "assumed" or "uncertain" items
2. Ask user (optional): "Are there any data discovery questions you'd like us to prioritize?"
   - Options:
     - No, proceed with standard discovery
     - Yes, here are specific things to check
     - I'm unsure if data exists for [metric/dimension] — please verify first
3. Document flags: business assumptions to validate, technical unknowns (e.g., "Does customer_segment column exist?"), dependencies (e.g., "ID Unification must be complete")

**Output:** Stage A → Stage B handoff notes + data discovery priorities + flagged assumptions

**Note:** This step is **optional** — only needed if Stage A left significant open questions.

---

## Step 1t: Additional/Custom Requirements (If Applicable)

**What to do:** Capture any project-specific requirements that don't fit the standard steps above — e.g., a one-off calculation, an unusual export format, or an integration quirk specific to this customer's data.

**Key actions:**
- Ask: "Is there anything specific to your data or use case that we haven't covered yet?"
- Document any custom requirement + its dependencies or follow-up actions under a **"Custom Requirements"** note in `state.md`

**Output:** Custom requirement answers (or "None") + dependencies identified + follow-up actions noted

---

## Quality Checklist: End of Stage A

Before moving to Stage B (data discovery), verify:

- ✅ Dashboard Complexity Score calculated (Q1 + Q2 + Q3 values recorded individually)
- ✅ **Validation checks run and all conflicts resolved:**
  - Q1 (Viewing Frequency) vs Step 1f (Data Freshness) — no contradiction
  - Q2 (Trends Critical) vs Step 1g (Historical Depth) — no contradiction
  - Q3 (Audience Scope) vs Step 1h (Target Users) — no contradiction
- ✅ Data source constraint evaluated (Pre-aggregated = `skip_workflow = true` regardless of score)
- ✅ **Combined path decision made** (Workflow vs Non-Workflow)
- ✅ Path recommendation confirmed and user approved
- ✅ **Workflow configuration captured (if Score 4-6 AND `skip_workflow ≠ true`):** SINK DB, TD Project, Run Schedule
- ✅ **Agent YES/NO decision explicitly recorded**
- ✅ `rendering_engine` recorded as `HTML Client`
- ✅ `dashboard_theme` captured (td-default or custom brand colors/logo)
- ✅ `proposed_tabs` captured (customer input or TBD)
- ✅ `benchmark_values` captured (metric expected ranges)
- ✅ Stage A → Stage B bridging documented: flagged assumptions, data discovery priorities, data quality concerns
- ✅ Custom requirements captured (if any)
- ✅ Ready for Stage B

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
