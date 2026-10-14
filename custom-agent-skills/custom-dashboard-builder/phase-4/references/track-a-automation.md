# Phase 4: Track A — Extract Reusable Skill (4a-0 to 4a-vii)

**Goal:** Extract the approved dashboard as a reusable, parameterized skill so future builds against a different database take ~10-30 minutes instead of 2-3 hours.

**When to run Track A:**
- The dashboard will be rebuilt for other databases/customers with the same shape
- The user wants to standardize this dashboard pattern for reuse
- Faster turnaround on dashboard variations is valuable

---

## Step 4a-0: Assemble Knowledge Package (10 min)

**What to do:**
Before building the render skill, assemble the knowledge files that let the skill — and anyone who receives it — answer deeper questions: metric definitions, data lineage, and SQL patterns. These travel alongside the skill and are never embedded inside the render `SKILL.md` itself.

**Why this matters:**
The render skill answers "show me the dashboard." The knowledge package answers everything beyond that.

**Knowledge package location (working directory):** `./<project-name>/skills/knowledge/`

*(This will be deployed to `~/.claude/skills/<skill-name>/knowledge/` in Step 4a-vi)*

```
./<project-name>/skills/knowledge/
├── business_context.md        ← company overview, goals, personas, confirmed metrics
├── data_dictionary.md         ← table schemas + column definitions + business meaning
├── sql_templates.md           ← parameterized queries with inline explanations
└── metrics_catalog.md         ← every dashboard metric: formula, source, exclusions
```

**How to assemble each file:**

| File | Source | Action |
|------|--------|--------|
| `business_context.md` | `state.md` (Phase 1) | Copy the business goal + confirmed metrics sections verbatim |
| `data_dictionary.md` | Phase 1 Stage B schema discovery + `tdx describe` output | Run `tdx describe <db>.<table>` for each table used, add business meaning per column |
| `sql_templates.md` | Phase 3 queries + Phase 2 workflow SQL (if run) | Extract each Phase 3 query; if Phase 2 ran, also extract the workflow SQL from the `.dig` files (see below) |
| `metrics_catalog.md` | `state.md` metrics list + Phase 3 validation | One row per dashboard metric: formula, SQL column, source table, exclusion rules, confirmed sample value |

**Extracting workflow SQL into `sql_templates.md` (only if Phase 2 ran):**

```bash
# Find the SQL in the workflow folder
find ./<project-name>/workflows -name "*.dig" | sort
# The SQL tasks are inline in .dig files, or referenced as separate .sql files in queries/
```

For each SQL task in the workflow, add a section to `sql_templates.md`:

```markdown
## [Q-N]: [Descriptive name]

**Source:** `./<project-name>/workflows/queries/<filename>.sql` (or inline in the `.dig` file)
**Builds:** `{SINK_DB}.<sink_table_name>`
**Runs against:** `{SOURCE_DB}.<source_table_name>`
**What this answers:** [Plain English]

​```sql
SELECT ...
FROM {SOURCE_DB}.orders
WHERE td_time_range(time, '{START_DATE}', '{END_DATE}', 'UTC')
GROUP BY ...
​```
```

Do this for every SQL task in the workflow, so no one needs to open the workflow files to understand the pipeline.

**Minimum viable package:** `business_context.md` + `data_dictionary.md` + `sql_templates.md`. Add `metrics_catalog.md` if the dashboard has more than a couple of KPIs worth documenting separately.

**Copy templates first — do not write knowledge files from scratch:**

```bash
mkdir -p ./<project-name>/skills/knowledge

cp references/templates/knowledge-base-business-context-template.md \
   ./<project-name>/skills/knowledge/business_context.md

cp references/templates/knowledge-base-data-dictionary-template.md \
   ./<project-name>/skills/knowledge/data_dictionary.md

cp references/templates/knowledge-base-sql-templates-template.md \
   ./<project-name>/skills/knowledge/sql_templates.md

cp references/templates/knowledge-base-metrics-dictionary-template.md \
   ./<project-name>/skills/knowledge/metrics_catalog.md
```

Then fill every `[PLACEHOLDER]` field. Writing from scratch risks inconsistency with the template format and takes longer.

---

## Step 4a-i: Extract Dashboard Skill Definition (10 min)

**Assembly workflow:** 
- Steps 4a-0 through 4a-v: Work in `./<project-name>/skills/` (project working directory)
- Step 4a-vi: Copy to `~/.claude/skills/<skill-name>/` (final deployed location for cross-session use)

**What to do:**
- Create a `skills/` folder inside `./<project-name>/` (working directory)
- `skills/SKILL.md` is the entry point — describes the execution flow and points to `knowledge/` for deeper questions
- The skill is HTML Client only — no engine choice, no per-engine sub-folders

**PRE-CONDITION — template must already exist from Phase 3 (CRITICAL):**

If either file below is missing, go back to Phase 3 and confirm the dashboard was approved before proceeding. The skill cannot execute without both.

