# FDE Public Skills

Skills for Treasure AI Studio that set up AI Signals models and custom AI agents on your own Treasure Data account — step by step, inside a Work Folder. Built by the Treasure AI Forward Deployed Engineering team.

## How it works

1. **Add the marketplace** `fde-public-skills` in Treasure AI Studio and enable the plugins you need.
2. **Start a setup in a Work Folder** — e.g. *"Set up RFM segmentation"*, *"Build a custom sales dashboard"*. The matching **setup skill** shows the plan and walks through it phase by phase, asking only what it can't learn from your data.
3. **It copies its templates into the Work Folder** and customizes the copies: a Treasure Data workflow (AI Signals solutions, or a dashboard workflow when needed) and an agent template.
4. **It installs your project's own agent** as a skill in `.claude/skills/<project>-agent/` (or `<project>-dashboard/`). That agent answers questions about your results in any chat in the folder, and can be shared with your team (Studio: Develop → Share).

Setup skills are the same for everyone and update with the marketplace; your project agent and files are yours. Ask a setup skill to resume, change or rebuild; ask your project agent about results.

## Skills

### `ai-signals-skills`

| Skill | Sets up | Project agent |
|---|---|---|
| `fde-rfm` | RFM segmentation — ten customer segments from recency, frequency and monetary value | `rfm-agent` |
| `fde-nbp` | Next Best Product — top product and category recommendations per customer | `nbp-agent` |
| `fde-mta` | Multi-Touch Attribution — channel contribution with Markov, Shapley and standard models | `mta-agent` |
| `fde-nba-scores` | Next Best Action — best time, channel and campaign per customer, engagement flags | `nba-scores-agent` |
| `fde-classifier` | Propensity scoring — any yes/no outcome (lead scoring, churn, conversion, response) | `classifier-agent` |

Five phases: data exploration → requirements doc → first workflow run → hands-on testing with the agent and dashboard (DEV) → Parent Segment attributes, docs and final agent (PROD, when you say the model is ready).

### `custom-agent-skills`

| Skill | Sets up | Project agent |
|---|---|---|
| `fde-custom-audience-agent` | An audience and segment-analysis agent on one parent segment, evaluated with ten test prompts | `audience-agent` |
| `fde-custom-dashboard-builder` | A custom HTML dashboard (new, or from a `.dash` export, HTML file or screenshot), with a workflow only when the data needs one | `<project>-dashboard` |

Agent names get a project prefix when you choose one (e.g. `loyalty-rfm-agent`), so several people can build their own side by side.

## Your files

Everything is written to your Work Folder — never to the plugin or an external service:

```
<Work Folder>/
├── agent_outputs/<project>/      # git-ignored: project_state.md (resume point), business context,
│                                 # requirements, workflow copy, dashboards, eval results, docs
└── .claude/skills/<agent-name>/  # your project agent (own .gitignore)
```

`project_state.md` records what was built and what comes next — in a new chat, ask the setup skill to continue. For Treasure AI Studio itself (Work Folders, sharing, permissions) see https://docs.treasure.ai/products/ai-studio/overview.

## For maintainers

| Path | Contents |
|---|---|
| `.claude-plugin/marketplace.json` | Marketplace and plugin registration (one entry per setup skill) |
| `ai-signals-skills/shared/` | AI Signals playbook (phase flow), solution standard, shared patterns |
| `custom-agent-skills/shared/` | Custom-agent playbook, solution standard, agent build and eval patterns |
| `<plugin>/<solution>/` | `SKILL.md` (setup flow), `references/`, `project_templates/` (workflow, dashboard and agent templates — copied, never edited in place) |

New solutions follow the solution standard of their plugin (`*/shared/solution_standard.md`): `name: fde-<solution folder name>`, a setup-only `description`, templates under `project_templates/`, all outputs under `agent_outputs/<project_slug>/`, and an entry in `marketplace.json`.
