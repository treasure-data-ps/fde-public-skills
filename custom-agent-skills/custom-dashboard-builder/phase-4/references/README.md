# Phase 4 References

Reference files for Phase 4: Automate & Deploy

## Quick Navigation

| Reference File | Purpose | When to Use |
|---|---|---|
| **track-a-automation.md** | Track A step-by-step guide | Track A: automating the dashboard for faster future builds |
| **track-b-ai-agent.md** | Track B step-by-step guide | Track B: deploying a companion Foundry AI agent |
| **templates/** | Embedded local templates (knowledge base + agent prompt) | Both tracks: source files to copy and fill in |

## Phase 4 Quick Start

### Track A: Dashboard Automation (4a-0 through 4a-vii)

**Goal:** Extract the Phase 3 dashboard as a reusable skill for faster future builds

**Timeline:** ~1-1.5 hours

**Steps:**
1. **Step 4a-0:** Assemble knowledge package (10 min) → Copy knowledge-base templates from `templates/` locally; fill in placeholders from Phase 1-3 artifacts
2. **Step 4a-i:** Extract skill definition (10 min) → See `track-a-automation.md` § "Step 4a-i"
3. **Step 4a-ii:** Parameterize queries (15 min) → See `track-a-automation.md` § "Step 4a-ii"
4. **Step 4a-iii:** Create config templates (10 min) → See `track-a-automation.md` § "Step 4a-iii"
5. **Step 4a-iv:** Document deployment checklist (10 min) → See `track-a-automation.md` § "Step 4a-iv"
6. **Step 4a-v:** Validate extracted skill end-to-end (10 min) → Run `generate-data.js` against the target database, spot-check `data.json`, reproduce the dashboard
7. **Step 4a-vi:** Package & share skill → Zip the `skills/` folder (excluding `data.json`, `.DS_Store`, `__MACOSX`)
8. **Step 4a-vii:** Generate Installation Guide (`INSTALL.md`) (5 min) → See `track-a-automation.md` § "Step 4a-vii"; include it in the packaged zip

**Output:** Dashboard skill + query script + templates + checklist + `INSTALL.md` (ready for the next build)

---

### Track B: Deploy Companion AI Foundry Agent (4b-i through 4b-vi)

**Goal:** Deploy a Foundry agent for conversational dashboard access

**Timeline:** ~1-2 hours

**Steps:**
1. **Step 4b-i/ii:** Decide + choose capability (15 min) → See `track-b-ai-agent.md` § "Step 4b-i & 4b-ii"
2. **Step 4b-iii:** Pre-flight checks (5 min) → See `track-b-ai-agent.md` § "Step 4b-iii"
3. **Step 4b-iv:** Configure KB (15 min) → Copy `templates/agent-prompt-template.md` locally and fill all placeholders; see `track-b-ai-agent.md` § "Step 4b-iv" for the full KB checklist
4. **Step 4b-v:** Deploy to Foundry (10 min) → See `track-b-ai-agent.md` § "Step 4b-v"
5. **Step 4b-vi:** Run test suite (15 min) → See `track-b-ai-agent.md` § "Step 4b-vi" for all 5 tests

**Output:** Foundry agent deployed + all tests passing ✅

---

## Which Files Do I Need?

### If doing **Track A only** (Automation):
- Read: `track-a-automation.md`
- Templates: `templates/knowledge-base-*.md`
- Time: ~1-1.5 hours

### If doing **Track B only** (AI Agent):
- Read: `track-b-ai-agent.md`
- Templates: `templates/agent-prompt-template.md`
- Time: ~1-2 hours

### If doing **Both Tracks** (Automation + AI Agent):
- Read: both step guides + both template sets
- Time: ~2-3.5 hours

---

## FAQ

**Q: What's the difference between Track A and Track B?**

**A:**
- **Track A (Automation):** Makes the dashboard faster to build again against a new database
- **Track B (AI Agent):** Makes the dashboard easier to use (conversational queries)
- Both are optional and complementary

**Q: Which capability should I choose for Track B?**

**A:** Start with **Insights** (recommended) — fastest to deploy, most flexible, lowest cost. Add other capabilities later via intent-routing without re-deploying.

**Q: How long does this take?**

**A:**
- Track A: ~1-1.5 hours
- Track B: ~1-2 hours
- Both: ~2-3.5 hours total

**Q: Can I do Track A without Track B?**

**A:** Yes — they're independent. Choose based on need.

**Q: What if agent tests fail?**

**A:** See `track-b-ai-agent.md` § "Failure-to-Fix Quick Reference". Common fixes:
- Update the per-table `.yml` file(s) in `knowledge_bases/` with correct table names
- Expand `business_context.md` with more examples
- Verify queries in knowledge bases match Phase 3 queries

---

## Next Steps

**Phase 4 complete:**
→ Proceed to **Phase 5: Handoff Documentation** (optional — see `../../phase-5/handoff-documentation-guide.md`), or close the engagement.

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
