# FDE Skills

Templatized skill library for deploying ML solutions and custom AI agents on Treasure AI with Claude. Everything a skill needs ships inside the plugin, and everything it produces stays on your machine.

## How routing works

Each solution folder (e.g. `ai-signals-skills/mta/`, `custom-agent-skills/custom-audience-agent/`) contains a `SKILL.md` whose YAML frontmatter `description` is what the skill registry uses to match user requests. The registry compares the user's prompt against every registered skill's description and loads the matching one directly. Shared pattern files (`*/shared/`) are not registered as skills; solution skills read them by path.

```
fde-public-skills/
├── README.md                          ← you are here (human docs)
├── .claude-plugin/marketplace.json    ← registers skills with the loader
│
├── ai-signals-skills/
│   ├── README.md                      ← category overview
│   ├── shared/                        ← generic phase flow + patterns (local outputs, deploy, requirements, docs)
│   ├── rfm/         SKILL.md + project_templates/, workflow-setup/, agent-skills/, prod-docs/
│   ├── mta/         SKILL.md + project_templates/, workflow-setup/, agent-skills/, prod-docs/
│   ├── classifier/  SKILL.md + project_templates/, workflow-setup/, agent-skills/, prod-docs/
│   ├── nba-scores/  SKILL.md + project_templates/, workflow-setup/, agent-skills/, prod-docs/
│   └── nbp/         SKILL.md + project_templates/, workflow-setup/, agent-skills/, prod-docs/
│
└── custom-agent-skills/
    ├── shared/                    ← local outputs, project state, requirements doc, docs set
    ├── custom-audience-agent/     SKILL.md + references/ (business-context, data-dictionary, eval templates)
    └── custom-dashboard-builder/  SKILL.md + phase-1/ … phase-5/, references/ (questionnaire-led HTML dashboard builder)
```

### Custom agent skills

| Skill | Folder | Use it when the user wants to… |
|---|---|---|
| `custom-audience-agent` | `custom-agent-skills/custom-audience-agent/` | analyze a CDP parent segment (attributes, behaviors, existing segments) and draft child segments |
| `fde-tais-custom-dashboard-builder` | `custom-agent-skills/custom-dashboard-builder/` | build or resume a custom HTML dashboard from Treasure Data tables, SQL, or a Sisense `.dash` file, following a 5-phase questionnaire-led pipeline |

## Where outputs go: `agent_outputs/`

Skills never write customer material into the plugin folders or to external services. Every engagement artifact — requirements doc, project state, the customized workflow copy, validation results, documentation, dashboards — is written to `agent_outputs/<customer_slug>/<solution_slug>/` in **your current working directory**.

- `agent_outputs/` is git-ignored twice: the skills create `agent_outputs/.gitignore` (containing `*`) on first use, and add `agent_outputs/` to the enclosing repo's `.gitignore` if there is one. Customer-specific information can't be committed by accident.
- Templates (`project_templates/` for ML workflows, `references/` for the audience agent) are read-only. A skill copies them into `agent_outputs/` and edits the copy; `tdx wf push` runs from the workflow copy.
- Resume an engagement in a new session by asking the skill to continue; it reads `agent_outputs/<customer_slug>/<solution_slug>/project_state.md` first.

See `ai-signals-skills/shared/local_outputs.md` for the full layout.

## Adding a new skill

**ML solutions must follow `ai-signals-skills/shared/solution_standard.md`** — the required folder layout, `SKILL.md` section order, the 5-phase contract (what each phase must / must not do), the allowed exceptions, and a conformance checklist. Run through its checklist before opening a PR. `nba-scores/` is the reference implementation.

1. Create a folder under `ai-signals-skills/` or `custom-agent-skills/`.
2. Add a `SKILL.md` with YAML frontmatter:
   - `name` — must be globally unique; prefix with `fde-` (e.g. `fde-cltv`).
   - `description` — concrete trigger phrases the registry will match against.
3. Put the deployable template under `project_templates/` and supporting material in `workflow-setup/references/`, `prod-docs/references/`, etc.
4. Write all engagement outputs to `agent_outputs/` per `ai-signals-skills/shared/local_outputs.md`.
5. Add the new skill path to `.claude-plugin/marketplace.json` (only folders that contain a `SKILL.md`).

## Repeating folder template (ML solutions)

```
<solution>/
├── SKILL.md
├── project_templates/
│   └── <wf_dir>/        # TD workflow template — read-only, copied into agent_outputs/
├── workflow-setup/
│   └── references/      # config templates, requirements doc template, eval checks, deploy instructions
├── agent-skills/
│   └── <insights-skill>/  # Claude skill for analyzing outputs + generating dashboards
└── prod-docs/
    └── references/      # content for the documentation set
```
