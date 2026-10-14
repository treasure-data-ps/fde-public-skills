# Phase 3: Workflow Configuration

Generate the `config/params.yml` file using the values gathered in Phases 1–2.

## Complete Template

```yaml
#####################################################################
########################## GLOBAL PARAMS ############################
#####################################################################

# -- Output --------------------------------------------------------
sink_database: ml_output                      # where output tables will be stored
prefix: 'nbp_'                                # prefix for all intermediate/output tables
user_master_attr_table: nbp_user_master       # final attribute table with per-rank recommendation columns
cleanup_temp_tables: no                       # 'yes' to drop temp tables after run

# -- Model Type ----------------------------------------------------
# 'hive'   = custom PS Hivemall collaborative filtering (no API dependency)
# 'automl' = PrecisionML via ml-batch-api
model_type: 'automl'
automl_model_type: als                        # als, similar_to_latest, or popular (automl only)
ml_batch_api_endpoint: 'https://ml-batch-api.treasuredata.com'  # varies by site
als_sample_rate: 1.0                          # user sampling ratio for ALS (1.0 = no sampling). Use < 1.0 for > 200K users.
als_max_users: 100000                         # max distinct users after sampling for ALS training
filter_viewed: false                          # exclude already-purchased items from recommendations (automl only; hive does this automatically)

#####################################################################
########################## INPUT PARAMS #############################
#####################################################################

# -- Source Tables --------------------------------------------------
in_db: gldn                                           # database containing source tables
original_item_transactions_table: enrich_orders       # transaction table (requires userid, itemid, timestamp)
original_item_info_table: enrich_orders               # item info table (requires itemid, item_name, item_category)
                                                      ## can be the same as the transactions table

# -- Column Mappings ------------------------------------------------
original_user_id_column_name: td_canonical_id         # USER ID column from transactions table
original_item_id_column_name: item_sku                # ITEM ID column from transactions table
original_item_name_column_name: item_name             # ITEM NAME column from transactions/info table
original_item_category_column_name: item_category     # ITEM CATEGORY column from transactions/info table
original_timestamp_name: time                         # order timestamp column (unix timestamp)

# -- Time Filter ----------------------------------------------------
orders_lookback: ''                                   # number of days (e.g., 180), or '' for all history

#####################################################################
######################## EXCLUSION FILTERS ##########################
#####################################################################

# Two-stage filtering:
#   exclude_product_train = remove items from training data
#   exclude_product_recs  = remove items from final recommendations
#
# exclusion_values:
#   - Regex pattern to match against exclusion_column (e.g., 'Gift Card|Membership')
#   - Or 'query' to use custom SQL in queries/create_transaction_table_filters.sql

transaction_filter: ''                        # if applicable, begin with 'AND ...' to dynamically apply to the queries/create_transaction_table.sql
exclusion_column: item                        # which column to filter on
exclusion_values: query                       # regex pattern, or 'query' for custom SQL
exclude_product_train: yes                    # edit queries/create_transaction_table_filters.sql
exclude_product_recs: no                      # edit queries/filter_products_recs.sql

#####################################################################
################### HIVE ENGINE PARAMETERS ##########################
#####################################################################
# These params are ONLY used when model_type = 'hive'
# Ignored when model_type = 'automl'

topk_similar_items: 3                         # item-item similarities per item (default: 3)
recent_items: 1                               # recent user purchases to seed from (default: 1)
max_recommended_items: 5                      # recommendations per user (default: 5)
min_cooccurence_filter: 1                     # minimum purchases per item (default: 1)
dimsum_similarity_threshold: 0.25             # similarity cutoff 0-1 (default: 0.25)

#####################################################################
################### MODEL EVALUATION ################################
#####################################################################

run_model_test_set: yes                       # run holdout test comparison
test_params:
  test_lookback: 30d                          # holdout period for test comparison
```

---

## Parameter Reference

### Global Parameters

