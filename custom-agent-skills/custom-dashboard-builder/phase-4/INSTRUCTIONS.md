---
name: phase-4-instructions
description: Phase 4 specific instructions for automation and agent deployment
priority: MEDIUM
load_order: 1.4
---

# Phase 4 Instructions — Automate & Deploy Agents

**Read this BEFORE `./SKILL.md`.**

**Phase 4 is OPTIONAL (after Phase 3 approved).**

---

## Phase 4 Goal

Extend the dashboard with two optional automation tracks:

**Option A (Recommended): Extract Reusable Skill**
- Convert Phase 3 dashboard to a reusable Claude Code skill installed to `~/.claude/skills/<skill-name>/` 
- Enables faster builds of similar dashboards in the future (10× speedup on next build)
- Users can ask deep-dive natural-language questions like "Which region has the highest growth?" and get live answers
- Available across all Claude Code sessions (plus optional zip file for sharing with team)

**Option B: Deploy Conversational Agent** 
- Create a Foundry agent with access to dashboard data (external-API-only use case)
- Only applicable if you need to make this dashboard available to users outside Treasure AI Studio
- Users can ask questions in natural language from external systems via API
- Advanced: Agent queries data on-the-fly or uses precomputed tables

**Deliverable:**
- Option A: A reusable skill installed to `~/.claude/skills/<skill-name>/` — available across all Claude Code sessions (plus optional zip file for sharing with team)
- Option B: A Foundry agent project deployed with knowledge bases
- state.md appended with Phase 4 results

---

## Pre-Execution Validation (Checkpoint)

**Cannot execute Phase 4 without validating:**

From `state.md` Phase 3 section, verify:
- ✅ Phase 3 marked ✅ Complete
- ✅ Dashboard approved by user (approval recorded)
- ✅ Data accuracy validated (spot-checks documented)
- ✅ Performance acceptable (query times recorded)

**Runtime validation before deploying agent (Track B only):**
```bash
# Verify dashboard data is current
tdx describe <SINK_DB>.<SINK_table>  # or source table if Phase 2 skipped
SELECT COUNT(*) FROM <table>          # Verify recent data

# Run one spot-check from state.md:
SELECT [KPI] FROM [table] WHERE [filter]
# Compare against spot-check value in state.md Phase 3 section
```

**If spot-check is STALE (> 1 day old):**
→ WARN: "Dashboard data may be stale. Re-run Phase 3 queries first?"
→ User decides: update dashboard or proceed with existing data

**If ANY validation FAILS:**
→ STOP: "Prerequisite validation failed: [reason]"
→ User action: Go back to Phase 3 and refresh data

---

## Quick Checklist (Quick Reference)

**Pre-Phase-4 Gate**
- [ ] Phase 3 complete (dashboard.html approved)
- [ ] Phase 2 complete (SINK ready) OR skipped (querying source)
- [ ] state.md updated through Phase 3
- [ ] User decided: Track A, Track B, both, or neither?

**Option A: Extract Reusable Skill (CORRECT ORDER)**
- [ ] 4a-0: Ask scope questions FIRST (name, install scope, known values) ← GATE 1
- [ ] 4a-0b: Hardcode all known values in SKILL.md (replace <PLACEHOLDER> with actual values)
- [ ] 4a-0c: Get approval before packaging
- [ ] 4a-i: Extract dashboard skill definition
- [ ] 4a-ii: Extract & parameterize query scripts (verify hardcoded DBs used)
- [ ] 4a-iii: Create configuration templates (zero placeholders)
- [ ] 4a-iv: Document deployment checklist (one-command: npm run build)
- [ ] 4a-v: Validate skill end-to-end (spot-check ±5%)
- [ ] 4a-vi: Final packaging (Python zipfile, not zip CLI)
- [ ] 4a-vii: Generate Installation Guide (hardcoded values visible)

**Option B: Deploy Foundry Agent**
- [ ] 4b-i/ii: Decide agent + capability
- [ ] 4b-iii: Pre-flight checks (access, data, compliance)
- [ ] 4b-iv: Configure knowledge bases (system_prompt.md ≤ 9KB)
- [ ] 4b-v: Deploy agent (`tdx agent push`)
- [ ] 4b-vi: Test agent (`tdx agent test`)

**Phase 4 → Phase 5 Handoff**
- [ ] Update state.md with track(s) run
- [ ] Record skill name (Track A) or agent name (Track B)
- [ ] Inform user: Phase 5 (optional) or close engagement

---

---

## ✅ Before You Proceed: Required Reads

**Before executing Phase 4 (both Track A and Track B), read these reference files:**

**Track A (Skill Extraction):**
- **`./references/track-a-automation.md`** — Skill packaging and extraction best practices
- **No extra template reads** — Phase 3 hardcodes the skill definition directly from dashboard.html

