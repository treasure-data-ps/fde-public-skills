# Stage A: Core Requirements Steps (1a-1o)

## Step 1a: Define Dashboard Purpose, Business Context & Success Criteria

**What to do:**
- Capture the company business model and company context in one sentence — grounds all metric definitions and filter logic
- Clarify what business question the dashboard answers
- Define who will use it, at what technical depth, and what decisions they'll make
- Establish concrete success criteria (how to know the dashboard is working)
- Ask about prior art — existing reports or dashboards this replaces or complements

**Key actions:**
- Ask: "In one sentence, what does this company/team do and how do they measure success?" (e.g., "B2B SaaS — we track ARR and churn")
- Ask user for business purpose (e.g., "Identify top-performing regions for Q4 strategy")
- Ask about **prior art**: "Has anyone tried to build this before? Is there an existing Excel report, Looker dashboard, or Metabase query we should replicate or replace?" — surfaces hidden metric definitions and sets baseline expectations for Phase 4
- Ask about **success metric for the dashboard itself**: "How will we know this dashboard is successful?" (e.g., "replaces the weekly Excel sheet", "leadership reviews it every Monday", "cuts time-to-answer from 1 hour to 5 minutes")
- Identify user audience and **technical depth**: executive summary (3 numbers) vs analyst drill-down (sortable tables, raw filters)
- Define 2-3 measurable success criteria

**AskUserQuestion:**

First discover available databases: `tdx databases`. Show as markdown table, then ask:

```markdown
I found these databases in your Treasure Data account:

| Database | Tables | Last Updated |
|----------|--------|--------------|
| analytics_prod | 45 | 2 hours ago |
| analytics_staging | 12 | 1 day ago |
| crm_db | 8 | 5 days ago |
```

```
AskUserQuestion:
  question: "Which database should we query?"
  header: "Source database"
  multiSelect: false
  options:
    - label: "analytics_prod (Recommended)"
      description: "45 tables, production, 2 hours old"
    - label: "analytics_staging"
      description: "12 tables, staging, 1 day old"
    - label: "Custom database"
      description: "Specify a different database"
```

**DO NOT:** Ask "What's your database name?" without options; assume a default like "analytics" or "main"; skip the discovery step.

**AskUserQuestion — Table Confirmation (Step 1a):**

Run `tdx tables --in <db>` to list tables, then `tdx describe <db>.<table>` per table of interest (NOT `tdx describe <db>.%` — describe rejects wildcards), classify tables by type, then confirm:

```markdown
I found these relevant tables in `analytics_prod`:

| Table | Type | Purpose | Rows | Recent Data |
|-------|------|---------|------|-------------|
| orders | Behavior | Transactional events — each row is one order | 2.1M | ✅ Today |
| customers | Attribute | Customer profiles — one row per customer (no time column) | 145K | ✅ Today |
| product_catalog | Snapshot | Product reference data — current state only | 8K | ⚠️ 3 days ago |
| daily_revenue_agg | Aggregate | Pre-aggregated daily revenue totals | 365 | ✅ Yesterday |

**Table type key:**
- **Behavior** — event/transactional tables with a business datetime column (e.g. orders, sessions, email_events). Date range filters apply.
- **Attribute** — entity state tables, one row per entity, no time column (e.g. customers, products, regions). Date filters do NOT apply.
- **Snapshot** — point-in-time reference tables with no meaningful time column. Date filters do NOT apply.
- **Aggregate** — pre-aggregated or ML output tables (e.g. SINK tables, RFM scores). May or may not have time column.

**Recommendation:** Include `orders` and `customers`. Review `daily_revenue_agg` — may skip Phase 2 (Workflow) if already pre-aggregated.
```

```
AskUserQuestion:
  question: "Should we proceed with these tables?"
  header: "Table confirmation"
  multiSelect: false
  options:
    - label: "Confirm as listed (Recommended)"
      description: "Use events and users"
    - label: "Exclude one or more"
      description: "I'll specify which tables to skip"
    - label: "Add tables"
      description: "Include additional tables"
```

