## General Overview:
This solution is meant to help Marketing Teams and Analysts extract and visualize important Campaign KPIs and Multi-Touch Attribution Models from ***web activity and customer transactions*** data in CDP. The Behavioral data can be filtered by time and pre-aggregated using ***Presto/Hive*** functions and ***DigDag*** to ensure `maximum compute efficiency` and `scalability on Big Data Volume`. The outputs of the wf enable some of the helpful insights below:

- Total Revenue, Conversions, Pageviews, Unique Visitors

- AVG Journey Length and Session Time for `Converted` vs. `Non-Converted` Journeys

- Distribution of User visits by: `Marketing Channel, Campaign, Country, Device` and others

- Daily/Weekly/Monthly trends of important activity such as: `pageviews, purchases, revenue` etc.

- Four MTA Models to compare by `channel, medium, and campaign` - ***First Touch, Last Touch, Linear, U-Shaped***

- Any additional useful KPIs such as: `visits by referral domain`, `revenue by Product Name`, etc.


### Requirements:
Requires understanding of Presto/Hive, DigDag, Python Custom Scripting and Treasure Insights. 

### Tech Implementation Summary:

The workflow is set-up, so that the end user only needs to configure the `.yml` files in the `config\` folder and the `config.json` file in main project folder and the wf can be ran and execute all tasks. Details on how to configure each `yml or config` file below:

### Workflow Structure (.dig files):

The project consists of multiple DigDag workflow files that orchestrate the MTA pipeline:

- **mta_advanced_launch.dig** - Main orchestrator workflow that serves as the entry point. Creates the sink database and calls the sub-workflows in sequence. Can be scheduled to run daily and includes error notification setup.

- **mta_union_src_tables.dig** - Source data preprocessing and union workflow. Key processes:
  - Parses YAML config into queryable table (`mta_table_params`)
  - Loops through all source tables (pageviews, emails, sales interactions, orders) in parallel
  - Applies UTM parsing logic to extract channel, source, campaign from URLs
  - Creates sessionized union table using `td_sessionize` function
  - Splits data into converted vs non-converted user journeys
  - Optionally enriches with customer attributes from RFM/customer tables
  - Generates summary statistics and sample tables for data validation

- **mta_journeys_and_models.dig** - Journey aggregation and standard MTA models workflow. Key processes:
  - Creates journey sessions table with conversion metrics
  - Aggregates journey statistics by configurable dimensions (channel, event_context, etc.)
  - Generates standard MTA attribution models: **First Touch, Last Touch, Linear, U-Shaped**
  - Conditionally includes/excludes non-converted channels based on config
  - Creates conversion journey stats and Sankey diagram data tables

- **mta_markov_shapely.dig** - Advanced ML attribution models workflow. Key processes:
  - Prepares aggregated journey data for ML model input
  - Runs **Markov Chain** attribution model via Python (calculates removal effect for each channel)
  - Creates transition matrices showing customer journey flow between channels
  - Runs **Shapley Value** attribution model via Python (game theory-based fair credit distribution)
  - Generates attribution percentage tables for both ML models
  - Both models execute in parallel using Docker containers with Python 3.9

###### config/global.yml:
Controls important parameters which are often applied globally across most of the data sources and processes in the workflow.
```YML
#####################################################################
########################## GLOBAL PARAMS ############################
#####################################################################
sink_database: <sink_database> (database where all model output tables will be saved)
unique_user_id: canonical_id (main join key used to join behavior tables to customer tables)
api_endpoint: 'api.treasuredata.com' (API endpoint for the TD account where customer data lives)
cleanup_temp_tables: 'no' ('yes' will DELETE all temp tables not used by final dashboard)
include_non_converted_channels: yes (include/exclude touchpoints with no conversions from final MTA models)

######################## CUSTOMER ANALYSIS ENRICHMENT ############################
add_customer_analysis: 'yes' ('yes' will join customer table to journey table and add customer labels)
customers_table: <source_database>.rfm_output_table (full table name for customer table to join)
attributes_list: 'recency, frequency, monetary_value, rfm_segment' (customer attributes to add to journey)

#####################################################################
######################## FILTER PARAMS ##############################
#####################################################################
time_filter_type: interval (Use 'range' for fixed dates OR 'interval' for lookback from end date)
time_range_start_date: 2022-01-01 (start date for TD_TIME_RANGE, format YYYY-MM-DD)
time_range_end_date: 2222-22-22 (use '2222-22-22' to always use latest date, or set custom YYYY-MM-DD)
lookback_period: -180d (-1M = 1 month, -30d = 30 days, -2w = 2 weeks; used with TD_INTERVAL)
session_length: 3600 (in seconds, 3600s = 60min; inactivity time before new session starts)
backfill_partition_col: ${unique_user_id} (backfill NULL touchpoints by 'unique_user_id' or 'session_id')
top_k_channel_perc: 0.01 (use top K channels by COUNT(), change others to 'other')
top_k_conv_perc: 0.01 (use top K channels by SUM(conversions), change others to 'other')
top_k_journeys: 50 (top K distinct touchpoint patterns for converted/non-converted journeys)
sample_tpoint_limit: 25 (max journey length for sample tables)
journey_steps_lookback: 20 (takes first and last-n touchpoints from each journey)
agg_analysis_cols: ["event_context", "channel"] (dimensions for journey aggregation)
summary_table_top_k: 20 (top K distinct values to include in summary JSON stats)

