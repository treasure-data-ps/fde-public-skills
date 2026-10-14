# RFM Workflow — Deployment Instructions

> **ALWAYS read `../../../shared/push_pattern_td_workflows.md` before proceeding.** It contains the mandatory steps that apply to every ml-skills solution — copying the template into `agent_outputs/`, confirming the project name with the user, and asking the user before triggering a workflow run. The RFM-specific details below extend those steps; they do not replace them.

## Template and Working Copy

The RFM workflow template ships with this skill at `project_templates/rfm_agent/` (relative to the RFM solution folder). It is read-only. For each engagement, copy it into the local, git-ignored working directory (see `../../../shared/local_outputs.md`):

```bash
dest="agent_outputs/<customer_slug>/rfm/workflow"
mkdir -p "$dest"
[ -d "$dest/rfm_agent" ] || cp -R "<rfm_solution_dir>/project_templates/rfm_agent" "$dest/"
```

All commands below run from inside this working copy (`agent_outputs/<customer_slug>/rfm/workflow/rfm_agent/`).

## Directory Structure

```
rfm_agent/
├── config/
│   └── input_params.yml              # Customer-specific configuration (YOU GENERATE THIS)
├── body.txt                           # Error email notification template
├── queries/
│   ├── create_src_table_summary.sql   # Per-source table summary
│   ├── parse_table_params.sql         # Parses YAML aggregate_metrics_tables into queryable rows
│   ├── create_agg_input_table.sql     # Aggregates union table into rfm_input_table
│   ├── rfm_custom.sql                 # Quartile-based RFM scoring (model_type: 'custom')
│   ├── rfm_ln_sum_scoring.sql         # Log-based scoring (alternative)
│   ├── rfm_minmax_sum_scoring.sql     # Min-max scaling (alternative)
│   ├── rfm_stats_summary.sql          # Per-segment statistical summary
│   ├── rfm_stats_histogram.sql        # Histogram bin distributions
│   ├── stats_model_params.sql         # Per-source run metadata
│   ├── stats_global_session_filter.sql # Session ranking
│   ├── stats_historic_agg.sql         # Historical score aggregation
│   ├── union_activity/
│   │   ├── create_activity_union_agg.sql          # Union without time filter
│   │   ├── create_activity_union_time_interval.sql # Union with interval filter
│   │   └── create_activity_union_time_range.sql    # Union with range filter
│   └── union_src_tables/
│       └── insert_src_rable.sql       # Per-source insert into union table
├── rfm_launch.dig                     # ENTRY POINT — main workflow orchestrator
├── rfm_union_all_activity.dig         # Union all source tables
├── rfm_custom.dig                     # Run custom quartile scoring
├── rfm_automl.dig                     # Run PrecisionML notebook scoring
├── rfm_agg_stats.dig                  # Generate dashboard stats tables
```

## Workflow Execution Flow

```
rfm_launch.dig (entry point)
├── 1. Create sink database if not exists
├── 2. rfm_union_all_activity.dig (if built_union_activity: yes)
│   ├── Parse YAML params → rfm_input_params table
│   ├── Create empty union table
│   ├── Loop through each source table (parallel)
│   │   └── Insert per-profile aggregated rows into union table
│   └── Create rfm_input_table (aggregate across sources)
├── 3. rfm_${model_type}.dig
│   └── rfm_custom.dig → quartile scoring → rfm_output_table
│       OR rfm_automl.dig → PrecisionML notebook
├── 4. rfm_agg_stats.dig
│   ├── rfm_stats (per-segment summary)
│   ├── rfm_stats_histogram (score distributions)
│   ├── rfm_stats_model_params (per-source metadata)
│   ├── rfm_stats_global_session_filter (session ranking)
│   └── rfm_stats_daily_agg (historical scores)
```

## Configuration

Write the generated `input_params.yml` to `config/input_params.yml` in the working copy (overwriting the template's example values).

See `workflow_setup_guide.md` for the full configuration walkthrough and `yaml_structure.md` for the parameter reference.

## Deploy to Treasure Data

### Option 1: Default Project Name

Push using the folder name (`rfm_agent`) as the project name, from inside the working copy:

```bash
( cd "agent_outputs/<customer_slug>/rfm/workflow/rfm_agent" && tdx wf push -y )
```

### Option 2: Custom Project Name

Push under a custom workflow project name, from inside the working copy:

```bash
( cd "agent_outputs/<customer_slug>/rfm/workflow/rfm_agent" && tdx wf upload <custom_project_name> )
```

## Run the Workflow

**ALWAYS ask the customer first if they want to trigger the workflow run and validate output tables.** Only proceed after explicit confirmation.

```bash
tdx wf run <workflow_project_name>.rfm_launch
```

## Monitor Execution

```bash
# Check running sessions
tdx wf sessions <workflow_project_name> --status running

# Follow the execution timeline
tdx wf timeline <workflow_project_name>.rfm_launch --follow

# Check attempt details
tdx wf attempt <attempt_id> tasks
tdx wf attempt <attempt_id> logs +<task_name>
```

## Re-deploy After Config Changes

1. Update `config/input_params.yml` in the working copy with the new configuration
2. Push the updated workflow from the working copy: `tdx wf push -y` (or `tdx wf upload <custom_project_name>`)
3. Run: `tdx wf run <workflow_project_name>.rfm_launch`
4. Verify output tables have expected row counts

## Access Requirements

- TD CLI (`tdx`) installed and authenticated against the customer's TD instance
- Write permissions to the target `sink_database` in TD