**Output:** Business model (1 sentence) + dashboard purpose (1 sentence) + prior art notes + success metric + user audience + technical depth preference + success criteria (2-3 bullets)

---

## Step 1b: Define Metrics (What to Measure)

**Common Metrics Reference** — If user needs examples, suggest from this list by category:

| Category | Examples |
|----------|----------|
| **Financial** | Total Revenue, Avg Order Value, Gross Margin, Cost per Acquisition, Lifetime Value |
| **Volume** | New Customers, Orders, Page Views, Sessions, Sign-ups |
| **Growth** | Month-over-month Growth %, Year-over-year Growth %, Churn Rate, Retention Rate |
| **Performance** | Conversion Rate, Click-through Rate, Engagement Rate, Load Time, Error Rate |
| **Efficiency** | Cost per Customer, Revenue per Employee, Time to Resolution, Support Tickets Resolved |
| **Quality** | Net Promoter Score, Customer Satisfaction, Defect Rate, Data Accuracy % |

**What to do:**
- Ask what metrics the user wants to track
- Get metric definitions in their own words
- List 5-10 key performance indicators (KPIs)
- Capture the top 3-5 questions they most frequently ask of this data — surfaces implicit metrics they forgot to mention
- Collect a business glossary of domain-specific terms that appear in column names, segment names, or filter values

**Key actions:**
- Ask: "What metrics are most important?" (revenue, count, rate, efficiency?)
- Get user's definition: "How do you calculate Total Revenue?" — include edge cases (refunds? date restrictions? currency?)
- Ask: **"Which metric groups should this dashboard include?"** — e.g., "Sales, Customers, Products, Trends"
- Ask: **"What does a 'good' number look like for your top metric?"** — e.g., "Revenue should be around $5M last month", "Churn should be below 3%". Captured as `benchmark_values` in `state.md`. Used in Phase 4 as sanity-check baseline when validating widget output and in Stage B to flag if sample values are wildly off.
- Ask: **"What are the 3-5 questions you most frequently want answered from this data?"** — e.g., "Which reps are behind quota?" or "What's our churn by segment this month?" — these reveal implicit KPIs and dimensions not captured in the formal list
- Ask: **"Are there any business terms or abbreviations I should know?"** — e.g., "We call converted customers 'activated', status=4 means closed-won, ARR excludes trials" — document as a glossary
- Confirm business terms and abbreviations if provided
- Confirm metric list via AskUserQuestion

```
AskUserQuestion:
  questions:
    - header: "Metric groups"
      question: "Which metric groups should this dashboard include?"
      multiSelect: true
      options:
        - label: "Sales"
          description: "Revenue, deals, pipeline"
        - label: "Customers"
          description: "Acquisition, retention, churn, LTV"
        - label: "Operations"
          description: "Costs, efficiency, capacity"
        - label: "Products"
          description: "Usage, engagement, adoption"
        - label: "Marketing"
          description: "Campaigns, conversions, ROI"
        - label: "Custom groups"
          description: "I'll type custom metric groups"
        - label: "Generate from metrics"
          description: "Suggest groups based on our metrics discussion"

    - header: "Benchmark values"
      question: "What does a 'good' number look like for your top metric?"
      multiSelect: false
      options:
        - label: "Provide expected ranges"
          description: "e.g., Revenue ≈ $5M/month, Churn < 3%"
        - label: "No benchmarks yet"
          description: "Skip now — Phase 4 will flag unexpected values"
        - label: "Other context"
          description: "I'll describe benchmarks differently"
```

**Output:** List of 5-10 metrics + user's formula for each + metric groups + `benchmark_values` (top metric → expected range) + top 3-5 analytical questions + business glossary (domain terms, abbreviations, column value meanings)

