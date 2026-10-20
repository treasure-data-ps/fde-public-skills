# Execution Contract — Non-Skippable Workflow Gates

This is the compact execution checklist for every engagement. Detailed procedures remain in the phase reference files; this file defines what must be true before the next action.

## How to use

1. Read this file after the master and cross-phase instructions, and again after compaction.
2. Keep the checklist in the project `project_state.md` and update it **append-only** at every gate.
3. A gate is not complete because a file was read or a plan was written. Record the actual user answer, validation result, or approval.
4. If a required item is unanswered, ambiguous, refused without a documented reason, or failed, stop and resolve it. Never infer completion.

## Engagement start gate

- [ ] New vs. resume answered explicitly
- [ ] Master instructions, cross-phase instructions, and current phase instructions read
- [ ] For a new engagement: guardrails and theme references read
- [ ] For a resume: project folder and `project_state.md` located; state integrity validated

## Phase 1 gate — requirements and discovery

- [ ] Setup-A through Setup-E answered with `AskUserQuestion`
- [ ] Mandatory requirements 1a, 1b, 1c+1d, 1e+1f, 1g, 1h (when customer-facing), and 1o answered
- [ ] Optional questions were either asked because relevant or recorded as not applicable
- [ ] Special-case route selected before normal questions (`.dash`, datamodel, combined, or standard)
- [ ] If a special-case route pre-fills requirements, the prefilled mandatory fields are shown to the user and explicitly confirmed; no required decision is silently skipped
- [ ] Required tables, columns, time fields, joins, and exclusions validated against live schema/data
- [ ] HTML Client data-size feasibility checked
- [ ] Canonical Q1–Q3 Dashboard Complexity Score answered and recorded
- [ ] Path decision recorded; score 3 has an explicit user choice
- [ ] Phase 1 `project_state.md` section appended with a clear next action
- [ ] Step 1v: `business-context.md` (markers) and `data-dictionary.md` drafted and reviewed with the user; `requirements.md` written and its path given

**Phase 1 cannot advance while any mandatory questionnaire is missing.**

## Phase 2 gate — workflow (when selected)

- [ ] State integrity and Phase 1 gate verified
- [ ] Join cardinality, time column, query, and SINK naming checks passed
- [ ] Dry-run completed and output reviewed before approval is requested
- [ ] User approval matches `YES, APPROVE [ACTION]` (case-insensitive); any other response re-opens the gate
- [ ] Physical objects created only after approval
- [ ] SINK outputs validated and appended to `project_state.md`

## Phase 3 gate — dashboard

- [ ] State integrity and prior phase gate verified
- [ ] Dashboard requirements map to tabs, widgets, global/tab/widget rules, and filters
- [ ] Data is piped through the rendering script; raw query output is not read into context
- [ ] Dashboard opens standalone as HTML Client
- [ ] At least 3 KPI spot-checks match the source within the documented tolerance
- [ ] Filter and performance checks passed
- [ ] User approval obtained before declaring the dashboard complete

## Phase 4 gate — dashboard agent (required)

- [ ] Phase 3 approval recorded; `business-context.md` and `data-dictionary.md` exist
- [ ] Master `generate-data.js` passes `phase-4/references/agent-build-rules.md` (one command, no questions, inline data, output outside the skill folder)
- [ ] `metrics-catalog.md` and `sql-templates.md` filled in `agent_outputs/<project_slug>/`
- [ ] User approval matches `YES, APPROVE AGENT INSTALL FOR <project_slug>-dashboard-agent` before the install
- [ ] Agent built in `agent_build/`, no unfilled placeholders, installed to `.claude/skills/<name>/`; build checks passed
- [ ] Output and next action appended to `project_state.md`

## Phase 5 gate — evaluation → production-ready

- [ ] 10-prompt plan written to `eval.md` and approved before running
- [ ] Every round recorded in `eval.md`; fixes applied only with approval; agent rebuilt after fixes
- [ ] Production bar met on the last full run: ≥ 9/10 Pass and every Compliance case Pass
- [ ] Business context confirmed (no `[NEEDS YOUR INPUT]`) before finalize; final round re-run if it changed
- [ ] Handoff docs created only if the user selected them; feedback question asked and recorded
- [ ] Completion appended to `project_state.md`

## Response rule

- **Clear answer:** record it and continue.
- **Ambiguous answer:** repeat the question with the allowed options; do not choose for the user.
- **Refusal:** ask why, record the reason, and stop if the item is mandatory.
- **Approval other than `YES, APPROVE [ACTION]`:** do not create or deploy anything; show the scope again and re-present the approval gate.

## Compaction checkpoint

After compaction or a phase transition, re-read:

1. `./INSTRUCTIONS.md`
2. `./references/guardrails-lite.md`
3. `./references/execution-contract.md`
4. `./phase-N/INSTRUCTIONS.md`
5. `./phase-N/SKILL.md` (Phases 1–3) or `./phase-N/INSTRUCTIONS.md` (Phases 4–5)

Then append proof of the reads and the next unchecked gate to `project_state.md` before continuing.
