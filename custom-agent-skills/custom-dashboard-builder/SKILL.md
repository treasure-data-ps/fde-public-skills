---
name: fde-tais-custom-dashboard-builder
description: >-
  Build or resume a custom HTML dashboard on Treasure Data data, and the project's own dashboard
  agent, through a questionnaire-led 5-phase pipeline: requirements and data discovery (with a
  recommended architecture — direct queries or a pre-aggregating workflow), optional workflow,
  dashboard build, the dashboard agent installed as a Work Folder skill, and an evaluation until it
  is production-ready. Trigger when the user asks to build, create, make, develop, or resume a
  dashboard, analytics dashboard, KPI dashboard, HTML dashboard, Treasure Data dashboard,
  Treasure Insights dashboard, Sisense dashboard migration, .dash conversion, dashboard from
  SQL/data, dashboard from a Treasure Data table, interactive dashboard, dashboard workflow,
  SINK dashboard, dashboard validation, dashboard agent, or dashboard handoff documentation. Also
  trigger when the user says resume dashboard, continue dashboard, dashboard requirements,
  dashboard questionnaire, dashboard data discovery, dashboard performance, dashboard filters,
  dashboard KPIs, dashboard to HTML, or dashboard from a .dash file. Do not skip the Phase 1
  questionnaire or any execution-contract gate; special-case imports prefill answers but still
  require explicit confirmation.
---

# FDE TAIS Dashboard Builder

> **⚠️ CRITICAL: Read instructions in this order:**
> 1. **`./INSTRUCTIONS.md`** (master instructions — load first)
> 2. **`./references/execution-contract.md`** (non-skippable gates and checkpoint ledger)
> 3. **The current phase's files** (Phase Reference Index below)
> 4. **`./SKILL.md`** (this file)
> 5. **Re-read after context compaction** (mandatory)

Builds a custom dashboard from Treasure Data databases and the project's **dashboard agent** with a self-serve 5-phase pipeline. Rendering is always **HTML Client** — a single portable `dashboard.html` with data inlined at build time. Everything is local to the Work Folder: engagement files in `agent_outputs/<project_slug>/`, the agent in `.claude/skills/<project_slug>-dashboard-agent/`.

**`<skill_dir>`** = the folder containing this `SKILL.md` — resolve it to an absolute path from the skill's base directory before running any command that reads from it (templates in `<skill_dir>/project_templates/`, scripts in `<skill_dir>/tools/`, shared patterns in `<skill_dir>/../shared/`). Commands run from the Work Folder, never from `<skill_dir>`. Templates are read-only: copy them into the project folder and edit the copy.

---

## How to Start

This builder follows the custom-agent principles in `<skill_dir>/../shared/playbook.md` (template copied into the Work Folder → data exploration → business context → agent → evaluation → production-ready) with its own phases, gates and approval phrases — the execution contract wins where they differ.

### Step 0: Engagement Type

**Ask the user:** "Is this a new dashboard engagement, or are you resuming an existing one?" — wait for the answer before any other step.

#### New engagement

1. Re-read `./references/execution-contract.md` and `./references/guardrails-lite.md`.
2. Say: "For this project, here are the 5 phases we'll work through step by step." and show:

   ```
   📊 FDE TAIS Dashboard Builder — Project Phases

   ✅ Phase 1: Requirements + Data Discovery
      → Stage A: KPIs, dimensions, filters, audience, success metrics
      → Stage B: validate tables/columns, recommend metrics/dimensions, dashboard plan
      → Output: Dashboard Complexity Score (0-6) + recommended architecture + business context draft

   ✅ Phase 2: Deploy Dashboard Workflow  [Optional — recommended for Score 4-6]
      → Scheduled workflow that pre-aggregates metrics into SINK tables

   🎨 Phase 3: Build Interactive Dashboard
      → dashboard.template.html + generate-data.js → dashboard.html, iterated until you approve it

   🤖 Phase 4: Dashboard Agent
      → Your project skill: opens and refreshes the dashboard, explains every metric,
        answers follow-up data questions, adds metrics — installed in this Work Folder

   🧪 Phase 5: Evaluation → Production-Ready
      → 10 test prompts until the agent passes; optional handoff docs
   ```

3. Read `./phase-1/SKILL.md` and start Phase 1. After Phase 1, route to Phase 2 or Phase 3 per the path decision.

