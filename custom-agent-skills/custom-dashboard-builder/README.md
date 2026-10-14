# FDE TAIS Dashboard Builder

Build custom dashboards from Treasure Data databases using a **self-serve 5-phase pipeline** that routes to either **non-workflow** (interactive, ad-hoc) or **workflow** (production, scheduled) paths. HTML Client is the only rendering engine — a single portable `dashboard.html`, no server required.


## Trigger phrases

Use this skill when the user says or implies: **build/create/make a dashboard**, **analytics or KPI dashboard**, **HTML dashboard**, **Treasure Data/Treasure Insights dashboard**, **dashboard requirements/questionnaire**, **dashboard data discovery/validation**, **dashboard workflow/SINK tables**, **Sisense migration**, **convert a `.dash` file to HTML**, **resume/continue a dashboard**, **dashboard automation**, **reusable dashboard skill**, **dashboard AI companion**, or **dashboard handoff documentation**.

A query-only request or a general chart question without a dashboard engagement should not trigger this pipeline.

## The Pipeline: One Flow, Two Paths

All dashboards follow the same 5 phases. At the end of Phase 1 (Stage B), your requirements determine which path is best:

```
Phase 1 (Stage A + B): Requirements Gathering & Targeted Data Discovery
                    ↓ SCORING AT END OF STAGE B (0-6 rubric)
                    │
    ┌───────────────┴──────────────────────────────────────┐
    │                                                        │
    ↓ Score 0-2                ↓ Score 3 (Optional)          ↓ Score 4-6
  Non-Workflow                Ask user                     Workflow
  Phase 3: Build Dashboard    Phase 2 or Phase 3            Phase 2: Deploy Workflow
                                                             Phase 3: Build Dashboard
    ↓                                                          ↓
  Phase 4 (optional):                                       Phase 4 (optional):
  Automate Dashboard & Deploy Companion AI Agent             Automate Dashboard & Deploy Companion AI Agent
    ↓                                                          ↓
  Phase 5 (optional):                                       Phase 5 (optional):
  Handoff Documentation                                     Handoff Documentation
```

### Quick Comparison

**Non-Workflow Path** (Score 0-2):
- Best for: Ad-hoc analysis, immediate needs
- Data: Query source tables directly (live)
- Cost: Pay-per-query (low if infrequent)

**Workflow Path** (Score 4-6):
- Automatic daily runs
- Best for: Production dashboards, frequent access
- Data: Pre-aggregated SINK tables (optimized)
- Cost: Low (pre-aggregated daily)

✅ **Integrated Dashboarding Agent**
- Phase 4: Companion AI agent deployment for conversational metric analysis
- Agent answers questions: "What's driving trends?", "Which dimensions perform best?"

---

## How to Start

**→ Always begin with Phase 1 (Requirements + Data Discovery)**

### For New Engagements

1. **Read `SKILL.md`** (this is your entry point) → "How to Start" section
2. **Execute Phase 1** (Stage A: requirements, Stage B: data discovery):
   - `./phase-1/SKILL.md` → Output: `state.md` created + **path score (0-6)**
3. **At end of Phase 1 Stage B, score determines your next file:**
   - **Score 0-2 (Non-Workflow):** `./phase-3/SKILL.md` (skip Phase 2)
   - **Score 3 (Optional):** Ask user: "Quick build or production workflow?" → route accordingly
   - **Score 4-6 (Workflow):** `./phase-2/SKILL.md` first, then Phase 3
4. **Phase 4-5:** Optional dashboard automation, companion AI agent deployment, and handoff documentation

### For Resuming Existing Engagements

1. Ask: "What's your project name?"
2. Ask the user to paste their `./<project-name>/state.md` contents, then read it to recover project state
3. Read it → Jump to current phase + next action

---

## Decision Tree

**Use this to choose your path:**

