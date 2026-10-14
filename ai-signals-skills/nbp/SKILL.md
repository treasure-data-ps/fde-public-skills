---
name: fde-nbp
description: |
  Next Best Product (NBP) recommendation workflow for Treasure Data. Configures workflows that generate personalized product recommendations using collaborative filtering (Hivemall) or PrecisionML (ml-batch-api). Trigger on: NBP, next best product, product recommendations, ALS, item similarity, NBP workflow setup, NBP configuration, NBP runbook, NBP output tables.
---

# NBP — Next Best Product

Next Best Product workflow that generates personalized product recommendations for every user using collaborative filtering (Hivemall) or PrecisionML (ml-batch-api with ALS, similar_to_latest, or popular algorithms). Output is shaped for direct ingestion into Audience Studio as Parent Segment attribute columns.

## How to Start

Read `../shared/playbook.md` — it defines the entry point (new vs. resume), the phase sequence, and when to read each shared pattern file. Follow that flow. This file provides the NBP-specific context you need at each phase.

## Phase Summary

| Phase | What happens |
|---|---|
| Phase 1 | Data exploration — discover transaction table, verify item-level granularity |
| Phase 2 | Bootstrap `agent_outputs/` + `project_state.md` + `requirements.md` |
| Phase 3 | Copy workflow template, push minimal workflow with safe defaults, validate output tables |
| Phase 4 | Re-configure workflow from filled requirements, re-validate |
| Phase 5 | Parent Segment update + example audiences, then customer-facing documentation set |

---

## NBP-Specific Context by Phase

### Phase 1: Data Exploration

Use `tdx-skills:tdx-basic` to explore the customer's TD database.

**Step 1 — List every table in the customer database.**
Run `tdx tables "<database>.*"` to get the full table list.

**Step 2 — Find the transaction table.**
NBP requires a table with **item-level granularity** — each row represents one user interacting with one item. Look for tables named like `order_items`, `transactions`, `purchases`, `enrich_orders`, `order_lines`.

**Step 3 — Verify item-level granularity.**
Run `DESCRIBE` and `SELECT * LIMIT 10` on the candidate table. Confirm:
- A user ID column (`td_canonical_id`, `canonical_id`, `cdp_profile_id`, `user_id`, `customer_id`)
- An item ID column (`item_sku`, `product_id`, `item_id`, `sku`)
- A timestamp column (`time`, `timestamp`, `event_time`)
- Item metadata columns (`item_name`, `item_category`) — either in the same table or a separate catalog

Tables with one row per order (no item column), aggregated user summaries, or profile tables are NOT suitable as the primary source.

**Step 4 — Check item info availability.**
If `item_name` and `item_category` are not in the transaction table, find a separate catalog/product table and verify the item ID join works.

**Step 5 — Run data quality validation.**
```sql
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT <user_col>) AS unique_users,
  COUNT(DISTINCT <item_col>) AS unique_items,
  CAST(COUNT(*) AS DOUBLE) / COUNT(DISTINCT <user_col>) AS avg_interactions_per_user
FROM <database>.<table>;
```
Minimum viable thresholds: `unique_users` > 100, `unique_items` > 10, `avg_interactions_per_user` > 1.

**Step 6 — Present findings to the user before proceeding.**
Show a summary table: transaction table name, item info source, user ID column, item ID column, timestamp column, item name column, item category column, row counts. Confirm with the `AskUserQuestion` tool — never as a plain text list — with pre-populated options (e.g. "Confirm as listed", "Use a different transaction table") plus "Other" for custom input.

Do not ask workflow configuration questions (engine, top-K, exclusions, sink database) here — they belong in the Phase 2 requirements doc.

**Solution slug for this solution:** `nbp` — all outputs go to `agent_outputs/<customer_slug>/nbp/`.

### Phase 2: Requirements Doc

1. Read `../shared/local_outputs.md` — bootstrap the git-ignored `agent_outputs/` folder and derive `<customer_slug>`.
2. Read `../shared/project_state.md` — create `agent_outputs/<customer_slug>/nbp/project_state.md` now.
3. Read `../shared/requirements_doc_pattern.md` — write `agent_outputs/<customer_slug>/nbp/requirements.md`, give the user its path to share with the customer, then continue to Phase 3 — the minimal push uses safe defaults while the customer fills it in.

Doc title: `NBP Requirements - <Customer>`

Body template: `workflow-setup/references/requirements_doc.md`

Ask questions with `AskUserQuestion` (see `workflow-setup/references/requirements_doc.md` *How to ask*). Key questions the requirements doc must answer: source database, transaction table, item info table, column mappings, model engine (`hive` / `automl`), automl algorithm (`als` / `similar_to_latest` / `popular`), top-K recommendations, lookback window, exclusion filters, sink database, TD site/region.

### Phase 3: Push Minimal Workflow

For the minimal push, populate `params.yml` with what you know from Phase 1 (transaction table, column mappings, sink database, TD site). Use Phase 2 answers if already available; otherwise use safe defaults (`automl` / `als`, 5 recommendations, all history, no exclusions).