---

## Step 1c+1d: Define Dashboard Structure, Dimensions, Filters, Layout & Interactions (Consolidated)

**⚠️ MANDATORY: This step captures comprehensive dashboard structure BEFORE detailed metric/dimension discovery.**

**What to do:**
- **Capture dashboard structure upfront** (tabs, visualizations, filters, drill-down, performance)
- Ask what dimensions users want to slice metrics by with typical values and unique counts
- List all filters users will need with dependencies
- Capture layout and visual preferences
- Confirm filter interactivity scope

**Key actions:**
- **STRUCTURE PHASE (ask first):**
  - Ask: "How many sections/tabs do you envision?" (single page / 2-3 tabs / 4+ tabs / drill-down structure)
  - Ask: "What visualization types do you need?" (KPI cards, trends, comparisons, distributions, tables, heatmaps)
  - Ask: "How should users interact?" (static / global filters / per-section filters / advanced cross-filters)
  - Ask: "Do users need drill-down?" (summary only / one level / multiple levels / detailed transactions)
  - Ask: "Performance targets?" (daily snapshot / multiple daily / hourly / live/on-demand)

- **REQUIREMENTS PHASE (after structure is clear):**
  - Ask: "How do you want to slice these metrics? By what categories?" (time, geography, segments, status?)
  - For each dimension, ask for examples and estimated unique value count
  - Ask: "What filters should users be able to adjust?" (date, region, segment, status, custom thresholds?)
  - Ask about filter dependencies: "Can I select any Region + Segment combination?"
  - Ask: **"Do you prefer summary cards at the top or raw tables? Charts or numbers? Color-coded status indicators or plain text?"** — captures layout preference before Phase 3 build
  - Ask: **"If you had to draw this on a whiteboard, what would it look like?"** — optional, often unlocks clearer mental model
  - Ask: **"Do you have brand colors or a logo you'd like applied to the dashboard?"** — capture hex codes or brand guide link; fall back to Treasure Data default theme if not provided. See output field `dashboard_theme` below.
  - Ask: **"Do you have a rough idea of how many sections or tabs you'd want?"** — e.g., "Sales, Customers, Products, Trends". Even a rough sketch here reduces rework later. Not required — Stage B will infer if not provided. Captured as `proposed_tabs` in `state.md`.
- Confirm all via AskUserQuestion

**AskUserQuestion — Dashboard Structure Batch 1: Tabs & Organization (Step 1c):**

```
AskUserQuestion:
  header: "Dashboard organization"
  question: "How many sections/tabs do you envision?"
  multiSelect: false
  options:
    - label: "Single page overview"
      description: "All metrics on one screen (3-8 widgets total)"
    - label: "2-3 focused tabs"
      description: "Overview + 1-2 detailed sections (8-15 widgets total)"
    - label: "4+ detailed tabs"
      description: "Segmented by business area/audience (15+ widgets)"
    - label: "Drill-down structure"
      description: "Summary view → click to drill into details"
    - label: "Not sure yet"
      description: "Will decide after we identify all metrics"
```

**AskUserQuestion — Dashboard Structure Batch 2: Visualization Types (Step 1c):**

```
AskUserQuestion:
  header: "Visualization types needed"
  question: "What visualization types do you need? (Select all that apply)"
  multiSelect: true
  options:
    - label: "KPI cards (summary numbers)"
      description: "Large numbers with trend indicators (Revenue: $4.5M ↑5%)"
    - label: "Trend charts (line charts)"
      description: "Revenue over 30 days, Customer growth over months"
    - label: "Comparison charts (bar charts)"
      description: "Revenue by region, Sales by product, Performance by team"
    - label: "Distribution charts (pie/donut)"
      description: "Market share by segment, Customer breakdown by tier"
    - label: "Detailed tables"
      description: "Transaction-level data, sortable columns, search"
    - label: "Heatmaps / color matrices"
      description: "Performance by region × product, Sales by channel × segment"
    - label: "Gauges / progress indicators"
      description: "Status vs target, completion %, performance meters"
    - label: "Not sure — recommend based on data"
      description: "Will decide during data discovery"
```