```
User asks: "I need a dashboard"
    ↓
Q1: Do you need the dashboard now?
├─ YES → NON-WORKFLOW PATH
├─ NOT SURE → Ask clarifying questions below
│  ├─ "Will you regenerate this 10+ times?"
│  │  ├─ YES → WORKFLOW PATH
│  │  └─ NO → NON-WORKFLOW PATH
│  ├─ "Do you need daily automated updates?"
│  │  ├─ YES → WORKFLOW PATH
│  │  └─ NO → NON-WORKFLOW PATH
│  └─ "Will you want AI insights about the data?"
│     ├─ YES → WORKFLOW PATH (with Phase 4 agent)
│     └─ NO → NON-WORKFLOW PATH
└─ NOT NOW (can wait) → WORKFLOW PATH
```

---

## Phase 1: Requirements Gathering & Data Discovery

**Deliverable:** `state.md` created + Stage B Scoring (0-6 model)
**Both paths use this:** Non-Workflow and Workflow paths complete Phase 1 identically

**Reference:**
- **`./phase-1/SKILL.md`** — Full Phase 1 instructions and steps
- **`./phase-1/INSTRUCTIONS.md`** — Phase 1 specific rules and quick checklist
- **`./phase-1/references/phase-1-walkthrough.md`** — Stage A: KPIs, dimensions, filters, schedule, compliance. Stage B: database/table discovery, metrics validation, **path decision (0-6 score)**

---

## Phase Summary Table

| Phase | Input | Output | Path(s) | Reference |
|-------|-------|--------|---------|-----------|
| **1: Requirements + Data Discovery** | Business questions + table exploration | `state.md`, KPIs, dimensions, table catalog, **path decision (0-6 score)** | Both | `./phase-1/SKILL.md` |
| **2: Deploy Dashboard Workflow** | Workflow config | SINK tables, schedule | Workflow only | `./phase-2/SKILL.md` |
| **3: Build Dashboard + Validate** | Business context + tables | Accurate interactive `dashboard.html` | Both | `./phase-3/SKILL.md` |
| **4: Automate & Deploy Agent** | Dashboard + tables | Dashboard skill + AI agent | Both (opt) | `./phase-4/SKILL.md` |
| **5: Handoff Documentation** | Implementation notes | 4 local markdown files | Both (opt) | `./phase-5/SKILL.md` |

---

## Quick Reference: Pick the Right File for Your Task

| Your Question | Read This |
|---|---|
| "What do I need to build a dashboard?" | Start with Phase 1 in `SKILL.md` |
| "How do I gather requirements?" | `./phase-1/SKILL.md` + `./phase-1/references/phase-1-walkthrough.md` (Stage A) |
| "How do I discover the right tables?" | `./phase-1/references/phase-1-walkthrough.md` (Stage B) |
| "Should I use Workflow or Non-Workflow?" | `./phase-1/references/stage-b-path-routing.md` (0-2 = Non-Workflow, 3 = Optional, 4-6 = Workflow) |
| "How do I set up a workflow?" | `./phase-2/SKILL.md` + `./phase-2/references/phase-2-walkthrough.md` (Workflow path only) |
| "How do I build the dashboard?" | `./phase-3/SKILL.md` + `./phase-3/references/phase-3-walkthrough.md` (both paths) |
| "How do I validate my data?" | `./phase-3/references/phase-3-walkthrough.md` (Validation gates) |
| "How do I test my dashboard?" | `./phase-3/references/testing-troubleshooting.md` |
| "Can I automate this dashboard?" | `./phase-4/SKILL.md` + `./phase-4/references/track-a-automation.md` (Track A) |
| "Can I add an AI agent?" | `./phase-4/references/track-b-ai-agent.md` (Track B) |

---

## Solution Structure

```
fde-tais-dashboard-builder/
├── SKILL.md              ← you are here — entry point and phase routing
├── README.md              ← this file
├── INDEX.md               ← full file & folder index
├── references/
│   └── guardrails-lite.md ← cross-phase guardrails (data integrity, queries, rendering, agent prompts)
├── phase-1/               ← Phase 1: Requirements + Data Discovery (Stage A + Stage B, state.md created)
├── phase-2/               ← Phase 2: Deploy Dashboard Workflow (template setup, configure, deploy, validate SINK tables) [Score 4-6 only]
├── phase-3/                ← Phase 3: Build + Validate Interactive Dashboard (HTML Client only, 12-step build+validate loop)
├── phase-4/                ← Phase 4: Automate Dashboard & Deploy companion AI Agent (Track A: skill extraction | Track B: Foundry AI agent) [Optional]
└── phase-5/                 ← Phase 5: Handoff Documentation (4 local markdown files) [Optional]
```

