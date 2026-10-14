---
name: fde-rfm
description: |
  RFM (Recency, Frequency, Monetary) Customer Segmentation for Treasure Data. Configures workflows that union customer behavioral data from multiple sources (pageviews, orders, email, sales), compute per-profile Recency, Frequency, and Monetary scores, and segment customers into actionable groups. Trigger on: RFM, recency frequency monetary, customer segmentation, RFM workflow setup, RFM configuration, RFM runbook, RFM output tables.
---

# RFM Customer Segmentation

RFM workflow that unions customer behavioral data from multiple sources, computes per-profile Recency, Frequency, and Monetary scores using quartile-based binning, and segments customers into actionable groups for targeted marketing.

## How to Start

Read `../shared/SKILL.md` — it defines the entry point (new vs. resume), the phase sequence, and when to read each shared pattern file. Follow that flow. This file provides the RFM-specific context you need at each phase.

## Phase Summary

| Phase | What happens |
|---|---|
| Phase 1 | Data exploration — discover tables, classify by RFM source type, confirm schema |
| Phase 2 | Bootstrap `agent_outputs/`, create `project_state.md` + `requirements.md` |
| Phase 3 | Copy workflow template, push minimal workflow, validate output tables |
| Phase 4 | Re-configure workflow from filled requirements, re-validate |
| Phase 5 | Parent Segment update + example audiences, then documentation set in `docs/` |

---

## RFM-Specific Context by Phase

### Phase 1: Data Exploration

Use `tdx-skills:tdx-basic` to explore the customer's TD databases. **Do not search by table name patterns.** Instead follow these steps:

**Step 1 — List every table in the customer database.**
Run `tdx tables "<database>.*"` to get the full table list.

**Step 2 — Classify each table.**
For every table, run `tdx describe` to inspect its schema. Classify it into one of three buckets:

| Bucket | Criteria |
|---|---|
| **Activity / behavior table** | Has a user ID column + a Unix timestamp column + rows represent a one-to-many customer activity (one row = one event or interaction per customer). **Any such table is a candidate for RFM** — if it captures a meaningful customer touchpoint it contributes at minimum to Recency and Frequency. When in doubt, include it and let the customer decide. |
| **Profile / dimension table** | Has a user ID column but rows represent one record per customer (master tables, attributes, membership tiers). Not a source table. |
| **System / output table** | Workflow output, audit logs, ML result tables. Not a source table. |

**Step 3 — Within activity tables, classify by RFM source type.**
For each candidate table, determine which RFM type it maps to:

| RFM Source Type | What to look for |
|---|---|
| **Pageviews / web activity** | URL column (`td_url`, `page_url`), referrer column — web events from JS SDK. Contributes to R and F. |
| **Email events** | `event_type` column with values like open/click/send, `campaign_name` — engagement events from ESP. Contributes to R and F (exclude `sent` events). |
| **Sales / CRM interactions** | `source`, `topic`, `rep_name`, appointment or test-drive columns — offline or in-person customer touchpoints. Contributes to R and F. |
| **Orders / purchases / services** | `order_status`, `unit_price`, revenue, or `cost` column — conversion or revenue events. Contributes to R, F, and **M**. |
| **Customer touchpoint** | Any other one-to-many activity table with a timestamp (reviews, support tickets, loyalty check-ins, etc.) that doesn't fit the above. Contributes to R and F. |

**Step 4 — Present the recommended list to the user before proceeding.**
First output a markdown table directly to the user showing ALL activity tables found with: table name, RFM source type, R/F/M contributions, and a one-line reason (include or exclude). Then immediately follow with an `AskUserQuestion` call to get confirmation. The question text must be short (one sentence asking for confirmation) — do NOT embed the table inside the question string. Put the choices in the options array only (e.g. "Confirm as listed", "Exclude one or more tables"). Do not skip this step.

**Step 5 — For each confirmed source table, note down:**
- Full table name
- User ID column name (`canonical_id`, `cdp_profile_id`, `user_id`)
- Timestamp column name
- Order amount column (order tables only — `unit_price`, `total_amount`, `revenue`)
- Filter needed (order status exclusion, email send exclusion, etc.)
- Which R/F/M dimensions it contributes to

These become `input_params.yml` values.

**Solution slug:** `rfm` — all engagement files go to `agent_outputs/<customer_slug>/rfm/` (see `../shared/local_outputs.md`).

### Phase 2: Requirements Doc

Doc title: `RFM Requirements - <Customer>`

File: `agent_outputs/<customer_slug>/rfm/requirements.md`

Body template: `workflow-setup/references/requirements_doc.md`

Key questions the requirements doc must answer: unique user ID column (`canonical_id`), ID Unification status, monetary metric column (or none for non-commerce), time filter / lookback period, scoring bins (`num_bins`), business rules (order status filters, email event type filters), sink database name, archive and historical score settings.

