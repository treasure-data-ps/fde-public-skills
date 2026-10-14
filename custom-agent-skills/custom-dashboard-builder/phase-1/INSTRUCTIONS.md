---
name: phase-1-instructions
description: Phase 1 specific instructions for requirements gathering and data discovery
priority: HIGH
load_order: 1.1
---

# Phase 1 Instructions — Requirements & Data Discovery

**Read this BEFORE `./SKILL.md`.**

---

## Phase 1 Goal

Gather business requirements (Stage A), validate them against real data (Stage B), calculate Dashboard Complexity Score (0-6), decide Workflow vs Non-Workflow path, and get user approval — **all in one session**.

**Deliverable:** `./<project-name>/state.md` containing approved requirements, confirmed data findings, Dashboard Complexity Score, and path decision.

---

## Pre-Execution Validation (Before Starting)

**Cannot execute Phase 1 without:**

If resuming from a broken session:
- ✅ User has Treasure Data access (can run `tdx databases`)
- ✅ Database name confirmed and accessible
- ✅ Previous progress saved in `state.md`

If starting fresh:
- ✅ Project name chosen (lowercase with hyphens, no spaces)
- ✅ User can articulate dashboard purpose in 1 sentence
- ✅ At least one metric/KPI identified

**If validation FAILS:**
→ STOP: "Missing prerequisite: [reason]"
→ User action: Confirm database access or provide state.md from prior session

---

## Quick Checklist (Quick Reference)

**Stage A: Session Setup + Requirements**
- [ ] **⚠️ Customer briefed on HTML Client constraints** (data inlined, size limits, pre-aggregation via optional Phase 2 Workflow)
- [ ] Project name chosen (short, lowercase with hyphens)
- [ ] Business goal / dashboard purpose (1 sentence)
- [ ] Platform target? (Treasure Work / Treasure AI Studio)
- [ ] Data source type? (Raw/Transactional / Pre-aggregated / Snapshot / Mixed)
- [ ] **Setup-E: Reference Resources** — Existing dashboard/mockups/specs checked
  - IF resources found (.dash, datamodel, specs) → Fast-track via special case path
  - IF "None" selected → Proceed to standard Stage A flow
- [ ] Use AskUserQuestion for every question (never plain text)
- [ ] **1a:** Dashboard purpose & success criteria
- [ ] **1b:** Metrics/KPIs (what to measure)
- [ ] **⚠️ MANDATORY 1c+1d: Dashboard Structure + Dimensions + Filters + Layout**
  - [ ] Tabs/organization (single page / 2-3 tabs / 4+ tabs / drill-down)
  - [ ] Visualization types (KPI cards, trends, comparisons, distributions, tables, heatmaps)
  - [ ] Filtering scope (static / global / per-section / advanced)
  - [ ] Drill-down depth (summary / one level / multiple / detailed table)
  - [ ] Performance target (daily / multiple daily / hourly / live)
  - [ ] Dimensions & filter list
  - [ ] Layout preferences & branding
- [ ] **⚠️ CRITICAL 1e-1f:** Date range, timezone, refresh/freshness
- [ ] **1g:** Historical depth
- [ ] **1h:** Sharing, access, target users (⚠️ MANDATORY if ANY customer-facing)
- [ ] **1o:** Exclusion rules & data quality

**Optional (only if relevant — use judgment):**
- [ ] **1j:** Alerts/thresholds (only if customer mentioned real-time alerts)
- [ ] **1k:** Mobile/responsive design (only if mobile use case exists)
- [ ] **1l:** Compliance/data sensitivity (only if sensitive data flagged)
- [ ] **1m:** Data source complexity / canonical ID (only if multi-database joins likely)
- [ ] **1n:** Drill-down depth (only if dimensions suggest multi-level drill-down)

**Stage B: Data Discovery & Validation**
- [ ] Database selected, tables confirmed to exist (`tdx databases`, `tdx describe`)
- [ ] Time column identified (business-event datetime vs TD insert-time `time` column)
- [ ] Metrics inferred/validated against live queries
- [ ] Dimensions validated (cardinality, join fan-out checked)
- [ ] Data Quality Gate run (all checks passed)
- [ ] **HTML Client data size validated** (total rows, estimated file size, feasibility check)

**Scoring & Path Decision**
- [ ] Dashboard Complexity Score calculated (Q1 + Q2 + Q3 = ___ / 6)
- [ ] Path decision made (Score 0-2 → Phase 3, Score 3 → user chooses, Score 4-6 → Phase 2 then Phase 3)

**Completion**
- [ ] state.md created with all findings
- [ ] User approval obtained
- [ ] Ready to proceed to Phase 2 or Phase 3

---

---

## ✅ Before You Proceed: Required Reads

**Before executing Phase 1 Stage A, read these reference files:**
1. **`../references/guardrails-lite.md`** — Cross-phase guardrails (re-read on every engagement)
2. **`./references/requirements-questionnaire-patterns.md`** — Requirement gathering patterns (if exists)

These files establish the baseline for all Stage A questions and ensure consistent scoping.

---


### Gate P1-X: Execution Contract Check

Before asking or recording any Phase 1 question, read `../references/execution-contract.md`. Use `AskUserQuestion` for every mandatory questionnaire, record each answer or refusal reason in `state.md`, and do not advance with a missing checkbox.

**Canonical scoring:** `./references/steps-1p-1t.md` is the sole Q1–Q3 Dashboard Complexity Score source. Do not use an inferred technical-factor rubric.

## Phase 1 Specific Rules (In Addition to Universal Rules)

### Rule P1-0: ALL Mandatory Questionnaires MUST Be Asked (ENFORCEMENT)

**⚠️ CRITICAL: CANNOT skip ANY mandatory questionnaire.**

**MANDATORY questionnaires (always ask, NEVER skip):**
- ✅ Setup-A: Project name
- ✅ Setup-B: Business goal
- ✅ Setup-C: Target platform
- ✅ Setup-D: Data source type
- ✅ Setup-E: Reference resources
- ✅ 1a: Dashboard purpose & success criteria
- ✅ 1b: Metrics/KPIs
- ✅ **1c+1d: Dashboard Structure** (ALL 5 structure batches mandatory)
  - Tabs/Organization
  - Visualization types
  - Filter & Interactivity
  - Drill-down depth
  - Performance targets
- ✅ **1c+1d (continued): Dimensions + Filters + Layout + Branding**
- ✅ **1e+1f: Date range, Timezone, Refresh/Freshness** (⚠️ timezone is CRITICAL)
- ✅ 1g: Historical depth
- ✅ 1h: Sharing, access, target users (if ANY customer-facing element)
- ✅ 1o: Exclusion rules & data quality