**Special case — `.dash` file:** if the user provides a Sisense / Treasure Insights `.dash` export (or JSON with a `"widgets"` array and a `"datasource"` key) during session setup, Phase 1 converts it with `<skill_dir>/tools/dash_to_html.py` and prefills requirements and discovery — `./phase-1/references/steps-1pre.md` ("`.dash` / Sisense Special Case"). Prefilled answers are still shown and confirmed.

#### Resuming

1. Re-read `./references/execution-contract.md` and `./references/guardrails-lite.md`.
2. List `agent_outputs/*/project_state.md` and keep those whose **Solution** is `dashboard-builder`; confirm the project with `AskUserQuestion`.
3. Read it: the header's Current phase and Next Action say where to pick up; the Phase Ledger holds every earlier decision. Show a short "Resuming" summary (completed phases, next action, key details) and continue at the next incomplete phase.

---

## Phase Reference Index

| Phase | Read | Key output | Condition |
|-------|------|-----------|-----------|
| **1: Requirements + Data Discovery** | `./phase-1/SKILL.md` | Score (0-6) + path decision + `project_state.md`; `business-context.md`, `data-dictionary.md`, `requirements.md` (Step 1v) | Always |
| **2: Workflow** | `./phase-2/SKILL.md` | SINK tables deployed + validated (`agent_outputs/<project_slug>/workflows/`) | Optional — Score 4-6 recommended, user can override |
| **3: Build Dashboard** | `./phase-3/SKILL.md` | Approved `dashboard.template.html` + `generate-data.js` + `dashboard.html` (`agent_outputs/<project_slug>/dashboards/`) | Always |
| **4: Dashboard Agent** | `./phase-4/INSTRUCTIONS.md` | `<project_slug>-dashboard-agent` installed to `.claude/skills/` | Always |
| **5: Evaluation → Production-Ready** | `./phase-5/INSTRUCTIONS.md` | `eval.md` rounds until ≥ 9/10 Pass + every Compliance case; finalized agent; optional docs | Always |

**Path decision at the end of Phase 1** (user can override): Score 0-2 → Phase 3 directly; Score 3 → user chooses; Score 4-6 → Phase 2, then Phase 3.

The state pattern (`project_state.md` header + append-only Phase Ledger) is in `./references/architecture-and-state.md`.

---

## How It Works

1. **Phase 1** asks what the dashboard must show and for whom, checks every metric against the live data, scores the complexity and recommends the architecture (direct queries or a pre-aggregating workflow). It drafts the business context and data dictionary the agent will use, and a requirements doc for the customer.
2. **Phase 2** (optional) deploys a scheduled workflow from `project_templates/workflow_template/` that writes SINK tables.
3. **Phase 3** copies `project_templates/dashboard_template/`, writes the queries in `generate-data.js`, renders `dashboard.html` and iterates with the user until approved.
4. **Phase 4** builds the dashboard agent from `project_templates/agent_template/` with the approved template and script and four knowledge files (business context, data dictionary, metrics catalog, SQL templates), and installs it with `<skill_dir>/../shared/customer_agent_pattern.md`.
5. **Phase 5** evaluates the agent with `<skill_dir>/../shared/eval_pattern.md` and finalizes it.

## Quick Reference

- **Solution:** `dashboard-builder` (the **Solution** line in `project_state.md`)
- **Engagement folder:** `agent_outputs/<project_slug>/` — `project_state.md`, `business-context.md`, `data-dictionary.md`, `metrics-catalog.md`, `sql-templates.md`, `requirements.md`, `workflows/`, `dashboards/`, `agent_build/`, `eval.md`, `docs/`
- **Agent:** `.claude/skills/<project_slug>-dashboard-agent/`
- **Templates:** `project_templates/workflow_template/`, `dashboard_template/`, `agent_template/`
- **Approval phrases:** `YES, APPROVE [ACTION]` (execution contract), e.g. `YES, APPROVE AGENT INSTALL FOR <name>`
- **Production bar:** ≥ 9/10 Pass and every Compliance case Pass

## Security & Privacy

**STRICT RULE:** query results flow through `generate-data.js` into the HTML, never into the chat context (`./references/guardrails-lite.md`). Nothing is uploaded or hosted — the dashboard and the agent stay in the Work Folder.
