# MTA Workflow Setup Guide

Step-by-step guide for configuring and deploying the MTA Journey Analytics workflow in Treasure Data.

The workflow builds a unified touchpoint journey from multiple data sources, then runs attribution models (Markov, Shapley) to measure channel contribution to conversions.

## What is MTA Journey Analytics?

Multi-Touch Attribution (MTA) analyzes the full customer journey across channels to determine which touchpoints contribute most to conversions. Unlike last-click attribution, MTA distributes credit across all touchpoints.

**Key outputs:**
- Unified journey table (all touchpoints sessionized per customer)
- Channel-level attribution scores (Markov, Shapley, linear, time-decay)
- Top conversion journeys and path analysis
- Channel spend efficiency (CPA, CPB, ROI)

## Use Cases

- Marketing budget allocation across channels
- Channel performance comparison
- Conversion path analysis and optimization
- Campaign effectiveness measurement
- Customer journey visualization (Sankey diagrams)

## MTA Configuration Workflow

### Step 1: Gather Requirements

Walk through `requirements_doc.md` with the user — it covers local output setup (`agent_outputs/`), customer name, ID Unification status, touchpoint sources, and conversion definition.

For a quick setup without the full requirements gathering, ask the user:
1. **What is the Treasure Data database name?** (e.g., `<source_database>`)
2. **What counts as a conversion?** (e.g., purchase, form submit, thank-you page visit)
3. **What is the user ID column?** (e.g., `canonical_id`)
4. **What time range should we analyze?** (fixed range or lookback period)

### Step 2: Explore the Customer's Database

Use **Trino SQL** via **tdx-skills** to discover touchpoint source tables.

MTA requires tables that represent **marketing touchpoints**. Look for:

#### Web Activity (pageviews, site visits)
- Tables like: `enriched_pageviews`, `web_events`, `page_views`
- Needed columns: time, user_id, URL, referrer, UTM params (source/medium/campaign)
- **Purpose**: Web touchpoints with UTM-based channel attribution

#### Email Events
- Tables like: `enriched_email_events`, `email_activity`
- Needed columns: time, user_id, event_type, campaign_name, email_name
- **Purpose**: Email channel touchpoints (opens, clicks, conversions)

#### Sales Rep Interactions
- Tables like: `enriched_sales_rep_interactions`, `crm_activity`
- Needed columns: time, user_id, source, topic
- **Purpose**: Offline/sales channel touchpoints

#### Orders / Conversions
- Tables like: `enriched_orders`, `purchases`, `transactions`
- Needed columns: time, user_id, order_type, order_status, unit_price
- **Purpose**: Conversion events — these define the goal the attribution models optimize for

### Step 3: Copy the MTA Workflow Template

The template ships with this skill at `project_templates/mta_journey_agent/` (relative to `ai-signals-skills/mta/`). Never edit it — copy it into the engagement's working directory (see `../../../shared/push_pattern_td_workflows.md` Step 1):

```bash
dest="agent_outputs/<customer_slug>/mta/workflow"
mkdir -p "$dest"
[ -d "$dest/mta_journey_agent" ] || cp -R "<mta_skill_dir>/project_templates/mta_journey_agent" "$dest/"
```

`<mta_skill_dir>` is the absolute path of the `ai-signals-skills/mta/` folder.

### Step 4: Generate the Input YAML Configuration

The critical file to generate is: `config/input_params.yml` inside the working copy (`agent_outputs/<customer_slug>/mta/workflow/mta_journey_agent/config/input_params.yml`)

**Reference**: Read `yaml_structure.md` for the complete YAML structure.

#### Global Parameters

```yaml
sink_database: <sink_database>
unique_user_id: canonical_id
api_endpoint: 'api.treasuredata.com'
cleanup_temp_tables: 'no'
include_non_converted_channels: yes
```

#### Customer Enrichment (Optional)

If the customer already has RFM or other customer-level scoring:
```yaml
add_customer_analysis: 'yes'
customers_table: <source_database>.rfm_output_table
attributes_list: 'recency, frequency, monetary_value, rfm_segment'
```

#### Time Filters

```yaml
time_filter_type: range              # 'range' or 'interval'
time_range_start_date: 2022-01-01
time_range_end_date: 2222-22-22      # 2222-22-22 = use latest available
lookback_period: -180d               # only used with 'interval'
```

#### Session & Journey Parameters

