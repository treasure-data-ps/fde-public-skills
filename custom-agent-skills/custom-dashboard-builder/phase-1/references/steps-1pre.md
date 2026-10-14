# Phase 1: Session Setup Questions

> **⛔ GUARDRAILS FIRST — before doing anything else in this file:**
> Read `../../references/guardrails-lite.md` now. Do not ask any question, run any command, or read any reference resource until guardrails-lite.md has been read in full.

Ask ALL 4 questions before collecting business requirements. These decisions gate the rest of Phase 1 and all downstream phases. **All 4 are mandatory — do not skip any.** If the user skips or ignores a question, re-ask before proceeding.

- Project name names the working directory `./<project-name>/` where everything this skill produces is written
- Data source type may eliminate Phase 2 (Workflow)
- Platform affects sharing guidance (rendering itself is always HTML Client)

Batch all 4 into a single AskUserQuestion call (max 4 questions per call):
- Setup-A (project name), Setup-B (business goal), Setup-C (target platform), Setup-D (data source type)

**⚠️ GATE: Do not proceed to Stage A (Steps 1a–1o) until this call is complete and all 4 answers are recorded in session.**

---

## Step Setup-A: Project Name

**Why first:** Everything this skill produces — `state.md`, workflow files, dashboard HTML, skill/agent artifacts — lives under `./<project-name>/`. Without it nothing can be written.

**AskUserQuestion:**

```
AskUserQuestion:
  header: "Project name"
  question: "What short, lowercase with hyphens name should I use for this project? (e.g., 'acme-campaign-perf', 'sales-pipeline')"
  multiSelect: false
  options:
    - label: "I'll provide a custom project name"
      description: "I'll type the exact name — becomes the working directory ./<project-name>/"
    - label: "Generate from dashboard purpose"
      description: "I'll suggest one once I know what the dashboard is for"
    - label: "Other — I'll type it now"
      description: "Provide a custom name as free text"
```

**Output:** `project_name` — the working directory for everything Phase 1-5 produce.

---

## Step Setup-B: Business Goal / Dashboard Purpose

**Why now:** A one-sentence purpose anchors every later decision (metrics, audience, layout).

**AskUserQuestion:**

```
AskUserQuestion:
  header: "Business goals"
  question: "What are the PRIMARY business goals for this dashboard? (Select all that apply)"
  multiSelect: true
  options:
    - label: "Track KPIs / Monitor performance"
      description: "Revenue, costs, usage, conversion rates, etc."
    - label: "Identify trends / Spot anomalies"
      description: "Year-over-year growth, seasonal patterns, outliers"
    - label: "Enable decisions / Support strategy"
      description: "Who to target, where to invest, what to optimize"
    - label: "Reduce time-to-insight"
      description: "Replace manual reports, answer questions faster"
    - label: "Enable forecasting / Plan ahead"
      description: "Predict future performance, budget allocation"
    - label: "Compare segments / Benchmark"
      description: "Sales region vs region, cohort A vs B, customer tier comparisons"
    - label: "Other business goal"
      description: "I'll describe something different"
```

**Output:** `business_goal` — stored in `state.md`.

---

## Step Setup-C: Target Platform

**Why it matters:** Platform affects sharing/access guidance. Rendering itself is always HTML Client (a single portable `dashboard.html`) in this lite skill — no engine decision is needed.

**AskUserQuestion:**

```
AskUserQuestion:
  header: "Target platform(s)"
  question: "Where will this dashboard be used? (Select all that apply)"
  multiSelect: true
  options:
    - label: "Treasure Work (internal)"
      description: "Open the HTML file locally or share it as a file"
    - label: "Treasure AI Studio"
      description: "Portable single-file HTML — easy to email or host"
    - label: "Externally hosted"
      description: "Deployed to a web server or static host"
    - label: "Other platform"
      description: "I'll describe where this will be used"
```

**Output:** `target_platform` — stored in `state.md`. Informative only; does not change the rendering engine.

---

## Step Setup-D: Data Source Type

**Why it matters:** Understanding the data source type (raw/transactional with high volumes and complex joins vs. pre-aggregated with low-volume pre-calculated KPIs) determines whether Phase 2 (Workflow) is necessary.

