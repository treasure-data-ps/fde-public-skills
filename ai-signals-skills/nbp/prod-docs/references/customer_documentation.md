# Phase 5: Customer Documentation

Write the NBP documentation set as local markdown files to `agent_outputs/<customer_slug>/nbp/docs/` (see `../../../shared/local_outputs.md` and `../../../shared/customer_docs_pattern.md`). Fill every `[placeholder]` from `project_state.md`, `requirements.md`, and the deployed config in `agent_outputs/<customer_slug>/nbp/workflow/nbp_prod/config/params.yml`.

## Doc Set

NBP uses the shared doc set plus one NBP-specific extra file:

```
agent_outputs/<customer_slug>/nbp/docs/
├── behavior.md               ← Step 1: Deployment Summary (customer)
├── configuration_summary.md  ← Step 2: Configuration Summary (customer, NBP-specific extra)
├── architecture.md           ← Step 3: Architecture & Output Schema (customer)
├── runbook.md                ← Step 4: Runbook & Maintenance (internal)
├── eval_results.md           ← Step 5: validation results from workflow-setup/references/eval.md (customer)
└── access_ownership.md       ← Step 6: per ../../../shared/customer_docs_pattern.md (internal)
```

Start each file with its audience marker (`> Audience: customer` or `> Audience: internal`) per the shared pattern.

---

## Step 1: Write the Deployment Summary (`docs/behavior.md`)

Write with the Write tool to `agent_outputs/<customer_slug>/nbp/docs/behavior.md`.

### Deployment Summary Template

Use this as the file body. Fill in all `[placeholders]` with actual values from the deployment.

```markdown
> Audience: customer

# NBP Deployment Summary - [Customer]

We deployed a Next Best Product (NBP) recommendation workflow for [customer name] using the **[hive/automl]** engine.

## Key Facts

| | |
|---|---|
| **Source data** | `[in_db].[original_item_transactions_table]` |
| **Users** | [X] distinct users |
| **Items** | [Y] distinct items |
| **Total interactions** | [Z] rows |
| **Model type** | [hive / automl ([algorithm])] |
| **Recommendations per user** | [max_recommended_items] |
| **Output table** | `[sink_database].[user_master_attr_table]` |
| **Dashboard** | [yes/no] |
| **TD Site** | [site] |
| **Deployed** | [date] |

## Output Columns

The final table `[user_master_attr_table]` contains:

| Column | Description |
|--------|-------------|
| `[user_id_column]` | User identifier |
| `nbp_1` | Top-1 recommended product name |
| `nbp_1_sku` | Top-1 recommended product SKU |
| `nb_category_1` | Top-1 recommended product category |
| `nbp_2`, `nbp_2_sku`, `nb_category_2` | Top-2 recommendation |
| ... | up to `nbp_[N]` |
| `product_recommendations` | Full array of recommended product names |
| `product_skus` | Full array of recommended product SKUs |
| `product_categories` | Full array of recommended product categories |

## Related Docs

- **Configuration Summary** (`configuration_summary.md`) — Source tables, column mappings, model parameters, exclusion filters
- **Architecture & Output Schema** (`architecture.md`) — Data flow, intermediate tables, output schema
- **Runbook & Maintenance** (`runbook.md`) — How to run, modify, troubleshoot, and maintain
```

---

## Step 2: Write the Configuration Summary (`docs/configuration_summary.md`)

Write to `agent_outputs/<customer_slug>/nbp/docs/configuration_summary.md`.

### Configuration Summary Template

```markdown
> Audience: customer

# NBP Configuration Summary - [Customer]

## Source Tables

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Database | `[in_db]` | Customer's [golden/staging/production] database |
| Transaction table | `[original_item_transactions_table]` | Contains item-level purchase history ([X] rows, [Y] users, [Z] items) |
| Item info table | `[original_item_info_table]` | [Same table as transactions / Separate catalog table] |

## Column Mappings

| Role | Column Name | Source Table |
|------|-------------|-------------|
| User ID | `[original_user_id_column_name]` | Transaction table |
| Item ID | `[original_item_id_column_name]` | Transaction table |
| Item Name | `[original_item_name_column_name]` | Item info table |
| Item Category | `[original_item_category_column_name]` | Item info table |
| Timestamp | `[original_timestamp_name]` | Transaction table |

## Model Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Model type | `[hive/automl]` | [Reason for choice] |
| Algorithm | `[als/similar_to_latest/popular]` | [Reason] (automl only) |
| Recommendations per user | `[max_recommended_items]` | |
| Orders lookback | `[orders_lookback]` | [All history / last N days] |
| ALS sample rate | `[als_sample_rate]` | (automl+ALS only) |
| ALS max users | `[als_max_users]` | (automl+ALS only) |
| Filter viewed | `[filter_viewed]` | (automl only) |

### Hive Engine Parameters (if model_type = hive)

| Parameter | Value |
|-----------|-------|
| `topk_similar_items` | [value] |
| `recent_items` | [value] |
| `max_recommended_items` | [value] |
| `min_cooccurence_filter` | [value] |
| `dimsum_similarity_threshold` | [value] |

## Exclusion Filters

| Filter | Method | Details |
|--------|--------|---------|
| Training exclusion | [regex/query] | [What was excluded and why] |
| Recommendation exclusion | [regex/query/none] | [What was excluded and why] |

[If using custom SQL, include the SQL logic here]

## Dashboard

| Parameter | Value |
|-----------|-------|
| Create dashboard | `[yes/no]` |
| API endpoint | `[api_endpoint]` |
| Workflow secret | `td.apikey` is set (do not include the actual key) |

## Output Tables

| Table | Description |
|-------|-------------|
| `[sink_database].[user_master_attr_table]` | Final recommendations with per-rank columns |
| `[sink_database].[prefix]transaction` | Standardized transaction table |
| `[sink_database].[prefix]topk_recommended_items` | Raw recommendation arrays |
| `[sink_database].[prefix]dash_*` | Dashboard aggregation tables |
```

