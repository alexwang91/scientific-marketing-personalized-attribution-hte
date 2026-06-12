# 08 · Long-Term Value & Surrogate Metrics

## When to Use

When asked "short-term works — what about long-term?"; when defining the
reward / optimization target; when the LTV calculation for a subsidy strategy
is needed; when deciding how long an experiment should run.

## Why Short Windows Systematically Mislead

- **Sleeping-dog harm is long-term**: unsubscribes, brand fatigue, growing
  do-not-disturb lists are invisible in a 14-day window.
- **Subsidies pull forward LTV**: some coupon-driven conversions are future
  full-price purchases brought forward to today at a discount — and they train
  users to wait for deals (price anchoring eroded by the strategy itself).
- **Channel cannibalization**: paid-acquisition "new customers" are partly
  repackaged organic traffic (→ ref 01 incrementality framing).

A short-window τ is blind to all three effects.

## Surrogate Index (the formal method for short-term proxies)

Waiting 12 months to observe LTV kills iteration speed. The Athey-Chetty-
Imbens surrogate index approach:

```
1. On a historical long-horizon dataset, model:
      long_term_Y ~ f(short_term_metrics_vector S)
   S = (7/14/30-day repurchase, AOV, activity frequency, unsubscribes,
        complaints, category breadth, …)

2. Experiment runs only the short term; measure treatment effects on S.

3. Long-term effect estimate = effect of treatment on f(S).
```

**Required assumption (must be reviewed periodically)**: treatment affects
long-term Y only through S (the surrogacy condition). Certain actions can
bypass S and directly damage long-term outcomes (e.g., brand damage) — which
is why a long-term holdout (below) is the institutional backstop.

**Practical tip**: use a **vector of metrics**, not a single metric. A single
short-term metric (e.g., first-purchase conversion) is the most gameable target.
The vector must include negative indicators (unsubscribes, complaints).

## Long-Term Holdout (Institutional Backstop)

- Retain a **permanent sub-segment of the GCG** (e.g., 1%) that receives no
  marketing touches permanently → measures cumulative CRM system effects.
- For each major policy change, retain a **long-term holdout** running 6–12
  months → validates surrogate estimates against reality.
- Annual review: surrogate-predicted long-term effects vs long-term holdout
  actuals. Large discrepancy → rebuild f(S).

## Incremental LTV Metric

```
incremental_LTV(x, t) =
    Σ_future_windows [ E[profit | treated] − E[profit | control] ] discounted
  − subsidy cost
  − pull-forward erosion (correction for accelerated demand)
```

**Pull-forward detection**: if the treated group shows high short-term
conversion followed by conversion **below control** in a subsequent window
(curves crossing), demand has been pulled forward. Extend the observation
window past the crossing point before reporting net effect.

## Step-by-Step

1. Build the surrogate index f(S) on historical data; document training
   date and assumptions.
2. Experiment / bandit reward uses f(S), not raw conversion (ref 07).
3. Build permanent holdout and policy-level long-term controls.
4. Quarterly: check for pull-forward curve crossings.
   Annually: surrogate deviation review.

## Common Failure Modes

- **Single surrogate, easily gamed**: optimizing first-purchase conversion →
  strategy learns to issue large coupons → LTV destruction becomes apparent
  after a year.
- **Surrogate built once, used forever**: population and product changed;
  f(S) is stale; no one notices.
- **Two-week experiment, final conclusion**: pull-forward crossings typically
  appear in weeks 4–8; positive effect is borrowed, not earned.
- **Long-term holdout cannibalized by operations**: "let's use that 1% for the
  double-11 push" → permanent baseline is gone.

## Acceptance Checklist

- [ ] Reward / objective includes surrogate index, not raw short-term conversion
- [ ] S is a vector including negative indicators
- [ ] Permanent holdout + policy-level long-term controls running
- [ ] Pull-forward check quarterly; surrogate deviation review annually

## Literature

- Athey, Chetty, Imbens & Kang (2019) "The Surrogate Index" — methodological
  foundation
- Yang, Eckles et al. — industrial surrogate applications
  (Netflix / Meta public materials)
- Gupta et al. (2006) "Modeling Customer Lifetime Value" — LTV metrics
- Anderson & Simester series — long-term effects of promotions: deep discounts
  train customers to wait for deals
