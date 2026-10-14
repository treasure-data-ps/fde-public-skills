# Stage B: Core Discovery Steps (2a-2e) — WITH EXTENDED DISCOVERY & INFERENCES

> **⛔ GUARDRAILS CHECK — before doing anything else:**
> Have you read `../../references/guardrails-lite.md` this session?
> ```
> AskUserQuestion:
>   header: "Guardrails"
>   question: "Have you read guardrails-lite.md this session?"
>   options:
>     - label: "Yes — proceed"
>       description: "guardrails-lite.md was read at session start"
>     - label: "Read it now"
>       description: "Load guardrails-lite.md before continuing"
> ```
> If "Read it now" → read `../../references/guardrails-lite.md` in full before any step.

## Step 2a: Discover & Select Database

**What to do:**
- Use `state.md` Session Setup block to narrow database search
- Confirm database selection with the user

**Stage A context (preferred path):**
1. Read the **Session Setup** block in `state.md` from Stage A
   - If a database was named: confirm it exists, verify access → skip to Step 2b
   - If a domain was mentioned ("sales data", "CDP data"): filter databases by name pattern
   - If no hint given: list all databases (fallback)

**Fallback — list all databases:**
1. Run `tdx databases` to list all available databases
2. Show results as markdown table: Database name, Table count, Last updated
3. Use **AskUserQuestion** to let the user choose
   - Annotate with Stage A context
   - Include database name, table count, recency as decision factors
   - Never assume or default to a database

**Output:** Selected database name (e.g., `analytics_prod`, `sales_db`)

---

## Step 2b: Discover & Confirm Tables (WITH EXTENDED DISCOVERY)

**What to do:**
- List tables containing Stage A metrics/dimensions
- **If the Stage A specified database has GAPS** (missing KPIs/dimensions/filters):
  - EXTEND search to OTHER databases in the account
  - Discover tables that could fill gaps
  - Recommend additional data sources
- Confirm which tables to use
- Assess table size and freshness
- Classify tables by source type

**Action items:**

1. **Primary search (Stage A specified database):**
   - Run `tdx tables --in <database>` to list all tables (NOT `tdx describe <database>` — describe always requires a specific table, it errors on a bare database name)
   - **FILTER for relevance:** Only show tables matching Stage A requirements
     - Stage A metrics: "Revenue, Order Count, AOV" → Look for `orders`, `transactions`, `sales`
     - Stage A dimensions: "Region, Segment" → Look for `customers`, `accounts`, `geography`
   - For each relevant table, get: row count, date range, update frequency, classification (Behavior/Attribute/Aggregate)

2. **Data Gap Discovery:**
   - Ask: "Do you have a transactions or sales table?" (if revenue is needed and not found)
   - Ask: "What revenue columns are available? (unit price, total price, service revenue, gross profit?)"
   - Ask: "Are there any metrics from Stage A you're unsure if we have data for?"
   - **Document any gaps** before proceeding to Step 2c

3. **Extended Search (if gaps found):**
   - Don't stop if the initial database lacks data
   - Search OTHER databases in the account:
     - Marketing DB (for campaign/email metrics)
     - Analytics DB (for pre-calculated metrics/segments)
     - CDP DB (for customer attributes/segments)
     - Product DB (for usage/feature metrics)
     - etc.
   - For each gap metric/dimension, find alternative source tables
   - Recommend extended data sources to the user

**Example extended discovery:**
```
Stage A specified: sales_db (orders table)
Stage B finds: No email/campaign data for "Email Open Rate" needed

Extended search:
✅ Found: marketing_db.campaigns table → email_opens, email_sends
✅ Found: analytics_db.customers table → customer_segment, lifecycle_stage

Recommendation:
- Use marketing_db.campaigns for email metrics
- Use analytics_db.customers for segment dimensions
- Join orders → customers → campaigns for full dashboard
```

