"""smcp — scientific-marketing causal personalization toolkit.

Installed from the repo root with `pip install .`; the modules are the same
files that ship inside the Claude Code skill:

    from smcp import qini_auuc        # Qini / AUUC / decile calibration
    from smcp import power_analysis   # uplift experiment power
    from smcp import ope_estimators   # IPS / SNIPS / DR + support check
    from smcp import hte_starter      # T / X / DR-learner templates
    from smcp import policy_budget    # lambda* budget-constrained allocation
    from smcp import generate_report  # provenance-enforced decision memo (CLI: sm-report)
"""

__all__ = [
    "generate_report",
    "hte_starter",
    "ope_estimators",
    "policy_budget",
    "power_analysis",
    "qini_auuc",
]
