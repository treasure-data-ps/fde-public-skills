# Phase 4: Track B — Deploy Companion AI Foundry Agent (4b-i to 4b-vi)

**Goal:** Deploy a companion AI Foundry agent for conversational dashboard analysis.

**When to deploy:**
- Users prefer NL queries over clicking filters
- Team wants anomaly detection and trend analysis
- Dashboard is mission-critical (questions arise daily)
- Support load is high (same questions repeated)

---

## Step 4b-i & 4b-ii: Decide on Agent + Choose Capability (15 min)

**Ask the user:**
```
"Your dashboard is ready! Would you like to add an AI agent so users can ask
questions in plain English like 'What's driving the churn spike?', 'Which region
has highest growth?', 'Show anomalies in the last week'?

The agent can also generate reports and detect trends automatically.

Interested? (Y/N)"
```

**Four Agent Capabilities Available (Composable — can combine in one agent):**

The four patterns below describe **capabilities** that can be combined in a single agent via intent-routing in the system prompt. Rather than forcing a re-deployment when a new capability is needed, design the agent's CRITICAL RULES section to route based on the user's question: "If user asks for a trend, do X; if they ask for a weekly report, do Y; if ad-hoc, do Z."

| Capability | What it does | Q&A / On-demand | Scheduled / Reports | Effort to implement |
|----------|---|---|---|---|
| **Insights** (NL queries) | User asks questions, agent answers | ✅ Yes | ❌ No | 1-1.5h |
| **Dashboard Generation** | Auto-generate dashboards on-demand | ✅ Yes | ⚠️ Possible | 1.5-2h |
| **Reporting** (summaries) | Weekly/monthly exec summaries, email/Slack | ❌ No | ✅ Yes | 1.5-2h |
| **Orchestration** (complex workflows) | Multi-step analysis, ML, custom logic | ✅ Yes | ✅ Yes | 2-3h |

**Recommended first deployment:** Insights capability (fastest, most flexible). Add other capabilities later if needed — no re-deployment required; just update the `prompt.md` intent-routing rules.

**Example: Composite system_prompt intent-routing:**
```markdown
## CRITICAL RULES: Intent-Based Routing

1. If user asks "What drove X?" / "Why did Y happen?" or "Show me [metric] trends"
   → Use INSIGHTS behavior: query the specific dimension → explain the spike/drop

2. If user asks "Generate dashboard" / "Create a report view"
   → Use DASHBOARD behavior: build multi-tab layout → export or render

3. If user says "Send me the weekly report" / "Schedule daily summary"
   → Use REPORTING behavior: query last 7 days → format as executive summary → email/Slack

4. If user asks multi-part like "Correlate churn with campaign spend AND predict next quarter"
   → Use ORCHESTRATION behavior: chain multiple tools → synthesize answer → explain caveats
```

This means **one deployed agent, all four behaviors**, triggered by what the user actually asks — no forced choice at deployment time.

**Record the chosen capabilities and intent-routing logic in:** `./<project-name>/agents/capabilities.md`

---


---

### Confirm Agent Name Before Deployment

**Every Foundry agent needs a unique name.** This becomes the agent's identifier in Treasure AI Studio.

```
AskUserQuestion:
  header: "Agent name"
  question: "What should the agent be called? (lowercase with hyphens, e.g., dashboard-churn-analyzer, revenue-insights-agent)"
  options:
    - label: "Suggest based on dashboard purpose + capabilities"
      description: "e.g., [dashboard-name]-analyzer, [dashboard-name]-insights"
    - label: "I'll type a custom name"
      description: "Provide a lowercase with hyphens name"
```

Lock in the confirmed `<agent-name>` before proceeding to pre-flight checks.

---

## Step 4b-iii: Pre-Flight Checks (5 min)

**Check 1: Foundry/LLM Access**
```bash
tdx llm project list
# If fails → STOP. Ask: "Do you have LLM/Foundry project creation permissions?"
```

**Check 2: Output tables exist & have data**
```bash
# Non-Workflow path:
tdx query "SELECT COUNT(*) FROM {database}.{metrics_table}"

# Workflow path:
tdx query "SELECT COUNT(*) FROM {sink_database}.{output_table}"

# If returns 0 → STOP. Complete Phase 2/3 first.
```

**Check 3: Audit existing Foundry project (avoid deploying a duplicate)**

Before deploying a new agent, check if a Foundry project already exists for this dashboard:

```bash
tdx llm project list | grep -i "<project-name>\|<dashboard-type>"
```

