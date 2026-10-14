# Classification Workflow — Deployment Instructions

> **ALWAYS read `../../../shared/push_pattern_td_workflows.md` before proceeding.** It contains the mandatory deploy guidelines that apply to every ML solution — copying the bundled template into `agent_outputs/`, the project-name confirmation gate, and asking the user before triggering a workflow run. The Classifier-specific steps below extend those guidelines; they do not replace them.

## Template

The Classification workflow template ships with this skill at:

```
ml-skills/classifier/project_templates/classify/
```

It is read-only. Copy it into the engagement's working directory (see `../../../shared/local_outputs.md`):

```bash
dest="agent_outputs/<customer_slug>/classifier/workflow"
mkdir -p "$dest"
[ -d "$dest/classify" ] || cp -R "<classifier_skill_dir>/project_templates/classify" "$dest/"
```

`<classifier_skill_dir>` is the absolute path of the directory containing the classifier `SKILL.md`. All commands below run from inside the working copy `agent_outputs/<customer_slug>/classifier/workflow/classify/`.

## Directory Structure

```
classify/
├── config.yml          # Customer-specific configuration (YOU GENERATE THIS)
├── classify.dig        # Wrapper workflow
├── train.dig           # ENTRY POINT — training workflow
├── predict.dig         # ENTRY POINT — prediction workflow
├── data_prep.dig       # Shared feature engineering steps
├── queries/            # Supporting SQL (do not edit)
├── sql/                # Customer-specific feature SQL (you create this — referenced from train/predict/data_prep .dig)
├── python/             # Training / prediction pipeline (do not edit)
├── models.py, preprocessor.py, explainer.py, parallel_writer.py
└── README.md
```

## Configuration

Write the generated config to `config.yml` in the working copy (overwrite the template's example values).

See `workflow_setup_guide.md` for the full configuration walkthrough and `yaml_structure.md` for the parameter reference.
Use `input_params_template.yml` as the starting point.

## Deploy to Treasure Data

Once the user has confirmed both the `config.yml` and the project name (default: `classify`, the folder name):

### Push the workflow

```bash
( cd "agent_outputs/<customer_slug>/classifier/workflow/classify" && tdx wf push -y )
```

### Custom project name

```bash
( cd "agent_outputs/<customer_slug>/classifier/workflow/classify" && tdx wf upload <custom_project_name> )
```

## Set the Required Secret

Before the first run, set the `apikey` secret — the Python training/prediction pipeline needs a TD API key with read/write access to `sink_database`:

```bash
tdx wf secrets set <project_name> apikey=<TD_API_KEY>
```

Use a Master API Key in `ACCOUNT_ID/KEY` format (OAuth tokens cause 401 errors). Without this secret, `train.dig`/`predict.dig` fails immediately. Never handle the actual key value in chat — present this command with a placeholder and let the user supply the real key (e.g. by running it themselves with `! tdx wf secrets set …`).

## Run the Workflow

**ALWAYS ask the user first if they want to trigger the workflow run and validate output tables.** Only proceed after explicit confirmation.

```bash
# Run training
tdx wf run <project_name>.train

# Run prediction (after training succeeds)
tdx wf run <project_name>.predict
```

## Monitor Execution

```bash
# Check running sessions
tdx wf sessions <project_name> --status running

# Follow the execution timeline
tdx wf timeline <project_name>.train --follow

# Check attempt details
tdx wf attempt <attempt_id> tasks
tdx wf attempt <attempt_id> logs +<task_name>
```

## Re-deploy After Config Changes

1. Update `config.yml` in the working copy with the new configuration
2. From the working copy, push the updated workflow: `tdx wf push -y`
3. Run: `tdx wf run <project_name>.train`
4. Verify output tables have expected row counts and metrics

## Access Requirements

- TD CLI (`tdx`) installed and authenticated against the customer's TD instance
- Write permissions to the target `sink_database` in TD
