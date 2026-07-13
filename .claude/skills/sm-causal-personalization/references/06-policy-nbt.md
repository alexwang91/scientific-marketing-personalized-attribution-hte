# 06 · Policy Learning & Next Best Treatment

## When to Use

When upgrading from "should we contact this person?" to "which action gives
the best return for this person?"; when budget or capacity is constrained;
when you need to evaluate a new policy before launching (OPE).

## Target Quantity

Policy π: x → treatment. Evaluate by **policy value**:

```
V(π)  = E[Y(π(X))]                     (absolute value)
ΔV    = V(π_new) − V(π_current)        (incremental vs current policy —
                                          the number that should be reported)
```

## Unconstrained Case: Per-User Argmax

```
π(x) = argmax_t [ τ̂_t(x) × unit_margin − c_t ]
```

where c_t comes from the treatment card (ref 02), and t = no-action (cost 0)
is always a valid option.

**Note**: τ̂ must be well-calibrated (ref 04). Correct rank ordering but
wrong magnitude → argmax systematically selects the wrong action.

## Budget / Capacity Constrained Case (almost always the real situation)

When budget B is insufficient to reach all users with positive incremental
return, this is a knapsack problem:

```
max Σᵢ [τ̂_{t_i}(xᵢ) × margin − c_{t_i}]   s.t.  Σᵢ c_{t_i} ≤ B
```

**Practical solution (Lagrangian / dual pricing)**: sort by "incremental profit
/ cost" (ROI) descending and allocate until budget exhausted. Equivalently,
find a shadow price λ* such that the decision rule becomes:

```
Allocate if:  τ̂_t(x) × margin − c_t ≥ λ* × c_t
```

λ* is "the minimum incremental return per ¥1 of marketing spend in this
organization" — a more useful management number than any single-point ROI.
Multiple treatments sharing a budget, or sales capacity constraints (ref 10:
SDR time), follow the exact same formulation — replace c_t with time cost.

### Three Tiers of the Same λ* Rule

The shadow-price allocation rule above applies at three different grains,
each with its own script — pick the one that matches the decision you're
actually making:

```
Person-level    (who gets which action):  policy_budget.py       — needs a
                                            randomized holdout; τ̂ per user.
SKU × module    (how much per SKU per     investment_engine.py   — business-
                 marketing lever, e.g.     planning cells with a point τ̂
                 "Search spend for SKU     estimate (randomized, modeled, MMM-
                 A3"):                     calibrated, or expert-assumed) and
                                           no holdout requirement; feeds ref 17
                                           chapter 1 (verdict) through 5
                                           (confidence). Config contract in
                                           `investment_schema.py`.
Channel-level   (how much per channel,    mmm_bridge.py bridges an externally
                 no person or SKU          fit pymc-marketing summary into the
                 granularity):             same report — see below.
```

All three fund a descending-marginal-ROI prefix and stop at the same kind of
cutoff (`required_mroi` / λ*). At the SKU × module tier the floor may differ
by evidence grade — `required_mroi_by_confidence` charges assumption-grade
cells a higher required return than validated ones (a risk premium for the
systematic optimism of unvalidated estimates; CausalDS, arXiv 2607.08093,
measured every frontier model's nominal 95% intervals covering only 20-71%
empirically). A step below its own tier's floor is skipped; the budget cutoff
still ends the prefix. A SKU-level cell's `confidence` badge
(`validated` / `mmm_calibrated` / `assumption_grade` / `blocked`) is always
computed from its evidence (`tau_source` + `measurement_gate` + `readiness`),
never a raw input — see `investment_engine.confidence_badge`.

## Two-Stage vs End-to-End: Architectural Choice

Current SKU-level investment rule: a `randomized_hte` cell must name
`validation_ref`, and that ref must pass the supplied `hte_validation` gate
(Qini/AUUC plus decile calibration) before the dashboard calls it `validated`.
Without that gate it is treated as `assumption_grade`, even if a measurement
gate string is present.

```
Two-stage (default):
  estimate τ̂(x) → optimize π(x) based on τ̂
  + Interpretable τ̂ values; declarative constraints; auditable
  + Calibration requirement: τ̂ must be well-calibrated (ref 04)
  − Two optimization gaps: estimation error + allocation error

End-to-end (E3IR, RecSys 2024; Booking 2024):
  train model directly on rank / allocation objective
  + Optimizes what you actually care about (rank quality / revenue)
  + Monotonicity constraints (discount₁ ≤ discount₂ effects) easily encoded
  − Less interpretable magnitude; harder to audit individual decisions
  − Requires more data to converge; L2+ only
```

**Default: two-stage.** Switch to end-to-end only when: (a) you have large
training data (≥1M treated observations), (b) calibration is genuinely hard
(zero-inflated revenue), and (c) interpretability requirements are met via
separate explanation layer.

## OPE: Offline Evaluation Before Launch (the core L2 capability)

Don't launch and gamble. Use historical logs (containing propensity p(t|x),
→ ref 03) to estimate V(π_new) offline:

```
IPS (inverse propensity weighting):
  V̂ = (1/n) Σ  𝟙[π(xᵢ)=tᵢ] / p(tᵢ|xᵢ) × yᵢ

SNIPS (self-normalized IPS):
  V̂ = IPS numerator / sum of weights  — lower variance; use this by default

DR (doubly robust):
  V̂ = model extrapolation + IPS correction on residuals
    — more stable when support is insufficient
```

Full implementation in `scripts/ope_estimators.py`.

### Large Action Space OPE (>100 arms, recommendation/ad settings)