If found, pull to `/tmp/` to avoid leaving debris in the project directory:

```bash
mkdir -p /tmp/agent-inspect-$$
cd /tmp/agent-inspect-$$
tdx llm project pull <project_name>
# Review: do the table names match the CURRENT schema,
# or are they stale (e.g. from an earlier version of this dashboard)?
cd -
rm -rf /tmp/agent-inspect-$$  # Clean up immediately
```

**Why `/tmp/`?** 
- Inspection-only; no need to keep in project
- Avoids confusion from leftover `agents-existing/` folders in the working directory
- Uses `$$` (PID) to avoid naming collisions if multiple inspections run in parallel

⚠️ **DECISION GATE — Ask user before overwriting existing Foundry resource:**

If an existing project is found, do NOT proceed directly to replacement. Foundry projects are shared, live resources. Ask first:

```
AskUserQuestion:
  header: "Existing Foundry project found"
  question: "Found existing Foundry project: [project-name]. What should we do?"
  options:
    - label: "Update it"
      description: "Replace its knowledge bases with the current versions (overwrite)"
    - label: "Create a new project"
      description: "Deploy as a separate Foundry project under a different name"
    - label: "Cancel — skip Track B"
      description: "Don't deploy an agent right now"
```

**Action after user selects:**
- [ ] **Update it:** Proceed to Step 4b-iv with the existing project name (full KB replacement)
- [ ] **Create new:** Change project name and proceed normally with a fresh project
- [ ] **Cancel:** Exit Track B; proceed to Phase 5 or close engagement

**Check 4: Required credentials**
- [ ] Treasure Data API key (for the agent to query tables)
- [ ] Foundry/LLM project credentials
- [ ] (Optional) Slack webhook, if the agent will deliver reports to Slack

**Check 5: Compliance & Data Sensitivity**

Before deploying, verify the Phase 1 compliance flag (Stage A, Step 1l) is honored:

```
From state.md, Stage A Step 1l:

Compliance requirements:
  [ ] None flagged → proceed normally
  [ ] Yes: _____ (describe, e.g., "PII masking", "SOC2 audit logging")

Mitigation for this agent:
  [ ] Masking: Will the agent's KB include masked columns only?
  [ ] Audit logging: Is Foundry logging enabled for queries?
  [ ] Residency: Is the agent deployed in the same region as the data?
  [ ] Row-level security: Will agent queries include a tenant_id filter?
```

**If compliance was flagged and mitigations are not yet in place:** stop and document the required constraints in `prompt.md` CRITICAL RULES before deploying. Example:

```markdown
## CRITICAL RULES (Compliance Gates)
1. **PII Masking Required:** Queries must use masked columns (email → email_hash, phone → phone_hash)
2. **SOC2 Audit Logging:** All agent queries are logged for compliance audit trail
3. **Regional Residency:** Agent operates in US-East region only (matching source data)
4. **Multi-tenant:** Always include AND tenant_id = {provided_tenant_id} in queries
```

**Action:**
- [ ] Read the Phase 1 Step 1l compliance flag from `state.md`
- [ ] For each flag, confirm the mitigation is implemented
- [ ] Document all compliance constraints in `prompt.md` CRITICAL RULES
- [ ] Record the compliance check result in `./<project-name>/agents/compliance-gate.md`

---

## Step 4b-iv: Configure Agent Knowledge Bases

KBs are assembled in **two stages**. Don't wait for fully-populated KBs before the first push — stub most files, populate fully after validation.

**CRITICAL: Foundry Agent Directory Structure**

The actual Foundry structure differs from earlier versions. Create this exact layout:

```bash
# File structure (CORRECT for Foundry)
agents/
├── <project-name>/
│   ├── agent.yml                  ← Agent configuration (model, tools, max_iterations)
│   ├── prompt.md                  ← System prompt (NOT in knowledge_bases/)
│   └── knowledge_bases/
│       ├── business_context.md    ← Text KB
│       ├── metrics_dictionary.md  ← Text KB
│       ├── sql_templates.md       ← Text KB
│       ├── sink_sales_revenue.yml         ← One KB per SINK table
│       ├── sink_customer_segments.yml     ← One KB per SINK table
│       └── sink_regional_summary.yml      ← One KB per SINK table
├── knowledge_bases/               ← (NOT used for agent — per-project folder only)
└── tdx.json                        ← Foundry project config
```

**Setup commands:**