4. **Time Column Discovery (CRITICAL — run for every confirmed behavior table):**

   Treasure Data tables always have a system `time` column, but `time` is **insert time** (when the row was written to TD), not the business event timestamp. For date filtering, trend analysis, and time-series metrics to be correct you must identify the **business event datetime column** — the column that records when the event actually happened.

   **For each confirmed behavior table, run this discovery sequence:**

   ```sql
   -- Step 1: List all columns and find candidates
   -- Run: tdx describe <database>.<table>
   -- Look for columns with types: timestamp, datetime, date, bigint (epoch), varchar (ISO date string)
   -- Candidate names to watch for: event_time, event_at, created_at, order_date,
   --   transaction_date, purchase_date, session_start, click_time, activity_date,
   --   record_date, action_date, log_time — anything that looks like a business moment
   ```

   ```sql
   -- Step 2: Check if the candidate column contains real business dates
   -- (not all the same value, not all NULLs, spread across a meaningful date range)
   SELECT
     MIN(<candidate_col>)  AS earliest,
     MAX(<candidate_col>)  AS latest,
     COUNT(*)              AS total_rows,
     COUNT(<candidate_col>) AS non_null_rows
   FROM <database>.<table>
   ```

   ```sql
   -- Step 3: Compare the candidate column to the system `time` column
   -- If they differ significantly, the candidate is the true business datetime
   SELECT
     FROM_UNIXTIME(time)   AS td_insert_time,
     <candidate_col>       AS business_event_time
   FROM <database>.<table>
   LIMIT 10
   ```

   **Decision rules after running the queries:**

   | Finding | Classification | What to record |
   |---------|---------------|----------------|
   | Candidate column has a wide date range (months/years) AND differs from `time` column | ✅ Business event datetime found | Record column name + type; use for all date filters |
   | Candidate column matches `time` column within minutes on most rows | ⚠️ Likely insert time too | Flag — ask the user if a separate event datetime exists |
   | No candidate column found beyond `time` | ⚠️ Insert-time only | Table is time-ordered by ingestion, not by event; flag for the user |
   | Table has no date-like columns at all (no `time`, no candidates) | 🔴 Snapshot / reference table | Classify as snapshot; omit all date filters for this table (see Step 2d-filter) |
   | Table has no system-usable time column, but has a varchar date column (e.g. `join_date`, `signup_date`) | 🟡 Attribute with date field | Treat as **snapshot for filter scope** (date range filter silently ignored); varchar date available for **cohort analysis only** (see Step 2d-filter cohort note) |

   **Ask the user if the correct column is not obvious:**

   ```
   AskUserQuestion:
     header: "Event datetime"
     question: "For table <table_name>, which column records when the event actually happened?
       • <col_1> (type: <type>, range: <min> → <max>)
       • <col_2> (type: <type>, range: <min> → <max>)
       • time (system column — insert time)"
     options:
       - label: "<col_1>"
         description: "Business event datetime for filtering"
       - label: "<col_2>"
         description: "Business event datetime for filtering"
       - label: "time"
         description: "No separate event datetime available"
       - label: "Snapshot table"
         description: "No time-based filtering applies"
   ```

   **Record findings in the time column summary (one row per table):**

   ```
   TIME COLUMN SUMMARY
   ──────────────────────────────────────────────────────────────────────────────────────────
   Table                   | System `time` | Business datetime col | Type      | Date Range (min → max)            | Status
   ──────────────────────────────────────────────────────────────────────────────────────────
   orders                  | insert time   | order_date            | date      | 2023-01-01 → 2026-06-28 (3.5 yrs) | ✅ Use order_date
   sessions                | insert time   | session_start         | timestamp | 2024-03-15 → 2026-06-28 (15 mo)   | ✅ Use session_start
   customers               | insert time   | (none found)          | —         | N/A — snapshot                    | 🔴 Snapshot — no date filter
   campaign_sends          | insert time   | sent_at               | bigint    | 2025-01-01 → 2026-06-28 (18 mo)   | ✅ Use sent_at (epoch → convert)
   product_catalog         | insert time   | (none found)          | —         | N/A — snapshot                    | 🔴 Snapshot — no date filter
   ──────────────────────────────────────────────────────────────────────────────────────────
   ```

   **Why date range matters:** The min/max values tell you:
   - Whether the table covers the Stage A historical depth requirement (e.g. "need 2 years" → check min date)
   - Whether to flag a data gap to the user (e.g. table only has 3 months but trends need 12+)
   - The safe default date range for Phase 3 dashboard filters (never default beyond max date)
   - Whether a behavior table is effectively a snapshot (all rows have the same date → treat as snapshot)

   **After recording the summary, run this gap check against Stage A:**

   | Stage A Historical Depth | Table Date Range | Status |
   |--------------------------|-----------------|--------|
   | User said "2 years" | min = 2024-01-01 (18 months only) | ⚠️ Gap — flag to the user |
   | User said "last 90 days" | min = 2023-01-01 | ✅ Covered |
   | User said "Not sure" | min = 2024-06-01 | ✅ Document range, confirm with the user |

   **Epoch / bigint column handling** — if the business datetime column is a `bigint` (Unix epoch seconds or milliseconds), confirm unit and note the conversion needed:

   ```sql
   -- Check if bigint is seconds or milliseconds
   SELECT
     <bigint_col>,
     FROM_UNIXTIME(<bigint_col>)         AS if_seconds,
     FROM_UNIXTIME(<bigint_col> / 1000)  AS if_milliseconds
   FROM <database>.<table>
   LIMIT 5
   -- Whichever produces a plausible business date (e.g. 2023-01-15) is the right unit
   ```

   Record: `<col_name> (bigint epoch — divide by 1000 for ms, or use as-is for s)` in the time column summary.

   **Output of this sub-step** — added to the Step 2b table classification output:
   - Time column summary table (one row per confirmed table)
   - For each behavior table: business event datetime column identified (or flagged as unknown/snapshot)
   - Epoch conversion note where applicable
   - List of snapshot tables → fed directly into Step 2d-filter (these tables ignore date range filters)

