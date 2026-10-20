# Phase 4 Instructions — Build the Dashboard Agent

> Read `../references/execution-contract.md` (Phase 4 gate) and `../references/guardrails-lite.md` first.

**Goal:** turn the approved dashboard into the project's **dashboard agent** — a skill installed to `.claude/skills/<project_slug>-dashboard-agent/` in this Work Folder, exactly like the other solutions' customer agents. It opens and refreshes the dashboard with one command, explains every metric in the customer's terms, answers follow-up data questions and adds metrics on request. This phase is required: the agent is the engagement's main deliverable.

**Mechanics:** `<skill_dir>/../shared/customer_agent_pattern.md` (name, staging build, install, verify) + `../references/agent-setup.md` (placeholders, files to copy, build checks, agent files table).

## Entry condition

- Phase 3 complete: `agent_outputs/<project_slug>/dashboards/dashboard.template.html` + `generate-data.js` approved by the user (`project_state.md`).
- `business-context.md` and `data-dictionary.md` exist in `agent_outputs/<project_slug>/` (Phase 1 Step 1v — draft them now if they are missing).

## Steps

### Step 1 — Check the dashboard files (no changes to the approved dashboard)

Check `agent_outputs/<project_slug>/dashboards/generate-data.js` against `./references/agent-build-rules.md`: hardcoded databases and queries (one command, no questions), explicit row limits, parallel queries, inline data only, `DASHBOARD_OUTPUT` / `DASHBOARD_TEMPLATE` honoured. If a rule fails, fix the master copy, regenerate once and confirm the KPIs still match the Phase 3 spot-checks.

### Step 2 — Knowledge files

Fill the two remaining knowledge files in `agent_outputs/<project_slug>/` from the skeletons in `<skill_dir>/project_templates/agent_template/references/` (never overwrite an existing engagement copy):

| File | Fill from |
|---|---|
| `metrics-catalog.md` | Phase 1 metric formulas (`project_state.md`), the approved `generate-data.js` queries, the Phase 3 spot-check values, the tab / widget each metric appears in |
| `sql-templates.md` | Every query in `generate-data.js`, parameterized; the workflow SQL if Phase 2 ran (`agent_outputs/<project_slug>/workflows/`); source-table fallbacks |

Update `data-dictionary.md` with anything Phase 2 / 3 added (SINK tables, columns the dashboard reads). The engagement folder holds the **master copies** of all knowledge and dashboard files; every build copies them into the agent.

### Step 3 — Approval, build, install

Show the user what will be installed (agent name, path, the files table from `../references/agent-setup.md`, the trigger phrases) and ask for approval with the exact phrase:

```
To install the dashboard agent, type exactly: YES, APPROVE AGENT INSTALL FOR <project_slug>-dashboard-agent
```

Any other answer: do not install; show the scope again. On approval:

1. `customer_agent_pattern.md` Step 1 — name `<project_slug>-dashboard-agent` (ask only if `.claude/skills/<name>/` is taken by another project).
2. Step 2 — staging build in `agent_outputs/<project_slug>/agent_build/<name>/`, plus the dashboard-specific copies and placeholders in `../references/agent-setup.md`.
3. Step 3 — install to `.claude/skills/<name>/`.
4. Step 5 — verify, then the build checks in `../references/agent-setup.md` (one-command refresh writes `agent_outputs/<project_slug>/dashboards/dashboard.html`, nothing written into `.claude/skills/`).

Tell the user the agent is available in new chats in this folder (and can be shared to the account with Studio's Develop → Share), show the agent files table and a starter prompt ("Show me the dashboard and tell me what changed").

### Step 4 — Record and continue

Append to `project_state.md` (Phase 4 ledger): agent name and path, files installed, build checks, date; header → Current phase "5 — evaluation", Next Action "Write the eval plan". Then continue to Phase 5 (`AskUserQuestion`, Phase 5 as `(Recommended)`).

## Rebuilds

Rebuild (Steps 2–3 of the shared pattern, no new approval phrase needed for a context-only refresh) whenever a master copy changes: customer answers merged into `business-context.md`, an approved Phase 5 fix, a metric added through the agent, or a dashboard change in Phase 3. A rebuild that changes what the agent does (new files, new capabilities) needs the approval phrase again.

## Quality gates

- Agent installed only after `YES, APPROVE AGENT INSTALL FOR <name>`
- No `{{` placeholders, no `*.template.md`, no generated `dashboard.html` or query output inside `.claude/skills/<name>/`
- One-command refresh works from the Work Folder root and matches the Phase 3 spot-checks
- `project_state.md` updated