---

## Step 3: Write the Architecture & Output Schema (`docs/architecture.md`)

Write to `agent_outputs/<customer_slug>/nbp/docs/architecture.md`.

### Architecture Template

```markdown
> Audience: customer

# NBP Architecture & Output Schema - [Customer]

## Data Flow

1. **Source**: `[in_db].[transaction_table]`
   - Raw item-level transactions (user + item + timestamp)

2. **Preprocessing**: `[prefix]transaction`
   - Columns standardized to `userid`, `itemid`, `tstamp`
   - Exclusion filters applied: [describe what was filtered]
   - Time filter: [all history / last N days]

3. **Model Training** ([hive/automl]):
   [For hive]:
   - Co-occurrence matrix computed from user-item interactions
   - DIMSUM algorithm calculates approximate cosine similarity between items
   - Top [topk_similar_items] similar items retained per item

   [For automl]:
   - Data sent to ml-batch-api (`[ml_batch_api_endpoint]`)
   - [ALS/similar_to_latest/popular] algorithm trained and predictions generated

4. **Prediction**: `[prefix]topk_recommended_items`
   - [max_recommended_items] recommendations generated per user
   - Raw output: `userid` + `rec_items` array

5. **Enrichment**: `[user_master_attr_table]`
   - Item names and categories joined from `[original_item_info_table]`
   - Per-rank columns exploded: `nbp_1`, `nbp_1_sku`, `nb_category_1`, `nbp_2`, ...

6. **Dashboard**: `[prefix]dash_*` tables
   - Aggregation tables for TD Insights visualization
   - Test set evaluation results ([enabled/disabled])

## Intermediate Tables

All tables use prefix `[prefix]` in database `[sink_database]`.

| Table | Engine | Description |
|-------|--------|-------------|
| `[prefix]transaction` | Both | Standardized transactions |
| `[prefix]itemid_name_product_mapping` | Both | Item ID to name/category mapping |
| `[prefix]user_item` | Both | Aggregated user-item interactions |
| `[prefix]item_similarity` | Hive only | Item-item DIMSUM similarity scores |
| `[prefix]topk_similar_items` | Hive only | Top-K neighbors per item |
| `[prefix]recent_item_contacts` | Hive only | Each user's recent purchases |
| `[prefix]topk_recommended_items` | Both | Raw recommendations |
| `[user_master_attr_table]` | Both | Final output with per-rank columns |
| `[prefix]dash_*` | Both | Dashboard tables |
| `[prefix]testset` | Both | Test set results (if enabled) |

## Final Output Schema

| Column | Type | Description |
|--------|------|-------------|
| `[user_id_column]` | VARCHAR | User identifier |
| `nbp_ranks` | ARRAY | Rank indices |
| `product_recommendations` | ARRAY | Ordered recommended product names |
| `product_categories` | ARRAY | Ordered product categories |
| `product_skus` | ARRAY | Ordered product SKUs |
| `nbp_1` | VARCHAR | Top-1 recommended product name |
| `nbp_1_sku` | VARCHAR | Top-1 recommended product SKU |
| `nb_category_1` | VARCHAR | Top-1 recommended category |
| ... | ... | Up to nbp_[max_recommended_items] |
```

---

## Step 4: Write the Runbook & Maintenance (`docs/runbook.md`)

Write to `agent_outputs/<customer_slug>/nbp/docs/runbook.md`.

### Runbook Template

````markdown
> Audience: internal

# NBP Runbook & Maintenance - [Customer]

## Running the Workflow

### Manual Run

```
tdx wf run next_best_product.nbp_launch
```

### Monitoring

