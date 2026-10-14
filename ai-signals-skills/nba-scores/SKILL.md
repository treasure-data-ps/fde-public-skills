---
name: fde-nba-scores
description: |
  NBA (Next Best Action) Engagement Scores for Treasure Data. Sets up a workflow that unions customer activity and writes per-profile Next Best Time, Next Best Channel and Next Best Campaign scores plus engagement flags (cart abandon, new visitor, recent purchase, ad engagement) for use as Parent Segment attributes, then builds a customer-specific NBA insights agent and dashboard. Trigger on: NBA, next best action, engagement scores, next best channel, next best time, next best campaign, cart abandon flag, new visitor flag, NBA workflow setup, NBA configuration, NBA runbook.
---

# NBA Engagement Scores

Unions a customer's touchpoint data (web, email, CRM, orders, …), scores every profile on **when** (time of day), **where** (channel) and **what** (campaign type) to engage, and writes one table that is added to a Parent Segment for Audience Studio segmentation.

## How to Start

Read `../shared/SKILL.md` — it defines the entry point (new vs. resume), the phase sequence, the name gates and when to read each shared pattern. Follow that flow. This file provides the NBA-specific context for each phase.

## Phase Summary

| Phase | What happens |
|---|---|
| Phase 1 | Data exploration — list and classify tables, confirm the touchpoint and conversion sources, run discovery queries |
| Phase 2 | `agent_outputs/` + `project_state.md` + `requirements.md` — then continue without waiting |
| Phase 3 | Copy the workflow template, configure from Phase 1, push, run, validate; build the customer agent draft |
| Phase 4 | Apply the customer's requirements to the config, re-push, re-run, re-validate, rebuild the agent if needed |
| Phase 5 | Parent Segment attributes + example audiences, documentation set, finalize the customer agent |

---

## NBA-Specific Context by Phase

### Phase 1: Data Exploration

Use `tdx-skills:tdx-basic`. Do not search by table-name patterns.

1. **List every table** in the customer's source database: `tdx tables "<database>.*"`.
2. **Classify each table** with `tdx describe`:

   | Bucket | Criteria |
   |---|---|
   | Activity | Profile ID + timestamp; one row per event or interaction. NBA source candidate |
   | Profile / dimension | One row per customer (master, attributes, tiers). Not a source |
   | System / output | Workflow outputs, logs, ML results, aggregates. Not a source |

3. **Keep only customer-initiated activity**, and mark each kept table as a touchpoint or a conversion source:

   | Include | Exclude |
   |---|---|
   | Pageviews, clicks, searches, add-to-cart | Bot or internal system events |
   | Email opens, clicks, unsubscribes | Email sends, deliveries, bounces |
   | Orders, purchases, reservations (conversions) | Refunds, cancellations |
   | Support tickets, chats, store visits, app sessions, surveys | ETL audit rows, pre-aggregated tables |

4. **Confirm the list with `AskUserQuestion`** — show every activity table with include/exclude, touchpoint/conversion and a one-line reason ("Confirm as listed" / "Change the list"). Do not skip this.
5. **Run the discovery queries** in `references/workflow-setup.md` §1 for each confirmed table (UTM coverage, channel values, conversion and add-to-cart patterns, event types/statuses, data date range).
6. **Record** in `project_state.md`: table, profile ID column, real event-time column, URL/referrer/path columns, UTM coverage, conversion signal, add-to-cart signal, filters needed, first/last event date.

**Solution slug:** `nba-scores` — all engagement files live in `agent_outputs/<customer_slug>/nba-scores/`.

### Phase 2: Requirements Doc

- Title: `NBA Engagement Scores Requirements - <Customer>`
- File: `agent_outputs/<customer_slug>/nba-scores/requirements.md`
- Body: `references/requirements_doc.md` (pre-fill from Phase 1)

Hand the path to the user and continue to Phase 3.

### Phase 3: Minimal Workflow + Agent Draft

