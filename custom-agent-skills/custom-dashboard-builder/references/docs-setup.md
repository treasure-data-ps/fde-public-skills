# Dashboard Builder — Handoff Docs

Optional, Phase 5 Step 3. Four docs, written to `agent_outputs/<project_slug>/docs/` from the templates in `<skill_dir>/phase-5/references/templates/` (copy, then fill — never edit the templates). Sources: `project_state.md`, `business-context.md`, `metrics-catalog.md`, `data-dictionary.md`, `eval.md`, the workflow copy (if Phase 2 ran) and the dashboard master copies. Each doc starts with `> Audience: customer` or `> Audience: internal`.

| Doc | Template | Audience | Must contain |
|---|---|---|---|
| `architecture.md` | `templates/architecture.md` | customer | The real data flow: source tables → workflow and SINK tables (if any) → `generate-data.js` queries → `dashboard.html`; the dashboard agent in `.claude/skills/<name>/` and its knowledge files; refresh frequency; dependencies |
| `usage_guide.md` | `templates/usage_guide.md` | customer | How to open and refresh the dashboard (through the agent); every KPI with its meaning; filters and charts; real example questions for the agent; common questions |
| `runbook.md` | `templates/runbook.md` | internal | Real workflow and table names, schedule and monitoring commands (`tdx wf sessions`, `tdx wf timeline`, `tdx wf attempt … tasks`); "workflow did not run", "numbers look wrong", "too slow" procedures; rebuilding the agent; where the master copies live |
| `access_ownership.md` | `templates/access_ownership.md` | internal | Owner and contacts as the user names them (roles if they prefer), access tiers, change requests, Treasure Data permissions needed |

Rules: real names, paths and examples from this engagement — no template placeholders left; no secrets; customer docs contain no Treasure Data internals (internal workflow details stay in the runbook). Record the doc paths in `project_state.md`.