```yaml
session_length: 3600                 # seconds of inactivity to start new session (3600 = 1hr)
backfill_partition_col: ${unique_user_id}  # backfill NULLs across full journey (or 'session_id' for session-only)
top_k_channel_perc: 0.01            # collapse low-frequency channels to 'others'
top_k_conv_perc: 0.01               # collapse low-conversion channels to 'others'
top_k_journeys: 50                  # top distinct conversion journeys to extract
sample_tpoint_limit: 25             # max touchpoints per sample journey
journey_steps_lookback: 20          # first/last-N touchpoints to keep per journey
agg_analysis_cols: ["event_context", "channel"]
summary_table_top_k: 20            # top-K distinct values for summary stats
```

### Step 5: Table-Specific Configuration

Each table entry in `aggregate_metrics_tables` has MTA-specific columns for channel identification, UTM parsing, and conversion flagging.

**Reference**: Read `table_configuration.md` for per-table-type guidance.

#### Pageviews / Web Activity

```yaml
- src_table: <source_database>.enriched_pageviews
  table_description: 'Web Activity data streamed from JS SDK'
  name: pageviews
  unixtime_col: time
  url_col: td_url
  referral_col: td_referrer
  medium_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_medium'), url_extract_parameter(LOWER(td_url),'medium'))"
  source_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_source'), url_extract_parameter(LOWER(td_url),'source'))"
  campaign_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_campaign'), url_extract_parameter(LOWER(td_url),'campaign'))"
  utm_mailing_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_mailing'), url_extract_parameter(LOWER(td_url),'mailing'))"
  context_col: td_title
  event_type: "'web activity'"
  custom_filter: "${unique_user_id} IS NOT NULL AND REGEXP_LIKE(lower(td_language), 'en')"
  conversion_flag: "IF(REGEXP_LIKE(lower(td_path), 'thank_you'), 1.0, 0.0)"
  item_price: 1.0
  apply_time_filter: false
  query_type:
```

**Key decisions per customer:**
- `conversion_flag`: What URL pattern = conversion? (e.g., `thank_you`, `confirmation`, `checkout/success`)
- `custom_filter`: Filter by language, exclude bots, etc.
- `url_col` / `referral_col`: Which columns hold URL and referrer data

**CRITICAL — UTM column syntax for web activity tables:**
The `medium_col`, `source_col`, `campaign_col`, and `utm_mailing_col` must **always** use the fixed COALESCE pattern below — only substituting the URL column name (e.g., `page_url`, `td_url`). **Never** coalesce NULLs to hardcoded defaults like `'direct'` or `'none'`. The workflow's backfill logic later fills NULL channel values from other touchpoints in the journey. Hardcoding defaults would prevent that backfill from working.

```
medium_col:      "COALESCE(url_extract_parameter(LOWER(<url_col>),''utm_medium''), url_extract_parameter(LOWER(<url_col>),''medium''))"
source_col:      "COALESCE(url_extract_parameter(LOWER(<url_col>),''utm_source''), url_extract_parameter(LOWER(<url_col>),''source''))"
campaign_col:    "COALESCE(url_extract_parameter(LOWER(<url_col>),''utm_campaign''), url_extract_parameter(LOWER(<url_col>),''campaign''))"
utm_mailing_col: "COALESCE(url_extract_parameter(LOWER(<url_col>),''utm_mailing''), url_extract_parameter(LOWER(<url_col>),''mailing''))"
```
Replace `<url_col>` with the actual URL column name from the customer's table (e.g., `td_url`, `page_url`).

#### Email Events

```yaml
- src_table: <source_database>.enriched_email_events
  table_description: 'Email activity from SFMC'
  name: email_events
  unixtime_col: time
  url_col: CAST(NULL AS VARCHAR)
  referral_col: "'email'"
  medium_col: "'email'"
  source_col: "'sfmc'"
  campaign_col: "REGEXP_REPLACE(lower(campaign_name), '[- ]', '_')"
  utm_mailing_col: "REGEXP_REPLACE(lower(campaign_name), '[- ]', '_')"
  context_col: "REGEXP_REPLACE(lower(email_name), '[- ]', '_')"
  event_type: "CONCAT('email_', event_type)"
  custom_filter: "${unique_user_id} IS NOT NULL AND NOT REGEXP_LIKE(lower(event_type), 'send')"
  conversion_flag: 0.0
  item_price: 0.0
  apply_time_filter: false
  query_type:
```