**Key distinction:**
- **Raw / Transactional:** High data volumes, complex table joins. A scheduled Phase 2 workflow is recommended for aggregation and performance.
- **Pre-aggregated:** Low volume data, already pre-calculated KPIs, minimal joins. Phase 2 can be skipped entirely — query source tables directly in Phase 3.

**AskUserQuestion:**

```
AskUserQuestion:
  header: "Data source type"
  question: "What is the nature of the data source?"
  multiSelect: false
  options:
    - label: "Raw/Transactional (high volume, complex joins)"
      description: "Event-level data with many joins and high volumes. Workflow recommended."
    - label: "Pre-aggregated (low volume, pre-calc KPIs)"
      description: "RFM output, Parent Segment, SINK tables. Minimal joins. Phase 2 not needed."
    - label: "Mix of raw and aggregated"
      description: "Both types. Phase 2 decision per metric during data discovery."
    - label: "Not sure — check during data discovery"
      description: "I'll recommend a path based on data structure"
    - label: "Other data source type"
      description: "Something different — I'll describe it"
```

**Downstream rules:**

| Answer | Phase 2 flag | Recommended Path | Notes |
|--------|-------------|------------------|-------|
| Raw / Transactional | `skip_workflow = false` | Use Dashboard Complexity Score normally | Complex joins + volume → Phase 2 usually beneficial |
| Pre-aggregated | `skip_workflow = true` | Skip Phase 2 regardless of score | Data already optimized — no workflow needed |
| Mix | `skip_workflow = partial` | Decide per-metric during data discovery | Some metrics may skip, others may need Phase 2 |
| Not sure | `skip_workflow = tbd` | Resolve during data discovery | Determined by actual table structure |

**Output:** `data_source_type` + `skip_workflow` flag — stored in `state.md`.

---

## Step Setup-E: Reference Resources & Prior Art

**Why it matters:** Sisense/Treasure Insights customers typically have multiple resources available: the `.dash` export (UI structure), the datamodel (schema/metrics/joins), and optionally an existing workflow (data refresh). Collect **all of them** — we'll combine them to prefill Stage A/B intelligently.

This is a separate `AskUserQuestion` call — ask it immediately after the Setup-A–D batch resolves, before starting Stage A core requirements. **This is a MULTI-SELECT question** — users may have all three.

**AskUserQuestion:**

```
AskUserQuestion:
  header: "Reference resources"
  question: "What resources do you have? (Select all that apply)"
  multiSelect: true
  options:
    - label: "Sisense/Treasure Insights export file (.dash)"
      description: "Upload the .dash file — we'll extract UI structure, tables, metrics, filters."
    - label: "Treasure Insights datamodel name or OID"
      description: "Provide the model name/OID — we'll fetch the schema via API."
    - label: "Existing Treasure Data workflow"
      description: "Provide the workflow project/name — we'll validate and reuse for Phase 2 if needed."
    - label: "Screenshots or mockups"
      description: "Upload images or wireframes — I'll reference them during Stage A questions."
    - label: "SQL queries or specs"
      description: "Paste SQL, JSON, or written specifications — I'll extract requirements."
    - label: "Other resource type"
      description: "Something different — I'll describe what you have"
    - label: "None — starting fresh"
      description: "No existing resources — proceed to Stage A requirements."
```

**Processing multi-select results:**

| User selects | Action |
|---|---|
| `.dash` only | Jump to "`.dash` / Sisense Special Case" (Step 1a–7 below) |
| datamodel only | Jump to "Treasure Insights API Special Case" (Step 2a–7 below) |
| workflow only | Capture workflow name; incorporate in Phase 2 planning; proceed to normal Stage A |
| `.dash` + datamodel | **Combined path (new):** Use `.dash` for UI structure + datamodel for confirmed schema relationships; prefill both Stage A/B with cross-validation |
| `.dash` + workflow | Use `.dash` for structure; incorporate existing workflow into Phase 2 strategy |
| datamodel + workflow | Use datamodel for schema; incorporate existing workflow into Phase 2 strategy |
| All three (`.dash` + datamodel + workflow) | **Combined path (new):** Use all three sources to maximize prefilled context; validate consistency across sources |
| Other resource(s) ± above | Include as supporting context in Stage A/B questions; only "fast-track" if `.dash` or datamodel selected alone or together |
| None | Proceed directly to Stage A (Steps 1a–1o in `./steps-1a-1o.md`) |

