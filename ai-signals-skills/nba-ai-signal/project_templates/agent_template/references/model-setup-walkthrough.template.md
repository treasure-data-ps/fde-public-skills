# NBA AI Signal — Model Setup Walkthrough (<project name>)

Use this document to answer questions about **how this customer's Next Best Action model was set up**: what data was explored, how the actions, the reward and the scoring population were defined, which decisions were made and why, what changed along the way, how the results were validated, and which artifacts exist. It is also the recipe for rebuilding or extending a customer-facing walkthrough presentation without repeating the discovery. For how the deployed workflow runs, see `workflow-guide.md`.

<!-- Build instructions (Phase 4 interim or Phase 5 final — remove this comment and every `fill` block when done):
- Interim (Phase 4): describe the setup deployed so far; mark assumed defaults "to confirm"; sections with nothing yet
  (e.g. Parent Segment) say "Not done yet — Phase 5". Final (Phase 5): update the interim file in place, keep the history.
- Save the filled copy as references/model-setup-walkthrough.md in the agent staging folder. Never install this .template.md file.
- Sources: project_state.md (Key Decisions per phase, validation results), requirements.md (questions and answers),
  docs/ (behavior, eval_results, runbook), the workflow working copy (workflow/config.yml, workflow/sql/input_features.sql,
  workflow/*.dig), the Parent Segment / segment YAML files, the latest run in nba_ais_run_log, nba_ais_action_stats and
  {{pred_table}}, and the chat history of this engagement when it is available.
- Every decision gets a reason. Every number gets its source (query or table) and the session ID / date it was taken from —
  numbers here are a BASELINE: when answering questions, re-query for current values and compare with the baseline.
- No secrets, no personal names or email addresses (write roles), no raw customer records — aggregates only.
- Keep it current: append to Decision Log and Accuracy Rules whenever a later chat changes the setup or finds a pitfall.
-->

**Status:** <Interim — pre-production | Final — production>  ·  **Engagement period:** <first phase date> → <latest update or finalize date>  ·  **Validated run:** <session ID, date>

---

## Engagement Summary

<!-- fill:
- Customer, decision (what is chosen per customer), current status (phase, finalized date), business goals from requirements.md
- Timeline: one line per phase with its date and outcome
- Headline result of the validated run (logged average reward vs estimated policy value with its interval, tuning
  hold-out lift if any, customers scored, the two biggest shifts in the action mix) in two or three sentences
-->

## Artifacts

<!-- fill:
- Local files (paths relative to the Work Folder): workflow working copy (incl. sql/input_features.sql), project_state.md,
  requirements.md, docs/*, dashboards/*, parent_segments/*.yml and segment YAML (if any), customer agent folder,
  presentation HTML (if any)
- TD objects: workflow project (name, ID), sink database, model name, {{pred_table}} and {{pred_table}}_history, the
  nba_ais_* tables, Parent Segment (name, ID), segments / folders created
- One line each on what the artifact is for and who it is for (customer / internal)
-->

## Phase 1 — Data Discovery

<!-- fill:
- Decision and success measure as first stated
- Databases and tables reviewed; for each: included or excluded, role (action log, outcome, context, population), reason
- The action list from discovery: rows, customers and reward rate per action; how actions were grouped, merged or dropped
- Assignment check: how actions were given in the past (rules, segments, random, rotation) and the caveats it creates
- ID column chosen and how it was checked (NULLs, distinct counts, overlap across sources); join keys that differed per source
- Event time column per source (time vs a real event timestamp) and the evidence
- Data coverage and freshness (first / last action, gap to the run date → `reference_date`)
- Key profiling queries that drove decisions — the SQL in a code block and the result that mattered
-->

## Phase 2 — Requirements

<!-- fill:
- Questions sent to the customer (from requirements.md) and the answer to each, or "assumed default — pending"
- Defaults that were assumed for the first push and whether the customer later confirmed them
-->

## Decision Log

<!-- fill — chronological table: date → phase → decision → alternatives considered → reason / evidence → config or file affected:
- Phase 3 initial setup: action list and grouping, reward rule and `reward_window_days`, `train_window_days`, context sources
  and `feature_lookback_days`, scoring population, `exclude_columns`, policy settings, tuning off
- Name-gate outcomes: sink database, workflow project, model name, agent name (and why a non-default was used)
- Changes to the input SQL or the .dig files and why (actions merged, features added / removed, leakage fixes)
- Phase 4 changes from the customer's answers (incl. turning tuning on): before → after, and the re-run that confirmed them
-->

## Data Quality and Leakage Checks

<!-- fill:
- Every filter or exclusion applied to the action log, outcomes or population (test sends, NULL IDs, duplicates, refunds)
  with the rows removed and why
- Leakage review: features checked against the action time, columns removed because they describe the action or the outcome
- Known data-quality limits that remain (narrowly assigned actions, short history for new actions) and their effect
-->

## Runs and Validation

<!-- fill:
- Table of runs: session ID / attempt ID → date → settings (tuned or not, model type) → result (success / failed) →
  what was learned or fixed
- Validation checks of the final run (Validate section of the solution's workflow-setup.md): check → result → numbers
- Baseline for later comparison: training rows and actions, rows and reward per action, logged average reward, estimated
  policy value with its interval, estimated lift, tuning choices and hold-out lift, customers scored, recommended mix
-->

## Benchmark Comparison

<!-- fill — only if the customer compared the model with their own reference (current rules, a holdout, an A/B test):
- The reference, its scope and how it was made comparable (population, reward window)
- Per-metric comparison: reference vs model, gap, explanation, confidence rating
- If not done: "No benchmark comparison was made."
-->

## Parent Segment and Activation

<!-- fill:
- Parent Segment name / ID and the attributes added from {{pred_table}} (Phase 5 Step 1) — or "Not done yet — Phase 5"
- Example audiences or segments created: name → rule in plain words → size at creation
- Eligibility rules added to the audiences; activations or journeys that use the recommendations; holdout design, if any
-->

## Walkthrough Presentation Recipe

<!-- fill — only if a customer-facing walkthrough / presentation was built; otherwise "No walkthrough built yet." and
keep the headings below as the plan for one:
- Output file path and the date it was last generated
- One subsection per tab or section, in order: purpose → sources (files to read, tables) → queries (SQL in code blocks)
  → baseline results → layout (cards, charts, tables) → accuracy rules for that section
- Rule: always query fresh; use the baseline only to spot unexpected changes
-->

## Accuracy Rules and Lessons Learned

<!-- fill — append-only list of pitfalls found during the engagement, each with the correct approach:
- Policy value is an in-sample estimate — always with its interval; logged reward per action is not the action's effect
- Latest run by `time`, dedupe appended tables, `is_best = 'true'` is a string
- Exact action spellings in the data and the business names for them
- Columns or tables that look right but must not be used, and why
- Anything a future chat got wrong once and should not repeat
-->

## Open Items and Limitations

<!-- fill:
- Pending customer answers, known limitations, agreed follow-ups and who owns each (role, not name)
-->
