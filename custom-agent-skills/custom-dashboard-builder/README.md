# FDE TAIS Dashboard Builder — User Guide

Build a custom HTML dashboard on your Treasure Data data — and a dashboard agent that opens it, explains it and answers follow-up questions — step by step in a Treasure AI Studio Work Folder. The builder asks what the dashboard must show, checks every metric against your data, recommends the right architecture (direct queries, or a scheduled workflow that pre-aggregates the data), builds the dashboard with you, and turns it into a project skill that is tested before it is called production-ready.

Everything stays in your Work Folder: no uploads, no hosting, no external services.

## Getting started

1. Add the `fde-public-skills` marketplace in Treasure AI Studio and enable the `custom-agent-skills` plugin.
2. Open (or create) a Work Folder for the project — e.g. *Automotive Dashboard*. All files are created there, which also makes troubleshooting easy.
3. In a new chat, ask for a dashboard, e.g. *"I would like to create a custom automotive dashboard using fde-tais-dashboard-builder"*. Naming the skill is optional; use it if another skill picks up the request.
4. Answer **new** (start from scratch) or **existing** (resume, or change a dashboard you built earlier).

The builder then shows the plan and walks through it phase by phase. Most questions offer options with a recommended default; you can always type your own answer.

## The five phases

### Phase 1 — Requirements + data discovery

A short questionnaire, then a check of your data:

- Project name (the folder name), primary business goal
- Existing resources — a Treasure Insights / Sisense `.dash` export, a data model or an existing workflow are read and used to prefill the answers
- Data source type (raw or pre-aggregated), database and tables
- Dashboard tabs, KPIs, filters and dimensions — if unsure, say "all of the above plus anything you find in the data"
- Date range and timezone, primary audience, viewing frequency, historical tracking, usage (single user or teams)
- What the dashboard agent should help with besides opening the dashboard (explain metrics, ad-hoc questions, add metrics, insights)

The builder validates the tables and columns, recommends metrics and dimensions, and presents a **dashboard plan** (tabs, KPIs, filters, optional workflow) for your approval. A complexity score (0–6) recommends the path: build directly, or deploy a workflow first. It also drafts a **business context** (your terms, metric meaning, exclusion and compliance rules — inferred items flagged for review) and a **requirements doc** you can send to your stakeholders.

### Phase 2 — Workflow (optional)

For frequently viewed or large dashboards: a scheduled workflow that pre-aggregates the metrics into SINK tables, pushed, run and validated against the plan. You confirm the SINK database, workflow project name and schedule.

### Phase 3 — Dashboard

The dashboard is built as one HTML file with the data inlined (`dashboard.html`), from a template and a data script (`generate-data.js`). It is shown to you for approval; ask for any change — missing filters or KPIs, metric calculations, colors, tabs, or embedded insights and recommendations — until it meets your expectations.

The data is inlined in the file, so very large data volumes affect file size and performance; the builder warns you and pre-aggregates where needed.

### Phase 4 — Dashboard agent

The approved dashboard becomes your project's **dashboard agent**, installed in the Work Folder as a skill (`.claude/skills/<project>-dashboard-agent/`) after you approve it. In any new chat in the folder you can then ask:

- *"Show me the automotive dashboard"* — refreshes the data and opens it
- *"How is average order value calculated?"*, *"Why did bookings drop last month?"*
- *"Which dealer had the most test drives this quarter?"* — questions beyond the dashboard
- *"Add a cancellation-rate KPI to the overview tab"*

It answers from what was captured during the build — business context, metrics catalog, data dictionary, SQL templates. Publish it from Studio (Develop → Share) to share it with other users.

### Phase 5 — Evaluation → production-ready

The builder writes ten test prompts based on your dashboard and business context (metric definitions, follow-up questions, exclusion and compliance rules, adding a metric), runs them after your approval, scores each one and proposes fixes until at least nine pass and every compliance test passes. Then the agent is finalized. Optional handoff docs (architecture, usage guide, runbook, access & ownership) are written for sharing — review them before sending to make sure no Treasure Data internals are included.

## What gets created

```
<Work Folder>/
├── agent_outputs/<project>/
│   ├── project_state.md          ← where the project stands and every decision; ask "where are we?" to resume
│   ├── business-context.md       ← your terms, metric meaning, rules (keep adding to it)
│   ├── data-dictionary.md, metrics-catalog.md, sql-templates.md
│   ├── requirements.md           ← questionnaire to share with stakeholders
│   ├── workflows/                ← workflow files, if Phase 2 ran (.dig, input_params.yaml, sql/)
│   ├── dashboards/               ← dashboard.template.html, generate-data.js, dashboard.html
│   ├── eval.md                   ← test prompts and results
│   └── docs/                     ← handoff docs, if requested
└── .claude/skills/<project>-dashboard-agent/   ← the dashboard agent
```

## Tips

- If the conversation drifts, ask *"Where are we with the dashboard implementation?"* — the builder reads `project_state.md` and continues phase by phase. You can also ask why, where and how any step was done.
- The builder may implement different dashboards differently for different use cases — the plan you approve in Phase 1 is what it follows.
- At the end, ask *"What could the dashboard builder do better, based on this implementation?"* and share the answer with the plugin maintainers.

## For maintainers

| Path | Contents |
|---|---|
| `SKILL.md` | Entry point: engagement routing and phase index |
| `INSTRUCTIONS.md`, `references/execution-contract.md`, `references/guardrails-lite.md` | Master rules, non-skippable gates, cross-phase guardrails |
| `phase-1/` … `phase-5/` | Phase instructions and step references |
| `project_templates/` | `workflow_template/` (Phase 2), `dashboard_template/` (Phase 3), `agent_template/` (Phase 4) — copied, never edited in place |
| `references/` | State pattern, agent setup, eval setup, requirements doc, docs setup, theme |
| `tools/` | `dash_to_html.py` (`.dash` conversion), `insights-api-helper.py` (Treasure Insights schema) |

Shared patterns used by Phases 4–5 live in `../shared/` (`customer_agent_pattern.md`, `eval_pattern.md`, `local_outputs.md`).