**Track B (Agent Deployment):**
- **`./references/templates/agent-prompt-template.md`** — Standard agent prompt template (147 lines) — **READ BEFORE writing agent prompt**
- **`./references/templates/knowledge-base-system-prompt-template.md`** — System prompt KB template
- **`./references/templates/knowledge-base-business-context-template.md`** — Business context KB template
- **`./references/templates/knowledge-base-data-dictionary-template.md`** — Data dictionary KB template
- **`./references/templates/knowledge-base-metrics-sql-template.md`** — Metrics & SQL KB template

**Why these reads matter:**
- `agent-prompt-template.md` ensures all 6 CRITICAL RULES are encoded (not invented from scratch)
- KB templates ensure consistent structure across all 4 knowledge base files; prevents one-off formatting

---


## ⚠️ Blocking Phase 4 Gate

Read `../references/execution-contract.md` and select Track A/B with `AskUserQuestion`; never infer the track. Track A must show the full Step 4a-vi packaging instructions after `generate-data.js` validation, even when a zip already exists. Track B must pass staging tests and receive approval before production deployment.

## Phase 4 Specific Rules (In Addition to Universal Rules)

### Rule P4-0: Dry-Run First (Track B Agent Only)

**⚠️ CRITICAL (Track B only): Test agent with sample queries BEFORE deployment.**

**Step 1: Deploy agent to staging/test environment**

```bash
# Create agent in test project (not production)
tdx agent push --project [project_name]-test
```

**Step 2: Run sample queries to verify KB accuracy**

Test the knowledge base:
```
Query 1: "What is the total revenue for last month?"
  KB says: Revenue table = [table_name]
  Agent queries: SELECT SUM(revenue) FROM [table_name]...
  Result: Returns value ✓

Query 2: "Show me customers by region"
  KB says: Regions available = US, EU, APAC
  Agent queries: SELECT * FROM [table] WHERE region IN (...)
  Result: Returns expected regions ✓

Query 3: "What's the churn rate?"
  KB says: Churn rate = (churned / total) customers
  Agent queries: SELECT COUNT(*) ... correctly calculates ✓
```

**Step 3: Verify KB spot-checks**

Before production deployment:
- [ ] All tables referenced in KB actually exist in TD
- [ ] All sample values in KB are current (not stale)
- [ ] All query patterns in KB run without errors
- [ ] Agent responds with expected data (no hallucinations)

**If any test fails:**
- Fix KB (update table names, refresh spot-check values)
- Redeploy to test
- Re-run tests
- Repeat until all pass

**Step 4: Only after all tests pass**
- Deploy to production
- Proceed to approval gate

**Why:** Agent KB accuracy = trust. Testing in staging prevents production failures.

---

### Rule P4-1: Track A Approval Gate — Skill Creation (ENFORCEMENT)

**⚠️ CRITICAL: CANNOT extract skill without explicit user approval.**

**Step 1: Present approval template (COPY/PASTE exactly):**

```
📋 Ready to create reusable skill:

Skill Name: [name]
Description: [1-2 sentences]

Skill will:
  • Accept similar data structures (same source tables/columns)
  • Generate dashboard.html in <30 minutes (typical)
  • Be shareable with other teams
  • Be stored at: [path]

Skill components:
  • SKILL.md (instructions)
  • INSTRUCTIONS.md (rules)
  • Quick Checklist in INSTRUCTIONS.md (quick reference)
  • references/ (query templates, theme)
  • tests/ (end-to-end verification)

To approve, please type exactly: YES, APPROVE SKILL EXTRACTION FOR [SKILL_NAME]
```

**Step 2: Wait for response**
- If user types: "YES, APPROVE SKILL EXTRACTION FOR [SKILL_NAME]" → Proceed ✓
- If user types: "NO" or anything else → **STOP** ✗

**Step 3: If NO**
- Do not create skill
- Ask: "Would you like to skip Track A?"
- If yes: Move to Track B or Phase 5

**If user says "just extract it":**
> "I cannot proceed without explicit approval. Skill extraction creates a new asset that will be reused across projects. I need your confirmation.
>
> Please type exactly: YES, APPROVE SKILL EXTRACTION FOR [SKILL_NAME]"

---

### Rule P4-1a: Scope Question Timing (REQUIRED BEFORE FILE CREATION)

**⚠️ CRITICAL: Ask scope BEFORE creating any skill files. Do NOT ask after packaging.**

**Scope questions to ask (IN THIS ORDER):**

1. **Skill name:** What should this skill be called?
   - Example: "retail-revenue-dashboard", "retail-analytics-builder"
   - Use business-friendly names (avoid technical naming conventions)

2. **Installation scope:** Where should this skill be installed?
   - **Option A (Recommended): Project-local Installation** — Install to `~/.claude/skills/<skill-name>/` for cross-project reuse across all your sessions
   - **Option B:** Zip distribution — Package as shareable zip for team members to install locally
   - **Option C:** Both — Save locally for immediate use + create zip for sharing

3. **Known values to hardcode:**
   - SINK database name (if Phase 2 completed)
   - Source database name (if querying source)
   - Absolute paths to `generate-data.js`
   - Paths to dashboard template