**Output:** `reference_resources_provided` (list of selected types) + `has_dash` (bool) + `has_datamodel` (bool) + `has_workflow` (bool) + `resource_type` (enum: `dash_only` / `api_only` / `combined` / `other` / `none`) — stored in `state.md`.

**NOTE:** Dashboard structure questionnaire is now part of **Step 1c+1d** in the main Stage A flow (`./steps-1a-1o.md`). It captures tabs, visualizations, filters, drill-down, and performance needs upfront, before detailed metric/dimension discovery.

---

### Combined Path (`.dash` + datamodel or all three)

**Trigger:** User selects both `.dash` file and datamodel name/OID (with or without workflow).

**Why this path:** Using both sources provides maximum context:
- `.dash` file shows the **current UI structure** (tabs, widgets, layout, filters as they appear to users)
- Datamodel provides the **canonical schema** (confirmed metrics/dimensions, official join relationships)
- Workflow (if present) shows the **data refresh strategy** (schedule, transformation logic, incremental patterns)

Combining them prevents stale export files from mismatching the live datamodel, and ensures we understand both what users *see* (`.dash` layout) and what data actually *supports* it (datamodel schema).

**Implementation:**
1. Fetch the datamodel schema via API (Step 2 of "Treasure Insights API Special Case" below)
2. Run the `.dash` converter to extract UI structure (Step 1 of "`.dash` / Sisense Special Case" below)
3. **Cross-validate:** Check that tables/joins in the `.dash` file exist in the datamodel; flag mismatches
4. **Prefill Stage A/B from both:**
   - Metrics ← `.dash` widgets labeled with their measure names, validated against datamodel `aggregations` field
   - Dimensions ← datamodel columns without aggregations, filtered to only those referenced in `.dash` widgets
   - Joins ← datamodel `relations[]` cross-checked against `.dash` converter's inferred joins
