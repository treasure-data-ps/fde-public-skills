---
name: fde-rfm
description: |
  RFM (Recency, Frequency, Monetary) Customer Segmentation for Treasure Data. Sets up a workflow that unions customer activity from multiple sources (pageviews, orders, email, sales), scores every profile on Recency, Frequency and Monetary value (AI Signals or SQL quartile scoring), assigns one of ten customer segments for use as Parent Segment attributes, then builds a customer-specific RFM insights agent and dashboard. Trigger on: RFM, recency frequency monetary, customer segmentation, RFM segments, champions, at-risk customers, RFM workflow setup, RFM configuration, RFM runbook, RFM output tables.
---

# RFM Customer Segmentation

Unions a customer's activity data (web, email, CRM, orders, …), scores every profile on **how recently**, **how often** and **how much** they engage and buy, and writes one table with R/F/M scores and a segment per profile, which is added to a Parent Segment for Audience Studio segmentation.

## How to Start

Read `../shared/playbook.md` — it defines the entry point (new vs. resume), the phase sequence, the name gates and when to read each shared pattern. Follow that flow. This file provides the RFM-specific context for each phase.

## Phase Summary

| Phase | What happens |
|---|---|
| Phase 1 | Data exploration — list and classify tables, confirm the activity sources and which feed Monetary, run discovery queries |
| Phase 2 | `agent_outputs/` + `project_state.md` + `requirements.md` — then continue without waiting |
| Phase 3 | Copy the workflow template, configure from Phase 1, push, run, validate; build the customer agent draft |
| Phase 4 | Apply the customer's requirements to the config, re-push, re-run, re-validate, rebuild the agent if needed |
| Phase 5 | Parent Segment attributes + example audiences, documentation set, finalize the customer agent |

---

## RFM-Specific Context by Phase

### Phase 1: Data Exploration

Use `tdx-skills:tdx-basic`. Do not search by table-name patterns.

1. **List every table** in the customer's source database: `tdx tables "<database>.*"`.
2. **Classify each table** with `tdx describe`:

   | Bucket | Criteria |
   |---|---|
   | Activity | Profile ID + timestamp; one row per event or interaction. RFM source candidate — any meaningful customer touchpoint adds to Recency and Frequency; when in doubt, include it and let the customer decide |
   | Profile / dimension | One row per customer (master, attributes, tiers). Not a source |
   | System / output | Workflow outputs, logs, ML results, aggregates. Not a source |

3. **Keep only customer-initiated activity**, and mark each kept table with the dimensions it feeds (R, F; plus M if it carries a purchase value):

   | Include | Exclude |
   |---|---|
   | Pageviews, clicks, searches | Bot or internal system events |
   | Email opens, clicks, replies, form fills | Email sends, deliveries, bounces |
   | Orders, purchases, services with a value (adds M) | Refunds, cancellations, returns |
   | Sales / CRM interactions, support tickets, store visits, app sessions, reviews | ETL audit rows, pre-aggregated tables |

4. **Confirm the list with `AskUserQuestion`** — first show a markdown table of every activity table with include/exclude, R/F/M contribution and a one-line reason, then ask one short question ("Confirm as listed" / "Change the list"). Do not put the table inside the question. Do not skip this.
5. **Run the discovery queries** in `references/workflow-setup.md` §1 yourself (no subagents): one `UNION ALL` profile query across all confirmed tables, then status / event-type breakdowns as parallel calls. Do not investigate caveats further — record them (step 6).
6. **Record** in `project_state.md`: table, profile ID column, real event-time column, order value column (monetary sources), context column, filters needed, R/F/M contribution, first/last event date.

**Solution slug:** `rfm` — all engagement files live in `agent_outputs/<customer_slug>/rfm/`.

### Phase 2: Requirements Doc

- Title: `RFM Requirements - <Customer>`
- File: `agent_outputs/<customer_slug>/rfm/requirements.md`
- Body: `references/requirements_doc.md` (pre-fill from Phase 1)

Hand the path to the user and continue to Phase 3.

### Phase 3: Minimal Workflow + Agent Draft

