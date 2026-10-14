
# NBP — Workflow Setup

This skill guides you through configuring and deploying the NBP workflow in Treasure Data. The workflow generates personalized product recommendations for every user using collaborative filtering (Hivemall) or PrecisionML (ml-batch-api).

## What is NBP?

NBP generates personalized product recommendations for every user. It supports two model engines:

- **`hive`** (custom PS code): Item-based collaborative filtering using Hivemall. Runs DIMSUM similarity on co-occurrence matrices, computes item-item similarity, then recommends items similar to each user's recent purchases. No external API dependency.
- **`automl`** (PrecisionML via ml-batch-api): Uses the ml-batch-api service with one of three algorithms:
  - **ALS**: Collaborative filtering — best quality for active users
  - **similar_to_latest**: Recommends items similar to the user's most recent purchase
  - **popular**: Globally popular items — cold-start fallback

**Key outputs:**
- Per-user product recommendations (nbp_1, nbp_2, ... columns) for Parent Segment ingestion
- Item-item similarity scores (hive engine)
- Model evaluation metrics (precision, recall vs random baseline)
- Dashboard with recommendation distribution, item analysis, and test set results

## Use Cases

- Personalized product recommendations for marketing campaigns
- Email content personalization (recommend products per user)
- Parent Segment attribute enrichment (nbp_1, nbp_2, ... columns)
- Cold-start coverage for new users (popular algorithm)
- Product affinity analysis (item-item similarity)

## NBP Configuration Workflow

### Step 1: Gather Requirements

Ask the user:
1. **What is the Treasure Data database name?** (e.g., `gldn`, `ecommerce_prod`)
2. **What site/region is their TD account on?** (determines API endpoint)
3. **Which model engine?** `hive` (custom Hivemall CF) or `automl` (ml-batch-api with ALS/similar_to_latest/popular)
4. **How many recommendations per user?** (default: 5)

**Reference**: Read `requirements_doc.md` for the full requirements gathering workflow including local outputs setup, table discovery, column mapping, exclusion filter analysis, and data quality validation.

### Step 2: Explore the Customer's Database

Use **Trino SQL** via **td-skills** to discover source tables.

NBP requires a **transaction/interaction table** with item-level granularity — each row represents one user interacting with one item.

#### Transaction / Order-Item Tables
- Tables like: `enrich_orders`, `enriched_orders`, `order_items`, `transactions`, `purchases`
- Needed columns: time, user_id, item_id, item_name, item_category
- **Purpose**: Primary input — user-item interactions for collaborative filtering

#### Item Info / Product Catalog Tables (Optional)
- Tables like: `products`, `product_catalog`, `item_master`
- Needed columns: item_id, item_name, item_category
- **Purpose**: Enrichment — item names and categories for recommendation output (can be same as transaction table)

**Reference**: Read `requirements_doc.md` Steps 3–4 for detailed table discovery queries and granularity verification.

### Step 3: Copy the NBP Workflow Template

Copy the bundled template into the engagement working copy (see `deploy_instructions.md`):

```bash
dest="agent_outputs/<customer_slug>/nbp/workflow"
mkdir -p "$dest"
[ -d "$dest/nbp_prod" ] || cp -R "<solution_dir>/project_templates/nbp_prod" "$dest/"
```

### Step 4: Generate the Input YAML Configuration

The critical file to generate is: `nbp_prod/config/params.yml`

**Reference**: Read `yaml_structure.md` for the complete YAML structure and parameter reference.

#### Global Parameters

```yaml
sink_database: ml_output                      # where output tables will be stored
prefix: 'nbp_'                                # prefix for all intermediate/output tables
user_master_attr_table: nbp_user_master       # final attribute table with per-rank columns
cleanup_temp_tables: no                       # 'yes' to drop temp tables after run
```

**Key decisions:**
- `sink_database`: Must exist and user must have write permissions
- `prefix`: Use a customer-specific prefix if multiple NBP deployments share a database

#### Model Type Parameters

