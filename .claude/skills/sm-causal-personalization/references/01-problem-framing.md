# 01 · Problem Framing & Measurement Framework

## When to Use

At project kickoff; when asked "is this marketing initiative worth it / how do
I define success metrics"; when the team is using attribution reports as causal
evidence; when defining KPIs and guardrail metrics.

## Decision Tree: Which Layer Are You Answering?

```
What are you trying to answer?
├─ How to allocate budget across channels / at scale → MMM (marginal ROI, quarterly)
├─ Which touchpoint gets credit for this conversion → Attribution / MTA
│     (attribution rule, correlation — not causation)
├─ Did this campaign produce incremental lift overall → Incrementality test
│     (geo / holdout, ATE)
└─ Is it worth doing this action for this specific person → HTE / uplift
      (τ(x), main thread of this skill)
```

### Triangulation: The Modern Measurement Architecture

The current industry standard is MMM × incrementality experiments × attribution,
each calibrating the others:
- Incrementality experiments calibrate MMM coefficients
- MMM handles budget-level decisions
- Attribution provides fast feedback for operations (not budget decisions)
- HTE takes incrementality down to the individual level

### Why Attribution Is Not Causal

MTA assigns credit to "touchpoints present in the conversion path" — but
sure-things (people who would have bought anyway) also have full touchpaths.
Last-click systematically overstates branded search and understates upper-funnel.
This bias is documented in repeated incrementality experiments. In the
cookieless era, third-party touchpoint data continues to degrade; the value of
first-party experiments only grows.

## Definition Checklist (complete before any code is written)

1. **Y (outcome)**: conversion / repurchase / AOV / retention / churn.
   State the observation window explicitly (e.g., 14 days post-touch).

2. **Business objective metric — incremental profit, not conversion rate**:
   ```
   incremental_profit(x, t) =
       τ_revenue(x, t) × gross_margin
     − coupon_value × P(redemption | treated)   ← subsidy only for treated
     − channel_cost (per SMS / push / ad impression)
     − E[long-term negative effects]             (churn, fatigue → ref 08)
   ```

3. **Guardrail metrics**: unsubscribe rate, complaint rate, contact frequency
   cap, minimum gross margin, return rate. Every deployed policy carries
   guardrails; breach triggers automatic rollback.

4. **Time window**: short-term proxy window (for decisions) + long-term
   validation window (quarterly review, → ref 08).

5. **Decision unit**: individual user / account (B2B → ref 10) / store /
   geography.

## Step-by-Step

1. Use the decision tree to confirm the problem layer. Write a one-sentence
   problem statement:
   "For [population], does [action] produce [incremental profit ≥ X] within
   [window], with guardrails [...]?"
2. Write the profit equation; have Finance confirm margin and redemption rate
   assumptions.
3. Define guardrails and rollback conditions.
4. Review the Six Prerequisites (SKILL.md); missing experimental data → go to
   ref 03 first.
5. Governance pre-check (ref 09) — before writing any code.

## Common Failure Modes

- **Attribution used as causation**: "Branded search has the highest ROI so
  increase budget" → incrementality test reveals it's mostly sure-things
- **Tracking conversion, not incremental profit**: sending coupons to people
  who would have bought anyway — conversion looks great, margin is destroyed
- **No guardrail metrics**: conversion up, unsubscribes also up; list is
  degraded six months later
- **Window too short**: 14-day positive effect, 90-day LTV is being pulled
  forward (→ ref 08)
- **Wrong problem layer**: using an HTE model to answer a budget-allocation
  question (that's MMM), or using MMM to answer a personalization question

## Acceptance Checklist

- [ ] One-sentence problem statement written and confirmed to be in the HTE
      layer (otherwise → MMM / experiment)
- [ ] Profit equation has Finance-confirmed margin and redemption assumptions
- [ ] Y, window, decision unit, and guardrails documented
- [ ] Six Prerequisites reviewed; gaps have remediation plans
- [ ] Governance pre-check passed (ref 09)

## Literature

- Kohavi, Tang & Xu, *Trustworthy Online Controlled Experiments* (2020) —
  experiment culture and pitfalls
- Blake, Nosko & Tadelis (2015) "Consumer Heterogeneity and Paid Search
  Effectiveness: A Large-Scale Field Experiment at eBay" — zero-lift branded
  search, a canonical result
- Lewis & Rao (2015) "The Unfavorable Economics of Measuring the Returns to
  Advertising" — why ad incrementality is structurally hard to measure
- Gordon et al. (2019, *Marketing Science*) — large-scale comparison of
  Facebook experiments vs observational methods; observational methods
  systematically mis-estimate
