"""Optional macro-calibration bridge to a Media Mix Model (ref 01, ref 06).

Pure stdlib. Phase 1 implements `mode="provided_summary"` only — it
normalizes an already-computed MMM output (e.g. from pymc-marketing, run
offline) into the shape chapter 5 renders. `mode="pymc_marketing"` (live
fitting inside this pipeline) is Phase 2: returns `status: "deferred"`
rather than silently failing or requiring a heavy optional dependency here.

See references/01-problem-framing.md's MMM cross-link and
https://github.com/pymc-labs/pymc-marketing for the production tool this
bridge is meant to sit in front of — HTE decides micro (SKU x module)
allocation; MMM (when supplied) calibrates macro channel response. Neither
replaces the other.
"""

from __future__ import annotations

_SUMMARY_FIELDS = (
    "channel_contribution", "posterior_roas", "adstock_curves",
    "saturation_curves", "optimized_channel_budget", "lift_calibration",
)


def _normalize_provided_mmm(mmm: dict) -> dict:
    out = {"status": "available"}
    for field in _SUMMARY_FIELDS:
        out[field] = mmm.get(field, [])
    return out


def build_mmm_summary(cfg: dict) -> dict:
    """cfg["mmm"] is optional; absence is not an error — chapter 5 states
    plainly that macro calibration wasn't supplied this cycle."""
    mmm = cfg.get("mmm", {})
    mode = mmm.get("mode")
    if mode == "provided_summary":
        return _normalize_provided_mmm(mmm)
    if mode == "pymc_marketing":
        return {
            "status": "deferred",
            "blocks": ["macro channel calibration"],
            "note": ("Live PyMC-Marketing fitting is Phase 2 — not implemented in this "
                     "build. Supply mode='provided_summary' with precomputed values instead."),
        }
    return {"status": "missing", "blocks": ["macro channel calibration"]}
