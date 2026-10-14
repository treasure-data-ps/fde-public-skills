# Stage B: Path Confirmation & state.md Update (Step 2f)

**CRITICAL CHECKPOINT:** Summarize Stage B inferences, update `state.md`, and confirm the path forward.

**⚠️ No Confluence updates, no git commits, no engineer gate, no customer clarification loop in this lite skill.** This is a single-session, self-serve flow — the user reviews and confirms directly, in-session.

**Step 2f must be executed in this exact order — do not skip or reorder:**

```
2f-1  Summarize Stage B findings (present to user)
2f-2  Check for Stage A vs Stage B conflicts
2f-3  Retrieve Stage A Dashboard Complexity Score
2f-4  ★ UPDATE state.md locally (Stage B data discovery)   ← MANDATORY before path question
2f-5  Evaluate path routing logic (score + data source)
2f-8  ★ AskUserQuestion: confirm path (Phase 2 or Phase 3)
2f-9  Final output checklist
      → If Phase 2 (score 4-6, skip_workflow ≠ true): proceed to ../../phase-2/deploy-workflow-guide.md
      → If Phase 3 (score 0-2, or skip_workflow = true): proceed directly to ../../phase-3/build-interactive-dashboard-guide.md
      → If Score 3: ask user to choose Phase 2 or Phase 3, then proceed accordingly
```

**★ = mandatory step — do NOT proceed past it without completing it.**

---

## Step 2f-1: Summarize Stage B Findings

Present a clean summary of all Stage B inferences to the user:

```
✅ Data Discovery & Inferences Complete!

Database: sales_analytics_prod
Tables verified:
  • orders (45.2M rows, updated 2h ago) — FACT
  • customers (1.2M rows, updated 1d ago) — DIMENSION
  • regions (6 rows) — DIMENSION

Metrics INFERRED (with real sample values):
  • Total Revenue: $4,859,839.20 (SUM excluding cancelled + refunded orders)
  • Order Count: 2,156,492 (COUNT(*) all orders)
  • Avg Order Value: $2,254.18 (AVG of order_amount)

Dimensions INFERRED (with actual DISTINCT values):
  • Region: 6 values (North America, Europe, APAC, LATAM, EMEA, APJC)
  • Order Status: 4 values (Completed, Pending, Cancelled, Returned)
  • Active Customer: Customers with ≥1 purchase in last 90 days (45% of base)

Data freshness: Updated 2 hours ago ✅
Extended search: No gaps found ✅
Any Stage A ↔ Stage B conflicts? No ✅
```

---

## Step 2f-2: Check for Conflicts Between Stage A & Stage B

**Re-validate:** Do Stage B inferences align with Stage A requirements?

| Scenario | Stage B Finding | Action |
|----------|---|---|
| Stage A: "daily refresh" | Stage B: Data updates weekly | ⚠️ **Conflict** — Document in `state.md`; clarify with user directly |
| Stage A: "6 regions" | Stage B: Data has 10 regions | ✅ **OK** (superset); proceed with full set |
| Stage A: "metric X needed" | Stage B: Column doesn't exist | ⚠️ **BLOCKER** — Clarify with user; recommend alternative metric from extended search |
| Stage A: "exclude cancelled" | Stage B: Can't identify cancelled orders | ⚠️ **BLOCKER** — Clarify with user which column identifies cancellations |

**If conflicts found:** Resolve directly with the user in-session, then update `state.md` with the resolution before proceeding.

---

## Step 2f-3: Retrieve Stage A Dashboard Complexity Score

- Read **`state.md`** for the Dashboard Complexity Score (Step 1p):
  - Q1: Viewing frequency (0-2 pts)
  - Q2: Historical data needs (0-2 pts)
  - Q3: Audience scope (0-2 pts)
  - **Total Score: [0-6]**

---

## Step 2f-4: UPDATE state.md (Stage B Data Discovery — CRITICAL)

**This is the Stage B deliverable.** `state.md` was created in Stage A with the Session Setup block. Now append Stage B data discovery findings to it.

**APPEND to `state.md`** — do NOT rewrite the Session Setup block:

