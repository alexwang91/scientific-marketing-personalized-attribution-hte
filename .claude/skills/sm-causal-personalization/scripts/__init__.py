"""smcp — scientific-marketing causal personalization toolkit.

Installed from the repo root with `pip install .`; the modules are the same
files that ship inside the Claude Code skill:

    from smcp import qini_auuc        # Qini / AUUC / decile calibration
    from smcp import power_analysis   # uplift experiment power
    from smcp import ope_estimators   # IPS / SNIPS / DR + support check
    from smcp import hte_starter      # T / X / DR-learner templates
    from smcp import policy_budget    # lambda* budget-constrained allocation
    from smcp import generate_report  # provenance-enforced decision memo (CLI: sm-report)
    from smcp import dashboard_data   # config -> dashboard data normalization
    from smcp import dashboard_render # single-file interactive dashboard renderer
    from smcp import report_semantics # 5-chapter spine + bilingual operator vocabulary
    from smcp import investment_schema  # cfg["investment_plan"] validation contract
    from smcp import investment_engine  # budget-frontier allocation (SKU x module)
    from smcp import investment_charts  # chart specs for the investment dashboard
    from smcp import mmm_bridge          # optional pymc-marketing macro-calibration bridge
    from smcp import svg_charts          # shared inline-SVG chart primitives
"""

__all__ = [
    "dashboard_data",
    "dashboard_render",
    "generate_report",
    "hte_starter",
    "investment_charts",
    "investment_engine",
    "investment_schema",
    "mmm_bridge",
    "ope_estimators",
    "policy_budget",
    "power_analysis",
    "qini_auuc",
    "report_semantics",
    "svg_charts",
]