```bash
# 1. Create project structure
mkdir -p ./<project-name>/agents/<project-name>/knowledge_bases

# 2. Copy agent configuration template to agent.yml
cp references/templates/agent-config-template.yml \
   ./<project-name>/agents/<project-name>/agent.yml

# 3. Fill [agent-name], [DASHBOARD_PURPOSE], [SINK_DATABASE], [TABLE_NAME] in agent.yml
vi ./<project-name>/agents/<project-name>/agent.yml

# 4. Copy agent prompt template to prompt.md (NOT in knowledge_bases/)
cp references/templates/agent-prompt-template.md \
   ./<project-name>/agents/<project-name>/prompt.md

# 5. Fill [DOMAIN], [DATABASE], [SINK_TABLES], [CRITICAL_RULES], [KEY_FACTS] in prompt.md
vi ./<project-name>/agents/<project-name>/prompt.md
```

**Why this structure?** `tdx agent push` expects:
- `agent.yml` + `prompt.md` as siblings (configuration + behavior)
- `knowledge_bases/` subfolder for all KBs (per-table `.yml` files + text KBs)
- Each `.yml` file becomes a separate registered KB in Foundry

**Example: `knowledge_bases/sink_sales_revenue.yml`**

```yaml
name: sink_sales_revenue
type: database
database: td_reporting_agents
tables:
  - name: sink_sales_revenue
    td_query: "SELECT * FROM <sink_db>.sink_sales_revenue LIMIT 1000"
    grain: "one row per order_date × region × channel"
    confirmed_totals:
      total_revenue: 1284302.55          # Must match Phase 2/3 validation within 1%
    reasoning_effort: "medium"           # OPTIONAL: low|medium|high complexity for agent reasoning
enable_data: false                        # Never enable live data export
enable_data_index: false                  # Index not needed for dashboard use
```

**`confirmed_totals:` field — REQUIRED:**
- Value is any key metric you spot-checked in Phase 2/3 validation
- Agent uses this to self-verify queries are working (answers should match within 1%)
- Example: if Phase 2 `tdx query` returned `total_revenue = 1284302.55`, place that number here
- Format: any key metric name + numeric value (can be a sum, count, average, etc.)

**`reasoning_effort:` field — OPTIONAL but recommended:**
- Set to `low`, `medium`, or `high` based on schema complexity
- `low`: simple schema, <5 columns, straightforward joins (e.g., daily aggregates)
- `medium`: moderate complexity, dimension breakdowns, some calculated fields
- `high`: complex schemas, many joins, non-additive metrics, cardinality nuances
- The agent uses this to gauge how much analysis effort to apply (affects response depth and tool calls)

**Example: `knowledge_bases/sink_customer_segments.yml`**

```yaml
name: sink_customer_segments
type: database
database: td_reporting_agents
tables:
  - name: sink_customer_segments
    td_query: "SELECT * FROM <sink_db>.sink_customer_segments LIMIT 10000"
    grain: "one row per customer_id"
    confirmed_totals:
      total_customers: 50423
enable_data: false
enable_data_index: false
```

**Why individual files?** `tdx agent push` reads each `.yml` file as a separate KB. It registers each one in Foundry with its own name (e.g., `sink_sales_revenue`, `sink_customer_segments`). The agent's `prompt.md` and `agent.yml` then reference each KB by name via `@ref(type: "knowledge_base", name: "sink_sales_revenue")`.

**Naming convention:** Use table names as KB names (e.g., `sink_orders.yml` creates a KB named `sink_orders`).

### First Push — Schema + Behavioral Rules Only

Populate `prompt.md` and the per-table `.yml` files (e.g. `sink_sales_revenue.yml`) fully. Stub the other three.

| File | First-push action | Source |
|------|-------------------|--------|
| `prompt.md` | ✅ **Populate fully** — CRITICAL RULES at the top | Copied from `references/templates/agent-prompt-template.md`; fill `[DOMAIN]`, `[DATABASE]`, `[SINK_TABLES]`, `[CRITICAL_RULES]`, `[KEY_FACTS]` |
| `<table>.yml` (one per SINK table) | ✅ **Populate fully** — schema is confirmed | Phase 3 schema + Phase 2 confirmed totals (if run); include `confirmed_totals:` and `grain:` for every table; **use ONLY `{name, td_query}` format (not plain table names)** — see format example above |
| `business_context.md` | ⚡ **Stub** — 3-5 bullets max | Phase 1 requirements (company, industry, dashboard purpose); full distillation happens post-validation |
| `metrics_dictionary.md` | ⚡ **Stub** — name + SQL formula only | Phase 3 validated queries; NL phrasings added post-validation |
| `sql_templates.md` | ⚡ **Stub for agent KB** — one KPI-summary template + one trend template only; **omit workflow SQL section** | Phase 3 core queries; agent doesn't need source→SINK transformation SQL |