| File | Created in | Copy from | Copy to |
|---|---|---|---|
| `dashboard.html` | Phase 3 | `./<project-name>/dashboards/dashboard.html` | `./<project-name>/skills/dashboard.html` |
| `dashboard-template.html` | Phase 3 | `./<project-name>/dashboards/dashboard-template.html` | `./<project-name>/skills/dashboard-template.html` |
| `generate-data.js` | Phase 3 | `./<project-name>/dashboards/generate-data.js` | `./<project-name>/skills/generate-data.js` |

```bash
mkdir -p ./<project-name>/skills
cp ./<project-name>/dashboards/dashboard.html           ./<project-name>/skills/dashboard.html
cp ./<project-name>/dashboards/dashboard-template.html  ./<project-name>/skills/dashboard-template.html
cp ./<project-name>/dashboards/generate-data.js        ./<project-name>/skills/generate-data.js
```

**`dashboard.html`, `dashboard-template.html`, and `generate-data.js` are the static artifacts** — they never change between runs. Only the env vars passed to `generate-data.js` (`SOURCE_DB`/`SINK_DB`) change per database. Never recreate them in Phase 4; always copy from the approved Phase 3 output. The template file is required because `generate-data.js` references it via `__dirname` when rebuilding the dashboard.

The skill's execution flow must:
1. Check if SINK tables exist → fall back to source tables if Phase 2 was skipped
2. Run `node generate-data.js` (with `SOURCE_DB`/`SINK_DB` env vars pointing at the target database) — this inlines data into `dashboard.html`
3. Open `dashboard.html` in a browser (`npx serve .` or `preview_document`)

**Create skill definition:**

```yaml
---
name: [business-friendly-name]-dashboard
description: |
  Reusable [type] dashboard. Builds similar dashboards in 10-30 minutes instead of 2-3 hours.
  Users can ask natural-language questions like "Which region has the highest growth?"
  
  Inputs: database names, optional date range
  Outputs: interactive HTML dashboard (single portable file, works offline)

---

# [Type] Dashboard Skill

## Inputs
- **SOURCE_DB / SINK_DB** (required) — env vars pointing `generate-data.js` at the target database
- **date_range** (optional, default: as built) — adjust inside `generate-data.js` if needed

## Execution Flow

1. Check if SINK tables exist → fall back to source tables if not
2. Run `SOURCE_DB=<db> SINK_DB=<db> node generate-data.js` — inlines data into `dashboard.html` (single self-contained file)
3. Open `dashboard.html` in a browser (`npx serve .` or `preview_document`)

**Never rewrite `dashboard.html` from scratch. The template injects data directly.**

## Deeper Questions

If the user asks anything beyond "show me the dashboard" — metric definitions, data lineage, why a number looks wrong, how to add a metric — read the knowledge package:

| Question type | Read |
|---|---|
| "What does [metric] mean / include / exclude?" | `knowledge/metrics_catalog.md` |
| "Where does this data come from?" | `knowledge/data_dictionary.md` |
| "Why is [number] different from what I expected?" | `knowledge/metrics_catalog.md` (exclusion rules) + `knowledge/sql_templates.md` |
| "How do I add a new metric?" | `knowledge/sql_templates.md` (add query) + `knowledge/data_dictionary.md` (confirm column exists) |
| "What was the business goal for this dashboard?" | `knowledge/business_context.md` |
| "Can you query the source directly? SINK is missing" | `knowledge/sql_templates.md` § "Workflow SQL" |

**Never answer metric/data questions from memory — always read from `knowledge/` first.**
```

**Store as:** `./<project-name>/skills/SKILL.md`

---

## Step 4a-ii: Extract & Parameterize Query Scripts (15 min)

**What to do:**
- Extract the Phase 3 queries as a reusable script (`generate-data.js`, already copied in Step 4a-i)
- **Inline data directly into `dashboard.html`** (Phase 4 enforces inline-only, no separate data.json)
- Validate column names against the actual schema
- Ensure all queries run in parallel
- Select only the columns the template actually reads
- Assess table grain vs. filter dimensions

---

### Inline-Only Policy: No External Data Files

**Phase 4 dashboards are self-contained.** All data is inlined directly into `dashboard.html`:

**What this means:**
- ✅ Single `dashboard.html` file with embedded data
- ✅ No separate `data.json` dependency
- ✅ Total file size < 2 MB (enforced by Phase 3 hard stop)
- ✅ Shareable as a single email attachment
- ✅ Works offline, no fetch() calls needed

**If you see references to `data-caching-strategy.md` or external JSON:**
These are deprecated. All Phase 4 dashboards now use inline embedding. The Phase 3 `generate-data.js` already enforces this.

**Checklist:**
- [ ] `generate-data.js` inlines data directly (no `data.json` file written)
- [ ] Total `dashboard.html` size < 2 MB
- [ ] If > 2 MB: `generate-data.js` exits with error message, directing you to optimize queries
- [ ] All queries optimized (pre-aggregate, narrow time window, drop unused columns)
- [ ] Template reads inline `RAW` variable (no `fetch()` needed)

---

**FIRST STEP — Column Name Audit (2 minutes, prevents 2+ hours debugging):**

