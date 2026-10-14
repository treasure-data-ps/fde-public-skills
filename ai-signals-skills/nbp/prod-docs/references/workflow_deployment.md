# Workflow Deployment (Phase 3 reference)

Deploy the configured NBP workflow to the customer's Treasure Data account.

## Step 1: Copy the Workflow Template

Copy the bundled template into the engagement working copy (skip if it already exists — it holds the customer's edited config):

```bash
dest="agent_outputs/<customer_slug>/nbp/workflow"
mkdir -p "$dest"
[ -d "$dest/nbp_prod" ] || cp -R "<solution_dir>/project_templates/nbp_prod" "$dest/"
```

`<solution_dir>` is the NBP skill folder (`ai-signals-skills/nbp/`), resolved to an absolute path. Never edit `project_templates/` directly.

## Step 2: Place the Generated Configuration

Replace `config/params.yml` in the working copy with the configuration generated from the requirements (Phase 2).

```bash
# Back up the original template
cp config/params.yml config/params.yml.template

# Write the new config (use your editor or write tool)
```

Verify the file is valid YAML before proceeding.

## Step 3: Edit Custom SQL Files (If Needed)

Only required when `exclusion_values: query` is set in `params.yml`.

### Training Exclusion

Edit `queries/create_transaction_table_filters.sql` with the custom exclusion logic:

```sql
-- Example: exclude gift cards, memberships, and test products
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

### Recommendation Exclusion

If `exclude_product_recs: yes`, edit `queries/filter_products_recs.sql` with the recommendation-stage exclusion logic.

## Step 4: Set the Workflow Secret

Both the automl engine and dashboard creation require a TD API key stored as a workflow secret:

```bash
tdx wf secrets set next_best_product td.apikey=<TD_API_KEY>   # use the confirmed project name; the user runs this themselves (`! ...`) so the key never appears in chat
```

**This is required for**:
- `model_type: automl` — ml-batch-api authentication
- `dash_params.create_dashboard: yes` — datamodel/dashboard creation via TD API

## Step 5: Upload the Workflow

### First Time — Create the Project

```bash
( cd "agent_outputs/<customer_slug>/nbp/workflow/nbp_prod" && tdx wf push -y )   # tdx.json in the working copy names the project — see workflow-setup/references/deploy_instructions.md
```

This creates the project `next_best_product` on TD and generates a `tdx.json` file in the project directory.

### Subsequent Updates

```bash
( cd "agent_outputs/<customer_slug>/nbp/workflow/nbp_prod" && tdx wf push -y )
```

This pushes changes to the existing project (uses `tdx.json` for project identity).

## Step 6: Run the Workflow

### Manual Run

```bash
tdx wf run next_best_product.nbp_launch
```

### Monitor Execution

```bash
# List recent sessions
tdx wf sessions next_best_product

# Check the latest attempt status
tdx wf attempt <attempt_id>

# View task logs
tdx wf logs <attempt_id>
```

### Expected Execution Time

| Dataset Size | Hive Engine | Automl (ALS) | Automl (similar_to_latest) | Automl (popular) |
|-------------|-------------|--------------|---------------------------|-----------------|
| < 100K users | 15-30 min | 10-20 min | 5-10 min | 5-10 min |
| 100K-500K users | 30-60 min | 20-45 min | 10-20 min | 5-10 min |
| > 500K users | 60-120 min | 30-60 min (with sampling) | 15-30 min | 5-10 min |

## Step 7: Validate Output

After the workflow completes successfully, verify the output tables exist and contain expected data.

### Check Output Tables Exist

```sql
-- List NBP output tables
SHOW TABLES IN sink_database LIKE 'nbp_%';
```

### Validate the User Master Table

```sql
-- Row count and sample
SELECT COUNT(*) AS total_users FROM sink_database.nbp_user_master;

-- Sample output
SELECT * FROM sink_database.nbp_user_master LIMIT 10;

-- Check recommendation coverage
SELECT
  COUNT(*) AS total_users,
  COUNT(CASE WHEN nbp_1 IS NOT NULL THEN 1 END) AS users_with_recs,
  COUNT(DISTINCT nbp_1) AS distinct_top1_items
FROM sink_database.nbp_user_master;
```

### Validate Intermediate Tables

```sql
-- Transaction table (standardized input)
SELECT COUNT(*) AS rows, COUNT(DISTINCT userid) AS users, COUNT(DISTINCT itemid) AS items
FROM sink_database.nbp_transaction;

-- Item mapping table
SELECT COUNT(*) FROM sink_database.nbp_itemid_name_product_mapping;

-- Raw recommendations
SELECT COUNT(*) FROM sink_database.nbp_topk_recommended_items;
```

### Validate Dashboard Tables (If Enabled)

```sql
-- Model stats
SELECT * FROM sink_database.nbp_dash_model_param_stats_agg
ORDER BY unixtime_tstamp DESC LIMIT 1;

-- Check session filter
SELECT * FROM sink_database.nbp_global_session_filter
ORDER BY session_rnk LIMIT 5;
```

## Step 8: Configure Error Notifications (Optional)

Uncomment the `_error` block in `nbp_launch.dig` and set recipient email addresses:

```yaml
_error:
  mail>: body.txt
  subject: NBP Model Workflow failed
  to: ['team@example.com']
```

Then push the update:
```bash
( cd "agent_outputs/<customer_slug>/nbp/workflow/nbp_prod" && tdx wf push -y )
```

---

## Troubleshooting

### Workflow Fails at Transaction Table Creation

- **Cause**: Column names in `params.yml` don't match the actual table schema
- **Fix**: Verify column names with `DESCRIBE in_db.original_item_transactions_table`

### Automl API Returns 401/403

- **Cause**: Missing or invalid `td.apikey` workflow secret
- **Fix**: `tdx wf secrets set next_best_product td.apikey=<TD_API_KEY>` with a valid API key

### Automl API Returns 404 or Connection Error

- **Cause**: Wrong `ml_batch_api_endpoint` for the customer's TD site
- **Fix**: Match the endpoint to the site (see `workflow-setup/references/requirements_doc.md` Step 2 — Site / API Endpoint Mapping)

### Dashboard Creation Fails

- **Cause**: Missing `td.apikey` or wrong `api_endpoint`
- **Fix**: Verify both `td.apikey` is set and `dash_params.api_endpoint` matches the site

### Item Info Join Returns Zero Rows

- **Cause**: Item ID column values don't match between transaction and item info tables after VARCHAR cast
- **Fix**: Check actual values — e.g., `12345` vs `SKU-12345` won't match even after VARCHAR cast

### Test Set Shows Zero Matches

- **Cause**: `test_params.test_lookback` is too short or too long, or the item catalog changed significantly
- **Fix**: Try a different holdout period (e.g., `7d` instead of `30d`)

### Workflow Runs But User Master Table Is Empty

- **Cause**: All items were excluded by filters, or no users had qualifying interactions
- **Fix**: Check exclusion filter impact — run the training SQL manually and count remaining rows