---

## Non-Workflow Path (Score 0-2)

**Entry point:** After Phase 1 Stage B, score 0-2
**What to read:** `./phase-3/SKILL.md` → `./phase-3/references/phase-3-walkthrough.md`
**Best for:** Ad-hoc analysis, immediate needs, exploratory work

**Features:**
- Query source tables directly (live data)
- Rendering: HTML Client (single portable file — no engine choice needed)
- Interactive filters and drill-downs
- Ready to share/embed immediately
- **Iterative refinement** — update colors, metrics, charts
- **Optional: Save as reusable skill** for future reuse

---

## Workflow Path (Score 4-6)

**Entry point:** After Phase 1 Stage B, score 4-6
**What to read (in order):**
1. `./phase-2/SKILL.md` → `./phase-2/references/phase-2-walkthrough.md` — Deploy dashboard workflow
2. `./phase-3/SKILL.md` → `./phase-3/references/phase-3-walkthrough.md` — Build Dashboard + Validate Loop

**Best for:** Production dashboards, frequent access, historical tracking

**Features:**
- Custom workflow creation via `tdx wf`
- Pre-aggregated SINK tables (optimized datamodel)
- Scheduled daily/weekly runs
- Fast dashboard queries (sub-second on pre-aggregated data)
- Optional: Companion Foundry agent for conversational analysis
- Operational runbook & monitoring

---

## The Business Context File: Central Control

**`state.md`** is the single source of truth for all dashboard implementation details, written under `./<project-name>/`. It controls SQL generation, validation, and feedback incorporation. It replaces the old `project_context.md` — same append-only pattern, no git/Confluence framing.

### What It Is
- **Business goals** — what the dashboard tracks
- **KPIs** — exact metrics and their SQL calculations
- **Dimensions** — slice-by attributes with cardinality
- **Exclusion rules** — hard filters (e.g., exclude test accounts)
- **Refresh schedule** — when/how often to update

### How It Flows Through Phases
```
Phase 1: Gather requirements + discover tables
    ↓
Phase 1: Distill into state.md
    ↓
Phase 2: Workflow SQL reads state.md (if run)
    ↓
Phase 3: Dashboard queries + validation read state.md
    ↓
Phase 4: Skill/agent extraction reads state.md (if run)
    ↓
FEEDBACK arrives
    ↓
Update state.md
    ↓
Phase 2-3 regenerate with new context
```

**See `./phase-1/references/phase-1-walkthrough.md` for template and detailed guidance.**

---

## Rendering

HTML Client only — a single portable `dashboard.html` with data inlined at build time. No engine-choice question is ever asked; there's nothing to decide.

---

## Prerequisites & Constraints

### Non-Workflow Path Requirements
- ✅ Treasure Data auth: `tdx auth` configured and active (`tdx use`)
- ✅ Read access to databases/tables you want to dashboard
- ✅ Basic SQL knowledge
- ❌ NO workflow deployment needed

### Workflow Path Requirements
- ✅ Treasure Data `push-workflow` credentials configured
- ✅ TD project with write access (for workflow deployment)
- ✅ Read/write access to source + sink databases

### Both Paths
- ✅ Source databases/tables exist and contain current data
- ✅ User can verify via `tdx databases` and `tdx describe`

---

## Data Accuracy Requirement (CRITICAL)

**EVERY DASHBOARD MUST USE REAL DATA FROM QUERIES, NOT SYNTHETIC DATA.**

1. Query the database first → Get actual schema, dimensions, aggregates
2. Never guess or assume → Query it
3. Embed exact real numbers → Not rounded estimates
4. Document the source → Database name + timestamp

**Validation gate (all dashboards):**
- [ ] Database connectivity verified
- [ ] Tables/columns verified
- [ ] Dimensions verified (SELECT DISTINCT)
- [ ] Aggregates calculated (SELECT ... GROUP BY)
- [ ] Results embedded (exact numbers, not synthetic)

See `./phase-3/references/phase-3-walkthrough.md` (Quality gates section) for detailed validation procedures.

---

## Security & Privacy (CRITICAL)