```markdown
## Stage B: Data Discovery & Inferences

### Database & Tables
- Selected Database: sales_analytics_prod
- Behavior Tables: orders (45.2M rows, updated 2h ago)
- Attribute Tables: customers (1.2M rows), regions (6 rows)

### Metric Definitions (INFERRED from Stage B queries)

**Total Revenue**
- Definition: SUM(order_amount) WHERE status NOT IN ('cancelled', 'refunded')
- Data type: NUMERIC
- Real sample value: $4,859,839.20 (last 90 days)
- Confirm with user: Is this definition correct? Include all revenue types?

**Order Count**
- Definition: COUNT(*) FROM orders WHERE order_date >= [Stage A lookback]
- Real sample value: 2,156,492
- Data type: INTEGER

**Avg Order Value**
- Definition: AVG(order_amount) WHERE status NOT IN ('cancelled', 'refunded')
- Real sample value: $2,254.18
- Confirm with user: Should this exclude low-value orders (<$10)?

### Business Definitions (INFERRED from data patterns)

**Active Customer**
- Definition: Customers with ≥1 purchase in last 90 days
- Data: 45% of customer base (1.8M customers)
- Confirm with user: Is 90 days the correct lookback? Or 30/180 days?

**Order Status Categories**
- Completed: ~85% of orders (fulfilled + delivered)
- Pending: ~10% of orders (awaiting fulfillment)
- Cancelled: ~3% of orders (customer-cancelled)
- Returned: ~2% of orders (returned after delivery)

### Recommended Additional Metrics (discoverable — confirm with user)
- Repeat Purchase Rate: % customers with >1 order — *why: identifies loyal vs one-time buyers; directly actionable for retention*
- Avg Days Between Orders: Average days since last order — *why: sets re-engagement timing*
- Customer Lifetime Value (approx): Total revenue per customer — *why: high-LTV customer profile for acquisition targeting*
- Return Rate: % orders with status='returned' — *why: early signal for product quality issues*

### Recommended Additional Dimensions (discoverable — confirm with user)
- Campaign Name — *why: attribute revenue to specific campaigns*
- Email Channel — *why: compare performance across channels*
- Customer Segment — *why: slice all KPIs by segment*

### Recommended Exclusions (from use case)
- Exclude: test/internal emails
- Exclude: test orders (order_id like 'TEST%')
- Exclude: orders with value < $0 (refunds/credits)
- Exclude: duplicate transactions

### Data Quality Notes
- No NULLs in critical columns (revenue, customer_id, order_date)
- Join cardinality validated: 1 order → 1 customer (1:N is safe)
- Large table performance: Queries execute <2s with Stage A filters

---

## Stage B Path Decision

- Dashboard Complexity Score: 5/6
- Rendering: HTML Client
- Recommended Path: Phase 2 (Workflow)
- Rationale: High business need + raw source data requires pre-aggregation

Last Updated: YYYY-MM-DD
Status: Path confirmed, proceeding
```

---

## Step 2f-5: Path Routing Decision Logic

**⚠️ STOP — Step 2f-4 MUST be completed before reading this routing table.**

Verify the checklist before proceeding:
- [ ] **2f-4 done:** `state.md` updated with Stage B inferences

If unchecked: complete it first. Do NOT skip to routing.

---

**Use Dashboard Complexity Score + `skip_workflow` flag (from `state.md`) to decide the path:**

```
IF skip_workflow == true (data source is pre-aggregated):
  → Skip Phase 2 (Workflow) regardless of score — no workflow needed
  → Route to PHASE 3 (Build Dashboard) immediately

IF complexity_score >= 4:
  → ⚠️ RECOMMEND Workflow path (scheduled refresh, production-ready)
  → WAIT FOR USER CONFIRMATION (see approval gate below)
  → If confirmed: Route to PHASE 2 (Workflow), then PHASE 3
  → If declined: Route to PHASE 3 (Non-Workflow) instead

IF complexity_score == 3:
  → Ask user: "Quick build now (Phase 3, same session) or set up scheduled refresh first (Phase 2, ~15-30 min)?"
  → Proceed per user's choice

IF complexity_score <= 2:
  → ⚠️ RECOMMEND Non-Workflow path (low business need)
  → WAIT FOR USER CONFIRMATION (see approval gate below)
  → If confirmed: Route to PHASE 3 (Build Dashboard) immediately
  → If user prefers workflow: Route to PHASE 2 instead
```

---

## ⚠️ APPROVAL GATES — After Path Recommendation

**⚠️ CRITICAL: After any path recommendation, WAIT for explicit user confirmation before proceeding.**

### Gate A: Workflow Path Confirmation (Score ≥ 4)

**When to use:** After recommending Workflow path

```
📋 Recommended: Workflow Path (Phase 2 → Phase 3)

Based on your data:
  • Dashboard Complexity Score: 5/6 (Score criteria met for Workflow)
  • Business Need: High (frequent refresh, production dashboard)
  • Data Complexity: Complex (multiple tables, joins required)
  • Recommendation: Set up scheduled Workflow to pre-aggregate metrics

⏱️ Time commitment:
  • Phase 2 (Workflow setup): ~20-30 minutes
  • Phase 3 (Dashboard build): ~30-45 minutes
  • Total: ~1 hour from now

💰 Cost Impact:
  • Workflow runs daily (adjust schedule in Phase 2)
  • Estimated query cost: ~$X per day
  • Storage cost for SINK tables: ~$X per month

✅ Benefits:
  • Dashboard loads in <2s (pre-aggregated)
  • Data refreshes on schedule automatically
  • Production-ready for team adoption

To proceed, please type exactly:
YES, PROCEED WITH WORKFLOW PATH

Or type:
NO, SKIP WORKFLOW AND BUILD NOW (Phase 3 only)
```