---

**Output:**
- Confirmed list of tables (fact + dimension + aggregate)
- Table classification (Behavior vs Attribute vs Snapshot vs Aggregate)
- **Time column summary** — business event datetime column per table (or snapshot flag)
- Data quality assessment
- **Documented data gaps** (or confirmation all Stage A metrics have data sources)
- **Extended data sources recommended** (if gaps filled by other databases)

---

## Step 2c: Discover Metrics & INFER Definitions (WITH RECOMMENDATIONS)

**What to do:**
- Run queries to INFER metric definitions from real data (not just validate)
- Get real data samples for each metric
- Recommend additional KPIs/metrics discoverable from same tables
- Clarify ambiguous metric definitions explicitly
- Validate exclusion rules in SQL
- Recommend exclusions based on use case

**Critical: Large Table Handling**

If table has billions of rows or query timeout risk:
- Use filtered queries first before aggregations
- Apply Stage A filters (date range, status, exclusions)
- If Presto times out: Try Hive with `set hive.exec.parallel=true`
- Contact TD Skills: `sql-skills:trino-optimizer`, `sql-skills:time-filtering`
- **Document any performance constraints** — very large record-level exports are a poor fit for the HTML Client's inlined-data pattern; consider pre-aggregating harder in Phase 2 (Workflow)

**Action items:**

1. **For EACH metric from Stage A, INFER definition from data:**
   - Column exists and has correct data type?
   - Column contains non-zero values (not all nulls)?
   - Run sample query with Stage A filters applied
   - **INFER the actual calculation** from database schema + data patterns
   - Example: "Total Revenue = SUM(order_amount) where status != 'cancelled'" (inferred from data structure)

2. **Clarify ambiguous metric definitions explicitly (CRITICAL):**

   For any metric that could have multiple valid definitions, ask the user:

   | Metric | Possible Definitions | What to Ask |
   |--------|---------------------|-----------|
   | **Email Open Rate** | (A) Unique customers who opened ≥1 time vs (B) Total opens / Total sends | "Which calculation?" |
   | **Revenue** | (A) Gross vs (B) Net revenue vs (C) Service only | "Which revenue type?" |
   | **Active Customer** | (A) 30 days vs (B) 90 days vs (C) 180 days lookback | "What's the 'active' window?" |
   | **Churn** | (A) Customers in period N vs N-1 vs (B) % inactive last 30d | "How do we define churn?" |

   **If the user hesitates:** "I can show both definitions in the dashboard for comparison." (Often resolves ambiguity.)

   **Document the definition** in `state.md` (Stage B Data Discovery block) before proceeding