Standard IPS breaks when the action space is large: the probability that
π_new's action appears in historical logs approaches zero → weight explosion.

**Solution ladder**:

1. **MIPS** (Marginalized IPS, Saito & Joachims 2022): marginalize over
   action embeddings rather than individual arms. Requires a learned action
   embedding space where similar arms share statistical strength.
   ```
   V̂_MIPS = (1/n) Σ [π_new(e|x) / p_logged(e|x)] × y
   ```
   where e = action embedding (cluster), not individual arm id.

2. **OffCEM** (Saito et al. 2023): cluster actions by context-conditional
   similarity; estimate OPE within clusters. Better bias-variance tradeoff
   than MIPS when action clusters are dense.

3. **Embedding-weighted OPE** (practical default for large action spaces):
   - Train an action embedding on historical co-occurrence or feature
     similarity
   - Compute importance weights in the lower-dimensional embedding space
   - Use DR correction to debias residuals

**Reference implementation**: Open Bandit Pipeline (OBP) library provides
MIPS and embedding-based OPE estimators for production use.
`pip install obp`

**Support check adaption for large action space**: instead of checking
individual arm overlap, check embedding-space coverage — fraction of
π_new's recommendation embedding mass covered by logs.

### Conformal OPE (Finite-Sample Valid Intervals)

Standard OPE gives asymptotic confidence intervals that can be unreliable
in finite samples. **Conformal prediction for OPE** provides finite-sample
valid prediction intervals under mild assumptions:

```
Use split conformal: calibrate residuals on a held-out log set,
construct prediction intervals for ΔV̂.
```

When the OPE CI is tight asymptotically but the sample is <10k, apply
conformal calibration before reporting the interval. `pip install mapie`

### Safe OPG: Launch Guardrail Ordering

**Safe Off-Policy Gradient (Safe OPG)**: when launching a new policy, apply
strict conservative constraints first and relax as data accumulates:

```
Round 1 (first 1–4 weeks): enforce ΔV̂ ≥ 0 AND
  worst-case lower bound (1−ε credible interval) > 0
Round 2 (subsequent retraining): relax to point estimate > 0
  with CI does not cross zero
```

This prevents the scenario where a noise-favorable OPE estimate launches
a policy that is actually worse than current, with irreversible rollout
effects (couponing patterns, user expectations already shifted).

**Support check (must run before anything else)**: the (x, t) pairs recommended
by π_new must appear in the historical log with non-zero probability. A new
action that was never deployed → IPS/DR cannot save you → small-traffic
experiment only. Check: compute the share of π_new's selections where the
historical propensity < threshold (e.g., 0.01); if > 5%, do not trust the OPE
result.

## Launch Sequence (fixed order)

```
1. Offline OPE: ΔV̂ > 0 and CI does not cross zero
2. Small-traffic experiment (5–10%): validate OPE estimate, calibrate magnitude
3. Full launch, retaining two permanent controls:
   a. GCG (receives no action) → measures total incremental lift
   b. Current-policy holdout → measures new policy's incremental gain
4. Guardrail monitoring (defined in ref 01); breach triggers auto-rollback
```

## Common Failure Modes

- **No propensity log**: OPE fails at step one. Ref 03: this is a data
  engineering debt; the earlier it's paid, the cheaper it is.
- **Support gap ignored**: the new policy loves actions the historical log
  rarely deployed; IPS weights explode; ΔV̂ is an illusion.
- **Argmax without budget constraint**: model says 40% of users deserve a
  coupon; budget covers only 10% — without λ*, first-come-first-served
  wastes budget on mediocre-ROI users.
- **Reporting absolute V(π) instead of ΔV**: the business wants "how much more
  did we earn vs current policy", not the absolute policy value.
- **Removing the holdout after launch**: "we've already validated it" —
  environment drifts; the permanent holdout is what keeps you honest
  (also critical for ref 07 and ref 08).

## Acceptance Checklist

- [ ] Calibrated τ̂_t(x) and cost c_t available for every action
- [ ] Budget constraint explicitly modeled; λ* computed
- [ ] Support check passed before OPE; for large action spaces use
      embedding-space coverage check
- [ ] Two-stage vs end-to-end decision documented with rationale
- [ ] Launch sequence followed: OPE → small traffic → full launch with
      dual holdouts
- [ ] Safe OPG conservative constraints in round 1 deployment
- [ ] Guardrails and auto-rollback wired up

## Literature

- Dudík, Langford & Li (2011) "Doubly Robust Policy Evaluation and Learning"
- Athey & Wager (2021, *Econometrica*) "Policy Learning with Observational Data"
- Swaminathan & Joachims (2015) "The Self-Normalized Estimator for
  Counterfactual Learning" — SNIPS
- Saito & Joachims (2022, ICML) "Off-Policy Evaluation for Large Action Spaces
  via Embeddings" — MIPS estimator
- Saito et al. (2023) "OffCEM: Off-Policy Evaluation via Causal Effect
  Estimation for Large Action Spaces"
- Kiyohara et al. (2021) "Open Bandit Pipeline" — OBP reference implementation
- Hitsch, Misra & Sanders (2024, QME) — comprehensive policy evaluation
  framework for marketing
- [pymc-marketing](https://github.com/pymc-labs/pymc-marketing)
  `BudgetOptimizer` (open source) — Bayesian **channel-level** budget
  allocation over saturation response curves; the channel-level complement
  to the person-level λ* rule here (`policy_budget.py`). Use it when the
  question is "how much per channel", not "which person gets which action"
