#!/usr/bin/env python3
"""
generate_report.py v2 — Scientific Marketing decision-memo HTML generator

v2 design contract (references/12-html-report-output.md, 16-estimation-discipline.md):

  1. NUMBER PROVENANCE IS ENFORCED. Every number lives in a central registry
     and must be sourced / assumed / derived / missing. Derived numbers carry
     a formula whose inputs resolve recursively; missing numbers render as
     gray placeholders, never as guessed values. Validation failure = build error.
  2. PYRAMID LAYOUT. Section 1 is a one-screen decision memo (thesis, verdict,
     decisions, overturn conditions, weakest point). Everything after supports it.
  3. ADVERSARIAL REVIEW HAS CONSEQUENCES. Challenges carry status
     resolved / open / open-blocking. Any action or budget line that references
     an open-blocking challenge renders with a BLOCKED stamp.
  4. SHORT-REPORT MODE. If the pipeline terminated at the viability screen
     (config["termination"]), only memo + math + evidence render.
  5. READABILITY BUDGET. Tables are capped at 4 columns; treatment actions and
     test plans render as cards; provenance markers are superscripts, not pills.

Usage:
  python generate_report.py --config config.json --output report.html
  python generate_report.py --demo > report.html        # minimal schema demo
  python generate_report.py --config c.json --validate-only

Config schema: see examples/ax3-romania-config.json and references/12.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

_HERE = Path(__file__).parent


def L(cfg, key, default):
    return cfg.get("labels", {}).get(key, default)


PROVENANCES = {"sourced", "assumed", "derived", "missing"}
CHALLENGE_STATUSES = {"resolved", "open", "open-blocking"}
CHANNEL_VERDICTS = {"viable", "not-viable", "undetermined", "role-only"}
_FORMULA_TOKEN = re.compile(r"^[A-Za-z0-9_+\-*/(). ]+$")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class ConfigError(Exception):
    """Raised when the config violates the provenance contract."""


# ──────────────────────────────────────────────────────────────────────────────
# Number registry: validation + resolution
# ──────────────────────────────────────────────────────────────────────────────

def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_range(v) -> bool:
    return (isinstance(v, list) and len(v) == 2 and all(_is_num(x) for x in v)
            and v[0] <= v[1])


def validate_and_resolve(numbers: dict[str, dict]) -> dict[str, dict]:
    """Validate provenance contract and compute derived values (interval-aware).

    Returns the registry with resolved 'value' on derived entries.
    Raises ConfigError listing every violation found.
    """
    errors: list[str] = []

    for nid, spec in numbers.items():
        if not isinstance(spec, dict):
            errors.append(f"{nid}: spec must be an object")
            continue
        prov = spec.get("provenance")
        if prov not in PROVENANCES:
            errors.append(f"{nid}: provenance must be one of {sorted(PROVENANCES)}, got {prov!r}")
            continue
        if prov == "sourced":
            if not spec.get("source_url") or not spec.get("accessed"):
                errors.append(f"{nid}: sourced requires source_url + accessed date")
            if not (_is_num(spec.get("value")) or _is_range(spec.get("value"))):
                errors.append(f"{nid}: sourced requires numeric value or [lo, hi] range")
        elif prov == "assumed":
            if not spec.get("basis"):
                errors.append(f"{nid}: assumed requires explicit basis")
            if not (_is_num(spec.get("value")) or _is_range(spec.get("value"))):
                errors.append(f"{nid}: assumed requires numeric value or [lo, hi] range")
        elif prov == "derived":
            if not spec.get("formula") or not spec.get("inputs"):
                errors.append(f"{nid}: derived requires formula + inputs")
            elif not _FORMULA_TOKEN.match(spec["formula"]):
                errors.append(f"{nid}: formula contains illegal characters")
            else:
                for ident in _IDENT.findall(spec["formula"]):
                    if ident not in spec["inputs"]:
                        errors.append(f"{nid}: formula references '{ident}' not listed in inputs")
                for inp in spec["inputs"]:
                    if inp not in numbers:
                        errors.append(f"{nid}: input '{inp}' not in registry")
        elif prov == "missing":
            if "value" in spec:
                errors.append(f"{nid}: missing numbers must NOT carry a value — that is a guess")
            if not spec.get("needed_from"):
                errors.append(f"{nid}: missing requires needed_from (where to get the data)")

    if errors:
        raise ConfigError("Provenance contract violations:\n  - " + "\n  - ".join(errors))

    # topological resolution of derived values, with interval propagation
    resolved: dict[str, Any] = {}

    def resolve(nid: str, stack: tuple = ()) -> Any:
        if nid in stack:
            raise ConfigError(f"circular derivation: {' -> '.join(stack + (nid,))}")
        if nid in resolved:
            return resolved[nid]
        spec = numbers[nid]
        prov = spec["provenance"]
        if prov == "missing":
            resolved[nid] = None
        elif prov in ("sourced", "assumed"):
            resolved[nid] = spec["value"]
        else:  # derived
            inputs = {i: resolve(i, stack + (nid,)) for i in spec["inputs"]}
            if any(v is None for v in inputs.values()):
                resolved[nid] = None  # derived-from-missing → missing
            else:
                resolved[nid] = _eval_interval(spec["formula"], inputs)
            spec["value"] = resolved[nid]
        return resolved[nid]

    for nid in numbers:
        resolve(nid)
    return numbers


def _eval_interval(formula: str, inputs: dict[str, Any]) -> Any:
    """Evaluate formula; range inputs propagate via corner enumeration."""
    range_keys = [k for k, v in inputs.items() if _is_range(v)]
    if not range_keys:
        return _safe_eval(formula, inputs)
    corners = []
    for combo in itertools.product(*([inputs[k][0], inputs[k][1]] for k in range_keys)):
        env = dict(inputs)
        env.update(zip(range_keys, combo))
        corners.append(_safe_eval(formula, env))
    return [min(corners), max(corners)]


def _safe_eval(formula: str, env: dict[str, float]) -> float:
    if not _FORMULA_TOKEN.match(formula):
        raise ConfigError(f"illegal formula: {formula!r}")
    return float(eval(formula, {"__builtins__": {}}, dict(env)))  # noqa: S307 — token-validated


# ──────────────────────────────────────────────────────────────────────────────
# Formatting
# ──────────────────────────────────────────────────────────────────────────────

_MARKER = {"sourced": "S", "assumed": "A", "derived": "D", "missing": "M"}


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt_scalar(v: float, spec: dict) -> str:
    if spec.get("pct"):
        return f"{v * 100:g}%"
    dec = spec.get("decimals", 1)
    out = f"{v:,.{dec}f}".rstrip("0").rstrip(".") if dec else f"{v:,.0f}"
    unit = spec.get("unit", "")
    return f"{out} {unit}".strip()


def fmt_value(nid: str, numbers: dict, marker: bool = True) -> str:
    spec = numbers[nid]
    prov = spec["provenance"]
    m = f'<sup class="mk mk-{prov}">{_MARKER[prov]}</sup>' if marker else ""
    if prov == "missing" or spec.get("value") is None:
        return f'<span class="missing-val">—{m}</span>'
    v = spec["value"]
    txt = (f"{_fmt_scalar(v[0], spec)}–{_fmt_scalar(v[1], spec)}" if _is_range(v)
           else _fmt_scalar(v, spec))
    return f"{esc(txt)}{m}"


def provenance_note(nid: str, numbers: dict) -> str:
    spec = numbers[nid]
    prov = spec["provenance"]
    if prov == "sourced":
        return (f'<a href="{esc(spec["source_url"])}">{esc(spec.get("source_label", "source"))}</a>'
                f', accessed {esc(spec["accessed"])}')
    if prov == "assumed":
        return esc(spec["basis"])
    if prov == "missing":
        return f'needed from: {esc(spec["needed_from"])}'
    return "derived"


def render_derivation(nid: str, numbers: dict) -> str:
    """Three-line Fermi chain: symbolic, substituted with markers, result."""
    spec = numbers[nid]
    if spec["provenance"] != "derived":
        return ""
    label = spec.get("label", nid)
    sub = spec["formula"]
    for inp in sorted(spec["inputs"], key=len, reverse=True):
        sub = re.sub(rf"\b{inp}\b", f"⟨{inp}⟩", sub)
    for inp in spec["inputs"]:
        ispec = numbers[inp]
        val = fmt_value(inp, numbers)
        note = ""
        if ispec["provenance"] in ("sourced", "assumed"):
            short = (ispec.get("source_label") or ispec.get("basis", ""))[:48]
            note = f' <span class="prov-note">({esc(short)})</span>' if short else ""
        sub = sub.replace(f"⟨{inp}⟩", f"{val}{note}")
    result = fmt_value(nid, numbers, marker=False)
    pretty_formula = spec["formula"].replace("*", "×").replace("/", "÷")
    pretty_sub = sub.replace("*", "×").replace("/", "÷")
    note_line = f'<div class="deriv-note">{esc(spec["note"])}</div>' if spec.get("note") else ""
    return f"""<div class="derivation">
  <div class="deriv-name">{esc(label)}</div>
  <div class="deriv-line">= {esc(pretty_formula)}</div>
  <div class="deriv-line">= {pretty_sub}</div>
  <div class="deriv-result">= <strong>{result}</strong></div>
  {note_line}