**OPTIONAL questionnaires (only if relevant):**
- ⚠️ 1j: Alerts/thresholds (only if customer mentioned real-time alerts)
- ⚠️ 1k: Mobile/responsive design (only if mobile use case exists)
- ⚠️ 1l: Compliance/data sensitivity (only if sensitive data flagged)
- ⚠️ 1m: Data source complexity (only if multi-database joins likely)
- ⚠️ 1n: Drill-down depth (only if dimensions suggest multi-level drill-down)

**Enforcement:**
- Use AskUserQuestion for EVERY question in mandatory list
- If customer says "skip this" → **STOP and ask why** → Escalate if truly not applicable
- Do NOT offer skip-out on mandatory questions
- Document in `state.md` if customer refuses to answer (with reason)

**If customer refuses a mandatory question:**
> "I cannot proceed without answering this. This information shapes the entire dashboard design. If [question] isn't applicable, let's clarify why — there might be a misunderstanding about what we're building."

---

### Rule P1-1: Requirements Must Be Validated Against Real Data

- [ ] **Stage A:** Gather business requirements (no data validation yet)
  - KPIs: What are they measuring?
  - Dimensions: How should metrics be sliced?
  - Filters: What does the audience need to filter on?
  - Audience: Who will use this?

- [ ] **Stage B:** Validate requirements against real data
  - Run `tdx describe <db>.<table>` for each source table
  - Verify columns exist (exact spelling, case-sensitive)
  - Test joins with sample queries
  - Verify time columns are present and non-nullable
  - Never accept "I assume the data exists" — verify with `tdx query`

**Why:** Many requirements fail at validation. Better to discover this in Phase 1 than Phase 3.

**Example validation query:**
```sql
-- Verify KPI column exists
SELECT SUM(revenue) FROM sales_table LIMIT 5;

-- Verify time column
SELECT MIN(created_at), MAX(created_at) FROM sales_table;

-- Verify dimension exists
SELECT DISTINCT country FROM sales_table LIMIT 10;
```

---

### Rule P1-2: Dashboard Complexity Score Calculation Is Deterministic

**Canonical source:** `./references/steps-1p-1t.md`, Step 1p. Ask Q1–Q3 with `AskUserQuestion` and sum their defined points for the 0–6 score. Do not substitute an inferred technical-factor rubric.

**Blocking gate:** Do not calculate or route until Q1–Q3 are answered or a refusal/not-applicable reason is recorded and escalated under Rule P1-0.

---

### Rule P1-2b: Dashboard Design Specification (ENFORCEMENT)

**⚠️ CRITICAL: Phase 1 Stage A must capture complete dashboard design before moving to Stage B.**

During Step 1c (Dimensions, Filters, Layout), capture:

1. **Tab Structure:**
   - How many tabs? (single or multiple)
   - What is each tab called?
   - Which metrics go on each tab?

2. **Three-Level Filter Hierarchy (ALL STACKABLE):**
   
   Define filters at three levels (users can apply any/all simultaneously):
   
   **Level 1: Global Filters** (apply to ALL widgets across ALL tabs)
   - Examples: Date Range, Region, Company
   - Affects: Every widget on every tab
   - Query impact: Added to WHERE clause on all queries
   
   **Level 2: Tab Filters** (apply to ALL widgets within that specific tab ONLY)
   - Examples: Tab 1 (Category), Tab 2 (Customer Segment), Tab 3 (Product Type)
   - Affects: Only widgets on that tab
   - Query impact: Added to WHERE clause only for tab's queries
   - Note: Other tabs are unaffected by tab-level filters
   
   **Level 3: Widget Filters** (apply to ONLY that single widget — EMBEDDED, NOT UI CONTROLS)
   - Examples: One KPI card has "exclude cancelled orders" filter, Chart shows "only revenue > $100"
   - **CRITICAL: These are NOT interactive controls users see**
   - **Instead: Embedded as widget configuration/business logic**
   - Affects: Only that one widget
   - Query impact: Added to WHERE clause only for that widget's query
   - Note: Other widgets on same tab unaffected
   - User sees: Only global and tab filters in the UI; widget rules are invisible configuration
   
   **Filter Stacking (IMPORTANT):**
   - Users can apply filters at ALL THREE LEVELS simultaneously
   - Filters combine via AND logic (all conditions must be met)
   - Example: Global Date Range AND Tab Category AND Widget Status = combined WHERE clause
   - Ask customer: "Can filters be applied together?" (always answer YES unless explicitly stated otherwise)

3. **Visualization Type per Metric:**
   - KPI card? Line chart? Bar chart? Pie chart? Table?
   - What dimensions slice each metric?

4. **Widget Details:**
   - Widget name
   - Chart type
   - Metric and calculation (SUM/COUNT/AVG/etc)
   - Dimensions (what to slice by)
   - Filters applied
   - Business definition

5. **Interactivity:**
   - Can users click to drill down?
   - Can users export data?
   - Which widgets update together?

**See:** `./references/dashboard-design-questions.md` for question sets and examples

**Capture in state.md:**
```yaml
### Dashboard Design Specification

**Tabs:** [number and names]

**Level 1: Global Filters** (apply to ALL tabs/widgets)
  - [filter name]: [type, cardinality, e.g., "Date Range (date picker)" or "Region (6 values)"]
  - [filter name]: [type, cardinality]

**Level 2: Tab-Specific Filters** (apply to widgets WITHIN that tab only)
  - Tab 1 - [filter name]: [type, cardinality]
  - Tab 2 - [filter name]: [type, cardinality]
  - Tab 3 - None (or list filters)

**Level 3: Widget-Specific Filters** (EMBEDDED CONFIGURATION, NOT UI CONTROLS)
  - [Tab Name] - [Widget Name]:
    Widget Rule (embedded, not shown in UI): [e.g., "Status != 'cancelled'", "Amount > 100"]
    Note: This rule is in generate-data.js code, NOT a visible filter control

**Widgets:**
  - [Tab Name] - [Widget Name]
    Chart Type: [KPI/Line/Bar/Pie/Table/...]
    Metric: [metric name]
    Calculation: [formula]
    Dimensions: [sliced by]
    Interactive Filters Applied: [Global + Tab only: e.g., "Global Date/Region + Tab Category"]
    Embedded Rules (hidden from UI): [e.g., "exclude cancelled"]
    Definition: [business meaning]

**Filter UI Rule:** Users only see Global + Tab filters. Widget rules are embedded configuration.
**Filter Stacking Rule:** All filters (visible + embedded) combine via AND logic and can be applied simultaneously
```

**Why:** This prevents rework in Phase 3. Users approve the complete design in Phase 1, so Phase 3 is execution, not design iteration.

---

### Rule P1-3: Join Key Validation (Phase 1→2 gate)

If requirements include 2+ tables:

