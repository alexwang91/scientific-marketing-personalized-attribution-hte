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
- [ ] Support check passed before OPE
- [ ] Launch sequence followed: OPE → small traffic → full launch with
      dual holdouts
- [ ] Guardrails and auto-rollback wired up

## Literature

- Dudík, Langford & Li (2011) "Doubly Robust Policy Evaluation and Learning"
- Athey & Wager (2021, *Econometrica*) "Policy Learning with Observational Data"
- Swaminathan & Joachims (2015) "The Self-Normalized Estimator for
  Counterfactual Learning" — SNIPS
- Hitsch, Misra & Sanders (2024, QME) — comprehensive policy evaluation
  framework for marketing
