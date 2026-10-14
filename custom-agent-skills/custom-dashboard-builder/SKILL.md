---
name: fde-tais-custom-dashboard-builder
description: >-
  Build or resume custom HTML Client dashboards from Treasure Data using a mandatory,
  questionnaire-led 5-phase self-serve pipeline with state.md checkpoints. Trigger when
  the user asks to build, create, make, develop, or resume a dashboard, analytics dashboard,
  KPI dashboard, HTML dashboard, Treasure Data dashboard, Treasure Insights dashboard,
  Sisense dashboard migration, .dash conversion, dashboard from SQL/data, dashboard from
  a Treasure Data table, interactive dashboard, dashboard workflow, SINK dashboard,
  dashboard validation, dashboard automation, reusable dashboard skill, conversational
  dashboard agent, or dashboard handoff documentation. Also trigger when the user says
  resume dashboard, continue dashboard, dashboard requirements, dashboard questionnaire,
  dashboard data discovery, dashboard performance, dashboard filters, dashboard KPIs,
  dashboard to HTML, or dashboard from a .dash file. Do not skip the Phase 1 questionnaire
  or any execution-contract gate; special-case imports prefill answers but still require
  explicit confirmation.
---

# FDE TAIS Dashboard Builder

> **⚠️ CRITICAL: Read instructions in this order:**
> 1. **`./INSTRUCTIONS.md`** (master instructions — load first)
> 2. **`./references/execution-contract.md`** (non-skippable gates and checkpoint ledger)
> 3. **`./phase-N/INSTRUCTIONS.md`** (phase-specific rules)
> 4. **`./SKILL.md`** (this file)
> 5. **Re-read after context compaction** (mandatory)

Build custom dashboards from Treasure Data databases using a **self-serve 5-phase pipeline**. Rendering is always **HTML Client** — a single portable `dashboard.html` file with data inlined at build time. No Confluence, no git branching — everything lives in one local project folder.

---

## How to Start

### Step 0: Engagement Type

**INSTRUCTION FOR CLAUDE:** Use the question below to route the engagement. **Wait for the user's response before proceeding to any phase.**

**Ask the user:** "Is this a new dashboard engagement, or are you resuming an existing one?"

- **Option A: New engagement** → Continue to "New Engagement Path" section below
- **Option B: Resuming existing** → Continue to "Existing Engagement Path" section below

---

#### New Engagement Path

Once you confirm this is a **new engagement**, **re-read these files immediately** (in this order):
1. **`./references/execution-contract.md`** — Non-skippable gates and questionnaire ledger
2. **`./references/guardrails-lite.md`** — Cross-phase guardrails

Then follow these 2 steps:

1. **Say to the user:** "For this project, here are the 5 phases we'll work through step by step."

2. **Display the 5-phase overview:**
   ```
   📊 FDE TAIS Dashboard Builder — Project Phases

   ✅ Phase 1: Requirements + Data Discovery
      → Stage A: Understand KPIs, dimensions, filters, audience, success metrics
      → Stage B: Validate tables/columns exist in your database, recommend metrics/dimensions
      → Output: Dashboard Complexity Score (0-6) + path decision (Workflow or Non-Workflow) + state.md created

   ✅ Phase 2: Deploy Dashboard Workflow  [Optional, recommended for Score 4-6]
      → Deploy a scheduled workflow, pre-aggregate metrics into SINK tables
      → Output: Pre-aggregated tables ready for Phase 3

   🎨 Phase 3: Build Interactive Dashboard (Html)
      → Query SINK tables (or source tables directly) → render a single dashboard.html
      → Test filters, performance, data accuracy
      → Output: Approved interactive dashboard as a HTML with data embedded inline and a generate-data.js data builder

   🤖 Phase 4: Automate & Deploy  [Optional but recommended]
      → Track A: Extract a reusable skill for faster future builds with context/knowledge for natural-language access
      → Track B: Deploy a companion Foundry agent for natural-language access

   📚 Phase 5: Handoff Documentation  [Optional]
      → Create Architecture, Usage Guide, Runbook, Access markdown files locally
   ```

3. **Route to Phase 1:** Read `./phase-1/SKILL.md` — it handles session setup (project name, business goal, scoring, path decision) for both Stage A (requirements) and Stage B (data discovery). After Phase 1 completes, **route to Phase 2 or Phase 3 per the path decision** (no additional prompt needed).

**Special case — providing a `.dash` file:** If, during session setup, the user provides a Sisense/Treasure Insights `.dash` export (or JSON with a `"widgets"` array + `"datasource"` key), Phase 1 detects it and switches to a fast-track migration path — it converts the file with `./references/dash_to_html.py`, prefills requirements and data discovery directly from the export, and skips straight to building/validating the dashboard instead of asking every Stage A/B question from scratch. See `./phase-1/references/steps-1pre.md` ("`.dash` / Sisense Special Case") for the full flow.