```yaml
model_type: 'automl'                          # 'hive' or 'automl'
automl_model_type: als                        # als, similar_to_latest, or popular (automl only)
ml_batch_api_endpoint: 'https://ml-batch-api.treasuredata.com'  # varies by site
als_sample_rate: 1.0                          # user sampling ratio for ALS (1.0 = no sampling)
als_max_users: 100000                         # max distinct users after sampling
filter_viewed: false                          # exclude already-purchased items (automl only)
```

**Key decisions:**
- `model_type`: Choose based on API dependency tolerance and cold-start needs (see Model Type Decision table below)
- `automl_model_type`: ALS for best quality, `popular` for cold-start fallback, `similar_to_latest` for recency-weighted
- `als_sample_rate`: Use < 1.0 for > 200K users to control training time

#### Input Table Mappings

```yaml
in_db: gldn                                   # database containing source tables
original_item_transactions_table: enrich_orders
original_item_info_table: enrich_orders       # can be the same as transactions table
original_user_id_column_name: td_canonical_id
original_item_id_column_name: item_sku
original_item_name_column_name: item_name
original_item_category_column_name: item_category
original_timestamp_name: time
orders_lookback: ''                           # number of days (e.g., 180), or '' for all history
```

**Key decisions:**
- `original_item_info_table`: Use same table if it contains item_name + item_category; otherwise use a separate catalog table
- `orders_lookback`: Empty string for all history, or integer for days (no quotes around the number)
- Column names must exactly match the actual schema — verify with `DESCRIBE`

#### Exclusion Filters

```yaml
transaction_filter: ''                        # if applicable, begin with 'AND ...' to dynamically apply to the queries/create_transaction_table.sql
exclusion_column: item                        # which column to filter on
exclusion_values: query                       # regex pattern, or 'query' for custom SQL
exclude_product_train: yes                    # edit queries/create_transaction_table_filters.sql
exclude_product_recs: no                      # edit queries/filter_products_recs.sql
```

**Key decisions:**
- `exclusion_values`: Use regex (e.g., `'Gift Card|Membership'`) for simple patterns, or `query` for complex logic
- When `query`: edit `queries/create_transaction_table_filters.sql` with custom exclusion SQL
- Typical exclusions: gift cards, memberships, discontinued products, test items

#### Hive Engine Parameters

```yaml
topk_similar_items: 3                         # item-item similarities per item (default: 3)
recent_items: 1                               # recent user purchases to seed from (default: 1)
max_recommended_items: 5                      # recommendations per user (default: 5)
min_cooccurence_filter: 1                     # minimum purchases per item (default: 1)
dimsum_similarity_threshold: 0.25             # similarity cutoff 0-1 (default: 0.25)
```

**Key decisions:**
- These params are ONLY used when `model_type: hive` — ignored for automl
- More diverse recommendations: increase `topk_similar_items` (5-10), lower `dimsum_similarity_threshold` (0.1)
- More focused recommendations: decrease `topk_similar_items` (2), raise `dimsum_similarity_threshold` (0.4)
- Filter rare items: increase `min_cooccurence_filter` (3-5)

#### Model Evaluation

```yaml
run_model_test_set: yes                       # run holdout test comparison
test_params:
  test_lookback: 30d                          # holdout period for test comparison
```

**Key decisions:**
- `run_model_test_set`: Set to `yes` for first deployment to validate quality; can disable for production runs
- `test_lookback`: Holdout period — `30d` is typical; shorter for fast-moving catalogs, longer for stable ones


**Key decisions:**
- Requires `td.apikey` workflow secret (TD API key) — set by the user themselves (so the key never appears in chat): `! tdx wf secrets set <project> td.apikey=<KEY>`
- `api_endpoint`: Must match the customer's site (see Site / API Endpoint Mapping below)

### Step 5: Table-Specific Configuration

NBP has one primary input: the transaction table. For each customer, verify:

#### Transaction Table Requirements

| Requirement | Check | Failure Mode |
|-------------|-------|--------------|
| Item-level granularity | Each row = one user + one item | Model trains on wrong cardinality |
| User ID present | `user_col IS NOT NULL` count | Users without IDs are dropped |
| Item ID present | `item_col IS NOT NULL` count | Items without IDs are dropped |
| Sufficient users | > 100 distinct users | Model can't learn patterns |
| Sufficient items | > 10 distinct items | Recommendations lack diversity |
| Item info available | item_name and item_category exist | Recommendations show IDs instead of names |

