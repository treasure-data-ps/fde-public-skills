---
name: fde-nba-ai-signal
description: |
  Sets up an AI Signals Next Best Action model on Treasure Data — contextual bandits that learn from a log of past actions (offers, campaigns, messages, channels, treatments) and their outcomes which action works best for each customer: a workflow that builds the project's action-log and current-context tables, optionally tunes, trains and evaluates the policy off-policy (nba_tune / nba_train / nba_predict) and writes one recommended action per customer for Parent Segment attributes, then builds the project's NBA agent and dashboard. Use it to start, set up, configure, change, re-run or resume an NBA AI Signal project and to build or rebuild its agent. Trigger on: set up NBA AI Signal, set up next best action with AI Signals, contextual bandit setup, recommend the best offer for each customer, which campaign to send each customer, learn the best action from past campaigns, offer optimization model, nba_train, nba_predict, nba_tune, NBA AI Signal workflow, configure NBA AI Signal, NBA AI Signal data prep, rebuild the NBA AI Signal agent, resume NBA AI Signal setup, NBA AI Signal runbook. For rule-based engagement scores (best time, channel and campaign type from activity counts), use fde-nba-scores instead. Once the project's NBA agent is installed, questions about its recommendations and policy value go to it.
---

# NBA AI Signal (Next Best Action)

Learns from past actions and their outcomes which action works best for which customer, with the AI Signals contextual-bandit model, and writes one recommended action per customer to a Parent Segment for segmentation and activation.

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

**Exceptions to the standard flow** (`../shared/solution_standard.md` §5): Phase 1 asks the decision, the actions and the reward first; Phase 3 writes the project's input SQL (`sql/input_features.sql`) besides the config.

## Phase Summary

| Phase | Stage | What happens |
|---|---|---|
| Phase 1 | DEV | Decision first; list and classify tables; confirm the action log, actions, reward, context sources and scoring population; check the action mix and assignment; draft `business-context.md` |
| Phase 2 | DEV | `requirements.md` with the open business-context questions — continue without waiting |
| Phase 3 | DEV | Copy the template, write the input SQL and config, push, train, recommend, validate; ask which hands-on kit to build |
| Phase 4 | DEV | Hands-on kit (agent, dashboard, interim guides); apply the customer's requirements in rounds (tuning usually turned on here) |
| Phase 5 | PROD — only when the user says the model is ready | Parent Segment attributes + example audiences, docs, final agent, final guides |

---

## NBA AI Signal-Specific Context by Phase

### Phase 1: Data Exploration

Use `tdx-skills:tdx-basic` (`tdx-skills:parent-segment-analysis` for a Parent Segment). Never search by table-name patterns.

1. **Decision** — one `AskUserQuestion` batch:
   - What to decide per customer: offer / campaign or content / channel / retention treatment (Other).
   - Success after an action: purchase or conversion / click or response / redemption / retention (Other).
   - Data location: Parent Segment (Recommended if one exists) / source databases — then ask the names.
   - Note whether the actions are logged in one table (sends, assignments) or must be assembled (settled in step 5).
2. **List tables** — `tdx tables "<database>.*"` per database. Parent Segment: bootstrap `agent_outputs/` (`../shared/local_outputs.md` Step 1), then `tdx ps desc "<name>" -o agent_outputs/<project_slug>/ps_schema.json`.
3. **Classify** from one column query (not `tdx describe` per table):
   `SELECT table_schema, table_name, column_name, data_type FROM information_schema.columns WHERE table_schema IN ('<db1>', '<db2>') ORDER BY 1, 2, ordinal_position`

   | Bucket | Criteria |
   |---|---|
   | Action log | Customer ID + action label + timestamp: sends, offer assignments, coupon issues, journey steps, treatments |
   | Outcome source | Holds the reward or the data to derive it — orders, conversions, clicks, redemptions, renewals |
   | Context source | Behavior with ID + timestamp (events, orders, email, web, app) or stable profile attributes |
   | Population | One row per customer — profiles, Parent Segment `customers` |
   | System / output | Workflow outputs, ML results, aggregates. Not a source |

4. **Pick** (`references/dataprep-guide.md` §1–§2):

   | Decision | First push |
   |---|---|
   | Action log, action column, grouping | 2–100 labels, hundreds+ rows each (§1 rules) |
   | Reward rule + window | Per use case (§1 table) |
   | Training window | 180 days of actions |
   | Context sources + lookback | 2–4 with the strongest signal, 90 days |
   | Scoring population | Customers eligible for the next decision |

5. **Confirm** — show a markdown table (action log + action column, the actions, reward rule + window, training window, each context source with ID and time column, scoring population, one-line reason each), then one `AskUserQuestion`: Confirm as listed / Change the actions or reward / Change the sources. Never skip.
6. **Discovery queries** — `references/workflow-setup.md` §1, all in one shell command, no subagents. Fewer than 2 usable actions, or no rewards → tell the user. Record caveats (rare actions, actions sent to one segment only); don't investigate further.
7. **Record** in `project_state.md`: decision, action log + column, action list with rows / reward rate, grouping applied, reward rule + window, training window, context sources (ID, time column), scoring population, join-key differences, first / last action date, assignment caveats, leakage suspects.
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
   - Sink database: default `td_agents`, must hold no `nba_ais_*` tables (fixed names = one project per database); taken → `nba_ais_<project_prefix>`. Created by the first run.
   - Workflow project: default `nba_ais`, must not exist.
   - `model_name`: `<project_prefix>_nba` (`-` → `_`) — unique per account.
4. **Input SQL** — rewrite `workflow/sql/input_features.sql`: `bounds` → `anchors` (log / population) → context CTEs → `reward` → final SELECT, 5–12 numeric features (`references/workflow-setup.md` §1, patterns in `references/dataprep-guide.md` §4). Don't review the `.dig` files.
5. **Config** — edit `workflow/config.yml` in place: `sink_database`, `model_name`, `user_column`, `action_column`, `reward_column`, `timestamp_column`, `exclude_columns`, `reward_window_days`, `train_window_days`, `feature_lookback_days`, `reference_date` (stale data), `ml_batch_api_endpoint` (region); `enable_tuning: false` and template model values (`workflow-setup.md` §2). Schedule and alert email stay commented unless asked. No local validation.
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
| Data prep | `sql/input_features.sql` builds the training log — one row per action logged in the `train_window_days` before `run date − reward_window_days`: the action, its reward in the `reward_window_days` after it, numeric context from the `feature_lookback_days` before it — and the scoring table: one row per customer, context at the run date |
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
| Config / project code | `config.yml` / `sql/input_features.sql` (rewritten per project) |
| Model | AI Signals `nba_tune` (optional) / `nba_train` / `nba_predict`; `lin_ucb`, `lin_ts`, `lin_eps_greedy`, `ipw_learner` |
| Key outputs | `pred_output_table` (Parent Segment, default `nba_ais_actions`), `<pred_output_table>_history`, `nba_ais_*` (fixed names) |
| Agent name | `<project_slug>-agent` (`nba-ai-signal-agent` by default) |
| Secrets | None — `${secret:td.apikey}` is provided by AI Signals |
| API endpoint | `ml_batch_api_endpoint` — US default; regions in the template README |