**Key decisions:**
- `source_col`: Hardcoded to email provider name (e.g., `'sfmc'`, `'marketo'`, `'braze'`)
- `custom_filter`: Exclude 'send' events — only engagement (open, click, etc.)
- `conversion_flag: 0.0` — emails are touchpoints, not conversion events

#### Sales Rep Interactions

```yaml
- src_table: <source_database>.enriched_sales_rep_interactions
  table_description: 'Sales rep notes from SFDC'
  name: sales_rep_interactions
  unixtime_col: time
  url_col: CAST(NULL AS VARCHAR)
  referral_col: CAST(NULL AS VARCHAR)
  medium_col: "'sales_rep_interactions'"
  source_col: source
  campaign_col: topic
  utm_mailing_col: topic
  context_col: topic
  event_type: "CONCAT('sales_rep_interactions_', source)"
  custom_filter: ${unique_user_id} IS NOT NULL
  conversion_flag: 0.0
  item_price: 0.0
  apply_time_filter: false
  query_type:
```

#### Orders / Conversion Events

```yaml
- src_table: <source_database>.enriched_orders
  table_description: 'Order history with item price and order status'
  name: order_events
  unixtime_col: time
  url_col: CAST(NULL AS VARCHAR)
  referral_col: CAST(NULL AS VARCHAR)
  medium_col: CAST(NULL AS VARCHAR)
  source_col: CAST(NULL AS VARCHAR)
  campaign_col: CAST(NULL AS VARCHAR)
  utm_mailing_col: CAST(NULL AS VARCHAR)
  context_col: order_type
  event_type: "CONCAT(lower(order_type), '_order')"
  custom_filter: "${unique_user_id} IS NOT NULL AND order_status IN ('COMPLETE', 'PROCESSING')"
  conversion_flag: 1.0
  item_price: unit_price
  apply_time_filter: false
  query_type: 'custom'
```

**Key decisions:**
- `conversion_flag: 1.0` — this IS the conversion event
- `item_price`: The revenue column (e.g., `unit_price`, `total_amount`)
- `custom_filter`: Only valid orders (exclude cancelled/returned)
- `query_type: 'custom'` — use when you need custom SQL in `sql/union_src_tables/order_events.sql`

### Step 6: Column Discovery

For each table, identify:
1. **Time column**: `time`, `timestamp`, `event_time`
2. **User ID column**: `canonical_id`, `cdp_profile_id`, `user_id`
3. **URL/referrer columns** (web tables): `td_url`, `page_url`, `td_referrer`
4. **Campaign/channel columns**: `campaign_name`, `utm_source`, `utm_medium`
5. **Event type column**: `event_type`, `action`, `activity_type`
6. **Conversion indicator**: URL pattern, status column, or event type
7. **Revenue column** (order tables): `unit_price`, `total_amount`, `revenue`

```sql
DESCRIBE database_name.table_name;
SELECT * FROM database_name.table_name LIMIT 10;

-- For web tables: check UTM parameter availability
SELECT url_extract_parameter(td_url, 'utm_source') as source,
       url_extract_parameter(td_url, 'utm_medium') as medium,
       COUNT(*) as cnt
FROM database_name.enriched_pageviews
WHERE td_url IS NOT NULL
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 20;

-- For email: check event types
SELECT DISTINCT event_type, COUNT(*) FROM database_name.enriched_email_events GROUP BY 1 ORDER BY 2 DESC;

-- For orders: check statuses and amounts
SELECT order_status, COUNT(*), AVG(unit_price) FROM database_name.enriched_orders GROUP BY 1 ORDER BY 2 DESC;
```

### Step 7: Validate the Configuration

Before finalizing, verify:
1. All table names exist in the database
2. Column names are correct for each table
3. `unique_user_id` is consistent across all tables
4. `conversion_flag` correctly identifies conversion events
5. `custom_filter` excludes invalid data (bots, sends, cancelled orders)
6. Channel columns (medium, source, campaign) will produce meaningful values
7. `sink_database` exists and user has write permissions

### Step 8: Present to User for Approval

Show the user:
1. **Discovered tables** and their role (touchpoint vs conversion)
2. **Conversion definition** — what triggers `conversion_flag: 1.0`
3. **Channel mapping** — how source/medium/campaign are derived per table
4. **Filters applied** — what data is excluded and why
5. **The generated `input_params.yml`**
6. **Request confirmation** before proceeding

### Step 9: Present Final YAML and Confirm

Before deploying, **always present the complete `input_params.yml`** to the user for review.

