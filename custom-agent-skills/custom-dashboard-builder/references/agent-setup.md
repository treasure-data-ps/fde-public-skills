# Dashboard Builder — Agent Setup

Dashboard-agent specifics for `../../shared/customer_agent_pattern.md`. Template: `<skill_dir>/project_templates/agent_template/`. Agent name: `<project_slug>-dashboard-agent`.

## What the agent does

Opens and refreshes the project's dashboard with one command (data inlined into `agent_outputs/<project_slug>/dashboards/dashboard.html`), explains metrics and numbers from the metrics catalog and business context, answers follow-up questions with SQL against the same tables, adds or changes metrics in the dashboard template on request (after approval), and summarizes trends.

## Files copied at every build

`customer_agent_pattern.md` Step 2 copies `business-context.md` and `data-dictionary.md`. Also copy the other master copies from the engagement folder into `$stage/references/`:

```bash
d="agent_outputs/<project_slug>"
cp "$d/metrics-catalog.md" "$d/sql-templates.md" "$stage/references/"
cp "$d/dashboards/dashboard.template.html" "$d/dashboards/generate-data.js" "$stage/references/"
```

Never copy `dashboard.html`, query results or `data.json` into the agent.

## Placeholders

Standard placeholders plus the dashboard ones, all in `SKILL.md`:

| Placeholder | Value |
|---|---|
| `{{agent_name}}` | `<project_slug>-dashboard-agent` |
| `{{project_name}}` | Project display name (e.g. `Acme Campaign Performance`) |
| `{{engagement_dir}}` | `agent_outputs/<project_slug>` |
| `{{dashboard_title}}` | The dashboard's title (the `<h1>` of the approved template) |
| `{{data_database}}` | The database the dashboard queries — the SINK database (Workflow path) or the source database (Non-Workflow) |
| `{{data_source_note}}` | `pre-aggregated by workflow <project>` or `queried directly from the source tables` |
| `{{source_database}}` | Source database |
| `{{sink_database}}` | SINK database; the source database again on the Non-Workflow path |
| `{{trigger_phrases}}` | 3–5 natural phrases from the business goal (e.g. "campaign dashboard", "show me campaign performance") |

The four knowledge files carry `{{project_name}}` from their skeletons — filled when the engagement copies were written.

## Agent files

Show after every build, then a starter prompt.

| File | What it is for | Ask it, for example |
|---|---|---|
| `SKILL.md` | The agent's instructions: refresh command, how it explains numbers, ad-hoc questions, adding metrics, rules | "What can you help me with?" |
| `references/business-context.md` | Your business knowledge — audience, terms, metric meaning, data caveats, exclusion and compliance rules. Keep adding to it: the more it says, the less the agent guesses | "Which of our definitions are still unconfirmed?" |
| `references/metrics-catalog.md` | Every dashboard metric: formula, source, exclusions, validated value | "How is average order value calculated?" |
| `references/data-dictionary.md` | Tables and columns behind the dashboard, time column, data quality notes | "Which table does the revenue chart use?" |
| `references/sql-templates.md` | The dashboard's queries, reusable for follow-up questions and new metrics | "Show revenue by region for last quarter" |
| `references/dashboard.template.html`, `generate-data.js` | The dashboard itself — the agent fills the template with fresh data in one command | "Show me the dashboard" |
| `references/runbook.md` (Phase 5) | Operating the dashboard and agent | "How do I refresh the workflow?" |

## Build checks (Phase 4 Step 3)

From the Work Folder root:

1. Run the refresh command from the installed `SKILL.md` once. Pass = exits without error, `agent_outputs/<project_slug>/dashboards/dashboard.html` is rewritten (`ls -l`), and nothing new appears in `.claude/skills/<name>/` (`ls .claude/skills/<name>/references/`).
2. The headline KPI in the regenerated file matches the Phase 3 spot-check value (one `tdx query` against `metrics-catalog.md`'s formula).
3. `grep -c "INFERRED\|NEEDS YOUR INPUT" .claude/skills/<name>/references/business-context.md` — report the number of unconfirmed items.

## Finalize (Phase 5)

Rebuild with the confirmed `business-context.md`, then add `references/runbook.md` (copy of `docs/runbook.md` if the docs were written; otherwise a short runbook: refresh command, workflow schedule and monitoring if Phase 2 ran, how to update the business context and rebuild, where the master copies live). Add it to the Session Start list in the staging `SKILL.md` as "read only for operations questions".