**AskUserQuestion — Dashboard Structure Batch 3: Filter & Interactivity (Step 1c):**

```
AskUserQuestion:
  header: "Filter & interactivity"
  question: "How should users interact with the dashboard?"
  multiSelect: false
  options:
    - label: "Static dashboard (no filters)"
      description: "Display fixed view, no user adjustments needed"
    - label: "Global date filter only"
      description: "Adjust date range, all metrics update together"
    - label: "Global filters (date + dimensions)"
      description: "Filter by date, region, segment, etc. — affects all metrics"
    - label: "Global + per-section filters"
      description: "Global filters + tab-specific filters (e.g., global date + regional filter on Tab 2)"
    - label: "Advanced (cross-filter interactions)"
      description: "Filters affect each other dynamically (select region → update product options)"
```

**AskUserQuestion — Dashboard Structure Batch 4: Drill-Down & Detail (Step 1c):**

```
AskUserQuestion:
  header: "Drill-down requirements"
  question: "Do users need to drill into detailed data?"
  multiSelect: false
  options:
    - label: "Summary only"
      description: "Aggregated view, no drill-down needed"
    - label: "One level deep"
      description: "Summary → click bar chart → see breakdown by category"
    - label: "Multiple drill-down levels"
      description: "Revenue → Region → Product → Customer → Transaction"
    - label: "Detailed transaction table"
      description: "Full data table with sorting, filtering, search"
    - label: "Not needed"
      description: "Only high-level aggregates"
```

**AskUserQuestion — Dashboard Structure Batch 5: Performance & Freshness (Step 1c):**

```
AskUserQuestion:
  header: "Performance & data freshness"
  question: "What are your performance and data freshness needs?"
  multiSelect: false
  options:
    - label: "Daily snapshot (static)"
      description: "Built once/day, shared as static HTML — cost-effective"
    - label: "Multiple times daily (2-4×)"
      description: "Rebuilt morning, midday, evening, EOD"
    - label: "Hourly or near real-time"
      description: "Refreshed every hour (or within 15 mins of data arrival)"
    - label: "Live/on-demand queries"
      description: "Fresh query each time dashboard loads (slower but latest)"
    - label: "Not sure — recommend based on data volume"
      description: "Will decide based on complexity and size"
```

**AskUserQuestion — Layout Preferences (Step 1c - visual styling):**

```
AskUserQuestion:
  header: "Layout & visualization style"
  question: "How do you prefer to view your metrics? (Select all that apply)"
  multiSelect: true
  options:
    - label: "Summary KPI cards"
      description: "Large numbers at the top with sparklines or trend indicators"
    - label: "Sortable data tables"
      description: "Raw data rows with filters and sorting"
    - label: "Charts (line, bar, pie)"
      description: "Visual trends and comparisons"
    - label: "Heatmaps / color-coded grids"
      description: "Visual patterns across dimensions"
    - label: "Gauges / progress indicators"
      description: "Status vs target, performance meters"
    - label: "Drill-down / multi-level detail"
      description: "Summary → click to see detail"
    - label: "Other layout style"
      description: "I'll describe what I want"
```

**AskUserQuestion — Dashboard Theme & Branding (Step 1c):**

```
AskUserQuestion:
  header: "Dashboard theme"
  question: "Do you have brand colors or a logo for this dashboard?"
  multiSelect: false
  options:
    - label: "Yes — I'll provide brand colors/logo (Recommended)"
      description: "Share hex codes, brand guide link, or logo. I'll apply to header, charts, KPI cards."
    - label: "No — use Treasure Data theme"
      description: "Clean blue/grey palette. Professional and neutral."
    - label: "Custom theme"
      description: "I'll describe the theme style I want"
    - label: "Not sure — decide later"
      description: "Build with TD theme now. Rebrand before Phase 3 if needed."
```

