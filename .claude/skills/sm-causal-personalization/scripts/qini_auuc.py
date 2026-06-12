"""Uplift model validation: Qini curve, AUUC, and decile calibration.

See references/04-hte-estimation.md.
Do NOT use AUC / accuracy to validate uplift models — individual-level τ labels
are unobservable. Use the randomized-data, group-level methods below.

Input convention (holdout set, from a randomized experiment):
    y:     outcome (n,)  binary or continuous
    t:     treatment indicator (n,)  0/1
    score: model-estimated τ̂(x) (n,)

Usage:
    python qini_auuc.py        # synthetic data demo: metrics + qini_curve.png
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def qini_curve(y: np.ndarray, t: np.ndarray, score: np.ndarray, n_bins: int = 100):
    """Sort by score descending, progressively expand targeting fraction, compute cumulative lift.

    Returns DataFrame: frac (targeting fraction), qini (cumulative incremental units,
    normalized to treated-group scale).
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
        # cumulative lift = treated conversions − control conversions (rescaled to treated volume)
        qini = yk[tk == 1].sum() - yk[tk == 0].sum() * (n_t / n_c)
        fracs.append(k / n)
        qinis.append(qini)
    return pd.DataFrame({"frac": fracs, "qini": qinis})


def auuc(y: np.ndarray, t: np.ndarray, score: np.ndarray, n_bins: int = 100) -> float:
    """AUUC: area under Qini curve minus area under random baseline (diagonal).
    Positive AUUC means the model has rank-ordering ability; zero/negative means it does not.
    """
    df = qini_curve(y, t, score, n_bins)
    total = df["qini"].iloc[-1]
    model_area = np.trapezoid(df["qini"], df["frac"])
    random_area = total / 2  # random ordering: straight line from 0 to total
    return float(model_area - random_area)


def decile_calibration(
    y: np.ndarray, t: np.ndarray, score: np.ndarray, n_buckets: int = 10
) -> pd.DataFrame:
    """Decile calibration table: bucket by τ̂, compare predicted vs actual treated−control gap.

    A good model should be monotone and calibrated: a bucket predicting 3% should
    actually show ~3% uplift. Correct rank but wrong magnitude → policy
    optimization in ref 06 will be systematically wrong.
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
    """Synthetic randomized data: true uplift correlates with x1; propensity correlates with x2.
    The propensity-as-uplift anti-pattern is demonstrated explicitly.
    """
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)               # drives uplift
    x2 = rng.normal(size=n)               # drives baseline purchase rate
    t = rng.binomial(1, 0.5, n)           # randomized
    base = 1 / (1 + np.exp(-(x2 - 2.5))) # baseline conversion ~7%
    tau = np.clip(0.03 * x1 + 0.03, 0, None)  # true uplift, mean ~3pp
    y = rng.binomial(1, np.clip(base + t * tau, 0, 1))
    good_score = tau + rng.normal(0, 0.01, n)   # near-oracle model
    propensity_score = base                      # anti-pattern: propensity used as uplift score
    return y, t, good_score, propensity_score


if __name__ == "__main__":
    y, t, good, prop = _synthetic()

    print(f"Uplift model   AUUC = {auuc(y, t, good):8.1f}  (should be significantly > 0)")
    print(f"Propensity anti-pattern AUUC = {auuc(y, t, prop):8.1f}  (≈0 or negative)")

    print("\nDecile calibration (uplift model, bucket 9 = highest τ̂):")
    print(decile_calibration(y, t, good).to_string(index=False, float_format="%.4f"))

    path = plot_qini(y, t, good)
    print(f"\nQini curve saved to: {path}")
