# Phase 4 References Directory

This directory contains detailed, reusable patterns for Phase 4: Automate & Deploy.

**Main file:** `../automate-deploy-guide.md` (the entry point — start here)

---

## Directory Structure

```
phase-4/references/
├── track-a-automation.md                    ← Track A step-by-step instructions (entry point)
├── track-b-ai-agent.md                      ← Track B step-by-step instructions (entry point)
└── templates/                               ← Embedded local templates (no external repo access needed)
    ├── knowledge-base-business-context-template.md
    ├── knowledge-base-data-dictionary-template.md
    ├── knowledge-base-metrics-dictionary-template.md
    ├── knowledge-base-sql-templates-template.md
    └── agent-prompt-template.md
```

All templates this phase needs are embedded locally in `templates/` — nothing is fetched from an external repository at runtime.

---

## How to Use These Files

### I'm implementing Phase 4 — where do I start?
→ Open `../automate-deploy-guide.md` (the main file with quick reference)

### I want to automate the dashboard as a reusable skill (Track A)
→ See [`track-a-automation.md`](track-a-automation.md) for step-by-step instructions
→ Copy knowledge-base templates from `templates/` and fill in all placeholders

### I want to deploy an AI agent (Track B)
→ See [`track-b-ai-agent.md`](track-b-ai-agent.md) for step-by-step instructions
→ Copy `templates/agent-prompt-template.md` and fill in all placeholders

---

## Quick Decision Guide

| User Needs | Choose |
|---|---|
| Will build this dashboard again for other databases | **Track A** (Automation) |
| Users ask frequent questions about metrics | **Track B** (AI Agent) |
| Strategic dashboard, will be reused + NL access needed | **Both** |
| One-off dashboard, no reuse plans | **Neither** (skip to Phase 5 or close) |

---

## Track A Output

✅ Dashboard skill definition (parameterized)
✅ Query script (`generate-data.js`) with env-var parameters
✅ Configuration templates (weekly, monthly, annual)
✅ Deployment & replication checklist

**Result:** future builds take ~10-30 minutes instead of 2-3 hours

---

## Track B Output

✅ Foundry agent deployed
✅ All 5 validation tests passed
✅ Knowledge bases configured
✅ Users can ask NL questions

**Result:** instant insights, reduced support load

---

## Timeline

- **Track A alone:** ~1-1.5 hours
- **Track B alone:** ~1-2 hours
- **Both tracks:** ~2-3.5 hours
- **Neither:** 0 hours (proceed to Phase 5 or close)

---

## Related Files

- `../../phase-3/build-interactive-dashboard-guide.md` — Phase 3 output (user-approved dashboard)
- `../../phase-5/handoff-documentation-guide.md` — Next phase (optional handoff docs)

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
