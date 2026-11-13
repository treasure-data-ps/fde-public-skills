---
name: fde-nba-ai-signal
description: |
  Sets up an AI Signals Next Best Action model on Treasure Data — contextual bandits that learn from past touches and their outcomes which action works best for each customer: the next best channel, send time, campaign, or any custom action (offer, treatment, content). A workflow unions the customer's touchpoints across web, email, app and other sources (web channels from UTM parameters, traffic source or referrer), orders them into sequential touches, builds the training log and current context, optionally tunes, trains and evaluates the policy off-policy (nba_tune / nba_train / nba_predict) and writes one recommended action per customer for Parent Segment attributes, then builds the project's NBA agent and dashboard. Use it to start, set up, configure, change, re-run or resume an NBA AI Signal project and to build or rebuild its agent. Trigger on: set up NBA AI Signal, set up next best action with AI Signals, next best channel model, next best time to send model, next best campaign model, contextual bandit setup, recommend the best offer for each customer, learn the best channel from past touchpoints, channel from utm_medium, union email web and app touchpoints for NBA, nba_train, nba_predict, nba_tune, NBA AI Signal workflow, configure NBA AI Signal, NBA AI Signal data prep, rebuild the NBA AI Signal agent, resume NBA AI Signal setup, NBA AI Signal runbook. For rule-based engagement scores (best time, channel and campaign type from activity counts, no model), use fde-nba-scores instead. Once the project's NBA agent is installed, questions about its recommendations and policy value go to it.
---

# NBA AI Signal (Next Best Action)

Learns from past touches and their outcomes which channel, send time, campaign or other action works best for which customer, with the AI Signals contextual-bandit model, and writes one recommended action per customer to a Parent Segment for segmentation and activation.

## How to Start

Read `../shared/playbook.md` and follow its flow (entry point, phases, name gates, shared patterns). Read each referenced file once per conversation; in a new session, resume from `project_state.md`. This file adds the NBA AI Signal-specific context.

| Question or task | Read |
|---|---|
| Actions, reward, windows, context SQL patterns, input checks, schedules | `references/dataprep-guide.md` |
| Config values from the data, deploy, output checks, troubleshooting | `references/workflow-setup.md` |
| How the model tunes / trains / evaluates / recommends, API parameters, other policy types | `references/ai-signals-guide.md` — end the answer with its public docs link |
| Columns of an output table, queries that read it | `references/output-tables-guide.md` |
| **Setup skill vs. project agent** — results of an installed project (policy value, action mix, recommendations) | This skill only sets up and changes; results go to the installed `<project_slug>-agent` — read its `SKILL.md` and answer by its rules, or tell the user to ask it in a new chat. No agent yet → say so and offer the setup |
| Rule-based engagement scores (best time / channel / campaign type) instead of a learned policy | That is `fde-nba-scores` — say so and offer to switch |
| How Treasure AI Studio works (Work Folders, access, sharing, plugins) | Answer from what you know, then share https://docs.treasure.ai/products/ai-studio/overview |

**Exceptions to the standard flow** (`../shared/solution_standard.md` §5): Phase 1 asks the decision type and the reward first; Phase 3 writes the project's input SQL (`sql/touchpoints_union.sql`, and adapts `sql/input_features.sql`) besides the config.

## Phase Summary

| Phase | Stage | What happens |
|---|---|---|
| Phase 1 | DEV | Decision type first (channel / time / campaign / custom); list and classify tables; confirm the touchpoint sources and their channel extraction, decision touches, reward and scoring population; check UTM coverage, channel and action mix; draft `business-context.md` |
| Phase 2 | DEV | `requirements.md` with the open business-context questions — continue without waiting |
| Phase 3 | DEV | Copy the template, write the input SQL and config, push, train, recommend, validate; ask which hands-on kit to build |
| Phase 4 | DEV | Hands-on kit (agent, dashboard, interim guides); apply the customer's requirements in rounds (tuning usually turned on here) |
| Phase 5 | PROD — only when the user says the model is ready | Parent Segment attributes + example audiences, docs, final agent, final guides |

---

## NBA AI Signal-Specific Context by Phase

### Phase 1: Data Exploration

