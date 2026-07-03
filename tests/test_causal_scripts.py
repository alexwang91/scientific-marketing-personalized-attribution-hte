#!/usr/bin/env python3
"""Numeric regression tests for the causal core scripts:
qini_auuc.py, power_analysis.py, ope_estimators.py.

Requires numpy / pandas / scipy; skips gracefully when they are absent so
scripts/run_all_checks.py stays runnable in a stdlib-only environment.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "scripts"

try:
    import numpy as np  # noqa: F401
    import pandas  # noqa: F401
    import scipy  # noqa: F401
except ImportError as exc:
    print(f"SKIP test_causal_scripts: scientific deps unavailable ({exc.name})")
    raise SystemExit(0)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


qini = _load("qini_auuc")
power = _load("power_analysis")
ope = _load("ope_estimators")
pb = _load("policy_budget")


def test_auuc_positive_for_good_model_and_flat_for_noise():
    y, t, good, _ = qini._synthetic(n=40_000, seed=0)
    rng = np.random.default_rng(1)
    noise = rng.normal(size=len(y))
    auuc_good = qini.auuc(y, t, good)
    auuc_noise = qini.auuc(y, t, noise)
    assert auuc_good > 0, auuc_good
    assert auuc_good > 5 * abs(auuc_noise), (auuc_good, auuc_noise)


def test_propensity_score_is_not_an_uplift_score():
    # the anti-pattern demo must stay an anti-pattern: baseline propensity
    # carries no rank information about uplift here
    y, t, good, prop = qini._synthetic(n=40_000, seed=0)
    assert qini.auuc(y, t, good) > qini.auuc(y, t, prop)


def test_decile_calibration_shape_and_rank():
    y, t, good, _ = qini._synthetic(n=40_000, seed=0)
    df = qini.decile_calibration(y, t, good)
    assert set(df.columns) == {"bucket", "n", "predicted_uplift", "actual_uplift"}
    assert len(df) <= 10
    top, bottom = df.iloc[0], df.iloc[-1]
    assert top["actual_uplift"] > bottom["actual_uplift"]


def test_n_per_arm_ate_scales_inverse_square_with_mde():
    n1 = power.n_per_arm_ate(0.05, 0.005)
    n2 = power.n_per_arm_ate(0.05, 0.0025)
    ratio = n2 / n1
    assert 3.7 < ratio < 4.3, ratio
    # reference: Evan Miller's calculator gives 31,234/arm for 5% → 5.5%, α=.05, power=.8
    assert 30_500 < n1 < 32_000, n1


def test_hte_needs_roughly_4x_the_ate_sample():
    n_ab = power.n_per_arm_ate(0.05, 0.005)
    n_hte = power.n_per_cell_hte(0.05, 0.05, uplift_a=0.010, uplift_b=0.005)
    multiplier = 4 * n_hte / (2 * n_ab)
    assert 3.0 < multiplier < 6.0, multiplier


def test_identical_uplifts_rejected():
    try:
        power.n_per_cell_hte(0.05, 0.05, uplift_a=0.01, uplift_b=0.01)
    except ValueError:
        return
    raise AssertionError("expected ValueError for identical uplifts")


def test_ope_estimators_recover_ground_truth():
    y, t, p, pi, q_hat, v_true_new, _ = ope._synthetic_logs(n=50_000, seed=0)
    for name, v in [("ips", ope.ips(y, t, p, pi)),
                    ("snips", ope.snips(y, t, p, pi)),
                    ("dr", ope.doubly_robust(y, t, p, pi, q_hat))]:
        assert abs(v - v_true_new) < 0.02, (name, v, v_true_new)


def test_support_check_flags_low_coverage():
    # regression: a policy that almost never matches the logs used to pass "OK"
    n = 1_000
    t_logged = np.zeros(n, dtype=int)
    p_logged = np.full(n, 0.5)
    pi_new = np.ones(n, dtype=int)  # never matches
    result = ope.support_check(t_logged, p_logged, pi_new)
    assert result["coverage"] == 0.0
    assert result["verdict"] != "OK", result


def test_support_check_flags_weak_propensities():
    n = 1_000
    t_logged = np.zeros(n, dtype=int)
    p_logged = np.full(n, 0.001)  # matched rows logged at near-zero propensity
    pi_new = np.zeros(n, dtype=int)
    result = ope.support_check(t_logged, p_logged, pi_new)
    assert result["verdict"] != "OK", result


def test_support_check_ok_on_healthy_logs():
    y, t, p, pi, *_ = ope._synthetic_logs(n=20_000, seed=0)
    assert ope.support_check(t, p, pi)["verdict"] == "OK"


def test_allocate_binding_budget_toy_example():
    # 3 users, value=10: profits are 10*0.5-1=4 (roi 4), 10*0.3-1=2 (roi 2),
    # 10*0.05-1=-0.5 (roi<0). Budget 1 funds only the best user.
    tau, cost = [0.5, 0.05, 0.3], 1.0
    a = pb.allocate(tau, 10.0, cost, budget=1.0)
    assert list(a["treat"]) == [True, False, False]
    assert a["lambda_star"] == 4.0 and a["budget_binding"]
    # budget 2 funds both positive-ROI users; λ* = marginal (last funded) ROI
    a = pb.allocate(tau, 10.0, cost, budget=2.0)
    assert list(a["treat"]) == [True, False, True]
    assert a["lambda_star"] == 0.0 and not a["budget_binding"]


def test_allocate_never_funds_negative_roi_even_with_slack_budget():
    a = pb.allocate([0.5, 0.01], 10.0, 1.0, budget=100.0)
    assert list(a["treat"]) == [True, False]
    assert a["lambda_star"] == 0.0


def test_allocate_decision_rule_matches_lambda_star():
    y, t, score, _, _ = pb._synthetic(n=20_000, seed=0)
    a = pb.allocate(score, 30.0, 1.0, budget=0.2 * len(y))
    rule = (score * 30.0 - 1.0) >= a["lambda_star"] * 1.0
    agree = (rule == a["treat"]).mean()
    assert agree > 0.999, agree  # only cumsum boundary ties may differ


def test_uplift_policy_beats_propensity_and_treat_all():
    y, t, score, prop, tau = pb._synthetic(n=60_000, seed=0)
    n = len(y)
    a = pb.allocate(score, 30.0, 1.0, budget=0.2 * n)
    prop_mask = np.zeros(n, dtype=bool)
    prop_mask[np.argsort(-prop)[:a["n_treated"]]] = True
    p_uplift = pb.policy_incremental_profit(y, t, a["treat"], 0.5, 30.0, 1.0)
    p_prop = pb.policy_incremental_profit(y, t, prop_mask, 0.5, 30.0, 1.0)
    p_all = pb.policy_incremental_profit(y, t, np.ones(n, bool), 0.5, 30.0, 1.0)
    assert p_uplift > 0 > p_all, (p_uplift, p_all)
    assert p_uplift > p_prop, (p_uplift, p_prop)
    # IPW estimate should track the synthetic ground truth
    true_uplift = float(np.mean(a["treat"] * (tau * 30.0 - 1.0)))
    assert abs(p_uplift - true_uplift) < 0.05, (p_uplift, true_uplift)


def test_policy_value_of_treat_none_is_zero():
    y, t, score, *_ = pb._synthetic(n=5_000, seed=0)
    none = np.zeros(len(y), dtype=bool)
    assert pb.policy_incremental_profit(y, t, none, 0.5, 30.0, 1.0) == 0.0


def test_profit_curve_spend_monotone_and_lambda_decreasing():
    y, t, score, *_ = pb._synthetic(n=20_000, seed=0)
    curve = pb.profit_curve(y, t, score, 0.5, 30.0, 1.0, n_points=6)
    assert (curve["spend"].diff().dropna() >= 0).all()
    assert (curve["lambda_star"].diff().dropna() <= 1e-9).all()
    assert curve["lambda_star"].iloc[-1] == 0.0  # full positive-ROI spend → not binding


if __name__ == "__main__":
    tests = [name for name in sorted(globals()) if name.startswith("test_")]
    failures = 0
    for name in tests:
        try:
            globals()[name]()
            print(f"PASS {name}")
        except Exception as exc:
            failures += 1
            print(f"FAIL {name}: {exc}")
    raise SystemExit(1 if failures else 0)