**If customer provides brand assets:** Capture:
- `primary_color` — main brand color (hex, e.g. `#1e40af`) — used for headers, KPI card accents, active tab indicators
- `secondary_color` — accent color (hex) — used for charts, highlights — optional
- `logo_url` — URL or file path to customer logo — displayed in dashboard header
- `logo_background` — `transparent` or `white` — determines header background treatment

**If no brand provided:** Set `dashboard_theme = "td-default"` — uses the clean Treasure Data blue/grey palette. See `../../references/treasure-data-theme.md` for the complete theme specification (CSS variables, chart colors, component styling).

**AskUserQuestion — Metrics/Dimensions Confirmation (Step 1b-1c):**

Show discovered metrics and dimensions as markdown first, then confirm:

```markdown
From your data, I found these metrics and dimensions:

**Metrics:** Total Revenue, Order Count, Avg Order Value, Unique Users
**Dimensions:** Date (365 days), Region (5 values), Segment (8 values), Category (42 values)
```

```
AskUserQuestion:
  question: "Which of these would you like to do?"
  header: "Metrics & dimensions adjustment"
  multiSelect: true
  options:
    - label: "Confirm all as listed (Recommended)"
      description: "Track all metrics across all dimensions"
    - label: "Remove some"
      description: "Skip specific metrics or dimensions"
    - label: "Add custom metrics"
      description: "Include additional metrics not yet discovered"
    - label: "Add custom dimensions"
      description: "Include additional dimensions or groupings"
    - label: "Other adjustments"
      description: "Something different — I'll describe what's needed"
```

**Output:**
- List of 3-5 dimensions + typical values + unique value estimates
- Complete filter list (names, types, dependencies)
- Layout preference (summary vs table, charts vs numbers, color coding)
- Filter combination assumptions
- `dashboard_theme` — `td-default` | `{ primary_color, secondary_color, logo_url, logo_background }` — written to `state.md` Session Setup; read during the Phase 3 dashboard build
- `proposed_tabs` — list of proposed tab names/topics from customer (e.g., "Sales, Customers, Products") | `TBD` — used in Stage B to validate tab grouping against discovered data

---

## Step 1e+1f: Plan Date Range, Timezone, Refresh Schedule & Data Freshness (Consolidated)

**What to do:**
- Confirm default date range and customize capability
- Capture the core **lookback window** for metric calculations (distinct from slider range)
- Capture timezone — CRITICAL for daily cutoffs, weekly windows, time-of-day filtering
- Understand acceptable data freshness and latency
- Plan refresh schedule (workflow path only)

**Key actions:**
- Ask for default date range via AskUserQuestion (last 7/30/90 days, QTD, YTD, custom?)
- Ask about dynamic date picker: "Can users adjust dates dynamically?"
- Ask: **"What lookback window should the core metrics use?"** — e.g., "RFM scores based on last 90 days" vs "pipeline coverage for current quarter only" — this is the CALCULATION window, not the slider range
- Ask: **"What timezone should all date calculations use?"** — ⚠️ **CRITICAL** — e.g., UTC, PST, JST. If source data is UTC and customer expects JST, every daily cutoff is off by 9 hours. Document timezone explicitly; note if source data timezone differs
- Ask: **"How fresh does the data need to be?"** (real-time? hourly? daily? multi-day?)
- Ask about acceptable delays: "What's the longest acceptable lag after events occur before data appears?"
- For WORKFLOW path only: Ask refresh schedule (daily, weekly, monthly, custom?)

**Output:**
- Default date range + date picker config
- Core lookback window (metric calculation window)
- Timezone (+ source data timezone if different) — ⚠️ **CRITICAL for accuracy**
- Acceptable data freshness SLA and acceptable lag
- Refresh schedule (workflow path only)

