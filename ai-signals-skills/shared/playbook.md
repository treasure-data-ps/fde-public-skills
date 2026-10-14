# ML Solution Playbook

This plugin is an **orchestrator of templates**. Each solution ships read-only blueprints in `<solution_dir>/project_templates/`:

- `workflow_template/` — the TD workflow (single source of truth: its `README.md` explains it; its `config/` YAML defines the parameters)
- `agent_template/` — the customer analysis agent blueprint

During an engagement you copy those templates into the user's working directory (a Treasure AI Studio Work Folder or a local project folder) and customize the **copies**. The plugin itself is never modified.

| Layer | Location | Contents |
|---|---|---|
| Framework (read-only) | this plugin | instructions + templates |
| Engagement workspace | `agent_outputs/<customer_slug>/<solution_slug>/` | workflow copy, project state, requirements, docs, dashboards |
| Customer agent | `.claude/skills/<agent-name>/` | customer-specific analysis skill, built from `agent_template/` |

`<solution_dir>` is the folder containing the solution's `SKILL.md` — resolve it to an absolute path from the skill's base directory before copying anything.

## Shared files

| File | What it contains |
|------|-----------------|
| `local_outputs.md` | Workspace layout, slug rules, git-ignore bootstrap, template-copy rule, what may / may not be stored |
| `project_state.md` | Cross-session context store — format and update rules |
| `push_pattern_td_workflows.md` | Copy `workflow_template/`, sink-database gate, config edit, project-name gate, `tdx wf push`, run, monitor, validate |
| `customer_agent_pattern.md` | Build the customer agent from `agent_template/`: name gate, placeholders, draft vs. final, install, verify |
| `parent_segment_update.md` | Phase 5 Step 1 — Parent Segment attributes + example audiences ("how"; the solution's `references/parent_segment.md` is the "what") |
| `customer_docs_pattern.md` | Phase 5 — documentation set written to `docs/` |

## Default-then-confirm names

Three names are always proposed with a default and confirmed with `AskUserQuestion` ("Use `<default>` (Recommended)" / "Use a different name"). Record each answer in `project_state.md` and reuse it everywhere afterwards.

Before asking, check the default is free — the account may already hold another engagement of the same solution. If it is taken, say so and recommend a customer-specific name instead (project `nba_eng_prod` → `nba_eng_prod_acme`; sink database `td_agents` → `nba_acme`), so one engagement never overwrites another's tables or project. The checks are in `push_pattern_td_workflows.md` (Step 3a, Step 5) and `customer_agent_pattern.md` (Step 1).

| Name | Asked | Default |
|---|---|---|
| Sink database | Phase 3, before writing the workflow config | `td_agents` |
| Workflow project name | Phase 3, before the first push | the template's default (solution Quick Reference) |
| Customer agent name | When the agent draft is built (end of Phase 3) | `<customer_slug>-<solution_slug>-agent` |

## Entry Point

Ask: **"Is this a new solution engagement, or are you resuming an existing one?"**

- **New:** present the 5-phase plan below, then start Phase 1.
- **Resume:** list `agent_outputs/*/<solution_slug>/project_state.md` (see `project_state.md`), confirm the customer, read it — "Current phase" + "Next Action" say where to pick up.

| User says | Likely phase |
|---|---|
| "the customer filled out their requirements" | Phase 4 |
| "push a fresh workflow for [customer]" | Phase 1 → Phase 3 |
| "create the requirements doc" | Phase 2 |
| "build / update the customer agent" | Phase 3 (draft) or Phase 5 (finalize) |
| "add the scores to the parent segment" / "create example audiences" | Phase 5 Step 1 |
| "write the customer facing / handoff docs" | Phase 5 |

When in doubt, **read `project_state.md` first**.

## Workflow Sequence

Rules for every phase:

- **Read files just in time.** In each phase, read only the files that phase names (here and in the solution `SKILL.md`). Do not open later-phase files early — for example, the requirements doc body is not needed in Phase 1; what to record there is listed in the solution's Phase 1 steps.
- **Keep moving.** After each step, continue straight to the next step of the same phase. At the end of a phase, give a short summary and ask with `AskUserQuestion` whether to continue, with the next phase as the `(Recommended)` option. Never end a turn without either continuing or asking.
- **Phases 1–3 are a first pass.** Their goal is a validated first run plus the agent draft, fast. Use safe defaults, record every data caveat and assumption in `project_state.md` as "default — confirm in requirements", and do not investigate further unless the user asks or a validation check fails. A "basic" or "quick" request means defaults and no extra analysis — never skipping steps: the agent draft is part of Phase 3.
- **Query efficiently, without subagents.** Run discovery yourself with `tdx query` — do not launch subagents for it unless the user asks. Combine the same check across tables into one query (`UNION ALL`), and send independent queries as parallel tool calls in one turn rather than one after another.

### Phase 1: Data Exploration

> **The solution SKILL overrides this phase entirely** — which databases to explore, how to classify tables, which columns to capture.

### Phase 2: Customer Requirements Doc

1. `local_outputs.md` Step 1 — bootstrap `agent_outputs/` before writing anything.
2. `project_state.md` — create the state file.
3. If `agent_outputs/<customer_slug>/<solution_slug>/requirements.md` already exists, read it and ask whether it is the customer's filled version — if yes, go to Phase 4.
4. Write `requirements.md` there from the solution's `references/requirements_doc.md` (title `<Solution Name> Requirements - <Customer>`). It must read as a clean customer questionnaire — no "generated by" notes or discovery details (those belong in `project_state.md`).
5. Hand its path to the user: it is plain markdown they can share in any format, and the customer's filled version must be saved back to the same path. Record "requirements doc sent `<date>`" in `project_state.md`.
6. **Continue to Phase 3** — do not wait for the answers.

### Phase 3: Minimal Workflow + Customer Agent Draft

1. `push_pattern_td_workflows.md` + the solution's `references/workflow-setup.md` — copy `workflow_template/`, read its `README.md`, confirm the sink database, write the config from Phase 1 findings + any answers (safe defaults otherwise), confirm the project name, push, ask before running.
2. Validate the outputs per the "Validate" section of `references/workflow-setup.md`.
3. `customer_agent_pattern.md` (Draft) + the solution's `references/agent-setup.md` — confirm the agent name, build and install the draft agent so the user can explore results and dashboards.
4. Update `project_state.md`.

### Phase 4: Update from Customer Requirements

Usually a new session — **read `project_state.md` first**.

1. Read the filled `requirements.md` (if the customer returned it elsewhere, ask the user to save it to `agent_outputs/<customer_slug>/<solution_slug>/requirements.md` first).
2. Map the answers with the mapping table at the end of the solution's `references/requirements_doc.md`, then present the planned config changes; wait for approval.
3. Edit the config in the workflow copy (`references/workflow-setup.md`), re-push, re-run, re-validate.
4. Rebuild the agent draft if the sink database, output tables or business context changed.

### Phase 5: Parent Segment, Documentation, Final Agent

1. **Parent Segment** (solutions with a PS step) — `parent_segment_update.md` for the process; the solution's `references/parent_segment.md` for the "what", read only after the user approves the plan.
2. **Documentation** — `customer_docs_pattern.md` + the solution's `references/docs-setup.md` → `docs/`.
3. **Finalize the customer agent** — `customer_agent_pattern.md` (Finalize) + `references/agent-setup.md`.
4. Update `project_state.md` → "complete — engagement live".

## Solution folder reference

| Path | Contents |
|---|---|
| `SKILL.md` | Solution-specific context per phase |
| `project_templates/workflow_template/` | TD workflow template (`README.md` + `config/` = source of truth) |
| `project_templates/agent_template/` | Customer agent blueprint (`SKILL.template.md` + `references/`) |
| `references/workflow-setup.md` | How to choose config values from the data, solution deploy details, output validation |
| `references/agent-setup.md` | Agent placeholders and finalize-time files |
| `references/requirements_doc.md` | Requirements doc body |
| `references/docs-setup.md` | Documentation set content |
| `references/parent_segment.md` | Phase 5 Parent Segment spec (if applicable) |

Authoring rules for solutions live in `solution_standard.md` (maintainers only — not needed during an engagement).