```bash
tdx show tables --in <database>
tdx describe <db>.<table>
tdx query -d <db> "SELECT <column_name> FROM <table> LIMIT 1"
```

**Common mistakes this catches:**
- Template expects `customer_count` → table has `total_customers` or `num_customers`
- Template expects `total_revenue` → table has `service_revenue` or `revenue_amount`
- Query references a column that doesn't exist (returns an error)

**Checklist:**
- [ ] Run `tdx describe <table>` and copy exact column names
- [ ] Cross-check against `state.md` metrics list
- [ ] Sample each column: `SELECT <col> FROM <table> LIMIT 1`

---

**Snapshot Table Date Column Check (1 minute, prevents silent wrong results):**

Some tables are **snapshots** — they hold the latest state of each entity and have **no date column**. A `WHERE date BETWEEN ...` filter on such a table either errors or silently returns zero rows.

```bash
tdx describe <db>.<table>
# Look for: date, created_at, time, event_date, transaction_date, etc.
```

| Table type | Has date column? | Action |
|---|---|---|
| Fact / transactional table | Yes | Safe to add a date filter |
| Snapshot / reference table | No | **Omit the date filter entirely** |
| Snapshot with `td_client_time` | Only a system column | Omit date filter — `td_client_time` is ingestion time, not business date |

```sql
-- ❌ WRONG: a geography snapshot table has no date column
SELECT region, state FROM sink_geography
WHERE date >= '2024-01-01' AND date <= '2024-12-31';   -- error or 0 rows

-- ✅ CORRECT: no filter needed
SELECT region, state FROM sink_geography;
```

**Checklist:**
- [ ] For every table, run `tdx describe` and confirm a date column exists before writing a date `WHERE` clause
- [ ] Snapshot tables: omit the date filter, note "snapshot — no date filter" as a comment

---

**`tdx query` Row Limit (non-negotiable — prevents silent data truncation):**

By default, `tdx query` silently truncates display output to ~40 rows. Without an explicit limit, `generate-data.js` may build the dashboard on partial data with no error or warning.

```bash
# ❌ WRONG: silently returns ~40 rows even if the table has 5,000+
tdx query -d <db> "SELECT * FROM sink_sales" --format json

# ✅ CORRECT: explicit safe limit
tdx query -d <db> "SELECT * FROM sink_sales" --format json --limit 10000
```

Guidance: small dimension/snapshot tables → `--limit 1000`; fact/transaction tables → `--limit 50000`; default when unsure → `--limit 10000`.

**Checklist:**
- [ ] Every `tdx query` call includes `--limit <N>`
- [ ] Every `executeQuery()` call in `generate-data.js` includes an explicit limit
- [ ] Row count spot-checked against `SELECT COUNT(*) FROM <table>`

---

**CLI Output JSON Parsing (prevents wrong parse):**

`tdx` prepends status lines before the JSON array:
```
- Executing query...
✔ Query completed: [Job ID: 3173...]
[{"col": "val"}, ...]
```

`raw.find('[')` matches `[Job ID: 3173...]`, not the real array. Use a regex instead:

```javascript
// ❌ WRONG
const jsonStr = raw.slice(raw.indexOf('['));

// ✅ CORRECT
const match = raw.match(/\[\s*\{/);
const jsonStr = match ? raw.slice(match.index) : '[]';
```

**Checklist:**
- [ ] All `tdx` output parsing in `generate-data.js` uses `\[\s*\{` — not `indexOf('[')` or `.find('[')`

---

**KPI Query Grain Design (prevents over-aggregated / mismatched totals):**

| Pattern | Grain | When to use |
|---|---|---|
| **Pre-aggregated KPI** | Single row (e.g. `total_orders: 648`) | Static KPI cards — no client-side filtering |
| **Full dimensional** | Row per `date × channel × category × segment` | Client-side JS filtering — the JS aggregates |

If the dashboard has client-side filter dropdowns, the query must fetch the full dimensional grain, not a collapsed total.

```sql
-- ❌ WRONG for client-side filtering: returns 1 aggregated row
SELECT COUNT(*) AS total_orders, SUM(revenue) AS total_revenue
FROM sink_sales WHERE date BETWEEN ... AND ...;

-- ✅ CORRECT: full grain, JS filters client-side by any combination
SELECT order_date, channel, category, customer_segment,
       COUNT(*) AS orders, SUM(revenue) AS revenue
FROM sink_sales
GROUP BY order_date, channel, category, customer_segment;
```

**Checklist:**
- [ ] For each query: does the dashboard filter client-side (JS) or server-side (new query per filter)?
- [ ] Client-side filtered charts: queries return the full dimensional grain
- [ ] Pre-aggregated KPI cards with no filter: single-row aggregation is fine

---

**Table Grain Assessment (1 minute, impacts payload size):**