</div>"""


def lint_prose(cfg: dict, numbers: dict) -> list[str]:
    """Warn on bare large numbers in prose that match no registry value."""
    known: set[float] = set()
    for spec in numbers.values():
        v = spec.get("value")
        if _is_num(v):
            known.add(round(float(v), 1))
        elif _is_range(v):
            known.update(round(float(x), 1) for x in v)
    warnings = []

    def scan(obj, path):
        if isinstance(obj, str):
            for m in re.finditer(r"(\d[\d,]*\.?\d*)\s*(?:RON|HUF|EUR|USD|CNY|元)", obj):
                val = round(float(m.group(1).replace(",", "")), 1)
                if val not in known:
                    warnings.append(f"{path}: '{m.group(0)}' matches no registry value")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if k != "numbers":
                    scan(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                scan(v, f"{path}[{i}]")

    scan({k: v for k, v in cfg.items() if k != "numbers"}, "$")
    return warnings


# ──────────────────────────────────────────────────────────────────────────────
# Optional power-analysis bridge
# ──────────────────────────────────────────────────────────────────────────────

def power_bridge(cfg: dict) -> str:
    pa = cfg.get("power_analysis")
    if not pa:
        return ""
    try:
        sys.path.insert(0, str(_HERE))
        from power_analysis import n_per_arm_ate, n_per_cell_hte, experiment_duration_days
        baseline, mde, epd = pa["baseline_cvr"], pa["mde_abs"], pa["eligible_per_day"]
        n_ab = n_per_arm_ate(baseline, mde)
        n_hte = n_per_cell_hte(baseline, baseline, mde * 2, mde)
        days = experiment_duration_days(4 * n_hte, epd)
        return (f'<div class="callout"><strong>power_analysis.py</strong> — baseline CVR {baseline:.1%}, '
                f"MDE {mde:.2%}: ATE needs <strong>{n_ab:,}/arm</strong>; an uplift-difference (HTE) test needs "
                f"<strong>{n_hte:,}/cell ({4 * n_hte:,} total)</strong> ≈ <strong>{days} days</strong> at "
                f"{epd:,} eligible/day. First round therefore runs coarse cells only "
                f"(channel × primary message), not per-dimension HTE.</div>")
    except Exception as e:  # missing scipy etc. — report honestly, don't fake
        return f'<div class="callout">power_analysis.py unavailable ({esc(e)}) — sample-size gate not computed.</div>'


# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────

_CSS = """
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  /* ── Design system: GPS sport-precision · nexu-io/open-design inspired ────
     Font: Inter Variable (Linear's choice) · Palette: dark graphite + performance
     orange · Layout: 8px grid, 1040px content column · Surfaces: layered whites
     with subtle shadows, not heavy borders.
  ────────────────────────────────────────────────────────────────────────── */
  :root{
    --bg:#eef0f3;
    --panel:#ffffff;
    --surface:#f8f9fa;
    --ink:#0f1117;
    --ink-2:#374151;
    --muted:#6b7280;
    --line:#e5e7eb;
    --line-subtle:rgba(0,0,0,.06);
    --accent:#f04e23;
    --accent-light:#fff2ee;
    --ok:#d1fae5;--ok-ink:#065f46;
    --warn:#fef3c7;--warn-ink:#78350f;
    --bad:#fee2e2;--bad-ink:#991b1b;
    --neutral:#f3f4f6;--neutral-ink:#374151;
    --radius:8px;
    --shadow-sm:0 1px 2px rgba(0,0,0,.05);
    --shadow-md:0 2px 8px rgba(0,0,0,.08),0 1px 2px rgba(0,0,0,.04);
    --shadow-lg:0 4px 16px rgba(0,0,0,.1),0 1px 4px rgba(0,0,0,.06);
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font-family:'Inter',-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased;
    font-feature-settings:'cv01','ss03'}
  main{max-width:1040px;margin:0 auto;padding:32px 24px 72px}

  /* ── Typography ── */
  h1{margin:0 0 8px;font-size:26px;font-weight:800;line-height:1.2;
    letter-spacing:-.025em;color:var(--ink)}
  h2{margin:40px 0 16px;font-size:18px;font-weight:700;letter-spacing:-.01em;
    color:var(--ink);display:flex;align-items:center;gap:10px}
  h2::before{content:'';display:inline-block;width:4px;height:20px;
    background:var(--accent);border-radius:2px;flex-shrink:0}
  h2+*{margin-top:0}
  h3{margin:20px 0 10px;font-size:11px;font-weight:700;text-transform:uppercase;
    letter-spacing:.08em;color:var(--accent)}
  p{margin:0 0 12px}
  strong{font-weight:600}

  /* ── Section card ── */
  section{background:var(--panel);border:1px solid var(--line);
    border-radius:12px;padding:28px 32px;margin:16px 0;
    box-shadow:var(--shadow-md)}
  a{color:var(--accent);text-decoration:none}
  a:hover{text-decoration:underline}

  /* ── KPI stat strip ── */
  .kpi-strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
    gap:12px;margin:0 0 24px}
  .kpi{background:var(--surface);border:1px solid var(--line);border-radius:10px;
    padding:20px 22px;position:relative;overflow:hidden;
    box-shadow:var(--shadow-sm)}
  .kpi::after{content:'';position:absolute;top:0;left:0;right:0;height:3px;
    background:var(--accent)}
  .kpi-num{font-size:28px;font-weight:800;letter-spacing:-.04em;
    line-height:1;color:var(--ink);margin-bottom:6px}
  .kpi-num .kpi-unit{font-size:14px;font-weight:600;color:var(--muted);margin-left:2px}
  .kpi-label{font-size:11px;color:var(--muted);text-transform:uppercase;
    letter-spacing:.06em;font-weight:600}

  /* ── CAC bar chart ── */
  .cac-chart{margin:0 0 24px;background:var(--surface);border:1px solid var(--line);
    border-radius:10px;padding:22px 24px 16px;box-shadow:var(--shadow-sm)}
  .cac-chart-title{font-size:11px;font-weight:700;text-transform:uppercase;
    letter-spacing:.08em;color:var(--accent);margin-bottom:20px}
  .cac-row{display:grid;grid-template-columns:140px 1fr;gap:14px;
    align-items:center;margin:12px 0}
  .cac-name{font-size:13px;font-weight:600;text-align:right;line-height:1.3;
    color:var(--ink-2)}
  .cac-track{position:relative;height:28px;background:#f0f1f3;border-radius:6px}
  .cac-bar{position:absolute;height:100%;border-radius:6px;top:0;
    display:flex;align-items:center;padding:0 8px;
    font-size:10px;font-weight:700;color:#fff;white-space:nowrap;min-width:2px}
  .cac-bar.viable{background:#16a34a}
  .cac-bar.undetermined{background:#f59e0b}
  .cac-bar.not-viable{background:#dc2626}
  .cac-bar.role-only{background:#9ca3af}
  .cac-ceiling{position:absolute;top:-8px;bottom:-8px;width:2px;
    background:var(--ink);z-index:6;border-radius:1px}
  .cac-ceiling-flag{position:absolute;top:-24px;transform:translateX(-50%);
    background:var(--ink);color:#fff;font-size:10px;font-weight:700;
    padding:2px 6px;border-radius:4px;white-space:nowrap;z-index:7}
  .cac-axis{display:grid;grid-template-columns:140px 1fr;gap:14px;margin-top:8px}
  .cac-axis-labels{display:flex;justify-content:space-between;
    font-size:10px;color:var(--muted);font-weight:600}
  .cac-legend{margin-top:12px;font-size:11px;color:var(--muted);
    display:flex;gap:14px;flex-wrap:wrap}
  .cac-legend span{display:inline-flex;align-items:center;gap:5px}
  .cac-legend i{width:10px;height:10px;border-radius:2px;display:inline-block}

  /* ── Sensitivity priority cards ── */
  .sens-chart{margin:0 0 24px}
  .sens-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
    gap:10px;margin-top:10px}
  .sens-card{background:var(--surface);border:1px solid var(--line);
    border-radius:8px;padding:14px 16px;display:flex;gap:12px;align-items:flex-start;
    box-shadow:var(--shadow-sm)}
  .sens-badge{width:32px;height:32px;border-radius:50%;display:flex;
    align-items:center;justify-content:center;font-size:12px;font-weight:800;
    color:#fff;flex-shrink:0}
  .sens-badge.p1{background:var(--accent)}
  .sens-badge.p2{background:#f59e0b}
  .sens-badge.p3{background:var(--ink)}
  .sens-badge.pN{background:var(--muted)}
  .sens-change{font-size:12px;font-weight:700;color:var(--ink);margin-bottom:4px;line-height:1.4}
  .sens-effect{font-size:11px;color:var(--muted);line-height:1.4}

  /* ── Dimension score chart ── */
  .dim-chart{margin:0 0 20px}
  .dim-chart-row{display:grid;grid-template-columns:160px 1fr 36px;
    gap:10px;align-items:center;margin:5px 0}
  .dim-label-cell{font-size:11px;font-weight:600;color:var(--ink-2);
    text-overflow:ellipsis;overflow:hidden;white-space:nowrap;text-align:right}
  .dim-bar-track{background:#f0f1f3;border-radius:4px;height:14px}
  .dim-bar{height:100%;border-radius:4px;transition:width .3s}
  .dim-score-lbl{font-size:10px;font-weight:700;color:var(--muted);text-align:right}

  /* ── Price comparison chart ── */
  .price-chart{margin:0 0 24px;background:var(--surface);border:1px solid var(--line);
    border-radius:10px;padding:22px 24px;box-shadow:var(--shadow-sm)}
  .price-chart-title{font-size:11px;font-weight:700;text-transform:uppercase;
    letter-spacing:.08em;color:var(--accent);margin-bottom:20px}
  .price-axis-wrap{position:relative;padding:36px 0 32px;margin:0 8px}
  .price-axis-line{height:3px;background:#e5e7eb;border-radius:2px;position:relative}
  .price-dot{position:absolute;transform:translateX(-50%) translateY(-50%);
    top:50%;width:16px;height:16px;border-radius:50%;border:3px solid #fff;
    box-shadow:0 2px 6px rgba(0,0,0,.2);z-index:2}
  .price-dot.ours{background:var(--accent);width:22px;height:22px}
  .price-dot.comp{background:var(--ink)}
  .price-top-label{position:absolute;transform:translateX(-50%);
    bottom:calc(100% + 14px);font-size:11px;font-weight:700;
    white-space:nowrap;color:var(--ink)}
  .price-top-label.ours{color:var(--accent);font-size:12px}
  .price-bot-label{position:absolute;transform:translateX(-50%);
    top:calc(100% + 14px);font-size:10px;color:var(--muted);white-space:nowrap}
  .price-axis-ends{display:flex;justify-content:space-between;
    font-size:10px;color:var(--muted);font-weight:600;margin-top:4px}

  /* ── Budget allocation bar ── */
  .budget-chart{margin:0 0 24px}
  .budget-bar-row{display:flex;height:36px;border-radius:8px;overflow:hidden;
    gap:2px;margin:12px 0;box-shadow:var(--shadow-sm)}
  .budget-seg{display:flex;align-items:center;padding:0 10px;
    font-size:10px;font-weight:700;color:#fff;white-space:nowrap;
    overflow:hidden;min-width:24px;transition:opacity .2s}
  .budget-legend{font-size:11px;color:var(--muted);display:flex;gap:14px;flex-wrap:wrap;margin-top:8px}
  .budget-legend span{display:inline-flex;align-items:center;gap:5px}
  .budget-legend i{width:10px;height:10px;border-radius:2px;display:inline-block}

  /* ── Signature element: verdict band ── */
  .memo{border:none;padding:0;box-shadow:none;background:transparent}
  .memo-verdict-band{
    background:var(--ink);color:#fff;
    border-radius:12px 12px 0 0;padding:36px 32px 28px}
  .verdict-label{font-size:10px;font-weight:700;letter-spacing:.12em;
    text-transform:uppercase;opacity:.5;margin-bottom:8px}
  .verdict{display:inline-block;padding:8px 24px;border-radius:6px;
    font-weight:800;font-size:22px;letter-spacing:.03em}
  .verdict-go{background:var(--ok);color:var(--ok-ink)}
  .verdict-no-go{background:var(--bad);color:var(--bad-ink)}
  .verdict-conditional{background:var(--accent);color:#fff}
  .memo-body{background:var(--panel);border:1px solid var(--line);
    border-top:none;border-radius:0 0 12px 12px;padding:28px 32px}
  .memo-thesis{font-size:15px;line-height:1.7;margin:0 0 22px;color:var(--ink)}
  .memo-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:4px}
  .memo-grid>div{border:1px solid var(--line);border-radius:8px;
    padding:16px 18px;background:var(--surface)}
  .memo-grid h3{margin:0 0 10px}
  .memo-grid ul{margin:0;padding-left:18px}
  .memo-grid li{margin:6px 0;font-size:13.5px;line-height:1.5}
  .mk-legend{font-size:11.5px;color:var(--muted);margin:16px 0 0;
    padding-top:12px;border-top:1px solid var(--line)}

  /* ── Derivation chains ── */
  .derivation{font-family:ui-monospace,"JetBrains Mono",Consolas,monospace;
    font-size:12px;background:var(--surface);border:1px solid var(--line);
    border-left:3px solid var(--accent);border-radius:0 8px 8px 0;
    padding:12px 16px;margin:10px 0;line-height:1.8}
  .deriv-name{font-weight:700;font-size:13px;margin-bottom:4px;color:var(--ink)}
  .deriv-line{padding-left:12px;color:#4b5563}
  .deriv-result{padding-left:12px;margin-top:4px;font-weight:700;color:var(--ink)}
  .deriv-note{margin-top:8px;color:var(--muted);
    font-family:'Inter',sans-serif;font-size:12px;
    padding-top:6px;border-top:1px dashed var(--line)}
  .prov-note{color:var(--muted);font-size:11px}

  /* ── Provenance markers ── */
  sup.mk{font-size:9px;font-weight:700;padding:1px 3px;margin-left:1px;border-radius:2px}
  .mk-sourced{color:#065f46;background:#d1fae5}
  .mk-assumed{color:#78350f;background:#fef3c7}
  .mk-derived{color:#1e40af;background:#dbeafe}
  .mk-missing{color:#991b1b;background:#fee2e2}
  .missing-val{color:#9ca3af;border-bottom:1px dashed #d1d5db}

  /* ── Pills ── */
  .pill{display:inline-block;padding:2px 9px;border-radius:999px;
    font-size:11px;font-weight:700;white-space:nowrap;letter-spacing:.01em}
  .pill-viable{background:var(--ok);color:var(--ok-ink)}
  .pill-not-viable{background:var(--bad);color:var(--bad-ink)}
  .pill-undetermined{background:var(--warn);color:var(--warn-ink)}
  .pill-role-only{background:var(--neutral);color:var(--neutral-ink)}
  .pill-resolved{background:var(--ok);color:var(--ok-ink)}
  .pill-open{background:var(--warn);color:var(--warn-ink)}
  .pill-open-blocking{background:var(--bad);color:var(--bad-ink)}
  .blocked-stamp{display:inline-block;border:2px solid var(--bad-ink);
    color:var(--bad-ink);padding:2px 9px;border-radius:4px;
    font-weight:700;font-size:11px;transform:rotate(-1.5deg);margin-left:8px}

  /* ── Tables ── */
  .table-wrap{overflow-x:auto;border:1px solid var(--line);
    border-radius:8px;background:#fff;margin:12px 0}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th{background:var(--surface);font-weight:700;font-size:10.5px;text-transform:uppercase;
    letter-spacing:.06em;color:var(--muted);padding:10px 14px;
    border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
  td{padding:11px 14px;border-bottom:1px solid var(--line);
    vertical-align:top;text-align:left;font-size:13px}
  tr:last-child td{border-bottom:0}
  tr:nth-child(even) td{background:#fafafa}

  /* ── Cards ── */
  .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));
    gap:14px;margin-top:14px}
  .card{border:1px solid var(--line);border-radius:8px;
    padding:16px 18px;background:var(--surface);border-top:3px solid var(--line)}
  .card.blocked{border-top-color:var(--bad-ink);background:#fff8f8}
  .card h3{margin:0 0 10px;font-size:14px;font-weight:700;line-height:1.35}
  .card dl{margin:0;font-size:13px}
  .card dt{color:var(--muted);font-size:10px;font-weight:700;
    text-transform:uppercase;letter-spacing:.06em;margin-top:10px}
  .card dd{margin:3px 0 0;line-height:1.5}

  /* ── Callout ── */
  .callout{border-left:4px solid var(--accent);border-radius:0 8px 8px 0;
    padding:14px 18px;margin:14px 0;background:var(--accent-light);
    font-size:13.5px;line-height:1.6}

  /* ── Heatmap ── */
  .heatmap{display:grid;gap:2px;background:var(--line);
    border:1px solid var(--line);border-radius:8px;
    overflow:hidden;font-size:11px;margin:14px 0;overflow-x:auto}
  .hm-header{background:var(--ink);color:#fff;font-weight:700;
    padding:7px 6px;text-align:center;font-size:9.5px;
    text-transform:uppercase;letter-spacing:.03em;line-height:1.3;
    word-break:break-all;min-width:36px}
  .hm-label{background:#f9fafb;font-weight:600;padding:8px 10px;
    font-size:11px;color:var(--ink);white-space:nowrap}
  .hm-cell{padding:8px 4px;text-align:center;font-weight:800;
    font-size:11px;letter-spacing:.03em;min-width:36px}
  .hm-high{background:#f04e23;color:#fff}
  .hm-test{background:#78350f;color:#fff}
  .hm-small{background:#e5e7eb;color:#4b5563}
  .hm-none{background:#f9fafb;color:#d1d5db}
  .hm-avoid{background:#991b1b;color:#fff}

  /* ── Score dots ── */
  .score-bar{display:inline-flex;gap:3px;vertical-align:middle}
  .score-dot{width:8px;height:8px;border-radius:50%}
  .score-dot.pass{background:#f04e23}.score-dot.fail{background:#e5e7eb}

  /* ── KOL card ── */
  .kol-card{border:1px solid var(--line);border-radius:8px;
    padding:16px 18px;background:var(--surface);margin:10px 0;
    border-left:3px solid var(--accent)}

  /* ── Checklist ── */
  .checklist{list-style:none;padding:0;margin:0}
  .checklist li{display:flex;gap:12px;padding:9px 0;
    border-bottom:1px solid var(--line);font-size:13px;align-items:flex-start}
  .checklist li:last-child{border-bottom:0}
  .chk-pending{color:var(--warn-ink);font-weight:800;min-width:18px;margin-top:1px}
  .chk-done{color:var(--ok-ink);font-weight:800;min-width:18px;margin-top:1px}
  .chk-blocked{color:var(--bad-ink);font-weight:800;min-width:18px;margin-top:1px}

  /* ── Evidence claim tags ── */
  .tag{display:inline-block;padding:2px 8px;border-radius:999px;
    font-size:11px;font-weight:700;white-space:nowrap}
  .tag.evidence{background:var(--ok);color:var(--ok-ink)}
  .tag.assumption{background:var(--warn);color:var(--warn-ink)}
  .tag.hypothesis{background:#dbeafe;color:#1e40af}
  .tag.needs-test{background:var(--bad);color:var(--bad-ink)}

  /* ── Footer ── */
  footer{max-width:1040px;margin:0 auto;padding:20px 24px 48px;
    color:var(--muted);font-size:12px;border-top:1px solid var(--line)}

  @media(max-width:720px){
    .memo-grid,.cards{grid-template-columns:1fr}
    .dim-chart-row{grid-template-columns:100px 1fr 32px}
    .sens-grid{grid-template-columns:1fr}
  }
  @media print{body{background:#fff;font-size:12px}
    section{break-inside:avoid;box-shadow:none}
    .memo-verdict-band{-webkit-print-color-adjust:exact;print-color-adjust:exact}
    a{color:var(--ink)}}
"""


# ──────────────────────────────────────────────────────────────────────────────
# Sections
# ──────────────────────────────────────────────────────────────────────────────

def s_memo(cfg: dict) -> str:
    memo = cfg["decision_memo"]
    meta = cfg.get("meta", {})
    verdict = memo.get("verdict", "conditional")
    vlabel = {"go": "GO", "no-go": "NO-GO", "conditional": "CONDITIONAL"}.get(verdict, verdict.upper())
    horizon_label = {
        "now": L(cfg, "horizon_now", "Now (zero cost)"),
        "checkpoint": L(cfg, "horizon_checkpoint", "At checkpoint"),
        "never": L(cfg, "horizon_never", "Not under this math"),
    }
    buckets: dict[str, list[str]] = {"now": [], "checkpoint": [], "never": []}
    for d in memo.get("decisions", []):
        buckets.setdefault(d["horizon"], []).append(d["text"])
    decision_html = ""
    for h in ("now", "checkpoint", "never"):
        if buckets.get(h):
            items = "".join(f"<li>{esc(t)}</li>" for t in buckets[h])
            decision_html += f"<h3>{horizon_label[h]}</h3><ul>{items}</ul>"
    overturn = "".join(f"<li>{esc(c)}</li>" for c in memo.get("overturn_conditions", []))
    return f"""<section class="memo">
  <div class="memo-verdict-band">
    <div class="verdict-label">{esc(L(cfg, "verdict_label", "VERDICT"))}</div>
    <div><span class="verdict verdict-{esc(verdict)}">{esc(vlabel)}</span></div>
    <div style="margin-top:14px;opacity:.7;font-size:13px;font-weight:500;letter-spacing:.02em">{esc(meta.get("product", ""))} · {esc(meta.get("market", ""))} · {esc(meta.get("date", ""))}</div>
  </div>
  <div class="memo-body">
    <h1>{esc(L(cfg, "memo_heading", "1 · Decision Memo"))}</h1>
    <p class="memo-thesis"><strong>{esc(L(cfg, "thesis_label", "Thesis:"))}</strong> {esc(memo["thesis"])}</p>
    <div class="memo-grid">
      <div>{decision_html}</div>
      <div>
        <h3>{esc(L(cfg, "overturn_heading", "What overturns this thesis"))}</h3><ul>{overturn}</ul>
        <h3>{esc(L(cfg, "weakest_heading", "Weakest point of this report"))}</h3><p style="margin:4px 0 0">{esc(memo.get("weakest_point", ""))}</p>
      </div>
    </div>
    <p class="mk-legend">{esc(L(cfg, "marker_legend", "Number markers: ◆S sourced (linked) · ◇A assumed (basis stated) · ⊕D derived (chain shown) · ○M missing (no value — placeholder only)"))}</p>
  </div>
</section>"""


def _scalar_of(v):
    """Return a representative scalar (hi end for ranges) for chart scaling."""
    if _is_range(v):
        return v[1]
    return v if _is_num(v) else None


def s_kpi_strip(cfg: dict, numbers: dict) -> str:
    """Big-number stat strip. Driven by cfg['kpi_strip'] = [number_id, ...]."""
    ids = cfg.get("kpi_strip", [])
    if not ids:
        return ""
    cells = ""
    for nid in ids:
        spec = numbers.get(nid)
        if not spec:
            continue
        val = fmt_value(nid, numbers, marker=False)
        label = esc(spec.get("label", nid))
        cells += f'<div class="kpi"><div class="kpi-num">{val}</div><div class="kpi-label">{label}</div></div>'
    if not cells:
        return ""
    return f'<div class="kpi-strip">{cells}</div>'


def s_cac_chart(cfg: dict, numbers: dict) -> str:
    """Horizontal bar chart: each channel's CAC interval vs the CAC ceiling.
    The single most important decision visual — drawn from channel_screen."""
    ceiling_id = cfg.get("cac_chart", {}).get("ceiling_id", "cac_ceiling")
    cspec = numbers.get(ceiling_id)
    if not cspec:
        return ""
    ceiling = _scalar_of(cspec.get("value"))
    if ceiling is None:
        return ""
    bars = []
    for ch in cfg.get("channel_screen", []):
        cid = ch.get("cac_estimate")
        if not cid or cid not in numbers:
            continue
        v = numbers[cid].get("value")
        if v is None:
            continue
        lo = v[0] if _is_range(v) else v
        hi = v[1] if _is_range(v) else v
        bars.append((ch["channel"], lo, hi, ch.get("verdict", "undetermined")))
    if not bars:
        return ""
    scale = max(max(hi for _, _, hi, _ in bars), ceiling) * 1.08
    ceiling_pct = ceiling / scale * 100
    rows = ""
    for name, lo, hi, verdict in bars:
        left = lo / scale * 100
        width = max((hi - lo) / scale * 100, 1.2)
        rng = (f"{lo:,.0f}–{hi:,.0f}" if hi != lo else f"{lo:,.0f}")
        rows += (
            f'<div class="cac-row"><div class="cac-name">{esc(name)}</div>'
            f'<div class="cac-track">'
            f'<div class="cac-bar {esc(verdict)}" style="left:{left:.1f}%;width:{width:.1f}%" title="{rng}">{rng}</div>'
            f'<div class="cac-ceiling" style="left:{ceiling_pct:.1f}%"></div>'
            f'</div></div>'
        )
    ceil_label = esc(L(cfg, "cac_chart_ceiling_label", "CAC ceiling"))
    title = esc(L(cfg, "cac_chart_title", "Channel CAC interval vs ceiling (HUF)"))
    unit = esc(cspec.get("unit", ""))
    leg_v = esc(L(cfg, "cac_legend_viable", "viable (whole interval under ceiling)"))
    leg_u = esc(L(cfg, "cac_legend_undetermined", "undetermined (interval spans ceiling)"))
    leg_n = esc(L(cfg, "cac_legend_notviable", "not-viable (best case over ceiling)"))
    flag = f"◄ {ceil_label} {ceiling:,.0f} {unit}"
    return f"""<div class="cac-chart">
  <div class="cac-chart-title">{title}</div>
  <div class="cac-row"><div class="cac-name"></div><div class="cac-track" style="background:transparent;height:8px">
    <div class="cac-ceiling-flag" style="left:{ceiling_pct:.1f}%">{esc(flag)}</div>
    <div class="cac-ceiling" style="left:{ceiling_pct:.1f}%"></div>
  </div></div>
  {rows}
  <div class="cac-axis"><div></div><div class="cac-axis-labels"><span>0</span><span>{scale:,.0f} {unit}</span></div></div>
  <div class="cac-legend">
    <span><i style="background:#16a34a"></i>{leg_v}</span>
    <span><i style="background:#f59e0b"></i>{leg_u}</span>
    <span><i style="background:#dc2626"></i>{leg_n}</span>
  </div>
  <p style="font-size:11px;color:var(--muted);margin:10px 0 0">{esc(L(cfg, "cac_chart_caption", "Bar = benchmark CAC interval · vertical line = ceiling · colour = screen verdict. A benchmark can only disprove viability (best case over ceiling) — it can never prove it, so a bar fully under the ceiling is still 'undetermined' until local data confirms."))}</p>
</div>"""


def s_sensitivity_chart(cfg: dict) -> str:
    """Sensitivity priority cards — visual alternative to the sensitivity table."""
    items = sorted(cfg.get("sensitivity", []), key=lambda x: x["priority"])
    if not items:
        return ""
    cards = ""
    for s in items:
        p = s["priority"]
        pclass = "p1" if p == 1 else ("p2" if p == 2 else "p3" if p == 3 else "pN")
        cards += (
            f'<div class="sens-card">'
            f'<div class="sens-badge {pclass}">P{p}</div>'
            f'<div><div class="sens-change">{esc(s["change"])}</div>'
            f'<div class="sens-effect">{esc(s["effect"])}</div></div>'
            f'</div>'
        )
    title = esc(L(cfg, "sensitivity_heading", "Sensitivity — which assumption flips the conclusion"))
    note = esc(L(cfg, "sens_note", "Verify in priority order: P1 first."))
    return f"""<div class="sens-chart">
  <h3>{title}</h3>
  <div class="sens-grid">{cards}</div>
  <p style="font-size:12px;color:var(--muted);margin-top:8px">{note}</p>
</div>"""


def s_dimension_chart(cfg: dict) -> str:
    """Horizontal bar chart of D-dimension entry scores, sorted descending."""
    dims = cfg.get("dimensions", [])
    if not dims:
        return ""
    scored = []
    for d in dims:
        score_str = d.get("entry_score", "")
        try:
            filled, total = map(int, score_str.split("/"))
            pct = (filled / max(total, 1)) * 100
        except Exception:
            filled, total, pct = 0, 5, 0
        scored.append((d["id"], d.get("name", ""), pct, filled, total))
    scored.sort(key=lambda x: -x[2])
    rows = ""
    for did, name, pct, filled, total in scored[:16]:
        color = "var(--accent)" if pct >= 60 else ("#f59e0b" if pct >= 40 else "#9ca3af")
        short = f"{did} {name}"[:22]
        rows += (
            f'<div class="dim-chart-row">'
            f'<div class="dim-label-cell" title="{esc(did)} {esc(name)}">{esc(short)}</div>'
            f'<div class="dim-bar-track"><div class="dim-bar" style="width:{pct:.0f}%;background:{color}"></div></div>'
            f'<div class="dim-score-lbl">{filled}/{total}</div>'
            f'</div>'
        )
    title = esc(L(cfg, "dim_chart_title", "D Dimension Score Ranking"))
    return f'<div class="dim-chart"><h3>{title}</h3>{rows}</div>'


def s_budget_chart(cfg: dict, numbers: dict) -> str:
    """Proportional budget allocation bar — visual companion to the budget table."""
    rows = cfg.get("budget_rows", [])
    if not rows:
        return ""
    _COLORS = ["#f04e23", "#1a1f2e", "#f59e0b", "#16a34a", "#6b7280", "#7c3aed"]
    segments = []
    for i, r in enumerate(rows):
        bid = r.get("budget_id")
        if bid and bid in numbers:
            v = numbers[bid].get("value")
            if v is not None:
                amt = float(v[1] if _is_range(v) else v)
                unit = numbers[bid].get("unit", "")
                segments.append((r.get("item", r.get("phase", "")), amt, unit, _COLORS[i % len(_COLORS)]))
    if not segments:
        return ""
    total = sum(a for _, a, _, _ in segments)
    if total <= 0:
        return ""
    bars = legend = ""
    for name, amt, unit, color in segments:
        pct = amt / total * 100
        bars += f'<div class="budget-seg" style="width:{pct:.1f}%;background:{color}" title="{esc(name)}: {amt:,.0f} {esc(unit)}">{esc(name[:14])}</div>'
        legend += f'<span><i style="background:{color}"></i>{esc(name)}: {amt:,.0f} {esc(unit)}</span>'
    title = esc(L(cfg, "budget_chart_title", "Budget Split"))
    return (f'<div class="budget-chart"><h3>{title}</h3>'
            f'<div class="budget-bar-row">{bars}</div>'
            f'<div class="budget-legend">{legend}</div></div>')


def s_price_comparison(cfg: dict, numbers: dict) -> str:
    """Horizontal price positioning axis: our product vs competitors."""
    pc = cfg.get("price_comparison")
    if not pc:
        return ""
    own_id = pc.get("own")
    competitors = pc.get("competitors", [])
    if not own_id or own_id not in numbers:
        return ""
    own_val = numbers[own_id].get("value")
    own_price = _scalar_of(own_val)
    if own_price is None:
        return ""
    comp_data = []
    for c in competitors:
        cid = c.get("id")
        if cid and cid in numbers:
            v = numbers[cid].get("value")
            price = _scalar_of(v) if v is not None else None
            if price is not None:
                comp_data.append((c.get("name", cid), price))
    if not comp_data:
        return ""
    all_prices = [own_price] + [p for _, p in comp_data]
    max_p = max(all_prices) * 1.12
    min_p = min(all_prices) * 0.88
    span = max_p - min_p or 1

    def pct(p):
        return (p - min_p) / span * 100

    own_pct = pct(own_price)
    own_lbl = numbers[own_id].get("label", "")
    unit = numbers[own_id].get("unit", "")
    dots = (
        f'<div class="price-dot ours" style="left:{own_pct:.1f}%"></div>'
        f'<div class="price-top-label ours" style="left:{own_pct:.1f}%">{own_price:,.0f}</div>'
        f'<div class="price-bot-label" style="left:{own_pct:.1f}%">{esc(own_lbl[:18])}</div>'
    )
    for name, price in comp_data:
        p = pct(price)
        dots += (
            f'<div class="price-dot comp" style="left:{p:.1f}%"></div>'
            f'<div class="price-top-label" style="left:{p:.1f}%">{price:,.0f}</div>'
            f'<div class="price-bot-label" style="left:{p:.1f}%">{esc(name[:16])}</div>'
        )
    title = esc(L(cfg, "price_comparison_title", "Competitive Price Positioning"))
    return f"""<div class="price-chart">
  <div class="price-chart-title">{title} ({esc(unit)})</div>
  <div class="price-axis-wrap">
    <div class="price-axis-line">{dots}</div>
    <div class="price-axis-ends"><span>{min_p:,.0f}</span><span>{max_p:,.0f} {esc(unit)}</span></div>
  </div>
</div>"""


def s_math(cfg: dict, numbers: dict) -> str:
    kpi = s_kpi_strip(cfg, numbers)
    cac_chart = s_cac_chart(cfg, numbers)
    chains = "".join(render_derivation(nid, numbers) for nid in cfg.get("derivations", []))
    sens = s_sensitivity_chart(cfg)

    screen_rows = ""
    for ch in cfg.get("channel_screen", []):
        v = ch["verdict"]
        cac = fmt_value(ch["cac_estimate"], numbers) if ch.get("cac_estimate") else "—"
        screen_rows += (f"<tr><td><strong>{esc(ch['channel'])}</strong></td>"
                        f"<td><span class='pill pill-{esc(v)}'>{esc(v)}</span></td>"
                        f"<td>{cac}</td><td>{esc(ch['reasoning'])}</td></tr>")
    screen = ""
    if screen_rows:
        screen = f"""<h3>{esc(L(cfg, "screen_heading", "Channel viability screen (threshold: CAC ceiling above)"))}</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>{esc(L(cfg, "screen_th_channel", "Channel"))}</th><th>{esc(L(cfg, "screen_th_verdict", "Verdict"))}</th><th>{esc(L(cfg, "screen_th_cac", "CAC estimate"))}</th><th>{esc(L(cfg, "screen_th_reasoning", "Reasoning / what's missing"))}</th></tr></thead>
    <tbody>{screen_rows}</tbody></table></div>
  <p style="font-size:13px;color:var(--muted)">{L(cfg, "screen_note", "Rules: a benchmark-based estimate can prove <em>not-viable</em> (best case still fails) but never <em>viable</em> — that requires local data. <em>undetermined</em> means the interval spans the ceiling; the action is to get data, not to pick an endpoint.")}</p>"""

    return f"""<section>
  <h2>{esc(L(cfg, "math_heading", "2 · The Math"))}</h2>
  {kpi}
  {cac_chart}
  {chains}
  {sens}
  {screen}
</section>"""


def _blocked_by(action: dict, challenges_by_id: dict) -> list[str]:
    return [cid for cid in action.get("blocked_by", [])
            if challenges_by_id.get(cid, {}).get("status") == "open-blocking"]


def s_actions(cfg: dict, numbers: dict, challenges_by_id: dict) -> str:
    cards = ""
    for a in cfg.get("actions", []):
        blockers = _blocked_by(a, challenges_by_id)
        stamp = "".join(f'<span class="blocked-stamp">⊘ BLOCKED by {esc(b)}</span>' for b in blockers)
        budget = ""
        if a.get("budget"):
            budget = f"<dt>{esc(L(cfg, 'budget_envelope_label', 'Budget envelope'))}</dt><dd>{fmt_value(a['budget'], numbers)}</dd>"
        gate = f"<dt>{esc(L(cfg, 'unlocks_label', 'Unlocks'))}</dt><dd>{esc(a['gate'])}</dd>" if a.get("gate") else ""
        cards += f"""<div class="card{' blocked' if blockers else ''}">
  <h3>{esc(a['id'])} · {esc(a['action'])} {stamp}</h3>
  <dl>
    <dt>{esc(L(cfg, 'mechanism_label', 'Mechanism'))}</dt><dd>{esc(a['mechanism'])}</dd>
    <dt>{esc(L(cfg, 'guardrail_label', 'Guardrail'))}</dt><dd>{esc(a['guardrail'])}</dd>
    <dt>{esc(L(cfg, 'test_label', 'Test'))}</dt><dd>{esc(a.get('test', a.get('measurement', '')))}</dd>
    {budget}{gate}
  </dl>
</div>"""
    rejected = "".join(
        f"<tr><td>{esc(r['option'])}</td><td>{esc(r['reason'])}</td></tr>"
        for r in cfg.get("rejected_options", [])
    )
    rej_html = ""
    if rejected:
        rej_html = f"""<h3>{esc(L(cfg, "rejected_heading", "Rejected options (and why)"))}</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>{esc(L(cfg, "rejected_th_option", "Option"))}</th><th>{esc(L(cfg, "rejected_th_reason", "Rejection reason"))}</th></tr></thead>
    <tbody>{rejected}</tbody></table></div>"""
    return f"""<section>
  <h2>{esc(L(cfg, "actions_heading", "3 · Actions"))}</h2>
  <p>{L(cfg, "actions_intro", "Only options that survived the viability screen appear as cards. A card stamped <strong>⊘ BLOCKED</strong> references an unresolved blocking challenge (section 4) and must not receive budget until that challenge is resolved.")}</p>
  <div class="cards">{cards}</div>
  {rej_html}
</section>"""


def s_challenges(cfg: dict) -> str:
    rows = ""
    for c in cfg.get("challenges", []):
        rows += (f"<tr><td><strong>{esc(c['id'])}</strong> · {esc(c['target'])}</td>"
                 f"<td>{esc(c['question'])}</td>"
                 f"<td><span class='pill pill-{esc(c['status'])}'>{esc(c['status'])}</span></td>"
                 f"<td>{esc(c.get('resolution') or c.get('evidence_needed', ''))}</td></tr>")
    return f"""<section>
  <h2>{esc(L(cfg, "challenges_heading", "9 · Causal Activation Reviewer (campaign-level)"))}</h2>
  <p>{L(cfg, "challenges_intro", 'Challenges are raised by an independent review pass and are immutable — the analysis may respond but not rewrite them. <strong>open-blocking</strong> challenges stamp every action that depends on them. An unresolved challenge displayed openly is the trust mechanism; "resolved" requires data, not rhetoric.')}</p>
  <div class="table-wrap"><table>
    <thead><tr><th>{esc(L(cfg, "ch_th_challenge", "Challenge"))}</th><th>{esc(L(cfg, "ch_th_question", "Question"))}</th><th>{esc(L(cfg, "ch_th_status", "Status"))}</th><th>{esc(L(cfg, "ch_th_resolution", "Resolution / evidence needed"))}</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
</section>"""


def s_test_plan(cfg: dict) -> str:
    cards = ""
    for t in cfg.get("test_plan", []):
        cards += f"""<div class="card">
  <h3>{esc(t['name'])}</h3>
  <dl>
    <dt>{esc(L(cfg, 'prediction_label', 'Prediction'))}</dt><dd>{esc(t['prediction'])}</dd>
    <dt>{esc(L(cfg, 'test_label', 'Test'))}</dt><dd>{esc(t['test'])}</dd>
    <dt>{esc(L(cfg, 'kill_line_label', 'Kill line'))}</dt><dd>{esc(t['kill_line'])}</dd>
    <dt>{esc(L(cfg, 'decision_date_label', 'Decision date'))}</dt><dd>{esc(t['decision_date'])}</dd>
  </dl>
</div>"""
    return f"""<section>
  <h2>{esc(L(cfg, "testplan_heading", "14 · Test Plan"))}</h2>
  <p>{L(cfg, "testplan_intro", "Every claim that survives to budget carries a falsifiable prediction, a kill line, and a decision date. On that date the line either becomes Sourced or is declared dead.")}</p>
  {power_bridge(cfg)}
  <div class="cards">{cards}</div>
</section>"""


def s_evidence(cfg: dict, numbers: dict) -> str:
    facts = "".join(
        f"<tr><td>{esc(f['fact'])}</td>"
        f"<td><a href='{esc(f['source_url'])}'>{esc(f['source_label'])}</a></td>"
        f"<td>{esc(f.get('accessed', ''))}</td></tr>"
        for f in cfg.get("facts", [])
    )
    assumed_rows = "".join(
        f"<tr><td>{esc(spec.get('label', nid))}</td><td>{fmt_value(nid, numbers, marker=False)}</td>"
        f"<td>{esc(spec['basis'])}</td></tr>"
        for nid, spec in numbers.items() if spec["provenance"] == "assumed"
    )
    missing_rows = "".join(
        f"<tr><td>{esc(spec.get('label', nid))}</td><td>{esc(spec['needed_from'])}</td>"
        f"<td>{esc(spec.get('cost_to_get', '—'))}</td><td>{esc(', '.join(spec.get('blocks', [])) or '—')}</td></tr>"
        for nid, spec in numbers.items() if spec["provenance"] == "missing"
    )
    return f"""<section>
  <h2>{esc(L(cfg, "evidence_heading", "16 · Evidence & Gaps"))}</h2>
  <h3>{esc(L(cfg, "sourced_facts_heading", "Sourced facts"))}</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>{esc(L(cfg, "ev_th_fact", "Fact"))}</th><th>{esc(L(cfg, "ev_th_source", "Source"))}</th><th>{esc(L(cfg, "ev_th_accessed", "Accessed"))}</th></tr></thead>
    <tbody>{facts}</tbody></table></div>
  <h3>{esc(L(cfg, "assumption_register_heading", "Assumption register"))}</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>{esc(L(cfg, "ev_th_assumption", "Assumption"))}</th><th>{esc(L(cfg, "ev_th_value", "Value"))}</th><th>{esc(L(cfg, "ev_th_basis", "Basis"))}</th></tr></thead>
    <tbody>{assumed_rows}</tbody></table></div>
  <h3>{esc(L(cfg, "missing_ledger_heading", "Missing ledger — sorted by sensitivity, this is the work plan"))}</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>{esc(L(cfg, "ev_th_what", "What"))}</th><th>{esc(L(cfg, "ev_th_where", "Where to get it"))}</th><th>{esc(L(cfg, "ev_th_cost", "Cost"))}</th><th>{esc(L(cfg, "ev_th_blocks", "Blocks"))}</th></tr></thead>
    <tbody>{missing_rows}</tbody></table></div>
</section>"""


def s_product_facts(cfg: dict, numbers: dict) -> str:
    """Section 3 — Product & market facts, with price comparison chart."""
    features = cfg.get("product_facts", [])
    mfacts = cfg.get("market_facts", [])
    feat_rows = ""
    for f in features:
        tag = f.get("tag", "evidence")
        feat_rows += (f"<tr><td>{esc(f['label'])}</td><td>{esc(f['detail'])}</td>"
                      f"<td><span class='tag {esc(tag)}'>{esc(tag.title())}</span></td></tr>")
    mfact_rows = ""
    for m in mfacts:
        tag = m.get("tag", "evidence")
        mfact_rows += (f"<tr><td>{esc(m['fact'])}</td>"
                       f"<td><span class='tag {esc(tag)}'>{esc(tag.title())}</span></td></tr>")
    feat_table = f"""<h3>{esc(L(cfg, "product_features_heading", "Product features relevant to targeting"))}</h3>
<div class="table-wrap"><table>
  <thead><tr><th>{esc(L(cfg, "pf_th_feature", "Feature"))}</th><th>{esc(L(cfg, "pf_th_relevance", "Targeting relevance"))}</th><th>{esc(L(cfg, "pf_th_status", "Status"))}</th></tr></thead>
  <tbody>{feat_rows}</tbody></table></div>""" if feat_rows else ""
    mfact_table = f"""<h3>{esc(L(cfg, "market_facts_heading", "Market facts"))}</h3>
<div class="table-wrap"><table>
  <thead><tr><th>{esc(L(cfg, "mf_th_fact", "Fact"))}</th><th>{esc(L(cfg, "mf_th_status", "Status"))}</th></tr></thead>
  <tbody>{mfact_rows}</tbody></table></div>""" if mfact_rows else ""
    price_chart = s_price_comparison(cfg, numbers)
    return f"""<section>
  <h2>{esc(L(cfg, "product_heading", "3 · Product & Market Facts"))}</h2>
  {price_chart}
  {feat_table}
  {mfact_table}
</section>"""


def s_channel_map(cfg: dict, numbers: dict) -> str:
    """Section 5 — Local channel map."""
    channels = cfg.get("channels", [])
    rows = ""
    for ch in channels:
        v = ch.get("verdict", "undetermined")
        cac_est = fmt_value(ch["cac_estimate"], numbers) if ch.get("cac_estimate") and ch["cac_estimate"] in numbers else "—"
        rows += (f"<tr><td><strong>{esc(ch['name'])}</strong></td>"
                 f"<td>{esc(ch.get('task','—'))}</td>"
                 f"<td>{esc(ch.get('proxy_quality','—'))}</td>"
                 f"<td><span class='pill pill-{esc(v)}'>{esc(v)}</span></td>"
                 f"<td>{cac_est}</td>"
                 f"<td>{esc(ch.get('note',''))}</td></tr>")
    return f"""<section>
  <h2>{esc(L(cfg, "channel_heading", "4 · Local Channel Map"))}</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>{esc(L(cfg, "cm_th_channel", "Channel"))}</th><th>{esc(L(cfg, "cm_th_task", "Task"))}</th><th>{esc(L(cfg, "cm_th_proxy", "Proxy quality"))}</th><th>{esc(L(cfg, "cm_th_verdict", "Verdict"))}</th><th>{esc(L(cfg, "cm_th_cac", "CAC estimate"))}</th><th>{esc(L(cfg, "cm_th_note", "Note"))}</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
  <p style="font-size:13px;color:var(--muted)">{L(cfg, "channel_note", "Benchmarks may prove <em>not-viable</em> (best case still fails ceiling) but never <em>viable</em>. <em>undetermined</em> = interval spans ceiling; data acquisition required.")}</p>
</section>"""


def _score_dots(score_str: str) -> str:
    """Render '4/5' as filled/empty dots."""
    try:
        filled, total = map(int, score_str.split("/"))
    except Exception:
        return esc(score_str)
    dots = "".join(
        f'<span class="score-dot {"pass" if i < filled else "fail"}"></span>'
        for i in range(total)
    )
    return f'<span class="score-bar">{dots}</span> {esc(score_str)}'


def s_dimensions(cfg: dict) -> str:
    """Section 6 — D dimension table + Causal Activation Reviewer."""
    dims = cfg.get("dimensions", [])
    rows = ""
    for d in dims:
        status = d.get("resolution_status", "open")
        v = d.get("verdict", "Retain")
        rows += (f"<tr><td><strong>{esc(d['id'])}</strong> {esc(d['name'])}</td>"
                 f"<td style='font-size:12px'>{esc(d['mechanism'])}</td>"
                 f"<td style='font-size:12px'>{esc(d['proxy'])}</td>"
                 f"<td>{_score_dots(d.get('entry_score','—'))}</td>"
                 f"<td>{esc(v)}</td>"
                 f"<td><span class='pill pill-{esc(status)}'>{esc(status)}</span></td></tr>")
    reviewer_rows = "".join(
        f"<tr><td>{esc(r['dimension'])}</td><td>{esc(r['challenge'])}</td>"
        f"<td>{esc(r['handling'])}</td><td>{esc(r.get('evidence_needed',''))}</td></tr>"
        for r in cfg.get("reviewer_table", [])
    )
    reviewer = f"""<h3>{esc(L(cfg, "reviewer_heading", "Causal Activation Reviewer — dimension challenges"))}</h3>
<div class="table-wrap"><table>
  <thead><tr><th>{esc(L(cfg, "rv_th_dimension", "Dimension"))}</th><th>{esc(L(cfg, "rv_th_challenge", "Challenge raised"))}</th><th>{esc(L(cfg, "rv_th_handling", "Current handling"))}</th><th>{esc(L(cfg, "rv_th_evidence", "Evidence needed"))}</th></tr></thead>
  <tbody>{reviewer_rows}</tbody></table></div>
<div class="callout">{esc(L(cfg, "reviewer_callout", "D dimensions are candidate operational variables for trial design. Before entering primary budget, each must pass: deployable proxy, testable incrementality, stated mechanism, no compliance or margin risk."))}</div>""" if reviewer_rows else ""
    dim_chart = s_dimension_chart(cfg)
    return f"""<section>
  <h2>{esc(L(cfg, "dim_heading", "5 · D Dimension Table & Causal Activation Reviewer"))}</h2>
  {dim_chart}
  <div class="table-wrap"><table>
    <thead><tr><th>{esc(L(cfg, "dt_th_dimension", "Dimension"))}</th><th>{esc(L(cfg, "dt_th_mechanism", "Mechanism"))}</th><th>{esc(L(cfg, "dt_th_proxy", "Platform proxy"))}</th><th>{esc(L(cfg, "dt_th_score", "Score"))}</th><th>{esc(L(cfg, "dt_th_verdict", "Verdict"))}</th><th>{esc(L(cfg, "dt_th_status", "Status"))}</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
  <p style="font-size:13px;color:var(--muted)">{esc(L(cfg, "dim_verdict_legend", "Verdicts: Retain = H or T in heatmap · Retain (test) = T or S · Demote S = S only · Suppression = exclude not target · Delete = remove."))}</p>
  {reviewer}
</section>"""


def s_heatmap(cfg: dict) -> str:
    """Section 7 — Semantic heatmap (channel × dimension)."""
    hm = cfg.get("heatmap")
    if not hm:
        return ""
    channels = hm["channels"]
    dims = hm["dimensions"]
    scores = hm["scores"]
    label_map = hm.get("dim_labels", {})
    score_labels = {"H": "H — Primary", "T": "T — Test", "S": "S — Small", "N": "N — None", "A": "A — Avoid"}
    _score_cls = {"H": "hm-high", "T": "hm-test", "S": "hm-small", "N": "hm-none", "A": "hm-avoid"}
    n_cols = len(dims) + 1
    label_col = "2fr" if len(dims) > 8 else "1fr"
    col_def = f"{label_col} repeat({len(dims)}, 1fr)"
    corner = esc(L(cfg, "heatmap_corner", "Channel / Dimension"))
    header = f'<div class="hm-header">{corner}</div>' + "".join(
        f'<div class="hm-header">{esc(label_map.get(d, d))}</div>' for d in dims
    )
    rows = ""
    for ch in channels:
        rows += f'<div class="hm-label">{esc(ch)}</div>'
        for d in dims:
            sc = scores.get(ch, {}).get(d, "N")
            cls = _score_cls.get(sc, "hm-none")
            rows += f'<div class="hm-cell {esc(cls)}">{esc(sc)}</div>'
    legend = " · ".join(f'<span class="hm-cell {_score_cls[s]}" style="display:inline-block;padding:2px 8px;border-radius:4px">{s}</span> {lbl.split("—")[1].strip()}' for s, lbl in score_labels.items())
    return f"""<section>
  <h2>{esc(L(cfg, "heatmap_heading", "6 · Semantic Heatmap (channel × dimension)"))}</h2>
  <p style="font-size:13px">{L(cfg, "heatmap_intro", "Only channels that survived the viability screen appear. H = primary investment target; A = actively suppress.")}</p>
  <div class="heatmap" style="grid-template-columns:{esc(col_def)};margin:12px 0">
    {header}{rows}
  </div>
  <p style="font-size:12px;color:var(--muted);margin-top:8px">{esc(L(cfg, "heatmap_legend_label", "Legend"))}: {legend}</p>
</section>"""


def s_h_main(cfg: dict) -> str:
    """Section 8 — H-main breakdown."""
    h_cells = cfg.get("h_main_breakdown", [])
    rows = "".join(
        f"<tr><td><strong>{esc(h['channel_dim'])}</strong></td>"
        f"<td style='font-size:12px'>{esc(h['hypothesis'])}</td>"
        f"<td>{esc(h.get('t_card','—'))}</td>"
        f"<td style='font-size:12px'>{esc(h.get('notes',''))}</td></tr>"
        for h in h_cells
    )
    return f"""<section>
  <h2>{esc(L(cfg, "hmain_heading", "7 · H-Main Breakdown"))}</h2>
  <p>{esc(L(cfg, "hmain_intro", "These are the cells where HTE is expected to be positive. Each maps to a Treatment Card in the Execution Gates section. Priority order: top to bottom."))}</p>
  <div class="table-wrap"><table>
    <thead><tr><th>{esc(L(cfg, "hmain_th_cell", "Channel × Dimension"))}</th><th>{esc(L(cfg, "hmain_th_hypothesis", "HTE hypothesis"))}</th><th>{esc(L(cfg, "hmain_th_tcard", "Treatment Card"))}</th><th>{esc(L(cfg, "hmain_th_notes", "Notes"))}</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
</section>"""


def s_execution_gates(cfg: dict, numbers: dict, challenges_by_id: dict) -> str:
    """Section 9 — Execution gates + Treatment Cards (full T-card format)."""
    gates = cfg.get("execution_gates", [])
    gate_rows = ""
    for g in gates:
        gstatus = g["status"]
        gate_rows += (f"<tr><td><strong>{esc(g['gate'])}</strong></td>"
                      f"<td>{esc(g.get('input_needed',''))}</td>"
                      f"<td><span class='pill pill-{esc(gstatus)}'>{esc(gstatus)}</span></td>"
                      f"<td>{esc(g.get('note',''))}</td></tr>")
    gate_html = f"""<div class="table-wrap"><table>
  <thead><tr><th>{esc(L(cfg, "eg_th_gate", "Gate"))}</th><th>{esc(L(cfg, "eg_th_input", "Input needed"))}</th><th>{esc(L(cfg, "eg_th_status", "Status"))}</th><th>{esc(L(cfg, "eg_th_note", "Note"))}</th></tr></thead>
  <tbody>{gate_rows}</tbody></table></div>""" if gate_rows else ""

    audience_lbl = esc(L(cfg, "tc_audience", "Audience"))
    baseline_lbl = esc(L(cfg, "tc_baseline", "Baseline"))
    mechanism_lbl = esc(L(cfg, "tc_mechanism", "Mechanism"))
    guardrail_lbl = esc(L(cfg, "tc_guardrail", "Guardrail"))
    measurement_lbl = esc(L(cfg, "tc_measurement", "Measurement"))
    budget_lbl = esc(L(cfg, "tc_budget", "Budget envelope"))
    blocked_lbl = esc(L(cfg, "tc_blocked_by", "BLOCKED by"))
    cards = ""
    for a in cfg.get("actions", []):
        blockers = _blocked_by(a, challenges_by_id)
        stamp = "".join(f'<span class="blocked-stamp">&#8856; {blocked_lbl} {esc(b)}</span>' for b in blockers)
        audience = f"<dt>{audience_lbl}</dt><dd>{esc(a['audience'])}</dd>" if a.get("audience") else ""
        baseline = f"<dt>{baseline_lbl}</dt><dd>{esc(a['baseline'])}</dd>" if a.get("baseline") else ""
        budget = (f"<dt>{budget_lbl}</dt><dd>{fmt_value(a['budget'], numbers)}</dd>"
                  if a.get("budget") and a["budget"] in numbers else "")
        cards += f"""<div class="card{' blocked' if blockers else ''}">
  <h3>{esc(a['id'])} · {esc(a['action'])} {stamp}</h3>
  <dl>
    {audience}
    {baseline}
    <dt>{mechanism_lbl}</dt><dd>{esc(a.get('mechanism', '—'))}</dd>
    <dt>{guardrail_lbl}</dt><dd>{esc(a.get('guardrail', '—'))}</dd>
    <dt>{measurement_lbl}</dt><dd>{esc(a.get('measurement', a.get('test', '—')))}</dd>
    {budget}
  </dl>
</div>"""
    maturity = cfg.get("measurement_plan", {}).get("maturity", "L0")
    return f"""<section>
  <h2>{esc(L(cfg, "eg_heading", "8 · Execution Gates & Treatment Cards"))}</h2>
  <p><strong>{esc(L(cfg, "maturity_label", "Maturity"))}: {esc(maturity)}</strong> — {esc(L(cfg, "eg_maturity_note", "this analysis supports trial design and channel screening, not CATE claims or policy optimization."))}</p>
  {gate_html}
  {power_bridge(cfg)}
  <h3>{esc(L(cfg, "eg_tcards_heading", "Treatment Cards (H-main cells only)"))}</h3>
  <div class="cards">{cards}</div>
</section>"""


def s_budget(cfg: dict, numbers: dict) -> str:
    """Section 10 — Budget allocation."""
    rows = cfg.get("budget_rows", [])
    if not rows:
        return ""
    row_html = "".join(
        f"<tr><td>{esc(r['phase'])}</td><td>{esc(r['item'])}</td>"
        f"<td>{fmt_value(r['budget_id'], numbers) if r.get('budget_id') and r['budget_id'] in numbers else esc(r.get('budget_display','—'))}</td>"
        f"<td>{esc(r.get('condition',''))}</td></tr>"
        for r in rows
    )
    note = cfg.get("budget_note", "")
    budget_chart = s_budget_chart(cfg, numbers)
    return f"""<section>
  <h2>{esc(L(cfg, "budget_heading", "10 · Budget Allocation"))}</h2>
  {budget_chart}
  <div class="table-wrap"><table>
    <thead><tr><th>{esc(L(cfg, "bg_th_phase", "Phase"))}</th><th>{esc(L(cfg, "bg_th_item", "Item"))}</th><th>{esc(L(cfg, "bg_th_budget", "Budget"))}</th><th>{esc(L(cfg, "bg_th_condition", "Condition"))}</th></tr></thead>
    <tbody>{row_html}</tbody></table></div>
  {f'<p class="callout">{esc(note)}</p>' if note else ""}
</section>"""


def s_priority_plays(cfg: dict, numbers: dict) -> str:
    """Section 11 — Priority plays."""
    plays = cfg.get("priority_plays", [])
    whynow_lbl = esc(L(cfg, "pp_why_now", "Why now"))
    cac_lbl = esc(L(cfg, "pp_expected_cac", "Expected incremental CAC"))
    needstest_lbl = esc(L(cfg, "tag_needs_test", "Needs test"))
    killline_lbl = esc(L(cfg, "pp_kill_line", "Kill line"))
    cards = "".join(
        f"""<div class="card">
  <h3>{esc(p['play'])} — {esc(p['action'])}</h3>
  <dl>
    <dt>{whynow_lbl}</dt><dd>{esc(p['why_now'])}</dd>
    <dt>{cac_lbl}</dt><dd><span class="tag needs-test">{needstest_lbl}</span> {esc(p.get('expected_cac','undetermined'))}</dd>
    <dt>{killline_lbl}</dt><dd>{esc(p.get('kill_line',''))}</dd>
  </dl>
</div>"""
        for p in plays
    )
    auuc_note = cfg.get("auuc_note", "No uplift model scores available yet — AUUC gate will be applied when model predictions are generated after pilot data collection.")
    return f"""<section>
  <h2>{esc(L(cfg, "plays_heading", "11 · Priority Plays & ROI Scenarios"))}</h2>
  <div class="callout">{esc(auuc_note)}</div>
  <div class="cards">{cards}</div>
</section>"""


def s_kol(cfg: dict, numbers: dict) -> str:
    """Section 12 — KOL / Creator sourcing."""
    kol = cfg.get("kol")
    if not kol or not kol.get("enabled"):
        return ""
    creators = kol.get("creators", [])
    creator_html = ""
    for c in creators:
        fee = fmt_value(c["fee_id"], numbers) if c.get("fee_id") and c["fee_id"] in numbers else "—"
        format_lbl = esc(L(cfg, "kol_format", "Format"))
        fee_lbl = esc(L(cfg, "kol_fee", "Fee estimate"))
        assumption_lbl = esc(L(cfg, "tag_assumption", "Assumption"))
        pending_lbl = esc(L(cfg, "kol_fee_pending", "pending direct quote"))
        attribution_lbl = esc(L(cfg, "kol_attribution", "Attribution"))
        incrementality_lbl = esc(L(cfg, "kol_incrementality", "Incrementality"))
        needstest_lbl = esc(L(cfg, "tag_needs_test", "Needs test"))
        creator_html += f"""<div class="kol-card">
  <strong>{esc(c['profile'])}</strong>
  <dl style="margin:6px 0 0;font-size:13px">
    <dt style="color:var(--muted);font-size:11px;text-transform:uppercase">{format_lbl}</dt>
    <dd>{esc(c['format'])}</dd>
    <dt style="color:var(--muted);font-size:11px;text-transform:uppercase;margin-top:6px">{fee_lbl}</dt>
    <dd><span class="tag assumption">{assumption_lbl}</span> {fee} — {pending_lbl}</dd>
    <dt style="color:var(--muted);font-size:11px;text-transform:uppercase;margin-top:6px">{attribution_lbl}</dt>
    <dd>{esc(c['attribution'])}</dd>
    <dt style="color:var(--muted);font-size:11px;text-transform:uppercase;margin-top:6px">{incrementality_lbl}</dt>
    <dd><span class="tag needs-test">{needstest_lbl}</span> {esc(c['incrementality_note'])}</dd>
  </dl>
</div>"""
    rule = kol.get("roi_rule", "KOL ROI is never Evidence without a holdout or credible identification strategy. All creator attribution is tagged Hypothesis until a holdout arm is designed.")
    return f"""<section>
  <h2>{esc(L(cfg, "kol_heading", "12 · KOL / Creator Sourcing"))}</h2>
  <div class="callout">{esc(rule)}</div>
  {creator_html}
</section>"""


def s_measurement(cfg: dict) -> str:
    """Section 13 — Measurement plan."""
    mp = cfg.get("measurement_plan", {})
    if not mp:
        return ""
    maturity = mp.get("maturity", "L0")
    primary = mp.get("primary_metric", "")
    secondary = mp.get("secondary_metrics", [])
    scale_up = mp.get("scale_up_rule", "")
    pause_rule = mp.get("pause_rule", "")
    gcg = mp.get("gcg_design", "")
    hte_note = mp.get("hte_note", "")
    sec = mp.get("secondary_metrics", [])
    sec_items = "".join(f"<li>{esc(m)}</li>" for m in sec)
    return f"""<section>
  <h2>{esc(L(cfg, "measurement_heading", "13 · Measurement Plan"))}</h2>
  <p><strong>{esc(L(cfg, "maturity_label", "Maturity"))}: {esc(maturity)}</strong></p>
  <p><strong>{esc(L(cfg, "mp_primary", "Primary metric:"))}</strong> {esc(primary)}</p>
  {"<p><strong>" + esc(L(cfg, "mp_secondary", "Secondary metrics:")) + "</strong></p><ul>" + sec_items + "</ul>" if sec_items else ""}
  {"<h3>" + esc(L(cfg, "mp_scaleup", "Scale-up rule")) + "</h3><p>" + esc(scale_up) + "</p>" if scale_up else ""}
  {"<h3>" + esc(L(cfg, "mp_pause", "Pause rule")) + "</h3><p>" + esc(pause_rule) + "</p>" if pause_rule else ""}
  {"<h3>" + esc(L(cfg, "mp_gcg", "GCG design")) + "</h3><p>" + esc(gcg) + "</p>" if gcg else ""}
  {"<div class='callout'>" + esc(hte_note) + "</div>" if hte_note else ""}
</section>"""


def s_suppression(cfg: dict) -> str:
    """Section 14 — Suppression & risk rules."""
    rules = cfg.get("suppression_rules", [])
    if not rules:
        return ""
    rows = "".join(
        f"<tr><td>{esc(r['rule'])}</td><td>{esc(r['dimension'])}</td><td>{esc(r['reason'])}</td></tr>"
        for r in rules
    )
    ope_note = cfg.get("ope_note", "OPE support check (ope_estimators.py) will run once propensity log P(t|x) is available. Gate: support check must pass before any scaled deployment.")
    return f"""<section>
  <h2>{esc(L(cfg, "suppression_heading", "15 · Suppression & Risk Rules"))}</h2>
  <div class="callout">{esc(ope_note)}</div>
  <div class="table-wrap"><table>
    <thead><tr><th>{esc(L(cfg, "sp_th_rule", "Rule"))}</th><th>{esc(L(cfg, "sp_th_dimension", "Dimension"))}</th><th>{esc(L(cfg, "sp_th_reason", "Reason"))}</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
</section>"""


def s_checklist(cfg: dict) -> str:
    """Section 15 — Sources + Verification checklist."""
    items = cfg.get("checklist", [])
    status_icons = {"done": "✓", "pending": "○", "blocked": "⊘", "na": "—"}
    status_cls = {"done": "chk-done", "pending": "chk-pending", "blocked": "chk-blocked", "na": "chk-pending"}
    list_items = "".join(
        f'<li><span class="{esc(status_cls.get(i["status"],"chk-pending"))}">'
        f'{esc(status_icons.get(i["status"],"○"))}</span> {esc(i["item"])}</li>'
        for i in items
    )
    return f"""<section>
  <h2>{esc(L(cfg, "checklist_heading", "17 · Sources & Verification Checklist"))}</h2>
  <ul class="checklist">{list_items}</ul>
</section>"""


def s_termination(cfg: dict) -> str:
    term = cfg.get("termination")
    if not term:
        return ""
    term_heading = L(cfg, "termination_heading", "Pipeline terminated at stage {stage}").format(stage=esc(str(term["stage"])))
    return f"""<section style="border-left:6px solid var(--bad-ink)">
  <h2>{term_heading}</h2>
  <p>{esc(term["reason"])}</p>
  <p>{esc(L(cfg, "termination_note", "This report is intentionally short: the math does not support a media plan. The levers that would change the math are listed in the sensitivity table and the Missing ledger. Re-run the pipeline when one of them moves."))}</p>
</section>"""


# ──────────────────────────────────────────────────────────────────────────────
# Assembly
# ──────────────────────────────────────────────────────────────────────────────

def generate_html(cfg: dict) -> str:
    numbers = validate_and_resolve(cfg.get("numbers", {}))
    for w in lint_prose(cfg, numbers):
        print(f"LINT WARNING — {w}", file=sys.stderr)

    challenges_by_id = {c["id"]: c for c in cfg.get("challenges", [])}
    meta = cfg.get("meta", {})
    short_mode = bool(cfg.get("termination"))

    # Single monotonic section sequence. s_actions was removed: it duplicated
    # the Treatment Cards already rendered by s_execution_gates.
    parts = [s_memo(cfg), s_termination(cfg), s_math(cfg, numbers)]
    if short_mode:
        parts.append(s_evidence(cfg, numbers))   # short report: memo + math + evidence
    else:
        parts += [
            s_product_facts(cfg, numbers),                     # 3
            s_channel_map(cfg, numbers),                       # 4
            s_dimensions(cfg),                                 # 5
            s_heatmap(cfg),                                    # 6
            s_h_main(cfg),                                     # 7
            s_execution_gates(cfg, numbers, challenges_by_id), # 8
            s_challenges(cfg),                                 # 9
            s_budget(cfg, numbers),                            # 10
            s_priority_plays(cfg, numbers),                    # 11
            s_kol(cfg, numbers),                               # 12
            s_measurement(cfg),                                # 13
            s_test_plan(cfg),                                  # 14
            s_suppression(cfg),                                # 15
            s_evidence(cfg, numbers),                          # 16
            s_checklist(cfg),                                  # 17
        ]

    title = f'{meta.get("product", "")} — {meta.get("market", "")} Decision Memo'
    return f"""<!doctype html>
<html lang="{esc(meta.get("lang", "hu"))}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<main>
{''.join(parts)}
</main>
<footer>
  Generated {esc(meta.get("date", str(date.today())))} ·
  Every number is sourced, assumed (basis stated), derived (chain shown), or missing (no value displayed) ·
  <a href="https://github.com/alexwang91/scientific-marketing-personalized-attribution-hte">methodology</a>
</footer>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# Demo config — minimal, shows the schema; real example: examples/ax3-romania-config.json
# ──────────────────────────────────────────────────────────────────────────────

DEMO_CONFIG: dict[str, Any] = {
    "meta": {"product": "DemoProduct", "market": "DemoMarket", "date": str(date.today()), "lang": "en"},
    "decision_memo": {
        "verdict": "conditional",
        "thesis": "Unit margin is 30.0 USD; no channel has local data proving CAC below the 18.0 USD ceiling. "
                  "Do not allocate media budget; run the two zero-cost data pulls first.",
        "decisions": [
            {"horizon": "now", "text": "Pull keyword CPC (zero cost) — it is the highest-sensitivity unknown."},
            {"horizon": "checkpoint", "text": "If projected CAC < ceiling at checkpoint, unlock pilot."},
            {"horizon": "never", "text": "Influencer hero spend — unit economics cannot support it."},
        ],
        "overturn_conditions": ["Margin is actually 50% (ceiling rises to 30 USD)"],
        "weakest_point": "CPC and CVR are both missing; the screen rests on benchmark ranges.",
    },
    "numbers": {
        "price": {"label": "Retail price", "value": 100, "unit": "USD", "decimals": 0,
                  "provenance": "sourced", "source_url": "https://example.com", "source_label": "official store",
                  "accessed": str(date.today())},
        "margin_rate": {"label": "Gross margin", "value": 0.30, "pct": True,
                        "provenance": "assumed", "basis": "user input, not confirmed by finance"},
        "unit_margin": {"label": "Unit margin", "unit": "USD",
                        "provenance": "derived", "formula": "price * margin_rate", "inputs": ["price", "margin_rate"]},
        "cac_share": {"label": "CAC share of margin", "value": 0.6, "pct": True,
                      "provenance": "assumed", "basis": "convention: acquisition ≤ 60% of first-order margin"},
        "cac_ceiling": {"label": "CAC ceiling", "unit": "USD",
                        "provenance": "derived", "formula": "unit_margin * cac_share", "inputs": ["unit_margin", "cac_share"]},
        "search_cpc": {"label": "Search CPC (local)", "provenance": "missing",
                       "needed_from": "Keyword Planner", "cost_to_get": "0 budget, 1 hour",
                       "blocks": ["search channel verdict"]},
        "bench_cvr": {"label": "Benchmark site CVR", "value": [0.01, 0.03], "pct": True,
                      "provenance": "assumed", "basis": "industry benchmark range, not local data"},
        "bench_cpc": {"label": "Benchmark CPC", "value": [0.3, 1.2], "unit": "USD", "decimals": 2,
                      "provenance": "assumed", "basis": "industry benchmark range, not local data"},
        "search_cac_bench": {"label": "Search CAC (benchmark)", "unit": "USD",
                             "provenance": "derived", "formula": "bench_cpc / bench_cvr",
                             "inputs": ["bench_cpc", "bench_cvr"],
                             "note": "Interval spans the ceiling → verdict is undetermined, not a coin flip."},
    },
    "kpi_strip": ["price", "unit_margin", "cac_ceiling"],
    "cac_chart": {"ceiling_id": "cac_ceiling"},
    "derivations": ["unit_margin", "cac_ceiling", "search_cac_bench"],
    "sensitivity": [
        {"change": "margin 30% → 50%", "effect": "ceiling 18 → 30 USD; search may flip to viable", "priority": 1},
    ],
    "channel_screen": [
        {"channel": "Search", "verdict": "undetermined", "cac_estimate": "search_cac_bench",
         "reasoning": "Benchmark interval spans the ceiling; need local CPC (missing) to decide."},
        {"channel": "Social prospecting", "verdict": "not-viable", "cac_estimate": None,
         "reasoning": "Best-case benchmark CAC already exceeds ceiling — benchmark may kill, never green-light."},
    ],
    "actions": [
        {"id": "A1", "action": "Pull local keyword CPC", "mechanism": "Resolves highest-sensitivity unknown",
         "guardrail": "—", "test": "Compare projected CAC vs ceiling", "gate": "Search pilot"},
    ],
    "rejected_options": [{"option": "Influencer hero spend", "reason": "Unit margin cannot cover creator costs."}],
    "challenges": [
        {"id": "C1", "target": "Search", "question": "Brand-term clicks may be sure-things.",
         "status": "open", "evidence_needed": "brand keyword holdout"},
    ],
    "test_plan": [
        {"name": "Search CAC check", "prediction": "CAC lands above ceiling",
         "test": "2-week minimal spend on exact-match terms", "kill_line": "CAC > 2× ceiling for 7 days",
         "decision_date": "checkpoint + 14d"},
    ],
    "facts": [
        {"fact": "Retail price 100 USD at official store", "source_url": "https://example.com",
         "source_label": "official store", "accessed": str(date.today())},
    ],
}


def main():
    ap = argparse.ArgumentParser(description="Decision-memo HTML report generator (v2, provenance-enforced)")
    ap.add_argument("--demo", action="store_true", help="render built-in minimal demo")
    ap.add_argument("--config", help="JSON config path")
    ap.add_argument("--output", help="output HTML path (default stdout)")
    ap.add_argument("--validate-only", action="store_true", help="validate config, render nothing")
    args = ap.parse_args()

    if args.demo:
        cfg = DEMO_CONFIG
    elif args.config:
        cfg = json.loads(Path(args.config).read_text())
    else:
        ap.print_help()
        sys.exit(1)

    try:
        if args.validate_only:
            validate_and_resolve(cfg.get("numbers", {}))
            for w in lint_prose(cfg, cfg["numbers"]):
                print(f"LINT WARNING — {w}", file=sys.stderr)
            print("Config valid: provenance contract satisfied.", file=sys.stderr)
            return
        html = generate_html(cfg)
    except ConfigError as e:
        print(f"BUILD FAILED — {e}", file=sys.stderr)
        sys.exit(2)

    if args.output:
        Path(args.output).write_text(html, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(html)


if __name__ == "__main__":
    main()
