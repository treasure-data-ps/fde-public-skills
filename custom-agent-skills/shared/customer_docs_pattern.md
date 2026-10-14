---
name: shared-customer-docs-pattern
description: |
  Documentation set for an audience-agent engagement, written as local markdown files to `agent_outputs/<customer_slug>/custom-audience-agent/docs/`. Defines the standard doc files (Architecture, Behavior, Eval Results, Runbook, Access & Ownership), their create order, and when to regenerate each. Used by custom-audience-agent Docs mode.
---

# Shared: Customer-Specific Documentation Pattern

Docs mode writes the documentation set to `agent_outputs/<customer_slug>/custom-audience-agent/docs/` (see `local_outputs.md`).

## When to use

After the customer's answers are merged into `business-context.md` and an eval round has been run — or whenever the user asks for handoff docs.

## Prerequisites

Read first: `project_state.md`, the customer's `business-context.md` and `data-dictionary.md`, `docs/eval_results.md` (if present), and `requirements.md`.

## Audience header

Each doc starts with a one-line audience marker so the user knows what can be shared as-is:

```markdown
> Audience: customer        ← safe to share with customer stakeholders
> Audience: internal        ← operator notes; review before sharing
```

Doc titles inside each file: `# Audience Agent <Doc Name> - <Customer>`.

## The Docs

| # | File | Audience | Content |
|---|---|---|---|
| 1 | `docs/architecture.md` | customer | Parent segment (name, ID, output database); tables in scope (`customers` + behavior tables); how the agent works (Claude skill + local context files + `tdx` CLI, read-only by default; segments pushed only on approval); where context files live |
| 2 | `docs/behavior.md` | customer | Plain-English summary of what the agent knows for THIS customer: business model, key terms, priority attributes, naming conventions, exclusion rules, output preferences. No YAML/JSON |
| 3 | `docs/eval_results.md` | customer | Written by Eval mode — see `../custom-audience-agent/references/eval.md` Results Format. Docs mode only checks it is current |
| 4 | `docs/runbook.md` | internal | How to resume (session start), refresh the data dictionary after parent-segment changes, re-run setup or eval, update context after customer feedback, export the standalone skill; common failure modes → which file to edit |
| 5 | `docs/access_ownership.md` | internal | Agent owner, customer stakeholders, support contact, tdx account/site used, location of the engagement folder, escalation path for platform issues |

## Create Order

1. Write the doc files with the Write tool (skip `eval_results.md` if Eval mode already wrote it; if it is missing, offer to run Eval first).
2. Reference the other docs and `../requirements.md` by relative path so navigation works when the folder is shared.
3. Update `project_state.md`: list the doc paths; stage → live.
4. Tell the user the `docs/` path and which files are customer-facing.

## Keeping Docs Current

| Doc | When to regenerate |
|---|---|
| Eval Results | After each eval round |
| Behavior | Whenever business-context.md changes materially |
| Architecture | When the parent segment or tables in scope change |
| Runbook | When the operating procedure changes |
| Access & Ownership | When ownership or access changes |
