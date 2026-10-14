# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Treasure Data (TD) Workflow project for Multi-Touch Attribution (MTA) analysis. It processes web activity, email events, sales interactions, and order data to generate marketing attribution models and journey analytics. The workflow is built on Treasure Workflow (Digdag), uses Trino/Hive SQL for data processing, and Python for advanced ML models (Markov chains, Shapley values).

## Workflow Execution

### Running the Workflow

The main entry point is `mta_advanced_launch.dig`. It orchestrates the entire pipeline:

```bash
# Test locally with dry-run
tdx wf run mta_advanced_launch.dig --dry-run

# Run locally
tdx wf run mta_advanced_launch.dig

# Push to TD server and run
tdx wf push mta_journey_agent
tdx wf start mta_journey_agent
```

### Workflow Components

The main workflow calls sub-workflows in sequence:
1. **mta_union_src_tables.dig** - Unions multiple data sources (pageviews, emails, sales interactions, orders) into a single journey table
2. **mta_journeys_and_models.dig** - Creates journey sessions and standard MTA models (First Touch, Last Touch, Linear, U-Shaped)
3. **mta_markov_shapely.dig** - Runs advanced ML attribution models (Markov chains, Shapley values)

### Monitoring and Debugging

```bash
# List recent workflow sessions
tdx wf sessions mta_journey_agent

# Check session status
tdx wf session <session_id>

# View logs for a specific attempt
tdx wf logs <attempt_id>

# Retry failed session
tdx wf retry <attempt_id>
```

## Configuration Architecture

The workflow is highly parameterized. **Configuration drives all data processing logic** - modify YAML/JSON configs instead of SQL when possible.

### config/global.yml

Controls global parameters across all workflows:
- **sink_database**: Output database for all tables
- **unique_user_id**: Primary join key (e.g., canonical_id, td_canonical_id)
- **time filtering**: Uses either `interval` (td_interval with lookback_period like `-180d`) or `range` (fixed start/end dates)
- **session_length**: Session timeout in seconds (default: 3600 = 60 min)
- **aggregate_metrics_tables**: Array defining each source table with column mappings
  - Each source specifies: table name, time column, URL column, UTM parsing logic, custom filters, conversion flags
  - Supports both standard YAML-driven queries and custom SQL (when `query_type: 'custom'`)

### config/mta_params.yml

Controls MTA model parameters:
- **u_shaped**: Attribution weights for first/last touch (default: 0.35 each, 0.30 distributed to middle touches)
- **shapely_lookback_window**: Number of touchpoints to consider in Shapley model (default: 5)
- **output_tables**: Names for all generated tables (journeys, models, aggregated stats)

### config.json

Controls data model creation via Python scripts (for Treasure Insights dashboards):
- **model_name**: Name of the Insights data model
- **model_tables**: Array of `{db, name}` objects to include in model
- **shared_user_list**: Users to share the data model with
- **change_schema_cols**: Column type transformations for the model (e.g., convert strings to dates)
- **join_relations**: Defines relationships between tables for cross-filtering

## SQL Architecture

### SQL Organization