3. **Get real sample values — and verify WHERE clause matches the metric definition:**
   - Metric: "Total Revenue" → Column: order_amount → Sample: $1,250,432 (last 90 days)
   - Metric: "Order Count" → Aggregation: COUNT(*) → Sample: 45,821 (last 90 days)
   - Show sample queries + results to the user for validation

   ⚠️ **CRITICAL: Verify the WHERE clause actually matches the metric's stated definition before recording the sample value.** This is especially easy to get wrong for "lookback window" metrics (active customers, recent purchases, last-N-days revenue) — it's easy to run the unfiltered query and label the result as filtered.

   **Check:** Does the query include the date/filter the metric implies?
   - "Active Customers (90-day)" → WHERE clause must include `event_date >= CURRENT_DATE - INTERVAL 90 DAY` (or equivalent). An unfiltered `COUNT(DISTINCT customer_id)` will produce the all-time count, not the 90-day count — and the numbers are often close enough to look plausible.
   - Record the **exact WHERE clause** alongside the sample value in `confirmed-values-checkpoint.md` so Phase 2 and Phase 3 can reproduce the same number.

   **Why this matters:** If the wrong (unfiltered) number ships as the Stage B spot-check, the Phase 2 SINK query and Phase 3 KPI card will both be validated against the wrong baseline — the error silently propagates through all phases.

4. **Validate exclusion rules in SQL:**
   - Stage A said: "Exclude cancelled orders"
   - Run: `SELECT COUNT(*) FROM orders WHERE status = 'cancelled'` → % excluded?
   - If >50% excluded: **FLAG to the user** (may indicate wrong metric definition)
   - Propose alternative: "Maybe we should only exclude fully refunded orders?"

5. **Recommend additional KPIs/metrics (discoverable from same tables):**

   After validating Stage A metrics, scan numeric/date columns for additional metrics. Present as "Recommended metrics" list.

   **Discovery rules:**
   - Scan all numeric columns not already in the Stage A list
   - Scan all date/timestamp columns for time-based metrics
   - Group recommendations by category

   **Present to the user:**
   ```
   ✅ Stage A Metrics Validated: [Revenue, Order Count, AOV]

   💡 Recommended Additional Metrics (discoverable from same tables):
   - Repeat Purchase Rate: % customers with >1 order
   - Avg Days Between Orders: Average days since last order
   - Customer Lifetime Value (approx): Total revenue per customer
   - Return Rate: % orders with status='returned'
   - Top Product Revenue: Revenue by product

   Would you like to add any of these? [AskUserQuestion: multiselect]
   ```

   **If Stage A provided NO metrics:** Scan ALL numeric columns in confirmed tables; propose 5–10 most meaningful; require the user to select at least 3

6. **Recommend exclusions based on use case:**

   Based on data patterns + use case, propose sensible exclusions:

   ```
   Recommended Exclusions (based on use case):
   - Exclude: test@company.com, internal@company.com emails
   - Exclude: test orders (order_id like 'TEST%')
   - Exclude: orders with value < $0 (refunds/credits)
   - Exclude: internal/admin users (user_type = 'admin')
   - Exclude: duplicate/cancelled transactions (status IN ('cancelled', 'duplicate'))

   Do you agree with these exclusions? Any others?
   ```

**Output:**
- Confirmed list of queryable metrics with INFERRED definitions
  - Metric name, column name, aggregation type
  - **Real sample value from database** (e.g., $4,859,839.20)
  - Definition inferred and confirmed with the user if uncertain
- **Recommended metrics list** (user-approved additions)
- **Recommended exclusions list** (use case-based)
- **Benchmark Values** — populate `state.md` Session Setup `Benchmark Values` field NOW with the real sample values discovered here (e.g. `"Revenue: $4.3M/month, AOV: $658, Open Rate: 46%"`). Do NOT leave it as a placeholder — Step 2f-4 (see `stage-b-path-routing.md`) will read this field when appending Stage B content.

---

## Step 2d: Discover Dimensions & INFER Definitions (WITH RECOMMENDATIONS)

**What to do:**
- Run DISTINCT queries to find actual dimension values
- INFER business definitions from data patterns
- Recommend additional dimensions/filters discoverable from extended search
- Validate join paths (no duplicates)
- Recommend exclusions based on use case

**Action items:**

1. **For EACH Stage A dimension, run DISTINCT queries:**

```sql
-- Get all distinct values for a dimension
SELECT DISTINCT region 
FROM customers 
ORDER BY region;

-- Get dimension value counts
SELECT segment, COUNT(DISTINCT customer_id) as customer_count 
FROM customers 
GROUP BY segment 
ORDER BY customer_count DESC;
```