Use `tdx-skills:tdx-basic` (`tdx-skills:parent-segment-analysis` for a Parent Segment). Never search by table-name patterns.

1. **Decision** — one `AskUserQuestion` batch:
   - What to decide per customer (`nba_type`): next best channel / next best time / next best campaign / another action — offer, treatment, content (Other). Several → one project each (prefix `channel`, `time`, …).
   - Success after a touch: purchase or conversion / click or response / sign-up or booking (Other) — and whether it is yes/no or a value (order total).
   - Data location: Parent Segment (Recommended if one exists) / source databases — then ask the names.
   - Next best time: the customers' main time zone and the time slots wanted (dayparts / hours / day of week × daypart).
2. **List tables** — `tdx tables "<database>.*"` per database. Parent Segment: bootstrap `agent_outputs/` (`../shared/local_outputs.md` Step 1), then `tdx ps desc "<name>" -o agent_outputs/<project_slug>/ps_schema.json`.
3. **Classify** from one column query (not `tdx describe` per table):
   `SELECT table_schema, table_name, column_name, data_type FROM information_schema.columns WHERE table_schema IN ('<db1>', '<db2>') ORDER BY 1, 2, ordinal_position`

   | Bucket | Criteria |
   |---|---|
   | Touchpoint source | Customer ID + timestamp, one row per interaction: pageviews (URL / referrer / UTM or traffic-source columns), email events, app or push events, SMS, call center, ad clicks — each becomes one block of the union |
   | Decision log | The business's own decisions with a label and time: sends, campaign or offer assignments, treatments (decision touches for `time` / `campaign` / `custom`) |
   | Conversion source | The reward — orders, sign-ups, bookings, renewals (`is_conversion = 1` rows of the union) |
   | Profile / dimension | One row per customer — profiles, Parent Segment `customers`; stable attributes only |
   | System / output | Workflow outputs, ML results, aggregates. Not a source |

   For every web table, note the URL, referrer and any traffic-source / medium / source / campaign columns — the channel is extracted from them (`references/dataprep-guide.md` §3).

4. **Pick** (`references/dataprep-guide.md` §1–§3):

   | Decision | First push |
   |---|---|
   | `nba_type` and the action | From step 1; the action list from discovery, grouped to 2–100 labels (`min_action_share`) |
   | Union sources | Every touchpoint source that reaches the customer through a channel (`channel`); the decision log plus engagement sources (`time`, `campaign`, `custom`) |
   | Decision touches (`action_sources`) | `''` for `channel`; the sends / decision log for the others |
   | Channel extraction per web source | UTM in the URL, else in the referrer URL, else a traffic-source column, else the referrer host (§3) |
   | Reward rule + window, attribution | Per use case (§1 table); `next_touch` when customers have several touches per window |
   | Training window, context lookback | 180 days of touches, 90 days of context |
   | Scoring population | Customers with a touch in the lookback (default), or a profile table |

5. **Confirm** — show a markdown table (`nba_type`, every union source with `src_name`, ID, time column and how its channel is set, decision touches, reward rule + window + attribution, training window, scoring population, one-line reason each), then one `AskUserQuestion`: Confirm as listed / Change the decision or reward / Change the sources. Never skip.
6. **Discovery queries** — `references/workflow-setup.md` §1, all in one shell command, no subagents: source profile, UTM / traffic-source coverage and values per web source, the derived channel mix, the action mix with reward rates, ID overlap. Fewer than 2 usable actions, or no conversions → tell the user. Record caveats (UTM coverage, rare actions, actions given to one segment only); don't investigate further.
7. **Record** in `project_state.md`: decision (`nba_type`, time zone and grain), each union source (`src_name`, table, ID, time column, channel rule, filters), customer-specific UTM values that need a channel rule, decision touches, action list with rows / reward rate, grouping, reward rule + window + attribution, training window, scoring population, join-key differences, first / last event date, caveats, leakage suspects.
8. **Business context** — playbook Phase 1: fill `project_templates/agent_template/references/business-context.template.md` from steps 1–7, review with the user, continue.

