# ML Skills

ML workflow skills for Treasure AI: customer segmentation, attribution, classification, recommendations, engagement scoring.

Each subfolder is a self-contained solution with its own `SKILL.md` entry point. The skill registry routes user requests directly to the matching solution — there is no router at this level.

| Folder | Solution | Status |
|--------|----------|--------|
| `rfm/` | RFM (Recency, Frequency, Monetary) customer segmentation | Ready |
| `mta/` | Multi-Touch Attribution (Markov, Shapley, journey analytics) | Ready |
| `classifier/` | Binary classification (lead scoring, churn, propensity) with SHAP explainability | Ready |
| `nba-scores/` | NBA — Next Best Channel / Time / Campaign engagement scores | Ready |
| `nbp/` | NBP — Next Best Product recommendations (Hivemall / PrecisionML) | Ready |

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
- `project_templates/` — the TD workflow template (read-only)
- `workflow-setup/references/` — config templates, requirements doc template, eval checks, deploy instructions
- `agent-skills/<insights-skill>/` — companion Claude skill for analyzing output tables and generating dashboards
- `prod-docs/references/` — content for the documentation set