- [ ] Identify join keys
- [ ] Test with sample queries:
  ```sql
  SELECT COUNT(DISTINCT customer_id) FROM customers;
  SELECT COUNT(DISTINCT customer_id) FROM orders;
  -- Counts should match (within 5%)
  ```
- [ ] If counts don't match, flag it for Phase 2 planning (pre-aggregation needed)

**Why:** Undetected join issues cause Phase 2 rework.

---

### Rule P1-4: Time Column Validation (Phase 1 discovery)

- [ ] Identify the business event or insert timestamp column
- [ ] Verify it's non-nullable: `tdx describe <db>.<table>`
- [ ] If nullable, flag as data quality issue — inform user
- [ ] Document the column name in state.md

**Example:**
```yaml
## Time Column Validation

Source Table: sales_events
- Column identified: `event_time` (business event time)
- Nullable: No ✓
- Format: TIMESTAMP
- Range: 2020-01-01 to 2026-07-22
```

---

### Rule P1-5: Special Case Paths (Sisense .dash or Treasure Insights API)

If user provides:
- **`.dash` file** → Follow `.dash` Special Case path (skip to dashboard prefilling)
- **Datamodel name/OID** → Follow Treasure Insights API Special Case path (fetch schema via API)
- **Both** → Follow Combined Resources path (validate consistency)
- **Neither** → Follow normal Stage A/B path

**Do NOT mix paths.** Once on a special path, stay on it.

**Why:** Special case paths have their own prefilling logic. Mixing causes duplicate questions.

---

### Rule P1-6: Negative Confirmation (Ask What NOT to Include)

At the end of requirements (Stage A), explicitly ask:

> "Is there anything you specifically do NOT want in this dashboard?"

Common answers:
- "Don't include revenue from EU (privacy)"
- "Don't show customer names (PII)"
- "Don't include last 24h (data quality lag)"

Document as "Exclusions" in state.md.

---

### Rule P1-7: Dimensions Validation

For each dimension user requests:

- [ ] Verify it exists in data: `SELECT DISTINCT <dimension> FROM <table> LIMIT 10`
- [ ] Check cardinality: `SELECT COUNT(DISTINCT <dimension>) FROM <table>`
- [ ] If cardinality > 1000, warn user (may be too granular for dashboard filters)

**Example:**
```yaml
## Dimensions Validation

- Dimension: country
  - Exists: ✓ (SELECT DISTINCT country ... returned 195 rows)
  - Cardinality: 195 (acceptable for filter)
  
- Dimension: customer_id
  - Exists: ✓
  - Cardinality: 1,200,000 (⚠️ WARNING: Very high cardinality, not suitable for filter)
  - Recommendation: Use name instead or provide search autocomplete
```

---

### Rule P1-7b: HTML Client Data Size Validation (ENFORCEMENT)

**⚠️ CRITICAL: Phase 1 must validate that dashboard design is feasible for HTML Client limits.**

HTML Client stores data INLINE in the HTML file (not fetched from API). This creates hard limits:

| Metric | Safe | Warning | Breaking |
|--------|------|---------|----------|
| HTML File Size | < 10 MB | 10-50 MB | > 50 MB |
| Data Rows (total) | < 100K | 100K-500K | > 500K |
| Load Time | < 2s | 2-5s | > 5s |

**During Stage B (data discovery), for EACH widget AND filter:**

1. **Analyze filters first (high-cardinality blocks):**
   ```bash
   # Check cardinality of each filter column
   tdx query "SELECT COUNT(DISTINCT region) FROM orders"
   tdx query "SELECT COUNT(DISTINCT status) FROM orders"
   tdx query "SELECT COUNT(DISTINCT customer_id) FROM orders"
   
   # Safe: < 50 values (use dropdown)
   # Warning: 50-500 values (consider search)
   # Danger: > 500 values (use search autocomplete, don't embed)
   # Breaks: > 10,000 values (definitely not in data.json)
   ```

2. **Estimate widget rows:**
   ```
   If aggregated (GROUP BY region, date, status):
     90 days × 6 regions × 4 statuses = 2,160 rows ✅
   
   If raw events (no aggregation):
     2.1M rows ❌ TOO LARGE
   ```

3. **Run actual query to test:**
   ```bash
   tdx query --output json < query.sql > data.json
   ls -lh data.json
   # If < 5 MB: ✅ Safe
   # If 5-10 MB: ⚠️ Approaching limit (acceptable but watch carefully)
   # If 10-20 MB: ⚠️ WARNING — approaching breaking point
   # If > 20 MB: ❌ Likely breaks (must reduce)
   ```

4. **⚠️ WARNING MESSAGE (if dataset ≥ 10 MB):**
   ```
   ⚠️ DATASET APPROACHING SIZE LIMIT
   
   Current estimated size: [X MB]
   Safe threshold: < 10 MB
   Breaking point: > 50 MB
   
   This dashboard is getting large. Users may experience slow load times 
   (> 5 seconds) or performance issues. 
   
   REQUIRED ACTION: Apply data size reduction plan below.
   If unable to get below 10 MB, contact FDE team for alternatives.
   ```

5. **Identify problems:**
   - High-cardinality filters (customer_id, product_id, user_id)? ← **START HERE**
   - Too many dimensions (combinations explode)?
   - Raw events instead of aggregated?
   - Too much history (3+ years daily data)?
   - Too many dimensions in GROUP BY?
   - Too many tabs with independent data?

6. **Data Size Reduction Plan (execute in order):**

   **Phase 1 (High Impact — should fix most cases):**
   1. **Remove high-cardinality filters** (if > 500 distinct values)
      - ❌ NOT: customer_id filter (1.2M distinct)
      - ✅ YES: Region filter (5 distinct)
      - Impact: -50% to -80% payload
   
   2. **Reduce historical scope** (narrow date range)
      - ❌ NOT: 5 years of daily data
      - ✅ YES: 1 year of daily OR 5 years of monthly
      - Impact: -50% to -95% payload
   
   3. **Coarsen time grain** (daily → weekly/monthly)
      - ❌ NOT: 1,095 days × 50 categories = 54,750 rows
      - ✅ YES: 52 weeks × 50 categories = 2,600 rows
      - Impact: -95% payload reduction
   
   **Phase 2 (Medium Impact):**
   4. **Coarsen spatial dimensions** (city → state, product SKU → category)
      - ❌ NOT: 45,000 cities
      - ✅ YES: 50 states
      - Impact: -60% to -90% payload
   
   5. **Reduce dimensions per widget** (4 dims → 2 main dims)
      - ❌ NOT: GROUP BY region, category, segment, status
      - ✅ YES: GROUP BY region, category (use drill-down for detail)
      - Impact: -40% to -70% payload
   
   **Phase 3 (Lower Impact — if still over 10 MB):**
   6. Remove least-used filters
   7. Paginate tables (top 1K rows only)
   8. Reduce number of tabs
   
   **If NONE of these work:**
   - You cannot get below 10 MB with reasonable tradeoffs
   - **Contact FDE team** for alternative solution options
   - Don't force dashboard into HTML Client if data doesn't fit

