# Phase 4: Automate & Deploy

**Entry Point:** After Phase 3 (Build + Validate Interactive Dashboard) is user-approved
**Continuation:** Same session from Phase 3, or resumed later using `state.md`
**Output:** (Track A) reusable, parameterized dashboard skill; (Track B) deployed companion Foundry agent

---

## Pre-Phase-4 Checklist

- ✅ Phase 3 complete: `dashboard.html` + `generate-data.js` approved by the user
- ✅ `state.md` accessible — read it for `project_name`, confirmed metrics/formulas, SINK or source database names, and the Phase 1 compliance flag (if any)
- ✅ Phase 4 Track A skill will be deployed to `~/.claude/skills/` (personal workspace for cross-session reuse)
- ✅ Phase 4 Track B agent will be deployed to Foundry

This phase is entirely optional. If the user doesn't need a reusable skill or a conversational agent, skip straight to Phase 5 (Handoff Documentation) or close the engagement.

---

## Template Sources

All templates this phase needs are already embedded locally — no external repo access required:

```bash
ls references/templates/
# knowledge-base-business-context-template.md
# knowledge-base-data-dictionary-template.md
# knowledge-base-metrics-dictionary-template.md
# knowledge-base-sql-templates-template.md
# agent-prompt-template.md
```

Track A copies the four knowledge-base templates into `./<project-name>/skills/knowledge/`. Track B copies `agent-prompt-template.md` into `./<project-name>/agents/system_prompt.md`. Exact copy commands are in `references/track-a-automation.md` and `references/track-b-ai-agent.md`.

---

## Phase 4 Compliance Gate (If Track B Planned)

Before deploying an agent, re-check the compliance flag captured in `state.md` during Phase 1 (Step 1l):

```
From state.md, Stage A Step 1l:

Compliance requirements:
  [ ] None flagged → proceed normally
  [ ] Yes: _____ (describe, e.g., "PII masking", "SOC2 audit logging")
```

**If compliance was flagged:** the mitigation (masking, audit logging, residency, row-level security) must be documented in the agent's `system_prompt.md` CRITICAL RULES before deploying — see `references/track-b-ai-agent.md` Step 4b-iii, Check 6.

---

## ⚠️ REQUIRED CHECKPOINT: Phase 3 → Phase 4 Transition Gate

**Before proceeding, confirm Phase 3 is complete:**

- ✅ Dashboard approved by user (in this session or from prior `state.md`)
- ✅ `dashboard.html` + `generate-data.js` are in `./<project-name>/dashboards/`
- ✅ `state.md` accessible with project_name, confirmed metrics, and database names

**If Phase 3 is NOT complete:** go back to Phase 3, complete the dashboard, and get user approval before continuing.

---

## Phase 4 Decision: Ask the User Which Tracks to Run

**This is the entry decision gate for Phase 4.** Do NOT skip this question. Make it explicit and unmissable:

```
AskUserQuestion:
  header: "Phase 4: Automate & Deploy (Choose Your Path)"
  question: "Your dashboard is approved! Phase 4 has two optional tracks. Which would you like to do?"
  options:
    - label: "Track A — Reusable Skill"
      description: "Extract as a reusable, parameterized skill for faster future builds (~10-30 min to replicate vs 2-3 hours from scratch). Standalone HTML dashboard others can deploy."
    - label: "Track B — Companion AI Agent"
      description: "Deploy a Foundry agent so users can ask questions in plain English about the dashboard data (e.g., 'What drove the spike?', 'Which region grew most?'). Requires Foundry access."
    - label: "Both Track A and Track B"
      description: "Extract the reusable skill AND deploy the Foundry agent (recommended for mission-critical dashboards)."
    - label: "Skip — go to Phase 5 or close"
      description: "No automation/deployment needed right now. Proceed to Phase 5 (Handoff Documentation) or close the engagement."
```

**After user selects, record the choice in state.md before proceeding to the track instructions.**

| Track | What it produces | Best for |
|---|---|---|
| **A — Reusable Skill** | `~/.claude/skills/<skill-name>/` — self-contained, parameterized skill available across all your Claude sessions + optional zip for sharing with team | Recurring dashboard builds, cross-project reuse, team standardization |
| **B — Companion Agent** | Foundry agent deployed with knowledge bases — conversational NL queries on dashboard data | Conversational NL queries, anomaly detection, scheduled reports |

