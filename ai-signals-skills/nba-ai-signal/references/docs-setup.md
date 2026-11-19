# NBA AI Signal — Documentation Set Content

NBA AI Signal content for the Phase 5 docs. File names, audience headers, create order and update rules are in `../../shared/customer_docs_pattern.md`. Docs go to `agent_outputs/<project_slug>/docs/`. Doc titles: `# <Project Name> <Doc Name>` (e.g. `# Offer NBA AI Signal Runbook`).

Sources for every value: `project_state.md`, `requirements.md`, `business-context.md`, the deployed working copy (`workflow/config.yml`, `workflow/sql/input_features.sql`, `workflow/nba_ais.dig` for schedule and alert email), and the latest validation results. Describe what is deployed, not template defaults. Parameter meanings come from `workflow/README.md` — customer docs reword them in business language (style below); internal docs may use technical names.

## Customer docs — writing style

`architecture.md`, `behavior.md` and `eval_results.md` are read by business stakeholders (marketing, CRM, campaign leads). Write as if presenting to a non-technical manager.

| Do | Don't |
|---|---|
| Business language: customers, offers, campaigns, "what to send next" | SQL, YAML, config keys, column or table names in the body |
| Short sentences, one idea per bullet; lead with what it means for them | Model internals (LinUCB, propensities, OCV, estimators) |
| Real numbers rounded and as people ("about 1 in 4 customers get the loyalty offer") | Raw decimals (0.0731), metric acronyms without explanation |
| Their own terms from `business-context.md` (offer names, KPIs) | Generic data-science jargon |
| A worked example ("Maria, frequent buyer, rarely opens emails, gets the SMS discount") — invented, never real customer data | Bare lists of features |
| "What you can do with this" at the end of each section | Caveats without a recommendation |

Translate every technical term:

| Technical | Say instead |
|---|---|
| Action, arm | The options we choose between (the offers, campaigns or channels) |
| Reward | What we count as success (e.g. "an order within 14 days") |
| Context features | What we know about the customer just before we decide (recent visits, purchases, email engagement) |
| Policy, bandit | The decision rule the model learned: which option tends to work best for which kind of customer |
| Logged average reward | How successful our past choices were on average |
| Estimated policy value | How successful the model's choices would have been on the same customers, estimated from past data |
| Confidence interval | The range we are fairly sure the result falls in |
| Exploration (`epsilon`) | The model keeps trying options it knows less about, so it keeps learning |
| Tuning, hold-out lift | We tested settings on the most recent period the model had not seen; result vs random choices |
| Parent Segment attributes | New fields you can use to build audiences in Audience Studio |

Technical names (project, database, tables) go only in a closing **"For your data team"** table in `architecture.md`.

## 1. `docs/architecture.md` (customer)

- **How it works, in one picture:** your past campaigns and their results → the model learns what worked for whom → every customer gets one recommended option → it appears in Audience Studio → teams send it. A simple flow in words or ASCII, no system names
- **What runs and when:** how often the model relearns and how often recommendations refresh, in plain words
- **What you get:** the new fields in Audience Studio (recommended option, date) and the example audiences
- **Who to contact** when something looks wrong
- **For your data team** (closing table): TD workflow project and entry point, sink database, model name, recommendation and history tables, Parent Segment attribute names

## 2. `docs/behavior.md` (customer)

- **What we decide** — the decision in one sentence, the options, who gets a recommendation and who is left out (and why)
- **What counts as success** — the reward and its time window
- **What the model looks at** — the kinds of signals and the history used; that it only uses what was known before each past decision
- **How it learned** — from N months of past decisions; it relearns every <cadence>; it can only recommend options that were used before, and learns best when options were tried on many kinds of customers
- **How to read a recommendation** — one option per customer, with a worked example; it is the best choice among the options for that customer, not a guarantee
- **The mix** — how often each option is recommended vs how often it was used before, and the plain reason for the biggest shifts
- **Good to know** — caveats in plain words, each with what to do about it (e.g. "option D was only ever sent to VIPs — the model can't judge it for others; include it in a small test")
- **Using it** — the example audiences from Phase 5, how to keep a small random group to measure the result, 2–3 campaign ideas tied to the customer's goals

## 3. `docs/eval_results.md` (customer)

- **Verdict first** — one sentence: is the model expected to beat the current way of choosing, and how sure we are
- **Expected result** — "past choices succeeded for about N in 100 customers; the model's choices would have succeeded for about M in 100 (range X–Y)"; from tuning, the result on the most recent period vs random choices
- **How confident** — whether the range clears today's result; what limits the confidence (few examples per option, options sent to narrow groups)
- **What happens next** — once real results are in, we compare customers who got the recommended option with those who didn't (`workflow-setup.md` §4 check 6) and report it here; recommend a holdout group
- Date of the validated run (session ID only in a footnote)

## 4. `docs/runbook.md` (internal)

- Working copy path and TD project name; re-deploy: edit `workflow/config.yml` or `workflow/sql/input_features.sql` → `( cd workflow && tdx wf push -y )` → `tdx wf run <project>.nba_ais` (or `.train` / `.predict`) → validate
- Monitoring: `tdx wf sessions <project>`, `tdx wf timeline <project>.nba_ais --follow`, `tdx wf attempt <id> tasks` / `logs +<task>`; a failed poll shows the API error in its log
- Cancelling a stuck ML run (`DELETE /v1/runs/<run_id>`, run id in the poll log) and dropping leftover `mltmp_nba_ais_*` tables
- Schedules and failure-alert recipient (from the `.dig` files); how to change them (edit the `.dig`, re-push); one attempt at a time per `model_name`
- Model: the AI Signals NBA solutions, `model_type` or tuning, `model_name` (every training run replaces it), the API endpoint (region); no secrets to manage
- Retraining guidance: when to retrain (new or retired actions, policy value moving between runs, live check below expectations) and how to compare two setups (a second project with its own `model_name` and sink database)
- The troubleshooting tables from `workflow-setup.md` and `ai-signals-guide.md` §7, filtered to what applies to this customer
- The input SQL as deployed (path) and every change made beyond the config, with dates
- Rebuilding the customer agent after config or SQL changes (`../../shared/customer_agent_pattern.md`)

## 5. `docs/access_ownership.md` (internal)

Standard content per `../../shared/customer_docs_pattern.md`, plus: TD project name, sink database, model name, recommendations table, Parent Segment name, customer agent name and path (`.claude/skills/<agent-name>/`).
