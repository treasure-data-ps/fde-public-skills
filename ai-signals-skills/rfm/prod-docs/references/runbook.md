# RFM Production Runbook

Production architecture, output schema, and operational reference for the RFM Customer Segmentation workflow.

## Workflow Overview

The RFM Customer Segmentation workflow unions customer behavioral data from multiple sources, computes per-profile Recency, Frequency, and Monetary values, assigns quartile scores (1-4), and segments customers into actionable groups.

- **TD Workflow Project**: `rfm_agent` (or the custom name recorded in `project_state.md`)
- **Workflow Source (working copy)**: `agent_outputs/<customer_slug>/rfm/workflow/rfm_agent/` — copied from the skill's bundled `project_templates/rfm_agent/`; edit config here and re-push with `tdx wf push -y`
- **Entry Point**: `rfm_launch.dig`

## Architecture

```
Source Tables (pageviews, email, sales, orders, support)
    ↓
Parse YAML Params → rfm_input_params
    ↓
Union & Aggregate per profile per source (rfm_combined_user_events)
    ↓
Aggregate across sources (rfm_input_table: recency, frequency, monetary_value)
    ↓
Quartile Scoring (25th/50th/75th percentile boundaries)
    ↓
Segment Assignment (R/F/M quartile combinations)
    ↓
rfm_output_table (r_quartile, f_quartile, m_quartile, rfm_quartile, rfm_score, rfm_segment)
    ↓
Dashboard Stats (rfm_stats, rfm_stats_histogram, rfm_stats_model_params)
    ↓
TI Datamodel (if create_dashboard: yes)
```

## Workflow Execution Flow

```
rfm_launch.dig
├── Create sink database
├── rfm_union_all_activity.dig (if built_union_activity: yes)
│   ├── parse_table_params.sql → rfm_input_params
│   ├── Create empty union table
│   ├── Loop sources (parallel) → insert_src_rable.sql into union table
│   └── create_agg_input_table.sql → rfm_input_table
├── rfm_${model_type}.dig
│   └── rfm_custom.sql → rfm_output_table (quartile scores + segments)
├── rfm_agg_stats.dig
│   ├── rfm_stats_summary.sql → rfm_stats
│   ├── rfm_stats_histogram.sql → rfm_stats_histogram
│   ├── stats_model_params.sql → rfm_stats_model_params
│   ├── stats_global_session_filter.sql → rfm_stats_global_session_filter
│   └── stats_historic_agg.sql → rfm_stats_daily_agg
└── rfm_datamodel_create.dig + rfm_datamodel_build.dig (if create_dashboard: yes)
```

## Output Tables

All written to `sink_database`:

| Table | Description |
|-------|-------------|
| `rfm_input_params` | Parsed YAML configuration with computed WHERE clauses |
| `rfm_combined_user_events` | Per-profile per-source aggregated activity (time, touchpoints, spend, recency_days) |
| `rfm_input_table` | Aggregated across sources: recency, frequency, monetary_value per profile |
| `rfm_output_table` | Final per-profile quartile scores (r/f/m_quartile), rfm_quartile label, rfm_score, rfm_segment |
| `rfm_stats` | Per-segment statistical summary (size, percentiles, correlations, date ranges) |
| `rfm_stats_histogram` | Histogram distributions per metric per segment |
| `rfm_stats_model_params` | Per-source run metadata (touchpoints, spend, date ranges) |
| `rfm_stats_global_session_filter` | Session ranking for multi-run tracking |
| `rfm_stats_daily_agg` | Historical segment scores (when `store_historic_scores: yes`) |

## Scoring (model_type: 'custom')

Uses quartile-based scoring from `rfm_custom.sql`:

| Dimension | Scoring Logic | Scale |
|-----------|--------------|-------|
| Recency (r_quartile) | Lower recency_days → higher score (reverse) | 1-4 |
| Frequency (f_quartile) | Higher touchpoints → higher score | 1-4 |
| Monetary (m_quartile) | Higher spend → higher score | 1-4 |

