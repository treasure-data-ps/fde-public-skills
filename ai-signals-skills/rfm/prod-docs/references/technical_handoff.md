# Phase 5: Information Gathering — Technical Handoff

Collect all information needed to generate the technical hand-off documentation for the RFM Customer Segmentation model. The documentation files are written locally to `agent_outputs/<customer_slug>/rfm/docs/` — see `../../../shared/customer_docs_pattern.md` for the file set and `../../../shared/local_outputs.md` for the folder layout.

This reference feeds: `docs/runbook.md`, `docs/access_ownership.md` (audience: internal).

## Step 1: Recover the Engagement Context

Read these local files first — they hold most of what the docs need:

| Source | What to extract |
|---|---|
| `agent_outputs/<customer_slug>/rfm/project_state.md` | Customer name, TD account / region, TD workflow project name, sink database, Parent Segment, key decisions |
| `agent_outputs/<customer_slug>/rfm/requirements.md` | Customer-confirmed answers: ID column, source tables, monetary metric, time filter, scoring bins, business rules |
| `agent_outputs/<customer_slug>/rfm/workflow/rfm_agent/config/input_params.yml` | The deployed configuration (source tables, filters, `num_bins`, archive / historical score settings) |

If `project_state.md` does not exist, ask the user for the customer name and look for `agent_outputs/*/rfm/project_state.md` before continuing.

## Step 2: Check for Existing Docs

If `agent_outputs/<customer_slug>/rfm/docs/` already contains files, read them and ask the user whether to regenerate or update them in place. Use any configuration details they contain to pre-fill later steps, but still validate everything against the deployed config and output tables.

## Step 3: Initial Questions

Collect answers to any of these that are not already answered by the files in Step 1, before exploring any data.

### 3a: Data Information

Ask: **What is the name of the database where the RFM tables live?** (default: the `sink_database` from `project_state.md`)
