---
name: shared-customer-agent-pattern
description: |
  Generic mechanics for turning a solution's agent template (`project_templates/agent_template/`) into a customer-specific Claude skill in the Work Folder's `.claude/skills/<agent-name>/`: name gate, placeholder filling, draft vs. final, git-ignore guard, verification. The solution's `references/agent-setup.md` supplies the "what". Used by every solution under ai-signals-skills/.
---

# Shared: Customer Agent Pattern

Each solution ships a **blueprint** of its analysis agent in `<solution_dir>/project_templates/agent_template/`. It is never used directly. During an engagement it is copied into the user's Work Folder as a customer-specific skill:

```
<working directory>/.claude/skills/<agent-name>/
├── SKILL.md          # from agent_template/SKILL.template.md, placeholders filled
├── .gitignore        # "*" — the agent holds customer context; never committable
└── references/       # template references + customer files added at finalize time
```

A skill in the Work Folder's `.claude/skills/` is loaded in every chat in that folder (Treasure AI Studio lists it under the folder's Actions and Skills; in Claude Code it is a project skill). It can later be shared to the account with Studio's Develop → Share — keep every file ≤ 1 MB.

The solution's `references/agent-setup.md` lists the placeholders, the extra files to add, and solution-specific checks.

## When

| Stage | When | Result |
|---|---|---|
| **Draft** | Right after the first validated workflow run (end of Phase 3) | Agent can query the real output tables and build dashboards during Phase 4 |
| **Finalize** | Phase 5, after the documentation set is written | Agent carries the confirmed business context, the as-built workflow guide, the setup walkthrough and the runbook |

Re-run **Finalize** whenever the workflow config, business context or docs change materially.

## Step 1: Name gate (draft only)

Default name: `<customer_slug>-<solution_slug>-agent` (e.g. `acme-rfm-agent`). Ask with `AskUserQuestion`: "Use `<default>` (Recommended)" / "Use a different name". Names: lowercase letters, digits, hyphens. If `.claude/skills/<name>/` already exists for a different engagement, ask before overwriting. Record the name in `project_state.md`.

## Step 2: Build the agent in a staging folder

Never copy an unfilled template into `.claude/skills/` — anything there is live immediately.

```bash
stage="agent_outputs/<customer_slug>/<solution_slug>/agent_build/<agent-name>"
mkdir -p "$stage"
cp -R "<solution_dir>/project_templates/agent_template/." "$stage/"
mv "$stage/SKILL.template.md" "$stage/SKILL.md"
rm -f "$stage"/references/*.template.md   # finalize-time skeletons — filled in Step 4, never installed unfilled
```

Fill every `{{placeholder}}` in the **`.md` files** of `$stage` (Edit/Write tools) from `project_state.md`. Never edit scripts or HTML (`*.js`, `*.html`, …): they are copied verbatim and their `{{…}}` tokens are runtime tokens filled by the script itself. At minimum:

| Placeholder | Value |
|---|---|
| `{{agent_name}}` | confirmed agent name (also the frontmatter `name:`) |
| `{{customer_name}}` / `{{customer_slug}}` | customer |
| `{{sink_database}}` | confirmed sink database (output tables live here) |
| `{{engagement_dir}}` | `agent_outputs/<customer_slug>/<solution_slug>` |

plus the solution-specific placeholders in `references/agent-setup.md`. Then check none remain:

```bash
grep -rn --include='*.md' '{{' "$stage" && echo "UNFILLED PLACEHOLDERS — fix before installing"
```

## Step 3: Install

```bash
mkdir -p .claude/skills
rm -rf ".claude/skills/<agent-name>.new" && cp -R "$stage" ".claude/skills/<agent-name>.new"
printf '*\n' > ".claude/skills/<agent-name>.new/.gitignore"
rm -rf ".claude/skills/<agent-name>" && mv ".claude/skills/<agent-name>.new" ".claude/skills/<agent-name>"
```

## Step 4: Finalize (Phase 5)

Add the customer files listed in `references/agent-setup.md` to the staging folder, update `SKILL.md`'s file list, then repeat Steps 2 (placeholder check) and 3. Every solution adds at least:

| File | Built from | Answers |
|---|---|---|
| `references/workflow-guide.md` | `agent_template/references/workflow-guide.template.md` | How the deployed workflow works end to end (pipeline, config, mappings, customizations, output tables) |
| `references/model-setup-walkthrough.md` | `agent_template/references/model-setup-walkthrough.template.md` | What was decided and done during setup (discovery, requirements, decision log, cleaning, validation baseline, artifacts, presentation recipe, accuracy rules) |
| `references/customer-context.md`, `references/runbook.md` | `docs/` | Business context; operations |

To fill a skeleton: copy it from `<solution_dir>` (not from the installed agent — the draft does not contain it) to `$stage/references/<name>.md`, follow its build instructions, replace every `<!-- fill … -->` block with content, and delete the build-instructions comment. Check nothing is left:

```bash
grep -rln '<!-- fill\|Build instructions' "$stage/references" && echo "UNFILLED SKELETON — fix before installing"
```

Refresh `workflow-guide.md` whenever the workflow config or `.dig` files change, and append to the walkthrough's Decision Log and Accuracy Rules whenever the setup changes or a pitfall is found.

## Step 5: Verify and report

- Frontmatter `name:` equals the folder name; `description` names the customer and the solution's trigger phrases.
- No `{{` placeholders in `.md` files; no `*.template.md` file and no `<!-- fill` block in `references/`; every file the `SKILL.md` references exists (draft: except the finalize-time files, which `SKILL.md` marks as added at Phase 5); no file > 1 MB.
- `git check-ignore -q .claude/skills/<agent-name>/SKILL.md` succeeds when the working directory is a git repo.

Tell the user the agent name and path, that it is available in new chats in this folder, and (Studio) that it can be shared to the account via Skills → Develop. Update `project_state.md`.
