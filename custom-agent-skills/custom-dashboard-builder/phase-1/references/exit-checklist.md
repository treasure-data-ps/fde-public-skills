# Stage B Exit Checklist — Close All Items Before Routing to Phase 2 or Phase 3

**SEQUENCE: Data Quality Gate FIRST → Exit Quality Gates SECOND → Route to Phase 2/3**

---

## ⚠️ FIRST: Pre-Phase 2/3 Data Quality Gate (Checks 1-12)

**RUN BEFORE anything else. This gate validates data is production-ready.**

### Pre-Phase 2/3 Data Quality Gate (BOTH PATHS — Workflow AND Non-Workflow)
**CRITICAL: Run BEFORE routing to Phase 2 or Phase 3. Data quality issues here prevent failures in both paths.**
- [ ] **Database connectivity verified** — `tdx use {database}` succeeds, credentials valid
- [ ] **Schema verification passed** — All metric columns have numeric data types (INT, BIGINT, DECIMAL, FLOAT)
- [ ] **Metric nulls acceptable** — < 10% nulls in any metric column (or use COALESCE in Phase 2/3)
- [ ] **Negative values acceptable** — No unexpected negatives (or documented reason in `state.md`)
- [ ] **Query returns rows** — After all Stage A filters + exclusion rules applied, row count > 0
- [ ] **Data freshness acceptable** — MAX(date_col) is fresh for use case (daily/weekly/monthly)
- [ ] **Dimension cardinality acceptable** — All dimensions < 1,000,000 unique values (or plan bucketing)
- [ ] **Join cardinality verified** — No join explosions; row count after join ≈ base table rows
- [ ] **Query performance baseline documented**
  - Phase 2 (Workflow): < 30 seconds (daily aggregation)
  - Phase 3 (Non-Workflow): < 60 seconds (on-demand queries)
- [ ] **Comprehensive quality report completed** — All red flags reviewed and documented

→ **See `validation-queries.md` "Data Quality Gate" section** for parameterized SQL templates (Checks 1-12)

---

## THEN: Stage B Exit Quality Gates (MUST PASS ALL)

**After Data Quality Gate passes, verify Stage B discovery work is complete:**

### Extended Database Discovery Complete
- [ ] Stage A specified database searched
- [ ] Data gaps identified (if any)
- [ ] Extended search completed (other databases checked for missing metrics/dimensions)
- [ ] All possible data sources documented
- [ ] No "might be available" items carried forward (either confirmed or explicitly out of scope)

### Metrics Inferred & Validated
- [ ] Each Stage A metric has ONE confirmed definition (inferred from actual database queries)
- [ ] Definition matches reality (based on actual data, not estimate)
- [ ] Real sample value obtained from database (not rounded estimate)
- [ ] Example: "Email Open Rate = COUNT(DISTINCT user_id WHERE opened=true) / COUNT(DISTINCT user_id WHERE sent=true)"
- [ ] Exclusion rules validated in SQL (cancel-out % documented)
- [ ] Large table performance documented (if applicable)

### Recommended Metrics Identified
- [ ] Additional KPIs/metrics discoverable from same tables identified
- [ ] Recommendations presented to user with real sample values
- [ ] User has approved/declined recommended metrics
- [ ] Approved recommendations documented in `state.md`

### Dimensions Inferred & Validated
- [ ] Each Stage A dimension has INFERRED business definition (from data patterns)
- [ ] Real DISTINCT values obtained from database
- [ ] Definition matches data patterns (inferred, not assumed)
- [ ] Example: "Active Customer = Customer with ≥1 purchase in last 90 days (45% of base)"
- [ ] Join cardinality validated (no unexpected fan-out)
- [ ] Data quality checked (NULLs, unexpected values)

### Recommended Dimensions Identified
- [ ] Additional dimensions/filters discoverable from extended search identified
- [ ] Recommendations presented to user
- [ ] User has approved/declined recommended dimensions
- [ ] Approved recommendations documented in `state.md`

### Exclusion Rules Inferred & Recommended
- [ ] Recommended exclusions based on use case identified
- [ ] Exclusions presented to user with SQL validation
- [ ] User has approved/declined recommended exclusions
- [ ] All exclusion rules documented in `state.md`

### Metric Definition Ambiguities Resolved
- [ ] Any ambiguous metrics clarified (revenue type, active window, churn definition, etc.)
- [ ] Definition explicitly chosen or "show both versions" approved
- [ ] Definition documented in `state.md`; if still uncertain, resolve with the user directly before proceeding

### Snapshot vs Transactional Filter Scope Classified
- [ ] Each confirmed table classified as **Behavior** (has business event datetime), **Attribute** (entity state — no time column), **Snapshot** (point-in-time, no time column), or **Aggregate** (pre-aggregated output)
- [ ] **Time column summary produced** — for every behavior table: business event datetime column identified by name (e.g. `order_date`, `event_at`). TD system `time` column evaluated and confirmed as insert-time unless the user explicitly says otherwise.
- [ ] For tables with a `bigint` event datetime: epoch unit confirmed (seconds vs milliseconds) and conversion noted
- [ ] For each Snapshot table: dashboard-level Date Range / Channel / Category filters documented as **non-applicable** (silent pass-through)
- [ ] SINK table design accounts for Snapshot vs Transactional split (separate pre-aggregations where needed)