2. **Compare Stage B findings to Stage A expectations:**

| Stage A Expected | Stage B Found | Status | Action |
|---|---|---|---|
| "6 regions" | 10 regions found | ✅ **OK (superset)** | Use all 10; recommend extended dimensions |
| "Status: Active, Inactive" | Status: Active, Inactive, Trial, Suspended | ✅ **OK** | Use all 4; recommend clarifying "active" |
| "Product: A, B, C" | Product: A, B, C, D, E | ✅ **OK** | Use all 5; recommend extended product filtering |
| "Regions: North, South, East" | Regions: North America, Latin America, APAC | ⚠️ **MISMATCH** | Names different? Ask the user |

3. **INFER business definitions from data patterns:**

```
Dimension: "Customer Status"
Data found: Active (45%), Inactive (30%), Trial (15%), Suspended (10%)

INFERRED business definition:
- Active: Customer with ≥1 purchase in last 90 days
- Inactive: Customer with no purchase in last 90 days (but >1 purchase ever)
- Trial: Customer in free trial (trial_end_date > today)
- Suspended: Customer account suspended (suspend_date <= today AND suspend_date NOT NULL)

Confirm with the user: Is 90 days the correct "active" definition? Or 30/180 days?
```

4. **Validate join paths (NO DUPLICATES):**

```sql
-- Check for duplicate rows after join
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT order_id) as unique_orders
FROM orders
LEFT JOIN customers ON orders.customer_id = customers.id
WHERE order_date >= DATE_SUB(current_date, interval 30 day);

-- If total_rows > unique_orders: JOIN IS BROKEN (duplicates!)
```

5. **Validate cardinality (watch for fan-out):**

```sql
-- One-to-many check (should NOT create massive fan-out)
SELECT customer_id, COUNT(*) as order_count 
FROM orders 
GROUP BY customer_id 
ORDER BY order_count DESC 
LIMIT 10;

-- If a single customer has 1000s of orders: 
-- Joining to dimension will cause massive fan-out
-- Flag for Phase 3 GROUP BY strategy or SINK grain review
```

6. **Recommend additional dimensions/filters (from extended search):**

```
✅ Stage A Dimensions Confirmed: [Region, Customer Status, Product]

💡 Recommended Additional Dimensions (discoverable from extended search):
- Campaign Name (from marketing_db.campaigns)
- Email Channel (from marketing_db.campaigns)
- Customer Segment (from analytics_db.customers)
- Product Category (from product_db.products)
- Subscription Type (from billing_db.subscriptions)

Would you like to add any of these dimensions? [AskUserQuestion: multiselect]
```

7. **Check for data quality issues:**

```sql
-- Find NULLs in dimension
SELECT COUNT(*) as null_count 
FROM orders 
WHERE region IS NULL;

-- Find unexpected values
SELECT DISTINCT region 
FROM orders 
WHERE region NOT IN ('North America', 'Europe', 'APAC');
```

**Output:**
- Confirmed list of queryable dimensions with INFERRED business definitions
  - Dimension name, source table, column name
  - **Actual distinct values** (list or count + examples)
  - Business definition INFERRED from data and confirmed with the user if uncertain
  - Cardinality (1:1, 1:many, many:many)
  - Join path validation status
- **Recommended additional dimensions** (user-approved additions)
- Data quality flags (NULLs, unexpected values)

---

## Step 2d-filter: Classify Filter Scope

**When to run:** After Step 2d dimensions are confirmed, before Step 2d-ext tab grouping.

**What to do:** For every confirmed filter/dimension, determine whether it can be applied at dashboard level, tab level, or widget level — based on which tables/columns it can actually reach. This prevents silent pass-through bugs (Snapshot tables ignore date filters) and produces the correct filter hierarchy for the Phase 3 build.

**⚠️ CRITICAL RULE: A filter qualifies as dashboard-level ONLY if its column exists in EVERY tab's source table.** Common mistake: assuming filters with "universal" names (Date Range, Channel, Category) are dashboard-level without verifying they reach all tabs. If a filter column doesn't exist in even one tab's tables, it must be demoted to tab-level or widget-level. This catches Snapshot tables (which have no time column) and prevents the filter from being silently ignored on some tabs.

**Filter scope classification rules:**

