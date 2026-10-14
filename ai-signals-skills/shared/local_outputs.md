---
name: shared-local-outputs
description: |
  Where every engagement artifact is written: a local, git-ignored `agent_outputs/` folder in the user's working directory. Defines the folder layout, customer/solution slug rules, the mandatory git-ignore bootstrap, and what may / may not be stored there. Used by every solution under ai-signals-skills/.
---

# Shared: Local Outputs (`agent_outputs/`)

Every document, working copy, and generated file produced during an engagement is written to a local `agent_outputs/` folder in the **user's current working directory** — never into the plugin's own folders, and never to an external service. Customer-specific information (requirements answers, table names, configs, docs, dashboards) is allowed there because it stays on the user's machine or server.

## Rules

1. **Never write customer material inside the plugin.** `project_templates/` and `references/` are read-only templates. Copy them into `agent_outputs/` and edit the copy.
2. **Bootstrap the ignore rules before the first write** (Step 1 below). `agent_outputs/` must never be committable.
3. **One folder per customer + solution.** Everything for an engagement lives under `agent_outputs/<customer_slug>/<solution_slug>/`.
4. **Tell the user the path.** Whenever you create or update a file the user or customer needs to read or fill in, print its relative path.

## Step 1: Bootstrap (run once per working directory, before the first write)

```bash
mkdir -p agent_outputs
[ -f agent_outputs/.gitignore ] || printf '*\n' > agent_outputs/.gitignore
# If the working directory is inside a git repo, also ignore the folder at the repo level
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  root=$(git rev-parse --show-toplevel)
  grep -qxF 'agent_outputs/' "$root/.gitignore" 2>/dev/null || printf '\nagent_outputs/\n' >> "$root/.gitignore"
fi
git check-ignore -q agent_outputs/probe 2>/dev/null && echo "agent_outputs is git-ignored" || echo "not a git repo (agent_outputs/.gitignore still protects it)"
```

`agent_outputs/.gitignore` containing `*` makes the folder ignore itself, so its contents can't be committed even if the repo-level `.gitignore` is later changed or the folder is copied into another repo.

## Step 2: Derive the slugs

`<customer_slug>` — customer name lowercased, non-alphanumerics replaced by `-`, runs of `-` collapsed, leading/trailing `-` stripped:

| Customer name | `<customer_slug>` |
|---|---|
| `Test Customer Retail` | `test-customer-retail` |
| `ACME Corp.` | `acme-corp` |
| `Bob's Burgers (B2B)` | `bobs-burgers-b2b` |

If `agent_outputs/<customer_slug>/<solution_slug>/` already exists for a *different* engagement (same-named customer, re-engagement), ask the user whether to resume it or append `-2`, `-3`, … and record the chosen slug in `project_state.md`.

`<solution_slug>` — the calling solution's folder name: `rfm`, `mta`, `classifier`, `nba-scores`, `nbp`.

## Folder layout

```
agent_outputs/
├── .gitignore                         # "*"
└── <customer_slug>/
    └── <solution_slug>/
        ├── project_state.md           # cross-session context store — see project_state.md
        ├── requirements.md            # customer-fillable requirements doc — see requirements_doc_pattern.md
        ├── workflow/                  # working copy of project_templates/workflow_template/ — config edited, `tdx wf push` runs here
        ├── segments/                  # `tdx sg pull` working directory — see parent_segment_update.md
        ├── agent_build/<agent-name>/  # staging copy of project_templates/agent_template/ — see customer_agent_pattern.md
        ├── dashboards/                # generated HTML dashboards (customer agent)
        └── docs/                      # final documentation set — see customer_docs_pattern.md
```

Create sub-folders lazily, when the phase that needs them starts.

## Templates

Each solution ships two read-only templates in `<solution_dir>/project_templates/` (`<solution_dir>` = the folder containing the solution's `SKILL.md`; resolve it to an absolute path — the working directory is usually not the plugin directory):

| Template | Copied to | How |
|---|---|---|
| `workflow_template/` | `agent_outputs/<customer_slug>/<solution_slug>/workflow/` | `push_pattern_td_workflows.md` + the solution's `references/workflow-setup.md` |
| `agent_template/` | `.claude/skills/<agent-name>/` (via `agent_build/`) | `customer_agent_pattern.md` + the solution's `references/agent-setup.md` |

Never overwrite an existing working copy — it holds the customer's edits. To pick up a newer template version later, diff the template against the working copy and port the changes with the user's approval.

The customer agent is the one engagement artifact outside `agent_outputs/`: it must live in `.claude/skills/` to be loaded as a skill. It carries its own `.gitignore` (`*`) so it is never committable either.

## What may / may not be stored

Store:
- Edited workflow configs (`input_params.yml`, `params.yml`, `config.yml`), `tdx.json` with the customer's project name
- Requirements answers, project state, validation results, docs, dashboards

Never store:
- API keys or credentials — authentication lives in `tdx auth setup` / workflow secrets, never in files
- Raw data dumps from exploration queries — summarize findings in `project_state.md` or the docs instead
