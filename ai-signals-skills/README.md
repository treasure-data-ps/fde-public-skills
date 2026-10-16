# ML Skills

ML workflow skills for Treasure AI: customer segmentation, attribution, classification, recommendations, engagement scoring.

Each subfolder is a self-contained solution with its own `SKILL.md` entry point. The skill registry routes user requests directly to the matching solution — there is no router at this level.

| Folder | Solution | Status |
|--------|----------|--------|
| `rfm/` | RFM (Recency, Frequency, Monetary) customer segmentation | Ready |
| `mta/` | MTA — Multi-Touch Attribution (standard models + AI Signals Markov and Shapley) | Ready |
| `classifier/` | Binary classification (lead scoring, churn, propensity) with SHAP explainability | Ready |
| `nba-scores/` | NBA — Next Best Channel / Time / Campaign engagement scores | Ready |
| `nbp/` | NBP — Next Best Product recommendations (AI Signals NBP model) | Ready |

## Shared workflow pattern

Every ML solution follows the same 5 phases (defined in `shared/playbook.md`):
1. **Data exploration** — explore the customer's TD database via Trino SQL (`tdx-skills:tdx-basic`), identify source tables and key columns
2. **Requirements doc** — write a customer-fillable `requirements.md` to `agent_outputs/`
3. **Minimal push** — copy the bundled workflow template from `project_templates/` into `agent_outputs/`, generate the config, push with `tdx wf push`, run, validate
4. **Production config** — apply the customer's answers, re-push, re-validate
5. **Parent Segment + docs** — add score attributes and example audiences, write the documentation set to `agent_outputs/`

All outputs are written to the git-ignored `agent_outputs/<project_slug>/` folder in the user's working directory — see `shared/local_outputs.md`.

## Sub-folder convention

Each solution folder contains:
- `SKILL.md` — entry point, solution-specific context per phase
- `project_templates/workflow_template/` — the TD workflow template (read-only; `README.md` + `config/` are the source of truth)
- `project_templates/agent_template/` — the customer analysis agent blueprint (`SKILL.template.md` + `references/`)
- `references/` — workflow setup, requirements doc, agent setup, docs content, Parent Segment spec, and the AI Signals model guide (AI Signals solutions)

`rfm/`, `nba-scores/`, `nbp/` and `mta/` follow this layout (`shared/solution_standard.md`); `classifier/` is still being restructured.
