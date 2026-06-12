"""HTE estimation starter: T-learner / X-learner / DR-learner (pure sklearn).

See references/04-hte-estimation.md default estimation path:
  - Balanced randomized data → DR-learner (or EconML CausalForestDML)
  - Imbalanced treatment/control (e.g., 95/5 GCG) → X-learner
  - T-learner as baseline comparison

To migrate to production libraries:
    from econml.dml import CausalForestDML       # with valid confidence intervals
    from econml.dr import DRLearner
    from causalml.inference.meta import BaseXRegressor

Usage:
    python hte_starter.py     # synthetic data: compare three learners by AUUC
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split


def _default_clf():
    return GradientBoostingClassifier(max_depth=3, n_estimators=200)


def _default_reg():
    return GradientBoostingRegressor(max_depth=3, n_estimators=200)


def t_learner(X, y, t):
    """Train separate outcome models for treated and control. Simple baseline;
    performs poorly under imbalance."""
    m1 = _default_clf().fit(X[t == 1], y[t == 1])
    m0 = _default_clf().fit(X[t == 0], y[t == 0])
    return lambda Xn: m1.predict_proba(Xn)[:, 1] - m0.predict_proba(Xn)[:, 1]


def x_learner(X, y, t, propensity: float | None = None):
    """X-learner: cross-imputed pseudo-effects + propensity-weighted combination.
    First choice when treatment/control is severely imbalanced.

    propensity: known treated fraction from a randomized experiment;
                None uses the sample proportion.
    """
    e = t.mean() if propensity is None else propensity
    m1 = _default_clf().fit(X[t == 1], y[t == 1])
    m0 = _default_clf().fit(X[t == 0], y[t == 0])
    # pseudo-effects: treated minus counterfactual from control model, and vice versa
    d1 = y[t == 1] - m0.predict_proba(X[t == 1])[:, 1]
    d0 = m1.predict_proba(X[t == 0])[:, 1] - y[t == 0]
    g1 = _default_reg().fit(X[t == 1], d1)
    g0 = _default_reg().fit(X[t == 0], d0)
    # weight by opposite group's propensity: small group borrows strength from large group
    return lambda Xn: (1 - e) * g1.predict(Xn) + e * g0.predict(Xn)


def dr_learner(X, y, t, propensity: float | None = None, n_splits: int = 2, seed: int = 0):
    """DR-learner: cross-fitting constructs doubly robust pseudo-outcomes, then regresses on X.
    Consistent if either nuisance model (outcome or propensity) is correctly specified.
    In randomized data, the propensity is known exactly — even stronger guarantee.
    """
    rng = np.random.default_rng(seed)
    e = t.mean() if propensity is None else propensity
    n = len(y)
    folds = rng.integers(0, n_splits, n)
    pseudo = np.zeros(n)
    for k in range(n_splits):
        tr, te = folds != k, folds == k
        m1 = _default_clf().fit(X[tr & (t == 1)], y[tr & (t == 1)])
        m0 = _default_clf().fit(X[tr & (t == 0)], y[tr & (t == 0)])
        mu1 = m1.predict_proba(X[te])[:, 1]
        mu0 = m0.predict_proba(X[te])[:, 1]
        yt, tt = y[te], t[te]
        # AIPW pseudo-outcome: model extrapolation + IPW residual correction
        pseudo[te] = (mu1 - mu0
                      + tt * (yt - mu1) / e
                      - (1 - tt) * (yt - mu0) / (1 - e))
    final = _default_reg().fit(X, pseudo)
    return lambda Xn: final.predict(Xn)


def _synthetic(n=60_000, treated_share=0.5, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 5))
    t = rng.binomial(1, treated_share, n)
    base = 1 / (1 + np.exp(-(X[:, 1] - 2.0)))
    tau = np.clip(0.04 * X[:, 0] + 0.04, 0, None)   # true τ(x)
    y = rng.binomial(1, np.clip(base + t * tau, 0, 1))
    return X, y, t, tau


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from qini_auuc import auuc

    scenarios = [
        (0.5, 60_000,  "Balanced 50/50"),
        (0.95, 200_000, "Imbalanced 95/5 (GCG scenario: only 5% control)"),
    ]

    for share, n, label in scenarios:
        X, y, t, tau = _synthetic(n=n, treated_share=share)
        idx_tr, idx_te = train_test_split(np.arange(len(y)), test_size=0.4, random_state=1)
        Xtr, ytr, ttr = X[idx_tr], y[idx_tr], t[idx_tr]
        Xte, yte, tte, taute = X[idx_te], y[idx_te], t[idx_te], tau[idx_te]

        print(f"\n=== {label} ===")
        for name, fit in [("T-learner", t_learner),
                          ("X-learner", x_learner),
                          ("DR-learner", dr_learner)]:
            est = fit(Xtr, ytr, ttr)
            s = est(Xte)
            corr = np.corrcoef(s, taute)[0, 1]
            print(f"{name:11s}  corr(τ̂, τ_true)={corr:5.3f}   AUUC={auuc(yte, tte, s):8.1f}")
