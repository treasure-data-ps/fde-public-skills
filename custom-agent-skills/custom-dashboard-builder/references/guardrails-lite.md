---
name: dashboarding-guardrails-lite
description: |
  Mandatory guardrails for the FDE TAIS Dashboard Builder. Load this file FIRST at the start of every session. Enforces strict rules on data integrity, queries, and HTML Client rendering. Violations cause rework — these are non-negotiable.
load_order: 1
---

# FDE TAIS Dashboard Builder — Guardrails

**Read this after `../INSTRUCTIONS.md` and `./execution-contract.md`, before phase work.**

The execution contract is the completion ledger; this file contains the detailed guardrails.

**Completion status:** Use `./execution-contract.md` as the compact, append-only gate ledger. This file contains the detailed guardrails; the contract determines whether a phase may advance.

**⚠️ CRITICAL — RE-READ THIS AFTER CONTEXT COMPACTION:** If context gets compressed/summarized, or when moving between phases, **STOP and re-read this entire file** before proceeding. Guardrails must not be lost or forgotten due to context boundaries.

These rules are derived from production incidents and real re-work on the full dashboarding-skills solution. Every rule has a reason. Violating any of them has caused rebuilds, wrong customer data, or lost trust in past engagements.

---

## 1. Data Integrity

### NEVER use synthetic, mock, or hardcoded data
Every number in a dashboard must come from a live SQL query result. No estimated values, no "probably around this much", no hardcoded sample arrays. If you don't have a query result yet, don't start building.

**Why:** Customers spot-check dashboards. Wrong numbers destroy trust and require complete rebuilds. Past incident: dashboard showed "New York is #1 destination" — actual top destination was Tokyo with 2× revenue.

### NEVER read raw query output files into AI context
Query results in `/tmp/` contain customer emails, IDs, counts, and financial data. Always pipe through node scripts (e.g., `render.js`) so data flows through the script only, never through AI context.

### ALWAYS warn customers that dashboard data is INLINED in HTML (Critical Limitation)
HTML Client embeds all data directly in the HTML file — no API, no server, no runtime queries. Customers MUST understand upfront:
- Full/pre-aggregated dataset downloads on first page load (not streaming)
  * Data can be pre-aggregated via Phase 2 Workflow on a defined schedule (daily, weekly, hourly, etc.)
  * Dashboard renders from the latest pre-aggregated snapshot on demand
- All data visible in browser (view source shows everything)
- Updates available on defined schedule if Phase 2 Workflow is used; otherwise static snapshot
- File size = aggregated data size + code (hard limit: 50MB breaking point)
- Filtering/interactions fast (in-browser), but only on loaded/pre-aggregated data