```javascript
// Table metadata (comment at top of generate-data.js)
// Table built at: customer_id, vehicle_model, region, service_type, fuel_type (5 dims)
// Dashboard filters on: customer_id, vehicle_model, region, service_type (4 dims)
// Action: GROUP BY only the 4 filter dimensions to avoid row fan-out

// ❌ WRONG: returns full table grain (6,619 rows, 1.4 MB payload)
SELECT * FROM fact_customer_overview;

// ✅ CORRECT: aggregate on filter dimensions only (2,240 rows, 600 KB)
SELECT customer_id, vehicle_model, region, service_type,
       SUM(revenue), AVG(rating), COUNT(*)
FROM fact_customer_overview
GROUP BY customer_id, vehicle_model, region, service_type;
```

**Checklist:**
- [ ] Identify all table dimensions vs. dashboard filter dimensions
- [ ] If the table has extra dimensions, GROUP BY only the ones the dashboard filters on

---

**Column Selection Audit (2 minutes, impacts payload size):**

```javascript
// Template usage map (document in generate-data.js)
// Template reads: customer_id, vehicle_model, total_revenue, avg_rating
// ✅ INCLUDE only these
// ❌ EXCLUDE unused columns: fuel_type, vehicle_type, tickets_resolved, status
```

**Checklist:**
- [ ] Scan `dashboard.html` for every data key it references
- [ ] `generate-data.js` fetches only those columns
- [ ] Remove "might be useful later" columns

---

**Parallel Queries (non-negotiable):**

`generate-data.js` must use `Promise.all()` for all queries:

```javascript
// ❌ WRONG: sequential (~5 seconds)
const metric1 = await executeQuery('SELECT SUM(revenue) FROM fact');
const metric2 = await executeQuery('SELECT COUNT(*) FROM fact');

// ✅ CORRECT: parallel (~1 second)
const [metric1, metric2] = await Promise.all([
  executeQuery('SELECT SUM(revenue) FROM fact'),
  executeQuery('SELECT COUNT(*) FROM fact'),
]);
```

---

**Performance floor (1 minute, prevents wasted optimization):**

- `tdx query` execution → ~0.5 second floor per query
- Browser rendering (HTML Client) → ~0.5 second floor

**Rule:** once total query time approaches ~0.5-1s, stop optimizing SQL — rendering cost dominates from there.

**Checklist:**
- [ ] Measure total query time with all queries in parallel
- [ ] If total < 0.5s: optimization is complete
- [ ] If total > 2s: re-check grain, column selection, and parallelization

---

## Step 4a-iii: Create Configuration Templates (10 min)

**What to do:** document common configurations so the next build is faster.

```yaml
# Template: Weekly Executive Rollup
schedule: Weekly (Monday 2 AM)
inputs:
  date_range: 7
  key_metrics: revenue, churn_rate, new_customers
filters: [region: all, segment: all]

---

# Template: Monthly by-Region Deep Dive
schedule: Monthly (1st of month, 1 AM)
inputs:
  date_range: 30
  key_metrics: all
filters: [region: pivot column, segment: multi-select]

---

# Template: Annual Historical Trend
inputs:
  date_range: 365
  key_metrics: all
filters: [date_range: adjustable, region: toggle]
performance: [Initial load: ~1s, Filter update: <0.5s]
```

**Create and store as:** `./<project-name>/skills/config-templates.yaml`

---

## Step 4a-iv: Document Deployment & Replication Checklist (10 min)

```markdown
# [Type] Dashboard Replication Checklist

## Pre-Flight (5 min)
- [ ] Verify database exists: tdx db list | grep {database_name}
- [ ] Confirm tables: tdx describe {database}.{table}
- [ ] Check data freshness: SELECT MAX(updated_at) FROM {database}.{table}
- [ ] Verify permissions: tdx query "SELECT 1 FROM {database}.{table} LIMIT 1"
- [ ] Confirm row count: SELECT COUNT(*) FROM {database}.{fact_table}

## Configuration (10 min)
- [ ] Select a config from skills/config-templates.yaml
- [ ] Update SOURCE_DB / SINK_DB env vars for the target database
- [ ] Adjust date_range / key_metrics if needed

## Deploy (5 min)
- [ ] Run: SOURCE_DB=<db> SINK_DB=<db> node generate-data.js
- [ ] Verify row counts match expectations
- [ ] Open dashboard.html and confirm it renders

## Validation (5 min)
- [ ] Visual check: layout matches the approved Phase 3 dashboard
- [ ] Filter check: all filters work (date, region, segment)
- [ ] Data check: KPI totals match confirmed samples (±5%)
- [ ] Performance check: queries complete in <5 seconds

## Post-Deploy (2 min)
- [ ] Document any issues found
- [ ] Note the database, date, and result in state.md

**Total replication time: ~10-30 minutes** (vs 2-3 hours from scratch)
```

**Create and store as:** `./<project-name>/skills/deployment-checklist.md`

---

## Step 4a-v: Validate the Extracted Skill

There's no transformer to unit-test for HTML Client — instead, trigger the skill end-to-end with real data and confirm the dashboard reproduces exactly as approved in Phase 3.

### Sub-step 1: Run generate-data.js against the target database

```bash
cd ./<project-name>/skills
SOURCE_DB=<source_db> SINK_DB=<sink_db> node generate-data.js
```