#### Existing Engagement Path

Once you confirm this is **resuming an existing project**, **re-read these files immediately** (in this order):
1. **`./references/execution-contract.md`** — Non-skippable gates and questionnaire ledger
2. **`./references/guardrails-lite.md`** — Cross-phase guardrails

Then follow these 3 steps:

1. **Validate the execution contract and state integrity before asking for the project name.**

2. **Ask for the project name:**
   - "What's the project name or folder name you're resuming? (e.g. `./<project-name>/`)"

3. **Locate the project state:**
   - Ask the user to paste the contents of `./<project-name>/state.md` — then read it directly to recover project state
   - Display the project state so the user sees:
     ```
     🔄 Resuming: travel-dashboard

     ✅ Completed Phases:
        • Phase 1 (Requirements + Data Discovery): Score 6/6 — Workflow path

     ⏳ Next Actions:
        • Phase 2: Deploy Workflow (SINK database: test_suraj)
        • Then Phase 3: Build Dashboard

     📌 Key Details:
        • Schedule: Weekly
        • Audience: Multiple (executives + analysts)
     ```

4. **Route to the next incomplete phase based on project state:**
   - For example, if Phase 1 is complete and Phase 2 is next → use `./phase-2/SKILL.md`
   - `state.md` clearly indicates which phase to start with (append-only log of every phase's outputs)

---

## Recommended Model

**This skill works with all Claude models.** Best default: **Claude Sonnet 5** (balanced cost/performance across all 5 phases) or similar. Alternatives can be used but better works with good models with context:
- **Haiku 4.5:** Fast iteration on Phase 1 requirements gathering
- **Opus 4.7/4.8:** Complex Phase 4 agent development if needed

---

## Phase Reference Index

| Phase | Read | Key Output | Condition |
|-------|------|-----------|-----------|
| **1: Requirements + Data Discovery** | `./phase-1/SKILL.md` | Dashboard Complexity Score (0-6) + path decision + **state.md created** | Always |
| **2: Workflow** | `./phase-2/SKILL.md` | Workflow output tables (SINK tables) deployed + validated + **state.md appended** | Optional, recommended Score 4-6 only, user can override |
| **3: Build Dashboard** | `./phase-3/SKILL.md` | User-approved interactive `dashboard.html` + **state.md appended** | Always (after Phase 1 or Phase 2) |
| **4: Automate + Agent** | `./phase-4/SKILL.md` | Reusable skill (Track A) + Foundry agent (Track B) | Optional, either/both/neither |
| **5: Handoff Docs** | `./phase-5/SKILL.md` | 4 local markdown files (Architecture, Usage Guide, Runbook, Access & Ownership) | Optional |

**Path decision at end of Phase 1, Stage B:** (user can override the recommendation)
- **Score 0-2 (Non-Workflow):** Phase 1 → Phase 3 — skip Phase 2
- **Score 3 (Optional):** User chooses between Phase 2 (workflow) or Phase 3 (direct build)
- **Score 4-6 (Workflow):** Phase 2 first, then Phase 3

---

---

## Core Concepts

**→ Read `./references/architecture-and-state.md` for:**
- Full 5-phase pipeline flow diagram
- `state.md` append-only pattern explanation (how context flows between phases)
- When to skip each phase
- Single-session vs multi-session workflows
- Resuming at a specific phase

---

## Phase Routing

**Quick rules:**
- New engagement → Phase 1 → [Phase 2 optional] → Phase 3 → [Phase 4/5 optional]
- Resume → read `./<project-name>/state.md` → jump to "Next Action" at bottom
- Phase 1 score = 3 → user decides: Phase 2 (workflow) or Phase 3 (direct build)

---

## Quick Navigation

| I want to... | Go to... |
|---|---|
| Start a new dashboard | `./phase-1/SKILL.md` |
| Resume an existing project | Read `./<project-name>/state.md`, then jump to next phase |
| Convert a Sisense .dash export | `./phase-1/SKILL.md` (provide the file during Setup-E) |
| Deploy a production workflow | `./phase-2/SKILL.md` (after Phase 1 scores 4-6) |
| Build and test the dashboard | `./phase-3/SKILL.md` |
| Automate for future builds | `./phase-4/SKILL.md` (Track A) |
| Deploy a conversational agent | `./phase-4/SKILL.md` (Track B) |
| Create handoff documentation | `./phase-5/SKILL.md` |

---

## Security & Privacy

**STRICT RULE:** All query results must flow through rendering scripts, never into AI context. See `./references/guardrails-lite.md` ("Never read raw query output files into AI context").

---

→ **Full file & folder index:** `./INDEX.md`

---

**Version:** 1.0.0
**Last Updated:** 23 July 2026
**Author:** FDE Team
