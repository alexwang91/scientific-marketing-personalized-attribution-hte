"""HTE 估计起手式：T-learner / X-learner / DR-learner（sklearn 纯实现）。

参见 references/04-hte-estimation.md 的默认路径：
  - 平衡随机化数据 → DR-learner（或 EconML CausalForestDML）
  - treatment/control 悬殊（如 95/5 GCG）→ X-learner
  - T-learner 作 baseline 对照

生产环境换 EconML / CausalML：
  from econml.dml import CausalForestDML            # 含置信区间
  from econml.dr import DRLearner
  from causalml.inference.meta import BaseXRegressor

用法：
    python hte_starter.py     # 合成数据演示，对比三个 learner 的 AUUC
"""

from __future__ import annotations

import numpy as np
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split


def _default_clf():
    return GradientBoostingClassifier(max_depth=3, n_estimators=200)


def _default_reg():
    return GradientBoostingRegressor(max_depth=3, n_estimators=200)


def t_learner(X, y, t):
    """treated/control 各训一个 outcome 模型。简单 baseline，不平衡时偏差大。"""
    m1 = _default_clf().fit(X[t == 1], y[t == 1])
    m0 = _default_clf().fit(X[t == 0], y[t == 0])
    return lambda Xn: m1.predict_proba(Xn)[:, 1] - m0.predict_proba(Xn)[:, 1]


def x_learner(X, y, t, propensity: float | None = None):
    """X-learner：交叉插补伪效应再回归，倾向性加权合成。不平衡数据首选。

    propensity: 随机化实验中的已知 treated 比例；None 则用样本比例。
    """
    e = t.mean() if propensity is None else propensity
    m1 = _default_clf().fit(X[t == 1], y[t == 1])
    m0 = _default_clf().fit(X[t == 0], y[t == 0])
    # 伪效应：treated 用自身减 control 模型的反事实，control 反之
    d1 = y[t == 1] - m0.predict_proba(X[t == 1])[:, 1]
    d0 = m1.predict_proba(X[t == 0])[:, 1] - y[t == 0]
    g1 = _default_reg().fit(X[t == 1], d1)
    g0 = _default_reg().fit(X[t == 0], d0)
    # 权重 = 对方组的倾向性：小组的估计借大组模型的力
    return lambda Xn: (1 - e) * g1.predict(Xn) + e * g0.predict(Xn)


def dr_learner(X, y, t, propensity: float | None = None, n_splits: int = 2, seed: int = 0):
    """DR-learner：cross-fitting 构造 doubly robust 伪结果，再回归到 X。

    nuisance（μ0/μ1/e）有一个估对就一致；随机化数据中 e 已知，更稳。
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
        mu1, mu0 = m1.predict_proba(X[te])[:, 1], m0.predict_proba(X[te])[:, 1]
        yt, tt = y[te], t[te]
        # AIPW 伪结果：模型外推 + 残差的逆倾向修正
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
    tau = np.clip(0.04 * X[:, 0] + 0.04, 0, None)   # 真实 τ(x)
    y = rng.binomial(1, np.clip(base + t * tau, 0, 1))
    return X, y, t, tau


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from qini_auuc import auuc

    for share, n, label in [(0.5, 60_000, "平衡 50/50"),
                            (0.95, 200_000, "不平衡 95/5（GCG 场景：control 只有 5%）")]:
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