#### Item Info Join (When Using Separate Table)

The workflow joins on item ID cast to VARCHAR. Verify the join works:

```sql
-- Check that item IDs match between tables
SELECT
  (SELECT COUNT(DISTINCT CAST(item_sku AS VARCHAR)) FROM db.transactions) AS tx_items,
  (SELECT COUNT(DISTINCT CAST(item_id AS VARCHAR)) FROM db.product_catalog) AS catalog_items;

-- Sample the join
SELECT t.item_sku, i.product_name, i.category
FROM db.transactions t
JOIN db.product_catalog i ON CAST(t.item_sku AS VARCHAR) = CAST(i.item_id AS VARCHAR)
LIMIT 10;
```

**CRITICAL**: Values must match after VARCHAR cast — `12345` vs `SKU-12345` will NOT match.

### Step 6: Column Discovery

For the transaction table, identify these columns:

| Role | Common Names | Priority |
|------|-------------|----------|
| User ID | `td_canonical_id`, `canonical_id`, `cdp_profile_id`, `user_id` | `td_canonical_id` > `canonical_id` > `user_id` |
| Item ID | `item_sku`, `product_id`, `item_id`, `sku` | `item_sku` > `product_id` > `item_id` |
| Timestamp | `time`, `timestamp`, `event_time`, `created_at` | `time` (TD standard) |
| Item Name | `item_name`, `product_name`, `title`, `name` | `item_name` > `product_name` |
| Item Category | `item_category`, `category`, `department`, `brand` | `item_category` > `category` |

**Watch out**: Don't confuse `order_id`, `transaction_id`, or `event_id` with item ID.

**Reference**: Read `requirements_doc.md` Step 5 for full discovery SQL queries.

### Step 7: Validate the Configuration

Before finalizing, verify:
1. All table names exist in the database
2. Column names are correct for each table
3. Item info join works (item IDs match between tables after VARCHAR cast)
4. Exclusion filters are appropriate
5. `sink_database` exists and user has write permissions
6. API endpoint matches the customer's site
7. `orders_lookback` is correct format (integer for days, `''` for all history)

### Step 8: Present to User for Approval

Show the user:
1. **Discovered tables** and their role (transaction + item info)
2. **Column mappings** — user ID, item ID, timestamp, item name, category
3. **Model configuration** — engine, algorithm, parameters
4. **Exclusion filters** — what's excluded and why
5. **The generated `params.yml`**
6. **Request confirmation** before proceeding

### Step 9: Present Final YAML and Confirm

Before deploying, **always present the complete `params.yml`** to the user for review.

Show the full YAML content and ask:

> Here is the final `params.yml` that will be deployed. Please review and confirm this is correct.

**Wait for explicit confirmation before proceeding.**

After confirmation, use `AskUserQuestion` to ask:

> Would you like to push this workflow with the default project name `next_best_product`, or would you like to provide a custom project name?

Present `next_best_product` as the recommended default option. If the user provides a custom name, record it and use it in all subsequent push/run/monitor commands.

### Step 10: Deploy

**STOP — read both files below before executing any command in this step:**
1. **`deploy_instructions.md`** — template location, working-copy path, and project-name push command.
2. **`../../../shared/push_pattern_td_workflows.md`** — full canonical deploy flow including the mandatory project name confirmation, secrets setup, workflow run, monitoring, and output validation.

Do not copy files, write files, or run any `tdx` command until both files have been read.

**Project name gate (mandatory — use `AskUserQuestion`):**
Before pushing, ask the user whether to use the default project name `next_best_product` or provide a custom name. Present `next_best_product` as the recommended option. Record the confirmed name and use it in all subsequent push/run/monitor commands.