```
AskUserQuestion:
  questions:
    - header: "Default date range"
      question: "What should the default date range be when the dashboard first loads?"
      multiSelect: false
      options:
        - label: "Last 7 days"
          description: "Rolling 7-day window — good for weekly views"
        - label: "Last 30 days (Recommended)"
          description: "Rolling 30-day window — most common for operational dashboards"
        - label: "Last 90 days"
          description: "Rolling 90-day window — good for trend analysis"
        - label: "QTD (Quarter-to-date)"
          description: "From start of quarter to today"
        - label: "YTD (Year-to-date)"
          description: "From start of year to today"
        - label: "Custom period"
          description: "Fixed or custom date range"
        - label: "Not sure"
          description: "I'll recommend based on Stage B data freshness"

    - header: "Date picker"
      question: "Can users adjust the date range dynamically?"
      multiSelect: false
      options:
        - label: "Yes — dynamic picker (Recommended)"
          description: "Users can select any date range"
        - label: "No — fixed range only"
          description: "Dashboard always shows same window"
        - label: "Partially — preset ranges only"
          description: "Users pick from predefined ranges (e.g., last 7/30/90 days)"
        - label: "Other configuration"
          description: "Something different — I'll describe it"

    - header: "Core lookback window"
      question: "What lookback window should core metrics use? (separate from date slider)"
      multiSelect: true
      options:
        - label: "Last 7 days"
          description: "Rolling 7-day window — fast-moving metrics"
        - label: "Last 30 days"
          description: "Rolling 30-day window — monthly view"
        - label: "Last 90 days (Recommended)"
          description: "Rolling 90-day window — RFM, engagement, churn"
        - label: "Current quarter (QTD)"
          description: "Quarter-to-date — sales pipeline, quota"
        - label: "Current year (YTD)"
          description: "Year-to-date metrics"
        - label: "Custom per metric"
          description: "Different metrics use different windows"
        - label: "Not sure"
          description: "I'll infer from data patterns in Stage B"
```


```
AskUserQuestion:
  questions:
    - header: "Timezone"
      question: "What timezone should date calculations use? (CRITICAL — affects daily cutoffs)"
      multiSelect: false
      options:
        - label: "UTC"
          description: "Coordinated Universal Time"
        - label: "JST (Tokyo)"
          description: "Japan Standard Time, UTC+9"
        - label: "PST/PDT (US Pacific)"
          description: "Pacific Standard/Daylight Time"
        - label: "EST/EDT (US Eastern)"
          description: "Eastern Standard/Daylight Time"
        - label: "GMT/BST (London)"
          description: "Greenwich Mean Time"
        - label: "Other timezone"
          description: "Provide IANA name (e.g., America/New_York, Europe/Berlin)"

    - header: "Data freshness"
      question: "How fresh does the data need to be?"
      multiSelect: false
      options:
        - label: "Daily (Recommended)"
          description: "Updated nightly — suitable for most dashboards"
        - label: "Near real-time (hourly or sub-hourly)"
          description: "Frequent updates — workflow or live query"
        - label: "Weekly or less"
          description: "Batch reporting — executive summaries"
        - label: "Custom schedule"
          description: "I'll describe the exact refresh cadence needed"
        - label: "Not sure"
          description: "I'll determine based on data source in Stage B"
```

**VALIDATION NOTES:**
- **vs Step 1p Q1 (View Frequency):** If Q1=Daily+ but freshness=Weekly → misalignment. Clarify: "Need real-time or weekly OK?"
- **vs Step 1p Q2 (Trends Critical):** If Q2=Yes but historical depth < 12 months → misalignment. Clarify: "Extend history for meaningful trends?"

---

## Step 1g: Historical Data Depth

**What to do:**
- Determine how far back historical data should go
- Identify trend analysis needs
- Assess impact on data retention strategy

