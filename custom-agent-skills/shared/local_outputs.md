---
name: shared-local-outputs
description: |
  Where every engagement artifact is written: a local, git-ignored `agent_outputs/` folder in the user's working directory. Defines the folder layout, customer/solution slug rules, the mandatory git-ignore bootstrap, the template-copy rule, and what may / may not be stored there. Used by custom-audience-agent.
---

# Shared: Local Outputs (`agent_outputs/`)

Every document and generated file produced during an engagement is written to a local `agent_outputs/` folder in the **user's current working directory** — never into the plugin's own folders, and never to an external service. Customer-specific information (context files, schema notes, requirements answers, eval results, docs) is allowed there because it stays on the user's machine or server.

## Rules

1. **Never write customer material inside the plugin.** The skill's `references/` files are read-only templates. Copy them into `agent_outputs/` and edit the copy.
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

`<solution_slug>` — `custom-audience-agent`.

## Folder layout

```
agent_outputs/
├── .gitignore                         # "*"
└── <customer_slug>/
    └── custom-audience-agent/
        ├── project_state.md           # cross-session context store — see project_state.md
        ├── business-context.md        # customer copy of references/business-context.md (loaded every session)
        ├── data-dictionary.md         # customer copy of references/data-dictionary.md (loaded every session)
        ├── schema.json                # `tdx ps desc -o` snapshot of the parent segment
        ├── requirements.md            # customer-fillable review doc — see requirements_doc_pattern.md
        ├── segments/<ps-slug>/        # `tdx sg pull` working directory — segment YAML drafts
        ├── docs/                      # eval_results.md + documentation set — see customer_docs_pattern.md
        └── export/                    # standalone-skill export (Export mode)
```

Create sub-folders lazily, when the mode that needs them runs.

## Templates

The skill's `references/` files are generic templates. Copy them into the engagement folder and fill the copy — never edit the files inside the plugin:

```bash
dir="agent_outputs/<customer_slug>/custom-audience-agent"
mkdir -p "$dir"
for f in business-context.md data-dictionary.md; do
  [ -f "$dir/$f" ] || cp "<skill_dir>/references/$f" "$dir/"
done
```

`<skill_dir>` is the directory containing the skill's `SKILL.md` (resolve it to an absolute path — the user's working directory is usually not the plugin directory). Never overwrite an existing customer copy.

## What may / may not be stored

Store:
- Customer context files, schema snapshot, requirements answers, project state, segment YAML, eval results, docs, exports

Never store:
- API keys or credentials — authentication lives in `tdx auth setup`, never in files
- Raw customer records from exploration queries — keep only column names, value lists and aggregates