- **sql/parse_table_params.sql**: Converts YAML config into a queryable table for dynamic SQL generation
- **sql/union_src_tables/**: Scripts for merging multiple data sources
  - `insert_src_table.sql`: Standard YAML-driven table insertion
  - `order_events.sql`: Custom query example (when `query_type: 'custom'`)
  - `sessionize_temp_table.sql`: Creates session IDs using td_sessionize
  - `split_converted_journeys.sql`: Separates converted vs non-converted journeys
- **sql/journeys_models/**: Journey aggregation and standard MTA models
  - `mta_journey_sessions.sql`: Core journey table with session stats
  - `mta_models_union*.sql`: First Touch, Last Touch, Linear, U-Shaped attribution
- **sql/ml_models/**: Advanced ML attribution models
  - `mta_journey_agg.sql`: Prepares data for Markov chains
  - `mta_shapely_input_table.sql`: Prepares data for Shapley values

### TD-Specific SQL Patterns

- **Time filtering**: Use `td_interval` for dynamic lookback (e.g., `TD_INTERVAL(time, '-180d/-1d', 'JST')`)
- **Sessionization**: Use `td_sessionize(time, ${session_length}, ${unique_user_id})` for session IDs
- **UTM parsing**: `url_extract_parameter(LOWER(td_url), 'utm_medium')`
- **Dynamic queries**: Use `td_for_each>` to loop through config tables and generate parallel tasks

## Python Components

### python/mta_lib.py

Entry point for Python tasks. Installs `td-ml-mta` package and imports Markov/Shapley functions. Reads environment variables set by Digdag:
- `TD_API_KEY`, `TD_API_SERVER`: Authentication
- `SINK_DB`: Output database
- Table and column names for the ML models

### python/markov.py & python/shapley.py

Contain the actual ML model implementations. These use the `td-ml-mta` library to:
- **Markov chains**: Calculate removal effect (how much each channel impacts conversions)
- **Shapley values**: Calculate fair credit distribution using game theory

Python tasks run in Docker containers (`digdag/digdag-python:3.9`) via the `py>` operator.

## Data Flow

1. **Source tables** (pageviews, emails, sales interactions, orders) →
2. **Union table** (`journey_src_union_final`) with sessionization and UTM parsing →
3. **Converted/Non-converted splits** (`journey_src_union_final_converted`, `*_nonconv`) →
4. **Journey stats table** (`mta_journeys`) with session/journey aggregations →
5. **Standard MTA models** (`mta_models_standard`) with First/Last/Linear/U-Shaped attribution →
6. **ML models** (`mta_markov_attribution_final`, `mta_shapley_attribution_final`) via Python

## Key Workflow Patterns

### Parallel Execution

```yaml
+task_name:
  _parallel: true
  # All child tasks run concurrently
```

Used extensively for processing multiple source tables simultaneously.

### Conditional Logic

```yaml
+check_if_exclude_channels:
  if>: ${include_non_converted_channels=='yes'}
  _do:
    # Execute this branch
  _else_do:
    # Execute alternative branch
```

### Dynamic Looping

```yaml
td_for_each>: sql/parse_table_params.sql  # Query returns rows
_do:
  # Each row becomes ${td.each.column_name}
```

Used to iterate through source tables defined in YAML config.

### Table Management

```yaml
td_ddl>:
  empty_tables: ["table1", "table2"]  # Create empty tables
  drop_tables: ["temp_table"]          # Drop tables
  rename_tables: [{from: "old", to: "new"}]  # Rename
```

## Adding New Data Sources

To add a new data source (e.g., SMS events, ad impressions):

1. Add configuration to `config/global.yml` under `aggregate_metrics_tables`:
   ```yaml
   - src_table: database.table_name
     name: 'descriptive_name'
     unixtime_col: time
     # ... map all required columns
     custom_filter: "WHERE clause for this source"
     conversion_flag: "CASE WHEN ... THEN 1.0 ELSE 0.0 END"
   ```

2. If YAML mapping is insufficient, set `query_type: 'custom'` and create `sql/union_src_tables/{name}.sql`

3. The workflow will automatically include it in the union table via the `td_for_each>` loop

## Output Tables

All tables are created in `${sink_database}` (defined in config/global.yml):

- **journey_src_union_final**: Unified, sessionized journey data (all users)
- **journey_src_union_final_converted**: Only converted journeys
- **mta_journeys**: Aggregated journey statistics for dashboards
- **mta_models_standard**: Standard MTA model results (First/Last/Linear/U-Shaped)
- **mta_agg_pageview_stats**: Aggregated web activity stats
- **mta_markov_attribution_final**: Markov chain attribution results
- **mta_shapley_attribution_final**: Shapley value attribution results
- **mta_table_params**: Parsed YAML config as a table (for debugging)

## Dashboard Integration

The workflow can automatically create/update Treasure Insights data models via Python scripts (currently commented out in workflows). The `config.json` defines model structure, table joins, and sharing permissions.
