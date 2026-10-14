---
name: skill-architecture
description: Complete architecture showing how all instruction files, checklists, and walkthroughs work together
---

# Skill Architecture — Complete Reference

This document shows how all files in the skill work together to ensure instructions are consistently followed across all phases.

---

## File Structure Overview

```
fde-tais-dashboard-builder/
│
├── INSTRUCTIONS.md ← Read FIRST (load_order: 0 — master)
│   ├── 9 universal rules (all phases)
│   ├── Re-read protocol after context compaction
│   ├── Quick navigation table
│   └── If blocked checklist
│
├── SKILL.md (root)
│   └── Routes to correct phase
│
├── references/
│   ├── INSTRUCTIONS.md (load_order: 1 — cross-phase)
│   │   ├── 7 cross-phase guardrails
│   │   ├── Data integrity rules
│   │   ├── Query optimization
│   │   ├── Phase-specific constraints
│   │   └── "If instruction blocked" protocol
│   │
│   ├── guardrails-lite.md (legacy, still valid)
│   ├── treasure-data-theme.md
│   ├── [other references]
│   └── [existing walkthroughs]
│
├── phase-1/
│   ├── INSTRUCTIONS.md (load_order: 1.1)
│   │   ├── 9 Phase 1 specific rules
│   │   ├── Requirements validation patterns
│   │   ├── Dashboard Complexity Score calculation
│   │   ├── Phase 1 decision tree
│   │   ├── Common blocks + solutions
│   │   └── After Phase 1 completes section
│   │
│   ├── Quick Checklist in INSTRUCTIONS.md (quick reference)
│   │   ├── Prerequisites
│   │   ├── Stage A checklist
│   │   ├── Stage B checklist
│   │   ├── Scoring & path decision
│   │   ├── Quality gate
│   │   └── Next steps
│   │
│   ├── SKILL.md (full details)
│   │   ├── Load order reference
│   │   ├── Recommended model
│   │   ├── Pre-Phase 1 checklist
│   │   ├── Stage A (requirements)
│   │   ├── Stage B (data discovery)
│   │   ├── Dashboard Complexity Score calculation
│   │   ├── Phase routing decision
│   │   └── state.md creation
│   │
│   └── references/
│       ├── phase-1-walkthrough.md
│       │   ├── Step-by-step walkthrough
│       │   ├── Example inputs/outputs
│       │   ├── Troubleshooting
│       │   └── Advanced patterns
│       │
│       ├── steps-1pre.md
│       │   └── Setup questions (multi-select support)
│       │
│       ├── steps-1a-1o.md
│       │   ├── Common metrics reference
│       │   └── Requirements questions
│       │
│       ├── [other Phase 1 references]
│       └── [existing guides]
│
├── phase-2/
│   ├── INSTRUCTIONS.md (load_order: 1.2)
│   │   ├── 9 Phase 2 specific rules
│   │   ├── Approval gate template (MUST READ)
│   │   ├── Join validation procedures
│   │   ├── SINK naming convention
│   │   ├── Workflow SQL patterns
│   │   ├── Phase 2 decision tree
│   │   ├── Common blocks + solutions
│   │   └── After Phase 2 completes section
│   │
│   ├── Quick Checklist in INSTRUCTIONS.md
│   │   ├── Prerequisites from Phase 1
│   │   ├── TD account setup
│   │   ├── Workflow planning
│   │   ├── User approval gate
│   │   ├── Quality gate
│   │   └── Next steps
│   │
│   ├── SKILL.md (full details)
│   ├── references/
│   │   ├── phase-2-walkthrough.md
│   │   └── [other Phase 2 references]
│   └── [other Phase 2 files]
│
├── phase-3/
│   ├── INSTRUCTIONS.md (load_order: 1.3)
│   │   ├── 10 Phase 3 specific rules
│   │   ├── Query source decision tree
│   │   ├── Spot-check validation patterns
│   │   ├── Standalone HTML verification
│   │   ├── Interactive testing requirements
│   │   ├── Phase 3 decision tree
│   │   ├── Common blocks + solutions
│   │   └── After Phase 3 completes section
│   │
│   ├── Quick Checklist in INSTRUCTIONS.md
│   │   ├── Prerequisites
│   │   ├── Query readiness
│   │   ├── Dashboard scope
│   │   ├── Rendering setup
│   │   ├── Quality gate
│   │   └── Next steps
│   │
│   ├── SKILL.md (full details)
│   ├── references/
│   │   ├── phase-3-walkthrough.md
│   │   └── [other Phase 3 references]
│   └── [other Phase 3 files]
│
├── phase-4/
│   ├── INSTRUCTIONS.md (load_order: 1.4)
│   │   ├── 9 Phase 4 specific rules
│   │   ├── Track A (skill extraction) approval
│   │   ├── Track B (agent deployment) approval
│   │   ├── Skill parameterization patterns
│   │   ├── Agent KB accuracy validation
│   │   ├── Phase 4 decision tree
│   │   ├── Common blocks + solutions
│   │   └── After Phase 4 completes section
│   │
│   ├── Quick Checklist in INSTRUCTIONS.md
│   │   ├── Prerequisites
│   │   ├── Track A setup (if chosen)
│   │   ├── Track B setup (if chosen)
│   │   ├── Quality gate
│   │   └── Next steps
│   │
│   ├── SKILL.md (full details)
│   ├── references/
│   │   ├── phase-4-walkthrough.md
│   │   └── [other Phase 4 references]
│   └── [other Phase 4 files]
│
└── phase-5/
    ├── INSTRUCTIONS.md (load_order: 1.5)
    │   ├── 4 Phase 5 specific rules
    │   ├── Architecture.md template (with real info required)
    │   ├── Usage Guide.md template (with real info required)
    │   ├── Runbook.md template (with real info required)
    │   ├── Access & Ownership.md template (with real info required)
    │   ├── Phase 5 decision tree
    │   ├── Common blocks + solutions
    │   └── After Phase 5 completes section
    │
    ├── Quick Checklist in INSTRUCTIONS.md
    │   ├── Prerequisites
    │   ├── 4 documentation files to create
    │   ├── Content validation checklist
    │   ├── Quality gate before handoff
    │   └── Next steps (project complete)
    │
    ├── SKILL.md (full details)
    ├── references/
    │   ├── phase-5-walkthrough.md
    │   └── [other Phase 5 references]
    └── [other Phase 5 files]
```

