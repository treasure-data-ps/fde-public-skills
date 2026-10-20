# Phase 5 Instructions — Evaluation, Production-Ready, Handoff

> Read `../references/execution-contract.md` (Phase 5 gate) first.

**Goal:** prove the dashboard agent works on the customer's data and follows their business context, then finalize it. Mechanics: `<skill_dir>/../shared/eval_pattern.md` (plan in `eval.md`, approval, one fresh subagent per prompt, scoring, fixes, re-runs, production bar **≥ 9/10 Pass and every Compliance case Pass**) + `../references/eval-setup.md` (dashboard test categories, failure → fix).

## Entry condition

Phase 4 complete: the dashboard agent is installed in `.claude/skills/<project_slug>-dashboard-agent/` and its build checks passed.

## Step 1 — Evaluation plan

Build **10 prompts** from the categories in `../references/eval-setup.md`, with real names from the engagement's `metrics-catalog.md`, `business-context.md` and `data-dictionary.md` and the Step 1r agent scope. Write them to `agent_outputs/<project_slug>/eval.md`, show the table, and ask with `AskUserQuestion`: "Run the 10 tests (Recommended)" / "Change the tests first" / "Not now". Never run before the approval.

## Step 2 — Run, score, fix

`eval_pattern.md` Steps 2–4: one fresh subagent per prompt against the installed agent (read-only — "add a metric" cases edit only a scratch copy of the dashboard files in `agent_outputs/<project_slug>/eval_scratch/` and stop before copying anything into the agent), score each case, record the round in `eval.md`, propose fixes with the failure → fix table, apply only the approved ones, rebuild the agent (Phase 4 rebuild), re-run. Repeat until the bar is met; re-run all 10 at least once.

## Step 3 — Production-ready

Only after the bar is met and the user asks to finalize:

1. **Business context confirmed** — the customer's `requirements.md` answers are merged (Phase 1 Step 1v, "When the customer returns"). Remove every remaining `[NEEDS YOUR INPUT]` (list them in `project_state.md` as "not answered") and ask about any `[INFERRED — please confirm]` left. If anything changed since the last passing round, rebuild and run a final round — the bar must still be met.
2. **Finalize the agent** — `customer_agent_pattern.md` Step 4 + `../references/agent-setup.md` (Finalize). Ask for the install approval phrase again if new files are added.
3. **Handoff docs** (optional — ask with `AskUserQuestion`) — `../references/docs-setup.md` → `agent_outputs/<project_slug>/docs/`. Remove Treasure Data internals from anything marked for the customer.
4. **Feedback** — ask the user: "What could the dashboard builder do better, based on this engagement?" Record the answer in `project_state.md` under Key Decisions → "Builder feedback" so it can be passed to the plugin maintainers.
5. Update `project_state.md`: header → Current phase "complete — agent live"; ledger → Phase 5 section with the final eval score, finalize date and docs.

## Quality gates

- Eval plan approved before running; every round recorded in `eval.md`
- Production bar met on the last full run; no change in the account during the eval
- No `[NEEDS YOUR INPUT]` in the installed `references/business-context.md` after finalize
- Feedback question asked and recorded