Expected output:
```
Querying <sink_db>...
✅ dashboard.html written — N rows across M queries (inline data)
```

**If it errors:** check env var names match what `generate-data.js` reads (`process.env.SOURCE_DB`, `process.env.SINK_DB`). Fix the script — never hardcode values.

### Sub-step 2: Verify inline data against Phase 1/3 confirmed samples

Open the generated `dashboard.html` in a browser and verify:

1. Visually inspect the dashboard: Do the KPI cards, charts, and tables show expected data?
2. Browser console check: Open DevTools (F12 → Console) and run:
```javascript
Object.keys(window.RAW).forEach(k => {
  const val = Array.isArray(window.RAW[k]) ? window.RAW[k].length + ' rows' : window.RAW[k];
  console.log(k, '→', val);
});
```

**Checklist:**
- [ ] All expected top-level keys present (match what `dashboard.html` reads)
- [ ] No key has `null`, `undefined`, `0`, or an empty array where real data is expected
- [ ] At least one numeric KPI is within ±5% of the confirmed sample value in `state.md`
- [ ] Row counts for list/table data match what Phase 3 rendered

**If a value looks wrong:** re-run the underlying query manually with `tdx query` and compare. The mismatch is almost always a wrong env var, a stale SINK table, or a `GROUP BY` difference vs. the Phase 3 query.

### Sub-step 3: Reproduce the dashboard

```bash
npx serve ./<project-name>/skills/
# → open http://localhost:3000/dashboard.html
```

Or use `preview_document` in Treasure Work: `preview_document: ./<project-name>/skills/dashboard.html`

### Sub-step 4: Reuse test — confirm the skill is self-contained

```bash
SOURCE_DB=<another_or_same_db> SINK_DB=<sink_db> node generate-data.js
# Re-open dashboard.html — confirm it loads without any code changes
```

**Pass criteria (all must be green before Step 4a-vi):**
- ✅ `generate-data.js` runs without errors against the target database
- ✅ `dashboard.html` created with inline data (single self-contained file)
- ✅ Total file size < 2 MB (Phase 3/4 hard limit enforced)
- ✅ Inline data keys and values match confirmed samples (±5%)
- ✅ `dashboard.html` renders and visually matches the Phase 3 approval
- ✅ No hardcoded database names in `generate-data.js` — only env vars
- ✅ Dashboard reproduces correctly after a clean re-run
- ✅ Reuse test passes — changing the database env var re-renders cleanly without editing any file
- ✅ `dashboard.html` works offline (no external fetch() calls or network dependencies)
- ✅ No browser console errors (F12 → Console)

---

## Track A Output

✅ `skills/knowledge/` — knowledge package (business_context, data_dictionary, sql_templates, metrics_catalog)
✅ `skills/SKILL.md` — execution flow + `## Deeper Questions` section pointing to `knowledge/`
✅ `skills/dashboard.html` + `skills/generate-data.js` — copied from the Phase 3 approved output
✅ `skills/config-templates.yaml` and `skills/deployment-checklist.md`

**Result:** future builds against a new database take ~10-30 minutes instead of 2-3 hours.

---

## Track A — Lessons Learned

- **Save the template at Phase 3 approval, not Phase 4** — the approved `dashboard.html` + `generate-data.js` are the source-of-truth. Copy them into `skills/` immediately after approval. Track A only wires the knowledge package and deployment docs around them — it never recreates them.
- **The skill must be a pure render skill** — no phase steps, no requirements gathering, no workflow deployment logic. When triggered it should: check for SINK tables (fall back to source), run `generate-data.js`, open `dashboard.html`. Nothing else.
- **The skill is NOT:** a summary of all phases, a deployment guide (that's `deployment-checklist.md`), or a requirements doc (that's `business_context.md`).
- **Write the trigger description for natural phrases, not technical ones:**

```yaml
# Good — fires on natural user phrases
description: |
  Use when user says "travel dashboard", "show me travel analytics",
  "I need a travel dashboard", or "travel KPIs".
  Runs N queries → renders a single-page HTML dashboard. No phases.

# Too technical — won't trigger naturally
description: |
  Executes the dashboard rendering pipeline for travel-domain tables
  using generate-data.js with pre-fetched query results.
```

- **Separate template from data:** `dashboard.html` (static, never edit between runs) stays untouched; only the env vars passed to `generate-data.js` change per database.

**Folder structure (local working directory):**

```
./<project-name>/
├── skills/                          ← Track A output
│   ├── SKILL.md
│   ├── dashboard.html
│   ├── generate-data.js
│   ├── config-templates.yaml
│   ├── deployment-checklist.md
│   └── knowledge/
│       ├── business_context.md
│       ├── data_dictionary.md
│       ├── sql_templates.md
│       └── metrics_catalog.md
├── workflows/                        ← Phase 2 (if run)
├── dashboards/                       ← Phase 3 output
├── agents/                           ← Track B (if run)
└── docs/                             ← Phase 5 (if run)
```

---

## Step 4a-vi: Deploy the Skill