---

## Reading Order (Load Order)

**When starting ANY phase or resuming after context compaction:**

```
Load Order 0 — MASTER (Read FIRST)
└─ ./INSTRUCTIONS.md
   - 9 universal rules
   - Re-read protocol
   - Phase reference index
   - Quick navigation

Load Order 1 — CROSS-PHASE (Read SECOND)
└─ ./references/guardrails-lite.md
   - 7 cross-phase guardrails
   - Data integrity rules
   - Rendering constraints
   - Phase-specific constraints

Load Order 1.N — PHASE-SPECIFIC (Read THIRD, where N=1-5)
├─ ./phase-N/INSTRUCTIONS.md
│  - 7-10 phase-specific rules
│  - Approval gate templates
│  - Decision trees
│  - Common blocks + solutions
│
├─ Quick Checklist in ./phase-N/INSTRUCTIONS.md (optional quick reference)
│  - Quick decision guide (2-3 min read)
│  - Prerequisites
│  - Quality gates
│
├─ ./phase-N/SKILL.md (full details — fallback reference)
│  - Complete phase walkthrough
│  - Edge cases
│  - Tips & tricks
│
└─ ./phase-N/references/phase-N-walkthrough.md (step-by-step)
   - Detailed walkthrough
   - Example inputs/outputs
   - Troubleshooting
   - Advanced patterns
```

---

## Re-Read Protocol (Critical After Context Compaction)

**When context is compacted/summarized:**

1. **STOP all activity**
2. **Re-read in order:**
   - `./INSTRUCTIONS.md` (load_order: 0)
   - `./phase-N/INSTRUCTIONS.md` (load_order: 1.N)
   - `./references/guardrails-lite.md` (load_order: 1)
3. **Verify** current phase from state.md
4. **Append checkpoint** to state.md (proof of re-read)
5. **Continue** with next action

