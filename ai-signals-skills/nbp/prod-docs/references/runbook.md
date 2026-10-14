
# NBP — Production Documentation

## Workflow Overview

The NBP workflow generates personalized product recommendations for every user using collaborative filtering (Hivemall) or PrecisionML (ml-batch-api). It outputs per-rank columns (nbp_1, nbp_2, ...) ready for Parent Segment ingestion.

**Workflow Template**: `project_templates/nbp_prod/` (bundled with the NBP skill — read-only)
**Workflow Working Copy**: `agent_outputs/<customer_slug>/nbp/workflow/nbp_prod/`
**TD Workflow Project**: `next_best_product` (default)

## Architecture

```
Source Tables (transactions + item info)
    |
Standardize & Filter (prefix_transaction)
    |
Build user-item matrix (prefix_user_item)
    |
Train Model:
  - hive: DIMSUM similarity -> item-item -> user recommendations
  - automl: ml-batch-api (ALS/similar_to_latest/popular)
    |
Generate Recommendations (prefix_topk_recommended_items)
    |
Enrich with item names/categories
    |
Explode to per-rank columns (user_master_attr_table)
    |
Dashboard tables (prefix_dash_*)
```

## Output Tables

All written to `sink_database`:

| Table | Description |
|-------|-------------|
| `{user_master_attr_table}` | Final output — per-rank recommendation columns for Parent Segment |
| `{prefix}transaction` | Standardized transactions (userid, itemid, item_name, item_category, tstamp) |
| `{prefix}itemid_name_product_mapping` | Distinct item_id to name/category mapping |
| `{prefix}user_item` | Aggregated user-item interactions with counts |
| `{prefix}item_similarity` | Item-item cosine similarity via DIMSUM (hive only) |
| `{prefix}topk_similar_items` | Top-K similar items per item (hive only) |
| `{prefix}recent_item_contacts` | Each user's recent item purchases (hive only) |
| `{prefix}topk_recommended_items` | Raw recommendations (userid, rec_items array) |
| `{prefix}dash_*` | Dashboard aggregation tables |
| `{prefix}testset` | Test set comparison results (when enabled) |

## Final Output Schema

The `user_master_attr_table` has exploded per-rank columns for direct Parent Segment ingestion:

| Column | Type | Description |
|--------|------|-------------|
| `<user_id_column>` | VARCHAR | User identifier (original column name preserved) |
| `nbp_ranks` | ARRAY | Rank indices |
| `product_recommendations` | ARRAY | Ordered recommended product names |
| `product_categories` | ARRAY | Ordered recommended product categories |
| `product_skus` | ARRAY | Ordered recommended product SKUs/IDs |
| `nbp_1` | VARCHAR | Top-1 recommended product name |
| `nbp_1_sku` | VARCHAR | Top-1 recommended product SKU |
| `nb_category_1` | VARCHAR | Top-1 recommended product category |
| `nbp_2`, `nbp_2_sku`, `nb_category_2` | VARCHAR | Top-2 recommendation (and so on up to `max_recommended_items`) |

## Configuration Reference

See `SKILL.md` and `workflow-setup/references/workflow_setup_guide.md` for the full configuration workflow, and `workflow-setup/references/` for:
- `requirements_doc.md` — full requirements gathering workflow
- `yaml_structure.md` — complete parameter reference
- `input_params_template.yml` — working example config
- `gap_analysis.md` — hive vs automl feature comparison

## Deployment

### Copy and Configure

```bash
# Copy the bundled template into the working copy (skip if it already exists)
dest="agent_outputs/<customer_slug>/nbp/workflow"
mkdir -p "$dest"
[ -d "$dest/nbp_prod" ] || cp -R "<solution_dir>/project_templates/nbp_prod" "$dest/"

# Place generated params.yml
cp config/params.yml config/params.yml.template
# Write new config to config/params.yml

# Set workflow secret (required for automl and dashboard)
tdx wf secrets set next_best_product td.apikey=<TD_API_KEY>   # use the confirmed project name; the user runs this themselves (`! ...`) so the key never appears in chat
```

### Push and Run

```bash
# First time
( cd "agent_outputs/<customer_slug>/nbp/workflow/nbp_prod" && tdx wf push -y )   # tdx.json in the working copy names the project — see workflow-setup/references/deploy_instructions.md
( cd "agent_outputs/<customer_slug>/nbp/workflow/nbp_prod" && tdx wf push -y )

# Run
tdx wf run next_best_product.nbp_launch
```

### Custom SQL Files (If Needed)

Only required when `exclusion_values: query`:
- `queries/create_transaction_table_filters.sql` — training exclusion logic
- `queries/filter_products_recs.sql` — recommendation exclusion logic

## Operational Runbook

### Running the Workflow

```bash
tdx wf run nbp_launch
tdx wf sessions nbp_launch --status running
```

