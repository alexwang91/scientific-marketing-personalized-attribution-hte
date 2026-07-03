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

## Netflix Surrogate Index Benchmark

Netflix ran 200 experiments with both short-term surrogate predictions and
long-term ground truth (63-day direct measurement). Key findings
(Farias et al., arXiv 2024):

- **95% consistency**: surrogate-predicted launch decisions matched ground
  truth in 95% of cases.
- **65–79% recall** on launch decisions: the surrogate correctly identified
  65–79% of the experiments that ground truth would have launched.
- **Practical implication**: surrogate index is a high-precision screening
  tool, not a final arbiter. Use it to prioritize iteration and eliminate
  clear losers quickly; keep long-term holdout for final launch authorization
  on high-stakes policy changes.

The 5% inconsistency rate is not random — it is concentrated in experiments
where the treatment mechanism has a direct long-term channel that bypasses
the surrogate metrics (e.g., one-time brand events, hard-to-reverse UX changes).
Document these "surrogate bypass" mechanisms explicitly when building f(S).

## LOPE: Long-Term Off-Policy Evaluation

**LOPE** (Long-term Off-Policy Evaluation, Spotify/Cornell, WWW 2024) bridges
off-policy evaluation (ref 06) and surrogate metrics (this file):

```
Problem: I have a new policy π_new; I want to estimate its long-term value
         V_∞(π_new) from short-term bandit logs without running a full long
         experiment.

LOPE solution:
  V_∞(π_new) = OPE(π_new; short-term logs) + surrogate bridge G(S, π_new)
  where G corrects OPE's short-window bias using the surrogate model f(S).
```

**When to use**: at L2/L3, when you retrain the offline policy frequently
and cannot wait 63 days for each version. LOPE gives a practically-valid
long-term estimate in days. Validate LOPE estimates against actual long-term
holdout quarterly; if they diverge, update f(S).

## Literature

- Athey, Chetty, Imbens & Kang (2019) "The Surrogate Index" — methodological
  foundation
- Farias et al. (2024, arXiv) "Correcting for Outcome Measurement Error in
  Surrogate Evaluation" — Netflix 200-experiment benchmark
- Bompaire et al. (2024, WWW / Spotify) "Long-Term Off-Policy Evaluation and
  Learning" — LOPE bridging OPE and surrogacy
- Yang, Eckles et al. — industrial surrogate applications
  (Netflix / Meta public materials)
- Gupta et al. (2006) "Modeling Customer Lifetime Value" — LTV metrics
- [pymc-marketing](https://github.com/pymc-labs/pymc-marketing) `clv` module
  (open source) — production BG/NBD, Pareto/NBD, Gamma-Gamma implementations
  for the LTV term of the surrogate index
- Anderson & Simester series — long-term effects of promotions: deep discounts
  train customers to wait for deals