**Key actions:**
- Ask: "How far back should we keep historical data?" (30 days, 90 days, 1 year, multi-year, all?)
- Follow-up: "Why? What trends are important?" (YoY? MoM? Current snapshot?)
- Ask about archival: "Archive data older than [X]? Delete or keep?"

**Output:** Historical data retention period + rationale + archival strategy

**VALIDATION NOTE (Step 1-val-B):** This step relates to Q2 (Trends Critical) from Dashboard Complexity Scoring (Step 1p).
- If Q2 = "Yes, trends are critical" AND 1g < 12 months → ⚠️ Misalignment
- **Clarify:** "You said trends are critical but only have 3 months of history. We need at least 12 months for meaningful trend analysis. What's the available data depth?"

---

## Step 1h: Sharing, Access, Target Users & Downstream Consumers

**What to do:**
- Determine who should access this dashboard
- Capture target users' role, technical depth, communication style preference (shapes layout, label verbosity)
- Identify data sensitivity requirements
- Identify downstream consumers (who/what else uses this data)

**Key actions:**
- Ask: "Who should have access?" (personal, team, company, partners, public?)
- Ask: **"What is their role and how technical are they?"** — e.g., "VP of Sales — wants a 3-number executive summary" vs "Data analyst — wants sortable columns, exact values" — determines layout density, label detail, summary cards vs data tables
- Ask: **"How do they prefer to consume data?"** — narratives, tables, interactive filters
- Ask: **"Does this data contain revenue, PII, or competitive info that shouldn't be visible to all viewers?"** — determines masking, value ranges vs exact numbers. Flag for Step 1l if formal compliance applies
- Ask: **"Who or what else will consume this dashboard's data?"** — e.g., weekly reports, Slack digests, Foundry agents. Impacts output column naming, precision, Phase 4 planning
- Note: since HTML Client output is a single portable file, sharing is simply distributing that file (or hosting it) — no login gating or platform-specific ACLs apply

**Output:** Access audience + technical depth + communication style + data sensitivity flag + downstream consumers

**VALIDATION NOTE (Step 1-val-C):** This step relates to Q3 (Audience Scope) from Dashboard Complexity Scoring (Step 1p).
- If Q3 = "Just me" BUT 1h mentions internal team or customer stakeholders → ⚠️ Misalignment
- **Clarify:** "You said just you uses this, but requirements list broader access. Confirm: who actually uses this?"

---

## Step 1j: Alert/Threshold Notifications ⚠ OPTIONAL

**What to do:**
- Identify if alerts are needed when metrics cross thresholds
- Define alert conditions and escalation

**Key actions:**
- Ask: "Do you need alerts?" (no/manual/automated?)
- If yes: Define conditions: "What metric thresholds trigger alerts?" (e.g., Revenue < $100K, Error Rate > 5%)
- Ask about delivery: "Email, Slack, SMS? Who gets notified? Escalation chain?"

**Output:** Alert requirements (yes/no) + threshold definitions + notification delivery method + escalation rules (if applicable)

**⚠️ NOTE:** A static HTML Client dashboard cannot alert natively — alerting requires a companion workflow or Foundry agent (see Phase 4, Track B) to check thresholds and notify externally.

---

## Step 1o: Exclusion Rules & Data Quality ✅ Always Ask

**What to do:**
- Confirm if any rows should be excluded from metrics
- Document any data quality filters
- Flag for Stage B validation and clarification if needed

**Key actions:**
- Ask: "Should we exclude any types of data?" (cancelled orders, test data, refunds?)
- Ask about data quality: "Normalize? Handle nulls? Flag outliers?"
- Document exclusions in SQL WHERE clause format
- ⚠️ **NOTE:** These will be VALIDATED in Stage B. If Stage B finds patterns or suggests clarifications, will revisit and propose specific rules
- Confirm via AskUserQuestion

