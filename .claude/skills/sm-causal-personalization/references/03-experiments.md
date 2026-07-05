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
- **Peeking with classical p-values**: checking p-values daily and stopping
  when significant — false positive rate explodes. Use fixed duration or
  **anytime-valid inference** (confidence sequences) for legitimate continuous
  monitoring (see below).
- **Experiment too short**: two weeks won't capture sleeping-dog harm or
  repurchase effects (→ ref 08)
- **Control group too small**: GCG compressed to 0.5% "to lose less revenue" —
  variance is too high to detect anything
- **Post-hoc subgroup fishing**: 50 subgroups found after the experiment —
  all noise (→ ref 04 multiple testing)
- **Propensity not logged**: three months later you want to run OPE and find
  only "what action was sent," not "with what probability"

## Anytime-Valid Inference (Legitimate Continuous Monitoring)

Classical p-values require a pre-committed stopping rule. **Anytime-valid
confidence sequences** provide intervals that are valid at every sample size,
allowing early stopping without inflating false positives. Now production-
standard at Netflix, Microsoft, Adobe.

**Rule**: replace fixed-horizon t-test with a confidence sequence (e.g.,
mixture martingale from Waudby-Smith & Ramdas 2024). You may stop as soon as
the CI excludes zero — this is statistically valid. Classical "peek once at
the end" remains equally valid; use whichever matches your operational cadence.

**When not to use early stopping**: for HTE subgroup analysis and uplift model
validation, keep the pre-committed sample to avoid winner's curse in subgroup
selection (ref 04).

## Switchback Interval Selection

For switchback experiments (time-slot rotation, ref identification ladder
level 3): interval duration should be **fit from historical data** using
Empirical Bayes on autocorrelation structure of the outcome series, not set
by intuition. A data-driven interval can reduce MSE by ~33% vs default choices.
Short intervals inflate variance from carryover; long intervals inflate bias
from trend. Instrument the autocorrelation and fit interval length before
running.

## Cluster Experiments: Two-Layer SRM Check

Cluster randomization (accounts, geos, time slots) requires a **two-layer
SRM check** (LinkedIn, 2024):

1. **Cluster-level SRM**: are the number of assigned clusters per arm correct?
2. **Unit-within-cluster SRM**: within each arm, does the unit distribution
   match expectations?

Failing either layer → stop and debug. A unit-level SRM inside a correctly
allocated cluster arm is a common silent failure mode.

## Experiments as Reusable Evaluation Assets

Every completed experiment is permanently valuable. Archive:
- Propensity logs (for OPE on future policies)
- Estimated τ̂(x) and confidence intervals
- Covariate balance statistics and SRM check results

Pooling historical experiments (Snap platform pattern, arXiv 2512.03060)
enables: (a) warm-start estimation for new experiments, (b) cross-scenario
τ̂ transfer for data-thin segments, (c) organizational learning that
compounds across years of experiments. Build the archive from day one —
retroactive reconstruction is expensive.

## Assumption → Validation Ledger (decide what to test first)

A power calculation tells you how big a test must be; it does not tell you
*which* test to run first. Before committing experiment traffic, inventory every
load-bearing assumption across the analysis and rank them — most teams test what
is easy, not what is decisive.

Build one table. Each row is an assumption the plan depends on:

| Assumption | Provenance now | Risk if wrong | Minimum valid test | Pass / fail rule |
|------------|----------------|---------------|--------------------|------------------|
| the claim the budget rests on | Hypothesis / Assumed / Missing (ref 16) | what breaks downstream, and how much | smallest experiment that could falsify it (identification ladder above) | the pre-committed line that settles it — not "looks better" |

**Ranking rule** (highest first):
1. **Blocking + cheap to test** — gates budget *and* is cheap to falsify. Always
   first; a zero-cost data pull beats a guess.
2. **Blocking + expensive** — gates budget but needs a real experiment; this is
   where the power calculation and duration above actually bind.
3. **Non-blocking** — nice to know; defer until the blockers clear.

**Three disciplines this enforces:**
- **Separate what the test measures from what it cannot.** A survey measures
  stated intent, not incremental sales; a landing-page A/B measures click-through,
  not margin; sell-in is not sell-through. State the gap in the row, or the
  ledger lies by omission.
- **Every row needs a pre-committed pass/fail line.** "We'll see how it looks" is
  not a rule — it is a license to rationalize after the fact (ref 04 multiple
  testing; ref 15 falsifiability). Set the line before the data arrives.
- **Hypothesis stays Hypothesis until a holdout moves it.** Customer voice
  (ref 00b), elicited WTP (ref 01), and reviewer challenges (ref 14) all enter
  this ledger as `Hypothesis`; the test is what promotes them to `Sourced`.

The ledger is the bridge from the Missing register (ref 16, sorted by
sensitivity) and the open-blocking challenges (ref 14) to a dated test roadmap.
`generate_report.py --depth deep` renders exactly this consolidation from the
config — missing numbers + open challenges + test predictions in one ranked list.

## Acceptance Checklist

- [ ] Identification level confirmed; written assumption justification for
      anything below level 2
- [ ] Assumption → validation ledger built; load-bearing assumptions ranked by
      (blocking × cost-to-test), each with a pre-committed pass/fail rule
- [ ] Power calculation done; sample and duration sufficient for the target MDE
- [ ] Randomization unit matches interference structure
- [ ] Propensity log instrumented at code-write time (not retrofitted later)
- [ ] Analysis plan pre-registered (primary metric / guardrails / subgroup list)
- [ ] SRM monitoring live at launch; cluster experiments check two layers
- [ ] Continuous monitoring uses confidence sequences, not classical p-values
- [ ] Completed experiment archived (propensity logs + τ̂ + balance stats)

## Literature

- Kohavi, Tang & Xu (2020), *Trustworthy Online Controlled Experiments* —
  SRM, peeking, experiment culture
- Waudby-Smith & Ramdas (2024) "Estimating Means of Bounded Random Variables
  by Betting" — confidence sequences / anytime-valid inference
- Howard et al. (2021) "Time-Uniform, Nonparametric, Nonasymptotic Confidence
  Sequences" — theoretical foundation for anytime-valid CIs
- Meta GeoLift (open source) / Google TBR — geo incrementality measurement
- [pymc-marketing](https://github.com/pymc-labs/pymc-marketing)
  `customer_choice.MVITS` (open source) — multivariate interrupted time
  series for geo / market-level quasi-experiments; its
  `mmm.lift_test.add_lift_test_measurements` feeds holdout / geo-lift
  results into an MMM as calibration constraints — the "experiments as
  reusable assets" principle applied at the channel layer
- Deng et al. (2013) "Improving the Sensitivity of Online Controlled
  Experiments by Utilizing Pre-Experiment Data" — CUPED
- Athey & Imbens (2017) "The State of Applied Econometrics: Causality and
  Policy Evaluation" — map of quasi-experimental methods
- Xiong et al. (2024) "Optimal Switchback Experiment Design" — Empirical
  Bayes interval selection for switchback experiments
- Pattern credit: the assumption → validation ledger adapts the
  "plan-validation-experiments" (S13) move from the GTM-Master skill suite
  (alexwang91/gtm-master), re-grounded on this skill's provenance contract so a
  Hypothesis is promoted only by a holdout, not by survey intent.
