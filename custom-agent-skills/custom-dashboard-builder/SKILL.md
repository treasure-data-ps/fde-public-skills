---
name: fde-custom-dashboard-builder
description: |
  Use when the user wants a custom HTML dashboard on Treasure Data data — built from a list of metrics and filters, or converted from an existing dashboard (.dash export, HTML file, screenshot) — or wants to resume, change or rebuild a dashboard project or its workflow. Trigger on: build a dashboard, create a KPI dashboard, I need a dashboard for these metrics, dashboard from a table or screenshot, convert a dashboard to HTML, Treasure Insights / Sisense dashboard migration, .dash conversion, dashboard workflow, resume dashboard project, using fde-custom-dashboard-builder. Asks before each decision and creates the project's dashboard skill only after the user agrees. Questions about an existing project dashboard's numbers go to that project's skill.
---

# Custom Dashboard Builder

Turns a list of metrics and filters — or an existing dashboard — into a single offline `dashboard.html` built from live Treasure Data queries, plus a **dashboard skill** for the project. Setup is a first draft with as few questions as possible; the user iterates afterwards through the dashboard skill (change metrics, filters, business context).

**`<skill_dir>`** = the folder containing this file — resolve it to an absolute path before running anything from it. Commands run from the Work Folder root. Templates in `<skill_dir>/project_templates/` are read-only: copy, then edit the copy.

**Treasure AI Studio questions:** when the user asks how Treasure AI Studio works — Work Folders, permissions and access, sharing skills or agents, plugins and marketplaces, or where to find Studio documentation — answer from what you know, then share the official documentation: https://docs.treasure.ai/products/ai-studio/overview

**Setup skill vs. project agent:** this skill sets up, changes and rebuilds the solution; it is the same for every project. Once the project's own agent is installed in `.claude/skills/` (`<project_slug>-dashboard`), questions about its results are answered by that agent. If this skill is invoked with such a question, read the installed agent's `SKILL.md` and answer by its rules (or tell the user to ask the agent in a new chat); if no agent is installed yet, say so and offer the setup.

## The flow

| Step | What happens | Asks the user |
|---|---|---|
| 1. Intake | Existing dashboard or metric list, database, project name | 1–2 questions |
| 2. Data Q&A + recommendation | Discovery queries, data quality, size; direct or workflow | 1 (accept the recommendation) |
| 3. Workflow (only if recommended) | Plan, defaults, build, run, validate, report | 1 (approve build + run) |
| 4. Dashboard + dashboard skill | First draft, spot-checks, knowledge files, register | 1 (register the skill) |

Start with one sentence on what will happen and this table, then ask Step 1's starting question. Use `AskUserQuestion` for every question, with a `(Recommended)` default for information only; never ask what the data can answer.

**Gates:** the resume choice, Step 1's starting point, Step 2's accept-or-switch, Step 3's build approval and Step 4's skill creation stop the flow. Do nothing past a gate until the user has answered in this conversation. Silence, a dismissed prompt, or an empty or off-topic reply is not an answer — ask again in plain text and stop. Never take a `(Recommended)` option on the user's behalf. If `AskUserQuestion` is unavailable, ask the same question in plain text and wait. Between non-gate steps, give a 2–4 line summary and continue.

**Shell working directory:** the shell keeps its `cd` between calls. Never `cd` outside a subshell — `( cd <dir> && <command> )` — and write every path in Steps 3–4 relative to the Work Folder root or as `$d`-style variables from it.

**Resume:** if `agent_outputs/*/project_state.md` with **Solution:** `dashboard-builder` exists, ask "new dashboard or continue `<project>`?" and pick up at its Next Action.

## Step 1 — Intake

Read `references/intake.md`. One `AskUserQuestion` batch:

- **Starting point:** "I have an existing dashboard" (attach a `.dash` export, an HTML file or a screenshot) / "I'll list the metrics and filters" / "Not now" (stop; nothing is written).
- **Database:** the database the tables live in — offer the likely ones from `tdx databases` (never assume).

Then read the dashboard (intake.md) or take the metric list, and derive the project name from the dashboard title (`<project_slug>`, lowercase with hyphens, e.g. `sales-performance`). Bootstrap the workspace — `<skill_dir>/../shared/local_outputs.md` Step 1 — and create `agent_outputs/<project_slug>/project_state.md` (`<skill_dir>/../shared/project_state.md`, **Solution:** `dashboard-builder`). Say once that all data in the HTML file is visible to anyone who opens it. Record the spec in `project_state.md`: Current phase "2 — data discovery", Next Action "Run data discovery".

## Step 2 — Data Q&A and recommendation

Read `references/data-discovery.md` and run it without asking: tables and columns, the business time column and timezone, each metric validated as a formula on live data, joins checked for fan-out, the data-quality gate, dimension cardinality, payload estimate, query times. Ask only what the data can't answer (e.g. which column defines "cancelled", or a metric with two valid definitions).

