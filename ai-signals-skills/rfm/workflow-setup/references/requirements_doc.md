# RFM Requirements — Customer-Fillable Template

This is the body template for the `RFM Requirements - <Customer>` doc, written to `agent_outputs/<customer_slug>/rfm/requirements.md`. Bootstrapping `agent_outputs/` and the hand-off / read-back flow are handled by `../../../shared/local_outputs.md` and `../../../shared/requirements_doc_pattern.md` — do not duplicate that flow here.

> **Do NOT include auto-generation disclaimers in the requirements doc.** It must read as a clean, customer-ready questionnaire.

---

## Step 1: Data Source Inventory

After completing Phase 1 data exploration (see `rfm/SKILL.md` Phase 1), summarize the confirmed source tables here:

| Source Table | RFM Type | User ID Column | Timestamp Column | Order Amount Column | Filters Applied | Contributes to |
|---|---|---|---|---|---|---|
| `db.table_name` | Pageviews / Email / Orders / Sales | `canonical_id` | `time` | `0.0` or column name | e.g., exclude 'sent' | R, F |
| | | | | | | |

**How to ask:** Never present confirmation as a plain text list. Always use the `AskUserQuestion` tool so each question renders as an interactive selector. Group into batches of up to 4 questions per call (tool limit). For each question provide 2–4 pre-populated answer options — mark the recommended default with `(Recommended)` — plus the implicit "Other" option that lets the user type a custom answer.

For the table confirmation step, provide options such as "Confirm tables as listed (Recommended)" and "Exclude or adjust one or more tables".

---

## Step 2: ID Configuration

**Has the customer's data gone through ID Unification? Do they have a `gldn` database with enriched/unified tables?**

- [ ] Yes — `join_key` is `canonical_id`, tables are in a `gldn_*` database
- [ ] No — unique identifier used across all tables: _______________

**`canonical_id` value (the column name to use as the user ID key):** _______________

---

## Step 3: Monetary Metric

**Which column represents the customer's monetary value (purchase amount)?**

| Source | Column | Notes |
|--------|--------|-------|
| Orders table | `unit_price` / `total_amount` / `revenue` | Identify which applies |
| Transactions table | `amount` | If applicable |
| None | — | Non-commerce use case — `order_amount: 0.0` for all tables |

Monetary column: _______________

If no monetary data exists, confirm with the user that the M score will be uniform (count-based only).

---

## Step 4: Time Filters & Business Rules

**Time filter:**
- [ ] No filter (default) — use all historical data *(recommended for first-time setup)*
- [ ] Lookback period: `lookback_period: -_____d`
- [ ] Fixed date range: `time_range_start_date: ________` → `time_range_end_date: ________`

**Business rules:**
- Order status filter: _______________  *(e.g., `NOT REGEXP_LIKE(lower(order_status), 'cancel|return')`)*
- Email event type filter: _______________  *(e.g., only `open`, `click`, `conversion`, `unsubscribe`)*
- Other filters: _______________

---

## Step 5: Scoring Configuration

**Scoring model (`model_type`):**
- [ ] `custom` *(default — quartile-based scoring using TD SQL, 1-4 scale per dimension)*
- [ ] `automl` *(AI-Signals feature — automated ML-based scoring)*

**Scoring bins (`num_bins`):**
- [ ] 10 *(default — decile scoring, 1-10 scale)*
- [ ] 5 *(quintile — simpler, easier to communicate to marketers)*
- [ ] Custom: _____

**Sink database (where output tables will be written):** _______________

**Archive previous RFM results before each run?**
- [ ] Yes *(default)*
- [ ] No

**Store historical scores for trending analysis?**
- [ ] No *(default)*
- [ ] Yes

**Auto-build named customer segments from RFM scores?**
- [ ] No *(default)*
- [ ] Yes *(Champions, Loyal Customers, At-Risk, Lost, etc.)*

**Create visualization dashboard?**
- [ ] Yes *(default)*
- [ ] No

---

## Step 6: Validate & Confirm

Before proceeding to YAML generation, present the full requirements summary to the user and wait for explicit confirmation:

```
RFM Customer Segmentation — Requirements Summary
===================================================

Customer: [name]
Database: [database_name]
User ID column: [canonical_id]
Sink database: [sink_database]
Requirements doc: agent_outputs/<customer_slug>/rfm/requirements.md

Data Sources:
1. [table_name] — [type] — contributes to: [R/F/M]
2. [table_name] — [type] — contributes to: [R/F/M]

Monetary Metric: [column name or "none (count-based)"]
Time Filter: [none / interval: -Xd / range: start–end]
Business Rules: [order status filter, email event filter, etc.]
Scoring: [num_bins]-bin scoring
Archive Results: [yes/no]
Store Historical Scores: [yes/no]
Auto-Build Segments: [yes/no]
Dashboard: [yes/no]

Please confirm this is correct before I proceed with configuration.
```

Once confirmed, proceed to YAML generation in `workflow_setup_guide.md`.