**Capture in state.md:**
```yaml
### HTML Client Data Validation

Widget | Type | Estimated Rows | Estimated Size | Status
--------|------|--------|--------|--------
[Widget Name] | [Type] | [N rows] | [X KB/MB] | [✅/⚠️/❌]

Total Estimated Size: [X MB]
Feasibility: [✅ Safe / ⚠️ Warning / ❌ Not Feasible]

**If dataset ≥ 10 MB:**
⚠️ WARNING: Dataset approaching size limit. Reduction plan applied:
  - [Remediation 1: e.g., "Removed customer_id filter (was 1.2M distinct values)"]
  - [Remediation 2: e.g., "Reduced from 5 years daily to 1 year daily"]
  - [Remediation 3: e.g., "Coarsened to weekly instead of daily (95% reduction)"]

Final Estimated Size: [Y MB]
Result: [✅ Safe / ⚠️ Warning (approved by customer) / ❌ Not feasible — Contact FDE team]
Customer Approval: [Yes/No]
```

**See:** `./references/html-client-data-limits.md` for detailed estimation and solutions

**Why:** Discovering data size issues in Phase 1 prevents Phase 3 build failures or slow dashboards.

---

### Rule P1-C: Communicate HTML Client Payload Constraints to Customer (REQUIRED)

**⚠️ CRITICAL: Phase 1 Stage A must inform the customer about HTML Client payload limits before finalizing dashboard design.**

During Step 1c (dashboard design specification), **before** diving into technical details:

1. **Set expectations upfront (CRITICAL DATA INLINING WARNING):**
   ```
   "This dashboard will be a single HTML file that opens in your browser 
   (no server needed, fully portable). 
   
   ⚠️ IMPORTANT: All data is EMBEDDED DIRECTLY in the HTML file itself.
   This means:
   
   • The full/pre-aggregated dataset is downloaded to your browser on first load
     (Data can be pre-aggregated into summary tables via Phase 2 Workflow on a defined schedule, 
      if opted. Phase 3 renders from those pre-aggregated tables on demand.)
   • Users will see a one-time load delay while the complete dataset and rendering happen
   • Filtering/interactions happen in the browser (fast, but only on loaded/pre-aggregated data)
   • The HTML file size = aggregated data size + code (can't be separated)
   • Anyone with the file can see the data (view source in browser)
   
   We need to keep the data size reasonable — typically under 10MB 
   for smooth performance, max 50MB before it gets very slow.
   
   **Updates:** If you need frequent refreshes (hourly, daily, weekly, etc.), 
   we'll use Phase 2 Workflow to pre-aggregate data on that schedule. 
   The dashboard then renders from the latest pre-aggregated snapshot on demand.
   
   If you need:
   - True real-time updates (sub-minute)
   - Huge raw datasets (GB+) that can't be aggregated to fit 50MB
   - Streaming data or live connections
   - Encrypted/secure data storage
   
   This HTML Client approach won't work for your needs. 
   Please contact the FDE team to explore alternative solutions. 
   Let's confirm this approach is right for you first before proceeding."
   ```

2. **Ask constraint-discovery questions:**
   - "How many distinct regions/categories do you filter on?" (cardinality)
   - "Do you need daily data or is weekly/monthly OK?" (time grain)
   - "How far back do you need history — 90 days, 1 year, 3 years?" (date range)
   - "Do you need customer-level detail or aggregate by company?" (granularity)

3. **Run estimation queries for their design:**
   - Check filter cardinality (how many distinct values)
   - Estimate total rows (time × dimensions × metrics)
   - Calculate payload size (run actual query, export to JSON)

4. **Present feasibility verdict WITH remediations:**

### Feasibility Verdict & Remediations

| Status | Action | Examples |
|--------|--------|----------|
| ✅ **Safe** (< 10MB, < 100K rows) | Approve design as-is | Daily data, 3-5 low-cardinality dimensions |
| ⚠️ **Warning** (10-50MB, 100K-500K rows) | Discuss tradeoffs, apply 1-2 remediations | May be slow, but acceptable with user approval |
| ❌ **Not Feasible** (> 50MB, > 500K rows) | **MUST apply remediations** | Cannot proceed without changing design |

### Remediation Menu (Order by Impact)

**High Impact (Start Here):**

1. **Drop high-cardinality filters** (if cardinality > 500)
   - Problem: `SELECT COUNT(DISTINCT customer_id) FROM orders` returns 1.2M
   - Solution: Remove customer_id filter, or provide search autocomplete instead of dropdown
   - Impact: -50% to -80% payload reduction

2. **Coarsen time grain** (if daily + 3+ years = explosion)
   - Problem: 1,095 days × 50 categories × 5 statuses = 273,750 rows ❌
   - Solution: Change to weekly (156 weeks) or monthly (36 months)
   - Examples: 
     - Daily → Weekly: 273,750 → 39,000 rows (-86%)
     - Daily → Monthly: 273,750 → 8,500 rows (-97%)
   - Impact: -70% to -90% payload reduction

3. **Coarsen spatial dimensions** (geography hierarchy)
   - Problem: `SELECT COUNT(DISTINCT city)` = 45,000 (too many)
   - Solution: Change from city → state/region (50-400 values)
   - Other hierarchies: Product SKU → Product Category, Employee ID → Department
   - Impact: -60% to -90% payload reduction

4. **Narrow date range** (if history too deep)
   - Problem: 5 years of daily data + 200 dimensions = huge
   - Solution: Change from 5 years to 1-2 years rolling window
   - Examples:
     - 5 years daily → 2 years daily: -60% rows
     - 5 years daily → 2 years weekly: -95% rows
   - Impact: -50% to -95% payload reduction

**Medium Impact:**

5. **Reduce dimensions per widget** (fewer GROUP BY columns)
   - Problem: Widget groups by Region + Category + Segment + Status (4 dims)
   - Solution: Group by 2 main dims only, drill-down for detail
   - Impact: -40% to -70% payload reduction

6. **Segment to top-N values** (when cardinality explodes)
   - Problem: 10,000 products in data, but only top 50 matter
   - Solution: `WHERE product IN (SELECT ... ORDER BY revenue DESC LIMIT 50)`
   - Impact: -80% to -95% payload reduction

7. **Aggregate/calculate once (not per widget)**
   - Problem: Each widget re-queries overlapping data
   - Solution: Single overview query with multiple aggregations, widgets share data
   - Impact: -40% to -60% payload reduction

**Low Impact (If still oversized):**

8. **Paginate large result sets**
   - Solution: Show top 1,000 rows in table, paginate rest
   - Impact: -20% to -40% payload reduction

