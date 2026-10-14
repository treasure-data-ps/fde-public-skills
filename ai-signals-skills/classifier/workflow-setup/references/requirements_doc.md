# Phase 2: Requirements Gathering

Collect all information needed to configure the Classification workflow before touching any configuration files.

## Step 1: Bootstrap Local Outputs

Read `../../../shared/local_outputs.md` and bootstrap `agent_outputs/` before writing anything. Use these Classifier-specific values:

- **Solution slug:** `classifier`
- **Engagement folder:** `agent_outputs/<customer_slug>/classifier/`
- **Requirements doc file:** `agent_outputs/<customer_slug>/classifier/requirements.md` — title `Classification Requirements Gathering - <Customer Name>`
- **Project state file:** `agent_outputs/<customer_slug>/classifier/project_state.md` (see `../../../shared/project_state.md`)

> Do NOT include auto-generation disclaimers in the requirements doc. It must read as a clean, customer-ready questionnaire.

## Step 2: Check for Existing Requirements Doc

Ask the user:

> Do you have an existing filled-out requirements gathering doc? If yes, give me its file path (or paste its contents).

Also check whether `agent_outputs/<customer_slug>/classifier/requirements.md` already exists. If a doc is available, read it and extract whatever configuration details are available (database, tables, target variable, model preferences, etc.). Use the extracted values to pre-fill later steps, but still validate everything through auto-discovery.

## Step 3: Initial Questions

Collect answers to these questions before exploring any data. These determine the scope and complexity of the Classification configuration.

> **How to ask:** Never present these as a plain text list. Always use the `AskUserQuestion` tool so each question renders as an interactive selector. Group into batches of up to 4 questions per call (tool limit). For each question provide 2–4 pre-populated answer options — mark the recommended default with `(Recommended)` — plus the implicit "Other" option that lets the user type a custom answer. Ask all questions in Step 3 across `AskUserQuestion` calls before proceeding to Step 4.

### 3a: Use Case Definition

Ask: **What binary outcome are you trying to predict?**

Options:
- Lead conversion / purchase propensity
- Customer churn / retention risk
- Campaign response / engagement prediction
- Other (let user describe)

This determines the business context for the model and influences parameter recommendations.

### 3b: Target Variable

Ask: **What is the target variable column name, and how is it defined?**

The target must be binary (0/1). Common patterns:

| Use Case | Target Column | Definition |
|----------|--------------|------------|
| Lead scoring | `converted` | 1 = lead became a customer |
| Churn prediction | `churned` | 1 = customer cancelled or became inactive |
| Campaign response | `responded` | 1 = clicked, opened, or converted |
| Fraud detection | `is_fraud` | 1 = transaction flagged as fraudulent |

Follow-up: **Does an existing column already store this as a 0/1 value, or does it need to be derived from other data?**

- If it exists as a column already, record the table and column name.
- If it needs to be derived (e.g., no `churned` flag exists — it must be calculated from inactivity; or "converted" requires joining a leads table to an orders table with a date cutoff), describe the derivation logic now in plain language. The exact SQL will be finalized once the relevant tables are confirmed in Step 4. Do not assume the label already exists — many use cases require a calculated label.

Follow-up: **What is the positive class event window?** (e.g., "converted within 90 days", "churned within 6 months"). This affects `train_end_months_from_now` — the gap must be at least as long as the event window.

### 3c: Data Readiness

Ask: **Has the customer's data gone through ID Unification? Do they have unified/enriched tables with a consistent user ID?**

- If **yes**: The `user_id_col` will likely be `canonical_id` or a unified ID, and feature tables may already exist in a golden database.
- If **no**: Ask — **Is there a unique identifier that can be used as the main user ID across all source tables?** (e.g., `customer_id`, `email`, `account_id`). This becomes `user_id_col` in the config.

**The join key is not guaranteed to be the same column across every source table.** If a Parent Segment or any source table exposes more than one plausible join key column, do not guess — ask the user which one to use. Track the confirmed join key per table in Step 4; some tables may need a lookup/join table to reconcile their ID column back to the canonical ID.

### 3d: Feature Sources

Ask: **Is there an existing Parent Segment for this customer that already has relevant attributes?**

If a Parent Segment exists, run `tdx ps desc "<name>" -o <slug>_ps_schema.json` and review the `customers` table columns — these are usable as model features directly, with no additional feature engineering. See `tdx-skills:parent-segment-analysis` for the discovery workflow. Note the Parent Segment's join key as a candidate for `user_id_col`.