**Proof-of-read template:**
```yaml
## Re-Read Checkpoint — [timestamp]

Context compaction occurred.
- ✓ Re-read ./INSTRUCTIONS.md (load_order 0)
- ✓ Re-read ./phase-N/INSTRUCTIONS.md (load_order 1.N)
- ✓ Re-read ./references/guardrails-lite.md (load_order 1)
- Ready to continue at: [next action]
```

---

## File Purposes & When to Use

| File | Purpose | When to Read | Load Order |
|------|---------|--------------|-----------|
| **INSTRUCTIONS.md** | Master rules for all phases | Before any phase | 0 (first) |
| **phase-N/INSTRUCTIONS.md** | Phase-specific rules | Before starting phase | 1.1-1.5 |
| **Quick Checklist in phase-N/INSTRUCTIONS.md** | Quick decision guide | When time is limited | — (optional) |
| **phase-N/SKILL.md** | Full phase details | When you need details | — (fallback) |
| **phase-N/references/phase-N-walkthrough.md** | Step-by-step walkthrough | New to phase | — (reference) |
| **references/guardrails-lite.md** | Cross-phase guardrails | After phase-specific rules | 1 (second) |

---

## Decision Trees Embedded in INSTRUCTIONS

Each INSTRUCTIONS.md includes a **decision tree** showing how to navigate that phase:

**Phase 1:** 
```
Gather Requirements (Stage A)
  ↓
Validate Against Data (Stage B)
  ↓
Calculate Dashboard Complexity Score (0-6)
  ↓
Route: Phase 1 → [Phase 2 or Phase 3]
```

**Phase 2:**
```
Validate Join Cardinality
  ↓
Plan Aggregation Logic
  ↓
Get Approval (SINK creation)
  ↓
Deploy Workflow + Test
  ↓
Proceed to Phase 3
```

**Phase 3:**
```
Decide Query Source (SINK or source tables)
  ↓
Write & Test Queries
  ↓
Execute Node Pipeline (query → render → HTML)
  ↓
Spot-Check KPIs
  ↓
Get User Approval
```

**Phase 4:**
```
Decide: Track A (skill), Track B (agent), or both?
  ↓
Get Approval (Track A or B)
  ↓
Execute Track(s)
  ↓
Finalize & Document
```

**Phase 5:**
```
Create 4 Documentation Files
  ├─ Architecture.md (data flow)
  ├─ Usage Guide.md (how to use)
  ├─ Runbook.md (operations)
  └─ Access & Ownership.md (permissions)
  ↓
Quality Gate (owner approval)
  ↓
Project Complete
```

---

## Approval Gates (Critical)

**Physical object creation requires explicit YES/NO:**

| Phase | Object | Gate Template |
|-------|--------|---------------|
| **Phase 2** | SINK tables | `📋 Ready to create SINK tables: [details]` |
| **Phase 2** | Workflow | Cost/scope/schedule approval |
| **Phase 4** | Skill | `📋 Ready to create skill: [details]` |
| **Phase 4** | Agent | `📋 Ready to deploy agent: [details]` |

**If user says NO or REVIEW:**
- STOP immediately
- Gather feedback
- Adjust plan
- Re-present

---

## Common Blocks & Solutions

Each INSTRUCTIONS.md includes a **"Common Blocks"** section with:

**Problem:** User says "I don't know my KPIs"
**Solution:** "Let's start with a metric you want to track. Common examples: Revenue, Customer Count, Churn Rate..."

**Problem:** "The data might not exist"
**Solution:** "Let's check! I'll run `tdx describe` on the table..."

**Problem:** "I'm not sure if the join will work"
**Solution:** "Perfect. Let me test it with: `SELECT COUNT(DISTINCT join_key)...`"

These are **tested solutions** from real implementations.

---

## Quality Gates Before Moving Forward

Each phase has a **Quality Gate** checklist before proceeding to the next phase:

