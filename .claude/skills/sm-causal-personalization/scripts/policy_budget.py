"""Budget-constrained policy allocation: λ* shadow price + policy value.

See references/06-policy-nbt.md. This is the Layer-3 tool of the four-layer
architecture: it turns τ̂(x) from Layer 2 into an allocation decision under a
budget constraint, and prices that constraint.

The problem (ref 06, "Budget / Capacity Constrained Case"):

    max Σᵢ [τ̂(xᵢ) × value − cᵢ]   s.t.   Σᵢ cᵢ ≤ B

Practical solution (Lagrangian / dual pricing): sort by incremental ROI
(τ̂ × value − c) / c descending and fund until the budget is exhausted.
The shadow price λ* is the marginal ROI of the last funded user; the
equivalent decision rule is

    treat x  iff  τ̂(x) × value − c ≥ λ* × c

λ* is "the minimum incremental return per unit of spend in this
organization" — a more useful management number than any point ROI.

Policy value is estimated on a RANDOMIZED holdout via inverse propensity
weighting — never on the training data, never from model predictions alone
(the OPE gate, ref 06 / ope_estimators.py).

Input convention:
    tau_hat: model-estimated incremental conversion probability τ̂(x)  (n,)
    value:   profit per incremental conversion (margin), scalar or (n,)
    cost:    cost of treating each user, scalar or (n,)
    budget:  total budget B

Usage:
    python policy_budget.py    # synthetic demo: uplift vs propensity vs random targeting
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def allocate(tau_hat, value, cost, budget: float) -> dict:
    """Greedy knapsack by incremental ROI (optimal up to the last fractional user).

    Returns dict with:
        treat          boolean mask (n,) — the policy π(x)
        lambda_star    shadow price: marginal ROI of the last funded user;
                       0.0 when the budget is not binding
        spend          total cost of the funded users
        n_treated      number of funded users
        budget_binding True if positive-ROI users were left unfunded
    """
    tau_hat = np.asarray(tau_hat, dtype=float)
    n = len(tau_hat)
    value = np.broadcast_to(np.asarray(value, dtype=float), (n,))
    cost = np.broadcast_to(np.asarray(cost, dtype=float), (n,))
    if np.any(cost <= 0):
        raise ValueError("cost must be strictly positive for every user")

    profit = tau_hat * value - cost          # incremental profit if treated
    roi = profit / cost                       # incremental return per unit of spend
    order = np.argsort(-roi)
    positive = roi[order] > 0
    fundable = positive & (np.cumsum(cost[order]) <= budget)

    treat = np.zeros(n, dtype=bool)
    treat[order[fundable]] = True
    budget_binding = bool(positive.sum() > fundable.sum())
    lambda_star = float(roi[order][fundable][-1]) if (budget_binding and fundable.any()) else 0.0
    return {
        "treat": treat,
        "lambda_star": lambda_star,
        "spend": float(cost[treat].sum()),
        "n_treated": int(treat.sum()),
        "budget_binding": budget_binding,
    }


def policy_incremental_profit(y, t, treat, p_treated: float, value, cost) -> float:
    """IPW estimate of E[incremental profit per user] of policy `treat`,
    evaluated on a randomized holdout with known treatment probability.

    For each user the incremental outcome is estimated with the
    Horvitz–Thompson transform y·t/p − y·(1−t)/(1−p), which is unbiased for
    τ(x) under randomization; the policy pays cost only where it treats.
    """
    y = np.asarray(y, dtype=float)
    t = np.asarray(t, dtype=int)
    treat = np.asarray(treat, dtype=bool)
    n = len(y)
    value = np.broadcast_to(np.asarray(value, dtype=float), (n,))
    cost = np.broadcast_to(np.asarray(cost, dtype=float), (n,))
    if not 0 < p_treated < 1:
        raise ValueError("p_treated must be in (0, 1)")
    uplift_ipw = y * t / p_treated - y * (1 - t) / (1 - p_treated)
    return float(np.mean(treat * (uplift_ipw * value - cost)))


def profit_curve(y, t, tau_hat, p_treated: float, value, cost,
                 n_points: int = 12) -> pd.DataFrame:
    """Incremental profit vs budget — the policy-level companion to the Qini curve.

    Sweeps the budget from ~0 to 'fund every positive-ROI user' and reports,
    per budget level: users funded, spend, λ*, and the IPW-estimated
    incremental profit per user on the randomized holdout.
    """
    tau_hat = np.asarray(tau_hat, dtype=float)
    n = len(tau_hat)
    value_b = np.broadcast_to(np.asarray(value, dtype=float), (n,))
    cost_b = np.broadcast_to(np.asarray(cost, dtype=float), (n,))
    max_spend = float(cost_b[tau_hat * value_b - cost_b > 0].sum())
    if max_spend == 0:
        return pd.DataFrame(columns=["budget", "n_treated", "spend",
                                     "lambda_star", "profit_per_user"])
    rows = []
    for budget in np.linspace(max_spend / n_points, max_spend, n_points):
        a = allocate(tau_hat, value, cost, budget)
        rows.append({
            "budget": budget,
            "n_treated": a["n_treated"],
            "spend": a["spend"],
            "lambda_star": a["lambda_star"],
            "profit_per_user": policy_incremental_profit(
                y, t, a["treat"], p_treated, value, cost),
        })
    return pd.DataFrame(rows)


def _synthetic(n: int = 200_000, seed: int = 0):
    """Randomized holdout in the qini_auuc.py convention: true uplift is driven
    by x1, baseline purchase rate by x2 (the propensity anti-pattern axis)."""
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    t = rng.binomial(1, 0.5, n)
    base = 1 / (1 + np.exp(-(x2 - 2.5)))
    tau = np.clip(0.03 * x1 + 0.03, 0, None)
    y = rng.binomial(1, np.clip(base + t * tau, 0, 1))
    score = tau + rng.normal(0, 0.01, n)      # near-oracle uplift model
    propensity_score = base                    # anti-pattern comparator
    return y, t, score, propensity_score, tau


if __name__ == "__main__":
    VALUE, COST = 30.0, 1.0                   # margin per incremental conversion; cost per contact
    y, t, score, prop, tau = _synthetic()
    n = len(y)
    budget = 0.20 * COST * n                   # can afford to contact 20% of users

    a = allocate(score, VALUE, COST, budget)
    print(f"Budget covers 20% of users → fund {a['n_treated']:,} users "
          f"(spend {a['spend']:,.0f}), λ* = {a['lambda_star']:.3f}")
    print(f"Decision rule: treat iff τ̂ × {VALUE:.0f} − {COST:.0f} ≥ {a['lambda_star']:.3f} × {COST:.0f}\n")

    rng = np.random.default_rng(1)
    same_n = a["n_treated"]
    random_mask = np.zeros(n, dtype=bool)
    random_mask[rng.choice(n, same_n, replace=False)] = True
    prop_mask = np.zeros(n, dtype=bool)
    prop_mask[np.argsort(-prop)[:same_n]] = True

    policies = [
        ("uplift targeting (λ*)", a["treat"]),
        ("propensity targeting", prop_mask),
        ("random targeting", random_mask),
        ("treat everyone", np.ones(n, dtype=bool)),
    ]
    print(f"{'policy':24s} {'est. profit/user (IPW)':>24s} {'true profit/user':>18s}")
    for name, mask in policies:
        est = policy_incremental_profit(y, t, mask, 0.5, VALUE, COST)
        true = float(np.mean(mask * (tau * VALUE - COST)))
        print(f"{name:24s} {est:24.4f} {true:18.4f}")

    print("\nProfit curve (budget sweep):")
    curve = profit_curve(y, t, score, 0.5, VALUE, COST, n_points=8)
    print(curve.to_string(index=False, float_format="%.3f"))
    print("\nRead: profit/user rises steeply while λ* is high, then flattens — "
          "the flat tail is budget that should not be spent.")