```
# List recent sessions
tdx wf sessions next_best_product

# View logs for a specific attempt
tdx wf logs <attempt_id>
```

### Scheduling

Configure recurring runs in the TD console or via CLI:
```
tdx wf schedule --set nbp_launch --cron "0 6 * * 1"
```

## Modifying Parameters

1. Edit `config/params.yml` in the workflow working copy (`agent_outputs/[customer_slug]/nbp/workflow/nbp_prod/`)
2. Push changes from the working copy: `( cd "agent_outputs/<customer_slug>/nbp/workflow/nbp_prod" && tdx wf push -y )` (`tdx.json` there names the project)
3. Re-run the workflow

### Common Changes

| Change | Parameter to Edit |
|--------|-------------------|
| Add/remove exclusion filters | `exclusion_values` or custom SQL files |
| Change lookback period | `orders_lookback` |
| Change number of recommendations | `max_recommended_items` |
| Switch algorithm (automl) | `automl_model_type` |

### Updating Source Data

If the source table name or column names change:
1. Update the corresponding parameters in `config/params.yml`
2. Push and re-run

## Re-running After Failure

```
# Check what failed
tdx wf logs <attempt_id>

# Retry from the failed task
tdx wf retry <attempt_id>

# Or start a fresh run
tdx wf run next_best_product.nbp_launch
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Workflow fails at transaction table creation | Column names changed in source table | Verify with `DESCRIBE` and update `params.yml` |
| Automl API returns 401/403 | Expired or missing API key secret | `tdx wf secrets set next_best_product td.apikey=<NEW_KEY>` |
| Dashboard not updating | API endpoint mismatch or stale secret | Verify `dash_params.api_endpoint` and re-set secret |
| User master table has fewer users than expected | Exclusion filters too aggressive | Review exclusion settings, check filter impact |
| Test set shows zero matches | Holdout period mismatch | Adjust `test_params.test_lookback` |
| Recommendations are all the same item | Too few items or threshold too high | Check item count, adjust `dimsum_similarity_threshold` (hive) |

## Maintenance

### When to Retrain

- **Weekly or bi-weekly** is typical for most e-commerce use cases
- More frequently if the product catalog changes rapidly
- Less frequently for stable catalogs (monthly)

### When to Update Configuration

- New product categories added that should be excluded
- Source table schema changes (column renames)
- Business requirements change (more/fewer recommendations per user)
- Switching from hive to automl or vice versa

### Monitoring

- Check the dashboard after each run for coverage and test set metrics
- Alert on workflow failures via the `_error` email notification
- Monitor `users_with_recs` trend — a sudden drop may indicate data issues

### API Key Rotation

If the TD API key is rotated:
```
tdx wf secrets set next_best_product td.apikey=<NEW_API_KEY>   # use the confirmed project name; the user runs this themselves (`! ...`) so the key never appears in chat
```

### Updating the Workflow Code

The workflow code lives in the working copy at `agent_outputs/[customer_slug]/nbp/workflow/nbp_prod/`. To adopt a newer NBP template version, diff the template (`project_templates/nbp_prod/` in the NBP skill) against the working copy, port the changes while keeping your `config/params.yml`, then push from the working copy:
```
( cd "agent_outputs/<customer_slug>/nbp/workflow/nbp_prod" && tdx wf push -y )
```
````

---

---

## Step 5: Write the Eval Results (`docs/eval_results.md`)

Write to `agent_outputs/<customer_slug>/nbp/docs/eval_results.md` (`> Audience: customer`): the results of each check in `../../workflow-setup/references/eval.md` from the final production run (row counts, coverage rates, test set precision/recall vs baseline, pass/fail per check), the run date, and known limitations.

## Step 6: Write Access & Ownership (`docs/access_ownership.md`)

Write to `agent_outputs/<customer_slug>/nbp/docs/access_ownership.md` (`> Audience: internal`) with the content listed in `../../../shared/customer_docs_pattern.md`.

## Step 7: Update Project State

Update `agent_outputs/<customer_slug>/nbp/project_state.md`: Phase 5 complete, list all doc paths, status "engagement live". Tell the user the `docs/` path and which files are customer-facing.

---

## Delivery Checklist

Before handing off to the customer, confirm:

- [ ] All doc files written to `agent_outputs/<customer_slug>/nbp/docs/`
- [ ] All `[placeholders]` replaced with actual values
- [ ] Configuration summary matches the deployed `params.yml`
- [ ] Architecture overview matches actual data flow
- [ ] Runbook commands are tested and working
- [ ] Dashboard is accessible and shows correct data
- [ ] Troubleshooting guide covers the most common failure modes
- [ ] Maintenance schedule is discussed and agreed
- [ ] Customer team has access to the workflow project in TD
- [ ] Customer team knows how to re-run and modify parameters
- [ ] API key secret is set and documented (not the actual key)