### ⚠️ Gap Alert: `sql_templates.md` for Agent KBs Must Be Trimmed

If you're copying `sql_templates.md` from Track A (or creating fresh for Track B), the full version with all 8 workflow SQL blocks (WF-Q1–WF-Q8) will exceed the 18,000 character KB size limit when pushed to Foundry.

**For agent KBs only:** create a trimmed version with only the SINK query examples (the agent queries SINK directly and doesn't need source→SINK transformation SQL).

```bash
# Check file size before push
wc -c ./<project-name>/agents/knowledge_bases/sql_templates.md
# If > 18000: remove workflow SQL section and re-check

# Trim: remove the "## Workflow SQL" section entirely
# Keep only: KPI-summary queries, trend queries, breakdown queries
```

**Stub content for first push:**
```markdown
## KPI Summary Query

SELECT [dimension_cols], COUNT(*) as total_records, SUM(metric) as total_metric
FROM {SINK_DB}.[table]
GROUP BY [dimension_cols];

## Trend Query

SELECT DATE([date_col]) as date, COUNT(*) as records
FROM {SINK_DB}.[table]
GROUP BY DATE([date_col])
ORDER BY date DESC
LIMIT 30;
```

Don't include workflow SQL (WF-Q1, WF-Q2, etc.) — remove that section entirely for agent KBs.

**Why:** the agent needs the per-table `.yml` files (schema) and `prompt.md` (behavioral rules) to pass Test 1 (connectivity). The other KBs can be stubs — Round 1 test failures reveal exactly what's missing before you spend time writing them.

> **Track A → Track B reuse (avoid re-authoring):** If Track A ran, `./<project-name>/skills/knowledge/` already has `business_context.md`, `metrics_catalog.md`, and `sql_templates.md`. Copy these directly into `agents/knowledge_bases/` as the starting point — do NOT re-write from scratch. Track B adds the per-table `.yml` files and `prompt.md` on top.
>
> **Copy commands from Track A to Track B:**
> ```bash
> # If Track A skill exists:
> cp ./<project-name>/skills/knowledge/business_context.md \
>    ./<project-name>/agents/<project-name>/knowledge_bases/business_context.md
> cp ./<project-name>/skills/knowledge/sql_templates.md \
>    ./<project-name>/agents/<project-name>/knowledge_bases/sql_templates.md
> 
> # Rename metrics_catalog.md → metrics_dictionary.md (Track B naming convention)
> cp ./<project-name>/skills/knowledge/metrics_catalog.md \
>    ./<project-name>/agents/<project-name>/knowledge_bases/metrics_dictionary.md
> ```
>
> ⚠️ **CRITICAL before copying `sql_templates.md` to agents/:** Remove the entire "## Workflow SQL" section (WF-Q1 through WF-Q8 blocks). The agent queries SINK tables directly and does NOT need source→SINK transformation SQL. Workflow SQL blocks inflate the file to 18,000+ characters, exceeding the Foundry KB text limit (~18K chars). Strip these blocks before copying to `agents/knowledge_bases/`.
>
> ```bash
> # After copying, trim sql_templates.md for agent use:
> # Open file and delete from "## Workflow SQL" to the end of WF-Q8 block
> vi ./<project-name>/agents/<project-name>/knowledge_bases/sql_templates.md
> # Keep only: KPI Summary, Trend Query, Breakdown Query sections
> # Verify char count after: wc -c sql_templates.md  (should be < 18000)
> ```

**CRITICAL: System Prompt Character Limit (⚠️ 9,000 CHARACTER MAXIMUM)**

The Foundry agent API enforces a **9,000 character limit** on `prompt.md`. A prompt with CRITICAL RULES + intent-routing table + business facts + exclusion rules + tone naturally produces 10,000-12,000+ characters for any dashboard with moderate complexity. You **will hit this limit** with a moderately complex schema or many metrics.

**Budget:**
- CRITICAL RULES (6 rules): ~800 chars
- Intent-routing table (if composable): ~1,200 chars
- Key Business Facts: ~600 chars
- Exclusion Rules (3-5 rules): ~400 chars
- Data Access table (redundant with get_table_schema): ~1,500 chars ← CUT THIS FIRST
- Tone section: ~200 chars
- **Total easily reaches 11,000+ chars — exceeds the 9,000 limit**

**If `prompt.md` exceeds 9,000 characters (check with `wc -c`), cut in this order (keeps all behavioral rules intact):**
1. **Remove the Data Access table** (redundant — the agent gets live table schema via the `get_table_schema` tool at runtime) → saves ~1,500 chars
2. **Condense NL phrasing repetitions** (if `metrics_dictionary.md` already lists phrasings, don't repeat them in the system prompt) → saves ~500 chars
3. **Remove verbose examples** in CRITICAL RULES (keep imperative bullets, drop multi-line explanations) → saves ~300 chars
4. **Shorten Key Business Facts** (2-3 facts max, not 5-10) → saves ~200 chars
5. **Combine multiple rules into concise bullets** (e.g., "Fan-out detection: check row counts; if increased >10%, investigate JOIN cardinality" instead of a full paragraph) → saves ~200 chars

**Pre-push check:**
```bash
wc -c ./<project-name>/agents/knowledge_bases/prompt.md
# If output > 9000: trim using the cut-order above, then re-check with wc -c
# Push only after confirmed ≤ 9000 chars
```

**Rules go FIRST.** LLM attention is highest at the beginning of the prompt — behavioral constraints must be at the top to get maximum weight.

```
CORRECT:
1. CRITICAL RULE 1 — Execute, Don't Explain
2. CRITICAL RULE 2 — Respond with Results
3. CRITICAL RULE 3 — Fan-Out Detection
4. CRITICAL RULE 4 — Exclusions (add one rule per confirmed exclusion from Phase 2/3)
5. Context / table references
6. Persona detection
7. Error handling

WRONG:
1. Welcome / context
2. Tables / metrics
5. ← Rules at bottom (low attention weight)
```

**Knowledge base location:**

```
./<project-name>/agents/knowledge_bases/
├── prompt.md            ← behavioral rules first
├── sink_sales_revenue.yml      ← one .yml per SINK table — schema + confirmed totals
├── sink_customer_segments.yml  ← one .yml per SINK table
├── business_context.md         ← stub on first push; full distillation post-validation
├── metrics_dictionary.md       ← stub on first push; full definitions post-validation
└── sql_templates.md            ← 2 templates on first push; full set post-validation
```

### Re-push After Validation

After the dashboard is validated and Round 1 test failures are analyzed:

| File | Action | Source |
|------|--------|--------|
| `business_context.md` | Full distillation — replace stub; add a `## Exclusion Rules` section (required even if empty — state explicitly that none were found) | Customer-validated Phase 1/3 inferences |
| `metrics_dictionary.md` | Full definitions — all NL phrasings + confirmed SQL; match **Excludes:** to the actual WHERE clauses | Phase 3 final queries, Phase 1 formulas |
| `sql_templates.md` | All templates + customer-specific NL patterns | Phase 3 validated queries + Round 1 test failure patterns |
| `prompt.md` | Add a CRITICAL RULE for each exclusion found during validation | Test failure analysis |
| `<table>.yml` (each per-table file) | Update column descriptions if the schema changed | Phase 3 final schema |

**Example `sink_sales_revenue.yml` with `confirmed_totals` and `grain`:**

```yaml
name: sink_sales_revenue
type: database
database: td_reporting_agents
tables:
  - name: sink_sales_revenue
    td_query: "SELECT * FROM <sink_db>.sink_sales_revenue LIMIT 1000"
    grain: "one row per order_date x region x channel"
    confirmed_totals:
      total_revenue: 1284302.55   # from Phase 1/3 spot-check — agent should match this within 1%
enable_data: false
enable_data_index: false
```

**Example `metrics_dictionary.md` entry format:**

```markdown
## Total Revenue

**Plain English:** Sum of completed order revenue, excluding refunds and test accounts.
**SQL formula:** `SUM(revenue) WHERE status = 'completed' AND is_test_account = false`
**Includes:** all completed orders across all channels
**Excludes:** refunded orders, cancelled orders, test accounts (account_id IN test list)
**NL phrasings:** "total revenue", "how much did we make", "sales total"
```

---

## Step 4b-v: Deploy Agent to Foundry

No cloning is required — this is a self-contained deploy sequence using `tdx` directly.

**Step 1 — Choose a Foundry project name.** Default to the `<project-name>` unless the user prefers a different name.

**Step 2 — Create (or confirm) the Foundry project:**
```bash
tdx llm project list | grep -i "<project-name>"
# If not found:
tdx llm project create <project-name>
```

**⚠️ Before creating a new Foundry project, get user confirmation:**

```
AskUserQuestion:
  header: "Create Foundry project"
  question: "Create new Foundry project: <project-name>?"
  options:
    - label: "Yes, create now"
      description: "Create project: tdx llm project create <project-name>"
    - label: "No, use existing"
      description: "Use an existing Foundry project (enter name)"
    - label: "Cancel — review first"
      description: "Let me review before creating"
```

**Only run `tdx llm project create` after user explicitly selects "Yes, create now".**

**Step 3 — Confirm knowledge bases are ready for the push round:**
- Round 1: `prompt.md` + per-table `.yml` files fully populated, other 3 files stubbed
- Round 2: all KB files fully populated

**Pre-Push Verification Checklist (run these commands BEFORE proceeding):**

```bash
# 1. Verify prompt.md character count (max 9,000 chars)
wc -c ./<project-name>/agents/<project-name>/prompt.md
# If > 9000: trim using the cut-order on line 336-341, re-check

# 2. Verify text KB character counts (max ~18,000 chars each)
wc -c ./<project-name>/agents/<project-name>/knowledge_bases/business_context.md
wc -c ./<project-name>/agents/<project-name>/knowledge_bases/metrics_dictionary.md
wc -c ./<project-name>/agents/<project-name>/knowledge_bases/sql_templates.md
# If any > 18000: trim by removing examples or condensing descriptions, re-check

# 3. Verify all per-table .yml files exist and have confirmed_totals
ls ./<project-name>/agents/<project-name>/knowledge_bases/*.yml
# Each should have confirmed_totals: field with actual values

# 4. Verify agent.yml exists and model name is in Foundry format
grep "model:" ./<project-name>/agents/<project-name>/agent.yml
# Should show: model: claude-opus-4-6  OR  model: claude-4.5-sonnet
# NOT Claude API format (claude-opus-4-8, claude-sonnet-4-6)
```

**Pass all four checks before pushing.**

**Step 4 — CONFIRMATION GATE — Show the deployment preview before pushing:**

Display the proposed deployment config to the user (never auto-push):

```
AskUserQuestion:
  header: "Review before deploying to Foundry"
  question: "Ready to deploy this agent to Foundry? Review the config below and confirm:"
  options:
    - label: "Yes, deploy now"
      description: "Push to Foundry: tdx agent push -y"
    - label: "No, let me review the KBs first"
      description: "Cancel this push. I want to review/edit the knowledge bases"
    - label: "No, cancel Track B"
      description: "Skip the agent deployment entirely"
```

**Show this preview to the user:**
```markdown
**Foundry Deployment Preview:**
- Project name: <project-name>
- Agent name: <agent-name>
- Knowledge bases ready:
  - prompt.md: [file size] chars
  - <table>.yml (one per SINK table): [N table .yml files listed]
  - business_context.md: [stub|full]
  - metrics_dictionary.md: [stub|full]
  - sql_templates.md: [stub|full]
- Deployment round: Round 1 or 2
- Location: `./<project-name>/agents/`
```

**If user selects "Yes, deploy now":**

**CRITICAL — Step 4b-v, Sub-step 1 (REQUIRED BEFORE PUSH):**
```bash
# Ensure the Foundry project exists FIRST
# If skipped, you'll get: LLM_PROJECT_NOT_FOUND error when running tdx agent push
tdx llm project create <project-name>
# This is safe to run even if the project already exists (idempotent)
```

**Step 5 — Push:**
```bash
cd ./<project-name>/agents/<project-name>
# CRITICAL: cd into the project folder (contains tdx.json + agent.yml + prompt.md)
# NOT just the parent agents/ folder
tdx agent push -y
```

⚠️ **If you get `LLM_PROJECT_NOT_FOUND` error:** you skipped the `tdx llm project create` step above. Go back and run it, then retry `tdx agent push -y`.

**Step 6 — Verify in the Foundry UI:**
- Confirm the agent project is visible and the KB files uploaded correctly
- Open the chat interface and send a simple test query (e.g., "what tables do you have access to?")

**If user selects "No, let me review" or "Cancel":**
- Return to Step 4b-iv to edit KBs, or exit Track B entirely

**Step 7 — Record the deployment** in `state.md`: agent name, project name, push timestamp, KB round (1 or 2).

Append to `state.md`:
```markdown
## Phase 4 Track B: Foundry Agent Deployed (YYYY-MM-DD)

- agent_name: [confirmed-agent-name]
- Capabilities: [Insights | Dashboard Generation | Reporting | Orchestration]
- Knowledge bases: [KB1, KB2, ...]
- Deployment timestamp: [ISO date]
- Ready for: User Q&A in Treasure AI Studio, scheduled reports (if Reporting capability enabled)
```

---

## Step 4b-vi: Test Agent with Validation Suite (15 min + iteration)

**⛔ Gate before running:** confirm KBs are ready for the round you're running.

- **Round 1 (first push):** `prompt.md` fully populated + all per-table `.yml` files fully populated. Stubs for the other 3 files are acceptable — Round 1 failures tell you what to add before Round 2.
- **Round 2 (post-validation re-push):** all KB files fully populated (not stubs). `business_context.md` has a `## Exclusion Rules` section.

Ask before running: *"KBs ready for Round [1/2]? Reply **run** to execute `tdx agent test --run all`."* Wait for explicit confirmation before executing.

**5-Test Validation Summary:**

| Test | What it catches | Pass condition |
|------|----------------|----------------|
| 1 — Connectivity | DB access, auth, basic query | Returns the confirmed total (within 1%) |
| 2 — Trend | Date filtering, temporal aggregation | Trend direction matches the dashboard; correct date range |
| 3 — Dimension Breakdown | GROUP BY logic, all values present | Sum across all values = overall total |
| 4 — Error Handling | Graceful failure, no crashes | No raw SQL errors; helpful alternatives offered |
| 5 — Business Question | NL→SQL, context usage, reasoning | Logical answer with real numbers from dashboard data |

Run each test as a direct chat prompt to the agent using `tdx chat`:

```bash
tdx chat --agent "<project-name>/<agent-name>" --new "your test question here"
```

**Example test queries:**
- Test 1: `tdx chat --agent "automotive-demo/automotive-analyzer" --new "How many total orders are in the dataset?"`
- Test 2: `tdx chat --agent "automotive-demo/automotive-analyzer" --new "How did revenue trend over the last 30 days?"`
- Test 3: `tdx chat --agent "automotive-demo/automotive-analyzer" --new "Break down revenue by region."`
- Test 4: `tdx chat --agent "automotive-demo/automotive-analyzer" --new "What's the nonsense_metric_that_doesnt_exist?"` — agent should decline gracefully, not error
- Test 5: `tdx chat --agent "automotive-demo/automotive-analyzer" --new "What's driving the change in revenue this month?"`

**Or run the full automated validation suite:**
```bash
cd ./<project-name>/agents
tdx agent test --run all
```

### Failure-to-Fix Quick Reference

| Symptom | Fix |
|---------|-----|
| Agent describes instead of executes (any test) | `prompt.md` → CRITICAL RULE 1 must be line 1 |
| Test 1 returns wrong total | Per-table `.yml` → `confirmed_totals`; check `sql_templates.md` KPI-summary template's GROUP BY |
| Test 3 dimension totals don't match | `sql_templates.md` breakdown template → add all grain columns to GROUP BY |
| Test 5 metric value wrong | `metrics_dictionary.md` → **Excludes:** field must match the actual WHERE clause |
| Agent ignores an exclusion | `prompt.md` → add a numbered CRITICAL RULE for that exclusion |

### Iteration with --reeval

```bash
# First round: run all
tdx agent test --run all

# Re-run only failed tests after fixing (saves most of the iteration time):
tdx agent test --reeval --name "trend-analysis"
tdx agent test --reeval --name "dimension-breakdown"
```

**When to use `--reeval`:**
- ✅ Fixing behavioral issues (agent describes instead of executes, wrong prompt)
- ✅ Same Foundry project, same database schema
- ❌ NOT for schema changes → re-run the full suite with `--run all`
- ❌ NOT after pushing code changes → use `--run all`

---

## Track B Output

✅ `agents/knowledge_bases/` — `prompt.md`, one `.yml` file per SINK table, `business_context.md`, `metrics_dictionary.md`, `sql_templates.md` — all fully populated after Round 2
✅ `agents/capabilities.md` — chosen capabilities + intent-routing logic
✅ `agents/compliance-gate.md` — compliance check result (if a flag was raised in Phase 1)
✅ Deployed, verified Foundry agent passing the 5-test validation suite

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team

---

## Troubleshooting: Foundry Agent Test Failures

**Scenario:** Agent test fails (Step 4b-v). What went wrong?

### Test failure types:

| Symptom | Cause | Fix |
|---|---|---|
| **Agent returns wrong data** | System prompt unclear on data scope/filtering | Refine prompt: clarify table names, add example queries |
| **Agent queries fail (401/403)** | Agent lacks TD credentials or wrong account context | Run `tdx auth setup` in agent working directory + verify `~/.tdx/profile.cfg` |
| **Agent returns generic response** | Tools not registered or knowledge base unavailable | Verify `tools:` array in agent.yml, re-run `tdx agent pull` |
| **Agent loops/repeats queries** | Query is too complex; agent re-tries same logic | Simplify prompt or add "Stop after 2 queries" constraint |
| **Test criteria never satisfied** | Criteria too strict or misaligned with agent goal | Review criteria in test.yml; loosen if reasonable or clarify agent prompt |

### Troubleshooting checklist:

- [ ] **Check agent credentials:** `tdx auth setup` + verify profile
- [ ] **Test agent manually:** Run `tdx agent chat <agent-name>` directly with test query
- [ ] **Review system prompt:** Is it clear on scope, tables, filters?
- [ ] **Check knowledge base:** Does knowledge/ folder have current business_context.md + data_dictionary.md?
- [ ] **Review test.yml:** Are criteria realistic? Can you manually satisfy them?
- [ ] **Run with --verbose:** `tdx agent test <agent-name> --verbose` to see query-by-query trace
- [ ] **Check for timeouts:** Add `timeout: 60` to test.yml if queries are slow

### Beyond --reeval:

If `--reeval` isn't enough:

1. **Rewrite agent system prompt** (simplify, add constraints)
2. **Adjust test criteria** (less strict, more achievable)
3. **Add context to knowledge base** (more examples, clearer definitions)
4. **Validate data** (run test query manually; does it return expected results?)

---

---

## Troubleshooting: tdx agent test Failures (Beyond --reeval)

### Common Failure Codes & Fixes

| Error | Cause | Fix |
|---|---|---|
| **Query timeout (>30s)** | Query is too slow or hits large table | Optimize query (LIMIT, pre-agg), or increase timeout in test.yml |
| **Prompt exceeds 9K chars** | System prompt or knowledge base too large | Trim prompt, move verbose docs to separate knowledge file |
| **Table not found** | Agent can't find table in knowledge base | Verify data_dictionary.md has table name, re-run `tdx agent pull` |
| **Intent routing confusion** | Agent misunderstands what user is asking | Clarify system prompt with examples, add "Stop after 1 query" constraint |
| **0% test pass rate** | Criteria too strict OR agent fundamentally broken | Loosen criteria first; if still fails, review system prompt + knowledge base |
| **Agent returns generic response** | Tools not available or agent ignores them | Check `tools:` array in agent.yml, verify credentials (`tdx auth setup`) |

### Diagnostic Steps

1. **Run test with verbose output:**
   ```bash
   tdx agent test <agent-name> --verbose 2>&1 | tee test-run.log
   ```
   → Shows query-by-query trace + query results

2. **Test agent manually:**
   ```bash
   tdx agent chat <agent-name>
   # Type the exact test query and observe response
   ```

3. **Check credentials:**
   ```bash
   tdx auth status
   tdx auth setup  # If needed
   ```

4. **Validate knowledge base:**
   ```bash
   ls -lah ./<project-name>/skills/knowledge/
   # Verify all files exist and aren't empty
   ```

5. **Validate agent YAML:**
   ```bash
   tdx agent validate <agent-name>
   # Checks for syntax errors, missing fields, etc.
   ```

### Per-Failure Recovery

**Symptom: Query timeout**
```bash
# Increase timeout in test.yml
timeout: 60  # Was default 30

# Or optimize query in knowledge base
# - Add LIMIT 1000 to expensive queries
# - Pre-aggregate fact tables
# - Remove JOINs if possible
```

**Symptom: Prompt too large**
```markdown
# In agent-prompt-template.md, remove verbose sections:
- Delete multi-paragraph explanations (keep 1 sentence)
- Move examples to knowledge base instead of prompt
- Remove commented-out sections
```

**Symptom: Agent doesn't use tools**
- Verify `tools:` array in agent.yml lists at least 1 tool
- Check that tools are registered: `tdx agent pull <agent-name>`
- Add explicit tool use instruction to prompt: "You have access to the `td_query` tool. Use it to answer questions."

**Symptom: Test criteria never satisfied**
- Loosen criteria first: `criteria: "Agent returns non-empty response"` (easier to pass)
- If still fails, issue is agent/knowledge base, not criteria
- Review system prompt for clarity + add 1-2 examples of good queries

---