5. Present a unified audit to the user (one row per widget, annotated with "source: .dash", "validated in: datamodel", etc.)
6. Proceed with migration goal question and Phase routing as if the primary resource is `.dash` (since that's what the user sees and cares about most — the datamodel is just the validator)

---

## `.dash` / Sisense / Treasure Insights Special Case — STOP and Follow This Path

**Trigger:** The user selected a `.dash` file in Setup-E (alone, with datamodel, with workflow, or with both).

**Why this path exists:** A Sisense/Treasure Insights export already encodes the dashboard's titles, tabs, widgets, chart types, JAQL queries (→ SQL), and filters. Re-asking every Stage A/B question from scratch would ignore information already sitting in the file. This path converts the file immediately, uses it to **prefill** Stage A requirements and Stage B data discovery, and only asks the handful of questions the file can't answer itself (output database, existing workflow, datamodel relationships, migration goal).

**Special note:** If the user also selected the datamodel in Setup-E, follow the "Combined Path" guidance in Step 2b below instead of running Steps 1–7 independently.

**Lite-specific notes:** No Confluence, no git branching — everything below writes to `state.md` only. No live Sisense datamodel API fetch — the datamodel question in Step 3 is answered conversationally (paste JSON or describe relationships in text), not via a `curl` call to a TD reporting API. The converter script lives locally at `../../references/dash_to_html.py` (repo-root `references/`) — there is no external repo dependency.

### Step 1: Run the Converter Immediately

```bash
python3 ../../references/dash_to_html.py "<path-to-dash-file>" --out /tmp/dash-convert --db __DB__
```

This produces `render.js`, `template.html`, and `widget_audit.json` in `/tmp/dash-convert/`. `__DB__` is a placeholder — the real database is confirmed in Step 3 and substituted in Step 4.

### Step 2: Show the User What Was Found

Present the converter's console summary plus a short readout, e.g.:

```
📄 Sisense/Treasure Insights Export Detected

Dashboard: <title>
Tabs: <n>
Total widgets: <n>
Widgets resolved to SQL: <resolved>/<total>
Unique tables referenced: <table_1>, <table_2>, ...
Global filter columns: <col_1>, <col_2>, ... (or "none")

⚠ Warnings (<n>):
  - <warning 1>
  - <warning 2>
```

### Step 3: Ask the Sisense-Specific Follow-Up Questions

These 4 questions cover exactly what the `.dash` file cannot answer on its own — batch into one `AskUserQuestion` call:

```
AskUserQuestion:
  questions:
    - header: "Source database"
      question: "Which Treasure Data database do the tables referenced in this dashboard (<table_1>, <table_2>, ...) actually live in?"
      options:
        - label: "I know the database name"
          description: "I'll type the exact database — used to replace the __DB__ placeholder in every generated query"
        - label: "Not sure — help me find it"
          description: "Run `tdx databases` and `tdx describe` to locate tables matching these names"

    - header: "Existing workflow"
      question: "Is there an existing TD workflow that creates or refreshes the tables this dashboard queries?"
      options:
        - label: "Yes — reuse it"
          description: "I'll provide the workflow name/project — Phase 2 becomes validation-only, no new workflow created"
        - label: "No — need one created"
          description: "No workflow exists yet — Phase 2 will create one if the migration goal needs scheduled refresh"
        - label: "Not sure"
          description: "I'll check during Stage B data discovery"

    - header: "Datamodel relationships"
      question: "Does this dashboard rely on a datamodel with joins/relationships between multiple tables?"
      options:
        - label: "Yes — I'll paste the datamodel JSON/spec"
          description: "Paste the datamodel definition (datasets + relations); I'll extract join keys from it"
        - label: "Yes — I'll describe the relationships"
          description: "Tell me in plain text which tables join on which columns"
        - label: "No — single table or infer from JAQL only"
          description: "Each widget's SQL already resolves from its own JAQL; no cross-table joins needed"

    - header: "Migration goal"
      question: "What's the goal for this migration?"
      options:
        - label: "Replicate — match the original exactly"
          description: "Fastest path: derive Stage A/B directly from the .dash file, minimal new questions, build to match"
        - label: "Replicate + improve"
          description: "Match the original as a baseline, then ask a few Stage A questions to add/fix metrics or filters"
        - label: "Modernize"
          description: "Use the .dash as a starting point only — run closer to the normal Stage A/B flow"
```

### Step 3b: Capture Datamodel Relationships (Conversational — No Live API Call)

**This is a text-based capture step, not a live fetch.** Do not call any Sisense/TD reporting API here — that mechanism is out of scope for this lite skill.

- **If the user pastes JSON/spec:** parse it directly for dataset/table names and join columns. Tag extracted relationships `[FROM USER-PROVIDED DATAMODEL]` in `state.md`.
- **If the user describes relationships in text:** record them as stated. Tag `[FROM USER DESCRIPTION]`.
- **If "infer from JAQL only":** no cross-table joins are assumed; each widget's SQL stands alone as resolved by the converter. Tag `[FROM JAQL ONLY — NO DATAMODEL]`.

Any relationship found here that the converter's auto-join heuristic didn't already apply should be flagged for a manual SQL fix before Step 4's re-run (the converter's own warnings — e.g. "no JOIN was generated" — often correspond to a missing datamodel relationship).

### Step 4: Re-Run the Converter With the Real Database

```bash
python3 ../../references/dash_to_html.py "<path-to-dash-file>" --out /tmp/dash-convert --db <confirmed-database>
```

Open `/tmp/dash-convert/template.html` (e.g. via `mcp__work__open_file`) so the user can see the structure before any data is queried.

### Step 5: Prefill Stage A Requirements + Stage B Data Discovery

Instead of asking Stage A/B questions from scratch, derive them from the converter output and mark each as `[Derived from .dash]` in `state.md`:

- **Metrics** ← each widget's `measure_cols` (aggregation + label)
- **Dimensions** ← each widget's `dim_col` / `break_by`
- **Filters** ← `global_filters` + per-widget filter conditions in `sql`
- **Tables** ← `widget_audit.json` unique table list — this **is** the Stage B "confirm tables" step; no separate `tdx describe` walkthrough needed for tables already found
- **Tabs / layout** ← the `.dash` file's tab structure

