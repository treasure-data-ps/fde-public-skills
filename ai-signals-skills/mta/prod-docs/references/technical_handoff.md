# Phase 5: Information Gathering

Collect all information needed to generate the technical hand-off documentation for MTA Model. Write the resulting files to `agent_outputs/<customer_slug>/mta/docs/` (`docs/runbook.md`, `docs/access_ownership.md`) following `../../../shared/customer_docs_pattern.md`.

## Step 1: Locate the Engagement Files

Read `../../../shared/local_outputs.md` for the folder layout. MTA-specific values:

- **Solution slug:** `mta`
- **Engagement folder:** `agent_outputs/<customer_slug>/mta/`

Read `agent_outputs/<customer_slug>/mta/project_state.md` first to recover the TD workflow project name, sink database, and artifact paths.

## Step 2: Check for Existing MTA Docs

Ask the user:

> Do you have existing filled-out technical hand-off docs for this engagement? If yes, give me the file path (or paste the contents).

Also check `agent_outputs/<customer_slug>/mta/requirements.md` and `agent_outputs/<customer_slug>/mta/docs/`. If anything is available, extract whatever configuration details it contains (database, tables, columns, conversion definition, etc.). Use the extracted values to pre-fill later steps, but still validate everything through auto-discovery. The deployed config itself is in `agent_outputs/<customer_slug>/mta/workflow/mta_journey_agent/config/input_params.yml`.

## Step 3: Initial Questions

Collect answers to these questions before exploring any data. These determine the information you will use in your hand-off.

### 3a: Data Information

Ask: **What is the name of the database where the mta tables live?**