| Parameter | Type | Required | Description | Example Values |
|-----------|------|----------|-------------|----------------|
| `sink_database` | string | yes | Output database for all NBP tables | `ml_output`, `<source_database>` |
| `prefix` | string | yes | Prefix for all intermediate/output table names | `nbp_`, `client_nbp_` |
| `user_master_attr_table` | string | yes | Final attribute table name (no prefix applied) | `nbp_user_master` |
| `cleanup_temp_tables` | yes/no | yes | Drop temporary tables after workflow completes | `no` (keep for first run), `yes` (drop) |

### Model Type Parameters

| Parameter | Type | Required | Description | Example Values |
|-----------|------|----------|-------------|----------------|
| `model_type` | string | yes | Recommendation engine | `hive` (Hivemall CF), `automl` (ml-batch-api) |
| `automl_model_type` | string | automl only | Algorithm for ml-batch-api | `als`, `similar_to_latest`, `popular` |
| `ml_batch_api_endpoint` | string | automl only | ml-batch-api URL (varies by TD site) | `https://ml-batch-api.treasuredata.com` |
| `als_sample_rate` | float | automl+ALS only | Random user sampling ratio (1.0 = no sampling) | `1.0`, `0.5`, `0.3` |
| `als_max_users` | int | automl+ALS only | Max distinct users after sampling | `100000`, `50000` |
| `filter_viewed` | bool | automl only | Exclude already-purchased items from recs. Hive engine does this automatically via SQL. | `false`, `true` |

#### ALS Sampling Guide

For automl with ALS on large datasets, sampling prevents excessive training time:

| User Count | `als_sample_rate` | `als_max_users` |
|-----------|-------------------|-----------------|
| < 200K | `1.0` (no sampling) | `100000` |
| 200K - 500K | `0.5` | `100000` |
| > 500K | `0.3` | `100000` |

Other algorithms (`similar_to_latest`, `popular`) and the hive engine are unaffected by these params.

### Input Table Parameters

| Parameter | Type | Required | Description | Example Values |
|-----------|------|----------|-------------|----------------|
| `in_db` | string | yes | Database containing source tables | `gldn`, `ecommerce_prod` |
| `original_item_transactions_table` | string | yes | Transaction table name (without db prefix) | `enrich_orders`, `order_items` |
| `original_item_info_table` | string | yes | Item info table (can be same as transactions) | `enrich_orders`, `products` |
| `original_user_id_column_name` | string | yes | User ID column in transactions table | `td_canonical_id`, `canonical_id`, `user_id` |
| `original_item_id_column_name` | string | yes | Item ID column in transactions table | `item_sku`, `product_id`, `item_id` |
| `original_item_name_column_name` | string | yes | Item name column in item info table | `item_name`, `product_name`, `title` |
| `original_item_category_column_name` | string | yes | Item category column in item info table | `item_category`, `category`, `department` |
| `original_timestamp_name` | string | yes | Timestamp column (unix timestamp) | `time`, `timestamp`, `event_time` |
| `orders_lookback` | string | yes | Lookback period in days, or `''` for all history | `''`, `180`, `365` |

#### Same vs Separate Item Info Table

```yaml
# Same table — item metadata alongside transactions
original_item_transactions_table: enrich_orders
original_item_info_table: enrich_orders

# Separate table — product catalog is distinct from transactions
original_item_transactions_table: order_items
original_item_info_table: product_catalog
```

The workflow JOINs on item ID (cast to VARCHAR) between the two tables.

### Exclusion Filter Parameters

| Parameter | Type | Required | Description | Example Values |
|-----------|------|----------|-------------|----------------|
| `transaction_filter` | string | yes | SQL Filter starting with 'AND..' to apply custom filter on transaction table | `AND country_code != 'JPN`, `' '` |
| `exclusion_column` | string | yes | Column to apply exclusion regex on | `item`, `item_category`, `item_name` |
| `exclusion_values` | string | yes | Regex pattern OR `query` for custom SQL | `'Gift Card\|Membership'`, `query` |
| `exclude_product_train` | yes/no | yes | Apply exclusion to training data | `yes`, `no` |
| `exclude_product_recs` | yes/no | yes | Apply exclusion to recommendation output | `yes`, `no` |