Regardless of whether a Parent Segment exists, also ask: **Are there any other tables — in the same database or a different one — that should be considered as additional feature sources?**

A Parent Segment's `customers` table rarely covers every useful signal (e.g., a newly integrated system, or a database that hasn't gone through ID Unification yet). Support **any number of additional databases** — do not assume all raw feature tables live in one place. For each additional database named, discover its tables the same way as any other source database.

Prompt the user with examples of what raw tables might contain:
- Web activity (page views, sessions, clicks)
- Purchase/transaction history (orders, cart, subscriptions)
- Email engagement (opens, clicks, campaigns)
- CRM interactions (calls, meetings, support tickets)
- Product usage (logins, feature usage, API calls)
- Customer profile (demographics, account age, plan type)

Each raw-table source feeds into the data prep SQL — the feature engineering step. Parent Segment attributes do not require this step. If a raw table's user ID column doesn't match the Parent Segment's join key directly, note whether a lookup/join table is needed to reconcile them.

### 3e: Precision/Recall Preference

Ask: **What matters more — avoiding false positives or catching all positive cases?**

Options:
- **Precision-biased** — "I'd rather miss some positives than waste effort on false positives" (e.g., sales outreach — don't want reps calling low-quality leads)
- **Balanced** — "Both matter about equally" (Recommended)
- **Recall-biased** — "I can't afford to miss any positive cases, even if some are false alarms" (e.g., fraud detection — must catch all fraud even with some false alerts)

This maps to `fbeta_beta`:
| Preference | `fbeta_beta` |
|-----------|-------------|
| Strongly precision-biased | `0.5` |
| Moderately precision-biased | `0.7` (default) |
| Balanced | `1.0` |
| Recall-biased | `2.0` |

### 3f: Model Type Preference

Ask: **Do you have a model type preference, or should we use the default (XGBoost)?**

Options:
- **XGBoost** — Best for most tabular data, handles missing values, fast training (Recommended)
- **CatBoost** — Better with many categorical features, also handles missing values
- **Logistic Regression** — Maximum interpretability (coefficients), best for linear relationships or regulatory requirements
- No preference — use the default

### 3g: Training Window

Ask: **How far back should we look for training data, and is there a label maturity period?**

- **Lookback period**: How many months of historical data to use for features (default: 27 months)
- **Label maturity gap**: How many months before "now" to stop training data (default: 2 months). This prevents using records whose outcomes haven't fully matured.

Example: For lead scoring where conversion typically takes 3 months, set `train_end_months_from_now: 3` to avoid labeling recent leads as "not converted" when they simply haven't had enough time.

### 3h: Output Configuration

Ask: **What database should the output tables be written to, and do you want a table name prefix?**

- `sink_database`: The TD database for all model output tables
- `table_prefix`: Optional prefix for output table names (e.g., `lead_scoring_`)

### 3i: Columns to Exclude from Features

Ask: **Are there any columns in the source tables that should NOT be used as model features?**

Prompt the user with common examples:
- ID columns (`user_id`, `account_id`, `batch_id`, a raw table's own `session_id`/browsing-session column — note this is unrelated to the workflow's own training-run `session_id`, see `yaml_structure.md` "Session ID Tracking")
- Date/time columns (`created_at`, `reference_date`, `event_time`)
- Columns derived from the target variable (e.g., `cancellation_date` for a churn model — this would leak future information)
- High-cardinality text columns that aren't useful as features (e.g., free-text `notes` fields)

These become the `columns_to_drop` list in `train.dig` and `predict.dig`. **The same list must appear in both files** — a mismatch causes feature misalignment at prediction time.

If the customer is unsure, default to: all ID columns, timestamp columns, and any column that is directly derived from the target variable.

## Step 4: Data Source Inventory

After initial questions, build a feature source inventory covering both source types.

**If a Parent Segment was identified in Step 3d**, list its attributes:

| Field | Description |
|-------|-------------|
| **Attribute name** | Column name in the Parent Segment `customers` table |
| **Data type** | Categorical / Array / Numerical |
| **Already aggregated?** | Yes — no data prep SQL needed |

**For raw feature source tables** (these may span more than one database — list every database used), collect:

| Field | Description |
|-------|-------------|
| **Table name** | Full `database.table_name` — always include the database, since sources may come from different databases |
| **Description** | What data this table contains |
| **User ID / join key column** | Confirm per table — do not assume it matches `user_id_col` or the Parent Segment's join key. If it differs, note whether a lookup/join table is needed to reconcile it to the canonical ID. |
| **Timestamp column** | Column for time-based feature aggregation |
| **Key feature columns** | Columns that can become predictive features |
| **Approximate row count** | Order of magnitude |
| **Date range** | Earliest to latest data |

For each raw source, run:
```sql
DESCRIBE database_name.table_name;
SELECT COUNT(*) as total_rows,
       MIN(time) as min_time,
       MAX(time) as max_time
FROM database_name.table_name;
SELECT * FROM database_name.table_name LIMIT 10;
```

## Step 5: Locate or Construct, Then Validate the Target Variable

If Step 3b determined the label already exists as a column, confirm its exact `database.table.column` now that the relevant table has been discovered in Step 4.

If Step 3b determined the label needs to be derived, write the derivation expression now (e.g., `CASE WHEN days_since_last_order > 180 THEN 1 ELSE 0 END` for churn, or a join between a leads table and an orders table with a date cutoff for conversion). Present the derivation logic to the user for confirmation before using it below — substitute it in place of `<target_variable_column>` in the queries.

```sql
-- Check class distribution
SELECT
  <target_variable_column_or_expression>,
  COUNT(*) AS cnt,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM <database_name>.<label_table>
GROUP BY 1
ORDER BY 1;

-- Check for non-binary values
SELECT DISTINCT <target_variable_column_or_expression>
FROM <database_name>.<label_table>
WHERE <target_variable_column_or_expression> NOT IN (0, 1);

-- Check for NULLs
SELECT COUNT(*) AS null_count
FROM <database_name>.<label_table>
WHERE <target_variable_column_or_expression> IS NULL;
```

**Pass criteria:**
- Only values 0 and 1 (no NULLs, no other values)
- Both classes have rows
- Minority class is at least 1% of total
- If heavily imbalanced (>95:5), note this for model configuration

## Step 6: Validate & Confirm

Before proceeding to configuration, present the full requirements summary to the user:

```
Binary Classification — Requirements Summary
=============================================

Customer: [name]
Use Case: [description]
Target Variable: [column_name] (1 = [event], 0 = [non-event])
Database: [sink_database]
User ID Column: [user_id_col]
Parent Segment: [segment_name or "None — raw tables only"]
Engagement folder: agent_outputs/[customer_slug]/classifier/

Feature Sources:
1. [Parent Segment attribute: attribute_name] — [data type]
2. [table_name] — [description] — [needs data prep SQL: yes/no]
...

Class Distribution: [X]% positive, [Y]% negative
Model Type: [xgboost / catboost / logistic]
Precision/Recall Preference: [preference] (fbeta_beta = [value])

Training Window: [look_back_months_training] months, with [train_end_months_from_now] month gap
Prediction Window: [look_back_months_prediction] months

Output: [sink_database] with prefix '[table_prefix]'

Please confirm this is correct before I proceed with configuration.
```

Once confirmed, this concludes the live interview (Part A). Proceed to the workflow configuration in `workflow_setup_guide.md` Step 4 for the Phase 3 minimal push.

## Step 7: Write the Customer-Shareable Doc (Part B)

After Phase 3's minimal push succeeds (or in parallel, if the user prefers), write the customer-facing doc to `agent_outputs/<customer_slug>/classifier/requirements.md` per `../../../shared/requirements_doc_pattern.md`. Use this section structure:

1. **Initial Questions** — use case, target variable definition (1 = event, 0 = non-event), whether the label exists or is derived, user ID / join keys, Parent Segment
2. **Model Configuration** — model type, precision/recall preference (`fbeta_beta`, `threshold_strategy`), output database + table prefix
3. **Population Definitions** — training window, prediction window, inclusion/exclusion rules for the scored population
4. **Features** — feature source tables and Parent Segment attributes, with relevance confirmation per item
5. **Columns to Exclude** — IDs, leakage columns, non-feature columns
6. **Notes** — anything else the customer wants the model to account for

Each question gets a `> _Your answer:_` placeholder.

**Pre-fill every section with what was learned in the Step 1–6 interview and Phase 1 data exploration** — do not hand the customer a blank form when the answer is already known. Mark pre-filled answers `[INFERRED — please confirm]`. Leave a section open (`[NEEDS YOUR INPUT]`) only when:
- The answer requires business judgment only the customer can make (e.g., precision/recall preference nuance, whether a borderline attribute counts as a feature)
- A candidate feature or table was found but its relevance is unconfirmed
- The question was deferred during the interview

Give the user the file path to share with the customer for review/correction, and update `project_state.md` with the requirements doc status and a note on what's pending customer confirmation. This doc — once the customer returns it — is what Phase 4 reads to re-configure the workflow.