Present one summary — metrics as formulas with their current values, filters, data range, caveats — and the **recommendation** (direct `generate-data.js` + template, or a workflow first) with its reasons. One question: accept, or switch path. Record everything in `project_state.md` → Discovery Findings, with the accepted path; Current phase "3 — workflow" or "4 — dashboard + skill" and the matching Next Action.

## Step 3 — Workflow (only when recommended)

Read `references/workflow-setup.md`. Show the plan — SINK tables with their grain and measures, the refresh mode, and the defaults for the workflow project name and `sink_database` (checked to be free). One `AskUserQuestion`: "Build, run and validate (Recommended)" / "Change project, database or table names" / "Skip the workflow — build directly". On approval: copy and customize the template, push, run, monitor, validate the SINK tables against the source, and report (tables, rows, spot-checks, issues). If validation fails, fix and re-run before Step 4. Update `project_state.md` after the approval (names), after the run (attempt, result) and after validation (tables, checks) — Current phase "4 — dashboard + skill" once it passes.

## Step 4 — First-draft dashboard, then the dashboard skill

1. **Dashboard** — `references/dashboard-build.md`: copy `project_templates/dashboard_template/` into `agent_outputs/<project_slug>/dashboards/`, write `CONFIG`, `QUERIES` and `LAYOUT` in `generate-data.js`, run it, spot-check ≥ 3 KPIs against the source (exact match), and show the dashboard. No approval needed — it is a local file. Update `project_state.md`: Next Action "Ask whether to create the dashboard skill".
2. **Ask before any skill file is written** — one `AskUserQuestion`, a gate: header "Dashboard skill"; question "Create the dashboard skill `<project_slug>-dashboard` in this Work Folder? It lets you open, refresh and explain this dashboard in new chats. It writes only to `.claude/skills/<project_slug>-dashboard/`." Options: "Create the skill (Recommended)" / "Not yet — keep the dashboard only". Wait for the answer.
3. **On "Create the skill"** — knowledge files and agent build (`references/agent-setup.md` §1–2): write `business-context.md` (inferences flagged for review), `data-dictionary.md`, `metrics-catalog.md` and `sql-templates.md` in `agent_outputs/<project_slug>/`, then build in the staging folder (`<skill_dir>/../shared/customer_agent_pattern.md` Step 2). Install (pattern Step 3), run the build check in `references/agent-setup.md` §3, and show how to use it: "Show me the dashboard", "How is <KPI> calculated?", "Add <metric> to the dashboard". Update `project_state.md`: Current phase "complete — dashboard skill live", what was built, open business-context items.
   **On "Not yet"** — write nothing under `.claude/skills/`. Update `project_state.md`: Current phase "4 — dashboard + skill", Next Action "Ask to create the dashboard skill when the user is ready". Tell the user they can ask for it at any time.

After Step 4 the user iterates through the dashboard skill. **On request only:** a 10-prompt evaluation of the skill (`references/eval-setup.md` + `<skill_dir>/../shared/eval_pattern.md`), a customer requirements questionnaire for the open business-context items (`references/requirements_doc.md`), handoff docs (`references/handoff-docs.md`), or a workflow change.

## Rules

- **Live data only.** Every number comes from a query; data reaches the HTML only through `generate-data.js`. Never type data into files.
- **Query results never enter the chat.** Results flow `tdx → generate-data.js → dashboard.html`; checks use aggregate queries that return single numbers.
- **Nothing changes in the account without approval** — the workflow (Step 3) and creating the dashboard skill (Step 4) are the approval points. Everything else is read-only. Silence is not approval.
- **Local only.** All files stay in the Work Folder (`agent_outputs/<project_slug>/`, `.claude/skills/<project_slug>-dashboard/`); nothing is uploaded or hosted. No generated `dashboard.html` or query output inside `.claude/skills/`.
- **No PII rows in the HTML** — aggregate, or mask.
- Templates and shipped scripts are pre-validated: fill them in, don't rewrite the engine.

## Quick reference

| Item | Value |
|---|---|
| Engagement folder | `agent_outputs/<project_slug>/` — `project_state.md`, knowledge files, `intake/`, `workflows/`, `dashboards/`, `agent_build/` |
| Dashboard skill | `.claude/skills/<project_slug>-dashboard/` |
| Templates | `project_templates/workflow_template/`, `dashboard_template/`, `agent_template/` |
| Tools | `tools/dash_to_html.py` (`.dash` spec extraction) |
| Workflow defaults | project `<project_slug>_dashboard` (underscores), tables `<project_prefix>_sink_<group>` |
| Payload budget | data < 500 KB ideal, ≤ 2 MB hard stop |