**Step 1: Confirm the skill name** — Phase 1 does not capture a skill name, so ask fresh here:

```
AskUserQuestion:
  header: "Skill name"
  question: "What should this skill be called?"
  options:
    - label: "Generate from the dashboard's business goal"
      description: "Suggest a name based on the business_goal in state.md (e.g., retail-revenue-dashboard)"
    - label: "I'll provide a custom name"
      description: "You'll type a business-friendly name"
```

Lock in the confirmed `<skill-name>` before proceeding.

---

**Step 2: Choose skill scope** — Where should the skill live?

| Scope | Location | Visibility | How to use | Best for |
|-------|----------|---|---|---|
| **Personal workspace (Recommended)** | `~/.claude/skills/<skill-name>/` | All your Claude Code sessions (you only) | Auto-loaded in all sessions + Treasure Work via `/plugin install` | Cross-project reuse, recurring builds, available everywhere |
| **Zip distribution** | `./<project-name>/<skill-name>.zip` | Manual transfer between systems | Unzip and place in `~/.claude/skills/` on recipient's machine; or upload to share | Cross-team sharing, offline distribution, collaboration |

```
AskUserQuestion:
  header: "Skill distribution"
  question: "Where should this skill live?"
  options:
    - label: "Personal workspace (Recommended)"
      description: "Copy to ~/.claude/skills/ → available in all your Claude Code sessions. You can use it across all projects."
    - label: "Package as Zip"
      description: "Create <skill-name>.zip for sharing with teammates. They unzip and place in their ~/.claude/skills/ to use."
```

Branch to the appropriate section below based on the user's choice.

---

## ➜ If Selected: PERSONAL WORKSPACE (Recommended)

**Action: Copy skill to personal workspace for cross-session use**

After Step 4a-v passes (generate-data.js validated), run these commands:

```bash
# 1. Create personal skills directory if needed
mkdir -p ~/.claude/skills

# 2. Copy extracted skill to personal workspace
cp -r ./<project-name>/skills/<skill-name> ~/.claude/skills/<skill-name>

# 3. Verify installation
ls -la ~/.claude/skills/<skill-name>/

# 4. Verify no data.json (data should be inlined in dashboard.html)
ls -la ~/.claude/skills/<skill-name>/ | grep data.json || echo "✅ No data.json found (correct)"
```

**Result:** Skill now available in all Claude Code sessions. Auto-loads whenever you reference the skill name.

**Next step:** Update `state.md` with skill location and proceed to Step 4a-vii (INSTALL.md).

---

## ➜ If Selected: ZIP DISTRIBUTION

**Action: Package skill as distributable zip**

**⚠️ Always show the full packaging instructions below after `generate-data.js` validation (Step 4a-v) passes — even if a zip was already created earlier in the session. Never skip or summarize this section.**

---

### What goes in the zip

```
<skill-name>/
├── SKILL.md
├── dashboard.html
├── dashboard-template.html        ← includes Chart.js inline (self-contained)
├── generate-data.js               ← embeds data directly into dashboard.html (no separate data.json)
├── config-templates.yaml
├── deployment-checklist.md
└── knowledge/
    ├── business_context.md
    ├── data_dictionary.md
    ├── sql_templates.md
    └── metrics_catalog.md
```

---


### ℹ️ Skill Portability: No Server Required

The dashboard skill (SKILL.md + dashboard.html + knowledge/) is completely portable:

✅ Recipients open `dashboard.html` in any browser (no installation needed)  
✅ Works offline  
✅ No dependencies beyond a browser  
✅ Share via email, Git, ZIP file, or folder copy  

**Recipient onboarding (one sentence):**
> "Open `dashboard.html` in your browser — it's a standalone dashboard that works offline."

---


### Step 2a: Packaging commands (ZIP DISTRIBUTION ONLY)

After Step 4a-v passes, display the following to the user verbatim (fill in `<skill-name>`):

---

**Your skill is validated and ready to share.**

**Skill name:** `<skill-name>`

⛔ **Run these commands from inside `./<project-name>/`** — the zip must land there, not at the repo root.

```bash
cd ./<project-name>

# 1. Copy the skill folder, rename to the skill name
cp -r skills <skill-name>

# 2. Verify no data.json exists (data is inlined into dashboard.html)
ls -la <skill-name>/ | grep data.json || echo "✅ No data.json found (correct)"

# 3. Zip it — exclude macOS artifacts
zip -r <skill-name>.zip <skill-name>/ \
  -x "*.DS_Store" \
  -x "*/__MACOSX/*" \
  -x "__MACOSX/*"

# 4. Confirm contents
unzip -l <skill-name>.zip | head -40

# 5. Clean up the staging copy
rm -rf <skill-name>/
```

⛔ **Run these commands now — do not just show them to the user. Confirm the zip was created before proceeding:**

```bash
ls -lh ./<project-name>/<skill-name>.zip
```