```
AskUserQuestion:
  header: "Data exclusions & quality"
  question: "Should we exclude or filter any data? (Select all that apply)"
  multiSelect: true
  options:
    - label: "Exclude cancelled/failed transactions"
      description: "Skip cancelled orders, failed events, or similar"
    - label: "Exclude test or internal data"
      description: "Skip test accounts, internal team activity, QA data"
    - label: "Exclude refunds or returns"
      description: "Exclude refunds, returns, or chargeback data"
    - label: "Normalize/standardize values"
      description: "Clean up data (e.g., uppercase, remove whitespace)"
    - label: "Handle nulls or missing data"
      description: "Replace nulls with defaults, exclude nulls, or flag them"
    - label: "Other exclusions"
      description: "I'll describe custom filtering rules"
    - label: "No exclusions"
      description: "Include all data as-is"
    - label: "Not sure — check Stage B"
      description: "I'll recommend exclusions based on data patterns"
```

**Output:** Exclusion rules (SQL format) + data quality handling rules + special cases + flagged for Stage B validation

---

## Optional Steps (1k-1n) ⚠

Ask ONLY if relevant — see `steps-1k-1n-optional.md` for details:

- **Step 1k: Mobile/Responsive Design** — Ask only if mobile use case likely.
- **Step 1l: Compliance & Governance** — Ask only if Step 1h flagged sensitive data OR compliance mentioned.
- **Step 1m: Data Source Complexity + Canonical ID** — Ask only if multi-database joins likely OR ID Unification involved.
- **Step 1n: Drill-Down Depth** — Ask only if dimensions suggest multi-level drill-down.

---

## Iterative Patterns: Rollback and Redo

Stage A is iterative — users can revisit any step before approving requirements at Finalization.

**Mid-Stage-A change:** User realizes a definition is wrong during Stage A
- Revisit the relevant step (e.g., Step 1b for metrics)
- Update the requirement and continue with remaining steps
- Final approval at Finalization

**Post-Stage-A change (before Stage B start):**
- **Minor change** (e.g., metric formula adjustment): Update requirement; proceed to Stage B with caveat; Stage B validates and reflects it in `state.md`
- **Major change** (e.g., new dimension, different refresh schedule): Revisit appropriate Stage A steps; revalidate quality checklist; re-approve with user before Stage B

**During Stage B (data discovery shows requirements can't be met):**
- Note the gap (e.g., "This dimension doesn't exist in your data")
- Propose alternatives or workarounds
- Update Stage A requirements; `state.md` reflects final validated requirements

**Phase 1 "complete"** = user explicitly approves all requirements at Finalization. `state.md` captures final validated requirements after Stage B.

---

## Stage A → Stage B Continuity (Not Sequential Handoff)

Stage A and Stage B are **designed to work together** within the same phase, not as strict sequential steps.

- **Stage A** gathers **business requirements** (what, why, who)
- **Stage B** validates against **actual data** (does it exist, how to calculate, what values)
- If Stage B finds conflicts → circle back to Stage A clarification → `state.md` reflects agreed resolution

### Examples of Stage A → Stage B Bridging

**Business requirement (Stage A):** "Track revenue by region"
- **Data validation (Stage B):** "Which column defines 'region'? Does it exist?"
- **If found:** Stage B confirms and proceeds
- **If not found:** Stage B escalates (e.g., "No region column; propose using state instead?")

**Business requirement (Stage A):** "Exclude cancelled orders"
- **Data validation (Stage B):** "What values in the 'status' column represent cancelled?"
- **If found:** Stage B captures the WHERE clause and proceeds
- **If not found:** Stage B escalates (e.g., "No status column; propose using created_date cutoff?")

**Key insight:** Don't worry if Stage A has unknowns — Stage B **discovers and validates** them. Stage A's job is to establish the business direction; Stage B's job is to prove it's possible with real data.

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