**Solution slug:** `nba-ai-signal` → `agent_outputs/<project_slug>/` (`<prefix>-nba-ai-signal` with a prefix — `../shared/local_outputs.md` Step 2). Recommend a decision prefix (`offer`, `channel`) when the account may get several.

### Phase 2: Requirements Doc

- File: `agent_outputs/<project_slug>/requirements.md`, title `<Project Name> Requirements`
- Body: `references/requirements_doc.md`, pre-filled from Phase 1
- Tell the user the path in one line and continue to Phase 3.

### Phase 3: Minimal Workflow

1. Read `../shared/push_pattern_td_workflows.md` and `references/workflow-setup.md`.
2. Copy `project_templates/workflow_template/` → `agent_outputs/<project_slug>/workflow/`; read its `README.md` and `sql/README.md`.
3. **Name checks** (one command):
   - Sink database: default `td_agents`, must hold no `nba_ais_*` tables (fixed names = one project per database); taken → `nba_ais_<project_prefix>` (`-` → `_`; database and table names allow only letters, digits and `_`). Created by the first run.
   - Workflow project: default `nba_ais`, must not exist.
   - `model_name`: `<project_prefix>_nba` (`-` → `_`) — unique per account.
4. **Input SQL** (`references/workflow-setup.md` §1, patterns in `references/dataprep-guide.md` §3–§4); don't review the `.dig` files:
   - `workflow/sql/touchpoints_union.sql` — rewrite: one block per confirmed source in the union contract (`sql/README.md`), web blocks with the UTM / traffic-source extraction chosen in Phase 1, conversions with `is_conversion = 1`.
   - `workflow/sql/touchpoints.sql` — add channel rules only for customer-specific UTM values found in discovery.
   - `workflow/sql/input_features.sql` — keep the anchors, reward and output; set the per-channel feature columns to the top channels from discovery; add 1–3 source-specific features if useful (5–20 numeric features in total).
5. **Config** — edit `workflow/config.yml` in place: `sink_database`, `model_name`, `nba_type`, `time_grain`, `local_timezone`, `action_sources`, `min_action_share`, `reward_attribution`, `reward_type`, `session_gap_minutes`, `user_column`, `action_column`, `reward_column`, `timestamp_column`, `exclude_columns`, `reward_window_days`, `train_window_days`, `feature_lookback_days`, `reference_date` (stale data), `ml_batch_api_endpoint` (region); `enable_tuning: false` and template model values (`workflow-setup.md` §2). Schedule and alert email stay commented unless asked. No local validation.
6. **Approve, push, run** — `../shared/push_pattern_td_workflows.md` Step 5: show config, SQL and names; ask once; push; run `nba_ais` (several minutes); monitor. Never ask for `td.apikey` — AI Signals provides it.
7. **Validate** — `references/workflow-setup.md` §4 (+ `dataprep-guide.md` §5 if check 1 looks off). `data_prep` fails → fix the SQL, re-run. A feature that describes the action or the outcome → drop it, re-run.
8. Update `project_state.md`: names, model name, SQL summary, assumed defaults, validation results.
9. **Hands-on kit question** (playbook Phase 3 step 4): agent + dashboard + guides (Recommended) / agent + dashboard / not now.

### Phase 4: Hands-on Testing and Customer Requirements

**Part A — Hands-on kit** (per the Phase 3 answer, or on request):

1. Build and install `<project_slug>-agent`: `../shared/customer_agent_pattern.md` Steps 1–3 + `references/agent-setup.md`.
2. Generate the dashboard; run the build checks in `references/agent-setup.md`.
3. Guides chosen → fill `workflow-guide.md` and `model-setup-walkthrough.md` as **interim** (`customer_agent_pattern.md` Step 4); reinstall.
4. Show the **agent files** table (`agent-setup.md`) and a starter prompt; update `project_state.md`.

**Part B — Customer requirements** (when `requirements.md` returns; repeat as needed):

