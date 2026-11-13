<!--
PURPOSE OF THIS FILE
The customer's business knowledge that the NBA agent cannot learn from the data: business jargon,
the decision and its actions, what counts as success, who is eligible, data edge cases, goals and
rules. The agent reads it every session and applies its definitions over generic ones.
How the Next Best Action model works does NOT belong here — it is in ai-signals-guide.md,
data-dictionary.md and the workflow guide.

HOW TO USE
Skeleton — never filled in place, never installed. Copied in Phase 1 to
  agent_outputs/<project_slug>/business-context.md
(shared/playbook.md, Phase 1 business context). Open questions go to the customer through the
requirements doc; answers are merged in Phase 4 Part B; the file is confirmed in Phase 5. Every
agent build copies the engagement file into the agent's references/.

AUTHORING RULES (for the engagement copy)
- Replace each question with a terse answer bullet once known. Reader is the agent: concrete and
  imperative ("Success = an order in `<table>` within 14 days of the send", "Call `offer_b` 'Free shipping'").
- Mark answers inferred from the data `[INFERRED — please confirm]`; keep unanswered questions as
  `- [NEEDS YOUR INPUT] <question>`. Remove a marker once the customer has answered or confirmed. Use only these
  two markers — no others.
- Business knowledge only: no notes on how this setup is run (test scope, resources to leave alone,
  approvals) — those belong in project_state.md.
- Real table, column and value names in backticks; aggregates only — never raw customer records,
  names, emails or other PII.
- Keep every section to a few bullets. Delete this comment and the line under the title in the copy.
-->

# {{project_name}} — Business Context

*Questions to consider are listed under each heading; answer the ones that apply.*

## Business Overview
- What does the company sell, and to whom (B2C, B2B, both)?
- Which channels and touchpoints exist (email, SMS, push, web, app, stores, call center)?
- Which regions, brands or business units does the data cover, and do they behave differently?
- Which team owns the decision the model makes (CRM, campaign, retention, merchandising)?

## Customers and Identity
- What is one customer in this model — a person, an account, a household?
- Can one customer have several IDs or records across the action log and the other sources?
- Which profiles are test, internal, employee or partner accounts, and how are they identified?

## Key Terms and Definitions
- What are the actions, in the team's own names (offer names, campaign themes, treatments), and what is each one?
- What exactly counts as success after an action, and as which event or status in the data?
- How are activity, engagement and value defined (active customer, engaged subscriber, high-value customer)?
- Is there a control / "do nothing" option, and is it logged?

## Buying Cycle and Seasonality
- How long after an action does the customer usually respond (hours, days, weeks)?
- How long after the response is it visible in the data (late orders, batch-loaded redemptions)?
- Which seasons, promotions or launches change which action works?
- Were actions added, retired or changed (new offer values, redesigned campaigns) during the history?

## Data Intricacies and Edge Cases
- How were actions assigned in the past — by rules, by segment, at random, by rotation, by an older model?
- Which actions were only sent to particular customers (VIPs, a region, new customers)?
- Which records should be ignored or treated specially (bulk resends, failed sends, refunds, test campaigns)?
- Are there known gaps, duplicates, late-arriving data or tracking changes in the action log or outcomes?

## Goals and Use Cases
- How will the recommended action be delivered (campaign audiences, journeys, website, sales scripts)?
- Which KPI will judge the model (conversion rate, redemption rate, revenue per customer, retention)?
- Does each action have a cost (discount value, call time) that matters when comparing them?
- Who will use the recommendations and the agent, and what decisions will they make with them?

## Rules and Exclusions
- Who must never receive an action (opted-out, minors, regulated groups, customers in disputes)?
- Which eligibility rules apply per action (minimum spend, region, product ownership, budget caps)?
- Are there contact-frequency or consent rules per channel?
- Which attributes must not be used as context for compliance or fairness reasons (age, gender, location, health)?

## Next Best Action Definitions
- Which decision is it — channel, send time, campaign, or another action — and which options does the model choose between (which are grouped)?
- Channels: which UTM mediums / sources, tracking codes or traffic-source values map to which channel; what counts as `direct`?
- Time: which time zone, and which time slots matter (dayparts, hours, day of week)?
- Which events are decisions made by the business (sends, assignments) and which are customer engagement?
- How long after an action should success count (the reward window)?
- Is success yes/no or a value (order value, margin)? Is there a cap on large values?
- Which customers should get a recommendation at each run?
- How will the result be measured after go-live (holdout group, A/B test, before/after)?