| Condition | Scope | Action |
|-----------|-------|--------|
| Filter column exists in ALL tables used across ALL tabs | Dashboard-level | Apply globally |
| Filter column exists in tables used by SOME tabs but not all | **Tab-level only** (NOT dashboard) | Move to each applicable tab; do NOT place at dashboard level — demotion reason: reaches only [Tab list], not [Tab list] |
| Filter column exists in only ONE tab's table | Tab-level (that tab only) | Place on that tab only |
| Table has no time column (Snapshot) | Widget-level flag | Filter silently ignored — add info block on affected widgets |
| Filter column exists but only ONE widget on a tab uses it | Widget-level | Place as widget-level filter; add info block noting "this filter only changes this widget" |

**Action — for each confirmed filter candidate:**

1. List all tables used across all tabs (from Step 2d + Step 2d-ext layout)
2. For each filter: check which tables contain the filter column
3. Classify:

```
Filter: Date Range
  Applicable tables: orders ✅, customers ❌ (snapshot — no time column), regions ❌ (lookup — no time column)
  Tabs using orders: Tab 1 (Revenue), Tab 3 (Trends)
  Tabs using customers/regions only: Tab 2 (Customer Profile)
  
  → CANNOT be dashboard-level (doesn't reach Tab 2 meaningfully)
  → Place as tab-level filter on Tab 1 and Tab 3
  → On Tab 2: widgets sourced from customers/regions get ⚠️ info block:
     "Date Range filter does not apply to this widget — customer profile data is a snapshot (no date column)"

Filter: Region
  Applicable tables: orders ✅, customers ✅, regions ✅
  All tabs use at least one of these → applies everywhere
  
  → Dashboard-level ✅

Filter: Campaign
  Applicable tables: marketing_db.campaigns ✅
  Only Tab 4 (Marketing) uses this table
  Only 1 widget on Tab 4 uses campaign column
  
  → Widget-level filter on that specific widget only
  → Add info block: "Campaign filter only changes this chart — other widgets on this tab are not affected"
```

4. **Produce filter scope map** (input to Step 2d-ext and the Phase 3 build):

```
FILTER SCOPE MAP
────────────────────────────────────────────────
Dashboard-level filters (apply to ALL tabs + widgets):
  • <filter name>: <column> — reason: found in all tables

Tab-level filters (apply to specific tabs only):
  • <filter name>: <column> — applicable on: Tab N, Tab M
    → NOT on: Tab X (table <name> has no <column>)
    → Affected widgets on Tab X: ⚠️ info block required

Widget-level filters (apply to single widget only):
  • <filter name>: <column> — applicable on: Tab N → Widget "<title>" only
    → Info block text: "This filter only changes this widget"

Snapshot table filter exceptions (silent pass-through):
  • Table: <name> — no time column → Date Range filter silently ignored
    → Affected tabs: Tab N → Affected widgets: <list>
    → Info block text: "Date Range filter does not apply — <table> is a snapshot (no date column)"

Attribute-with-date-field tables (varchar date — cohort only):
  • Table: <name> — has <join_date/signup_date> (varchar) but no usable epoch time column
    → Date Range filter silently ignored (treat as snapshot for filter scope)
    → varchar date field available for cohort analysis (e.g., "members who joined in 2025")
    → Add info block on affected widgets: "Date Range filter does not apply — use <col> for join-date cohort analysis"
────────────────────────────────────────────────
```

**Example (Retail Analytics Dashboard):**
```
Filter: Date Range (order_date column)
  Tables: sales_db.orders ✅, sales_db.items ✅
  Snapshot tables (no time column): customer_db.customers ❌, customer_db.segments ❌
  
  Tabs and their source tables:
    • Tab 1 (Revenue): uses orders → ✅ can filter by date
    • Tab 2 (Inventory): uses items → ✅ can filter by date
    • Tab 3 (Customer Profile): uses customers only → ❌ NO date column in customers table
    
  Result: Date Range is DEMOTED from dashboard-level to TAB-LEVEL
    • Dashboard-level: NO — doesn't reach Tab 3 (customers is a snapshot)
    • Tab-level: ✅ Apply to Tab 1 + Tab 2 only
    • Tab 3: ⚠️ Add info block: "Date Range filter does not apply to this tab — customer profile data is a snapshot"

Filter: Region (region column exists in ALL tables)
  Tables: orders ✅, items ✅, customers ✅, segments ✅
  All tabs use at least one → 
  
  Result: Region stays DASHBOARD-LEVEL ✅
    • Apply globally across all tabs
```

