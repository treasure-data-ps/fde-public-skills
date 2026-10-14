---
name: fde-tais-dashboard-builder-phase-2
description: INTERNAL — Phase 2 only. Deploy a scheduled workflow that pre-aggregates metrics into SINK tables.
---

# Phase 2: Deploy Dashboard Workflow (FDE TAIS Dashboard Builder)

> **Read in this order:**
> 1. `../INSTRUCTIONS.md` (master rules, load_order: 0)
> 2. `../references/execution-contract.md` (non-skippable execution gates)
> 3. `./INSTRUCTIONS.md` (Phase 2 rules, load_order: 1.2) — includes Quick Checklist
> 4. `./SKILL.md` (this file — full details)
> 5. `./references/phase-2-walkthrough.md` (step-by-step walkthrough)
> 6. `../references/guardrails-lite.md` (cross-phase guardrails)

**Phase Goal:** Convert approved Stage B queries into a scheduled Treasure Data Workflow that pre-aggregates metrics into workflow output tables (SINK tables) — making Phase 3 dashboard queries fast, fresh, and production-grade.

**Skip this phase if you don't need scheduled refresh** — go straight to Phase 3 (Build) and query source tables directly on demand.

**Skills used in this phase:** `workflow-skills:digdag` · `sql-skills:trino` · `sql-skills:trino-optimizer` · `sql-skills:time-filtering`

---

## Pre-Phase-2: Extract Configuration

→ **Before Phase 2:** Read `./<project_name>/state.md` and extract 5 configuration fields. See `./references/phase-2-entry-requirements.md` for details.

---

## Phase 2 Steps 2a–2h

→ **Full workflow:** See `./references/phase-2-walkthrough.md` for step-by-step overview, checklists, troubleshooting, and next-phase routing.

→ **Key resources:** `./references/workflow-setup-configure.md` · `workflow-deployment-validate.md` · `td-time-functions.md` · `testing-troubleshooting.md` · `workflow-templates/`

### Step 2c: SINK Schema Design — Avoiding Multi-Dimension Double-Counting

⚠️ **When SINK tables grain by BOTH product/vehicle dimensions AND customer dimensions, customers with multiple products appear in multiple rows, causing SUM(customer_count) to over-count.**

**Pattern A: Separate SINK Tables (RECOMMENDED)**

If your dashboard needs both customer-level and vehicle-level analysis:
```sql
-- SINK Table 1: Customer KPIs (no vehicle dimension)
CREATE TABLE fact_customer_kpis AS
SELECT
  customer_id,
  segment,
  churn_risk,
  COUNT(DISTINCT vehicle_id) as num_vehicles,
  SUM(revenue) as total_revenue,
  COUNT(*) as total_transactions
FROM source_data
GROUP BY customer_id, segment, churn_risk;

-- SINK Table 2: Vehicle KPIs (vehicle dimension + customer)
CREATE TABLE fact_vehicle_kpis AS
SELECT
  DATE(date) as date_key,
  vehicle_make,
  vehicle_model,
  customer_segment,
  COUNT(DISTINCT customer_id) as unique_customers,  -- COUNT(DISTINCT), not SUM
  SUM(revenue) as total_revenue
FROM source_data
GROUP BY DATE(date), vehicle_make, vehicle_model, customer_segment;
```

Use fact_customer_kpis for "Total Unique Customers" KPI. Use fact_vehicle_kpis for "Revenue by Make/Model" chart.

**Pattern B: Pre-Computed Distinct Counts (In Same Table)**

If you must use a single SINK table with mixed dimensions:
```sql
CREATE TABLE fact_combined AS
SELECT
  DATE(date) as date_key,
  vehicle_make,
  customer_segment,
  COUNT(DISTINCT customer_id) as unique_customers,      -- NOT SUM(customer_count)!
  SUM(transaction_count) as total_transactions,
  SUM(revenue) as total_revenue
FROM source_data
GROUP BY DATE(date), vehicle_make, customer_segment;
```

**Phase 3 Impact:** The Phase 3 KPI queries will use `SELECT unique_customers FROM fact_combined` (safe) instead of `SELECT SUM(customer_count)` (would over-count).

---

→ **See `./references/workflow-deployment-validate.md`** for full deployment and SINK validation steps.

→ **See `./references/phase-2-walkthrough.md`** for: deliverables, end-of-phase checklist, quick reference, performance expectations, and next-phase routing.

→ **See Quick Checklist in `./INSTRUCTIONS.md`** for a condensed Phase 2 decision checklist (setup, deploy, SINK validation gates).
---

**Version:** 1.0.0
**Last Updated:** 23 July 2026
**Author:** FDE Team