⚠️ **STRICT RULES:**

1. **Never read query output files yourself or hardcode real data into scripts**
   - Query results may contain PII: emails, phone numbers, IDs, addresses
   - AI reading these files exposes sensitive data
   - **Solution**: All data flows through Node scripts (`generate-data.js`, `render.js`) only

2. **All data must flow through rendering scripts, not AI context**
   - Write query results to a local temp/output file
   - Node scripts read these files via `parseTable()` functions
   - Agent never reads the files directly

3. **No sample/mock data with real values**
   - Never copy real data into examples
   - Use placeholders: `{email}`, `{id}`, `{count}`, etc.

4. **No hardcoded key names or field lists**
   - Derive column names dynamically from query results
   - Don't assume structure

5. **Minimize data in Agent context**
   - Include only config and templates when saving skills
   - Store actual data in separate `data.json` files (not in code)
   - `render.js` loads `data.json` at runtime, not code generation time

---

## Iterative Workflow: Create → Feedback → Iterate → Save

### Non-Workflow Path Example

```
Step 1: Initial Dashboard
User: "Show me revenue by region and product"
→ Agent queries database → Renders dashboard

Step 2: Get Feedback & Iterate
User: "Add pie chart for segment, change default to 90 days"
→ Agent updates config → Re-renders

Step 3: Save as Reusable Skill (Optional)
User: "Perfect! Can you save this?"
→ Agent creates skill: dashboard-revenue-by-region
→ Ready to regenerate anytime

Step 4: Future Regeneration
Next conversation: "Generate my revenue dashboard"
→ Skill loads → Dashboard regenerates instantly ✅
```

---

## Key Reference Files

| File | Purpose | Path |
|------|---------|------|
| **SKILL.md** | 5-phase workflow entry point | Root |
| **phase-1-walkthrough.md** | Phase 1 requirements + data discovery (Stage A + B) | `./phase-1/references/` |
| **phase-2-walkthrough.md** | Phase 2 workflow deployment (Workflow path only) | `./phase-2/references/` |
| **phase-3-walkthrough.md** | Phase 3 dashboard build + validate (both paths) | `./phase-3/references/` |
| **phase-3-data-patterns.md** | Data patterns, filters, cardinality, performance | `./phase-3/references/` |
| **track-a-automation.md** | Phase 4 Track A: skill extraction & automation | `./phase-4/references/` |
| **track-b-ai-agent.md** | Phase 4 Track B: Foundry AI agent deployment | `./phase-4/references/` |
| **testing-troubleshooting.md** | Comprehensive dashboard testing checklist + troubleshooting guide | `./phase-3/references/` |
| **guardrails-lite.md** | Cross-phase guardrails | `./references/` |
| **treasure-data-theme.md** | Official Treasure AI 2026 brand colors & styling | `./references/` |

---

## Multi-Database Support

Dashboards can join data from multiple Treasure Data databases. Specify all required databases during Phase 1, and queries will join across them as needed.

---

## Support & Questions

- **On-demand dashboards?** → Read `SKILL.md` → Phase 1 → Score 0-2 → Phase 3
- **Scheduled production dashboards?** → Read `SKILL.md` → Phase 1 → Score 4-6 → Phase 2 → Phase 3
- **How to gather requirements?** → `./phase-1/SKILL.md` (Stage A)
- **How to discover tables?** → `./phase-1/references/phase-1-walkthrough.md` (Stage B)
- **Business context strategy?** → `./phase-1/references/phase-1-walkthrough.md`
- **Workflow deployment?** → `./phase-2/SKILL.md` + `./phase-2/references/phase-2-walkthrough.md`
- **Automation & AI agents?** → `./phase-4/SKILL.md` + `./phase-4/references/track-a-automation.md` or `track-b-ai-agent.md`
- **Handoff documentation?** → `./phase-5/SKILL.md` + `./phase-5/references/phase-5-walkthrough.md`
- **Data validation?** → `./phase-3/references/phase-3-walkthrough.md` (Quality gates section)
- **Testing & troubleshooting?** → `./phase-3/references/testing-troubleshooting.md`

---

**Version:** 1.0.0
**Last Updated:** 23 July 2026
**Author:** FDE Team