**Output:** Filter scope map — fed directly into Step 2d-ext tab layout and the Phase 3 HTML Client build.

---

## Step 2d-ext: Propose Tab Grouping

**When to run:** After Step 2d-filter filter scope map is complete.

**What to do:** Group confirmed metrics and dimensions into proposed tabs. Use `proposed_tabs` from `state.md` if provided; otherwise infer from metric/dimension clusters. Apply the filter scope map from Step 2d-filter to each tab — tab-level and widget-level filters must already be assigned before this layout is presented.

**Action:**

1. **Read `proposed_tabs` from `state.md`** — if the user named tabs in Stage A, use those as the skeleton. Map each confirmed metric/dimension to the nearest tab.

2. **If `proposed_tabs = TBD`** — infer grouping from data clusters:
   - Group transaction metrics (revenue, orders, AOV) → likely a Sales/Revenue tab
   - Group customer attributes (segment, lifecycle, LTV) → likely a Customer tab
   - Group product/category data → likely a Product tab
   - Group time-series data → likely a Trends tab

3. **Estimate widget count per tab** — count KPIs + charts + tables planned per tab. The HTML Client template inlines all data at build time, so very high total widget/row counts (100K+ rows) are a poor fit — flag and consider pre-aggregating harder in Phase 2 (Workflow) if this comes up.

4. **Apply filter scope map to each tab** — for each tab, pull its applicable filters from the Step 2d-filter output:
   - Dashboard-level filters: list which ones apply on this tab
   - Tab-level filters (demoted from dashboard): list with reason for demotion
   - Widget-level filters: assign to specific widgets; mark those widgets for info block
   - Snapshot widgets: mark with info block flag for Phase 3

5. **Present proposed tab layout:**

```
📐 Proposed Tab Structure (<N> tabs, ~<total> widgets total)

Dashboard-level filters (apply to ALL tabs):
  • <filter name> — <column>

Tab 1: <Title>
  Purpose: <1-line>
  Metrics: <list>
  Tab-level filters (this tab only):
    • <filter name> — <reason it couldn't be dashboard-level, e.g. "Date Range: customers table has no time column">
  Widget types: <KPI cards, bar chart, line chart, table>
  Estimated widgets: <N>
  Info blocks required:
    • Widget "<title>" — ⚠️ "<filter name> does not apply — sourced from <table> (snapshot / no time column)"
    • Widget "<title>" — ℹ️ "<filter name> only changes this widget — other widgets on this tab are unaffected"

Tab 2: <Title>
  Purpose: <1-line>
  Metrics: <list>
  Tab-level filters (this tab only):
    • <filter name> — <reason>
  Widget types: <...>
  Estimated widgets: <N>
  Info blocks required: None

... (repeat per tab)

Total estimated widgets: <N>
```

6. **Confirm with the user via AskUserQuestion:**

```
AskUserQuestion:
  header: "Tab grouping"
  question: "Does this proposed tab structure work?"
  options:
    - label: "Yes — looks good"
      description: "Proceed to Stage B exit checklist"
    - label: "Adjust grouping"
      description: "Move metrics between tabs or rename tabs"
    - label: "Add / remove a tab"
      description: "Change tab count"
```

**Output:** Confirmed tab layout + per-tab widget estimate + total widget count → feeds directly into the Phase 3 HTML Client build.

---

## Step 2e: Rendering (Fixed — HTML Client)

Rendering is always **HTML Client** — a single portable `dashboard.html` with data inlined at build time. No engine selection step runs here; this step is a no-op carried forward only for numbering continuity with the internal skill.

**Output:** `rendering_engine = HTML Client` (already recorded in Stage A, Step 1r-post).

---

---

## Step 2e-join: Validate Join Keys (If Joining Tables)

**Purpose:** Confirm that any join keys used across tables are compatible — same data type, same format — to prevent silent join failures.

**When to run:** If your dashboard metrics require joining two or more tables
**If no joins needed:** Skip this step

### Pre-Join Validation Checklist

Before writing any JOIN in your dashboard queries, verify the join keys:

**1. Sample both tables**
```sql
SELECT DISTINCT user_id FROM table_a LIMIT 10;
SELECT DISTINCT user_id FROM table_b LIMIT 10;
```
→ Do the IDs look identical? Same format?

**2. Check data types**
```sql
SELECT user_id, typeof(user_id) FROM table_a LIMIT 1;
SELECT user_id, typeof(user_id) FROM table_b LIMIT 1;
```
→ Are they both integers? Both strings? If different, join will fail silently.

**3. Check for nulls**
```sql
SELECT COUNT(*) FROM table_a WHERE user_id IS NULL;
SELECT COUNT(*) FROM table_b WHERE user_id IS NULL;
```
→ Null values won't match on a join

**4. Count the matches** (dry-run the join)
```sql
SELECT COUNT(*) as matched
FROM table_a a
JOIN table_b b ON a.user_id = b.user_id;
```

**5. Calculate match rate**
```sql
-- Compare matched count to total rows in table_a
-- (matched / table_a_total) should be >= 80%
```

**Interpret results:**
- **80-100% match:** ✅ Good — proceed with join
- **50-80% match:** ⚠️ Investigate — some IDs are missing from table_b
- **0-50% match:** ❌ Stop — join key format mismatch or incomplete data

### Example: Silent Join Failure (❌ WRONG)

```sql
-- table_a has user_id as INTEGER: 1, 2, 3
-- table_b has user_id_string as STRING: "1", "2", "3"

SELECT a.user_id, b.revenue
FROM table_a a
JOIN table_b b ON a.user_id = CAST(b.user_id_string AS INT)
-- Result: 0 rows matched (string → int cast behaves unexpectedly)
```

### Example: Working Join (✅ RIGHT)

```sql
-- Both tables have user_id as INTEGER
SELECT a.user_id, b.revenue
FROM table_a a
JOIN table_b b ON a.user_id = b.user_id
-- Result: All matching rows found
```

**Output:** Confirmed join keys are compatible → safe to proceed to Phase 2/3 queries.

---



---

## Step 2e-pii: Compliance & PII Handling (If Applicable)

**When to run:** If your dashboard will include personally identifiable information (PII) — emails, phone numbers, names, addresses, IP addresses, etc.

**If no PII:** Skip this step

### PII Detection Checklist

- [ ] Does any column contain: names, emails, phone numbers, addresses, IDs (SSN, passport, etc.)?
- [ ] Does any column contain: IP addresses, cookies, device IDs, or other tracking identifiers?
- [ ] Does the dashboard expose user-level data (not aggregated)?

If yes to any → Run compliance steps below.

### Implementation Template: PII Masking

```sql
-- ✅ MASK email addresses
SELECT 
  user_id,
  CONCAT(SUBSTRING(email, 1, 3), '***@***') as email_masked,
  revenue
FROM users;

-- ✅ MASK phone numbers
SELECT 
  user_id,
  CONCAT(SUBSTRING(phone, 1, 3), '***', SUBSTRING(phone, -4)) as phone_masked
FROM users;

-- ✅ HASH sensitive IDs (one-way, can't reverse)
SELECT 
  MD5(CONCAT(user_id, 'salt123')) as user_id_hashed,
  revenue
FROM users;

-- ✅ AGGREGATE to remove user-level exposure
SELECT 
  DATE_TRUNC('day', created_at) as date,
  COUNT(*) as user_count,
  SUM(revenue) as total_revenue
FROM users
GROUP BY 1;
```

### Compliance Frameworks

**GDPR (EU):** Personal data must be anonymized or pseudonymized. Use hashing or masking.

**CCPA (California):** Users have right to access/delete. Don't embed permanent hashes; use reversible encryption.

**HIPAA (Healthcare):** Requires encryption at rest + in transit. Consider: should this dashboard use HTTPS only?

**SOX (Financial):** Audit trail required. Log: who viewed, when, what data was exported.

### Recording in state.md

```markdown
## Compliance & PII

**Status:** [Not applicable / Masked / Aggregated / Encrypted]

**Approach:** [Describe what was done]
- Column: email → CONCAT(SUBSTRING(...), '***@***')
- Column: ssn → MD5(ssn || 'salt')
- Overall: Aggregated by date (no user-level exposure)

**Frameworks:** [GDPR, CCPA, HIPAA, SOX if applicable]

**Owner approval:** [Name + date]
```

---


**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