Still ask (the `.dash` file can't answer these): timezone, sharing/access, alerts — reuse `./steps-1a-1o.md` templates for just those gaps, batched into one call. Skip every other Stage A/B question already answered by the derivation above.

### Step 6: Phase Routing (Lite Numbering)

```
IF migration_goal == "Replicate":
  → Fast-track: skip live Stage A/B interviews entirely (derived from .dash + Step 3/3b answers)
  → Phase 2 (Workflow): validation-only if an existing workflow was confirmed in Step 3
      → If existing workflow confirmed: reuse as-is, do NOT create a new one — validate its SINK output matches, then skip straight to Phase 3
      → If no existing workflow AND source data is large/raw: create a minimal workflow (normal Phase 2 flow) before Phase 3
      → If source is already small/pre-aggregated: skip Phase 2 entirely
  → Phase 3 (Build Dashboard): starts directly from `/tmp/dash-convert/template.html` + `render.js` — do not rebuild from scratch

IF migration_goal == "Replicate + improve" OR "Modernize":
  → Run closer to the normal Stage A/B flow, but pre-filled with the .dash-derived answers above as defaults
  → User confirms/edits each pre-filled value rather than answering from a blank slate
  → Dashboard Complexity Scoring (1p) still runs normally to decide Phase 2 vs Phase 3
  → Phase 3 may still start from the converter output as a base, then layer on requested changes
```

### Step 7: Mandatory Before/After Validation Gate

**This gate is required for every `.dash` migration, regardless of migration goal — it cannot be skipped.**

Present `widget_audit.json`, grouped by tab, one row per widget:

```
📋 Widget Audit — <project_name>

Tab: <tab_name>
  • <widget title> — Source: <table> | Metric: <measure> | Filter scope: <applies_global_filters> | Notes: <warnings, or "none">
  • ...
```

```
AskUserQuestion:
  header: "Widget audit"
  question: "Review the widget-by-widget breakdown above against the original dashboard. Does it match?"
  options:
    - label: "Approve as-is"
      description: "Every widget's source table, metric, and filter scope look correct — proceed"
    - label: "Approve with noted changes"
      description: "Mostly correct — I'll list specific widgets/columns to fix before or after rendering"
    - label: "Needs rework"
      description: "Significant mismatches — return to Step 3b/5 to fix table/join/metric mapping"
```

**Comments alone, without an explicit approve, do not clear this gate.** Run this check twice: once here (before rendering, against `widget_audit.json` alone) and once again in Phase 3 after `dashboard.html` is rendered (against the live rendered output).

### Step 8: Write state.md and Continue

Write the Session Setup block (Setup-A–E) plus the `.dash`-derived Requirements and Data Discovery blocks (tagged `[Derived from .dash]`) to `state.md` in one pass, then proceed per Step 6's routing — never auto-continue past Step 7's gate without an explicit approval.

---

## Treasure Insights API Special Case — STOP and Follow This Path

**Trigger:** The user provides a **Treasure Insights datamodel name or OID** during Setup-E instead of a `.dash` file.

**Why this path exists:** A Treasure Insights datamodel already encodes the schema (tables, columns, metrics, dimensions, and join relationships) in the Reporting API. Instead of asking every Stage A/B question from scratch, we fetch the live schema via API and **prefill** Stage A requirements and Stage B data discovery automatically. This is faster and avoids stale export files.

**Lite-specific notes:** Uses the Reporting API (documented at `../references/treasure-insights-api-integration.md`) to fetch the schema. The helper script lives at `../../references/insights-api-helper.py` (repo-root `references/`) — pure Python, no external dependencies beyond `requests`.

### Step 1: Fetch the Datamodel Schema

Ask the user: "Is this a datamodel name (e.g., 'sales_model') or a datamodel OID (e.g., 'datamodel_123')?"

Once provided, run the helper script:

```bash
python3 ../../references/insights-api-helper.py "<datamodel_name_or_oid>" --region <us|jp|eu|kr>
```

This outputs:
- A markdown-formatted extraction (metrics, dimensions, relations)
- A JSON file: `insights_datamodel_<datamodel_id>.json`

**Errors to handle:**
- `404 Not Found` → datamodel name/OID incorrect. Suggest: run `tdx` or list datamodels via API. See `../references/treasure-insights-api-integration.md` for "List All Datamodels" endpoint.
- `401 Unauthorized` → API key expired. Ask user to re-authenticate: `tdx auth setup`

### Step 2: Show the User What Was Found

Present the markdown extraction, e.g.:

```
📊 Treasure Insights Data Model Extraction

Model Name: sales_model
Model ID: datamodel_123

## Discovered Metrics
- Total Amount (SUM) (analytics.orders.total_amount)
- Average Amount (analytics.orders.total_amount)
- Order Count (analytics.orders.order_id)

## Discovered Dimensions
- Region (analytics.orders.region) — string
- Order Date (analytics.orders.order_date) — date
- Customer Name (analytics.customers.customer_name) — string

## Discovered Join Relationships
- orders.customer_id → customers.customer_id
```

### Step 3: Ask the API-Specific Follow-Up Questions

These 2 questions cover what the API schema cannot answer — batch into one `AskUserQuestion` call:

```
AskUserQuestion:
  questions:
    - header: "Migration goal"
      question: "What's your goal with this datamodel?"
      options:
        - label: "Replicate existing dashboard"
          description: "Use discovered schema as-is for Phase 3 rendering"
        - label: "Replicate + improve"
          description: "Use schema as base; confirm/edit metrics and dimensions"
        - label: "Modernize"
          description: "Use schema as reference; redesign dashboard from scratch with selected metrics"

    - header: "Join confirmation"
      question: "The datamodel has these join relationships: [list from Step 2]. Are they correct?"
      options:
        - label: "Yes — use as-is"
          description: "Relationships are correct — use for Phase 2/3"
        - label: "Yes, but I want to describe additional relationships"
          description: "Existing joins are correct; I'll add more"
        - label: "No — I'll describe the correct joins"
          description: "These don't match my data structure — I'll provide the correct ones"
```

### Step 4: Prefill Stage A Requirements + Stage B Data Discovery

Derive from the API response:

- **Metrics** ← each extracted column with `aggregations` field
- **Dimensions** ← each extracted column without aggregations (especially type=string or date)
- **Tables** ← each dataset.table in the response — this **is** the Stage B "confirm tables" step
- **Joins** ← the `relations` array from the API response

Still ask (the API can't answer these): timezone, sharing/access, alerts, business goal (unless provided in Setup-B) — reuse `./steps-1a-1o.md` templates for just those gaps, batched into one call. Skip every other Stage A/B question already answered by the derivation above.

### Step 5: Mandatory Metric/Dimension Confirmation Gate

**This gate is required for every Treasure Insights API migration — it cannot be skipped.**

Present the discovered metrics and dimensions in a table:

```
📋 Schema Extraction — <project_name>

Metrics (Measures):
  • Total Amount (SUM) — Source: orders.total_amount | Aggregation: sum
  • Average Amount (AVG) — Source: orders.total_amount | Aggregation: avg

Dimensions (Attributes):
  • Region — Source: orders.region | Type: string | Cardinality: <n>
  • Order Date — Source: orders.order_date | Type: date
  • Customer Name — Source: customers.customer_name | Type: string | Cardinality: <n>

Joins:
  • orders.customer_id → customers.customer_id
```

```
AskUserQuestion:
  header: "Schema confirmation"
  question: "Review the extracted metrics, dimensions, and joins above. Does this match your data structure?"
  options:
    - label: "Approve as-is"
      description: "All metrics, dimensions, and joins are correct — proceed"
    - label: "Approve with edits"
      description: "Mostly correct — I'll list specific columns to remove/rename"
    - label: "Needs rework"
      description: "Significant mismatches — I'll describe the correct schema"
```

**Comments alone, without an explicit approve, do not clear this gate.**

### Step 6: Phase Routing

```
IF migration_goal == "Replicate":
  → Fast-track: skip live Stage A/B interviews entirely (all prefilled from API)
  → Phase 2 (Workflow): per Dashboard Complexity Score normally
  → Phase 3 (Build Dashboard): starts fresh (no pre-rendered template)

IF migration_goal == "Replicate + improve" OR "Modernize":
  → Run Stage A/B with user edits to prefilled values
  → Dashboard Complexity Scoring (1p) still runs normally
  → Phase 3: builds fresh dashboard with approved metrics/dimensions
```

### Step 7: Write state.md and Continue

Write Session Setup (Setup-A–E) plus the API-derived Requirements and Data Discovery blocks (tagged `[Derived from Treasure Insights API]`) to `state.md`, then proceed per Step 6's routing.

---

## Combined Resources Path — `.dash` + Datamodel ± Workflow

**Trigger:** User selected multiple resources in Setup-E (`.dash` + datamodel, or `.dash` + datamodel + workflow, or any combination).

**Why this path:** Combining resources maximizes prefilling accuracy and prevents inconsistencies:
- `.dash` file tells us **what users see** (UI structure, layout, current filters)
- Datamodel tells us **what data should be used** (canonical schema, confirmed joins, official metrics)
- Workflow (if present) tells us **how data flows** (refresh schedule, incremental logic, SINK table location)

Running these together:
1. Validates that `.dash` widgets reference tables that exist in the datamodel
2. Cross-checks joins inferred by the `.dash` converter against official datamodel relationships
3. Incorporates workflow metadata (if present) into Phase 2 planning

### Combined Path Execution

**Step A: Fetch All Resources Simultaneously**

```bash
# Fetch datamodel schema
python3 ../../references/insights-api-helper.py "<datamodel_name_or_oid>" --region <us|jp|eu|kr>

# Convert .dash file
python3 ../../references/dash_to_html.py "<path-to-dash-file>" --out /tmp/dash-convert --db __DB__
```

**Step B: Cross-Validate**

Compare the two extractions:

| Check | .dash source | Datamodel source | Action if mismatch |
|---|---|---|---|
| Tables referenced | `widget_audit.json` unique table list | datamodel `datasets[].table` | Flag missing tables; ask user if `.dash` is stale |
| Metrics (measures) | widget `measure_cols` | datamodel columns with `aggregations` | Validate each widget's metric exists in datamodel |
| Dimensions | widget `dim_col` / `break_by` | datamodel columns without aggregations | Validate each widget's dimension exists in datamodel |
| Joins | converter-inferred joins from JAQL | datamodel `relations[]` | Ensure `.dash` joins match official datamodel relationships |

**Report to user:**

```
🔄 Cross-Validation Results

Tables: ✓ All <n> tables in .dash are present in datamodel
Metrics: ✓ <n> widget metrics matched; <m> mismatches flagged
Dimensions: ✓ <n> widget dimensions matched; <m> mismatches flagged
Joins: ✓ <n> joins inferred from .dash; <m> additional joins from datamodel not yet used

Recommended action: [proceed as-is / resolve <m> mismatches before continuing]
```

**Step C: Prefill Stage A/B From Both Sources**

Combine the prefilled values:

- **Metrics** ← `.dash` widget metrics, labeled with widget name, validated against datamodel
- **Dimensions** ← `.dash` widget dimensions + datamodel columns (user can add more in Stage A)
- **Filters** ← `.dash` global filters + per-widget conditions
- **Tables** ← `.dash` converter's table list (already confirmed Stage B)
- **Joins** ← datamodel official joins, cross-checked against `.dash` converter's inferred joins

**Step D: Ask Only the Unanswerable Questions**

Skip everything already answered by the two sources. Ask only:
- Timezone (`.dash` doesn't encode this)
- Sharing/access (needs user intent, not in datamodel)
- Alerts/thresholds (not in `.dash` or datamodel)
- Business goal (if not captured in Setup-B)
- **Migration goal** (Replicate / Replicate+improve / Modernize)
- **Workflow reuse** (if user selected workflow in Setup-E): "Should I reuse the existing workflow `<name>` or create a new one?"

**Step E: Unified Audit Before Proceeding**

Present a single audit table combining `.dash` structure + datamodel validation:

```
📋 Combined Audit — <project_name>

Tab: <tab_name>
  • <widget title>
    - Source: <table> (✓ in datamodel)
    - Metric: <measure> (✓ validated in datamodel)
    - Dimensions: <dim1>, <dim2> (✓ validated)
    - Joins: <join info from datamodel>
    - Notes: <warnings or "none">
```

Ask user: "Does this combined view (UI structure from `.dash`, schema from datamodel) look correct?"

**Step F: Phase Routing**

```
IF workflow selected + existing workflow confirmed:
  → Phase 2: validate workflow's SINK output; do NOT create new workflow
  → Then Phase 3

IF workflow selected + no existing workflow:
  → Phase 2: create new workflow per Dashboard Complexity Score
  → Then Phase 3

IF no workflow selected:
  → Use migration goal + Dashboard Complexity Score to decide Phase 2 vs skip
```

**Step G: Write state.md**

Tag all prefilled values with their sources:

```markdown
## Phase 1 — Data Discovery
- Database.Table(s): <...> [Derived from .dash file]
- Metrics: <...> [Extracted from .dash; validated in datamodel]
- Dimensions: <...> [Extracted from .dash; validated in datamodel]
- Joins: <...> [From official datamodel; cross-checked with .dash converter]
- Workflow: <workflow_name> [Reuse existing] or [Create new] [If workflow selected in Setup-E]
- Cross-validation result: [✓ Pass / ⚠ Warnings logged]
```

---

## Combined AskUserQuestion Call

```
AskUserQuestion:
  questions:
    - header: "Project name"
      question: "What short, lowercase with hyphens name should I use for this project?"
      options: [see Setup-A above]

    - header: "Dashboard purpose"
      question: "In one sentence, what decision or question should this dashboard help answer?"
      options: [see Setup-B above]

    - header: "Target platform"
      question: "Where will this dashboard be used?"
      options: [see Setup-C above]

    - header: "Data source type"
      question: "What is the nature of your data source?"
      options: [see Setup-D above]
```

---

**⚠️ GATE: Do not proceed to Steps 1a–1o until all of the following are confirmed:**
- `project_name` recorded
- `business_goal` recorded
- `target_platform` recorded
- `data_source_type` recorded
- `skip_workflow` flag set
- **Setup-E (reference resources) asked** — see below
- Ready to proceed to Stage A (or to the `.dash` Special Case, if triggered)

**Then run Setup-E (Reference Resources) as its own `AskUserQuestion` call — see "Step Setup-E" above.** If the resource provided is a `.dash`/Sisense/Treasure Insights export, jump to the "`.dash` / Sisense Special Case" section instead of Stage A.

---

## Output: What Gets Written to `state.md`

After the Setup-A–D call completes, this becomes the first block of `./<project-name>/state.md`:

```markdown
## Phase 1 — Session Setup

- **Project Name:** <project-name>
- **Business Goal:** <one sentence>
- **Target Platform:** <Treasure Work | Treasure AI Studio | Not sure>
- **Data Source Type:** <Raw/Transactional | Pre-aggregated | Mix | TBD>
- **Skip Workflow Flag:** <true | false | partial | tbd>
- **Reference Resource Provided:** <yes | no>
- **Resource Type:** <.dash | treasure-insights-api | other | none>
```

Then proceed to Setup-E (if not already asked), then Stage A (Steps 1a–1o) — or the `.dash` Special Case if triggered.

---

## Quality Checklist: End of Session Setup

Before moving to Stage A (business requirements) or the `.dash` Special Case, verify every item below. **Do not proceed if any item is blank or unanswered.**

- ✅ **`guardrails-lite.md` read** — (`../../references/guardrails-lite.md`) — must be first
- ✅ `project_name` recorded
- ✅ `business_goal` recorded
- ✅ `target_platform` recorded
- ✅ `data_source_type` recorded
- ✅ `skip_workflow` flag set — one of: true | false | partial | tbd
- ✅ Setup-E asked — `reference_resource_provided` + `resource_type` recorded
- ✅ If `resource_type = .dash` → routed to the `.dash` Special Case, not Stage A
- ✅ If `resource_type = treasure-insights-api` → routed to the "Treasure Insights API Special Case", not Stage A
- ✅ Ready to proceed to Stage A (or one of the Special Cases)

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