---

### Gate B: Non-Workflow Path Confirmation (Score ≤ 2)

**When to use:** After recommending Non-Workflow path

```
📋 Recommended: Non-Workflow Path (Phase 3 only)

Based on your data:
  • Dashboard Complexity Score: 2/6 (Low business complexity)
  • Business Need: Low (infrequent refresh, exploratory)
  • Data Source: Simple (few tables, light queries)
  • Recommendation: Build dashboard directly without scheduled workflow

⏱️ Time commitment:
  • Phase 3 (Dashboard build): ~30-45 minutes
  • Total: from now

💰 Cost Impact:
  • No workflow infrastructure
  • Query cost per dashboard load: minimal (~$0.01 per view)
  • No ongoing storage cost

⚠️ Trade-offs:
  • Dashboard loads in 5-10s (queries run on-demand)
  • Data is fresh but slower to fetch
  • Refreshes only when you re-open dashboard (manual)

You can always add a workflow later (Phase 4: Automate & Deploy)

To proceed, please type exactly:
YES, BUILD DASHBOARD NOW (Non-Workflow)

Or type:
NO, SET UP WORKFLOW INSTEAD (Phase 2 → Phase 3)
```

**Canonical score boundaries (single source of truth — use these, not values in other files):**
- **Score 0–2:** Non-Workflow → Phase 3 directly
- **Score 3:** Optional — ask user to choose Phase 2 or Phase 3
- **Score 4–6:** Workflow → Phase 2 (then Phase 3)

**Note:** Rendering engine is always HTML Client — it is never a routing factor.

---

## Step 2f-8: Explicit Path Confirmation

Before asking the path question, present the dashboard plan summary in a code block so the user can review what was discovered:

```
📊 Dashboard Plan — <project_name>

Source Database:   <database>
Tables:
  • <table_1> (<row_count>, updated <freshness>)  — <FACT | DIMENSION>
  • <table_2> (<row_count>, updated <freshness>)  — <FACT | DIMENSION>

Metrics confirmed:
  • <Metric 1>: <formula with real sample value>
  • <Metric 2>: <formula with real sample value>
  • <Metric 3>: <formula with real sample value>

Dimensions confirmed:
  • <Dimension 1>: <N> values  (<val1>, <val2>, ...)
  • <Dimension 2>: <N> values  (<val1>, <val2>, ...)

Date range:        <default_range> | picker: <yes | no>
Data freshness:    <last updated>
Rendering:         HTML Client
Dashboard Complexity Score:   <n>/6

Stage A vs Stage B conflicts:  <None | list conflicts>
```

Then immediately follow with:

```
AskUserQuestion:
  header: "Path Selection"
  question: "Review the plan above. Which path?"
  options:
    - label: "Phase 3 — Build now (Non-Workflow)"
      description: "Fast (minutes). Manual refresh — re-run to update data."
    - label: "Phase 2 — Set up workflow first"
      description: "Scheduled refresh via TD Workflow. Takes longer to set up."
    - label: "Not sure"
      description: "I'll recommend Phase 3. You can add a workflow later in Phase 4 (Automate & Deploy)."
```

**If user selects "Not sure":**
- **DEFAULT to Phase 3 (Non-Workflow)**
- Explain: "We'll build the dashboard now. If you want scheduled refreshes later, we can set that up afterward."

---

## Step 2f-9: Final Output & Next Steps

**Required sequence — do these IN ORDER before routing to any next phase:**

**Phase 3 path (score 0–3, or `skip_workflow = true`):**
1. ✅ **2f-4 done** — `state.md` updated with Stage B inferences
2. ✅ **2f-8 done** — path confirmed as Phase 3
3. ✅ Proceed directly to `../../phase-3/build-interactive-dashboard-guide.md`

**Phase 2 path (score 4–6):**
1. ✅ **2f-4 done** — `state.md` updated with Stage B inferences
2. ✅ **2f-8 done** — path confirmed as Phase 2
3. ✅ Proceed to `../../phase-2/deploy-workflow-guide.md`, then to `../../phase-3/build-interactive-dashboard-guide.md`

---

## Next Phase Routing

### Route to Phase 2 (Workflow Path, Score 4-6, `skip_workflow ≠ true`)
- Proceed to `../../phase-2/deploy-workflow-guide.md`

### Route to Phase 3 (Non-Workflow Path, Score 0-2, or `skip_workflow = true`)
- Proceed to `../../phase-3/build-interactive-dashboard-guide.md` immediately — no pause, same session

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