Read `workflow-setup/references/workflow_setup_guide.md` for full parameter generation instructions.
Read `workflow-setup/references/yaml_structure.md` for the parameter reference.
Read `workflow-setup/references/table_configuration.md` for per-source-type config.
Use `workflow-setup/references/input_params_template.yml` as the starting point.

**Before any push command:** Read `../shared/push_pattern_td_workflows.md` for the template copy step, the mandatory project name confirmation gate, and push mechanics, and `workflow-setup/references/deploy_instructions.md` for the NBP-specific paths and push command. Do not run `tdx wf push` or `tdx wf upload` until both have been read and the project name confirmed with the user via `AskUserQuestion`. Write `params.yml` only into the working copy `agent_outputs/<customer_slug>/nbp/workflow/nbp_prod/config/params.yml`.

After the workflow run finishes, validate output tables following instructions in `workflow-setup/references/eval.md`.


### Phase 4: Update Workflow with Customer Requirements

Almost always a new session: read `project_state.md`, then the filled `agent_outputs/<customer_slug>/nbp/requirements.md`, and present a summary of the parameter changes you plan to make before touching any files. Key areas that typically change between Phase 3 and Phase 4:

- Model engine or algorithm switch (e.g. `als` → `similar_to_latest` for recency-heavy use case)
- Lookback window (customer may want to limit to recent 180 days)
- Exclusion filters (gift cards, discontinued products, low-volume items)
- Top-K recommendation count
- `filter_viewed` toggle (exclude already-purchased items)

Read `workflow-setup/references/workflow_setup_guide.md` for update mechanics. Edit `params.yml` in the working copy, then re-push from it.
Re-run the workflow and re-validate output tables (same checks as Phase 3).

### Phase 5: Parent Segment + Customer Documentation

**Step 1 — Parent Segment attributes + example audiences.**
Read `../shared/parent_segment_update.md` for the process.
Read `prod-docs/references/parent_segment.md` for the NBP-specific attribute columns and example segment definitions. Do not read this file until the user has approved the plan.

**Step 2+ — Documentation files.**
Read `../shared/customer_docs_pattern.md` for the doc set, then `prod-docs/references/customer_documentation.md` for the NBP doc templates. All docs are written to `agent_outputs/<customer_slug>/nbp/docs/`.

NBP-specific content for each doc is in `prod-docs/references/`:

| Docs written | How |
|---|---|
| `docs/behavior.md`, `docs/configuration_summary.md`, `docs/architecture.md`, `docs/runbook.md`, `docs/eval_results.md`, `docs/access_ownership.md` | Follow `prod-docs/references/customer_documentation.md` Steps 1–6 |
| — | Use `prod-docs/references/runbook.md` and `prod-docs/references/workflow_deployment.md` as source content for architecture, deploy and operations sections |

---

## Engine Decision

| Consideration | `hive` | `automl` |
|---|---|---|
| API dependency | None — runs on Hive | Requires ml-batch-api |
| Algorithm control | Full tuning (similarity threshold, K neighbors) | Algorithm selection only |
| Cold-start handling | No built-in fallback | `popular` algorithm covers all users |
| Already-purchased filtering | Built into SQL (`NOT EXISTS`) | `filter_viewed` toggle |
| Compute | Hive cluster | ml-batch-api service |

For deeper trade-offs see `workflow-setup/references/gap_analysis.md`.

## How It Works

1. **Ingest**: Standardize transaction table (user + item + timestamp) with exclusion filters
2. **Map**: Build item-to-name/category mapping from item info table
3. **Train**: Run collaborative filtering (hive: DIMSUM similarity) or PrecisionML (automl: ALS / similar_to_latest / popular)
4. **Predict**: Generate top-K recommendations per user
5. **Enrich**: Join item names/categories, explode into per-rank columns (`nbp_1`, `nbp_1_sku`, `nb_category_1`, ...)
6. **Dashboard**: Create TI datamodel with model stats, test set evaluation, and recommendation distribution

## Companion skill

Registered as its own skill and triggers directly from user prompts:

- **`fde-nbp-insights-agent`** — query NBP dashboard tables to summarize runs, analyze recommendation coverage, explain item/category distributions, and interpret test set results, or generate the standalone NBP Summary Dashboard. Follow this companion skill whenever the user asks for dashboards or analytical deep dives after workflow setup.

## Quick Reference

- **Solution slug**: `nbp`
- **Workflow template**: `project_templates/nbp_prod/` (read-only — copy it, never edit it)
- **Working copy**: `agent_outputs/<customer_slug>/nbp/workflow/nbp_prod/`
- **Workflow project name**: `next_best_product` (default; the template has no `tdx.json` — create it per `workflow-setup/references/deploy_instructions.md`)
- **Entry point**: `nbp_launch.dig`
- **Config file**: `config/params.yml`
- **Key output**: `nbp_user_master` (per-rank recommendation columns for the Parent Segment), `dash_*` dashboard tables
