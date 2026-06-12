"""Uplift 实验功效计算器（参见 references/03-experiments.md）。

两个问题：
1. 检测 ATE（普通 A/B）需要多少样本
2. 检测两个子群的 uplift 差异（HTE 最小问题）需要多少样本 —— 约为前者 4 倍

用法：
    python power_analysis.py                # 跑内置示例
    在代码中 import 后调用 n_per_arm_ate / n_per_arm_hte
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
    """普通 A/B（两比例 z 检验）每组所需样本量。

    baseline_rate: 控制组转化率，如 0.05
    mde_abs: 最小可检测的绝对提升，如 0.005（即 0.5pp）
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
    """检测两个子群 uplift 差异（τ_A − τ_B）每个 cell 所需样本量。

    共 4 个 cell：A-treated / A-control / B-treated / B-control。
    方差是四个组之和（差异的差异），这就是 HTE 比 ATE 贵 ~4 倍的来源。
    """
    delta = abs(uplift_a - uplift_b)
    if delta == 0:
        raise ValueError("两子群 uplift 相同，差异不可检测")
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
    """给定总样本量与每日可入组用户数，估算实验天数。"""
    return math.ceil(n_total / eligible_users_per_day)


def max_segments(
    total_users: int,
    baseline_rate: float,
    mde_abs: float,
    treated_share: float = 0.5,
    alpha: float = 0.05,
    power: float = 0.8,
) -> int:
    """给定总样本，最多能把人群分成几个子群仍保有检测 MDE 的功效。

    分群数翻倍 → 每群样本减半 → 可检测 MDE 涨 √2 倍。
    这是"分得太细全是噪声"的量化版本。
    """
    n_needed = n_per_arm_ate(baseline_rate, mde_abs, alpha, power)
    per_segment = n_needed / min(treated_share, 1 - treated_share)
    return max(1, int(total_users // per_segment))


if __name__ == "__main__":
    base, mde = 0.05, 0.005

    n_ab = n_per_arm_ate(base, mde)
    print(f"[ATE] 基线 {base:.1%}, MDE {mde:.1%} → 每组 {n_ab:,} 人，共 {2 * n_ab:,}")

    n_hte = n_per_cell_hte(
        baseline_rate_a=0.05, baseline_rate_b=0.05,
        uplift_a=0.010, uplift_b=0.005,
    )
    print(f"[HTE] 检测两子群 uplift 差 0.5pp → 每 cell {n_hte:,} 人，共 {4 * n_hte:,}")
    print(f"      HTE/ATE 样本倍数 ≈ {4 * n_hte / (2 * n_ab):.1f}x")

    k = max_segments(total_users=2_000_000, baseline_rate=base, mde_abs=mde)
    print(f"[分群上限] 200万用户、保持检测 {mde:.1%} 的功效 → 最多 {k} 个子群")

    days = experiment_duration_days(4 * n_hte, eligible_users_per_day=30_000)
    print(f"[时长] 每日入组 3 万 → HTE 实验约需 {days} 天")
