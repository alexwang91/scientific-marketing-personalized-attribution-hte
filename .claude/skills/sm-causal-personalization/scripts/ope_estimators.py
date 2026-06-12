"""离线策略评估（OPE）：IPS / SNIPS / Doubly Robust + support 检查。

参见 references/06-policy-nbt.md。前提：日志含倾向性 p(t|x)（见 03）。
没有倾向性日志，本文件帮不了你——先回去补埋点。

输入约定（历史日志，每行一次决策）：
    y_logged:    实际观察到的结果 (n,)
    t_logged:    实际执行的动作 (n,) 整数编码 0..K-1
    p_logged:    当时该动作被选中的概率 (n,)   ← 关键字段
    pi_new:      新策略对每行的动作选择 (n,) 整数编码
    q_hat:       可选，outcome 模型 Q̂(x,t) 的预测 (n, K)，DR 用

用法：
    python ope_estimators.py    # 合成日志演示：OPE 估计 vs 真值
"""

from __future__ import annotations

import numpy as np


def support_check(t_logged, p_logged, pi_new, min_propensity: float = 0.01) -> dict:
    """OPE 之前必跑。新策略选中的动作在日志里支持不足 → OPE 结果不可信。"""
    match = (pi_new == t_logged)
    weak = match & (p_logged < min_propensity)
    coverage = float(match.mean())            # 新策略与日志动作重合率
    weak_share = float(weak.sum() / max(match.sum(), 1))
    verdict = "OK" if weak_share < 0.05 else "支持不足——OPE 不可信，走小流量实验"
    return {"coverage": coverage, "weak_support_share": weak_share, "verdict": verdict}


def ips(y_logged, t_logged, p_logged, pi_new) -> float:
    """逆倾向加权。无偏但方差大，倾向性小的样本权重爆炸。"""
    w = (pi_new == t_logged) / p_logged
    return float(np.mean(w * y_logged))


def snips(y_logged, t_logged, p_logged, pi_new) -> float:
    """自归一化 IPS。轻微有偏、方差小得多，默认选这个。"""
    w = (pi_new == t_logged) / p_logged
    return float(np.sum(w * y_logged) / np.sum(w))


def doubly_robust(y_logged, t_logged, p_logged, pi_new, q_hat) -> float:
    """DR：outcome 模型外推 + IPS 修正残差。模型或倾向性有一个对就一致。"""
    n = len(y_logged)
    q_pi = q_hat[np.arange(n), pi_new]            # 模型对新策略动作的预测
    q_t = q_hat[np.arange(n), t_logged]           # 模型对实际动作的预测
    w = (pi_new == t_logged) / p_logged
    return float(np.mean(q_pi + w * (y_logged - q_t)))


def bootstrap_ci(estimator, *args, n_boot: int = 400, alpha: float = 0.05, seed: int = 0):
    """任意 OPE 估计量的 bootstrap 置信区间。ΔV 的 CI 跨零就别上线。"""
    rng = np.random.default_rng(seed)
    n = len(args[0])
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        vals.append(estimator(*[a[idx] for a in args]))
    lo, hi = np.percentile(vals, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def _synthetic_logs(n=100_000, n_actions=3, seed=0):
    """合成日志：老策略按 propensity 倾斜选动作（典型历史日志），真值可算。"""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n)
    # 各动作真实期望收益：动作2对 x>0 好，动作1对 x<0 好，动作0是不动作
    true_q = np.stack([
        np.full(n, 0.05),
        0.08 - 0.03 * x,
        0.05 + 0.05 * x,
    ], axis=1).clip(0.01, 0.99)
    # 老策略：偏爱动作1（带探索），并记录倾向性
    logits = np.stack([np.zeros(n), np.ones(n) * 1.0, x * 0.5], axis=1)
    p_all = np.exp(logits) / np.exp(logits).sum(1, keepdims=True)
    t = np.array([rng.choice(n_actions, p=p) for p in p_all])
    p_logged = p_all[np.arange(n), t]
    y = rng.binomial(1, true_q[np.arange(n), t]).astype(float)
    # 新策略：按 x 选最优（贪心）
    pi_new = true_q.argmax(1)
    v_true_new = true_q[np.arange(n), pi_new].mean()
    v_true_old = (p_all * true_q).sum(1).mean()
    # outcome 模型：真值加噪声（演示 DR 的稳健性）
    q_hat = (true_q + rng.normal(0, 0.02, true_q.shape)).clip(0, 1)
    return y, t, p_logged, pi_new, q_hat, v_true_new, v_true_old


if __name__ == "__main__":
    y, t, p, pi, q_hat, v_new, v_old = _synthetic_logs()

    print("Support 检查:", support_check(t, p, pi))
    print(f"\n真值:  V(π_new) = {v_new:.4f}   V(π_old) = {v_old:.4f}   ΔV = {v_new - v_old:+.4f}\n")

    v_ips = ips(y, t, p, pi)
    v_snips = snips(y, t, p, pi)
    v_dr = doubly_robust(y, t, p, pi, q_hat)
    lo, hi = bootstrap_ci(snips, y, t, p, pi)

    print(f"IPS    = {v_ips:.4f}")
    print(f"SNIPS  = {v_snips:.4f}   95% CI [{lo:.4f}, {hi:.4f}]")
    print(f"DR     = {v_dr:.4f}")
    print("\n上线判据：ΔV̂ = V̂(π_new) − V̂(π_old) 的 CI 不跨零，且 support 检查通过。")
