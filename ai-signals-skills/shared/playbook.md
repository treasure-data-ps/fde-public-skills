# ML Solution Playbook

This plugin is an **orchestrator of templates**. Each solution ships read-only blueprints in `<solution_dir>/project_templates/`:

- `workflow_template/` — the TD workflow (single source of truth: its `README.md` explains it; its `config/` YAML defines the parameters)
- `agent_template/` — the customer analysis agent blueprint

During an engagement you copy those templates into the user's working directory (a Treasure AI Studio Work Folder or a local project folder) and customize the **copies**. The plugin itself is never modified.

| Layer | Location | Contents |
|---|---|---|
| Framework (read-only) | this plugin | instructions + templates |
| Engagement workspace | `agent_outputs/<customer_slug>/<solution_slug>/` | workflow copy, project state, business context, requirements, docs, dashboards |
| Customer agent | `.claude/skills/<agent-name>/` | customer-specific analysis skill, built from `agent_template/` |

`<solution_dir>` is the folder containing the solution's `SKILL.md` — resolve it to an absolute path from the skill's base directory before copying anything.

## Shared files

| File | What it contains |
|------|-----------------|
| `local_outputs.md` | Workspace layout, slug rules, git-ignore bootstrap, template-copy rule, what may / may not be stored |
| `project_state.md` | Cross-session context store — format and update rules |
| `push_pattern_td_workflows.md` | Copy `workflow_template/`, sink-database gate, config edit, project-name gate, `tdx wf push`, run, monitor, validate |
| `customer_agent_pattern.md` | Build the customer agent from `agent_template/`: name gate, placeholders, hands-on build vs. final, interim and final guides, install, verify |
| `parent_segment_update.md` | Phase 5 Step 1 — Parent Segment attributes + example audiences ("how"; the solution's `references/parent_segment.md` is the "what") |
| `customer_docs_pattern.md` | Phase 5 — documentation set written to `docs/` |

## Default-then-confirm names

Three names are always proposed with a default and confirmed with `AskUserQuestion` ("Use `<default>` (Recommended)" / "Use a different name"). Record each answer in `project_state.md` and reuse it everywhere afterwards.

Before asking, check the default is free — the account may already hold another engagement of the same solution. If it is taken, say so and recommend a customer-specific name instead (project `nba_eng_prod` → `nba_eng_prod_acme`; sink database `td_agents` → `nba_acme`), so one engagement never overwrites another's tables or project. The checks are in `push_pattern_td_workflows.md` (Step 3a, Step 5) and `customer_agent_pattern.md` (Step 1).

| Name | Asked | Default |
|---|---|---|
| Sink database | Phase 3, before writing the workflow config | `td_agents` |
| Workflow project name | Phase 3, before the first push | the template's default (solution Quick Reference) |
| Customer agent name | Phase 4, when the hands-on kit is built | `<customer_slug>-<solution_slug>-agent` |

## Entry Point

Ask: **"Is this a new solution engagement, or are you resuming an existing one?"**

- **New:** present the 5-phase plan below, then start Phase 1.
- **Resume:** list `agent_outputs/*/<solution_slug>/project_state.md` (see `project_state.md`), confirm the customer, read it — "Current phase" + "Next Action" say where to pick up.

| User says | Likely phase |
|---|---|
| "the customer filled out their requirements" | Phase 4 |
| "push a fresh workflow for [customer]" | Phase 1 → Phase 3 |
| "create the requirements doc" | Phase 2 |
| "build / update the customer agent", "build the dashboard", "write the workflow guide / setup walkthrough" | Phase 4 (hands-on kit) or Phase 5 (final) |
| "add the scores to the parent segment" / "create example audiences" | Phase 5 Step 1 |
| "write the customer facing / handoff docs" | Phase 5 |

When in doubt, **read `project_state.md` first**.

## Workflow Sequence

Rules for every phase:

- **Read files just in time.** In each phase, read only the files that phase names (here and in the solution `SKILL.md`). Do not open later-phase files early — for example, the requirements doc body is not needed in Phase 1; what to record there is listed in the solution's Phase 1 steps.
- **Keep moving.** After each step, continue straight to the next step of the same phase. At the end of a phase, give a short summary and ask with `AskUserQuestion` whether to continue, with the next phase as the `(Recommended)` option. Never end a turn without either continuing or asking.
- **Phases 1–3 are a first pass.** Their goal is a validated first workflow run, fast. Use safe defaults, record every data caveat and assumption in `project_state.md` as "default — confirm in requirements", and do not investigate further unless the user asks or a validation check fails. A "basic" or "quick" request means defaults and no extra analysis — never skipping steps or the end-of-phase question.
- **Query efficiently, without subagents.** Run discovery yourself with `tdx query` — do not launch subagents for it unless the user asks. Combine the same check across tables into one query (`UNION ALL`), and send independent queries as parallel tool calls in one turn rather than one after another.

### Phase 1: Data Exploration

> **The solution SKILL defines the discovery steps** — which databases to explore, how to classify tables, which columns to capture. Its last step is the business context draft below.

**Business context draft and review** (end of Phase 1, after discovery):

`business-context.md` holds what the customer knows about their business and the model can't learn from the data — business jargon, definitions (lead, high-value customer, conversion), buying cycles, data edge cases, goals and exclusion rules. It is the customer agent's main source of business meaning. How the model works does **not** belong here (that is in the solution's model guide, the agent's `data-dictionary.md` and the guides).

1. `local_outputs.md` Step 1 — bootstrap `agent_outputs/`; `project_state.md` — create the state file (if not already there).
2. Copy `<solution_dir>/project_templates/agent_template/references/business-context.template.md` to `agent_outputs/<customer_slug>/<solution_slug>/business-context.md`, fill `{{customer_name}}`, and follow its authoring rules: answer what the Phase 1 findings support with confidence, marked `[INFERRED — please confirm]`; leave every other question under its section marked `[NEEDS YOUR INPUT]`. Do not run extra queries for it.
3. Show the user a short summary — one line per section: what was inferred, and the open questions — then ask with `AskUserQuestion`: "Looks right — continue (Recommended)" / "I'll add context now" / "Change assumptions". Write any answer into the file (customer answers replace inferences; remove the marker of each answered item) and record "Business context: drafted / reviewed `<date>`" in `project_state.md`.
4. Continue to Phase 2 — questions still marked `[NEEDS YOUR INPUT]` go to the customer through the requirements doc.

### Phase 2: Customer Requirements Doc

1. If not done in Phase 1: `local_outputs.md` Step 1 (bootstrap `agent_outputs/`) and `project_state.md` (create the state file).
2. If `agent_outputs/<customer_slug>/<solution_slug>/requirements.md` already exists, read it and ask whether it is the customer's filled version — if yes, go to Phase 4.
3. Write `requirements.md` there from the solution's `references/requirements_doc.md` (title `<Solution Name> Requirements - <Customer>`). It must read as a clean customer questionnaire — no "generated by" notes or discovery details (those belong in `project_state.md`).
4. End it with a **Business context** section: every question still marked `[NEEDS YOUR INPUT]` in `business-context.md`, except those the doc's own sections already ask, each with `> _Your answer:_`. Omit the section if none are left.
6. Hand its path to the user: it is plain markdown they can share in any format, and the customer's filled version must be saved back to the same path. Record "requirements doc sent `<date>`" in `project_state.md`.
7. **Continue to Phase 3** — do not wait for the answers.

### Phase 3: Minimal Workflow

1. `push_pattern_td_workflows.md` + the solution's `references/workflow-setup.md` — copy `workflow_template/`, read its `README.md`, confirm the sink database, write the config from Phase 1 findings + any answers (safe defaults otherwise), confirm the project name, push, ask before running.
2. Validate the outputs per the "Validate" section of `references/workflow-setup.md`.
3. Update `project_state.md`.
4. **Offer the hands-on kit** — summarize the validated run, then ask with `AskUserQuestion` what to build now for Phase 4 testing:
   - "Agent, dashboard and both guides (Recommended)" — the customer agent, its HTML dashboard, `workflow-guide.md` and `model-setup-walkthrough.md`
   - "Agent and dashboard only"
   - "Not now — wait for the customer's requirements"

   Record the answer in `project_state.md` and continue with Phase 4 Part A (or stop at "Not now" with Next Action "Phase 4 — hands-on kit or requirements").

### Phase 4: Hands-on Testing and Customer Requirements

The hands-on kit lets non-technical users and the customer test the model and see how it works while the setup is iterated toward production.

**Part A — Hands-on kit** (right after Phase 3, or whenever the user asks for it):

1. `customer_agent_pattern.md` Steps 1–3 + the solution's `references/agent-setup.md` — confirm the agent name, build and install the customer agent.
2. Generate the dashboard once with the agent's dashboard command (`references/agent-setup.md` build checks). The bundled dashboard is pre-validated — check only that the file was written; no screenshots, QA scripts or edits.
3. If the guides were chosen: `customer_agent_pattern.md` Step 4 (**interim** guides) — fill `workflow-guide.md` and `model-setup-walkthrough.md` from the engagement files so far, marked interim, and reinstall the agent.
4. Tell the user what was built and how to use it (the agent is available in new chats in this folder), then update `project_state.md`.

**Part B — Update from customer requirements** (usually a new session — **read `project_state.md` first**):

1. Read the filled `requirements.md` (if the customer returned it elsewhere, ask the user to save it to `agent_outputs/<customer_slug>/<solution_slug>/requirements.md` first).
2. Map the answers with the mapping table at the end of the solution's `references/requirements_doc.md`, then present the planned config changes; wait for approval.
3. Edit the config in the workflow copy (`references/workflow-setup.md`), re-push, re-run, re-validate.
4. Merge the business answers (use case, Business context section, definitions in any answer) into `business-context.md` — customer answers replace inferences; remove the marker of each answered item.
5. Refresh the hands-on kit if it exists: rebuild the agent if the sink database, output tables or business context changed; regenerate the dashboard; refresh the interim guides (`customer_agent_pattern.md` Step 4).

Repeat Part B as often as the testing needs. At the end of Phase 4, ask whether to continue to Phase 5 (production).

### Phase 5: Parent Segment, Documentation, Final Agent

1. **Parent Segment** (solutions with a PS step) — `parent_segment_update.md` for the process; the solution's `references/parent_segment.md` for the "what", read only after the user approves the plan.
2. **Documentation** — `customer_docs_pattern.md` + the solution's `references/docs-setup.md` → `docs/`.
3. **Confirm the business context** — in `business-context.md`, remove every question still marked `[NEEDS YOUR INPUT]` (list them in `project_state.md` Key Decisions as "not answered") and any `[INFERRED — please confirm]` the user has confirmed; ask about inferences still unconfirmed. Record "Business context: confirmed `<date>`".
4. **Finalize the customer agent** — `customer_agent_pattern.md` Step 5 + `references/agent-setup.md` (build the agent first with Steps 1–3 if Phase 4 Part A was skipped).
5. **Offer the final guides** — ask with `AskUserQuestion`: "Update `workflow-guide.md` and `model-setup-walkthrough.md` with the final production setup? (Recommended)" / "Keep them as they are" (or "Create them now" / "Skip" if they were never built). On yes: `customer_agent_pattern.md` Step 4 (**final** guides) and reinstall the agent.
6. Update `project_state.md` → "complete — engagement live".

## Solution folder reference

| Path | Contents |
|---|---|
| `SKILL.md` | Solution-specific context per phase |
| `project_templates/workflow_template/` | TD workflow template (`README.md` + `config/` = source of truth) |
| `project_templates/agent_template/` | Customer agent blueprint (`SKILL.template.md` + `references/`, incl. `business-context.template.md`) |
| `references/ai-signals-guide.md` | AI Signals model guide — input, API parameters, how it scores, outputs, common changes (AI Signals solutions) |
| `references/workflow-setup.md` | How to choose config values from the data, solution deploy details, output validation |
| `references/agent-setup.md` | Agent placeholders, build checks, guides and finalize-time files |
| `references/requirements_doc.md` | Requirements doc body |
| `references/docs-setup.md` | Documentation set content |
| `references/parent_segment.md` | Phase 5 Parent Segment spec (if applicable) |

Authoring rules for solutions live in `solution_standard.md` (maintainers only — not needed during an engagement).