### Rendering Confirmed
- [ ] Rendering engine recorded as `HTML Client` (fixed — no selection needed)
- [ ] Performance baseline established (if large table) — Pattern A inlines data at build time, so very large record-level exports are a poor fit; flag and consider pre-aggregating harder in Phase 2

### state.md Updated (Stage A created, Stage B appends)
**Rule: `state.md` is CREATED in Stage A Step 1u with the Session Setup block. Stage B APPENDS a new Data Discovery block. Never overwrite prior content.**
- [ ] Session Setup block (Stage A) preserved — never edited
- [ ] Stage B Data Discovery block APPENDED (not overwriting Stage A)
- [ ] Database + tables documented
- [ ] Metric definitions (inferred) documented with real sample values
- [ ] Recommended metrics documented (with user decision: Add/Skip)
- [ ] Business definitions (inferred) documented
- [ ] Recommended dimensions + exclusions documented
- [ ] Data quality gate results documented
- [ ] Path decision recorded
- [ ] Dashboard Complexity Score retrieved from Stage A + recorded
- [ ] Updated `state.md` with Stage B Data Discovery block appended

### Stage A ↔ Stage B Alignment Verified
- [ ] All Stage A requirements addressed:
  - [ ] Stage A metrics found or alternative recommended
  - [ ] Stage A dimensions found or alternative recommended
  - [ ] Stage A filters found or alternative recommended
  - [ ] Data freshness acceptable
  - [ ] No blockers carried forward

### Path Decision Confirmed
- [ ] Dashboard Complexity Score retrieved from Stage A (0-6)
- [ ] Path routing decision made (Score + `skip_workflow` → Phase 2 or Phase 3)
- [ ] Path confirmed with user via AskUserQuestion
- [ ] Path decision recorded in `state.md`

---

## If ANY Gate Fails

| Gate | Action |
|------|--------|
| Extended discovery incomplete | Complete search across enterprise databases. Document all possible sources before proceeding. |
| Metric definition ambiguous | Clarify with user: choose ONE definition or approve "show both". Don't carry forward undefined. |
| Metric definition not inferred | Go back to database query. Infer definition from actual data structure + patterns. Not acceptable to use Stage A estimate. |
| Data gaps not documented | Document them NOW. Decide: (A) use alternative metric, (B) leave out, (C) ask the user. Don't carry forward. |
| Recommended metrics not presented | Present recommendations with real sample values. Get user approval/decline. Document in `state.md`. |
| `state.md` not created | Create NOW. This is your session memory + link to Phase 2/3. Mandatory. |
| Conflicting Stage A/B items | Document conflict in `state.md`. Resolve with the user before routing. |
| Pre-Phase 2/3 data quality check fails | Run `validation-queries.md` Checks 1-12. Fix critical issues (nulls, query timeout, fresh data, join cardinality) before proceeding to either Phase 2 or Phase 3. Document resolutions in `state.md`. |

---

## Path Routing Decision (Final Step)

After all gates pass:

1. **Retrieve Dashboard Complexity Score** from Stage A (`state.md` Session Setup block)
   - Score 0–2 → Phase 3 (Non-Workflow) — proceed directly
   - Score 3 → Ask user: "Quick build (Phase 3) or set up scheduled refresh first (Phase 2)?"
   - Score 4–6 → Phase 2 (Workflow) then Phase 3

   **Canonical routing logic lives in `stage-b-path-routing.md` Step 2f-5 — use that as the single source of truth for edge cases.**

2. **Confirm routing with user** using AskUserQuestion:
   ```
   AskUserQuestion:
     header: "Stage B Complete"
     question: "Discovery ready. Proceed to Phase 2 or Phase 3?"
     options:
       - label: "Yes — proceed"
         description: "Ready for the next phase"
       - label: "More questions"
         description: "Need clarification"
   ```

3. **Route to next phase:**
   - **Phase 2 (Workflow, Score 4-6):** proceed to `../../phase-2/deploy-workflow-guide.md`
   - **Phase 3 (Non-Workflow, Score 0-2, or `skip_workflow = true`):** proceed immediately to `../../phase-3/build-interactive-dashboard-guide.md`

---

## Session Handoff Notes (for future resumption)

If resuming this project in a future session:

1. **For Phase 2:** Read `./<project_name>/state.md` — it has all Stage B inferences. Proceed to Phase 2 workflow setup.
2. **For Phase 3:** Read `./<project_name>/state.md` — has inferred definitions + recommended additions. Proceed to Phase 3 dashboard build immediately.

---

## Artifact Checklist (to verify nothing was skipped)

Before marking Stage B complete, verify these are complete:

- [ ] `state.md` updated with Stage B Data Discovery block (all inferred definitions + recommendations)
- [ ] Dashboard Complexity Score from Stage A documented in `state.md`
- [ ] Rendering confirmed as HTML Client (recorded in Stage A)
- [ ] Path decision (Phase 2 or Phase 3) documented in `state.md`
- [ ] Data quality gate results documented in `state.md` (query performance baseline, null %, cardinality checks, freshness status)

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
