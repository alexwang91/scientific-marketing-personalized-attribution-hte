# 03 · Experiment Design & Identification Strategy

## When to Use

Before designing any experiment; when asked "can we use historical data to
estimate this?"; when calculating required sample size; when choosing the
randomization unit.

## Identification Ladder (descend only when the level above is infeasible)

```
1. RCT / Global Control Group (GCG)         ← default; individual randomization
2. Geo-lift (geographic randomization / synthetic control)
     ← when individual randomization is impossible (brand ads, offline, TV)
3. Switchback (time-slot rotation)
     ← high-interference settings (pricing, supply-demand platforms)
4. Quasi-experiments: DiD / IV / RDD
     ← policy changes, natural experiments; identification assumption must be argued
5. Observational + unconfoundedness
     ← last resort; mandatory to write identification assumptions + sensitivity analysis
```

**Hard rule: Marketing log data is confoundeed by design — who gets targeted
is determined by the existing targeting policy. Without randomization, build a
GCG first. Do not estimate CATE from observational logs.**

If you must use observational data (level 5), you must:
- Write explicit identification assumptions (which confounders are covered by X;
  which are not)
- Run a negative control test
- Run sensitivity analysis (E-value / Rosenbaum bounds)
- Label all conclusions "observational estimate"

## Global Control Group (GCG) — The Core Infrastructure for L1

- Reserve **1–5%** of users who receive **no** CRM / lifecycle marketing touches
- This is the institutionalized alternative to "running a new experiment each
  time": build once, all campaigns share the same baseline
- **Rotating vs permanent**: a permanent GCG (e.g., 1%) measures long-term
  cumulative effects; a rotating GCG (e.g., quarterly rotation) ensures
  fairness and reduces income loss. Both can coexist.
- GCG requires a **global frequency-control system** to enforce — without it,
  the GCG is a policy on paper only (ref 02 control-group contamination)
- Produce a quarterly "CRM total incrementality report": all treated users vs
  GCG. This is the only credible metric for proving the marketing team's value
  to leadership.

## Power Calculation: HTE Is Much More Expensive Than ATE

Standard A/B (detecting ATE): two-proportion z-test, standard formula.

Detecting **the difference in uplift between two subgroups** (the minimal HTE
question) is a "difference-in-differences": its variance is the sum of all
four cells:

```
Var(τ̂_A − τ̂_B) = Var(Ȳ_{A1}) + Var(Ȳ_{A0}) + Var(Ȳ_{B1}) + Var(Ȳ_{B0})
```

**Rule of thumb: to detect the same MDE, detecting an uplift difference
requires ~4× the sample of a standard A/B test.** Doubling the number of
segments halves the per-segment sample, and inflates the detectable MDE by √2.
Run `scripts/power_analysis.py` before deciding how many segments to use.

Variance-reduction techniques: CUPED (use pre-experiment covariates; typical
30–50% variance reduction), paired / stratified randomization, continuous Y
(revenue is more sensitive than binary conversion).

## Propensity Log — The Most Commonly Missing, Irreplaceable Field

**At every action decision, record P(action | x) — the probability that this
specific action was selected for this user at this moment.**

- Uniform random: log 1/K
- Stratified random: log the per-stratum probability
- Live policy / bandit: log the probability the policy assigned

Without it: OPE (ref 06) is impossible; observational debiasing is impossible;
bandit logs cannot be reused for evaluation.
With it: all historical logs become reusable evaluation assets. This has higher
priority than any modeling work.

## Choosing the Randomization Unit

```
├─ toC individual outreach → user-level randomization
├─ toB / ABM → account-level cluster randomization
│     (contacts within an account talk to each other; individual randomization
│      guarantees contamination)
├─ High interference (social, market supply/demand, shared budget)
│     → geo-level or switchback
└─ Offline / untargetable → geo-lift
      (GeoLift-type tools; synthetic control as counterfactual)
```

Interference / SUTVA-violation signals: recommendation-driven cross-category
cannibalization, couponed and uncouponed users sharing inventory, referral
mechanics. When present, escalate the randomization unit.

## Step-by-Step

1. Choose identification level; document assumptions for anything below level 2.
2. Run `power_analysis.py`: given baseline rate, MDE, α=0.05, power=0.8 →
   required sample and experiment duration.
3. Select randomization unit; check for interference.
4. Design randomization: stratify on key X (balance), log propensity scores.
5. Pre-register the analysis plan: primary metric, guardrails, subgroup list
   (prevents post-hoc cherry-picking — ref 04 multiple testing).
6. At launch, check for SRM (sample ratio mismatch): if group proportions deviate
   from design values → stop immediately and debug.

## Common Failure Modes

- **SRM not checked**: randomization code has a bug, groups are incomparable,
  all conclusions are void
- **Peeking**: checking p-values daily and stopping when significant — false
  positive rate explodes. Use fixed duration or sequential testing.
- **Experiment too short**: two weeks won't capture sleeping-dog harm or
  repurchase effects (→ ref 08)
- **Control group too small**: GCG compressed to 0.5% "to lose less revenue" —
  variance is too high to detect anything
- **Post-hoc subgroup fishing**: 50 subgroups found after the experiment —
  all noise (→ ref 04 multiple testing)
- **Propensity not logged**: three months later you want to run OPE and find
  only "what action was sent," not "with what probability"

## Acceptance Checklist

- [ ] Identification level confirmed; written assumption justification for
      anything below level 2
- [ ] Power calculation done; sample and duration sufficient for the target MDE
- [ ] Randomization unit matches interference structure
- [ ] Propensity log instrumented at code-write time (not retrofitted later)
- [ ] Analysis plan pre-registered (primary metric / guardrails / subgroup list)
- [ ] SRM monitoring live at launch

## Literature

- Kohavi, Tang & Xu (2020), *Trustworthy Online Controlled Experiments* —
  SRM, peeking, experiment culture
- Meta GeoLift (open source) / Google TBR — geo incrementality measurement
- Deng et al. (2013) "Improving the Sensitivity of Online Controlled
  Experiments by Utilizing Pre-Experiment Data" — CUPED
- Athey & Imbens (2017) "The State of Applied Econometrics: Causality and
  Policy Evaluation" — map of quasi-experimental methods
