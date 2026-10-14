# NBA Engagement Scores — Customer Agent Setup

NBA specifics for `../../shared/customer_agent_pattern.md` (name gate, staging build, install, verify). Template: `<solution_dir>/project_templates/agent_template/`. Default agent name: `<customer_slug>-nba-scores-agent`.

## What the agent does

Answers questions about the deployed NBA run — latest-run summary, score and flag distributions, run-to-run comparison, source volumes, "how is X scored" — by querying the three `nba_dash_*` tables in the sink database, and builds the standalone HTML dashboard with `references/generate-data.js`.

## Placeholders

Only the standard placeholders are used, all in `.md` files:

| Placeholder | Value | Used in |
|---|---|---|
| `{{agent_name}}` | Confirmed agent name | `SKILL.md` frontmatter, generator path in `SKILL.md` and `references/dashboard_template.md` |
| `{{customer_name}}` | Customer display name | `SKILL.md` description and intro, dashboard command |
| `{{customer_slug}}` | Customer slug | Dashboard command |
| `{{sink_database}}` | Confirmed sink database | `SKILL.md`, `references/data-dictionary.md`, `references/dashboard_template.md` |
| `{{engagement_dir}}` | `agent_outputs/<customer_slug>/nba-scores` | `SKILL.md`, `references/dashboard_template.md`, `references/visualization-instructions.md` |

`references/generate-data.js` and `references/dashboard_template.html` are copied unchanged — their `{{…}}` tokens are filled by the script at run time.

`references/workflow-guide.template.md` and `references/model-setup-walkthrough.template.md` are **guide skeletons**: removed from every build and filled only when the user chose the guides — interim in Phase 4, final in Phase 5 (Guides, below).

## Build checks (Phase 4 Part A)

After installing, from the Work Folder root:

1. `tdx query -d <sink_database> "SELECT MAX(session_id) FROM nba_dash_model_metrics"` returns the validated run.
2. Generate the dashboard once with the command in the installed `SKILL.md`. Pass = the command exits without an error and `ls -l agent_outputs/<customer_slug>/nba-scores/dashboards/nba_summary_dashboard.html` shows the file. Nothing else — the dashboard template and `generate-data.js` are pre-validated: run the command once and use the result as it is. Do not take screenshots, run browser, QA or validation scripts, re-check the data, or edit the generated HTML, and do not apply other visualization or design skills to it. If something looks wrong, tell the user instead of fixing it. Requires `node`; if it is missing, tell the user the chat analysis still works and the HTML dashboard needs Node.js.

## Guides (Phase 4 interim, Phase 5 final)

Built only when the user chose them (Phase 3 end question for interim, Phase 5 question for final) — mechanics and the Interim / Final status line in `../../shared/customer_agent_pattern.md` Step 4:

| File | Content |
|---|---|
| `workflow-guide.md` | Fill `<solution_dir>/project_templates/agent_template/references/workflow-guide.template.md` — the as-built workflow: pipeline, config values, source mappings, channel / scoring / flag rules, customizations, output tables. Follow the skeleton's build instructions |
| `model-setup-walkthrough.md` | Fill `<solution_dir>/project_templates/agent_template/references/model-setup-walkthrough.template.md` — discovery, requirements, decision log, data cleaning, runs and validation baseline, Parent Segment, artifacts, presentation recipe, accuracy rules. Follow the skeleton's build instructions |

Interim guides describe the setup deployed so far — assumed defaults marked "to confirm", Parent Segment and docs sections "Not done yet — Phase 5". They are already routed by the **How It Was Built** section of `SKILL.md`.

## Finalize (Phase 5)

Add to the staging folder's `references/` (keep the template's `business-context.md` — it explains the metrics generically):

| File | Content |
|---|---|
| `customer-context.md` | This customer's use cases, Parent Segment, what the deployed windows and rules mean for their marketing (exact values live in `workflow-guide.md`), example audiences, caveats — from `docs/behavior.md` |
| `runbook.md` | Copy of `docs/runbook.md` |

Then add `customer-context.md` to the **Initialization** list in the staging `SKILL.md` (right after `business-context.md`) and `runbook.md` as "read only for operations questions"; then ask about the final guides (Guides, above). Add one line under **Critical Rules**: "When `customer-context.md` or `workflow-guide.md` and the run config in `nba_dash_model_metrics` disagree, report the difference — the table reflects what actually ran." Run the placeholder check in `../../shared/customer_agent_pattern.md` Step 2 before installing.