If customer needs sub-minute real-time updates, streaming data, huge raw datasets (can't be aggregated to 50MB), or encrypted storage, this approach is OUT OF SCOPE → contact FDE team. Discuss feasibility in Phase 1, not discovered during Phase 3 build. This skill is HTML Client only — no server-side options available.

### ALWAYS verify column names against the actual table schema before writing any query or inject script
Run `tdx describe <db>.<table>` first. Copy exact column names (case-sensitive). Past incident: dashboard showed all zeros because `customers` ≠ `total_customers` in the SINK schema.

### ALWAYS use COUNT(column) instead of COUNT(*) for KPIs — ask customer if unsure
COUNT(*) counts all rows including those with NULLs, which can inflate counts. COUNT(column_name) counts only non-NULL values in that specific column, which is usually what's intended.

**Rule:** Ask customer: "For your count KPI, which specific entity are we counting?" (e.g., "count distinct customers" → COUNT(DISTINCT customer_id), "count orders placed" → COUNT(order_id), not COUNT(*)).

**Why:** Past incident: COUNT(*) showed 5.2M transactions, but COUNT(order_id) showed 4.8M due to NULL order_ids in data quality issues. Dashboard looked wrong to customer.

**Examples:**
- ❌ COUNT(*) — may include rows with missing key columns
- ✅ COUNT(customer_id) — counts actual customers
- ✅ COUNT(DISTINCT region) — counts unique regions
- ✅ COUNT(order_id) — counts actual orders

### ALWAYS spot-check dashboard numbers against the SOURCE database, not SINK
After rendering, pick at least 3 KPIs and verify them with a direct SQL query **against the original SOURCE tables** (not SINK tables). Numbers must match to the exact value — not "approximately". If 1% off, something is wrong.

**Why SOURCE, not SINK?**
- If Phase 2 created SINK tables, they may have their own transformations/aggregations
- Validating only against SINK verifies consistency but misses bugs in Phase 2 aggregations
- Source tables are the "ground truth" — this validates the entire pipeline (Phase 2 + Phase 3)

### ALWAYS check for join fan-out before writing aggregation queries
If joining 1-to-many tables, count rows before and after. If `after_join > 2 × before_join`, you have fan-out.

**Fix = pre-aggregate the many-side table into a subquery keyed on the join key BEFORE joining. Never aggregate after a fan-out join.**

```sql
-- WRONG: aggregate after join → inflated totals
SELECT SUM(o.amount) FROM customers c JOIN orders o ON c.id = o.customer_id

-- RIGHT: pre-aggregate orders, then join
SELECT SUM(agg.total) FROM customers c
JOIN (
  SELECT customer_id, SUM(amount) AS total FROM orders GROUP BY customer_id
) agg ON c.id = agg.customer_id
```

Past incident: revenue inflated from $4.32M to $6.86M due to undetected fan-out on a 1-to-many orders join.

### ALWAYS use GROUP BY on exactly the dimensions approved in Phase 1, and ensure consistent filter behavior across all widgets
**CRITICAL:** Every query in `generate-data.js` must GROUP BY the EXACT dimensions listed in Phase 1 `state.md` filters, configured as dashboard-level, tab-level, or both per the plan. When filters are applied, ALL affected widgets must show the same data combination — no partial updates or cache misses.

**How it works:**
1. Read Phase 1 `state.md` → extract filter dimensions + placement (dashboard-level/tab-level/both)
2. Configure query grain per placement:
   - Dashboard-level filters: `GROUP BY` on ALL queries (global scope)
   - Tab-level filters: `GROUP BY` per-tab queries only (tab scope)
   - Both: `GROUP BY` dashboard dims on all + tab dims on respective tabs
3. Validate: Apply filter combo (e.g., Region=West, Product=A), verify **every widget on affected tabs** shows the same subset

**Common failure patterns:**
- Phase 1 approves `[Region, Product]` filters, but Phase 3 queries only `GROUP BY Region` → Product filter changes nothing
- Dashboard has Region (global) + Tab1 has Product (per-tab), but Tab1 query missing Product column → tab filter ignored
- Two widgets on same tab show different numbers when Region filter applied (grain mismatch)

Spot-check: Pick 1 filter value, verify every affected widget shows consistent results. If one widget shows different total, grain is wrong.

Past incident: 7-dimension table caused 60% row inflation when only 4 dimensions were filtered; separate incident: mixed queries (one with Region, one without) caused widgets to show unfiltered vs filtered data simultaneously.

---

## 2. Database & Queries

### NEVER assume a database name — always AskUserQuestion
Use `tdx databases` to discover available databases, then present them as options. Never guess or infer the database name.

### ALWAYS run queries in parallel
Every data-generation script must use `Promise.all()` for all queries. Sequential queries multiply latency. Past incident: 5 sequential queries took 5s total; switching to `Promise.all()` brought it to 1.5s.

```javascript
// Always
const [a, b, c] = await Promise.all([queryA(), queryB(), queryC()]);
```

### ALWAYS add --limit xxxx for tables that may return more than 40 rows
`tdx query` defaults to 40 rows. Dimension tables and histogram buckets regularly have 60+ rows. Missing rows cause silent gaps in charts.

### SELECT only the columns the template actually reads
Before writing any query, map what the template displays, then fetch only those columns. Past incident: unused columns added 445 KB to every response.

---

## 3. Rendering (HTML Client only)

This skill produces a single portable `dashboard.html` file with data inlined at build time (Pattern A) — no server, no separate API calls at runtime. This is the only rendering pattern in scope.

### NEVER use Python for file I/O in dashboard rendering — always use Node.js
`python3` is not the standard for this pipeline. All file reading, template injection, and output writing must use `node` (`generate-data.js` / `render.js`).

### NEVER let the AI read raw query results directly — always pipe through a script
Same rule as Data Integrity above: query results flow `tdx query → node script → dashboard.html`, never through AI context.

### Know the rendering floor before optimizing queries
- `tdx query` per query → ~0.5s floor
- `node` script startup → ~0.3s floor

If queries are already faster than this floor, stop optimizing SQL — you're limited by script startup, not the queries.

### ALWAYS confirm the final HTML file opens standalone
Since the whole point of HTML Client is portability, open `dashboard.html` directly in a browser (no dev server) before calling it done. If it needs a running server to render, the build is wrong.

---

## 4. Requirements & Workflow Configuration

### NEVER expose workflow incrementality to non-technical users; full-refresh is default
Incrementality (append-only, 1-day/7-day lookback) is an advanced optimization for large datasets. Non-technical users don't need to know it exists.

**Rule:**
- Phase 1 Stage A Step 1e: Ask "How far back do you need data?" ONLY to determine if Phase 2 is needed, not to choose incremental mode
- Phase 2 deployment: Configure full-refresh by default (simple, predictable)
- Only mention incrementality if: Data size > 500MB + deep history (2+ years) + user is technical
- In state.md: If user is non-technical, never document incremental mode — just say "full refresh daily"

**Why:** Incrementality adds edge cases (late-arriving data, corrections, re-runs). It's a performance optimization, not a feature. Exposing it to non-technical users causes confusion and misunderstandings.

---

### ALWAYS resolve metric definition ambiguity explicitly — offer "show both"
When two valid definitions exist (e.g., unique openers vs total opens), don't force a binary choice. Propose showing both. Past incident: email open rate was 30.5% (unique) vs 87.4% (total) — showing both resolved the ambiguity and gave more insight.

---

## 5. Agent Prompts (Phase 4 Track B)

### ALWAYS put "Execute queries, don't describe them" as the FIRST rule in every agent system prompt
LLM attention weights early instructions highest. If this rule is buried, agents describe what they would do instead of doing it. It must be line 1.

### ALWAYS embed confirmed values in knowledge bases
Schema alone is not enough. KBs must include spot-checked values (e.g., "Total customers (confirmed): 1,000") as ground truth anchors. Without them, agents compute totals from fan-out data and return wrong numbers.

### ALWAYS audit existing Foundry projects for stale schema before deploying
Check whether a project already exists. If yes, pull it and diff the KB table names against the current schema. Past incident: stale KBs referenced a deprecated table name instead of the current one.

### ALWAYS use `--reeval` when iterating on prompt fixes
Re-run only the failing test with `tdx agent test --reeval --name <test_id>`. Don't re-run all tests on every prompt tweak. Past incident: running all 5 tests on every fix wasted 80% of iteration time.

---

## 6. Critical Phase Checkpoints

These rules prevent phase-specific failures. Violating any causes rework or data loss.

### Time Column Validation (Phase 2 critical)
**RULE:** Every metric table MUST have exactly ONE valid business-event or insert-time column.

**Check before Phase 2:**
- Run `tdx describe <db>.<table>` for each source table
- Identify the time column: is it `created_at`, `event_time`, `timestamp`, or `updated_at`?
- Is it nullable? If yes, you have a data quality issue — raise with user
- **Do NOT proceed to Phase 2 without this confirmed**

**Why:** Phase 2 workflow uses time column for daily scheduling and incremental loads. Wrong column → meaningless schedules, missed data, duplicate loads.

### Join Key Validation (Phase 2 critical)
**RULE:** For multi-table dashboards, join keys MUST be unique and consistent across tables.

**Check before Phase 2:**
- If dashboard joins 2+ tables, test the join: `SELECT COUNT(DISTINCT join_key) FROM table_a` vs `SELECT COUNT(DISTINCT join_key) FROM table_b`
- Counts MUST be equal (or close within 5%)
- Check column types: `tdx describe <db>.table_a` — join columns must be same type
- **Do NOT proceed to Phase 2 without join validation queries**

**Why:** Invalid joins cause silent data duplication, inflated metrics, wrong customer segments. Past incident: revenue inflated from $4.3M to $6.9M due to undetected fan-out join.

### state.md Preservation (Phase continuity critical)
**RULE:** NEVER overwrite, modify, or lose `state.md` between phases.

**Check before each phase:**
- The file `./<project-name>/state.md` MUST exist and be readable
- Each phase APPENDS a new section — never replaces old sections
- The "Next action" pointer MUST be present so users can resume
- **If state.md is missing or corrupted, STOP and ask user to recover it**

**Why:** state.md is the single source of truth for phase continuity. Loss of state.md = complete project restart.

### Phase Sequencing Enforcement (Routing critical)
**RULE:** Follow Dashboard Complexity Score routing strictly. Do NOT allow users to skip phases arbitrarily.

**Check at end of Phase 1:**
- Score 0-2 → Phase 1 → Phase 3 (skip Phase 2) ✓
- Score 3 → Ask user: "Workflow or quick build?" ✓
- Score 4-6 → Phase 1 → Phase 2 → Phase 3 ✓
- **Do NOT allow Score 0-2 to enter Phase 2, or Score 4-6 to skip Phase 2 without explicit user override + documented reason**

**Why:** Score routing is based on data complexity and refresh frequency. Skipping Phase 2 on a high-scoring project = performance problems downstream.

### Special Case Path Enforcement (Flow critical)
**RULE:** Once on `.dash` migration path OR Treasure Insights API path, do NOT mix with normal Phase 1 flow.

**Check at setup (Setup-E):**
- If user provides `.dash` file → Follow "`.dash` Special Case" path ONLY
- If user provides datamodel name/OID → Follow "Treasure Insights API Special Case" path ONLY
- If user provides both → Follow "Combined Resources Path" ONLY
- Do NOT repeat questions already answered by the special-case import
- Show and explicitly confirm every prefilled mandatory decision before continuing

**Why:** Special case paths have their own prefilling logic. Mixing paths causes duplicate requirements, conflicting decisions, wasted effort.

### Treasure Data Account Access (Phase 2 critical)
**RULE:** Before Phase 2 starts, verify `tdx auth show` works and user has database create permissions.

**Check before Phase 2:**
- Ask user: "Can you run `tdx auth show` and paste me the output?"
- Verify: profile shows `endpoint`, `apikey`, `database` (default or chosen)
- Verify: user has CREATE TABLE permission (ask them to run `tdx databases`)
- **If auth fails or permissions missing, STOP and ask user to run `tdx auth setup`**

**Why:** Phase 2 creates SINK tables in Treasure Data. Without valid auth, workflow deployment fails and blocks Phase 3.

### SINK Table Naming Convention (Phase 2→3 critical)
**RULE:** SINK table names MUST follow pattern: `<project_name>_sink_<metric_group>` and match dashboard query expectations.

**Check before Phase 3:**
- Generate expected names based on project name and metric groups (from Phase 1)
- Example: project_name = "sales-dashboard", metric_groups = ["revenue", "pipeline"]
  - → SINK table names: `sales_dashboard_sink_revenue`, `sales_dashboard_sink_pipeline`
- Verify Phase 3 dashboard queries reference these exact names
- **If names don't match, Phase 3 queries will find no data**

**Why:** Misnamed SINK tables → dashboard shows empty tables, requires Phase 2 rework.

---

## 7. Physical Object Creation — Approval Gates

**RULE: BEFORE creating, modifying, or deleting any physical object in Treasure Data or external systems, you MUST get explicit user approval.**

Physical objects that require approval:
- ✅ SINK tables (Phase 2)
- ✅ Workflows / scheduled jobs (Phase 2)
- ✅ Segments or parent segments (Phase 2)
- ✅ Foundry agents or skills (Phase 4)
- ✅ External activations (any phase)

**Approval workflow (NON-NEGOTIABLE):**

1. **BEFORE Phase 2 deployment:**
   ```
   📋 Ready to create the following in Treasure Data:
   
   - Database: <db_name>
   - SINK tables: <sink_table_1>, <sink_table_2>, ...
   - Workflow: <workflow_name>
   - Schedule: <daily/weekly/custom>
   
   ✓ This will cost approximately: $X per month
   ✓ First run: <estimated time>
   
   Do you approve? (YES / NO / REVIEW DETAILS)
   ```

2. **BEFORE Phase 4 agent/skill creation:**
   ```
   📋 Ready to create the following in Foundry:
   
   - Foundry Agent/Skill name: <name>
   - Knowledge Base tables: <table_1>, <table_2>, ...
   - Visibility: <internal/shared/public>
   
   Do you approve? (YES / NO / MAKE CHANGES)
   ```

3. **BEFORE any external activation (journey, segment push, etc.):**
   ```
   📋 Ready to activate the following:
   
   - Destination: <Salesforce / Slack / Email / ...>
   - Audience size: <N> records
   - Action: <send email / update CRM / ...>
   
   Do you approve? (YES / NO / REVIEW)
   ```

**If user says NO or REVIEW:**
- STOP immediately — do not proceed
- Gather feedback on what to change
- Return to planning phase, adjust, and re-present

**Why:** Physical objects are real costs (compute, storage), real consequences (data modifications), and hard to undo. Approval gates prevent accidental deployments, runaway costs, and unintended side effects.

---

## Quick Pre-Flight Checklist

Before starting any dashboarding session, verify:

**Data & Queries:**
- [ ] I will ask for the DB name — never assume
- [ ] I will run queries in parallel (`Promise.all`)
- [ ] I will verify column names before writing inject scripts
- [ ] I will spot-check 3+ KPIs against the database after rendering

**Rendering:**
- [ ] I will confirm the final `dashboard.html` opens standalone in a browser
- [ ] I will never let AI read raw query results directly

**Phase Checkpoints:**
- [ ] I will validate time columns before Phase 2
- [ ] I will validate join keys before Phase 2
- [ ] I will preserve state.md between all phases
- [ ] I will enforce Dashboard Complexity Score routing strictly
- [ ] I will NOT mix special case paths (.dash / API) with normal Phase 1 flow
- [ ] I will verify TD account access before Phase 2
- [ ] I will use correct SINK table naming convention

**Approval Gates:**
- [ ] I will get explicit user approval BEFORE creating any SINK tables (Phase 2)
- [ ] I will get explicit user approval BEFORE creating any workflows (Phase 2)
- [ ] I will get explicit user approval BEFORE creating any Foundry agents/skills (Phase 4)
- [ ] I will get explicit user approval BEFORE any external activations
- [ ] I will present clear cost/scope details in every approval request


---

## Execution and phase transition rules

Use `./execution-contract.md` as the completion ledger. The following phase-transition behavior is mandatory:

- Phase 1: route to Phase 2 or Phase 3 from the canonical score/path decision; score 3 requires an explicit user choice.
- Phase 2: after validated workflow output, proceed to Phase 3.
- Phase 3: after all validation and explicit dashboard approval, present Track A, Track B, Phase 5, or close.
- Phase 4: after the selected track completes, present Phase 5 or close.
- Phase 5: after the four documents are reviewed and state is updated, close the engagement.

Never stop at a phase boundary with a generic “let me know.” Present the concrete next options and wait only when the phase is optional or requires user approval.

## Query performance and partitioning

- Check join cardinality before aggregation.
- Use `--limit` explicitly for dimensions and result sets that can exceed the CLI default.
- Use `TD_TIME_RANGE()` or `td_interval()` for partition pruning where applicable.
- Run independent data-generation queries with `Promise.all()`.

## Packaging

For Phase 4 packaging, use Python `zipfile` rather than assuming the shell `zip` command exists. After `generate-data.js` validation passes, show the complete Track A Step 4a-vi packaging instructions even if a zip was created earlier.

## Instruction failure protocol

If a required instruction cannot be verified, stop and report: (1) the blocking rule, (2) why it cannot be verified, and (3) the exact user input or action needed. Never silently skip a failed gate.