**ONLY AFTER user confirms all three:**
- Create SKILL.md
- Package files
- Show approval gate

**Example conversation:**
```
Me: "Ready to extract Track A skill. Let's scope it first.

1. What should we call this skill?
   → 'fde-retail-analytics'

2. Where do you want this installed?
   → 'Personal workspace'

3. Known values I should hardcode:
   - SINK_DB = 'warehouse_sink'
   - SRC_DB = 'raw_events'
   → Confirm? ✓

Great. Now I'll create the skill with those values hardcoded.
I'll show you the approval template next."
```

**Why:** Asking late means reworking files after they're created. Ask early, code once.

---

### Rule P4-1b: Hardcode Known Values in Extracted Skill (ENFORCEMENT)

**⚠️ CRITICAL: The extracted skill MUST NOT ask for values again.**

When extracting a skill in Track A, hardcode ALL known values into SKILL.md:

❌ **WRONG:**
```markdown
## Configuration

Edit `generate-data.js` before running:

```bash
SOURCE_DB=???? node generate-data.js
# User must remember to set SOURCE_DB
```

✅ **RIGHT:**
```markdown
## Configuration

The skill is pre-configured for your environment:

**Hardcoded values (from your project):**
- SINK_DB = warehouse_sink
- SRC_DB = raw_events
- SINK_SCHEMA = [table list with columns]
- Dashboard template path = ./references/retail-dashboard.html

No configuration needed. Run immediately:

```bash
node generate-data.js  # uses hardcoded values
```
```

**Hardcode checklist:**
- [ ] `SINK_DB` (if Phase 2 completed)
- [ ] `SRC_DB` (if querying source)
- [ ] Database names in SQL queries
- [ ] Table names in SQL queries
- [ ] Absolute paths to scripts and templates
- [ ] Schedule frequency (if applicable)
- [ ] Date range defaults
- [ ] Metric definitions (column names, aggregations)

**In SKILL.md, create a "Quick Start" section:**

```markdown
## Quick Start

### 1-Command Setup
\`\`\`bash
# Everything is pre-configured. Just run:
npm install
node generate-data.js

# Output: dashboard.html (ready to share)
\`\`\`

### Pre-Configured Values
| Variable | Value | Source |
|----------|-------|--------|
| SINK_DB | warehouse_sink | From Phase 2 |
| SRC_DB | raw_events | From Phase 1 |
| Dashboard template | ./templates/unified-dashboard.html | Included |

### To Customize Later
If you need to adapt this skill for a different project:
1. Edit [config file] with new database names
2. Update queries in [queries folder]
3. Re-run node generate-data.js
```

**Why:** The whole point of extraction is reusability WITHOUT asking the same questions again. If the extracted skill asks for config, it defeats the purpose.

---

### Rule P4-1c: One-Command Skill Execution (ENFORCEMENT — NON-NEGOTIABLE)

**⚠️ CRITICAL: Extracted skill MUST run with ONE command. No questions, no config, no prompts.**

**The goal of skill extraction:**
```
User runs: npm run build
           ↓
Skill uses pre-hardcoded values
           ↓
Dashboard.html created + data injected
           ↓
Done (< 5 minutes)
```

**NOT this (defeats skill purpose):**
```
User runs: node generate-data.js
           ↓
Skill asks: "Which database contains your SINK tables?" ❌
Skill asks: "Which queries do you want to run?" ❌
Skill asks: "Which template should we use?" ❌
           ↓
User configures (defeats reusability)
```

**Hardcoding checklist (BEFORE skill is extracted):**

❌ **FAIL: Skill will ask questions if any of these are missing:**

```
Hardcoded Database:
  - [ ] SINK_DB hardcoded in generate-data.js: SINK_DB = 'warehouse_sink'
  - [ ] SRC_DB hardcoded in generate-data.js: SRC_DB = 'raw_events'
  - If MISSING: Skill will ask "Which database?" ❌

Hardcoded Queries:
  - [ ] Metrics query hardcoded: SELECT SUM(amount) FROM ${SINK_DB}...
  - [ ] Chart data query hardcoded: SELECT DATE, region, SUM(amount) FROM ${SINK_DB}...
  - [ ] Rows query hardcoded: SELECT * FROM ${SINK_DB}.orders...
  - If MISSING: Skill will ask "Which queries?" ❌

Hardcoded Paths:
  - [ ] Dashboard template path: ./references/unified-dashboard.html
  - [ ] Output path: ./output/dashboard.html
  - If MISSING: Skill will ask "Where should I put the output?" ❌

Hardcoded Schedule (if workflow):
  - [ ] Workflow schedule: daily at 02:00 UTC
  - [ ] Retention: 365 days
  - If MISSING: Skill will ask "How often should it run?" ❌

SKILL.MD Template (no placeholders, no ???? values):
  - [ ] SKILL.md lists exact DB names
  - [ ] SKILL.md lists exact query file paths
  - [ ] SKILL.md lists exact template paths
  - [ ] Zero "edit this value" instructions (should say "already configured")
  - If any placeholder remains: Skill will ask ❌
```

