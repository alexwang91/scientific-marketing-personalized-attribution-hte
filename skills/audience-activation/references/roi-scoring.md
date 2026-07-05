# ROI Scoring v1

## Purpose

Audience Activation Planner v1 does not calculate real ROAS unless the user supplies enough economics and performance data. Without AOV, margin, CVR, CAC, and observed campaign data, it outputs a relative ROI score from 1-5.

## Relative ROI score

| Score | Meaning |
|---|---|
| 5 | Highest expected planning value because intent or first-party signal is strong |
| 4 | Strong planning value, usually performance-capable but still needs validation |
| 3 | Medium planning value, often useful for consideration, creators, or content |
| 2 | Lower short-term performance value, often awareness or support role |
| 1 | Limited direct ROI expectation for the selected goal |

## Heuristics

- Search intent receives a higher score for purchase, lead, and store-visit goals.
- Consented CRM / retargeting receives a higher score when first-party data exists.
- Broad awareness channels receive lower short-term ROI scores for purchase goals.
- Video, TikTok, and creators receive higher scores for awareness goals.
- Marketplaces / retail media receive higher scores for purchase goals when a product can be sold there.
- Confidence stays low when product, budget, AOV, margin, CVR, or CAC is missing.

## Required language

Every report must state:

- ROI is a planning estimate unless calibrated.
- Relative ROI score is not real ROAS.
- Real validation requires campaign data, holdouts, or experiments.
- Synthetic / assumed signals are hypotheses, not observed sales or clicks.
