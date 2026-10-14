---
name: fde-tais-dashboard-builder-phase-5
description: INTERNAL — Phase 5 only. Optional: create 4 local handoff documentation files.
---

# Phase 5: Handoff Documentation (FDE TAIS Dashboard Builder)

> **Read in this order:**
> 1. `../INSTRUCTIONS.md` (master rules, load_order: 0)
> 2. `../references/execution-contract.md` (non-skippable execution gates)
> 3. `./INSTRUCTIONS.md` (Phase 5 rules, load_order: 1.5) — includes Quick Checklist
> 4. `./SKILL.md` (this file — full details)
> 5. `./references/phase-5-walkthrough.md` (step-by-step walkthrough)
> 6. `../references/guardrails-lite.md` (cross-phase guardrails)

**Phase Goal:** Create 4 local markdown documentation files that enable the user's team to use, maintain, and support the dashboard independently — then formally close the engagement.

**Deliverable:** 4 local markdown files (2 user-facing, 2 internal/maintainer) + `state.md` updated + files shared

---

→ **See `./references/phase-5-walkthrough.md`** for: Pre-Phase extraction checklist, approval gate, file templates for all 4 docs, `state.md` append block, sharing step, and engagement complete.

---

## Custom Dashboard-Specific Phase 5 Notes

### Data to Extract for Each File

All 4 files are populated from prior phase artifacts — no new research required:

**For all files:**
- Dashboard name and project name (Phase 1, Stage A)
- Phase 1 Stage B Step 2a–2d (confirmed database, tables, metrics, dimensions)
- Rendering is always HTML Client — no engine choice to document (Phase 1 Stage B Step 2e is a no-op)
- Phase 2 (if Workflow path): SINK database, schedule, workflow project name, `config.json`
- Phase 3 Step 4j (technical parameters: query performance, metrics table)
- Phase 4 (if chosen): Track A skill path or Track B agent details

**Architecture file specifics:**
- Use table format for metrics (from Phase 3 Step 4j)
- Include exclusion rules in SQL format (Phase 1 Stage A Step 1o)
- Document SINK tables if Workflow path (Phase 2 `config.json`)
- Reference Phase 4 artifacts if automation/agent were deployed

**Usage Guide specifics:**
- List each filter with default value (Phase 1 Stage A Step 1e+1f for date range, Step 1c+1d for dimensions)
- Include metric definitions and formulas (Phase 1 Stage A Step 1b glossary + Phase 3 metrics)
- Add FAQ section based on Phase 1 Stage A Step 1h audience + known questions
- Explain export options (if supported — noted in Phase 1 Stage A Step 1c+1d)

**Runbook specifics:**
- Weekly/monthly maintenance checklist (based on path: Non-Workflow = manual refresh, Workflow = automated)
- Include common issues table with resolution steps (reference Phase 3 testing)
- Add escalation contacts (dashboard owner + data platform team, if applicable)
- Document re-deployment commands (from Phase 3 Step 4e / Phase 4 Step 4a-vi packaging, if Track A was run)

**Access & Ownership specifics:**
- Primary users from Phase 1 Stage A Step 1h + user count
- Support channel + response expectations
- Escalation path (L1 usage questions → L2 data issues → L3 platform issues)
- Compliance notes if Phase 1 Stage A Step 1l flagged (PII, data sensitivity, regulatory)

### File Naming & Visibility

**User-facing files (share with the requesting team/stakeholders):**
- `./<project-name>/docs/architecture.md`
- `./<project-name>/docs/usage_guide.md`

**Internal/maintainer files (keep with whoever owns upkeep):**
- `./<project-name>/docs/runbook.md`
- `./<project-name>/docs/access_ownership.md`

**Important:** When sharing (Step 5d), **share only the two user-facing files**. Keep the runbook and access/ownership doc with the maintainer.

---

**Version:** 1.0.0
**Last Updated:** 23 July 2026
**Author:** FDE Team
