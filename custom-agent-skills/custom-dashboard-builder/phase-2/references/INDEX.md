# Phase 2 References Directory

Detailed, reusable patterns for Phase 2: Deploy Dashboard Workflow.

**Entry point:** `../deploy-workflow-guide.md` — start here for the 8-step overview and starting-point (locally embedded templates).

---

## Reference Files

| File | Purpose |
|---|---|
| **[phase-2-entry-requirements.md](phase-2-entry-requirements.md)** | Extract 5 configuration fields from `state.md` before Phase 2 begins |
| **[workflow-setup-configure.md](workflow-setup-configure.md)** | Steps 2a–2d: set up, configure `input_params.yaml`, SQL patterns, schedule, datamodel |
| **[workflow-deployment-validate.md](workflow-deployment-validate.md)** | Steps 2e–2h: pre-deploy review, deployment, SINK validation, incremental strategy |
| **[td-time-functions.md](td-time-functions.md)** | `td_time_range()`, `TD_SCHEDULED_TIME()`, `TD_TIME_ADD()` and incremental mode decisions |
| **[incremental_update_patterns.md](incremental_update_patterns.md)** | `INSERT INTO` examples per incremental mode; upsert patterns |
| **[input_params_examples.md](input_params_examples.md)** | Worked `input_params.yaml` examples for 5 verticals |
| **[pre-deployment-checklist.md](pre-deployment-checklist.md)** | Go/no-go checklist before `tdx wf push` |
| **[testing-troubleshooting.md](testing-troubleshooting.md)** | Testing, troubleshooting, and performance tuning guide |
| **[workflow-templates/](workflow-templates/)** | Embedded workflow template: `.dig` files, SQL, `input_params.yaml` |

---

## Quick Navigation by Step

| Step | File |
|---|---|
| Phase 2 entry requirements (read Stage A/B config) | `phase-2-entry-requirements.md` |
| 2a. Set up project (copy embedded template) | `workflow-setup-configure.md` + `workflow-templates/` |
| 2b. Configure `input_params.yaml` | `workflow-setup-configure.md` + `input_params_examples.md` |
| 2c. Customize SQL (aggregation patterns) | `workflow-setup-configure.md` (SQL Aggregation Patterns section) |
| 2c. Configure schedule | `workflow-setup-configure.md` (Schedule Configuration section) |
| 2c. TD time functions | `td-time-functions.md` |
| 2c. Incremental INSERT INTO patterns | `incremental_update_patterns.md` |
| 2d. Configure `config.json` datamodel (optional) | `workflow-setup-configure.md` (Datamodel Design Principles section) |
| 2e. Review configuration | `workflow-deployment-validate.md` + `pre-deployment-checklist.md` |
| 2f. Deploy workflow | `workflow-deployment-validate.md` |
| 2g. Validate SINK tables | `workflow-deployment-validate.md` (SINK Table Documentation Template section) |
| 2h. Incremental strategy + test | `workflow-deployment-validate.md` (Step 2h section) |
| Troubleshooting | `testing-troubleshooting.md` |
| Performance tuning | `testing-troubleshooting.md` (Performance Tuning section) |

---

## Phase 2 Output Summary

At end of Phase 2:
- ✅ Template configured with all Stage B metrics, source tables, and exclusion filters
- ✅ Workflow deployed and first historical run complete
- ✅ Incremental mode chosen (append-only / 1-day / 7-day lookback), if applicable
- ✅ All SINK tables validated (row counts, metric cross-checks, no duplicates)
- ✅ Workflow running on schedule (all sub-workflows SUCCESS)
- ✅ Ready for Phase 3 (dashboard queries SINK tables, not source tables)

---

## Related Skills

- `workflow-skills:digdag` — Digdag `.dig` syntax, operators, session variables
- `sql-skills:trino` — TD Trino SQL patterns and TD-specific functions
- `sql-skills:trino-optimizer` — `APPROX_DISTINCT`, CTAS, performance patterns
- `sql-skills:time-filtering` — `td_time_range()`, `TD_SCHEDULED_TIME()`, `TD_TIME_ADD()` reference
---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
