"""Off-Policy Evaluation: IPS / SNIPS / Doubly Robust + support check.

See references/06-policy-nbt.md. Requires propensity logs p(t|x) (ref 03).
If you have no propensity logs, this file cannot help you — instrument first.

Input convention (historical logs, one row per decision):
    y_logged:  observed outcome (n,)
    t_logged:  action actually taken (n,)  integer-coded 0..K-1
    p_logged:  probability the logged action was selected (n,)  ← critical field
    pi_new:    new policy's action choice for each row (n,)  integer-coded
    q_hat:     optional outcome model Q̂(x,t) predictions (n, K), used by DR

Usage:
    python ope_estimators.py    # synthetic log demo: OPE estimates vs ground truth
"""

from __future__ import annotations

import numpy as np


def support_check(t_logged, p_logged, pi_new, min_propensity: float = 0.01) -> dict:
    """Must run before any OPE. Insufficient support for the new policy → results unreliable."""
    match = (pi_new == t_logged)
    weak = match & (p_logged < min_propensity)
    coverage = float(match.mean())
    weak_share = float(weak.sum() / max(match.sum(), 1))
    verdict = ("OK" if weak_share < 0.05
               else "Insufficient support — OPE unreliable; run small-traffic experiment instead")
    return {"coverage": coverage, "weak_support_share": weak_share, "verdict": verdict}


def ips(y_logged, t_logged, p_logged, pi_new) -> float:
    """Inverse Propensity Weighting. Unbiased but high variance;
    small propensity values cause weight explosion."""
    w = (pi_new == t_logged) / p_logged
    return float(np.mean(w * y_logged))


def snips(y_logged, t_logged, p_logged, pi_new) -> float:
    """Self-Normalized IPS. Slightly biased, much lower variance. Use this by default."""
    w = (pi_new == t_logged) / p_logged
    return float(np.sum(w * y_logged) / np.sum(w))


def doubly_robust(y_logged, t_logged, p_logged, pi_new, q_hat) -> float:
    """Doubly Robust estimator. Consistent if either the outcome model or
    the propensity model is correctly specified."""
    n = len(y_logged)
    q_pi = q_hat[np.arange(n), pi_new]       # model prediction for new policy's action
    q_t = q_hat[np.arange(n), t_logged]      # model prediction for logged action
    w = (pi_new == t_logged) / p_logged
    return float(np.mean(q_pi + w * (y_logged - q_t)))


def bootstrap_ci(estimator, *args, n_boot: int = 400, alpha: float = 0.05, seed: int = 0):
    """Bootstrap confidence interval for any OPE estimator.
    If ΔV CI crosses zero, do not launch — run a real experiment.
    """
    rng = np.random.default_rng(seed)
    n = len(args[0])
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        vals.append(estimator(*[a[idx] for a in args]))
    lo, hi = np.percentile(vals, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def _synthetic_logs(n=100_000, n_actions=3, seed=0):
    """Synthetic logs: old policy selects actions with propensity bias (typical historical log).
    True values are computable, enabling validation of OPE estimates.
    """
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n)
    # true expected reward per action: action 2 is better for x>0, action 1 for x<0
    true_q = np.stack([
        np.full(n, 0.05),
        0.08 - 0.03 * x,
        0.05 + 0.05 * x,
    ], axis=1).clip(0.01, 0.99)
    # old policy: biased toward action 1 with exploration; propensity logged
    logits = np.stack([np.zeros(n), np.ones(n) * 1.0, x * 0.5], axis=1)
    p_all = np.exp(logits) / np.exp(logits).sum(1, keepdims=True)
    t = np.array([rng.choice(n_actions, p=p) for p in p_all])
    p_logged = p_all[np.arange(n), t]
    y = rng.binomial(1, true_q[np.arange(n), t]).astype(float)
    # new policy: greedy argmax on true rewards
    pi_new = true_q.argmax(1)
    v_true_new = true_q[np.arange(n), pi_new].mean()
    v_true_old = (p_all * true_q).sum(1).mean()
    # outcome model: true values + noise (demonstrates DR robustness)
    q_hat = (true_q + rng.normal(0, 0.02, true_q.shape)).clip(0, 1)
    return y, t, p_logged, pi_new, q_hat, v_true_new, v_true_old


if __name__ == "__main__":
    y, t, p, pi, q_hat, v_new, v_old = _synthetic_logs()

    print("Support check:", support_check(t, p, pi))
    print(f"\nGround truth:  V(π_new)={v_new:.4f}  V(π_old)={v_old:.4f}  ΔV={v_new - v_old:+.4f}\n")

    v_ips = ips(y, t, p, pi)
    v_snips = snips(y, t, p, pi)
    v_dr = doubly_robust(y, t, p, pi, q_hat)
    lo, hi = bootstrap_ci(snips, y, t, p, pi)

    print(f"IPS    = {v_ips:.4f}")
    print(f"SNIPS  = {v_snips:.4f}   95% CI [{lo:.4f}, {hi:.4f}]")
    print(f"DR     = {v_dr:.4f}")
    print("\nLaunch criterion: ΔV̂ CI does not cross zero AND support check passes.")