---

## Track A: Quick Reference

| Step | What | Details |
|---|---|---|
| 4a-0 | Assemble knowledge package | `references/track-a-automation.md` § Step 4a-0 |
| 4a-i | Extract skill definition (`./<project-name>/skills/SKILL.md`) | `references/track-a-automation.md` § Step 4a-i |
| 4a-ii | Extract & parameterize query scripts | `references/track-a-automation.md` § Step 4a-ii |
| 4a-iii | Create configuration templates | `references/track-a-automation.md` § Step 4a-iii |
| 4a-iv | Document deployment & replication checklist | `references/track-a-automation.md` § Step 4a-iv |
| 4a-v | Validate the extracted skill end-to-end | `references/track-a-automation.md` § Step 4a-v |
| 4a-vi | Deploy skill to `~/.claude/skills/` (cross-session) + optional zip | `references/track-a-automation.md` § Step 4a-vi |
| 4a-vii | Generate Installation Guide (`INSTALL.md`) | `references/track-a-automation.md` § Step 4a-vii |

## Track B: Quick Reference

| Step | What | Details |
|---|---|---|
| 4b-i/ii | Decide on agent + choose capability | `references/track-b-ai-agent.md` § Step 4b-i & 4b-ii |
| 4b-iii | Pre-flight checks | `references/track-b-ai-agent.md` § Step 4b-iii |
| 4b-iv | Configure agent knowledge bases | `references/track-b-ai-agent.md` § Step 4b-iv |
| 4b-v | Deploy agent to Foundry | `references/track-b-ai-agent.md` § Step 4b-v |
| 4b-vi | Test agent with validation suite | `references/track-b-ai-agent.md` § Step 4b-vi |

---

## Key Reference Materials

| I want to... | See... |
|---|---|
| **Extract a reusable skill (Track A)** | [`references/track-a-automation.md`](references/track-a-automation.md) |
| **Deploy a companion agent (Track B)** | [`references/track-b-ai-agent.md`](references/track-b-ai-agent.md) |
| **Find the knowledge-base / agent-prompt templates** | [`references/templates/`](references/templates/) |
| **See all reference files** | [`references/INDEX.md`](references/INDEX.md) |

---

## Phase 4 Exit Quality Gates

**Track A (if run) — Quick Self-Check:**
- [ ] `skills/SKILL.md` exists and describes the execution flow (queries → data vars → render)
- [ ] `skills/knowledge/` has all 4 knowledge files with placeholders filled (not left as `[CUSTOMER_NAME]` etc.)
- [ ] `skills/dashboard.html` + `skills/generate-data.js` copied from the approved Phase 3 output
- [ ] Skill validated end-to-end against real data (Step 4a-v) — reproduces the Phase 3-approved dashboard within ±5% on all KPIs
- [ ] No hardcoded database names in `generate-data.js` — only env vars
- [ ] Full Step 4a-vi packaging instructions shown to the user (zip commands, install prompt) — never skipped

**Track B (if run) — Quick Self-Check:**
- [ ] `agents/system_prompt.md` ≤ 9,000 characters (`wc -c`)
- [ ] `agents/knowledge_bases/<table>.yml` (one per SINK table) uses `{name, td_query}` format, includes `confirmed_totals`
- [ ] Compliance flags from `state.md` (if any) reflected in `system_prompt.md` CRITICAL RULES
- [ ] `tdx agent test --run all` passing (or documented, understood exceptions)
- [ ] Agent verified in the Foundry UI

**Next:** Phase 5 (Handoff Documentation, optional) or close the engagement.

---

## Reference Directory

Start with [`references/INDEX.md`](references/INDEX.md) for the full file listing.

---

**Next Phase**

### ➡ Route to Phase 5 (Optional)
**Condition:** User wants local handoff docs
**Next:** `../phase-5/handoff-documentation-guide.md`

### ➡ Close (if no Phase 5)
Mark engagement complete. Share the final artifacts with the user: `dashboard.html`, the skill zip (if Track A ran), and/or the deployed Foundry agent (if Track B ran).

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
