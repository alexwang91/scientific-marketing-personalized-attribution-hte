"""Uplift 模型验证三件套：Qini 曲线、AUUC、分桶增量校准。

参见 references/04-hte-estimation.md。禁止用 AUC 验证 uplift 模型——
个体级 τ 不可观察，必须用以下随机化数据上的群体级方法。

输入约定（持出集，且来自随机化实验）：
    y:     结果 (n,)  0/1 或连续
    t:     是否 treated (n,) 0/1
    score: 模型输出的 τ̂(x) (n,)

用法：
    python qini_auuc.py        # 合成数据演示，输出指标并存 qini_curve.png
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def qini_curve(y: np.ndarray, t: np.ndarray, score: np.ndarray, n_bins: int = 100):
    """按 score 降序逐步扩大“投放比例”，计算累积增量。

    返回 DataFrame: frac（投放比例）, qini（累积增量人数，treated 规模口径）
    """
    order = np.argsort(-score)
    y, t = y[order], t[order]
    n = len(y)
    fracs, qinis = [0.0], [0.0]
    for k in np.linspace(n / n_bins, n, n_bins).astype(int):
        yk, tk = y[:k], t[:k]
        n_t, n_c = tk.sum(), (1 - tk).sum()
        if n_t == 0 or n_c == 0:
            continue
        # 累积增量 = treated 转化数 − control 转化数（折算到 treated 规模）
        qini = yk[tk == 1].sum() - yk[tk == 0].sum() * (n_t / n_c)
        fracs.append(k / n)
        qinis.append(qini)
    return pd.DataFrame({"frac": fracs, "qini": qinis})


def auuc(y: np.ndarray, t: np.ndarray, score: np.ndarray, n_bins: int = 100) -> float:
    """AUUC：Qini 曲线下面积减去随机基线（对角线）下面积。>0 才有排序能力。"""
    df = qini_curve(y, t, score, n_bins)
    total = df["qini"].iloc[-1]
    model_area = np.trapezoid(df["qini"], df["frac"])
    random_area = total / 2  # 随机排序的 Qini 是从 0 到 total 的直线
    return float(model_area - random_area)


def decile_calibration(
    y: np.ndarray, t: np.ndarray, score: np.ndarray, n_buckets: int = 10
) -> pd.DataFrame:
    """分桶增量校准表：按 τ̂ 分桶，对比桶内预测均值与实际 treated−control 差。

    好模型应当：actual_uplift 随桶单调上升，且与 predicted_uplift 量级一致。
    排序对但量级错 → 06 的利润优化全错，必须先校准。
    """
    df = pd.DataFrame({"y": y, "t": t, "score": score})
    df["bucket"] = pd.qcut(df["score"], n_buckets, labels=False, duplicates="drop")
    rows = []
    for b, g in df.groupby("bucket"):
        gt, gc = g[g.t == 1], g[g.t == 0]
        if len(gt) == 0 or len(gc) == 0:
            continue
        rows.append({
            "bucket": int(b),
            "n": len(g),
            "predicted_uplift": g["score"].mean(),
            "actual_uplift": gt["y"].mean() - gc["y"].mean(),
        })
    return pd.DataFrame(rows).sort_values("bucket", ascending=False)


def plot_qini(y, t, score, path: str = "qini_curve.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = qini_curve(y, t, score)
    total = df["qini"].iloc[-1]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(df["frac"], df["qini"], label=f"model (AUUC={auuc(y, t, score):.1f})")
    ax.plot([0, 1], [0, total], "--", color="gray", label="random")
    ax.set_xlabel("targeted fraction")
    ax.set_ylabel("cumulative incremental conversions")
    ax.set_title("Qini curve")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    return path


def _synthetic(n: int = 200_000, seed: int = 0):
    """合成随机化数据：真实 uplift 与 x1 正相关，propensity 与 x2 相关（混淆项演示）。"""
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)               # 驱动 uplift
    x2 = rng.normal(size=n)               # 驱动基线购买率
    t = rng.binomial(1, 0.5, n)           # 随机化
    base = 1 / (1 + np.exp(-(x2 - 2.5)))  # 基线转化 ~7%
    tau = np.clip(0.03 * x1 + 0.03, 0, None)  # 真实 uplift，均值 ~3pp
    y = rng.binomial(1, np.clip(base + t * tau, 0, 1))
    good_score = tau + rng.normal(0, 0.01, n)   # 接近真值的模型
    propensity_score = base                      # 反面教材：propensity 当 uplift 用
    return y, t, good_score, propensity_score


if __name__ == "__main__":
    y, t, good, prop = _synthetic()

    print(f"uplift 模型   AUUC = {auuc(y, t, good):8.1f}  （应显著 > 0）")
    print(f"propensity 冒充 AUUC = {auuc(y, t, prop):8.1f}  （反面教材：≈0 或为负）")

    print("\n分桶校准（uplift 模型，桶 9 = τ̂ 最高）：")
    print(decile_calibration(y, t, good).to_string(index=False, float_format="%.4f"))

    path = plot_qini(y, t, good)
    print(f"\nQini 曲线已保存: {path}")