**Expected zip structure** — verify the listing from step 4 matches this shape:
```
<skill-name>/
<skill-name>/SKILL.md
<skill-name>/dashboard.html
<skill-name>/dashboard-template.html
<skill-name>/generate-data.js
<skill-name>/config-templates.yaml
<skill-name>/deployment-checklist.md
<skill-name>/knowledge/business_context.md
<skill-name>/knowledge/data_dictionary.md
<skill-name>/knowledge/metrics_catalog.md
<skill-name>/knowledge/sql_templates.md
```

No `__MACOSX/` entries. No `.DS_Store` entries. No loose files outside `<skill-name>/`.

---

**Optional: Create a zip file to share with teammates**

```
AskUserQuestion:
  header: "Share skill"
  question: "Would you like to create a zip file to share this skill with teammates?"
  options:
    - label: "Yes, create a zip"
      description: "Create <skill-name>.zip for sharing. Recipients unzip and place in ~/.claude/skills/ to use."
    - label: "No, I'm done"
      description: "Skill is already in ~/.claude/skills/ and ready to use. You can share the zip manually later if needed."
```

**If creating a zip for sharing:**

Send the recipient `<skill-name>.zip` plus these instructions:

```
1. Unzip: unzip <skill-name>.zip
2. Move into your personal skills folder: mv <skill-name>/ ~/.claude/skills/
3. Restart your Claude Code session
4. The skill is now available in all your sessions — type the trigger phrase from <skill-name>/SKILL.md
```

---

**OLD: Project-folder install (deprecated — skills should not live in projects):**

~~Send the recipient `<skill-name>.zip` plus this ready-to-use prompt (fill in `<skill-name>` and `<sink-database>` from `state.md` before sending — use real values, not placeholder tokens)~~

```
I have uploaded a dashboard skill zip to this project. Please do the following:

0. Scan the project directory first.
   - Run: find . -name "*.zip" 2>/dev/null
   - Also check: find . -name "<skill-name>" -type d 2>/dev/null
   - If <skill-name>/ already exists (previously unzipped), skip to Step 2.

1. Unzip the skill into the current project directory.
   - Run: unzip <skill-name>.zip
   - Confirm: ls <skill-name>/
     Expected: SKILL.md, dashboard.html, generate-data.js
   - If either dashboard.html or generate-data.js is missing: STOP and report which file is absent.
     Do NOT manually re-implement the queries — the zip is the canonical source.

2. Read <skill-name>/SKILL.md and follow its execution flow exactly.

3. Run the dashboard.
   - From inside <skill-name>/, run:
       SINK_DB=<sink-database> node generate-data.js
     This inlines data into dashboard.html (single self-contained file). No other flags or arguments.

4. Open the dashboard.
   - Use preview_document on <skill-name>/dashboard.html, or open it directly in a browser.

5. Confirm it rendered correctly:
   - All panels visible, KPI cards show real numbers (not dashes, zeros, or "undefined")
   - No JavaScript console errors

Sink database: <sink-database>
```

**Fill-in reference:**

| Placeholder | Where to find it |
|-------------|-----------------|
| `<skill-name>` | `name:` field in `./<project-name>/skills/SKILL.md` |
| `<sink-database>` | `state.md` — SINK database name (omit if Phase 2 was skipped; use the source database instead) |

**What the recipient gets:**

| File | Purpose |
|------|---------|
| `SKILL.md` | Entry point — execution flow |
| `knowledge/` | Answers deeper questions about data, metrics, and SQL |
| `dashboard.html` | Static dashboard (never edit between runs) |
| `generate-data.js` | Parameterized data pipeline (change env vars only) |

**They do NOT need to run any Phase 1-3 steps.** The skill is self-contained: set env vars, run, get the dashboard.

---

---


---

## Step 4a-vii: Generate Installation Guide (INSTALL.md)

After packaging and before sharing, create `skills/INSTALL.md` with platform-specific instructions so recipients know exactly how to install and run the skill.

**What to include in INSTALL.md:**

```markdown
# Installation & Usage Guide: [Skill Name]

## Prerequisites
- TAIS (Treasure AI Studio) OR Treasure Work
- Treasure Data account with access to:
  - Database: [SINK_DB from state.md]
  - Tables: [list confirmed tables]
- API key (if not using default auth)

## Installation

### Claude Code (Recommended)
1. Unzip `<skill-name>.zip`
2. Copy the `<skill-name>` folder to `~/.claude/skills/`
3. Restart Claude Code or refresh
4. Skill appears in all your sessions

### Treasure Work
```bash
# Option A: Copy to personal skills
unzip <skill-name>.zip && mv <skill-name>/ ~/.claude/skills/