### Monitoring

```bash
tdx wf timeline nbp_launch --follow
tdx wf attempt <id> tasks
tdx wf attempt <id> logs +failed_task
```

### Validate Output

```sql
-- Check output tables exist
SHOW TABLES IN sink_database LIKE 'nbp_%';

-- Validate user master table
SELECT COUNT(*) AS total_users FROM sink_database.nbp_user_master;
SELECT * FROM sink_database.nbp_user_master LIMIT 10;

-- Check recommendation coverage
SELECT
  COUNT(*) AS total_users,
  COUNT(CASE WHEN nbp_1 IS NOT NULL THEN 1 END) AS users_with_recs,
  COUNT(DISTINCT nbp_1) AS distinct_top1_items
FROM sink_database.nbp_user_master;
```

### Common Failure Points

| Problem | Action |
|---------|--------|
| Column not found | Verify column names with `DESCRIBE in_db.table_name`, update `params.yml` |
| Automl API returns 401/403 | `tdx wf secrets set next_best_product td.apikey=<TD_API_KEY>` with valid key |
| Automl API returns 404 | Wrong `ml_batch_api_endpoint` for site |
| Dashboard creation fails | Verify `td.apikey` is set and `dash_params.api_endpoint` is correct |
| Item info join returns zero rows | Check item ID types — values must match after VARCHAR cast |
| Test set shows zero matches | Adjust `test_params.test_lookback` period |
| User master table is empty | Check exclusion filter impact — too aggressive filtering |
| Too few items (< 10) or users (< 100) | NBP needs sufficient diversity in training data |

### Re-running After Config Change

1. Update `config/params.yml`
2. `tdx wf push -y` to deploy changes
3. `tdx wf run nbp_launch` to execute with new config
4. Verify output tables have expected row counts

### Scheduling

```bash
tdx wf schedule --set nbp_launch --cron "0 6 * * 1"
```

### API Key Rotation

```bash
tdx wf secrets set next_best_product td.apikey=<NEW_API_KEY>   # use the confirmed project name; the user runs this themselves (`! ...`) so the key never appears in chat
```

## Dashboard

### Dashboard Tables

| Table | Description |
|-------|-------------|
| `{prefix}dash_final_recs_stats_daily` | Recommendation distribution per rank |
| `{prefix}dash_most_ordered_items` | Historical item ordering frequency |
| `{prefix}dash_item_category_mapping_agg` | Item catalog summary by category |
| `{prefix}dash_model_param_stats_agg` | Model run metadata and summary stats |
| `{prefix}dash_similarity_stats_agg` | Item-item similarity pairs (hive only) |
| `{prefix}dash_testset` | Test set precision/recall histograms (if enabled) |
| `{prefix}dash_testset_numbers` | Test set aggregate metrics (if enabled) |
| `{prefix}global_session_filter` | Session index — join hub for filtering by run |

### Suggested Dashboard Layout

| Tab | Tables Used | Charts |
|-----|------------|--------|
| **Overview** | `dash_most_ordered_items`, `dash_model_param_stats_agg` | KPI cards (users with recs, distinct items, coverage), most ordered items bar chart |
| **Item Analysis** | `dash_item_category_mapping_agg`, `dash_most_ordered_items` | Category distribution pie chart, full item catalog table |
| **Recommendations** | `dash_final_recs_stats_daily` | Top-1 recommendation distribution bar chart, category spread across ranks |
| **Model Performance** | `dash_model_param_stats_agg`, `dash_similarity_stats_agg` | Similarity score distribution, run detail card |
| **Test Set** *(if enabled)* | `dash_testset_numbers`, `dash_testset` | Precision/recall KPI cards, precision vs random baseline, histograms |

### Join Relationships

```
global_session_filter.session_id --> dash_model_param_stats_agg.session_id
global_session_filter.session_id --> dash_testset_numbers.session_id    (testset only)
global_session_filter.session_id --> dash_testset.session_id            (testset only)
```

## Customer Documentation

### Documentation Files

Write documentation files to the engagement's local docs folder:

```
agent_outputs/<customer_slug>/nbp/docs/
+-- behavior.md               (Deployment Summary)
+-- configuration_summary.md
+-- architecture.md
+-- runbook.md
+-- eval_results.md
+-- access_ownership.md
```

**Reference**: Read `references/customer_documentation.md` for full doc templates with all placeholders.

### Expected Execution Time

| Dataset Size | Hive Engine | Automl (ALS) | Automl (similar_to_latest) | Automl (popular) |
|-------------|-------------|--------------|---------------------------|-----------------|
| < 100K users | 15-30 min | 10-20 min | 5-10 min | 5-10 min |
| 100K-500K users | 30-60 min | 20-45 min | 10-20 min | 5-10 min |
| > 500K users | 60-120 min | 30-60 min (with sampling) | 15-30 min | 5-10 min |