1. Read `../shared/push_pattern_td_workflows.md` and `references/workflow-setup.md`.
2. Copy `project_templates/workflow_template/` to `agent_outputs/<customer_slug>/nba-scores/workflow/` and read its `README.md`.
3. **Sink-database gate** (default `td_agents`; first check it holds no `nba_*` tables from another engagement). The first run creates the database if missing (`references/workflow-setup.md` §3).
4. Edit `workflow/config/input_params.yml` in place from Phase 1 findings, following `references/workflow-setup.md` §1–2 (minimal-push rule for anything not yet answered). Set or remove the failure email and decide on the schedule in `workflow/nba_eng_launch.dig`.
5. **Project-name gate** (default `nba_eng_prod`; first check it isn't already taken), push, ask before running, run, monitor.
6. Validate with `references/workflow-setup.md` §4. If check 4 shows the paid channels or add-to-cart rule do not match, fix the config and re-run before continuing.
7. **Agent-name gate** (default `<customer_slug>-nba-scores-agent`), then build and install the draft: `../shared/customer_agent_pattern.md` + `references/agent-setup.md`. Run the draft checks there.
8. Update `project_state.md` (names, assumed defaults, validation results, agent status).

### Phase 4: Update from Customer Requirements

1. Read `project_state.md`, then the filled `requirements.md`.
2. Map the answers with the table at the end of `references/requirements_doc.md`; choose values with `references/workflow-setup.md` §2.
3. Present the planned changes; wait for approval.
4. Edit the config (and `nba_eng_launch.dig` for schedule/alert email) in `workflow/`, re-push, re-run, re-validate (§4).
5. Rebuild the agent draft if the sink database, sources or business rules changed.

### Phase 5: Parent Segment, Documentation, Final Agent

1. **Parent Segment** — `../shared/parent_segment_update.md` for the process; `references/parent_segment.md` for the attributes and example audiences — read it only after the user approves the plan.
2. **Documentation** — `../shared/customer_docs_pattern.md` + `references/docs-setup.md` → `docs/`.
3. **Finalize the agent** — `../shared/customer_agent_pattern.md` (Finalize) + `references/agent-setup.md` (Finalize). This includes filling the two skeletons `workflow-guide.template.md` (as-built workflow) and `model-setup-walkthrough.template.md` (setup decisions, validation baseline, artifacts) from the engagement files.
4. Update `project_state.md` → "complete — engagement live".

---

## How It Works

1. **Union** — every source in `aggregate_metrics_tables` is filtered, mapped to a common column set and unioned; events are sessionized and missing channels back-filled; only the most frequent channels keep their name (others → `others`).
2. **Next Best Time** — events are assigned to four dayparts; each profile gets per-daypart counts and scores and a top daypart.
3. **Next Best Channel** — each channel above a minimum share gets per-profile counts and scores; each profile gets a top channel.
4. **Flags + Next Best Campaign** — seven profile flags from conversion, paid-channel and add-to-cart rules with windows counted from the run date; the campaign type follows cart abandon → recent purchase → recent ad engagement → prospecting.
5. **Combine** — one row per profile in the final table (Parent Segment attribute table).
6. **Dashboard stats** — run config, per-source volumes and score/flag distributions appended to the `nba_dash_*` tables, which the customer agent reads.

## Quick Reference

- **Solution slug:** `nba-scores`
- **Workflow template:** `project_templates/workflow_template/` → working copy `agent_outputs/<customer_slug>/nba-scores/workflow/`
- **Agent template:** `project_templates/agent_template/` → `.claude/skills/<agent-name>/`
- **Default workflow project name:** `nba_eng_prod`
- **Entry point:** `nba_eng_launch.dig`
- **Config file:** `config/input_params.yml`
- **Key outputs:** `nba_combined_metrics_final` (Parent Segment attributes); `nba_dash_stats_summary`, `nba_dash_model_metrics`, `nba_dash_source_tables`
- **Default agent name:** `<customer_slug>-nba-scores-agent`
- **Secrets:** none