| Phase | Before Proceeding | Gate |
|-------|------------------|------|
| **Phase 1** | Phase 2 or Phase 3 | All Stage A + B questions answered? Dashboard Complexity Score calculated? state.md created? |
| **Phase 2** | Phase 3 | SINK tables created? Workflow tested? First run successful? |
| **Phase 3** | Phase 4 (optional) | Dashboard approved? Spot-checks passed? Filters work? |
| **Phase 4** | Phase 5 (optional) | Skill/agent tested? KB accurate? End-to-end tests pass? |
| **Phase 5** | Handoff | All 4 docs created? Owner approved? Ready to share? |

---

## How Instructions Are "Sticky"

### Problem Being Solved
> "Claude skipped some instructions after context compaction. How do we prevent this?"

### Solution: Layered, Load-Ordered Instructions

1. **Master instructions (INSTRUCTIONS.md)** — Load order 0
   - Always read first
   - Referenced by every phase
   - Never gets skipped

2. **Re-read protocol** — Mandatory after compaction
   - Explicit checklist in state.md
   - Claude stops and re-reads master + phase files
   - Proof appended to state.md

3. **Inline checklists** — Not just at end
   - Embedded in flow (not summary list)
   - Decision points have inline checklist
   - Harder to skip than bottom-of-file checklist

4. **Phase-specific rules** — 7-10 per phase
   - Different rules per phase (not one-size-fits-all)
   - Clear "why" for each rule (past incidents)
   - Examples of what happens if violated

5. **Approval gates** — Physical objects
   - Explicit YES/NO template
   - Must appear before creation
   - Can't proceed without approval

---

## Integration Points

### state.md
- Created in Phase 1 with requirements
- Appended in Phase 2 with workflow details
- Appended in Phase 3 with dashboard details
- Appended in Phase 4 with automation details
- Appended in Phase 5 with documentation details
- **Serves as context bridge across phases**

### Each phase's INSTRUCTIONS.md
- References state.md for context
- Shows what to append to state.md
- Includes "Next Action" pointer
- Links to other phases (if applicable)

### Re-read protocol
- Uses state.md to identify current phase
- Re-reads master + phase instructions
- Appends checkpoint to state.md
- Resumes with clear "Next Action"

---

## Version & Updates

**Current Version:** 1.0.0 (Complete Architecture)
**Last Updated:** 22 July 2026

**Components:**
- ✅ Master INSTRUCTIONS.md (load_order: 0)
- ✅ Cross-phase INSTRUCTIONS.md (load_order: 1)
- ✅ Phase 1-5 INSTRUCTIONS.md (load_order: 1.1-1.5)
- ✅ Phase 1-5 Quick Checklists in INSTRUCTIONS.md (quick reference)
- ✅ Phase 1-5 SKILL.md (full details, updated with load order ref)
- ✅ Phase 1-5 walkthroughs (step-by-step)
- ✅ state.md template (context bridge)
- ✅ Re-read protocol (compaction safety)
- ✅ Approval gates (physical object safety)

---

## Quick Reference

**Starting a new engagement:**
```
1. Read: ./INSTRUCTIONS.md (load_order: 0)
2. Read: ./phase-1/INSTRUCTIONS.md (load_order: 1.1) — includes Quick Checklist
3. Refer: Quick Checklist section in ./phase-1/INSTRUCTIONS.md (quick decision guide)
4. Fallback: ./phase-1/SKILL.md (full details)
5. Walkthrough: ./phase-1/references/phase-1-walkthrough.md (step-by-step)
```

**After context compaction:**
```
1. STOP immediately
2. Re-read: ./INSTRUCTIONS.md
3. Re-read: ./phase-N/INSTRUCTIONS.md (where N = current phase)
4. Re-read: ./references/guardrails-lite.md
5. Verify current phase in state.md
6. Append checkpoint to state.md
7. Continue with "Next Action"
```

**Before creating any physical object:**
```
1. Read: Approval gate section in ./phase-N/INSTRUCTIONS.md
2. Present: Cost/scope/naming plan (use template)
3. Wait: Explicit YES/NO from user
4. If NO/REVIEW: Stop, gather feedback, re-present
5. If YES: Proceed with creation
```

---

This architecture ensures **no instructions are skipped** and **all guidelines are followed consistently** across all phases and contexts.