### Phase 3: Push Minimal Workflow

**Workflow template:** `project_templates/rfm_agent/` (read-only — never edit)
**Working copy:** `agent_outputs/<customer_slug>/rfm/workflow/rfm_agent/`
**Workflow project name:** `rfm_agent`
**Entry point:** `rfm_launch.dig`
**Config file:** `config/input_params.yml` (inside the working copy)

For the minimal push, populate `input_params.yml` with what you know from Phase 1 (tables, user ID column, timestamp column, order amount column). Use Phase 2 answers if already available; otherwise use safe defaults.

Read `workflow-setup/references/workflow_setup_guide.md` for full parameter generation instructions.
Read `workflow-setup/references/yaml_structure.md` for the parameter reference.
Read `workflow-setup/references/table_configuration.md` for per-source-type config.
Use `workflow-setup/references/input_params_template.yml` as the starting point.

**Before any push command:** Read `../shared/push_pattern_td_workflows.md` for the template copy step, the mandatory project name confirmation gate, and push mechanics. RFM-specific deploy details (directory tree, run, monitor, re-deploy) are in `workflow-setup/references/deploy_instructions.md`. Do not run `tdx wf push` or `tdx wf upload` until the project name has been confirmed with the user via `AskUserQuestion`.

After the workflow run finishes, validate output tables following instructions in `workflow-setup/references/eval.md`.


### Phase 4: Update Workflow with Customer Requirements

After reading the filled requirements doc, present a summary of the parameter changes you plan to make before touching any files. Key areas that typically change between Phase 3 and Phase 4:

- Scoring bins (`num_bins`) — customer may prefer 5-bin quintile instead of 10-bin default
- Time filter / lookback period
- Adding or removing source table types
- Order status filter refinement (customer may have non-standard status values)
- Email event type filter (confirm which event types count as engagement)
- `auto_build_segments` toggle if customer wants named segment labels

Read `workflow-setup/references/workflow_setup_guide.md` for update mechanics. Edit the config in the working copy only.
Re-run the workflow and re-validate output tables (same checks as Phase 3).

### Phase 5: Parent Segment + Customer Documentation

**Step 1 — Parent Segment attributes + example audiences.**
Read `../shared/parent_segment_update.md` for the process.
Read `prod-docs/references/parent_segment.md` for the RFM-specific attribute columns and example segment definitions. Do not read this file until the user has approved the plan.

**Step 2+ — Documentation files.**
Read `../shared/customer_docs_pattern.md` for the doc set. Write them to `agent_outputs/<customer_slug>/rfm/docs/`.

RFM-specific content for each doc is in `prod-docs/references/`:

| Doc | Reference file |
|---|---|
| `docs/architecture.md` | `prod-docs/references/runbook.md` (architecture section) |
| `docs/runbook.md` | `prod-docs/references/runbook.md` |
| `docs/behavior.md` | `prod-docs/references/customer_docs.md` |
| `docs/eval_results.md` | `workflow-setup/references/eval.md` results from the final run |
| `docs/access_ownership.md` | `prod-docs/references/technical_handoff.md` |

---

## Quick Reference

- **Workflow template:** `project_templates/rfm_agent/`
- **Working copy:** `agent_outputs/<customer_slug>/rfm/workflow/rfm_agent/`
- **Workflow project name:** `rfm_agent`
- **Entry point:** `rfm_launch.dig`
- **Config file:** `config/input_params.yml`
- **Key outputs**: `rfm_output_table` (per-profile R/F/M quartiles + segment), `rfm_stats` (per-segment distribution stats), `rfm_combined_user_events` (union activity), `rfm_stats_histogram`, `rfm_stats_model_params` (dashboard tables) in the sink database
- **Scoring**: Quartile-based (1-4 scale) using 25th/50th/75th percentile boundaries
- **Solution slug**: `rfm`

## Companion skill (separate entry point)

This is registered as its own skill — it triggers directly from user prompts, no need to route through this file:

- **`fde-rfm-analysis-agent`** — query RFM output tables for segmentation, customer value, and engagement insights, or generate the standalone RFM Summary Dashboard. Follow this companion skill whenever the user asks for dashboards or analytical deep dives after workflow setup.

## How It Works

1. **Union**: Combine pageviews, email events, sales interactions, orders into `rfm_combined_user_events` (per-profile aggregation per source)
2. **Compute metrics**: For each profile — min recency_days across sources (Recency), sum of total_touchpoints (Frequency), sum of total_spend (Monetary)
3. **Score**: Assign quartile scores (1-4) using 25th/50th/75th percentile boundaries, combine into `rfm_quartile` label (e.g., `R4F3M2`)
4. **Segment**: Assign customer segments based on R/F/M quartile combinations (Champions, Loyal Customers, Cannot lose them, Lost customers, etc.)
5. **Dashboard stats**: Generate per-segment statistics, histograms, and model parameters for the TI dashboard
