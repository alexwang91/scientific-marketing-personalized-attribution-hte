# 04 · HTE Estimation & Model Validation

## When to Use

When you have randomized data and want to estimate τ(x); when choosing an
estimator; when asked "is this uplift model reliable?"

## Target Quantity

```
τ(x) = E[Y(1) − Y(0) | X = x]    (CATE: Conditional Average Treatment Effect)
```

Not predicting who will buy (propensity) — predicting "whether marketing
changed this person's behavior."

**Fundamental challenge**: the same individual can only ever be observed in one
potential outcome state. Therefore uplift models cannot be validated the way
standard ML models are — standard metrics like AUC are invalid (see
Validation below).

## Default Estimation Path (narrow path, not a survey)

```
Is the data from a randomized experiment? ─ No → back to ref 03; do not
│                                                  force-estimate from logs
├─ Binary treatment, sufficient sample (≥ tens of thousands per arm)
│   → Default: Causal Forest (EconML CausalForestDML) or DR-learner
│     Reason: DR-learner is doubly robust to nuisance model error;
│             causal forest provides valid confidence intervals
│
├─ Imbalanced treatment/control (e.g., 95/5 from a GCG setup)
│   → X-learner (designed for imbalance; borrows strength from the large arm)
│
├─ Multiple treatments (action library)
│   → Estimate τ_t(x) for each treatment vs control separately,
│     sharing the baseline outcome model μ₀(x)
│     If too many arms for individual estimation → treatment featurization (ref 02)
│
└─ Continuous / dose-type treatment (discount depth)
    → Double ML (DML) dose-response
```

**One-line summaries of each learner:**

- **T-learner**: train separate μ₁(x) and μ₀(x); τ̂ = μ̂₁ − μ̂₀. Simple;
  performs poorly with imbalance.
- **S-learner**: single model with T as a feature. Treatment effect can be
  regularized away when signal is weak — use with caution.
- **X-learner**: T-learner base + cross-imputed pseudo-effects + propensity-
  weighted combination. First choice for imbalanced data.
- **DR-learner**: constructs doubly robust pseudo-outcomes, then regresses on X.
  Consistent if either the outcome or propensity model is correctly specified.
- **Causal Forest**: generalized random forest splitting on heterogeneity;
  honest splitting gives valid confidence intervals.

**Library choice**: **EconML** (Microsoft — DML/DR/forest, complete);
**CausalML** (Uber — uplift trees and industry-standard metrics).
Starter code in `scripts/hte_starter.py` (sklearn implementation,
drop-in replaceable with the above libraries).

## Validation: The Only Valid Three-Piece Suite for Uplift Models

**Do not use AUC / accuracy to validate an uplift model** — you have no
individual-level τ labels.

1. **Qini curve / AUUC**: sort users by τ̂ descending, progressively expand
   the targeting fraction, plot cumulative incremental outcomes. A more convex
   curve and higher AUUC = better rank ordering. Compare against two baselines:
   random ordering (diagonal) and propensity-score ordering (a common
   anti-pattern).

2. **Decile calibration**: split into ten buckets by τ̂, compute actual
   treated − control difference in each bucket, compare against the in-bucket
   mean τ̂. A good model should be monotone and calibrated (a bucket where τ̂
   predicts 3% should actually show ~3%).

3. **Holdout set policy value**: simulate "target only the top k% by τ̂" on
   the validation set and compute incremental profit vs current policy
   (the full version of this is OPE in ref 06).

All three implemented in `scripts/qini_auuc.py`.

## Confidence Intervals & Multiple Testing

- Causal forest's honest CIs can directly answer "is this subgroup's effect
  significantly non-zero"
- **Post-hoc subgroup fishing must be corrected**: 50 subgroups tested
  post-experiment ≈ pure noise. Pre-register subgroups (ref 03) or apply
  Benjamini-Hochberg FDR correction.
- **Winner's curse**: the "best" subgroup selected from the data is guaranteed
  to have an inflated effect estimate. Apply shrinkage or re-estimate on a
  separate holdout before committing.

## Step-by-Step

1. Confirm randomized data source; obtain propensity (GCG fraction or
   experiment allocation ratio).
2. All features X must use values **from before the treatment decision**
   (prevent leakage — see below).
3. Choose learner per default path; use cross-fitting (prevent nuisance model
   from contaminating effect estimation).
4. Run validation three-piece suite: AUUC significantly better than random +
   decile calibration monotone → model is usable.
5. Output: τ̂(x) scores + confidence intervals + validation report → feeds
   into ref 05 / 06.

## Common Failure Modes

- **Feature leakage**: used post-treatment behavioral features (e.g., "whether
  the user opened that message") — τ̂ looks perfect but is entirely wrong
- **Propensity mindset for validation**: "model AUC is 0.85 — great" —
  AUC measures who buys, not who is changed by the treatment
- **Insufficient sample, hard segmentation**: thousands of samples per arm
  for causal forest → Qini curve flattens on holdout
- **Treating observational data as randomized**: forgot that these logs were
  generated by the existing targeting policy; τ̂ learns the targeting rule
- **Validating rank only, not calibration**: rank ordering is correct but
  magnitude is off by 2× → profit optimization in ref 06 is entirely wrong

## Acceptance Checklist

- [ ] Randomized data source confirmed; propensity known
- [ ] Feature cutoff time < treatment decision time
- [ ] Learner choice per default path; rationale documented
- [ ] Qini / AUUC significantly beats random baseline on holdout
- [ ] Decile calibration monotone and magnitude plausible
- [ ] Subgroup conclusions pass multiple-testing correction

## Literature

- Künzel et al. (2019, PNAS) "Metalearners for Estimating Heterogeneous
  Treatment Effects using Machine Learning" — S/T/X-learner
- Kennedy (2023) "Towards Optimal Doubly Robust Estimation of Heterogeneous
  Causal Effects" — DR-learner
- Wager & Athey (2018, JASA) "Estimation and Inference of Heterogeneous
  Treatment Effects using Random Forests" — causal forest
- Chernozhukov et al. (2018) "Double/Debiased Machine Learning for Treatment
  and Structural Parameters" — DML
- Gutierrez & Gérardy (2017) "Causal Inference and Uplift Modelling: A Review
  of the Literature" — uplift evaluation metrics
- Tools: EconML (Microsoft), CausalML (Uber)
