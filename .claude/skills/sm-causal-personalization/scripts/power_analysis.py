"""Uplift experiment power calculator (see references/03-experiments.md).

Two questions:
1. Sample required to detect ATE (standard A/B)
2. Sample required to detect an uplift difference between two subgroups
   (the minimal HTE question) — roughly 4× the standard A/B requirement

Usage:
    python power_analysis.py            # run built-in examples
    import as module: n_per_arm_ate / n_per_arm_hte
"""

from __future__ import annotations

import math

from scipy import stats


def n_per_arm_ate(
    baseline_rate: float,
    mde_abs: float,
    alpha: float = 0.05,
    power: float = 0.8,
) -> int:
    """Per-arm sample size for a standard A/B test (two-proportion z-test).

    baseline_rate: control group conversion rate, e.g. 0.05
    mde_abs:       minimum detectable absolute lift, e.g. 0.005 (0.5 pp)
    """
    p0, p1 = baseline_rate, baseline_rate + mde_abs
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    p_bar = (p0 + p1) / 2
    n = ((z_a * math.sqrt(2 * p_bar * (1 - p_bar))
          + z_b * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) / mde_abs) ** 2
    return math.ceil(n)


def n_per_cell_hte(
    baseline_rate_a: float,
    baseline_rate_b: float,
    uplift_a: float,
    uplift_b: float,
    alpha: float = 0.05,
    power: float = 0.8,
) -> int:
    """Per-cell sample size to detect an uplift difference (τ_A − τ_B).

    Requires 4 cells: A-treated / A-control / B-treated / B-control.
    Variance is the sum of all four cell variances (difference-in-differences).
    This is the mathematical source of the ~4× rule vs standard A/B.
    """
    delta = abs(uplift_a - uplift_b)
    if delta == 0:
        raise ValueError("Uplifts are identical; difference is not detectable.")
    rates = [
        baseline_rate_a + uplift_a,  # A treated
        baseline_rate_a,             # A control
        baseline_rate_b + uplift_b,  # B treated
        baseline_rate_b,             # B control
    ]
    var_sum = sum(p * (1 - p) for p in rates)
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    n = var_sum * ((z_a + z_b) / delta) ** 2
    return math.ceil(n)


def experiment_duration_days(n_total: int, eligible_users_per_day: int) -> int:
    """Estimate experiment duration given total sample and daily eligible users."""
    return math.ceil(n_total / eligible_users_per_day)


def max_segments(
    total_users: int,
    baseline_rate: float,
    mde_abs: float,
    treated_share: float = 0.5,
    alpha: float = 0.05,
    power: float = 0.8,
) -> int:
    """Maximum number of segments still detectable at the target MDE given total users.

    Doubling segments halves per-segment sample → MDE grows by √2.
    Quantifies "too many segments = pure noise."
    """
    n_needed = n_per_arm_ate(baseline_rate, mde_abs, alpha, power)
    per_segment = n_needed / min(treated_share, 1 - treated_share)
    return max(1, int(total_users // per_segment))


if __name__ == "__main__":
    base, mde = 0.05, 0.005

    n_ab = n_per_arm_ate(base, mde)
    print(f"[ATE] baseline {base:.1%}, MDE {mde:.1%} → {n_ab:,} per arm, {2 * n_ab:,} total")

    n_hte = n_per_cell_hte(
        baseline_rate_a=0.05, baseline_rate_b=0.05,
        uplift_a=0.010, uplift_b=0.005,
    )
    print(f"[HTE] detect 0.5pp uplift difference → {n_hte:,} per cell, {4 * n_hte:,} total")
    print(f"      HTE/ATE sample multiplier ≈ {4 * n_hte / (2 * n_ab):.1f}×")

    k = max_segments(total_users=2_000_000, baseline_rate=base, mde_abs=mde)
    print(f"[Segment cap] 2M users, maintain power to detect {mde:.1%} → at most {k} segments")

    days = experiment_duration_days(4 * n_hte, eligible_users_per_day=30_000)
    print(f"[Duration] 30k eligible/day → HTE experiment needs ~{days} days")