Summary of steps (details in shared instructions):
1. Copy the template into `agent_outputs/<customer_slug>/nbp/workflow/nbp_prod/` (see `deploy_instructions.md`)
2. Write `params.yml` into `agent_outputs/<customer_slug>/nbp/workflow/nbp_prod/config/params.yml`
3. Edit custom SQL files in the working copy if `exclusion_values: query`
4. Authenticate: confirm correct TD profile is active
5. **Ask the user for the project name** (gate above), write `tdx.json` with that name in the working copy, then push with `( cd "agent_outputs/<customer_slug>/nbp/workflow/nbp_prod" && tdx wf push -y )` (see `deploy_instructions.md`)
6. Ask the user if they want to trigger a workflow run before proceeding
7. If yes: run, monitor, and validate output tables (see `eval.md`)
8. Record the project name, push date, and validation results in `project_state.md`

## Model Type Decision

| Consideration | `hive` | `automl` |
|--------------|--------|----------|
| API dependency | None — runs on Hive | Requires ml-batch-api |
| Algorithm control | Full tuning (similarity threshold, K neighbors) | Algorithm selection only |
| Cold-start handling | No built-in fallback | `popular` algorithm covers all users |
| Already-purchased filtering | Built into SQL (`NOT EXISTS`) | `filter_viewed` toggle |
| Compute | Hive cluster | ml-batch-api service |

## Critical Configuration Rules

### Site / API Endpoint Mapping

| Site      | API Endpoint | ml-batch-api (automl only) |
|-----------|-------------|----------------------------|
| aws       | `api.treasuredata.com` | `https://ml-batch-api.treasuredata.com` |
| aws-tokyo | `api.treasuredata.co.jp` | `https://ml-batch-api.treasuredata.co.jp` |
| eu01      | `api.eu01.treasuredata.com` | `https://ml-batch-api.eu01.treasuredata.com` |
| ap02      | `api.ap02.treasuredata.com` | `https://ml-batch-api.ap02.treasuredata.com` |
| ap03      | `api.ap03.treasuredata.com` | `https://ml-batch-api.ap03.treasuredata.com` |

### Common Mistakes to Avoid

**1. Using an aggregated table instead of transaction-level**
```yaml
# DON'T: user_summary has one row per user, no item detail
original_item_transactions_table: user_summary
# DO: use item-level table
original_item_transactions_table: enrich_orders
```

**2. Wrong item column**
```yaml
# DON'T: order_id is not an item
original_item_id_column_name: order_id
# DO: use the product/item identifier
original_item_id_column_name: item_sku
```

**3. Item info table join failure**
The item ID column must match between tables. The workflow casts both to VARCHAR, but verify the values actually match (e.g., `12345` vs `SKU-12345` won't match).

**4. Wrong api_endpoint for the site**
```yaml
# DON'T: aws endpoint for a Tokyo customer
ml_batch_api_endpoint: 'https://ml-batch-api.treasuredata.com'
# DO: match the site
ml_batch_api_endpoint: 'https://ml-batch-api.treasuredata.co.jp'
```

**5. orders_lookback as string vs number**
```yaml
# DON'T: use quotes around the number
orders_lookback: '180'
# DO: no quotes for number, or '' for all history
orders_lookback: 180
orders_lookback: ''
```

**6. Wrong model_type for the use case**
```yaml
# DON'T: using hive when you need cold-start coverage
model_type: 'hive'  # hive has no 'popular' fallback for zero-history users
# DO: use automl with 'popular' for cold-start
model_type: 'automl'
automl_model_type: popular
```

## Progressive Disclosure

- **Full requirements gathering workflow**: Read `requirements_doc.md`
- **Complete YAML structure & parameter reference**: Read `yaml_structure.md`
- **Table-specific configuration**: Read `table_configuration.md`
- **Template copy + deploy instructions**: Read `deploy_instructions.md`
- **Hive vs automl gap analysis**: Read `gap_analysis.md`
- **Input params template**: Read `input_params_template.yml`

## Workflow Template Location

The NBP workflow template ships with this skill at `project_templates/nbp_prod/`. After generating `params.yml`, place it in the engagement working copy at `agent_outputs/<customer_slug>/nbp/workflow/nbp_prod/config/params.yml` — never in the template.
