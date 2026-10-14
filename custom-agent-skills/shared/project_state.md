---
name: shared-project-state
description: |
  Cross-session context store for an engagement. Defines the local `agent_outputs/<customer_slug>/<solution_slug>/project_state.md` file format and the rule that every resumed session reads it first. Used by custom-audience-agent.
---

# Shared: Project State

Engagements span multiple sessions. `agent_outputs/<customer_slug>/<solution_slug>/project_state.md` is the cross-session context store — a running summary of what's been done, the key decisions, and the paths of every artifact created. See `local_outputs.md` for the folder layout.

## Rules

1. **Create early.** `project_state.md` is the first file created for an engagement, before any customer-shareable docs.
2. **Update after every mode run** (setup, eval, segment push, docs, export): date, file status, key decisions, next action.
3. **Read first on resume.** When starting a new session, list existing engagements and read the matching file:
   ```bash
   ls agent_outputs/*/custom-audience-agent/project_state.md 2>/dev/null
   ```
   If several match, ask the user which one with `AskUserQuestion`. The "Current stage" + "Next Action" fields determine where to pick up.
4. **Authoritative.** When in doubt, the state file wins.
5. **Rewrite, don't append.** Update by re-rendering the whole file with the new values (use the Write tool), keeping Key Decisions cumulative.

## Template

```markdown
# Project State - Custom Audience Agent - <Customer>

Living context store. Update after every setup, eval, segment push, docs or export run. New sessions read this file first.

## Status
- **Current stage:** <setup drafted | customer review | context confirmed | live>
- **Last updated:** <YYYY-MM-DD>

## Project
- **Customer:** <name> (`<customer_slug>`)
- **TD account / site:** <tdx user + site>
- **Parent segment:** <name> (ID <parent_id>)
- **Output database:** cdp_audience_<parent_id>

## Files (paths relative to the working directory)
- Business context: agent_outputs/<customer_slug>/custom-audience-agent/business-context.md (<drafted | confirmed <date>>)
- Data dictionary: agent_outputs/<customer_slug>/custom-audience-agent/data-dictionary.md (<date>)
- Requirements doc: agent_outputs/<customer_slug>/custom-audience-agent/requirements.md (<pending | sent <date> | returned <date>>)
- Eval results: agent_outputs/<customer_slug>/custom-audience-agent/docs/eval_results.md (<pending | Round 1 <date> n% | Round 2 <date> n%>)
- Docs: agent_outputs/<customer_slug>/custom-audience-agent/docs/ (<pending | list>)
- Export: <pending | path + date>

## Pushed Segments
<none yet — name, folder, segment ID, Console link, date>

## Key Decisions
<none yet — append>

## Next Action
<one-sentence handoff for the next session>
```

## Update conventions

| Event | Update |
|---|---|
| Setup drafted | stage → setup drafted; parent segment, output DB, file dates |
| requirements.md shared | stage → customer review; requirements status "sent <date>" |
| Customer answers merged | stage → context confirmed; business-context "confirmed <date>"; changes in Key Decisions |
| Eval run | Eval results line (round, date, pass rate); open failures in Next Action |
| Segment pushed (with approval) | add to Pushed Segments |
| Docs / export written | file paths; stage → live after docs |
