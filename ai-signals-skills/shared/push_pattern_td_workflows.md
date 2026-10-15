---
name: shared-ml-push-pattern-td-workflows
description: |
  Reusable deploy pattern for ai-signals-skills TD Workflow projects. Covers copying the solution's bundled workflow template (`project_templates/workflow_template/`) into the engagement's `agent_outputs/` working copy, config-only edits, the sink-database and project-name confirmation gates, tdx authentication, `tdx wf push` / `tdx wf upload`, run + monitoring, and validation. Used by every solution under ai-signals-skills/.
---

# Shared: Push Pattern — TD Workflows

Each solution bundles its TD Workflow template in `<solution_dir>/project_templates/workflow_template/` — the single source of truth for the workflow: its `README.md` explains structure, parameters and outputs; its `config/` YAML defines exact parameter names and syntax. The template is **read-only**: copy it into the engagement's working directory, edit the copy, and push from the copy.

## ALWAYS MUST

- Never edit files under `project_templates/`. All customer edits happen in `agent_outputs/<project_slug>/workflow/`.
- Before writing the config, confirm the sink database (Step 3a); before any `tdx wf push` / `tdx wf upload`, confirm the TD workflow project name (Step 5). Both use the default-then-confirm gate in `SKILL.md`.
- Before any `tdx wf run`, ask the user whether to run now.

## Solution variables

The calling solution SKILL provides these values (see its "Quick Reference" section). Keep them in memory for the whole engagement:

| Variable | Meaning |
|---|---|
| `<solution_dir>` | Directory containing the solution's `SKILL.md` (absolute path) |
| `<Workflow project name>` | Default TD workflow project name (from the template's `tdx.json`) |
| `<Workflow Entry point>` | `.dig` file that kicks off a run |
| `<Workflow Config file>` | Params YAML inside the template (e.g. `config/input_params.yml`) |

`<workdir>` below means `agent_outputs/<project_slug>/workflow`.

## Step 1: Copy the Template

Bootstrap `agent_outputs/` first if not done (`local_outputs.md` Step 1). Then:

```bash
dest="agent_outputs/<project_slug>/workflow"
[ -d "$dest" ] || { mkdir -p "$dest" && cp -R "<solution_dir>/project_templates/workflow_template/." "$dest/"; }
```

If the working copy already exists (resumed engagement), do not re-copy — it holds the customer's edited config.

> **Stay in the user's working directory.** The shell keeps its cwd between commands, so never `cd` on its own. Run every command that must execute inside the working copy in a subshell: `( cd "<workdir>" && <command> )`. This keeps later relative paths (`agent_outputs/...`) correct and prevents a nested `agent_outputs/` from being created inside the workflow copy and uploaded with it.

Read `<workdir>/README.md` before editing anything — it explains the workflow structure, every parameter and the outputs.

## Step 2: Inspect the Project Structure

You should NOT need to edit anything in `queries/`, `sql/`, `python/` or `python_files/` for a standard deployment — the template's `README.md` lists the customization points. All customizations are controlled by `<Workflow Config file>` (and the alert email in the entry-point `.dig`, if the customer wants failure notifications — the template ships with the placeholder `your-team@example.com`).

## Step 3: Write the Config

### 3a: Sink database gate

Default: `td_agents`. First check it doesn't already hold this solution's output tables from another engagement: `tdx tables "td_agents.<output_table_prefix>*"` (the prefix is in the template README's Outputs section, e.g. `nba_`). If it does, a run would overwrite them — recommend `<output_table_prefix><project_prefix>` with `-` → `_` (e.g. `nba_loyalty`) instead and say why — if the project has no prefix, ask the user for one. Ask with `AskUserQuestion`: "Use `<recommended>` (Recommended)" / "Use a different database" — explain that the workflow's output tables are written there and the customer agent will query it. Record the answer in `project_state.md`. If the database doesn't exist, the workflow's create-database step creates it on first run (check the template README).

### 3b: Edit the config

Edit `<workdir>/<Workflow Config file>` in place, following the solution's `references/workflow-setup.md`: keep the template's keys and structure exactly, and replace the example values with the customer's (from Phase 1 findings, the requirements doc, and the confirmed sink database). The template's values are examples only. Never add keys the template doesn't define.

## Step 4: Authenticate to the Customer's TD Account

```bash
tdx auth setup            # if not already configured
tdx use <profile_name>    # switch to the customer's profile/account
tdx databases             # confirm you're in the right account by listing databases
```

If the customer's region is non-default (EU01, AP02, etc.), confirm `tdx` is targeting that region. Templates with an `api_endpoint` config key (e.g. MTA, NBP) read it from their config, but `tdx` authenticates with your local profile.

## Step 5: Confirm the Project Name and Push

First check the default isn't taken: `tdx wf projects <Workflow project name>`. If it exists, pushing would replace another project's workflow — recommend `<Workflow project name>_<project_prefix>` with `-` → `_` (e.g. `rfm_ais_loyalty`) instead and say why; if the project has no prefix, ask the user for one. Use `AskUserQuestion`: push under the recommended name, or a custom name (used for multiple isolated pipelines per region or brand).

Make sure `<workdir>/tdx.json` exists and names the confirmed project — some templates ship without one. Create or update it with the Write tool:

```json
{
  "workflow_project": "<confirmed project name>"
}
```

Then push:

```bash
( cd "<workdir>" && tdx wf push -y )
```

Use the confirmed name as `<Workflow project name>` from here on. Because `tdx.json` now records it, every later re-push is the same `tdx wf push -y`.

### Step 5a: Workflow Secrets (if the solution needs them)

Set secrets with `tdx wf secrets` (see `tdx-skills:workflow`). Never write API keys into config files or chat — ask the user to run the secret command themselves (`! tdx wf secrets set …`) if a key value is required.

## Step 6: Run the Workflow

Ask the user first. If yes:

```bash
tdx wf run <Workflow project name>.<Workflow Entry point>
```

For the first run, monitor closely:

```bash
tdx wf sessions <Workflow project name> --status running
tdx wf timeline <Workflow project name>.<Workflow Entry point> --follow
```

If a step fails:

```bash
tdx wf attempt <attempt_id> tasks
tdx wf attempt <attempt_id> logs +<failed_task_name>
```

## Step 7: Validate Results

Run the output validation checks from the "Validate" section of the solution's `references/workflow-setup.md`, then record the results and the push date in `project_state.md`.

## Re-deploying (Phase 4 and later)

Edit the config in `<workdir>`, then re-run Step 5 (no new name confirmation needed unless the name changes) and Steps 6–7.
