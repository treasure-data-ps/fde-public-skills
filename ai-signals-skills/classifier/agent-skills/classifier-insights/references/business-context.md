# Business Context — Classification Model

## Customer & Use Case

> **Populate this file with customer-specific context before deploying the agent.**

| Field | Value |
|-------|-------|
| **Customer** | [CUSTOMER NAME] |
| **Industry** | [INDUSTRY] |
| **Use Case** | [USE CASE DESCRIPTION — e.g., "Lead scoring for automotive dealer network"] |
| **Target Variable** | `[column_name]` — [DEFINITION — e.g., "1 = lead submitted a finance application within 90 days"] |
| **Positive Class Meaning** | [WHAT A SCORE OF 1 MEANS IN BUSINESS TERMS] |
| **Score Interpretation** | Higher score = more likely to [TARGET EVENT] |

## Business Terminology

Map technical ML terms to customer-friendly language:

| Technical Term | Customer Term |
|---------------|---------------|
| Predicted positive | [e.g., "High-potential lead", "At-risk customer"] |
| Predicted negative | [e.g., "Low-potential lead", "Stable customer"] |
| Target variable (1) | [e.g., "Converted", "Churned", "Responded"] |
| Target variable (0) | [e.g., "Did not convert", "Retained", "Did not respond"] |
| Prediction score | [e.g., "Lead score", "Churn risk score", "Propensity score"] |
| False positive | [e.g., "Lead flagged high but didn't convert"] |
| False negative | [e.g., "Lead scored low but actually converted"] |

## Key Business Rules

> Add customer-specific rules that the agent must follow when presenting results.

- [e.g., "Never use the word 'revenue' — refer to 'applications' instead"]
- [e.g., "Score buckets should be labeled: Hot (>0.8), Warm (0.5-0.8), Cool (0.3-0.5), Cold (<0.3)"]
- [e.g., "Only show top 10 features to non-technical stakeholders"]
- [e.g., "Always mention the model retraining date when showing metrics"]

## Data Sources

| Source | Description | Key Features |
|--------|------------|--------------|
| [Source table 1] | [Description] | [Features derived from this source] |
| [Source table 2] | [Description] | [Features derived from this source] |

## Model Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Model type | [xgboost / catboost / logistic] | [Why this was chosen] |
| `fbeta_beta` | [value] | [Precision/recall preference explanation] |
| `threshold_strategy` | [value] | [Why this strategy] |
| Training window | [value] months | [Why this length] |
| Label maturity gap | [value] months | [Event window explanation] |

## Score Bucket Definitions

| Bucket | Score Range | Business Label | Recommended Action |
|--------|------------|---------------|-------------------|
| 5 | 0.80 – 1.00 | [e.g., "Hot Lead"] | [e.g., "Immediate sales outreach"] |
| 4 | 0.60 – 0.80 | [e.g., "Warm Lead"] | [e.g., "Nurture campaign"] |
| 3 | 0.40 – 0.60 | [e.g., "Medium"] | [e.g., "Monitor engagement"] |
| 2 | 0.20 – 0.40 | [e.g., "Cool Lead"] | [e.g., "Low-priority follow-up"] |
| 1 | 0.00 – 0.20 | [e.g., "Cold Lead"] | [e.g., "Exclude from outreach"] |