#####################################################################
############# TABLE INPUT PARAMS FOR UNION TABLE ####################
#####################################################################
aggregate_metrics_tables: (array of source tables to union)
  - src_table: <source_database>.enriched_pageviews (full table name)
    table_description: 'Web Activity data streamed from JS SDK'
    name: pageviews (alias for this source)
    unixtime_col: time (UNIXTIME timestamp column name)
    url_col: td_url (URL column name)
    referral_col: td_referrer (referrer column name)
    medium_col: "COALESCE(...)" (SQL expression to extract utm_medium)
    source_col: "COALESCE(...)" (SQL expression to extract utm_source)
    campaign_col: "COALESCE(...)" (SQL expression to extract utm_campaign)
    utm_mailing_col: "COALESCE(...)" (SQL expression to extract utm_mailing)
    context_col: td_title (event context column)
    event_type: "'web activity'" (event type label)
    custom_filter: "WHERE clause" (custom SQL filter for this source)
    conversion_flag: "IF(...)" (SQL expression: 1.0 for conversion, 0.0 otherwise)
    item_price: 1.0 (revenue/price value)
    apply_time_filter: false (whether to apply time filtering)
    query_type: (leave blank for YAML-driven, use 'custom' for custom SQL file)

  # Additional sources: enriched_email_events, enriched_sales_rep_interactions, enriched_orders
  # (see config/global.yml for full configuration of all sources)

####### OUTPUT PARAMS
src_union_table: journey_src_union (name of the unified source table)
journeys_input_table: ${src_union_table}_final_converted (final converted journeys table)
  ```


###### config/mta_params.yml:
Controls important parameters for MTA model calculations and output table configurations.
```YML
####################### MTA STANDARD MODELS LOGIC ##################################
u_shaped: (U-Shaped attribution model parameters)
  first_touch_att: 0.35 (credit given to first touch, default 35%)
  last_touch_att: 0.35 (credit given to last touch, default 35%; remaining 30% distributed to middle touches)

####################### MTA ML ADVANCED MODELS LOGIC ##################################
shapely_lookback_window: 5 (number of touchpoints to consider in Shapley model)
ml_models_records_limit: 750000 (max records to process in ML models for performance)
removal_effect_limit: 0.005 (minimum removal effect threshold for Markov model)

####################### OUTPUT TABLES ####################################
output_tables: (output table names for all MTA results)
  database: <sink_database> (database where output tables are saved)
  journeys_table: mta_journeys (journey statistics table)
  models_table: mta_models_standard (standard MTA models table)
  agg_pageviews_table: mta_agg_pageview_stats (aggregated pageview stats table)
  agg_journey_markov_table: mta_journey_agg_markov (aggregated journey data for Markov model)
  shapely_input_table: mta_shapely_input_table (input table for Shapley model)
  ```

### Table Outputs:

- **mta_pageviews_conversion_events** - The raw output table with unified `web_activity` and `transacttions` tables data and parsed `conversion events`. It is used as intermediate table to pre-aggregate KPIs for Web Analytics and MTA Models, but is not sent to final datamodel.

- **mta_journeys** - table with Conversion Journey and Session KPIS parsed from the raw `mta_pageviews_conversion_events` table and aggregated into a dense format for Datamodel build.

- **mta_journeys_agg_stats** - Journey statistics aggregated by configurable dimensions (channel, event_context, etc.) from the config. Provides detailed breakdowns of journey behavior for dashboard analysis and comparative metrics.

- **mta_models_standard** - table with MTA Model KPIs, parsed from the raw `mta_pageviews_conversion_events` table and aggregated into a dense format for Datamodel build.

- **mta_agg_pageview_stats** - table with web_activity KPIs and stats, parsed from the raw `mta_web_activity_union` table and aggregated into a dense format for Datamodel build.

- **mta_markov_attribution** - Markov chain attribution results showing the removal effect of each channel. Uses game theory to calculate how much each channel contributes to conversions by measuring impact when removed from the journey.

- **mta_markov_transition_final** - Markov transition matrices showing customer journey flow probabilities between channels. Critical for understanding common path patterns and channel sequencing behavior.

- **mta_shapley_attribution_final** - Shapley value attribution results providing fair credit distribution across touchpoints using cooperative game theory. Considers all possible touchpoint combinations within the configured lookback window.

- **mta_top_conversion_journeys** - Top-K most common journey patterns for both converted and non-converted users. Useful for identifying high-performing touchpoint sequences and comparing successful vs unsuccessful journey paths.

- **mta_sankey_journeys** - Journey flow data formatted for Sankey diagram visualization in dashboards. Shows the progression of users through different channels leading to conversion with visual flow metrics.