Percentile boundaries: 25th, 50th, 75th. Monetary percentiles exclude values <= 0.05.

Combined: `rfm_quartile` = `R<r>F<f>M<m>` (e.g., `R4F3M2`), `rfm_score` = avg of three quartiles.

## Segment Definitions

| Segment | R | F | M | Description |
|---------|---|---|---|-------------|
| Champions | 4 | 4 | 4 | Top customers |
| Loyal Customers | 3+ | 3+ | 3+ | Very active and valuable |
| Potential Loyalists | 3+ | 2-3 | 2-3 | Room to grow |
| Promising | 3+ | 2+ | 2+ | Some above-average spend |
| New Customers | 3+ | low | low | Recently engaged, low history |
| Cannot lose them | 2 | any | 3+ | High spenders at risk of churn |
| Need attention | 2 | 2+ | 2 | Active but declining |
| Hibernating | 2 | low | low | Below average across the board |
| High Value Sleeping | 1 | any | 3+ | Past loyalists, stopped engaging |
| Lost customers | 1 | low | low | Lowest priority |

## Configuration Reference

For workflow setup and configuration, see `../../workflow-setup/references/`:
- `workflow_setup_guide.md` — full setup walkthrough
- `yaml_structure.md` — complete parameter reference
- `table_configuration.md` — per-table-type setup guide
- `input_params_template.yml` — working example config
- `requirements_doc.md` — requirements gathering template

## Operational Runbook

### Running the Workflow
```bash
( cd "agent_outputs/<customer_slug>/rfm/workflow/rfm_agent" && tdx wf push -y )
tdx wf run
tdx wf sessions --status running
```

### Monitoring
```bash
tdx wf timeline --follow
tdx wf attempt <id> tasks
tdx wf attempt <id> logs +<failed_task>
```

### Common Failure Points
- **Source table missing or renamed**: Verify `src_table` values in `input_params.yml`
- **Column not found**: Check that `unixtime_col`, `join_key`, and `order_amount` column names are correct
- **No data after filtering**: Custom filters may be too restrictive — test filter queries manually
- **All M quartiles equal**: Verify that at least one table has a real `order_amount` column (not `0.0`)
- **Memory errors on large datasets**: Enable `apply_time_filter` to narrow the data window
- **Dashboard creation fails**: Check that the `td.apikey` workflow secret is set — the user runs `! tdx wf secrets set <project> td.apikey=<TD_API_KEY>` themselves so the key never appears in chat

### Re-running After Config Change
1. Update `config/input_params.yml`
2. `tdx wf push -y` to deploy changes
3. `tdx wf run` to execute with new config
4. Verify output tables have expected row counts

### Output Validation
```sql
-- Check total profiles scored
SELECT COUNT(DISTINCT <canonical_id>) FROM rfm_output_table;

-- Check segment distribution
SELECT rfm_segment, COUNT(*) as cnt
FROM rfm_output_table
GROUP BY rfm_segment
ORDER BY cnt DESC;

-- Check quartile distributions
SELECT r_quartile, COUNT(*) as cnt
FROM rfm_output_table
GROUP BY r_quartile
ORDER BY r_quartile;

-- Check per-source contributions
SELECT source, COUNT(*) as profiles, SUM(total_touchpoints) as events
FROM rfm_combined_user_events
GROUP BY source
ORDER BY events DESC;

-- Verify stats table (latest run)
SELECT * FROM rfm_stats
WHERE session_id = (SELECT MAX(session_id) FROM rfm_stats);
```

### Archiving
When `archive_results: yes`, the workflow backs up previous output tables before writing new results. This allows comparison between runs and rollback if needed.

### Historical Scores
When `store_historic_scores: yes`, each run appends scores with a timestamp to `rfm_stats_daily_agg`, enabling trend analysis of customer segment migrations over time.