Show the full YAML content and ask:

> Here is the final `input_params.yml` that will be deployed. Please review and confirm this is correct.

**Wait for explicit confirmation before proceeding.**

### Step 10: Deploy

**STOP — read `../../../shared/push_pattern_td_workflows.md` before executing any command in this step.** It is the canonical deploy flow: template copy, mandatory project name confirmation, push mechanics, secrets, workflow run, monitoring, and output validation.

Do not write files or run any `tdx` command until it has been read.

**Project name gate (mandatory — use `AskUserQuestion`):**
Before pushing, ask the user whether to use the default project name `mta_journey_agent` or provide a custom name. Present `mta_journey_agent` as the recommended option. Record the confirmed name and use it in all subsequent push/run/monitor commands.

Once the user has confirmed both the YAML and the project name:
1. Copy the template into `agent_outputs/<customer_slug>/mta/workflow/mta_journey_agent/` if not done yet (Step 3)
2. Write `input_params.yml` to `agent_outputs/<customer_slug>/mta/workflow/mta_journey_agent/config/input_params.yml`
3. Push the workflow to TD from inside `agent_outputs/<customer_slug>/mta/workflow/mta_journey_agent/`:
   - **Default name**: `tdx wf push -y` (uses `mta_journey_agent` from `tdx.json`)
   - **Custom name**: `tdx wf upload <custom_project_name>` (pushes under a different project name without renaming the folder)
4. Set the required workflow secret (needed by the Markov and Shapley Python models). The value is the TD API key used for `tdx auth` — never write it to a file or chat; ask the user to run it themselves:
   ```bash
   ! tdx wf secrets set <project_name> secret_key=<TD_API_KEY>
   ```
   Without this secret, the `mta_markov_shapely` step will fail immediately.
5. Run the workflow using the full entry point dig file:
   ```bash
   tdx wf run <project_name>.mta_advanced_launch
   ```
   `mta_advanced_launch.dig` is the end-to-end entry point — it runs union → journeys → Markov/Shapley in sequence. Do not run `mta_journeys_and_models` or `mta_union_src_tables` directly on the first run; they depend on prior steps completing first.
6. Monitor via `tdx wf sessions <project_name>` and `tdx wf timeline <project_name>.mta_advanced_launch`
7. After a successful run: validate output tables per `eval.md` and update `agent_outputs/<customer_slug>/mta/project_state.md` with the project name, push date, and validation summary

## Critical Configuration Rules

### Conversion Flag Logic

Every table must have a `conversion_flag`. Only conversion-event tables should use `1.0`:

| Table Type | conversion_flag | Reasoning |
|-----------|----------------|-----------|
| Pageviews | `IF(REGEXP_LIKE(lower(td_path), 'thank_you'), 1.0, 0.0)` | Only specific URL patterns count as conversions |
| Email | `0.0` | Touchpoints only, not conversions |
| Sales Rep | `0.0` | Touchpoints only |
| Orders | `1.0` | Orders ARE the conversion |

### Common Mistakes to Avoid

**1. Missing channel columns for non-web tables**
```yaml
# Use CAST(NULL AS VARCHAR) when a channel field doesn't apply
url_col: CAST(NULL AS VARCHAR)
medium_col: "'email'"  # Hardcode the channel name instead
```

**2. Not excluding email 'send' events**
```yaml
# BAD — sends inflate touchpoint counts
custom_filter: "${unique_user_id} IS NOT NULL"
# GOOD
custom_filter: "${unique_user_id} IS NOT NULL AND NOT REGEXP_LIKE(lower(event_type), 'send')"
```

**3. Including cancelled orders as conversions**
```yaml
# BAD
custom_filter: "${unique_user_id} IS NOT NULL"
# GOOD
custom_filter: "${unique_user_id} IS NOT NULL AND order_status IN ('COMPLETE', 'PROCESSING')"
```

**4. Wrong conversion_flag on touchpoint tables**
```yaml
# BAD — email is NOT a conversion
conversion_flag: 1.0
# GOOD
conversion_flag: 0.0
```

## Workflow Template Location

The MTA workflow template ships with this skill at `project_templates/mta_journey_agent/` (read-only). The customer's working copy lives at `agent_outputs/<customer_slug>/mta/workflow/mta_journey_agent/`.

After generating `input_params.yml`, place it in `agent_outputs/<customer_slug>/mta/workflow/mta_journey_agent/config/input_params.yml`.