9. **Remove least-used filters**
   - Solution: If 5 filters exist, user only uses 3, remove the 2 they never touch
   - Impact: -10% to -25% payload reduction

10. **Reduce number of tabs**
   - Problem: 10 independent tabs, each with heavy data
   - Solution: Consolidate to 3-5 tabs, use filters instead of separate tabs
   - Impact: -50% to -80% payload reduction

**Nuclear Option (Last Resort — Out of Scope):**

11. **Dashboard is NOT feasible for HTML Client**
   - When: No remediations work, user needs 50MB+, real-time updates, or encrypted storage
   - Recommendation: This dashboard is out of scope for this pipeline (HTML Client only)
   - User action: Contact FDE team to explore alternative solutions
   - Why: This skill is designed for portable, self-contained HTML dashboards only

---

### Capture Customer Approval in state.md

```yaml
### HTML Client Payload Constraints & Approval

**Initial Feasibility:** [✅ Safe / ⚠️ Warning / ❌ Not Feasible]

**If Warning/Failing:**
Remediations Applied:
  - [Remediation 1: e.g., "Removed customer_id filter (cardinality 1.2M)"]
  - [Remediation 2: e.g., "Changed from daily to weekly grain"]
  - [Remediation 3: e.g., "Narrowed date range from 5y to 2y"]

**Final Feasibility:** [✅ Safe / ⚠️ Warning (approved)]

**Customer Sign-Off:**
  - [ ] Customer understands HTML Client limits (10-50MB range)
  - [ ] Customer approves remediations (trade-offs explained)
  - [ ] Customer confirms design is final for Phase 3 build
```

**Why:** Discussing payload upfront prevents Phase 3 surprises ("Why is my dashboard so slow?") and design rework.

---

### Rule P1-8: Metrics Validation

For each metric user requests:

- [ ] Verify column exists and is numeric
- [ ] Check for missing/null values
- [ ] Validate with a sample aggregation
- [ ] **For COUNT metrics: Ask which entity/column to count** (use COUNT(column), not COUNT(*))

**For COUNT KPIs — ALWAYS ask:**
> "For your count KPI, which specific entity/column are we counting?"

**Why:** COUNT(*) includes rows with NULLs, which inflates counts. COUNT(column_name) counts only non-NULL values.

**Examples:**
- "Count of customers" → COUNT(DISTINCT customer_id)
- "Count of orders" → COUNT(order_id)
- "Count of transactions" → COUNT(transaction_id)
- ❌ NOT COUNT(*) — unless explicitly confirmed

**Example queries:**
```sql
-- Verify column exists and is numeric
SELECT SUM(revenue) FROM sales_table LIMIT 5;

-- Check for nulls (shows difference between COUNT(*) and COUNT(column))
SELECT COUNT(*) total_rows, COUNT(revenue) non_null_revenue, 
       COUNT(*) - COUNT(revenue) AS nulls_in_revenue
FROM sales_table;

-- For COUNT KPI: count specific column
SELECT COUNT(DISTINCT customer_id) FROM sales_table;  -- Customers
SELECT COUNT(order_id) FROM sales_table;              -- Orders (not rows)

-- Quick aggregation test
SELECT SUM(revenue) FROM sales_table WHERE DATE(created_at) = '2026-07-22';
```

---

### Rule P1-9: Filter Edge Case Question (REQUIRED IN STAGE A)

**⚠️ CRITICAL: Ask explicitly: "What should KPIs show when a filter makes accurate computation impossible?"**

**Add this question to Stage A Step 1c (Filters & Layout):**

```
For each metric, decide edge case behavior:

Q: "Total Customers" filtered by "Product Category" 
   = Can't compute accurately (same customer buys multiple categories)
   Options:
     a) Show COUNT(DISTINCT customer) per category (separate count per category)
     b) Show "—" (dash, not available)
     c) Show estimate with "*" (estimate, confidence note)
   User decides: (a/b/c)

Q: "Revenue" filtered by "Date" 
   = Can compute accurately (revenue IS date-filterable)
   Options:
     a) Show filtered revenue (correct answer)
   User decides: (a)

Q: "Unique Visitors" filtered by "Page"
   = Can't compute accurately (same visitor visits multiple pages)
   Options:
     a) Show visitors per page (separate count per page, not unique across)
     b) Show "—"
     c) Show all-time visitors (unfiltered, maybe with warning)
   User decides: (a/b/c)
```

**Capture in state.md:**
```yaml
### Filter Edge Case Behaviors (if filter makes computation impossible)

Metric: Total Customers
- If filtered by Category: Show "—" (can't count distinct across categories)
- If filtered by Region: Show COUNT(DISTINCT customer_id) per region ✓

Metric: Unique Sessions
- If filtered by Page: Show sessions per page OR show "—"
- If filtered by Date: Show COUNT(DISTINCT session_id) per date ✓

Metric: Revenue
- All filters: Show filtered revenue (always computable)
```

**Why:** Prevents Phase 3 discovery of incomputable metrics. Better to decide in Phase 1.

---

### Rule P1-9a: Filter Interaction Rules (REQUIRED BEFORE PHASE 3)

**⚠️ CRITICAL: Specify what happens to metrics when filters are applied. Ask explicitly in Stage A Step 1c.**

For each **KPI/metric** that will have filters applied, specify:

1. **Date filter applied:** Does the metric recalculate? Show `—` if impossible to aggregate to single value?
2. **Category/dimension filter applied:** Does the metric update? Show adjusted value, `—`, or estimate?
3. **Custom segment filter applied:** How does this affect the KPI? Show for segment only, show total + segment, or exclude?

**Examples:**