#### Exclusion Methods

**Method 1: Column-based regex**
```yaml
exclusion_column: item_category
exclusion_values: 'Gift Card|Membership|Discontinued'
exclude_product_train: yes
exclude_product_recs: no
```

**Method 2: Custom SQL query**
```yaml
exclusion_column: item
exclusion_values: query
exclude_product_train: yes
exclude_product_recs: no
```
When set to `query`, edit the corresponding SQL files directly:
- `queries/create_transaction_table_filters.sql` — training exclusion logic
- `queries/filter_products_recs.sql` — recommendation exclusion logic

Example custom SQL for training exclusion:
```sql
WITH exclude AS (
  SELECT DISTINCT itemid
  FROM ${prefix}transaction_unfiltered
  WHERE item_category IN ('Gift Card', 'Membership')
     OR LOWER(item_name) LIKE '%test%'
     OR itemid IN ('INTERNAL_001', 'INTERNAL_002')
)
SELECT * FROM ${prefix}transaction_unfiltered
WHERE itemid NOT IN (SELECT itemid FROM exclude)
```

### Hive Engine Parameters

Only used when `model_type: hive`. Ignored for automl.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topk_similar_items` | int | 3 | Number of item-item similarities to retain per item |
| `recent_items` | int | 1 | Number of each user's most recent purchases to seed from |
| `max_recommended_items` | int | 5 | Recommendations per user |
| `min_cooccurence_filter` | int | 1 | Minimum purchases per item to be included |
| `dimsum_similarity_threshold` | float | 0.25 | DIMSUM cosine similarity threshold (0 = no filtering, 1 = exact match only) |

#### Hive Tuning Guide

- **More diverse recommendations**: Increase `topk_similar_items` (e.g., 5-10) and lower `dimsum_similarity_threshold` (e.g., 0.1)
- **More focused recommendations**: Decrease `topk_similar_items` (e.g., 2) and raise `dimsum_similarity_threshold` (e.g., 0.4)
- **Include more user history**: Increase `recent_items` (e.g., 3-5)
- **Filter rare items**: Increase `min_cooccurence_filter` (e.g., 3-5) to remove items with very few purchases

### Model Evaluation Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `run_model_test_set` | yes/no | yes | Run holdout test set comparison |
| `test_params.test_lookback` | string | `30d` | Holdout period (e.g., `30d`, `7d`, `60d`) |

The test set evaluation compares recommendations against actual purchases in the holdout period, computing:
- Similarity scores between recommended and purchased items
- Category match rates
- Precision and recall metrics (automl only)

### Dashboard Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dash_params.create_dashboard` | yes/no | yes | Create/refresh TI datamodel and dashboard |
| `dash_params.api_endpoint` | string | `api.treasuredata.com` | TD API endpoint (must match customer's site) |
| `dash_params.model_config_table` | string | `datamodel_build_history` | Table to track datamodel build history |

**Requirement**: A TD API key must be stored as a workflow secret named `td.apikey`.

---

## Validation Checklist

Before presenting to the user, verify:

1. **Line-item granularity**: Transaction table has one row per user-item interaction (not order-level or aggregated)
2. **Column names are correct**: user, item, time, item name, item category all match the actual schema
3. **Item info join works**: Item ID columns match between transaction and item info tables
4. **Exclusion filters are appropriate**: Reviewed categories/items to exclude
5. **Sink database exists**: User has write permissions
6. **API endpoint matches site**: Both `ml_batch_api_endpoint` (automl) and `dash_params.api_endpoint`
7. **`orders_lookback` is correct format**: Integer (no quotes) for days, or `''` (quoted empty string) for all history

```sql
-- Final validation queries
-- Confirm item-level granularity
SELECT COUNT(*) AS rows, COUNT(DISTINCT user_col) AS users, COUNT(DISTINCT item_col) AS items
FROM database_name.table_name;

-- Check for NULLs in critical columns
SELECT
  COUNT(CASE WHEN user_col IS NULL THEN 1 END) AS null_users,
  COUNT(CASE WHEN item_col IS NULL THEN 1 END) AS null_items,
  COUNT(CASE WHEN time_col IS NULL THEN 1 END) AS null_time
FROM database_name.table_name;

-- Verify item info join
SELECT COUNT(DISTINCT t.item_id) AS transaction_items,
       COUNT(DISTINCT i.item_id) AS info_items,
       COUNT(DISTINCT CASE WHEN i.item_id IS NOT NULL THEN t.item_id END) AS matched
FROM transaction_table t
LEFT JOIN item_info_table i ON CAST(t.item_id AS VARCHAR) = CAST(i.item_id AS VARCHAR);
```

---

## Presenting to User for Approval

Show the user a summary like this:

```
I've configured NBP for your database:

Model type: automl (ALS via ml-batch-api)

Source: gldn.enrich_orders
  - 2.3M rows, 150K users, 8K products
  - User column: td_canonical_id
  - Item column: item_sku
  - Time column: time

Item info: same table (enrich_orders)
  - Item name: item_name
  - Item category: item_category

Exclusion filters:
  - Training: custom query (edit queries/create_transaction_table_filters.sql)
  - Recommendations: none

Output:
  - Sink database: ml_output
  - User master table: nbp_user_master (with nbp_1, nbp_2, ... columns)
  - Dashboard: yes (api.treasuredata.com)

Please review the generated params.yml and confirm.
```

Then present the full `params.yml` file for review.

---

## Common Mistakes to Avoid

### 1. Using an aggregated table instead of transaction-level
```yaml
# DON'T: user_summary has one row per user, no item detail
original_item_transactions_table: user_summary
```

### 2. Wrong item column
```yaml
# DON'T: order_id is not an item
original_item_id_column_name: order_id
```

### 3. Item info table join failure
The item ID column must match between tables. The workflow casts both to VARCHAR, but verify the values actually match.

### 4. Wrong api_endpoint for the site
```yaml
# DON'T: aws endpoint for a Tokyo customer
api_endpoint: 'api.treasuredata.com'

# DO: match the site
api_endpoint: 'api.treasuredata.co.jp'
```

### 5. orders_lookback as string vs number
```yaml
# DON'T: use quotes around the number
orders_lookback: '180'

# DO: no quotes for number, or '' for all history
orders_lookback: 180
orders_lookback: ''
```

### 6. Wrong model_type for the use case
```yaml
# DON'T: using hive when you need cold-start coverage
model_type: 'hive'  # hive has no 'popular' fallback for zero-history users

# DO: use automl with 'popular' for cold-start
model_type: 'automl'
automl_model_type: popular
```

---

## Key Differences from MTA Configuration

| Aspect | NBP | MTA |
|--------|-----|-----|
| Input tables | Single transaction table + optional item info | Multiple touchpoint sources (pageviews, email, sales, orders) |
| Per-table columns | `user_id`, `item_id`, `timestamp`, `item_name`, `item_category` | `url_col`, `referral_col`, `medium_col`, `source_col`, `campaign_col`, `utm_mailing_col`, `context_col`, `event_type`, `conversion_flag`, `item_price` |
| Global params | `model_type`, `prefix`, `sink_database`, engine-specific tuning | `session_length`, `backfill_partition_col`, `top_k_*`, `journey_steps_lookback` |
| Purpose of each table | Single source of user-item interactions | Each is a touchpoint source; one or more define conversions |
| Conversion concept | Not applicable — all rows are interactions | Explicit `conversion_flag` per table |
| Channel attribution | Not applicable | `medium_col`, `source_col`, `campaign_col` per table |
| Model output | Per-user ranked product recommendations | Per-channel attribution scores (Markov, Shapley, linear, time-decay) |
| Config file | `config/params.yml` | `config/input_params.yml` |
