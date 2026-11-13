# NBA AI Signal — Customer Agent Setup

NBA AI Signal specifics for `../../shared/customer_agent_pattern.md` (agent name, staging build, install, verify). Template: `<solution_dir>/project_templates/agent_template/`. Agent name: `<project_slug>-agent` (`nba-ai-signal-agent` by default).

## What the agent does

Answers questions about the deployed Next Best Action model — whether the learned policy beats past decisions (estimated policy value vs logged reward, confidence interval, tuning hold-out lift), which actions are recommended to how many customers and how that differs from the past mix, why a customer gets an action, how stable recommendations are between runs, which settings tuning chose, "how was it built" — by querying the `nba_ais_*` tables and the recommendations in the sink database, and builds the standalone HTML dashboard with `references/generate-data.js`.

## Placeholders

Standard placeholders plus two NBA AI Signal ones, all in `.md` files:

| Placeholder | Value | Used in |
|---|---|---|
| `{{agent_name}}` | Confirmed agent name | `SKILL.md` frontmatter, generator path in `SKILL.md` and `references/dashboard_template.md` |
| `{{project_name}}` | Project display name (e.g. `Offer NBA AI Signal`) | `SKILL.md` description and intro, dashboard command, `business-context.template.md` |
| `{{project_slug}}` | Project slug (e.g. `offer-nba-ai-signal`) | Dashboard command |
| `{{sink_database}}` | Confirmed sink database | `SKILL.md`, `references/data-dictionary.md`, `references/dashboard_template.md` |
| `{{engagement_dir}}` | `agent_outputs/<project_slug>` | `SKILL.md`, `references/data-dictionary.md`, `references/dashboard_template.md` |
| `{{pred_table}}` | `pred_output_table` from the deployed config (default `nba_ais_actions`) | Table names in `SKILL.md` and `references/` |
| `{{decision}}` | The decision in one short phrase from `business-context.md` (e.g. `which offer to send each customer`) | `SKILL.md` description and intro |

`references/generate-data.js` and `references/dashboard_template.html` are copied unchanged — their `{{…}}` tokens are filled by the script at run time.

Two files are copied in at every build (`../../shared/customer_agent_pattern.md` Step 2): the engagement's `business-context.md` (drafted from `references/business-context.template.md` in Phase 1 — the skeleton itself is never installed) and `<solution_dir>/references/ai-signals-guide.md`, unchanged.

`references/workflow-guide.template.md` and `references/model-setup-walkthrough.template.md` are **guide skeletons**: removed from every build and filled only when the user chose the guides — interim in Phase 4, final in Phase 5 (Guides, below).

## Agent files

Show this table to the user after every build (`../../shared/customer_agent_pattern.md` Step 6), with only the files the build contains, then a starter prompt.

| File | What it is for | Ask it, for example |
|---|---|---|
| `SKILL.md` | The agent's instructions: what it answers, which tables it queries, its accuracy rules | "What can you help me with?" |
| `references/business-context.md` | Your business knowledge — the decision, your actions and their names, what counts as success, who is eligible, data edge cases, goals and rules. Keep adding to it while you test: the more it says, the better the agent understands your data and jargon, and the less it guesses | "Which of our business definitions are still unconfirmed?" |
| `references/ai-signals-guide.md` | How the AI Signals Next Best Action model works: the input it needs, its API parameters, how it tunes, learns and evaluates, how to read the outputs, common changes | "How does the model decide between the offers, and what does exploration mean?" |
| `references/data-dictionary.md` | Every NBA output table and column, and what each metric means | "What is the estimated policy value, and is ours good?" |
| `references/workflow-guide.md` (if built) | The deployed workflow end to end: actions, reward, context features and their windows, config values, output tables | "How is success defined in the model?" |
| `references/model-setup-walkthrough.md` (if built) | What was decided during setup and why, the validation baseline and accuracy rules | "Why were these actions merged?" |
| `references/dashboard_template.md`, `dashboard_template.html`, `generate-data.js`, `visualization-instructions.md` | The NBA AI Signal Summary dashboard: the agent runs `generate-data.js` to fill the HTML template with the latest run, and follows the chart rules for answers in chat | "Show me the NBA dashboard" |
| `references/runbook.md` (Phase 5) | Operating the production workflow | "How do I retrain the model?" |

## Build checks (Phase 4 Part A)

After installing, from the Work Folder root:

1. `tdx query -d <sink_database> "SELECT session_id, estimated_policy_value FROM nba_ais_run_log ORDER BY time DESC LIMIT 1"` returns the validated run, and `tdx query -d <sink_database> "SELECT COUNT(*) FROM <pred_table>"` returns the scored customers.
2. Generate the dashboard once with the command in the installed `SKILL.md`. Pass = exit without error and `ls -l agent_outputs/<project_slug>/dashboards/nba_ai_signal_dashboard.html` shows the file.
   - Pre-validated: no screenshots, browser / QA scripts, data re-checks, HTML edits or other design skills. Looks wrong → tell the user.
   - No `node` → chat analysis still works; the HTML dashboard needs Node.js.

## Guides (Phase 4 interim, Phase 5 final)

Built only when the user chose them (Phase 3 end question for interim, Phase 5 question for final) — mechanics and the Interim / Final status line in `../../shared/customer_agent_pattern.md` Step 4:

| File | Content |
|---|---|
| `workflow-guide.md` | Fill `<solution_dir>/project_templates/agent_template/references/workflow-guide.template.md` — the as-built workflow: pipeline, input SQL (actions, reward, context, scoring population, windows), model settings, output tables. Follow the skeleton's build instructions |
| `model-setup-walkthrough.md` | Fill `<solution_dir>/project_templates/agent_template/references/model-setup-walkthrough.template.md` — discovery, requirements, decision log, data quality and leakage checks, runs and validation baseline, Parent Segment, artifacts, presentation recipe, accuracy rules. Follow the skeleton's build instructions |

Interim guides describe the setup deployed so far — assumed defaults marked "to confirm", Parent Segment and docs sections "Not done yet — Phase 5". They are already routed by the **How It Was Built** section of `SKILL.md`.

## Finalize (Phase 5)

Rebuild with the confirmed `business-context.md` (playbook Phase 5 step 3; Step 2 copies it), then add to the staging folder's `references/`:

| File | Content |
|---|---|
| `runbook.md` | Copy of `docs/runbook.md` |

Add `runbook.md` to the **Initialization** list in the staging `SKILL.md` as "read only for operations questions"; then ask about the final guides (Guides, above). Add one line under **Query Rules**: "When `workflow-guide.md` and the config columns of the latest `nba_ais_run_log` row disagree, report the difference — the table reflects what actually ran." Run the placeholder check in `../../shared/customer_agent_pattern.md` Step 2 before installing.
