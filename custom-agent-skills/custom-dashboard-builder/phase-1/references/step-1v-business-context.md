# Step 1v: Business Context, Data Dictionary, Requirements Doc

Runs at the end of Phase 1, **after** the dashboard plan and path are approved and before routing to Phase 2 or 3. It turns what Stage A and Stage B found into the two files the dashboard agent reads in every session (Phase 4), and gives the customer one questionnaire for everything still open. Do not run extra queries for it — use what is already recorded in `project_state.md`.

| File | Holds | Source |
|---|---|---|
| `agent_outputs/<project_slug>/business-context.md` | Business meaning and rules: goal, audience, glossary, metric definitions in business words, exclusion and compliance rules, naming, tone | Stage A answers (Setup-B goal, 1a–1j, 1h sharing / sensitivity, 1l compliance, business glossary, exclusion rules) |
| `agent_outputs/<project_slug>/data-dictionary.md` | Structure: tables, columns used, types, time column, confirmed values, data quality notes | Stage B discovery, Data Quality Gate, confirmed-values checkpoint |
| `agent_outputs/<project_slug>/requirements.md` | Customer questionnaire for every open or inferred item | The two files above |

## 1. Draft the files

Copy the skeletons from `<skill_dir>/project_templates/agent_template/references/` (never overwrite an existing engagement copy) and fill `{{project_name}}` and the database names:

```bash
d="agent_outputs/<project_slug>"
for f in business-context data-dictionary; do
  [ -f "$d/$f.md" ] || cp "<skill_dir>/project_templates/agent_template/references/$f.template.md" "$d/$f.md"
done
```

Follow each file's authoring rules:

- **Business context:** answer what the user confirmed in Stage A as plain facts (no marker). Answer what Stage B inferred from the data with confidence — category values, a status column that defines "completed", a test-account pattern — marked `[INFERRED — please confirm]`. Keep every other question under its section as `- [NEEDS YOUR INPUT] <question>`. Metric formulas are already user-confirmed in Stage A; add their business meaning ("Revenue excludes refunds") — the SQL detail goes to the metrics catalog in Phase 4.
- **Data dictionary:** fill it completely from Stage B — every table and column the dashboard uses, the event time column and timezone, confirmed dimension values, Data Quality Gate notes. Facts only, no markers.

## 2. Review with the user

Show one line per business-context section — what was taken from the answers, what was inferred, and the open questions — then ask with `AskUserQuestion`: "Looks right — continue (Recommended)" / "I'll add context now" / "Change assumptions". "Looks right" confirms the inferences: remove their markers. Write any other answer into the file (answers replace inferences; remove the marker of each answered item).

## 3. Requirements doc

Write `agent_outputs/<project_slug>/requirements.md` from `<skill_dir>/references/requirements_doc.md` (title `<Project Name> Requirements`): one section per business-context heading that still has open or inferred items, the drafted answer, and `> _Your answer:_`. It must read as a clean customer questionnaire — no notes on how it was drafted. Tell the user in one line: its path, that it is plain markdown to share in any format, and that the filled version must be saved back to the same path. **Do not wait for the answers** — continue to Phase 2 or 3.

## 4. Record

Append to `project_state.md` (Phase 1 ledger): business context "drafted / reviewed `<date>`", data dictionary written, requirements "sent `<date>`"; update the header's Next Action.

**When the customer returns `requirements.md`** (any later session): merge each answer into `business-context.md` (customer answers replace inferences; remove the marker of each answered item), show the user a summary of the changes, record it in `project_state.md`, then rebuild the dashboard agent (Phase 4 Step 3) and run a new evaluation round (Phase 5). If an answer changes a metric definition or filter, update the dashboard first (Phase 3 change loop).