1. Read `../shared/push_pattern_td_workflows.md` and `references/workflow-setup.md`.
2. Copy `project_templates/workflow_template/` to `agent_outputs/<customer_slug>/rfm/workflow/` and read its `README.md`.
3. **Sink-database gate** (default `td_agents`; first check it holds no `rfm_*` tables from another engagement). The first run creates the database if missing (`references/workflow-setup.md` §3).
4. Edit `workflow/config/input_params.yml` in place from Phase 1 findings, following `references/workflow-setup.md` §1–2 (minimal-push rule for anything not yet answered). Leave the schedule and failure email in `workflow/rfm_launch.dig` commented unless the user asks for them.
5. **Project-name gate** (default `rfm_ais`; first check it isn't already taken), push. Ask before running, run, monitor. With `globals.model_type: ai_signals`, no secret is needed up front — only if scoring fails with 401/403, ask the user to set `td.apikey` themselves (`references/workflow-setup.md` §3).
6. Validate with `references/workflow-setup.md` §4. If check 2 or 4 shows a missing monetary source or a source with no rows, fix the config and re-run before continuing.
7. Continue straight here after validation — the agent draft is part of Phase 3, also for a "basic" setup. **Agent-name gate** (default `<customer_slug>-rfm-agent`), then build and install the draft: `../shared/customer_agent_pattern.md` + `references/agent-setup.md`. Run the draft checks there.
8. Update `project_state.md` (names, scoring model, assumed defaults, validation results, agent status).

### Phase 4: Update from Customer Requirements

1. Read `project_state.md`, then the filled `requirements.md`.
2. Map the answers with the table at the end of `references/requirements_doc.md`; choose values with `references/workflow-setup.md` §2.
3. Present the planned changes; wait for approval.
4. Edit the config (and `rfm_launch.dig` for schedule/alert email) in `workflow/`, re-push, re-run, re-validate (§4).
5. Rebuild the agent draft if the sink database, sources or business rules changed.

### Phase 5: Parent Segment, Documentation, Final Agent

1. **Parent Segment** — `../shared/parent_segment_update.md` for the process; `references/parent_segment.md` for the attributes and example audiences — read it only after the user approves the plan.
2. **Documentation** — `../shared/customer_docs_pattern.md` + `references/docs-setup.md` → `docs/`.
3. **Finalize the agent** — `../shared/customer_agent_pattern.md` (Finalize) + `references/agent-setup.md` (Finalize). This includes filling the two skeletons `workflow-guide.template.md` (as-built workflow) and `model-setup-walkthrough.template.md` (setup decisions, validation baseline, artifacts) from the engagement files.
4. Update `project_state.md` → "complete — engagement live".

---

## How It Works

1. **Union** — every source in `aggregate_metrics_tables` is filtered and aggregated to one row per profile per source: last event, number of touchpoints, total spend, days since the last event.
2. **Compute R/F/M** — per profile: Recency = the lowest days-since-last-event across sources; Frequency = the sum of touchpoints; Monetary = the sum of spend (never below 0).
3. **Score** — `ai_signals` (default) sends the input table to the AI Signals batch API; `custom` assigns 1–4 quartile scores in SQL from the 25th/50th/75th percentiles. Both write `r_quartile`, `f_quartile`, `m_quartile`, `rfm_quartile` (e.g. `R4F3M2`), `rfm_score`.
4. **Segment** — each profile gets one of ten segments (Champions, Loyal Customers, Potential Loyalists, Promising, New Customers, Cannot lose them, Need attention, Hibernating, High Value Sleeping, Lost customers).
5. **Dashboard stats** — per-segment stats and histograms for the latest run, plus run config and segment stats appended every run, which the customer agent reads.

## Quick Reference

- **Solution slug:** `rfm`
- **Workflow template:** `project_templates/workflow_template/` → working copy `agent_outputs/<customer_slug>/rfm/workflow/`
- **Agent template:** `project_templates/agent_template/` → `.claude/skills/<agent-name>/`
- **Default workflow project name:** `rfm_ais`
- **Entry point:** `rfm_launch.dig`
- **Config file:** `config/input_params.yml`
- **Scoring model:** `globals.model_type` — `ai_signals` (default, `rfm_ai_signals.dig`) or `custom` (`rfm_custom.dig`)
- **Key outputs:** `rfm_output_table` (Parent Segment attributes); `rfm_stats`, `rfm_stats_histogram`, `rfm_stats_model_params`, `rfm_stats_daily_agg`
- **Default agent name:** `<customer_slug>-rfm-agent`
- **Secrets:** `td.apikey` read by `ai_signals` — usually provided by TD Workflow; set only on 401/403