# Option B: Install via plugin command
/plugin install <skill-name>-skill.zip
```

## Running the Skill

### TAIS
1. Open Develop tab → select the skill
2. Environment variables required:
   - `SINK_DB=<database-name>` (default: `[SINK_DB from state.md]`)
   - `SOURCE_DB=<database-name>` (if Phase 2 was skipped, same as SINK_DB)
3. Click **Run** or type the trigger phrase

### Treasure Work
```bash
/plugin run <skill-name> --env SINK_DB=<database-name>
```

## Verification Checklist
- [ ] Dashboard loads without errors (F12 → Console: no red errors)
- [ ] All KPI cards show numbers (not "undefined" or dashes)
- [ ] Filters work (date, region, segment — if applicable)
- [ ] Data matches confirmed values from original build (within ±5%)

Confirmed spot-check values (from original build):
- [Metric 1]: [value from state.md]
- [Metric 2]: [value from state.md]
- [Metric 3]: [value from state.md]

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| "undefined" in KPI cards | Query failed or env var wrong | Check SINK_DB env var; run `tdx query` manually |
| Filters don't work | `generate-data.js` failed | Check console errors; run `generate-data.js` manually |
| Dashboard layout broken | browser compatibility | Use Chrome/Firefox; check browser console |

## Support
For questions about the data, see `skills/knowledge/` files:
- `business_context.md` — why this dashboard exists
- `data_dictionary.md` — table/column definitions
- `metrics_catalog.md` — KPI formulas
- `sql_templates.md` — underlying queries

---

**Skill Version:** [from skills/SKILL.md]  
**Built:** [YYYY-MM-DD from state.md]  
**Data Source:** [SINK_DB]
```

**Fill in the bracketed placeholders from `state.md` and Phase 3 confirmed values.**

**Store as:** `./<project-name>/skills/INSTALL.md`

**Then include INSTALL.md in the final zip (Step 4a-vi packaging):**
```bash
zip -r <skill-name>.zip <skill-name>/ -x "*.DS_Store"
# INSTALL.md is already in skills/ folder, so it's included automatically
```

---

## Skill Auto-Discovery in Claude Code / Treasure Work

**After copying skill to `~/.claude/skills/<skill-name>/`:**

The skill appears in the **Develop** tab automatically, but timing depends on your client:

### Desktop App (Treasure Work / Claude Code)
1. Copy skill to `~/.claude/skills/<skill-name>/`
2. **Restart the application** (or wait ~30 seconds for file watchers to pick up changes)
3. Open **Develop** tab → skill appears in the list
4. Click the skill to load it

### Web App (claude.ai/code)
1. Copy skill to `~/.claude/skills/<skill-name>/` (must be on same machine serving web app)
2. **Refresh the browser** or **Force reload (Cmd+Shift+R / Ctrl+Shift+R)**
3. Open **Develop** tab → skill appears
4. Click the skill to load it

### Troubleshooting: Skill Not Appearing

**Check 1: Folder structure is correct?**
```bash
ls -la ~/.claude/skills/<skill-name>/
# Must have: SKILL.md at root
# Example:
# SKILL.md
# dashboard.html
# generate-data.js
# config-templates.yaml
# knowledge/
```

**Check 2: SKILL.md frontmatter is valid?**
```yaml
---
name: fde-dashboard-travel-analytics
description: Short description here
---
```

**Check 3: Still not showing?**
- Clear browser cache (if web app)
- Restart app (if desktop)
- Check file permissions: `chmod 755 ~/.claude/skills/<skill-name>/`

**Auto-discovery takes up to 30 seconds** — the file watcher periodically scans `~/.claude/skills/`.

---

### After Sharing — Record to state.md

Append to `state.md`:
```markdown
## Phase 4 Track A: Reusable Skill Packaged (YYYY-MM-DD)

- skill_name: [confirmed-skill-name]
- Packaging method: [zip | workspace-copy]
- Shared with: [recipient / team]
- Archive location: `./<project-name>/<skill-name>.zip` (or workspace path)
- Ready for: Recipients to install and re-run with different data sources
```

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team

---

## ⚠️ Data Privacy During Validation

**CRITICAL: When running `generate-data.js` against real data (Step 4a-v):**

### Rule: Query Results Must NOT Enter AI Context

❌ **DON'T:** Read query results into AI agent or Claude for analysis
```javascript
// WRONG — exposes customer data to AI
var result = execSync('tdx query "SELECT email, revenue FROM customers"');
var analysis = ai.analyze(result);  // ← Breach!
```

✅ **DO:** Read results into generate-data.js variables only (stays local)
```javascript
// RIGHT — data stays in local JavaScript, never sent to AI
var result = execSync('tdx query ...');
var RAW = JSON.parse(result);  // ← Local only
fs.writeFileSync('dashboard.html', html);  // ← Static file
```

### Validation Flow (Safe)

1. Run `generate-data.js` locally → generates dashboard.html with real data embedded
2. Open dashboard.html in browser → verify metrics visually
3. **Never paste query results or embedded data into Claude/AI for interpretation**

### If You Need AI Help Analyzing Results

1. Use **anonymized/aggregated data only** (no PII):
   ```sql
   SELECT DATE(created_at) as date, COUNT(*) as user_count
   FROM customers
   GROUP BY 1
   -- OK to analyze — no PII
   ```

2. Or use **synthetic/fake data** that mirrors real structure:
   ```sql
   SELECT 'john_anon_1'::text as user_id, 1000.0 as revenue
   -- Safe to analyze — clearly fake
   ```

### See Also

→ Read `../../references/guardrails-lite.md` for complete data handling rules

---

