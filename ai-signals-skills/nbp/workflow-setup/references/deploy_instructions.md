# NBP — Deploy Instructions

## Workflow Template

The NBP workflow template ships with this skill at:

```
<solution_dir>/project_templates/nbp_prod/
```

`<solution_dir>` is `ml-skills/nbp/` (the directory containing the NBP `SKILL.md`), resolved to an absolute path. The template is read-only — never edit it.

## Copy into the Engagement Working Copy

Bootstrap `agent_outputs/` first (`../../../shared/local_outputs.md` Step 1). Then copy the template — only if a working copy doesn't already exist:

```bash
dest="agent_outputs/<customer_slug>/nbp/workflow"
mkdir -p "$dest"
[ -d "$dest/nbp_prod" ] || cp -R "<solution_dir>/project_templates/nbp_prod" "$dest/"
```

For all subsequent steps (writing `params.yml`, pushing the workflow), work from `agent_outputs/<customer_slug>/nbp/workflow/nbp_prod`.

**Full deploy mechanics** (project name prompt, secrets, run, monitor, validation) are in `../../../shared/push_pattern_td_workflows.md`. Read that file before executing any push step.

## Project Name

The NBP template ships without a `tdx.json`. After the project name is confirmed (default `next_best_product`), create it in the working copy with the Write tool — `agent_outputs/<customer_slug>/nbp/workflow/nbp_prod/tdx.json`:

```json
{
  "workflow_project": "next_best_product"
}
```

Then every push — first and later — is:

```bash
( cd "agent_outputs/<customer_slug>/nbp/workflow/nbp_prod" && tdx wf push -y )
```

## Directory Structure

```
nbp_prod/
├── config/
│   └── params.yml              ← generated configuration (Step 4)
├── queries/
│   ├── create_transaction_table_filters.sql   ← custom training exclusion (when exclusion_values: query)
│   └── filter_products_recs.sql               ← custom recommendation exclusion
├── nbp_launch.dig              ← main workflow entry point
└── ...                         ← workflow SQL and sub-workflows
```
