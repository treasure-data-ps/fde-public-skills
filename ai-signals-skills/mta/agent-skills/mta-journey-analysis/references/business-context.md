<!--
PURPOSE OF THIS FILE
Business context the MTA journey agent reads before answering attribution and journey
questions. It explains the customer's business so the agent can interpret touchpoints,
channels, conversion events and journey patterns in business terms (not just as table rows).
Table schemas and column descriptions belong in data-dictionary.md, not here.

HOW TO USE
This is a template. For each engagement, copy it into
agent_outputs/<customer_slug>/mta/business-context.md, replace every <placeholder> and
example with the customer's details (from Phase 1 exploration and the filled requirements.md),
and point the agent at that copy. Keep it short and factual. Delete sections that don't apply.
Do not store credentials or raw data extracts.
-->

# <Customer Name> — Business Context Guide

Use this document to interpret customer data, marketing touchpoints, conversion events, and journey behavior in the context of <Customer Name>'s business model. For table schemas and column descriptions, refer to the data dictionary.

---

## Business Model Overview
<!-- 2–4 sentences: industry, what is sold, who the customers are, how they buy.
Example: "<Customer Name> is a <industry> retailer selling <product lines> to <B2C/B2B segment>
through online and in-store channels." -->

## Sales Channels
<!-- One subsection per channel where purchases or conversions happen. -->

### <Channel 1, e.g. Website>
- <Role of the channel, e.g. "Primary digital storefront — highest traffic and order volume">

### <Channel 2, e.g. Mobile App / Physical Stores / Sales Reps>
- <Role of the channel>

## Marketing Touchpoints & Channel Definitions
<!-- Map the channel values that appear in the MTA output tables to business meaning.
Example rows: | organic | Unpaid search traffic | Website pageviews with no UTM / search referrer | -->

| Channel value | Business meaning | Source / how it is identified |
|---|---|---|
| <channel_value> | <what it represents> | <table or UTM rule> |

## Conversion Definition
<!-- What counts as a conversion (e.g. completed order, test-drive booking, form submit),
which table/rule flags it, and any secondary or micro-conversions. -->

## Customer Journey Characteristics
<!-- Typical journey length and timeframe, seasonality, lookback window used, known
patterns (e.g. "most buyers research on mobile, purchase on desktop"). -->

## Key Business Questions
<!-- The questions stakeholders want the attribution analysis to answer, e.g.
- Which channels contribute most to conversions?
- Where should budget be reallocated?
- Which journey paths convert best? -->

## Known Data Caveats
<!-- Gaps or quirks that affect interpretation, e.g. low UTM coverage, offline sales not
tracked, channel naming changes over time. -->