| Metric | Date Filter | Category Filter | Segment Filter |
|--------|------------|-----------------|---|
| **Total Revenue** | ✅ Recalculate | ✅ Show by category | ✅ Show for segment |
| **Unique Customers** | ⚠️ Show `—` (can't aggregate) | ⚠️ Show by category | ✅ Show for segment |
| **Avg Order Value** | ✅ Recalculate | ✅ Show by category | ✅ Show for segment |

**Questions to ask the user:**

1. "For [Metric X], if someone filters to [specific category], should the value update or show `—`?"
2. "If a metric can't be accurately filtered (e.g., Unique Customers by date), should we show an estimate, hide it, or show a warning?"
3. "When multiple filters are applied together, should metrics show the intersection, or revert to unfiltered?"

**Capture in state.md:**
```yaml
### Filter Interaction Rules

**Metric: [Metric Name]**
- Date filter behavior: [Recalculate / Show — / Show estimate]
- Category filter behavior: [Show by category / Show — / Show estimate]
- Segment filter behavior: [Show for segment / Show total + segment]
- Multi-filter behavior: [Intersection / Revert]

**Metric: [Next Metric Name]**
- [Same structure]
```

**Why:** Prevents Phase 3 confusion about what filters should do to each metric. Discovered late = rework cycles.

---

### Rule P1-10: State.md Creation

At end of Phase 1, create `state.md` with this structure:

```yaml
# Dashboard Project: [project-name]

## Phase 1 — Requirements & Data Discovery
**Date:** [date]
**Status:** ✅ Complete

### Business Requirements (Stage A)

**Primary Goal:** [1-2 sentence summary]

**KPIs:**
- [metric 1]: [definition]
- [metric 2]: [definition]

**Dimensions:**
- [dimension 1]: [cardinality]
- [dimension 2]: [cardinality]

**Filters:**
- [filter 1]: [options]
- [filter 2]: [options]

**Audience:** [names/roles]

**Exclusions:** [what NOT to include]

### Data Findings (Stage B)

**Source Tables:**
- [table 1]: [columns], [row count], [last updated]
- [table 2]: [columns], [row count], [last updated]

**Time Column:**
- Table: [table name]
- Column: [column name]
- Format: [TIMESTAMP/DATE/etc]
- Nullable: [YES/NO]

**Join Keys (if 2+ tables):**
- [table 1] ↔ [table 2]: [join key], [cardinality validated: YES/NO]

**Validation Results:**
- All columns verified: ✓
- All joins tested: ✓
- Time column present: ✓

### Dashboard Complexity Score

**Final Score:** [X/6]

**Breakdown:**
- Multiple tables: [+1 if yes]
- 1-to-many joins: [+1 if yes]
- Sub-daily refresh: [+1 if yes]
- Aggregation required: [+1 if yes]
- High concurrency (5+ users): [+1 if yes]

### Dashboard Plan Summary (Displayed to User)

**Dashboard Filters (applied to all tabs):**
- [Filter 1]: [dimension/field], type: [dropdown/date-picker/search]
- [Filter 2]: [dimension/field], type: [dropdown/date-picker/search]

**Tabs:**
- Tab 1: [name] — Widgets: [count]
- Tab 2: [name] — Widgets: [count]

**Tab 1: [Tab Name]**

| Widget | Type | Metric | Dimensions | Filters | Calculation |
|--------|------|--------|-----------|---------|-------------|
| [Widget 1 Name] | [Chart Type: KPI/Bar/Line/Table] | [Metric] | [Sliced by] | [Filter 1, Filter 2] | [Formula/Aggregation] |
| [Widget 2 Name] | [Chart Type] | [Metric] | [Sliced by] | [Filters] | [Formula/Aggregation] |

**Tab 2: [Tab Name]**

| Widget | Type | Metric | Dimensions | Filters | Calculation |
|--------|------|--------|-----------|---------|-------------|
| [Widget Name] | [Chart Type] | [Metric] | [Sliced by] | [Filters] | [Formula/Aggregation] |

**Data Source:**
- Database: [database]
- Tables: [table1, table2, ...]
- Date Range: [range]
- Data Freshness: [last updated]
- Rendering: HTML Client (standalone, portable)

**HTML Client Data Size Validation:**

**Filters Analysis:**
- Global Filters: [list, e.g., "Date Range, Region (6), Status (4)"]
- Tab-Specific Filters: [list or "None"]
- Cardinality Check: [✅ All < 50 values OR ⚠️ [filter name] has [N] values OR ❌ [filter name] too high]
- Filter Data Size: [X KB]

**Widget Data:**
| Widget | Type | Rows | Size | Filters Applied | Status |
|--------|------|------|------|-----------------|--------|
| [Widget 1] | [Type] | [N] | [X KB] | [filter names] | ✅ |
| [Widget 2] | [Type] | [N] | [X KB] | [filter names] | ✅ |

**Total Size Breakdown:**
- Widget Data: [X KB]
- Filter Options: [X KB]
- HTML/JS/CSS: [~50 KB]
- JSON Overhead: [X KB]
- **Final HTML File:** [X MB]

- **Load Time (estimated):** [X seconds]
- **Tab Complexity:** [N tabs - low/medium/high]
- **Filter Complexity:** [N filters, max cardinality [N] - low/medium/high]
- **Feasibility:** ✅ Safe for HTML Client OR ⚠️ Warning OR ❌ Not feasible
- **Actions Taken (if any):** [e.g., "Removed high-cardinality customer filter", "Reduced to weekly aggregation"]

### Path Decision

**Recommended Path:** Phase 1 → [Phase 2 → Phase 3 OR Phase 3]

**Justification:** Score X indicates [workflow/non-workflow] path

**User Approval:**
- Plan reviewed: [YES / NO]
- Plan approved: [YES / NO]
- Path confirmed: [Phase 2 / Phase 3]
- Confirmation timestamp: [YYYY-MM-DD HH:MM:SS]

---

### Rule P1-11: Path Confirmation (ENFORCEMENT)

**⚠️ CRITICAL: CANNOT proceed to Phase 2 or Phase 3 without explicit user confirmation of the path.**

After calculating Dashboard Complexity Score and recommending a path:

**If Score 0-2 (Non-Workflow recommended):**
- Present: "Recommended: Non-Workflow Path (Phase 3 only)"
- Wait for: `YES, BUILD DASHBOARD NOW (Non-Workflow)` OR `NO, SET UP WORKFLOW INSTEAD`
- If user confirms Non-Workflow: Proceed to Phase 3
- If user chooses Workflow instead: Proceed to Phase 2

**If Score 4-6 (Workflow recommended):**
- Present: "Recommended: Workflow Path (Phase 2 → Phase 3)"
- Wait for: `YES, PROCEED WITH WORKFLOW PATH` OR `NO, SKIP WORKFLOW AND BUILD NOW`
- If user confirms Workflow: Proceed to Phase 2
- If user declines Workflow: Proceed to Phase 3 instead

**If Score 3 (User choice):**
- Ask directly: "Which path? Phase 2 (Workflow) or Phase 3 (Non-Workflow)?"
- User answers: →  **Immediately proceed** (no second approval needed)
- If Phase 2 chosen: "Starting Phase 2 now..."
- If Phase 3 chosen: "Starting Phase 3 now..."

**CRITICAL: Auto-start after confirmation (Rule 0: Phase Auto-Advance)**
- Score 0-2 confirmed → "Starting Phase 3 now..."
- Score 4-6 confirmed → "Starting Phase 2 now..."
- User choice confirmed → Start chosen phase immediately

**See:** `./references/stage-b-path-routing.md` → "Approval Gates" section for full templates

**Why:** Path decisions have real cost/time/complexity implications. User must explicitly confirm they understand the tradeoffs. But once confirmed, start immediately (don't wait).

---

### Rule P1-12: Dashboard Plan Summary Display (ENFORCEMENT)

**⚠️ CRITICAL: Before asking for final approval, show the user a dashboard plan summary.**

**When:** End of Stage B (before path confirmation in Rule P1-10)

**What to show:**
```
📊 Dashboard Plan — <project-name>

Source Database:   <database_name>
Tables:
  • <table_1> (<row_count>, updated <freshness>) — <FACT | DIMENSION>
  • <table_2> (<row_count>, updated <freshness>) — <FACT | DIMENSION>

Metrics confirmed:
  • <Metric 1>: <definition with sample value>
  • <Metric 2>: <definition with sample value>
  • <Metric 3>: <definition with sample value>

Dimensions confirmed:
  • <Dimension 1>: <N> values (<examples>)
  • <Dimension 2>: <N> values (<examples>)

Date range:        <default_range>
Data freshness:    <last updated>
Rendering:         HTML Client (standalone, portable)
Dashboard Complexity Score:   <X>/6

Conflicts detected: <None | list conflicts>
```

**Example:**
```
📊 Dashboard Plan — sales-performance

=== DASHBOARD FILTERS (Global - applies to all tabs) ===

Filters:
  • Date Range: date-picker (Last 90 days default)
  • Region: dropdown (North America, Europe, APAC, LATAM, EMEA, APJC)
  • Order Status: multi-select (Completed, Pending, Cancelled, Returned)

=== TABS ===

Tab 1: "Revenue Overview" — 4 widgets
Tab 2: "Orders & Customers" — 3 widgets
Tab 3: "Trends" — 2 widgets

=== TAB 1: REVENUE OVERVIEW ===

Widget 1: Total Revenue (KPI)
  • Chart Type: KPI card with trend
  • Metric: Total Revenue
  • Calculation: SUM(amount) WHERE status NOT IN ('cancelled', 'refunded')
  • Sample Value: $4,859,839
  • Filters Applied: Date Range, Region, Order Status
  • Definition: Total revenue from all completed orders (excludes cancelled/refunded)

Widget 2: Revenue by Region (Bar Chart)
  • Chart Type: Horizontal Bar Chart
  • Metric: Total Revenue
  • Dimensions: Region (x-axis shows region, y-axis shows revenue)
  • Calculation: SUM(amount) BY region WHERE status NOT IN ('cancelled', 'refunded')
  • Sample Data: North America ($2.1M), Europe ($1.5M), APAC ($900K), ...
  • Filters Applied: Date Range, Order Status (not Region — Region is displayed)
  • Definition: Revenue breakdown by geographic region

Widget 3: Revenue Trend (Line Chart)
  • Chart Type: Line Chart
  • Metric: Daily Revenue
  • Dimensions: Date (x-axis), Revenue (y-axis)
  • Calculation: SUM(amount) BY DATE(order_date) WHERE status NOT IN ('cancelled', 'refunded')
  • Period: Last 90 days (daily data points)
  • Filters Applied: Date Range, Region, Order Status
  • Definition: Daily revenue trend over time to spot seasonal patterns

Widget 4: Revenue by Order Status (Pie Chart)
  • Chart Type: Pie Chart
  • Metric: Revenue by Status
  • Dimensions: Order Status (slices)
  • Calculation: SUM(amount) BY status
  • Sample Data: Completed (85%, $4.1M), Cancelled (3%, $150K), Returned (2%, $80K), Pending (10%, $530K)
  • Filters Applied: Date Range, Region (not Status — Status is displayed)
  • Definition: Revenue distribution across order statuses

=== TAB 2: ORDERS & CUSTOMERS ===

Widget 1: Order Count (KPI)
  • Chart Type: KPI card
  • Metric: Order Count
  • Calculation: COUNT(*) FROM orders
  • Sample Value: 2,156,492
  • Filters Applied: Date Range, Region, Order Status
  • Definition: Total number of orders

Widget 2: Active Customers (KPI)
  • Chart Type: KPI card
  • Metric: Unique Customers
  • Calculation: COUNT(DISTINCT customer_id) WHERE purchase_date >= DATE_SUB(NOW(), 90 DAY)
  • Sample Value: 1,234,567
  • Filters Applied: Date Range, Region
  • Definition: Customers with at least 1 purchase in last 90 days

Widget 3: Orders by Status (Table)
  • Chart Type: Data Table
  • Metrics: Count, Revenue, Avg Order Value
  • Dimensions: Order Status (rows)
  • Calculation: COUNT(*), SUM(amount), AVG(amount) BY status
  • Sample Data:
    | Status     | Count   | Revenue  | Avg Value |
    | Completed  | 1.8M    | $4.1M    | $2,281    |
    | Pending    | 215K    | $530K    | $2,465    |
    | Cancelled  | 107K    | $150K    | $1,402    |
    | Returned   | 34K     | $80K     | $2,353    |
  • Filters Applied: Date Range, Region (not Status — Status is displayed)
  • Definition: Detailed breakdown of orders by status with metrics

=== TAB 3: TRENDS ===

Widget 1: Orders per Day (Line Chart)
  • Chart Type: Line Chart
  • Metric: Daily Order Count
  • Dimensions: Date (x-axis), Order Count (y-axis)
  • Calculation: COUNT(*) BY DATE(order_date)
  • Period: Last 90 days
  • Filters Applied: Date Range, Region, Order Status
  • Definition: Daily order volume trend

Widget 2: Customer Acquisition (Cumulative Line)
  • Chart Type: Cumulative Area Chart
  • Metric: New Customers
  • Dimensions: Date (x-axis), Cumulative Count (y-axis)
  • Calculation: COUNT(DISTINCT customer_id) CUMULATIVE BY DATE(first_purchase_date)
  • Period: Last 90 days
  • Filters Applied: Date Range, Region
  • Definition: Cumulative new customer count over time

=== DATA SOURCE ===

Source Database:   analytics_prod
Tables:
  • orders (2.1M rows, updated 2h ago) — FACT
  • customers (156K rows, updated 1d ago) — DIMENSION
  • regions (6 rows, static) — DIMENSION

Dashboard Complexity Score:   5/6
Date Range:        Last 90 days
Data Freshness:    Updated 2 hours ago
Rendering:         HTML Client (standalone, portable)

=== HTML CLIENT DATA VALIDATION ===

**Filters Analysis:**
- Global Filters: Date Range, Region (6), Order Status (4)
- Filter data size: ~300 bytes
- Cardinality check: All filters < 50 values ✅

**Widget Data Size Estimates (Phase 1 Stage B):**

| Widget | Type | Rows | Size | Filter Impact | Status |
|--------|------|------|------|---------------|--------|
| Total Revenue (KPI) | KPI | 1 | < 1 KB | Uses all global filters | ✅ Safe |
| Revenue by Region (Bar) | Bar | 6 | < 5 KB | Region not in filter (shown in chart) | ✅ Safe |
| Revenue Trend (Line) | Line | 90 | < 30 KB | Uses all global filters | ✅ Safe |
| Revenue by Status (Pie) | Pie | 4 | < 2 KB | Status not in filter (shown in chart) | ✅ Safe |
| Order Count (KPI) | KPI | 1 | < 1 KB | Uses all global filters | ✅ Safe |
| Active Customers (KPI) | KPI | 1 | < 1 KB | Uses all global filters | ✅ Safe |
| Orders by Status (Table) | Table | 4 | < 5 KB | Status not in filter (shown in table) | ✅ Safe |
| Orders per Day (Line) | Line | 90 | < 30 KB | Uses all global filters | ✅ Safe |
| Customer Acq (Cumulative) | Area | 90 | < 30 KB | Uses global filters (Region, Date) | ✅ Safe |

**Total Size Breakdown:**
- Widget data: ~105 KB
- Filter dropdown options: ~300 bytes
- HTML/JS/CSS: ~50 KB
- JSON overhead (+20%): ~31 KB
- **Final HTML File:** ~186 KB

**Feasibility:** ✅ SAFE FOR HTML CLIENT
- Load time (estimated): < 1 second
- Browser compatibility: All modern browsers
- Performance: Smooth interactions, all filters responsive
- Filter complexity: Low (3 filters, max 6 values each)
- Tab complexity: Low (3 tabs)

**Actions Taken:** None needed — data and filters well within safe limits

Conflicts Detected: None
```

**Then ask:**
> "Does this dashboard plan look correct? If yes, we'll move to the next step. If no, what needs to change?"

**Why:** Users need to see a clear summary of what they're approving — metrics, dimensions, data freshness, and path — before committing to Phase 2 or Phase 3.

---

## Next Action

1. ✓ Phase 1 complete
2. User to review state.md and approve
3. If Score ≤2: Jump to Phase 3 (`../phase-3/INSTRUCTIONS.md`)
4. If Score 3: User decides Phase 2 or Phase 3
5. If Score ≥4: Jump to Phase 2 (`../phase-2/INSTRUCTIONS.md`)
```

---

## Phase 1 Pre-Flight Checklist

**Before starting Phase 1 Stage A, verify:**

### Engagement Setup
- [ ] Engagement type confirmed: new project or resuming existing?
- [ ] If resuming: project name confirmed, state.md located
- [ ] User understands Phase 1 goal (1-2 hours, produces state.md)

### Data Access
- [ ] TD account accessible (`tdx auth show` works)
- [ ] User can access required databases (`tdx databases` list returned)
- [ ] At least one source table accessible via `tdx query`

### Requirements Clarity
- [ ] User has basic idea of KPIs (even if rough)
- [ ] User has basic idea of audience (who will use this?)
- [ ] User willing to validate requirements against real data (Phase 1 Stage B)

---

## Phase 1 Decision Tree

```
START Phase 1 Stage A: Gather Requirements
    ↓
Ask: KPIs? Dimensions? Filters? Audience?
    ↓
START Phase 1 Stage B: Validate Against Data
    ↓
For each source table:
    - Run: tdx describe <db>.<table>
    - Verify columns exist (exact spelling)
    - Test joins with sample queries
    ↓
Calculate Dashboard Complexity Score (0-6)
    ↓
DECISION POINT:
    Score 0-2?  → Route to Phase 3 (skip Phase 2)
    Score 3?    → Ask user: Phase 2 (workflow) or Phase 3 (direct)?
    Score 4-6?  → Route to Phase 2 (workflow)
    ↓
Create state.md with requirements + findings
    ↓
Get user approval on state.md
    ↓
END Phase 1
```

---

## Common Phase 1 Blocks

### "I don't know my KPIs"
**Response:** 
> "That's OK. Let's start with a metric you want to track. Common examples: Revenue, Customer Count, Churn, Conversion Rate, NPS. What matters most to your business right now?"

### "The data might not exist"
**Response:**
> "Let's check! I'll run `tdx describe` on the table. If the column doesn't exist, we have two options: (1) find an alternative metric in the data, or (2) flag this as a data gap for your team to build."

### "I have 20 metrics I want"
**Response:**
> "Great. Let's prioritize by importance. Which 3-5 are must-haves? We can always add more later. (Phase 1 goal is to validate the core requirements, not build everything.)"

### "I'm not sure if the join will work"
**Response:**
> "Perfect. Let me test it. I'll run: `SELECT COUNT(DISTINCT customer_id) FROM customers` and `SELECT COUNT(DISTINCT customer_id) FROM orders`. If counts match (within 5%), the join is clean. If not, we have a fan-out issue that Phase 2 will handle."

---

## Phase Progression Gate (CANNOT Skip)

**⚠️ CRITICAL: Before proceeding to Phase 2 or Phase 3, verify:**

- [ ] All Stage A questions answered (1a-1o)
- [ ] All Stage B data validations complete (tables confirmed, columns verified, joins tested)
- [ ] **HTML Client data size validated** (all widgets checked, feasibility confirmed)
- [ ] Dashboard Complexity Score calculated (0-6, with breakdown)
- [ ] Dashboard Plan Summary displayed to user (Rule P1-12) — includes data validation
- [ ] User reviewed and approved the plan (including data feasibility)
- [ ] Path Confirmation obtained (Rule P1-11)
- [ ] state.md created with ALL Phase 1 results:
  - Business requirements documented
  - Data findings documented
  - Time column identified
  - Join keys validated
  - Dashboard Complexity Score and justification
  - Dashboard plan summary captured
  - Path decision (Phase 2 or Phase 3) with user approval
  - "Next Action" pointer

**If ANY item is missing:**
> "Cannot proceed to next phase. Phase 1 incomplete.
> Missing: [specific item]
> Please complete before moving forward."

**Only after all items verified:**
- Append "Phase 1 COMPLETE" to state.md with timestamp
- Record: "Dashboard plan reviewed and approved by user"
- Move to next phase based on Dashboard Complexity Score and user confirmation

---

## After Phase 1 Completes

**If Score 0-2:**
```
✓ Phase 1 Complete → Jump to Phase 3
  Read: ../phase-3/INSTRUCTIONS.md
  Then: ../phase-3/SKILL.md
```

**If Score 3:**
```
✓ Phase 1 Complete → User Decision
  Option A: Phase 2 (workflow for scheduled refresh)
    Read: ../phase-2/INSTRUCTIONS.md
  Option B: Phase 3 (direct build, no workflow)
    Read: ../phase-3/INSTRUCTIONS.md
```

**If Score 4-6:**
```
✓ Phase 1 Complete → Phase 2 Required
  Read: ../phase-2/INSTRUCTIONS.md
  Then: ../phase-2/SKILL.md
```

---

**Version:** 1.0.0
**Last Updated:** 22 July 2026
**Load Order:** 1.1 (read after master INSTRUCTIONS.md)