1. Read `project_state.md`, then the filled `requirements.md`.
2. Map answers with the table in `references/requirements_doc.md`; values from `workflow-setup.md` §2, `dataprep-guide.md` (actions and reward §1, windows §2, schedules §6), `ai-signals-guide.md` §5 (policy, tuning, propensities).
3. Present planned SQL and config changes; wait for approval. Offer `enable_tuning: true` once the actions and reward are confirmed and the account has `nba_tune`.
4. Edit `workflow/` (`sql/input_features.sql`, `config.yml`, schedules in `train.dig` / `predict.dig` or `nba_ais.dig`), re-push, re-run, re-validate; compare with the previous run in `project_state.md`.
5. Merge business answers into `business-context.md`.
6. Refresh the kit: rebuild the agent if the sink database, recommendations table, decision or business rules changed; regenerate the dashboard and interim guides. Log the round under **Phase 4 iterations**; offer another round — never Phase 5.

### Phase 5: Parent Segment, Documentation, Final Agent

Only after the user says the model is ready and confirms the move.

1. **Parent Segment** — process: `../shared/parent_segment_update.md`; attributes and audiences: `references/parent_segment.md` (read after the plan is approved).
2. **Docs** — `../shared/customer_docs_pattern.md` + `references/docs-setup.md` → `docs/`. Customer docs in business language for non-technical readers (`docs-setup.md` writing style).
3. **Confirm the business context** — playbook Phase 5 step 3.
4. **Finalize the agent** — `customer_agent_pattern.md` Step 5 + `agent-setup.md` (Finalize); build it first if Part A was skipped.
5. **Final guides question** — update (or create) both guides with the production setup (Recommended); on yes, `customer_agent_pattern.md` Step 4 (final) and reinstall.
6. `project_state.md` → "complete — engagement live".

---

## How It Works

| Step | What happens |
|---|---|
| Data prep | `sql/touchpoints_union.sql` unions every source (web, email, app, orders …); `sql/touchpoints.sql` sets a channel per event (source → UTM → referrer), inherits it within a session and collapses consecutive same-channel events into sequential touches; `sql/input_features.sql` builds the training log — one row per decision touch in the `train_window_days` before `run date − reward_window_days`, the action per `nba_type` (channel / local time slot / campaign / custom label), its reward until the next touch or `reward_window_days`, numeric context from the `feature_lookback_days` before it — and the scoring table: one row per customer, context at the run date |
| Tune (optional) | `nba_tune`: time-split, cross-validated off-policy search over preprocessing, estimator and policy; trials appended to `nba_ais_tuning_results` |
| Train | `nba_train`: contextual-bandit policy (`lin_ucb` default, or the tuned choice), off-policy estimate of its value vs the logged reward; stored under `model_name`; logged to `nba_ais_run_log` / `nba_ais_train_metrics` |
| Predict | `nba_predict`: one action per customer → `pred_output_table` (Parent Segment table), `<pred_output_table>_history`, `nba_ais_action_stats` |
| Explain | The project agent and dashboard read the run log, tuning results, action mix and recommendations |

## Quick Reference

| Item | Value |
|---|---|
| Solution slug / short name | `nba-ai-signal` / `NBA AI Signal` (e.g. `Offer NBA AI Signal`) |
| Workflow template | `project_templates/workflow_template/` → `agent_outputs/<project_slug>/workflow/` |
| Agent template | `project_templates/agent_template/` → `.claude/skills/<agent-name>/` |
| Workflow project / entry point | `nba_ais` / `nba_ais.dig` (train → predict); `train.dig`, `predict.dig` run alone |
| Config / project code | `config.yml` / `sql/touchpoints_union.sql` (rewritten per project), `sql/input_features.sql` (context adapted) |
| Decision types | `nba_type`: `channel`, `time` (`daypart`, `hour`, `dow_daypart`), `campaign`, `custom` |
| Model | AI Signals `nba_tune` (optional) / `nba_train` / `nba_predict`; `lin_ucb`, `lin_ts`, `lin_eps_greedy`, `ipw_learner` |
| Key outputs | `pred_output_table` (Parent Segment, default `nba_ais_actions`), `<pred_output_table>_history`, `nba_ais_*` (fixed names) |
| Agent name | `<project_slug>-agent` (`nba-ai-signal-agent` by default) |
| Secrets | None — `${secret:td.apikey}` is provided by AI Signals |
| API endpoint | `ml_batch_api_endpoint` — US default; regions in the template README |
