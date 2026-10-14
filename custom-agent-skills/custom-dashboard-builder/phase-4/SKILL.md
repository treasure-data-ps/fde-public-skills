---
name: fde-tais-dashboard-builder-phase-4
description: INTERNAL — Phase 4 only. Optional: extract reusable skill (Option A - Recommended) or deploy Foundry agent (Option B - external API access only).
---

# Phase 4: Automate & Deploy (FDE TAIS Dashboard Builder)

> **Read in this order:**
> 1. `../INSTRUCTIONS.md` (master rules, load_order: 0)
> 2. `../references/execution-contract.md` (non-skippable execution gates)
> 3. `./INSTRUCTIONS.md` (Phase 4 rules, load_order: 1.4) — includes Quick Checklist
> 4. `./SKILL.md` (this file — full details)
> 5. `./references/phase-4-walkthrough.md` (step-by-step walkthrough)
> 6. `../references/guardrails-lite.md` (cross-phase guardrails)

**Phase Goal:** Optionally turn the approved dashboard into a reusable asset — Option A packages it as a skill for `~/.claude/skills/` (cross-session reuse, recommended), Option B deploys a companion Foundry agent for external API access. Both are entirely optional; skip this phase to go straight to Phase 5 (Handoff) or close the engagement.

**Deliverable (Option A):** Skill installed to `~/.claude/skills/<skill-name>/` — a self-contained, reusable dashboard skill (HTML Client only) available across all Claude Code sessions + optional zip file for sharing
**Deliverable (Option B):** Foundry agent deployed with knowledge bases (external API access only)

---

## Entry Condition

- ✅ Phase 3 complete: `dashboard.html` + `generate-data.js` approved by the user
- ✅ `state.md` accessible — read it for `project_name`, confirmed metrics, SINK/source database names, and the Phase 1 compliance flag (if any)

**If the user doesn't need automation or an agent:** skip this phase entirely — go to Phase 5 (Handoff Documentation, optional) or close the engagement.

---

## How to Execute

**Quick start:** See Quick Checklist in `./INSTRUCTIONS.md` for a fast gate-check before proceeding.

Ask the user which option(s) to run. Then follow the detailed guides:

- **Option A (Recommended):** [`references/track-a-automation.md`](references/track-a-automation.md) — Steps 4a-0 through 4a-vii (skill extraction)
- **Option B:** [`references/track-b-ai-agent.md`](references/track-b-ai-agent.md) — Steps 4b-i through 4b-vi (Foundry agent deployment - external API only)

---

## Quality Gates

✅ Option A (if run): skill validated end-to-end against real data, packaged, and the full Step 4a-vi packaging instructions shown to the user (zip commands, install prompt) — never skipped, even if a zip already exists
✅ Option B (if run): `system_prompt.md` ≤ 9,000 characters, all 5 validation tests passing (or documented exceptions), agent deployed and verified in the Foundry UI
✅ `state.md` updated (append only) with option(s) run and their outputs

---

## Next Phase

### ➡ Route to Phase 5 (Optional)
**Condition:** User wants local handoff docs
**Next:** `../phase-5/handoff-documentation-guide.md`

### ➡ Close (if no Phase 5)
Mark engagement complete, share the final artifacts (`dashboard.html`, skill zip, and/or Foundry agent).

---

**Version:** 1.0.0
**Last Updated:** 23 July 2026
**Author:** FDE Team
