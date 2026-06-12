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
  :root{--bg:#f6f7f8;--panel:#fff;--ink:#172026;--muted:#5f6b76;--line:#d9dee3;
    --ok:#dff3e8;--ok-ink:#145c3b;--warn:#fff1bf;--warn-ink:#6b4e00;
    --bad:#f8d2cf;--bad-ink:#84211b;--neutral:#f2f4f7;--neutral-ink:#4c5965;--blue:#245d7c}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:Arial,"Helvetica Neue",sans-serif;line-height:1.5}
  main{max-width:1080px;margin:0 auto;padding:22px 24px 48px}
  h1{margin:0 0 6px;font-size:26px;line-height:1.2}
  h2{margin:30px 0 12px;font-size:19px;border-bottom:1px solid var(--line);padding-bottom:8px}
  h3{margin:18px 0 8px;font-size:15px}
  p{margin:6px 0 10px}
  a{color:#0f5f91}
  section{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:18px;margin:14px 0}
  .memo{border-left:6px solid var(--blue);padding:20px 22px}
  .memo .thesis{font-size:16px;line-height:1.55;margin:10px 0 14px}
  .verdict{display:inline-block;padding:5px 14px;border-radius:6px;font-weight:700;font-size:14px;letter-spacing:.03em}
  .verdict-go{background:var(--ok);color:var(--ok-ink)}
  .verdict-no-go{background:var(--bad);color:var(--bad-ink)}
  .verdict-conditional{background:var(--warn);color:var(--warn-ink)}
  .memo-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
  .memo-grid>div{border:1px solid var(--line);border-radius:8px;padding:12px;background:#fbfcfd}
  .memo-grid h3{margin:0 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
  .memo-grid ul{margin:0;padding-left:18px}
  .memo-grid li{margin:4px 0}
  .derivation{font-family:ui-monospace,Consolas,monospace;font-size:13px;background:#f6f8fa;
    border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:10px 0}
  .deriv-name{font-weight:700;margin-bottom:4px}
  .deriv-line{padding-left:14px;color:#33414d}
  .deriv-result{padding-left:14px;margin-top:2px}
  .deriv-note{margin-top:6px;color:var(--muted);font-family:Arial,sans-serif;font-size:12px}
  .prov-note{color:var(--muted);font-size:11px}
  sup.mk{font-size:9px;font-weight:700;padding:0 2px;margin-left:1px}
  .mk-sourced{color:#0f6842}.mk-assumed{color:#805d00}.mk-derived{color:#164f78}.mk-missing{color:#8a2018}
  .mk-legend{font-size:12px;color:var(--muted);margin:6px 0 0}
  .missing-val{color:#9aa4ad;border-bottom:1px dashed #c2cad1}
  .pill{display:inline-block;padding:3px 9px;border-radius:999px;font-size:12px;font-weight:700;white-space:nowrap}
  .pill-viable{background:var(--ok);color:var(--ok-ink)}
  .pill-not-viable{background:var(--bad);color:var(--bad-ink)}
  .pill-undetermined{background:var(--warn);color:var(--warn-ink)}
  .pill-role-only{background:var(--neutral);color:var(--neutral-ink)}
  .pill-resolved{background:var(--ok);color:var(--ok-ink)}
  .pill-open{background:var(--warn);color:var(--warn-ink)}
  .pill-open-blocking{background:var(--bad);color:var(--bad-ink)}
  .blocked-stamp{display:inline-block;border:2px solid var(--bad-ink);color:var(--bad-ink);
    padding:2px 10px;border-radius:4px;font-weight:700;font-size:12px;transform:rotate(-2deg);margin-left:8px}
  .table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:#fff}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{border-bottom:1px solid var(--line);border-right:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
  th{background:#edf1f4;font-weight:700}
  tr:last-child td{border-bottom:0}
  td:last-child,th:last-child{border-right:0}
  .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px;margin-top:10px}
  .card{border:1px solid var(--line);border-radius:8px;padding:12px 14px;background:#fbfcfd}
  .card.blocked{border-color:var(--bad-ink);background:#fdf6f5}
  .card h3{margin:0 0 6px;font-size:14px}
  .card dl{margin:0;font-size:13px}
  .card dt{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.03em;margin-top:7px}
  .card dd{margin:1px 0 0}
  .callout{border-left:5px solid var(--blue);border:1px solid var(--line);border-left-width:5px;
    border-radius:8px;padding:12px 16px;margin:12px 0;background:#f9fbfc}
  footer{max-width:1080px;margin:0 auto;padding:18px 24px 40px;color:var(--muted);font-size:12px}
  @media(max-width:760px){.memo-grid,.cards{grid-template-columns:1fr}}
  @media print{body{background:#fff}section{break-inside:avoid}a{color:#000}}
"""


# ──────────────────────────────────────────────────────────────────────────────
# Sections
# ──────────────────────────────────────────────────────────────────────────────

def s_memo(cfg: dict) -> str:
    memo = cfg["decision_memo"]
    meta = cfg.get("meta", {})
    verdict = memo.get("verdict", "conditional")
    vlabel = {"go": "GO", "no-go": "NO-GO", "conditional": "CONDITIONAL"}.get(verdict, verdict.upper())
    horizon_label = {"now": "Now (zero cost)", "checkpoint": "At checkpoint", "never": "Not under this math"}
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
  <div><span class="verdict verdict-{esc(verdict)}">{esc(vlabel)}</span>
  &nbsp; <span style="color:var(--muted);font-size:13px">{esc(meta.get("product", ""))} · {esc(meta.get("market", ""))} · {esc(meta.get("date", ""))}</span></div>
  <h1 style="margin-top:12px">1 · Decision Memo</h1>
  <p class="thesis"><strong>Thesis:</strong> {esc(memo["thesis"])}</p>
  <div class="memo-grid">
    <div>{decision_html}</div>
    <div>
      <h3>What overturns this thesis</h3><ul>{overturn}</ul>
      <h3>Weakest point of this report</h3><p style="margin:4px 0 0">{esc(memo.get("weakest_point", ""))}</p>
    </div>
  </div>
  <p class="mk-legend">Number markers: <sup class="mk mk-sourced">S</sup> sourced (linked)
  · <sup class="mk mk-assumed">A</sup> assumed (basis stated)
  · <sup class="mk mk-derived">D</sup> derived (chain shown)
  · <sup class="mk mk-missing">M</sup> missing (no value — placeholder only)</p>
</section>"""


def s_math(cfg: dict, numbers: dict) -> str:
    chains = "".join(render_derivation(nid, numbers) for nid in cfg.get("derivations", []))
    sens_rows = "".join(
        f"<tr><td>{esc(s['change'])}</td><td>{esc(s['effect'])}</td>"
        f"<td style='text-align:center'>{esc(str(s['priority']))}</td></tr>"
        for s in sorted(cfg.get("sensitivity", []), key=lambda x: x["priority"])
    )
    sens = ""
    if sens_rows:
        sens = f"""<h3>Sensitivity — which assumption flips the conclusion</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>Assumption change</th><th>Effect on conclusion</th><th>Verify priority</th></tr></thead>
    <tbody>{sens_rows}</tbody></table></div>
  <p style="font-size:13px;color:var(--muted)">Verification order below follows this table, not convenience.</p>"""

    screen_rows = ""
    for ch in cfg.get("channel_screen", []):
        v = ch["verdict"]
        cac = fmt_value(ch["cac_estimate"], numbers) if ch.get("cac_estimate") else "—"
        screen_rows += (f"<tr><td><strong>{esc(ch['channel'])}</strong></td>"
                        f"<td><span class='pill pill-{esc(v)}'>{esc(v)}</span></td>"
                        f"<td>{cac}</td><td>{esc(ch['reasoning'])}</td></tr>")
    screen = ""
    if screen_rows:
        screen = f"""<h3>Channel viability screen (threshold: CAC ceiling above)</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>Channel</th><th>Verdict</th><th>CAC estimate</th><th>Reasoning / what's missing</th></tr></thead>
    <tbody>{screen_rows}</tbody></table></div>
  <p style="font-size:13px;color:var(--muted)">Rules: a benchmark-based estimate can prove
  <em>not-viable</em> (best case still fails) but never <em>viable</em> — that requires local data.
  <em>undetermined</em> means the interval spans the ceiling; the action is to get data, not to pick an endpoint.</p>"""

    return f"""<section>
  <h2>2 · The Math</h2>
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
            budget = f"<dt>Budget envelope</dt><dd>{fmt_value(a['budget'], numbers)}</dd>"
        gate = f"<dt>Unlocks</dt><dd>{esc(a['gate'])}</dd>" if a.get("gate") else ""
        cards += f"""<div class="card{' blocked' if blockers else ''}">
  <h3>{esc(a['id'])} · {esc(a['action'])} {stamp}</h3>
  <dl>
    <dt>Mechanism</dt><dd>{esc(a['mechanism'])}</dd>
    <dt>Guardrail</dt><dd>{esc(a['guardrail'])}</dd>
    <dt>Test</dt><dd>{esc(a['test'])}</dd>
    {budget}{gate}
  </dl>
</div>"""
    rejected = "".join(
        f"<tr><td>{esc(r['option'])}</td><td>{esc(r['reason'])}</td></tr>"
        for r in cfg.get("rejected_options", [])
    )
    rej_html = ""
    if rejected:
        rej_html = f"""<h3>Rejected options (and why)</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>Option</th><th>Rejection reason</th></tr></thead>
    <tbody>{rejected}</tbody></table></div>"""
    return f"""<section>
  <h2>3 · Actions</h2>
  <p>Only options that survived the viability screen appear as cards. A card stamped
  <strong>⊘ BLOCKED</strong> references an unresolved blocking challenge (section 4) and
  must not receive budget until that challenge is resolved.</p>
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
  <h2>4 · Adversarial Review</h2>
  <p>Challenges are raised by an independent review pass and are immutable — the analysis
  may respond but not rewrite them. <strong>open-blocking</strong> challenges stamp every
  action that depends on them. An unresolved challenge displayed openly is the trust
  mechanism; "resolved" requires data, not rhetoric.</p>
  <div class="table-wrap"><table>
    <thead><tr><th>Challenge</th><th>Question</th><th>Status</th><th>Resolution / evidence needed</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
</section>"""


def s_test_plan(cfg: dict) -> str:
    cards = ""
    for t in cfg.get("test_plan", []):
        cards += f"""<div class="card">
  <h3>{esc(t['name'])}</h3>
  <dl>
    <dt>Prediction</dt><dd>{esc(t['prediction'])}</dd>
    <dt>Test</dt><dd>{esc(t['test'])}</dd>
    <dt>Kill line</dt><dd>{esc(t['kill_line'])}</dd>
    <dt>Decision date</dt><dd>{esc(t['decision_date'])}</dd>
  </dl>
</div>"""
    return f"""<section>
  <h2>5 · Test Plan</h2>
  <p>Every claim that survives to budget carries a falsifiable prediction, a kill line,
  and a decision date. On that date the line either becomes Sourced or is declared dead.</p>
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
  <h2>6 · Evidence &amp; Gaps</h2>
  <h3>Sourced facts</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>Fact</th><th>Source</th><th>Accessed</th></tr></thead>
    <tbody>{facts}</tbody></table></div>
  <h3>Assumption register</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>Assumption</th><th>Value</th><th>Basis</th></tr></thead>
    <tbody>{assumed_rows}</tbody></table></div>
  <h3>Missing ledger — sorted by sensitivity, this is the work plan</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>What</th><th>Where to get it</th><th>Cost</th><th>Blocks</th></tr></thead>
    <tbody>{missing_rows}</tbody></table></div>
</section>"""


def s_termination(cfg: dict) -> str:
    term = cfg.get("termination")
    if not term:
        return ""
    return f"""<section style="border-left:6px solid var(--bad-ink)">
  <h2>Pipeline terminated at stage {esc(str(term["stage"]))}</h2>
  <p>{esc(term["reason"])}</p>
  <p>This report is intentionally short: the math does not support a media plan.
  The levers that would change the math are listed in the sensitivity table and the
  Missing ledger. Re-run the pipeline when one of them moves.</p>
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

    parts = [s_memo(cfg), s_termination(cfg), s_math(cfg, numbers)]
    if not short_mode:
        parts += [s_actions(cfg, numbers, challenges_by_id),
                  s_challenges(cfg),
                  s_test_plan(cfg)]
    parts.append(s_evidence(cfg, numbers))

    title = f'{meta.get("product", "")} {meta.get("market", "")} — Decision Memo'
    return f"""<!doctype html>
<html lang="{esc(meta.get("lang", "en"))}">
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
