# MTA Production Runbook

Production architecture, output schema, and operational reference for the MTA Journey Analytics workflow.

## Workflow Overview

The MTA Journey Analytics workflow builds a unified customer journey from multiple touchpoint sources, sessionizes interactions, and runs attribution models to measure channel contribution to conversions.

- **TD Workflow project**: `mta_journey_agent` (or the custom name recorded in `project_state.md`)
- **Workflow source (customer working copy)**: `agent_outputs/<customer_slug>/mta/workflow/mta_journey_agent/` — copied from the bundled template `project_templates/mta_journey_agent/`
- **Config file**: `config/input_params.yml` inside the working copy

## Architecture

```
Source Tables (pageviews, email, sales, orders)
    ↓
Union & Standardize (src_union_table)
    ↓
Sessionize (session_length param)
    ↓
Backfill NULL channels (backfill_partition_col)
    ↓
Build Journeys (journeys_input_table)
    ↓
Attribution Models (Markov, Shapley, Linear, Time-Decay)
    ↓
Output Tables → Dashboard / Agent Analysis
```

## Output Tables

All written to `sink_database`:

| Table | Description |
|-------|-------------|
| `journey_src_union` | Unified touchpoint table from all sources |
| `journey_src_union_temp_converted` | Sessionized with conversion flags |
| `journey_src_union_final_converted` | Final journey table for attribution |
| `mta_journeys` | Per-customer journey sequences with conversion flags |
| `mta_models_standard` | Rule-based attribution (first/last touch, linear, time-decay) |
| `mta_markov_attribution_final` | Markov chain channel attribution |
| `mta_markov_transition_final` | Channel-to-channel transition probabilities |
| `mta_shapley_attribution_final` | Shapley value channel attribution |
| `mta_top_conversion_journeys` | Top-K distinct conversion paths |
| `mta_sankey_journeys` | Step-prefixed paths to conversion/churn (Sankey) |
| `marketing_channel_spends` | Channel spend data for ROI calculation (optional input) |

## Attribution Models

| Model | Description | Best For |
|-------|-------------|----------|
| Markov | Probability-based transition model | Understanding channel interdependencies |
| Shapley | Game-theory fair value distribution | Budget allocation across channels |
| Linear | Equal credit to all touchpoints | Baseline comparison |
| Time-Decay | More credit to recent touchpoints | Recency-weighted analysis |

## Configuration Reference

For workflow setup and configuration, see `../../workflow-setup/references/`:
- `workflow_setup_guide.md` — full setup walkthrough
- `yaml_structure.md` — complete parameter reference
- `table_configuration.md` — per-table-type setup guide
- `input_params_template.yml` — working example config
- `requirements_doc.md` — requirements gathering template

## Operational Runbook

### Running the Workflow
From inside the working copy `agent_outputs/<customer_slug>/mta/workflow/mta_journey_agent/`:
```bash
( cd "agent_outputs/<customer_slug>/mta/workflow/mta_journey_agent" && tdx wf push -y )
tdx wf run mta_journey_agent.mta_advanced_launch
tdx wf sessions mta_journey_agent --status running
```

### Monitoring
```bash
tdx wf timeline mta_journey_agent.mta_advanced_launch --follow
tdx wf attempt <id> tasks
tdx wf attempt <id> logs +failed_task
```

### Common Failure Points
- **Source table missing or renamed**: Verify `src_table` values in `input_params.yml`
- **No conversions found**: Check `conversion_flag` logic against actual data
- **Memory errors on large datasets**: Narrow time range or increase `top_k_channel_perc`
- **NULL channels dominate**: Improve UTM tagging or adjust `backfill_partition_col`

### Re-running After Config Change
1. Update `config/input_params.yml` in the working copy
2. `tdx wf push -y` from the working copy to deploy changes
3. `tdx wf run` to execute with new config
4. Verify output tables have expected row counts