✅ **PASS: Skill runs one-command if ALL are hardcoded:**

```bash
# User does this ONLY:
npm install
npm run build

# Skill does the rest automatically:
#   - Connects to warehouse_sink (hardcoded)
#   - Runs existing queries (hardcoded paths)
#   - Uses unified-dashboard.html (hardcoded path)
#   - Injects data
#   - Outputs dashboard.html
#   - Done
```

**Validation before extraction:**

```yaml
### Pre-Extraction Hardcoding Audit

SINK Database:
  - SINK_DB = 'warehouse_sink' ✓ (hardcoded in line 5 of generate-data.js)
  - SRC_DB = 'raw_events' ✓ (hardcoded in line 6)

Queries:
  - queries/metrics.sql ✓ (path hardcoded, SELECT ... FROM warehouse_sink)
  - queries/chart-data.sql ✓ (path hardcoded, SELECT ... FROM warehouse_sink)
  - queries/rows.sql ✓ (path hardcoded, SELECT ... FROM warehouse_sink)

Paths:
  - Dashboard template: ./references/unified-dashboard.html ✓
  - Output: ./output/dashboard.html ✓

Schedule (if Phase 2 SINK):
  - Workflow frequency: daily at 02:00 UTC ✓

SKILL.md Content:
  ```
  ## Quick Start
  npm install
  npm run build
  # Output: ./output/dashboard.html
  
  Pre-Configured:
  - Database: warehouse_sink
  - Queries: ./queries/*.sql (metrics, chart-data, rows)
  - Template: ./references/unified-dashboard.html
  - Schedule: Daily 02:00 UTC
  
  No configuration needed. All values are hardcoded.
  ```

Result: ✅ PASS (ready for extraction)
```

**If ANY value is not hardcoded:**
- ❌ STOP extraction
- List what's missing (e.g., "SINK_DB is still a placeholder")
- Have user confirm the values
- Hardcode them
- Then extract skill

**Example of what NOT to do (❌ WILL FAIL):**

```javascript
// generate-data.js (before extraction)
const SINK_DB = process.env.SINK_DB || '????';  // ❌ NOT HARDCODED
const SRC_DB = process.env.SRC_DB || '????';    // ❌ NOT HARDCODED

// User runs: node generate-data.js
// Skill asks: "Which database contains your SINK tables?"
// Defeats skill purpose ❌
```

**Example of what TO do (✅ WILL WORK):**

```javascript
// generate-data.js (before extraction)
const SINK_DB = 'warehouse_sink';  // ✅ HARDCODED
const SRC_DB = 'raw_events';        // ✅ HARDCODED

// User runs: npm run build
// Skill uses hardcoded values
// Dashboard created in 2 minutes ✅
```

**Why:** Extracted skill's entire value is "build fast without repeating setup". If skill asks the same questions as Phase 1-4, it's not a skill, it's just the same process again. Defeats the purpose.

**Past incident:** Extracted skill asked "Which database contains your SINK tables?" User had to look up the answer from the original project. Extraction was useless — user could have just run the original dashboard again. Defeated 10x speedup promise.

---

### Rule P4-2: Track B Approval Gate — Agent Creation (ENFORCEMENT)

**⚠️ CRITICAL: CANNOT deploy agent without explicit user approval.**

**Step 1: Present approval template (COPY/PASTE exactly):**

```
📋 Ready to deploy Foundry agent:

Agent Name: [name]
Description: [1-2 sentences]

Agent capabilities:
  • Answer natural language questions about dashboard metrics
  • Query live or precomputed tables
  • Support conversational analysis
  • Audit trail (all queries logged, read-only access)

Cost impact:
  • Agent queries cost: ~$X per query
  • Monthly estimate: ~$X (depending on usage)
  • Monthly budget alert: [set if applicable]

Access control:
  • Who can access: [internal / shared / public]
  • Permissions: Read-only (SELECT only, no INSERT/UPDATE/DELETE)
  • Can be disabled: Yes (by revoking permissions)

To approve, please type exactly: YES, APPROVE AGENT DEPLOYMENT FOR [AGENT_NAME]
```

**Step 2: Wait for response**
- If user types: "YES, APPROVE AGENT DEPLOYMENT FOR [AGENT_NAME]" → Proceed ✓
- If user types: "NO" or anything else → **STOP** ✗

**Step 3: If NO**
- Do not deploy agent
- Ask: "Would you like to skip Track B?"
- If yes: Move to Phase 5

**If user says "just deploy it":**
> "I cannot proceed without explicit approval. Agent deployment creates a new conversational interface to your data. I need your confirmation.
>
> Please type exactly: YES, APPROVE AGENT DEPLOYMENT FOR [AGENT_NAME]"

---

### Rule P4-3: Track A — Skill Structure

Extracted skill must follow standard structure:

```
skill-name/
├── SKILL.md (orchestrator + instructions)
├── INSTRUCTIONS.md (skill-specific rules)
├── references/
│   ├── queries/
│   │   ├── kpi_1.sql
│   │   ├── kpi_2.sql
│   │   └── ...
│   ├── templates/
│   │   └── dashboard.html.template
│   ├── treasure-data-theme.md
│   └── [other references]
├── tests/
│   ├── test-query-execution.js
│   ├── test-html-rendering.js
│   └── test-spot-check.js
└── .claude-plugin/
    └── marketplace.json (if shareable)
```

---

### Rule P4-4: Track A — Query Templates Must Be Parameterized

All extracted queries must accept parameters:

```sql
-- ✅ RIGHT: parameterized for reuse
SELECT 
  DATE(event_time) AS date,
  region,
  SUM(amount) AS revenue
FROM {{SOURCE_TABLE}}
WHERE event_time >= '{{START_DATE}}'
  AND event_time < '{{END_DATE}}'
GROUP BY DATE(event_time), region
ORDER BY date DESC, region
```

**Not:**
```sql
-- ❌ WRONG: hardcoded to this project
SELECT ... FROM sales_events WHERE event_time >= '2026-07-01'
```

**Why:** Reusable skill accepts different source tables + date ranges.

---

### Rule P4-4a: Track B — Agent Configuration (agent.yml Format Reference)

**⚠️ REQUIRED: Document full agent.yml structure upfront. No reverse-engineering from live projects.**

**agent.yml structure (complete template):**

```yaml
name: [project_name]-agent
description: Conversational interface for [dashboard name]

tools:
  - type: knowledge_base
    name: [project_name]_kb
    description: Dashboard schema and metric definitions

system_prompt: |
  You are an analytics assistant for [dashboard name].
  
  You have access to a knowledge base describing:
  - Available tables and columns
  - Metric definitions and calculations
  - Business glossary and terms
  
  When users ask questions:
  1. Identify which table/metric they're asking about
  2. Write a Trino/Hive query to fetch the data
  3. Format results clearly (metrics, trends, insights)
  
  Always:
  - Verify the column exists before querying
  - Limit results to top 100 rows for tables
  - Explain your query before returning data

model: claude-opus-4-6  # Foundry model name (NOT Claude API format: claude-opus-4-8)
# Foundry models: claude-opus-4-6, claude-4.5-sonnet (NOT claude-opus-4-8, claude-sonnet-4-6)
temperature: 0.7
max_tokens: 4096

inputs:
  - user_query: # user's natural language question
  
outputs:
  - response: # agent's natural language + data results
```

**⚠️ CRITICAL: Foundry Model Name Format**

Use **Foundry format** (not Claude API format) for the `model:` field:

| Use Case | Foundry Name ✓ | Claude API Name ✗ | Notes |
|----------|---|---|---|
| **Latest Opus** | `claude-opus-4-6` | `claude-opus-4-8` | Use for complex queries, reasoning |
| **Latest Sonnet** | `claude-4.5-sonnet` | `claude-sonnet-4-6` | Recommended for most agents (better speed/cost) |

If you paste Claude API format names (like `claude-opus-4-8`), `tdx agent push` returns a **422 error**. Always use the Foundry column names.

---

**Knowledge base format (project_name_kb.md):**

```markdown
# [Dashboard Name] Knowledge Base

## Available Tables

### Table: sales_events
- **Description:** Raw sales transaction events
- **Columns:**
  - event_id (UUID): Unique transaction ID
  - event_date (DATE): Transaction date
  - region (VARCHAR): Sales region (US, EU, APAC, LATAM)
  - product_category (VARCHAR): Product category
  - revenue (DECIMAL): Sale amount in USD
  - customer_id (INT): Customer identifier

### Table: customers
- **Description:** Customer master data
- **Columns:**
  - customer_id (INT): Unique customer ID
  - customer_name (VARCHAR): Customer name
  - segment (VARCHAR): Customer segment (Premium, Standard, Trial)
  - signup_date (DATE): Account creation date

## Key Metrics

### Total Revenue
- **Definition:** SUM(revenue) from sales_events
- **Time grain:** Can be aggregated by day, week, month, year
- **Example:** Total revenue for last 30 days = $4.8M

### Unique Customers
- **Definition:** COUNT(DISTINCT customer_id) from sales_events
- **Constraints:** Cannot be aggregated across multiple dimensions without accuracy issues
- **Example:** Unique customers in 2026 = 1.2M

## Common Queries

### Revenue by Region
\`\`\`sql
SELECT region, SUM(revenue) as total_revenue
FROM sales_events
WHERE event_date >= DATE_ADD(CURRENT_DATE, -30)
GROUP BY region
ORDER BY total_revenue DESC
\`\`\`

### Top Products
\`\`\`sql
SELECT product_category, SUM(revenue) as revenue, COUNT(*) as orders
FROM sales_events
WHERE event_date >= DATE_ADD(CURRENT_DATE, -30)
GROUP BY product_category
ORDER BY revenue DESC
LIMIT 10
\`\`\`

## Business Glossary

- **Revenue:** Net sales amount after discounts and returns
- **Region:** Geographic sales territory (US=North America, EU=Europe, APAC=Asia-Pacific, LATAM=Latin America)
- **Segment:** Customer tier based on annual spend (Premium >$100K, Standard $10-100K, Trial <$10K)
```

**Why:** Prevents agent from reverse-engineering structure from live projects. Explicit docs = faster setup + fewer errors.

---

### Rule P4-5: Track B — Agent Knowledge Base

Foundry agent knowledge base MUST include:

1. **Schema documentation** (table names, column names, types)
2. **Spot-checked values** (e.g., "Total customers: 1,200,000")
3. **Dimension options** (e.g., "Regions: US, EU, APAC")
4. **Query patterns** (how to filter, aggregate, join)

**Example KB section:**
```yaml
tables:
  - name: sales_revenue
    description: "Daily revenue by region"
    columns:
      - date: "Date (YYYY-MM-DD)"
      - region: "Region code (US, EU, APAC)"
      - revenue: "Revenue amount (USD)"
    verified_values:
      - "Total revenue (all time): $45.2M"
      - "Average daily: $125K"
    sample_query: |
      SELECT SUM(revenue) FROM sales_revenue 
      WHERE date >= '2026-01-01'

dimensions:
  - region: ["US", "EU", "APAC"]
  - date_range: ["Last 7 days", "Last 30 days", "YTD"]
```

---

### Rule P4-6: Track B — Agent Approval Before Tools Access

Foundry agent MUST NOT access production systems without explicit approval:

- [ ] Agent queries are read-only (SELECT only, no INSERT/UPDATE/DELETE)
- [ ] Agent has access to SINK tables (Phase 2) or limited source tables
- [ ] Agent queries are audited (all user queries logged)
- [ ] User can disable agent at any time (revoke permissions)

---

### Rule P4-7: Track A — Skill Must Be Tested End-to-End

Before finalizing extracted skill:

- [ ] Test 1: Use skill to build a dashboard from scratch
- [ ] Test 2: Verify output matches Phase 3 dashboard structure
- [ ] Test 3: Spot-check numbers from Test 1 dashboard against DB

```javascript
// test-skill-end-to-end.js
async function testSkill() {
  // 1. Load skill
  const skill = loadSkill('skill-name');
  
  // 2. Run with test inputs
  const result = await skill.build({
    source_table: 'test_events',
    start_date: '2026-07-01',
    metrics: ['revenue', 'customers']
  });
  
  // 3. Verify output
  assert(result.html_file_exists, 'dashboard.html created');
  assert(result.contains('Total Revenue'), 'KPI present');
  
  // 4. Spot-check
  const dashValue = extractFromHTML(result, 'Total Revenue');
  const dbValue = await queryDB('SELECT SUM(amount) FROM test_events');
  assert(dashValue === dbValue, 'numbers match');
}
```

---

### Rule P4-8: Track B — Agent Knowledge Base Must Be Accurate

Before deploying agent:

- [ ] All table names verified (match actual DB schema)
- [ ] All column names verified (exact spelling, case-sensitive)
- [ ] Spot-checked values confirmed current (not stale)
- [ ] Query patterns tested (run sample queries, verify results)

**Validation checklist:**
```bash
# Verify table exists
tdx describe <db>.sales_revenue

# Verify columns
tdx query "SELECT * FROM sales_revenue LIMIT 1"

# Verify sample aggregate
tdx query "SELECT COUNT(*), SUM(revenue) FROM sales_revenue"
# Compare against KB documented values
```

---

### Rule P4-8a: Track B — Standard 5-Test Validation Template (ENFORCEMENT)

**⚠️ REQUIRED: Test agents with standard 5-test validation BEFORE deployment. Ensures consistent coverage.**

**The 5 tests (run in order):**

```
Test 1: Connectivity
  Query: "How many customers do we have?"
  Expected: Agent connects to KB, queries customer table, returns count
  Status: ✅ (connectivity works) or ❌ (query failed/timeout)

Test 2: Trend/Time-Series
  Query: "What's the revenue trend over the last 30 days?"
  Expected: Agent aggregates by date, shows increasing/decreasing trend
  Status: ✅ (trend query works) or ❌ (dates wrong/nulls/invalid data)

Test 3: Dimension/Grouping
  Query: "Show me revenue by region"
  Expected: Agent groups by region, shows all 6 regions with values
  Status: ✅ (all regions present, values correct) or ❌ (missing regions/wrong names)

Test 4: Error Handling
  Query: "Show me revenue for year 3000" (impossible data)
  Expected: Agent says "no data found" or "outside available range"
  Status: ✅ (graceful error) or ❌ (returns NULL/crashes/wrong value)

Test 5: Business Question
  Query: "Which region had the highest revenue in the last 7 days?"
  Expected: Agent returns correct region + amount, explains reasoning
  Status: ✅ (correct answer + explanation) or ❌ (wrong region/no explanation)
```

**Validation matrix:**

```yaml
### Agent 5-Test Validation

Test 1: Connectivity
  Input: "How many customers do we have?"
  KB says: "Customer table = sales.customers, count field = customer_id"
  Agent response: "1,234,567 customers"
  DB verification: SELECT COUNT(DISTINCT customer_id) FROM sales.customers = 1,234,567
  Status: ✅ PASS

Test 2: Trend
  Input: "Revenue trend last 30 days"
  KB says: "Revenue table = sales.daily_revenue, partition by date"
  Agent response: [Line chart showing 30 days, increasing from $100K to $150K]
  DB verification: SELECT SUM(revenue) BY DATE, verify dates are correct
  Status: ✅ PASS

Test 3: Dimension
  Input: "Revenue by region"
  KB says: "Regions: US, EU, APAC, LATAM, EMEA, Internal"
  Agent response: Shows all 6 regions with values
  DB verification: SELECT DISTINCT region FROM sales.revenue = 6 values
  Status: ✅ PASS

Test 4: Error Handling
  Input: "Revenue for year 3000"
  Expected: "No data available for year 3000"
  Agent response: "Year 3000 is outside available range (2020-2026)"
  Status: ✅ PASS (graceful error)

Test 5: Business Question
  Input: "Top region last 7 days?"
  KB says: "Daily revenue by region available"
  Agent response: "US had highest revenue at $500K in last 7 days"
  DB verification: SELECT region, SUM(revenue) ... ORDER BY revenue DESC = US $500K
  Status: ✅ PASS (correct + explanation)

Overall: ✅ Agent ready for deployment
```

**If any test fails (❌):**
- STOP deployment
- Debug the failure
  - Test 1 failure: KB table name wrong or connectivity issue
  - Test 2 failure: Date aggregation logic broken
  - Test 3 failure: Dimension values not in KB or wrong column names
  - Test 4 failure: Error handling not implemented in KB
  - Test 5 failure: Agent reasoning broken or KB incomplete
- Fix KB or agent prompt
- Re-run all 5 tests
- Only deploy when all 5 pass

**Why:** Inconsistent test coverage leads to unvalidated agents. Standard template ensures every agent tested the same way.

**Past incident:** Agent tested with one custom question, deployed with different KB. Discovered gaps during first user interaction (time-series question broke).

---

### Rule P4-9: State.md Append (Phase 4)

Append Phase 4 results to state.md:

```yaml
---

## Phase 4 — Automate & Deploy Agents
**Date:** [date]
**Status:** ✅ Complete

### Option A: Reusable Skill

- **Skill Name:** [name]
- **Repository:** [path or URL]
- **Status:** ✓ Extracted and tested
- **Tests:** [N] end-to-end tests passing

**Queryable Parameters:**
  - source_table: [default or options]
  - start_date: [format]
  - end_date: [format]
  - metrics: [list]
  - dimensions: [list]

---

### Option B: Foundry Agent

- **Agent Name:** [name]
- **Visibility:** [internal / shared / public]
- **Status:** ✓ Deployed and tested
- **Knowledge Base:** [tables], [dimensions], [verified values]

**Agent Capabilities:**
  - Query 1: [description]
  - Query 2: [description]
  - Query 3: [description]

**Access Control:**
  - Read-only access: ✓
  - Audit logging: ✓
  - Can be disabled: ✓

---

### Validation Results

- [ ] Option A: End-to-end skill test passed
- [ ] Option A: Output matches Phase 3 structure
- [ ] Option B: KB tables verified against DB schema
- [ ] Option B: KB spot-checked values confirmed current
- [ ] Option B: Sample agent queries return expected results

---

## Next Action

1. ✓ Phase 4 complete (optional automation done)
2. Optional: Phase 5 (handoff documentation)
3. Or: Project complete and ready for production
```

---

## Phase 4 Pre-Flight Checklist

**Before starting Phase 4, verify:**

### Prerequisites
- [ ] Phase 3 dashboard is approved and working
- [ ] state.md exists and up-to-date
- [ ] Decision made: Track A (skill), Track B (agent), or both?

### Track A Setup (if chosen)
- [ ] Phase 3 dashboard queries are parameterized
- [ ] Reusable skill structure designed
- [ ] Template variables identified
- [ ] Test plan created

### Track B Setup (if chosen)
- [ ] Foundry agent is new or existing project available
- [ ] Knowledge base schema documented
- [ ] Query patterns identified
- [ ] Access control planned (read-only verified)

---

## Phase 4 Decision Tree

```
START Phase 4: Automate & Deploy Agents
    ↓
Is Phase 3 dashboard approved?
    NO  ↓ → ERROR: Cannot proceed without Phase 3 complete
    YES ↓ → Continue
    ↓
Decide: Track A (skill), Track B (agent), or both?
    ↓
TRACK A FLOW (if chosen):
    ├─ Get user approval (Rule P4-1)
    ├─ Extract queries to templates
    ├─ Create SKILL.md + INSTRUCTIONS.md
    ├─ Create test suite
    ├─ Run end-to-end tests
    ├─ Verify output matches Phase 3
    └─ Finalize + document
    ↓
TRACK B FLOW (if chosen):
    ├─ Get user approval (Rule P4-2)
    ├─ Create/load Foundry agent project
    ├─ Document knowledge base (tables + schema)
    ├─ Add spot-checked values
    ├─ Verify KB against actual DB schema
    ├─ Test sample queries
    ├─ Configure access control (read-only)
    └─ Deploy agent
    ↓
Append Phase 4 results to state.md
    ↓
END Phase 4
```

---

## Common Phase 4 Blocks

### Option A: "How do I make this reusable?"
**Response:**
> "Parameterize the queries: replace hardcoded values with {{PLACEHOLDER}}. For example, {{SOURCE_TABLE}}, {{START_DATE}}, {{METRICS}}. Then the skill can accept these as inputs for any similar project."

### Option B: "My agent is giving wrong numbers"
**Response:**
> "Common causes: (1) KB has stale spot-checked values, (2) KB has wrong table/column names, (3) Sample queries in KB aren't matching actual data. Let me verify KB against current schema and update it."

### Option A: "What if the next project has different columns?"
**Response:**
> "Good question. The skill accepts column names as parameters. So for Project 2 with different columns, you provide a mapping: {original_column} → {project_2_column}. The SKILL.md documents how to do this."

### Option B: "Can the agent write to the database?"
**Response:**
> "No — agent has read-only access (SELECT only). This is a security gate to prevent accidental modifications. If you need write access, that would require separate approval + audit logging."

---

## Phase Progression Gate (CANNOT Skip)

**⚠️ CRITICAL: Before proceeding to Phase 5 (optional), verify:**

- [ ] Phase 3 marked COMPLETE in state.md
- [ ] If Track A chosen: skill extracted and end-to-end tests PASSED
- [ ] If Track B chosen: agent deployed and sample queries tested
- [ ] state.md appended with Phase 4 results:
  - Option A: Skill name, location, test results
  - Option B: Agent name, KB accuracy, sample queries verified
  - Both: Completion status
  - "Next Action" pointer (Phase 5 optional or project complete)

**If ANY item is missing or tests failed:**
> "Cannot proceed. Phase 4 incomplete or tests failed.
> Missing/Failed: [specific item]
> Please complete before moving forward."

**Only after all items verified:**
- Append "Phase 4 COMPLETE" to state.md
- If user wants Phase 5: proceed to phase-5/INSTRUCTIONS.md
- Or project can close (automation done, or skipped)

---

## After Phase 4 Completes (Rule 0: Phase Auto-Advance)

**If Option A (Skill) completes (IMMEDIATE OFFER, ONE QUESTION):**

**Say this (EXACT SCRIPT):**
```
✅ Phase 4 Complete — Reusable Skill Created

### Summary
- Skill: [name] 
- Location: ~/.claude/skills/[name]/
- Benefit: Next similar dashboard builds in 10-30 minutes (vs 2-3 hours)
- Users can ask natural-language questions like "Which brand has the highest growth in GB?" and get live answers

### Next: Final Step?

**Option A:** Phase 5 — Documentation & Handoff (Optional)
→ Create: Architecture diagram, Usage guide, Runbook, Troubleshooting guide
→ Time: 1 hour
→ Benefit: Support team + CS can self-serve, no escalations

**Option B:** Close engagement
→ Skill is production-ready and installed

**→ Continue to Phase 5? (YES/NO)**
```

**If Option B (Agent) completes (IMMEDIATE OFFER, ONE QUESTION):**

**Say this (EXACT SCRIPT):**
```
✅ Phase 4 Complete — Foundry Agent Deployed

### Summary
- Agent: [name]
- Access: External API (users outside Treasure AI Studio can query the data)
- Benefit: Natural-language queries from external systems

### Next: Final Step?

**Option A:** Phase 5 — Documentation & Handoff (Optional)
→ Create: Architecture diagram, Agent usage guide, Troubleshooting
→ Time: 1 hour

**Option B:** Close engagement
→ Agent is deployed and ready

**→ Continue to Phase 5? (YES/NO)**
```

**Then wait for ONE answer and proceed immediately:**
- User says YES → Start Phase 5
- User says NO → "Engagement complete. [Skill/Agent] is ready."

**If both Option A + B completed:**
```
✅ Phase 4 Complete — Skill Created AND Agent Deployed

### Summary
- Skill: [name] (for internal reuse, 10-30 min dashboards)
- Agent: [name] (for external API access)

### Next: Final Step?

**Option A:** Phase 5 — Documentation & Handoff (Optional)
→ Complete handoff docs for both skill and agent

**Option B:** Close engagement
→ Both are production-ready

**→ Continue to Phase 5? (YES/NO)**
```

**Why:** Phase 4 is the last automation step. Must offer Phase 5 immediately after completion, not wait for user to ask.

---

**Version:** 1.0.0
**Last Updated:** 22 July 2026
**Load Order:** 1.4 (read after Phase 1-3 INSTRUCTIONS.md)
