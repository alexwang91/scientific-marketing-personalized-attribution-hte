# Interactive Dashboard Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `--format dashboard` output that renders a single-file interactive dashboard from this repository's existing causal personalization configs.

**Architecture:** Keep the existing report renderer stable and default. Add a small data-normalization module that converts current configs into a dashboard object, then a separate renderer that emits the interactive HTML, CSS, and inline JavaScript. `generate_report.py` only routes between report and dashboard formats.

**Tech Stack:** Python stdlib, existing JSON config schema, single-file HTML/CSS/JavaScript, current custom test runner style, optional Node syntax check when available.

---

## File Structure

- Create `.claude/skills/sm-causal-personalization/scripts/dashboard_data.py`
  - Build normalized dashboard dictionaries from existing configs.
  - Preserve provenance and missing-data states.
  - Support SKU/product-country and `category_portfolio` configs.

- Create `.claude/skills/sm-causal-personalization/scripts/dashboard_render.py`
  - Render the normalized object into single-file HTML.
  - Own dashboard CSS, right-panel markup, search, click handlers, responsive behavior.

- Modify `.claude/skills/sm-causal-personalization/scripts/generate_report.py`
  - Add `--format report|dashboard`.
  - Keep report path unchanged.
  - Route dashboard format to `dashboard_data.build_dashboard_data()` and `dashboard_render.render_dashboard()`.

- Modify `.claude/skills/sm-causal-personalization/scripts/__init__.py`
  - Export new modules for package import smoke tests.

- Create `tests/test_dashboard_data.py`
  - Unit tests for SKU and category conversion.

- Create `tests/test_dashboard_render.py`
  - Rendering and CLI smoke tests.

- Modify `tests/test_generate_report.py`
  - Add a CLI test for `--demo --format dashboard`.

- Modify `scripts/run_all_checks.py`
  - Include new dashboard tests.

- Modify `.github/workflows/validate.yml`
  - Render dashboard smoke outputs for all committed example configs.
  - Check package import includes new modules.

---

### Task 1: Dashboard Data Converter

**Files:**
- Create: `.claude/skills/sm-causal-personalization/scripts/dashboard_data.py`
- Test: `tests/test_dashboard_data.py`

- [ ] **Step 1: Write failing data-converter tests**

Create `tests/test_dashboard_data.py`:

```python
#!/usr/bin/env python3
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "scripts"
DATA_PATH = SCRIPTS / "dashboard_data.py"
REPORT_PATH = SCRIPTS / "generate_report.py"
SKU_CONFIG = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "examples" / "sample-sku-en-config.json"
CAT_CONFIG = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "examples" / "aurora-airpurifier-category-config.json"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


data_mod = _load_module("dashboard_data", DATA_PATH)
rpt = _load_module("generate_report", REPORT_PATH)


def _config(path):
    cfg = json.loads(path.read_text(encoding="utf-8"))
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    return cfg


def test_sku_config_builds_dashboard_data():
    data = data_mod.build_dashboard_data(_config(SKU_CONFIG))
    assert data["kind"] == "sku"
    assert data["meta"]["product"] == "Vela BrewPro B1"
    assert data["overview"]["verdict"] == "conditional"
    assert data["kpis"]
    assert any(c["name"].startswith("Search") for c in data["channels"])
    assert any(t["id"] == "A1" for t in data["treatments"])
    assert data["evidence"]["missing"]


def test_category_config_builds_portfolio_dashboard_data():
    data = data_mod.build_dashboard_data(_config(CAT_CONFIG))
    assert data["kind"] == "category_portfolio"
    assert data["meta"]["product"] == "Aurora Air Purifiers"
    assert data["portfolio"]["verdict_counts"]["grow"] == 3
    assert len(data["portfolio"]["tiers"]) == 3
    assert len(data["portfolio"]["diagnosis"]) == 6
    assert any(row["sku"] == "Aurora A3" for row in data["portfolio"]["skus"])


def test_missing_numbers_stay_missing():
    data = data_mod.build_dashboard_data(_config(SKU_CONFIG))
    missing = {row["id"]: row for row in data["evidence"]["missing"]}
    assert "search_cpc" in missing
    assert missing["search_cpc"]["value"] is None
    assert "Keyword Planner" in missing["search_cpc"]["needed_from"]


def test_demo_config_has_readable_fallbacks():
    cfg = copy.deepcopy(rpt.DEMO_CONFIG)
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    data = data_mod.build_dashboard_data(cfg)
    assert data["meta"]["product"] == "DemoProduct"
    assert data["heatmap"]["columns"]
    assert data["heatmap"]["rows"]
    first = data["heatmap"]["columns"][0]
    assert first["id"] and first["label"]


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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python tests/test_dashboard_data.py
```

Expected: fails because `dashboard_data.py` does not exist.

- [ ] **Step 3: Implement dashboard data converter**

Create `.claude/skills/sm-causal-personalization/scripts/dashboard_data.py` with:

```python
#!/usr/bin/env python3
"""Normalize existing report configs into interactive dashboard data."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


def build_dashboard_data(cfg: Dict[str, Any]) -> Dict[str, Any]:
    if cfg.get("report_type") == "category_portfolio":
        return _build_category_dashboard(cfg)
    return _build_sku_dashboard(cfg)


def _meta(cfg: Dict[str, Any]) -> Dict[str, Any]:
    meta = cfg.get("meta", {})
    return {
        "product": meta.get("product") or meta.get("category") or "Untitled",
        "market": meta.get("market", "Unknown market"),
        "brand": meta.get("brand", ""),
        "category": meta.get("category", ""),
        "date": meta.get("date", ""),
        "lang": meta.get("lang", "en"),
    }


def _value_text(row: Dict[str, Any]) -> str:
    value = row.get("value")
    if value is None:
        return "Missing"
    if isinstance(value, list):
        return " - ".join(_format_scalar(v, row) for v in value)
    return _format_scalar(value, row)


def _format_scalar(value: Any, row: Dict[str, Any]) -> str:
    if isinstance(value, (int, float)):
        decimals = int(row.get("decimals", 1 if isinstance(value, float) else 0))
        if row.get("pct"):
            return f"{value * 100:.{decimals}f}%"
        text = f"{value:,.{decimals}f}"
        if decimals == 0:
            text = text.split(".")[0]
        unit = row.get("unit")
        return f"{text} {unit}" if unit else text
    return str(value)


def _number_row(number_id: str, row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": number_id,
        "label": row.get("label", number_id),
        "value": row.get("value"),
        "value_text": _value_text(row),
        "provenance": row.get("provenance", "unknown"),
        "basis": row.get("basis", ""),
        "note": row.get("note", ""),
        "needed_from": row.get("needed_from", ""),
        "cost_to_get": row.get("cost_to_get", ""),
        "blocks": row.get("blocks", []),
        "source_url": row.get("source_url", ""),
        "source_label": row.get("source_label", ""),
        "accessed": row.get("accessed", ""),
    }


def _numbers(cfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {number_id: _number_row(number_id, row) for number_id, row in cfg.get("numbers", {}).items()}


def _kpis(cfg: Dict[str, Any], numbers: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    ids = cfg.get("kpi_strip") or list(numbers.keys())[:4]
    return [numbers[number_id] for number_id in ids if number_id in numbers]


def _overview(cfg: Dict[str, Any], numbers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    memo = cfg.get("decision_memo", {})
    decisions = memo.get("decisions", [])
    top_now = next((d.get("text", "") for d in decisions if d.get("horizon") == "now"), "")
    missing = [row for row in numbers.values() if row["provenance"] == "missing"]
    top_blocker = missing[0]["label"] if missing else memo.get("weakest_point", "")
    return {
        "verdict": memo.get("verdict", "undetermined"),
        "thesis": memo.get("thesis", ""),
        "top_action": top_now,
        "top_blocker": top_blocker,
        "weakest_point": memo.get("weakest_point", ""),
        "overturn_conditions": memo.get("overturn_conditions", []),
        "decisions": decisions,
    }


def _channels(cfg: Dict[str, Any], numbers: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    channels = []
    for idx, row in enumerate(cfg.get("channel_screen", []), 1):
        estimate_id = row.get("cac_estimate")
        channels.append({
            "id": f"CH{idx:02d}",
            "name": row.get("channel", f"Channel {idx}"),
            "verdict": row.get("verdict", "undetermined"),
            "reasoning": row.get("reasoning", ""),
            "cac_estimate_id": estimate_id,
            "cac_estimate": numbers.get(estimate_id, {}) if estimate_id else {},
        })
    return channels


def _treatments(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    treatments = []
    for idx, row in enumerate(cfg.get("actions", []), 1):
        treatment_id = row.get("id") or f"A{idx}"
        treatments.append({
            "id": treatment_id,
            "label": _short(row.get("action", treatment_id)),
            "action": row.get("action", ""),
            "mechanism": row.get("mechanism", ""),
            "guardrail": row.get("guardrail", ""),
            "test": row.get("test", ""),
            "gate": row.get("gate", ""),
            "blocked_by": row.get("blocked_by", []),
        })
    return treatments


def _challenges(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [{
        "id": row.get("id", f"C{idx}"),
        "target": row.get("target", ""),
        "question": row.get("question", ""),
        "status": row.get("status", "open"),
        "evidence_needed": row.get("evidence_needed", ""),
    } for idx, row in enumerate(cfg.get("challenges", []), 1)]


def _dimensions(cfg: Dict[str, Any], treatments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    raw = cfg.get("dimensions") or cfg.get("d_dimensions") or []
    if raw:
        return [{
            "id": row.get("id", f"D{idx}"),
            "label": row.get("label") or row.get("name") or row.get("dimension") or f"D{idx}",
            "status": row.get("status", "test"),
            "logic": row.get("logic", row.get("reasoning", "")),
            "proxy": row.get("proxy", ""),
            "treatment_ids": row.get("treatment_ids", []),
        } for idx, row in enumerate(raw, 1)]
    fallback = []
    for idx, treatment in enumerate(treatments[:5], 1):
        fallback.append({
            "id": f"D{idx}",
            "label": _short(treatment["label"], 28),
            "status": "test",
            "logic": treatment.get("mechanism", ""),
            "proxy": treatment.get("gate", ""),
            "treatment_ids": [treatment["id"]],
        })
    return fallback or [{"id": "D1", "label": "Decision blocker", "status": "test", "logic": "Needs data", "proxy": "", "treatment_ids": []}]


def _heatmap(channels: List[Dict[str, Any]], dimensions: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    for channel in channels:
        verdict = channel.get("verdict")
        grades = []
        for idx, _dimension in enumerate(dimensions):
            if verdict == "not-viable":
                grade = "A" if idx == 0 else "N"
            elif verdict == "viable":
                grade = "H" if idx == 0 else "T"
            elif verdict == "role-only":
                grade = "S" if idx == 0 else "N"
            else:
                grade = "T" if idx == 0 else "N"
            grades.append(grade)
        rows.append({"channel_id": channel["id"], "grades": grades})
    return {"columns": dimensions, "rows": rows}


def _evidence(numbers: Dict[str, Dict[str, Any]], cfg: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sourced": [row for row in numbers.values() if row["provenance"] == "sourced"],
        "assumed": [row for row in numbers.values() if row["provenance"] == "assumed"],
        "derived": [row for row in numbers.values() if row["provenance"] == "derived"],
        "missing": [row for row in numbers.values() if row["provenance"] == "missing"],
        "facts": cfg.get("facts", []),
    }


def _build_sku_dashboard(cfg: Dict[str, Any]) -> Dict[str, Any]:
    numbers = _numbers(cfg)
    treatments = _treatments(cfg)
    challenges = _challenges(cfg)
    channels = _channels(cfg, numbers)
    dimensions = _dimensions(cfg, treatments)
    return {
        "kind": "sku",
        "meta": _meta(cfg),
        "overview": _overview(cfg, numbers),
        "kpis": _kpis(cfg, numbers),
        "economics": {
            "derivations": [numbers[number_id] for number_id in cfg.get("derivations", []) if number_id in numbers],
            "sensitivity": cfg.get("sensitivity", []),
        },
        "channels": channels,
        "dimensions": dimensions,
        "heatmap": _heatmap(channels, dimensions),
        "treatments": treatments,
        "budgets": cfg.get("budget", []) or cfg.get("budgets", []),
        "plays": cfg.get("priority_plays", []),
        "challenges": challenges,
        "tests": cfg.get("test_plan", []),
        "rejected_options": cfg.get("rejected_options", []),
        "evidence": _evidence(numbers, cfg),
    }


def _build_category_dashboard(cfg: Dict[str, Any]) -> Dict[str, Any]:
    numbers = _numbers(cfg)
    portfolio = cfg.get("portfolio", [])
    return {
        "kind": "category_portfolio",
        "meta": _meta(cfg),
        "overview": {
            "verdict": "portfolio",
            "thesis": cfg.get("_note", ""),
            "top_action": _category_top_action(portfolio),
            "top_blocker": _category_top_blocker(numbers),
            "weakest_point": "",
            "overturn_conditions": [],
            "decisions": [],
        },
        "kpis": _portfolio_kpis(portfolio, numbers),
        "economics": {"derivations": [], "sensitivity": []},
        "channels": [],
        "dimensions": [],
        "heatmap": {"columns": [], "rows": []},
        "treatments": [],
        "budgets": [],
        "plays": [],
        "challenges": [],
        "tests": [],
        "rejected_options": [],
        "evidence": _evidence(numbers, cfg),
        "portfolio": {
            "tiers": cfg.get("price_tiers", []),
            "diagnosis": cfg.get("diagnosis", []),
            "skus": portfolio,
            "verdict_counts": dict(Counter(row.get("verdict", "unknown") for row in portfolio)),
        },
    }


def _portfolio_kpis(portfolio: List[Dict[str, Any]], numbers: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts = Counter(row.get("verdict", "unknown") for row in portfolio)
    kpis = [
        {"id": "sku_count", "label": "SKUs", "value": len(portfolio), "value_text": str(len(portfolio)), "provenance": "derived"},
        {"id": "grow_count", "label": "Grow", "value": counts.get("grow", 0), "value_text": str(counts.get("grow", 0)), "provenance": "derived"},
        {"id": "exit_count", "label": "Exit", "value": counts.get("exit", 0), "value_text": str(counts.get("exit", 0)), "provenance": "derived"},
    ]
    missing = [row for row in numbers.values() if row["provenance"] == "missing"]
    if missing:
        kpis.append({"id": "missing_count", "label": "Missing data", "value": len(missing), "value_text": str(len(missing)), "provenance": "missing"})
    return kpis


def _category_top_action(portfolio: List[Dict[str, Any]]) -> str:
    grow = [row.get("sku", "") for row in portfolio if row.get("verdict") == "grow"]
    return "Deep-dive Grow SKUs: " + ", ".join(grow[:3]) if grow else "No Grow SKU selected"


def _category_top_blocker(numbers: Dict[str, Dict[str, Any]]) -> str:
    missing = [row for row in numbers.values() if row["provenance"] == "missing"]
    return missing[0]["label"] if missing else "No missing number registered"


def _short(text: str, limit: int = 36) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python tests/test_dashboard_data.py
```

Expected: all tests pass.

### Task 2: Dashboard Renderer

**Files:**
- Create: `.claude/skills/sm-causal-personalization/scripts/dashboard_render.py`
- Test: `tests/test_dashboard_render.py`

- [ ] **Step 1: Write failing render tests**

Create `tests/test_dashboard_render.py`:

```python
#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "scripts"
REPORT_PATH = SCRIPTS / "generate_report.py"
DATA_PATH = SCRIPTS / "dashboard_data.py"
RENDER_PATH = SCRIPTS / "dashboard_render.py"
SKU_CONFIG = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "examples" / "sample-sku-en-config.json"
CAT_CONFIG = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "examples" / "aurora-airpurifier-category-config.json"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rpt = _load_module("generate_report", REPORT_PATH)
data_mod = _load_module("dashboard_data", DATA_PATH)
render_mod = _load_module("dashboard_render", RENDER_PATH)


def _html(path):
    cfg = json.loads(path.read_text(encoding="utf-8"))
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    return render_mod.render_dashboard(data_mod.build_dashboard_data(cfg))


def test_sku_dashboard_html_contains_core_sections():
    html = _html(SKU_CONFIG)
    for marker in ["<!doctype html>", "decision-dashboard", "Economics", "Channel Screen", "Treatment Gates", "Evidence Ledger"]:
        assert marker in html, marker
    assert "Vela BrewPro B1" in html
    assert "Search" in html
    assert "__PLACEHOLDER__" not in html


def test_category_dashboard_html_contains_portfolio_sections():
    html = _html(CAT_CONFIG)
    for marker in ["Portfolio Verdict", "Tier Map", "Diagnosis Lenses", "SKU Matrix"]:
        assert marker in html, marker
    assert "Aurora A3" in html
    assert "L1" in html


def test_dashboard_cli_demo_renders_to_file():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "dashboard.html"
        proc = subprocess.run(
            [sys.executable, str(REPORT_PATH), "--demo", "--format", "dashboard", "--output", str(out)],
            capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        html = out.read_text(encoding="utf-8")
        assert "DemoProduct" in html
        assert "decision-dashboard" in html


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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python tests/test_dashboard_render.py
```

Expected: fails because `dashboard_render.py` and CLI support do not exist.

- [ ] **Step 3: Implement renderer**

Create `.claude/skills/sm-causal-personalization/scripts/dashboard_render.py` with:

```python
#!/usr/bin/env python3
"""Render normalized dashboard data as a single-file interactive HTML cockpit."""

from __future__ import annotations

import json
from html import escape
from typing import Any, Dict, Iterable, List


def render_dashboard(data: Dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    title = f"{data['meta'].get('product', 'Dashboard')} · {data['meta'].get('market', '')}"
    if data.get("kind") == "category_portfolio":
        body = _render_category(data)
    else:
        body = _render_sku(data)
    return f"""<!doctype html>
<html lang="{_esc(data['meta'].get('lang', 'en'))}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(title)}</title>
  <style>{_css()}</style>
</head>
<body>
<div class="decision-dashboard" data-kind="{_esc(data.get('kind', 'sku'))}">
  <nav class="rail" aria-label="Dashboard sections">
    <div class="rail-mark">SM</div>
    {_nav(data)}
  </nav>
  <main class="workspace">
    {body}
  </main>
  <aside class="detail-panel" id="detail-panel">
    <div class="eyebrow">Detail</div>
    <h2 id="detail-title">Select an item</h2>
    <div id="detail-body"><p>Click a KPI, channel, heatmap cell, treatment, diagnosis, or evidence row to inspect its reasoning.</p></div>
  </aside>
</div>
<script>
const DASHBOARD_DATA = {payload};
{_js()}
</script>
</body>
</html>"""


def _render_sku(data: Dict[str, Any]) -> str:
    return "\n".join([
        _hero(data, "Causal Launch Cockpit"),
        _kpis(data),
        _economics(data),
        _channels(data),
        _causal_map(data),
        _heatmap(data),
        _treatments(data),
        _evidence(data),
    ])


def _render_category(data: Dict[str, Any]) -> str:
    return "\n".join([
        _hero(data, "Portfolio Diagnostic Cockpit"),
        _kpis(data),
        _portfolio_tiers(data),
        _portfolio_diagnosis(data),
        _portfolio_skus(data),
        _evidence(data),
    ])


def _hero(data: Dict[str, Any], label: str) -> str:
    meta = data["meta"]
    overview = data.get("overview", {})
    return f"""<section class="hero section" id="overview">
  <div>
    <div class="eyebrow">{_esc(label)}</div>
    <h1>{_esc(meta.get('product', 'Untitled'))} <span>{_esc(meta.get('market', ''))}</span></h1>
    <p>{_esc(overview.get('thesis', 'No thesis provided.'))}</p>
  </div>
  <div class="hero-actions">
    <button class="pill verdict" data-detail='{_detail_json("Verdict", overview.get("thesis", ""), overview)}'>{_esc(str(overview.get('verdict', 'undetermined')).upper())}</button>
    <button class="pill" data-detail='{_detail_json("Top action", overview.get("top_action", ""), overview)}'>Top action</button>
    <button class="pill muted" data-detail='{_detail_json("Top blocker", overview.get("top_blocker", ""), overview)}'>Top blocker</button>
  </div>
</section>"""


def _kpis(data: Dict[str, Any]) -> str:
    cards = []
    for row in data.get("kpis", []):
        cards.append(f"""<button class="kpi-card" data-detail='{_detail_json(row.get("label", ""), row.get("note") or row.get("basis") or row.get("needed_from", ""), row)}'>
  <span>{_esc(row.get('label', 'Metric'))}</span>
  <strong>{_esc(str(row.get('value_text', row.get('value', ''))))}</strong>
  <em>{_esc(row.get('provenance', ''))}</em>
</button>""")
    return f'<section class="kpi-strip section" id="kpis">{"".join(cards)}</section>'


def _economics(data: Dict[str, Any]) -> str:
    rows = []
    for row in data.get("economics", {}).get("derivations", []):
        rows.append(_wide_card(row.get("label", row.get("id", "")), row.get("note") or row.get("basis", ""), row))
    for row in data.get("economics", {}).get("sensitivity", []):
        rows.append(_wide_card(row.get("change", "Sensitivity"), row.get("effect", ""), row))
    return _section("economics", "Economics", "Unit economics, CAC ceiling, and sensitivity levers.", rows or [_empty("No economics rows available.")])


def _channels(data: Dict[str, Any]) -> str:
    cards = []
    for channel in data.get("channels", []):
        cards.append(_wide_card(channel.get("name", ""), channel.get("reasoning", ""), channel, extra=f'<span class="status">{_esc(channel.get("verdict", ""))}</span>'))
    return _section("channels", "Channel Screen", "Which channels can be defended before spend is unlocked.", cards or [_empty("No channel screen available.")])


def _causal_map(data: Dict[str, Any]) -> str:
    nodes = ["Product", "Economics", "Channel", "Dimension", "Treatment", "Measurement"]
    html = "".join(f'<button class="graph-node" data-detail=\'{_detail_json(n, "Layer in the causal decision chain.", {"layer": n})}\'>{_esc(n)}</button>' for n in nodes)
    return _section("map", "Causal Map", "The dashboard keeps the reasoning sequence visible.", [f'<div class="graph">{html}</div>'])


def _heatmap(data: Dict[str, Any]) -> str:
    heatmap = data.get("heatmap", {})
    columns = heatmap.get("columns", [])
    rows = heatmap.get("rows", [])
    channels = {c["id"]: c for c in data.get("channels", [])}
    if not columns or not rows:
        return _section("heatmap", "Heatmap", "Channel x dimension fit.", [_empty("No heatmap data available.")])
    head = "<div class='heat-head'>Channel</div>" + "".join(f"<div class='heat-head'>{_esc(c['id'])}<br><span>{_esc(c['label'])}</span></div>" for c in columns)
    body = []
    for row in rows:
        channel = channels.get(row.get("channel_id"), {"name": row.get("channel_id", "")})
        body.append(f"<div class='heat-channel'>{_esc(channel.get('name', ''))}</div>")
        for col, grade in zip(columns, row.get("grades", [])):
            detail = {"channel": channel, "dimension": col, "grade": grade}
            cell_text = f"{grade}: {col.get('label', '')}"
            body.append(f"<button class='heat-cell grade-{_esc(grade)}' data-detail='{_detail_json(channel.get('name', ''), cell_text, detail)}'>{_esc(grade)}</button>")
    return _section("heatmap", "Heatmap", "Click a cell to inspect the causal hypothesis, proxy, and validation action.", [f"<div class='heatmap' style='--cols:{len(columns) + 1}'>{head}{''.join(body)}</div>"])


def _treatments(data: Dict[str, Any]) -> str:
    cards = []
    for treatment in data.get("treatments", []):
        text = " · ".join(x for x in [treatment.get("mechanism"), treatment.get("test"), treatment.get("gate")] if x)
        cards.append(_wide_card(f"{treatment.get('id')} {treatment.get('label')}", text, treatment))
    return _section("treatments", "Treatment Gates", "Every action carries mechanism, guardrail, test, and gate.", cards or [_empty("No treatment/action cards available.")])


def _portfolio_tiers(data: Dict[str, Any]) -> str:
    cards = [_wide_card(t.get("label", ""), f"{t.get('trend', '')} · {t.get('audience', '')} · {t.get('channel_fit', '')}", t) for t in data.get("portfolio", {}).get("tiers", [])]
    return _section("tiers", "Tier Map", "Price tiers, audiences, forces, and channel fit.", cards)


def _portfolio_diagnosis(data: Dict[str, Any]) -> str:
    cards = [_wide_card(f"{d.get('lens', '')} {d.get('title', '')}", d.get("implication", ""), d, extra=f'<span class="status">{_esc(d.get("severity", ""))}</span>') for d in data.get("portfolio", {}).get("diagnosis", [])]
    return _section("diagnosis", "Diagnosis Lenses", "L1-L6 category and 4P diagnosis.", cards)


def _portfolio_skus(data: Dict[str, Any]) -> str:
    cards = [_wide_card(f"{s.get('sku', '')} · {s.get('verdict', '')}", s.get("note", ""), s) for s in data.get("portfolio", {}).get("skus", [])]
    return _section("skus", "SKU Matrix", "SKU verdicts and 4P moves.", cards)


def _evidence(data: Dict[str, Any]) -> str:
    evidence = data.get("evidence", {})
    rows = []
    for group in ["missing", "sourced", "assumed", "derived"]:
        for row in evidence.get(group, []):
            rows.append(_wide_card(row.get("label", row.get("id", "")), row.get("needed_from") or row.get("basis") or row.get("note", ""), row, extra=f'<span class="status">{group}</span>'))
    for fact in evidence.get("facts", []):
        rows.append(_wide_card("Fact", fact.get("fact", ""), fact))
    return _section("evidence", "Evidence Ledger", "Sourced facts, assumptions, derivations, and missing values.", rows or [_empty("No evidence rows available.")])


def _section(section_id: str, title: str, subtitle: str, children: Iterable[str]) -> str:
    return f"""<section class="panel section" id="{_esc(section_id)}">
  <div class="section-head"><div><div class="eyebrow">{_esc(section_id)}</div><h2>{_esc(title)}</h2><p>{_esc(subtitle)}</p></div></div>
  <div class="panel-grid">{''.join(children)}</div>
</section>"""


def _wide_card(title: str, text: str, payload: Dict[str, Any], extra: str = "") -> str:
    return f"""<button class="wide-card" data-detail='{_detail_json(title, text, payload)}'>
  <span class="card-extra">{extra}</span>
  <strong>{_esc(title)}</strong>
  <span>{_esc(text or "Needs data")}</span>
</button>"""


def _empty(text: str) -> str:
    return f'<div class="empty">{_esc(text)}</div>'


def _nav(data: Dict[str, Any]) -> str:
    if data.get("kind") == "category_portfolio":
        items = [("overview", "01"), ("kpis", "02"), ("tiers", "03"), ("diagnosis", "04"), ("skus", "05"), ("evidence", "06")]
    else:
        items = [("overview", "01"), ("kpis", "02"), ("economics", "03"), ("channels", "04"), ("map", "05"), ("heatmap", "06"), ("treatments", "07"), ("evidence", "08")]
    return "".join(f'<a href="#{sid}">{label}</a>' for sid, label in items)


def _detail_json(title: str, text: str, payload: Dict[str, Any]) -> str:
    return _esc(json.dumps({"title": title, "text": text, "payload": payload}, ensure_ascii=False))


def _esc(value: Any) -> str:
    return escape(str(value), quote=True)


def _css() -> str:
    return r"""
:root{--bg:#f3f3f1;--panel:rgba(255,255,255,.86);--line:#e4e5de;--ink:#111510;--muted:#6d7068;--green:#dff3e8;--amber:#fff1bf;--orange:#ffe1c2;--red:#f8d2cf;--blue:#e2f0f5;--select:#245d7c}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:13px/1.55 "Microsoft YaHei UI","Microsoft YaHei",Arial,sans-serif;letter-spacing:0}.decision-dashboard{display:grid;grid-template-columns:64px minmax(0,1fr) 320px;gap:16px;padding:16px}.rail{position:sticky;top:16px;height:calc(100vh - 32px);background:var(--panel);border:1px solid var(--line);border-radius:10px;display:flex;flex-direction:column;align-items:center;gap:10px;padding:12px 8px}.rail-mark{font-size:10px;color:var(--muted);border-bottom:1px solid var(--line);width:100%;text-align:center;padding-bottom:8px}.rail a{color:var(--muted);text-decoration:none;border:1px solid var(--line);border-radius:7px;padding:6px 8px;background:#fff}.rail a:hover{background:var(--blue);color:var(--select)}.workspace{display:flex;flex-direction:column;gap:14px;min-width:0}.section{scroll-margin-top:16px}.hero,.panel,.detail-panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:0 16px 38px rgba(20,24,18,.06)}.hero{display:flex;justify-content:space-between;gap:16px;padding:16px}.hero h1{font-size:24px;line-height:1.15;margin:2px 0 6px}.hero h1 span{color:var(--muted);font-weight:500}.hero p{margin:0;color:var(--muted);max-width:820px}.hero-actions{display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap;justify-content:flex-end}.pill,.kpi-card,.wide-card,.heat-cell,.graph-node{font:inherit;cursor:pointer}.pill{border:1px solid var(--line);border-radius:999px;background:#fff;padding:6px 10px}.pill.verdict{background:var(--amber)}.pill.muted{color:var(--muted)}.kpi-strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}.kpi-card{border:1px solid var(--line);border-radius:9px;background:#fff;text-align:left;padding:12px;min-height:86px}.kpi-card span,.kpi-card em{display:block;color:var(--muted);font-style:normal}.kpi-card strong{display:block;font-size:22px;margin:4px 0}.panel{padding:16px}.section-head{display:flex;justify-content:space-between;gap:12px}.section-head h2{font-size:18px;margin:0}.section-head p{margin:2px 0 12px;color:var(--muted)}.eyebrow{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}.panel-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px}.wide-card{position:relative;border:1px solid var(--line);border-radius:8px;background:#fff;text-align:left;padding:12px;min-height:104px;overflow:hidden}.wide-card strong{display:block;font-size:14px;margin-bottom:6px}.wide-card span{color:var(--muted)}.card-extra{position:absolute;top:10px;right:10px}.status{border:1px solid var(--line);border-radius:999px;padding:3px 7px;background:#f8f9f6;color:var(--muted);font-size:11px}.graph{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;width:100%}.graph-node{border:1px solid var(--line);border-radius:8px;background:#fff;padding:14px;font-weight:700}.heatmap{display:grid;grid-template-columns:180px repeat(var(--cols),minmax(86px,1fr));gap:1px;background:var(--line);overflow:auto;border:1px solid var(--line);border-radius:8px}.heat-head,.heat-channel,.heat-cell{background:#fff;padding:10px;min-width:0}.heat-head{font-weight:700}.heat-head span{font-size:11px;color:var(--muted);font-weight:400}.heat-channel{font-weight:700}.heat-cell{border:0;font-weight:800;text-align:center}.grade-H{background:var(--green)}.grade-T{background:var(--amber)}.grade-S{background:var(--orange)}.grade-A{background:var(--red)}.grade-N{background:#f2f4f7}.empty{border:1px dashed var(--line);border-radius:8px;padding:18px;color:var(--muted);background:#fff}.detail-panel{position:sticky;top:16px;height:calc(100vh - 32px);padding:16px;overflow:auto}.detail-panel h2{font-size:20px;margin:4px 0 12px}.detail-panel p{color:var(--muted)}.detail-kv{display:grid;grid-template-columns:1fr;gap:7px}.detail-kv div{border:1px solid var(--line);border-radius:7px;padding:8px;background:#fff;overflow-wrap:anywhere}.detail-kv b{display:block;color:var(--muted);font-size:11px;text-transform:uppercase}@media(max-width:980px){.decision-dashboard{grid-template-columns:48px minmax(0,1fr)}.detail-panel{position:static;grid-column:2;height:auto}.hero{flex-direction:column}.heatmap{grid-template-columns:150px repeat(var(--cols),minmax(74px,1fr))}}@media(max-width:640px){.decision-dashboard{display:block;padding:10px}.rail{position:static;height:auto;flex-direction:row;margin-bottom:10px;overflow:auto}.workspace{gap:10px}.detail-panel{margin-top:10px}.panel-grid{grid-template-columns:1fr}}@media print{.rail,.detail-panel{display:none}.decision-dashboard{display:block}.hero,.panel{box-shadow:none;break-inside:avoid}}
"""


def _js() -> str:
    return r"""
function safeText(value){return value === null || value === undefined || value === "" ? "—" : String(value);}
function renderDetail(raw){
  const detail = JSON.parse(raw);
  document.getElementById("detail-title").textContent = detail.title || "Detail";
  const payload = detail.payload || {};
  const rows = Object.entries(payload).slice(0, 14).map(([key,value]) => {
    const rendered = Array.isArray(value) || (value && typeof value === "object") ? JSON.stringify(value) : safeText(value);
    return `<div><b>${key}</b>${rendered}</div>`;
  }).join("");
  document.getElementById("detail-body").innerHTML = `<p>${safeText(detail.text)}</p><div class="detail-kv">${rows}</div>`;
}
document.querySelectorAll("[data-detail]").forEach((el) => {
  el.addEventListener("click", () => renderDetail(el.getAttribute("data-detail")));
});
"""
```

- [ ] **Step 4: Run render tests after CLI task**

This task's render tests depend on CLI support in Task 3. Run them after Task 3.

### Task 3: CLI and Package Integration

**Files:**
- Modify: `.claude/skills/sm-causal-personalization/scripts/generate_report.py`
- Modify: `.claude/skills/sm-causal-personalization/scripts/__init__.py`
- Modify: `tests/test_generate_report.py`

- [ ] **Step 1: Add failing CLI smoke test**

Append to `tests/test_generate_report.py`:

```python
def test_demo_dashboard_format_renders():
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        path = f.name
    proc = subprocess.run(
        [sys.executable, str(REPORT_PATH), "--demo", "--format", "dashboard", "--output", path],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    html = Path(path).read_text(encoding="utf-8")
    assert "decision-dashboard" in html
    assert "DemoProduct" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python tests/test_generate_report.py
```

Expected: fails because `--format` is unknown.

- [ ] **Step 3: Add dashboard routing**

Modify `generate_report.py`:

```python
def _load_dashboard_modules():
    try:
        from dashboard_data import build_dashboard_data
        from dashboard_render import render_dashboard
    except ImportError:
        from .dashboard_data import build_dashboard_data
        from .dashboard_render import render_dashboard
    return build_dashboard_data, render_dashboard
```

Add parser argument:

```python
ap.add_argument("--format", choices=["report", "dashboard"], default="report",
                help="report = existing decision memo HTML; dashboard = interactive decision cockpit")
```

Replace the report-only render line with:

```python
if args.format == "dashboard":
    build_dashboard_data, render_dashboard = _load_dashboard_modules()
    html = render_dashboard(build_dashboard_data(cfg))
else:
    html = generate_html(cfg, depth=depth, echarts_js=echarts_js)
```

- [ ] **Step 4: Export modules**

Add to `__init__.py` docstring and `__all__`:

```python
"dashboard_data",
"dashboard_render",
```

- [ ] **Step 5: Run CLI and render tests**

Run:

```bash
python tests/test_generate_report.py
python tests/test_dashboard_render.py
```

Expected: all tests pass.

### Task 4: Check Runner and CI

**Files:**
- Modify: `scripts/run_all_checks.py`
- Modify: `.github/workflows/validate.yml`

- [ ] **Step 1: Add dashboard tests to local check runner**

Modify `COMMANDS` in `scripts/run_all_checks.py` to include:

```python
[sys.executable, "tests/test_dashboard_data.py"],
[sys.executable, "tests/test_dashboard_render.py"],
```

Place them after `tests/test_generate_report.py`.

- [ ] **Step 2: Add CI dashboard smoke render**

Modify `.github/workflows/validate.yml` after the regular render step:

```yaml
      - name: Render dashboard examples
        run: |
          for cfg in ../examples/*-config.json; do
            echo "::group::dashboard $cfg"
            python generate_report.py --config "$cfg" --format dashboard --output "/tmp/$(basename "$cfg" .json)-dashboard.html"
            echo "::endgroup::"
          done
          python generate_report.py --demo --format dashboard > /tmp/demo-dashboard.html
```

- [ ] **Step 3: Run full lightweight checks**

Run:

```bash
python scripts/run_all_checks.py
```

Expected: dashboard tests pass; causal tests may still skip if scientific deps are unavailable.

### Task 5: End-to-End Verification

**Files:**
- No new source files unless verification exposes a defect.

- [ ] **Step 1: Render sample dashboards to temp files**

Run:

```bash
python .claude/skills/sm-causal-personalization/scripts/generate_report.py --config .claude/skills/sm-causal-personalization/examples/sample-sku-en-config.json --format dashboard --output $env:TEMP\sample-sku-dashboard.html
python .claude/skills/sm-causal-personalization/scripts/generate_report.py --config .claude/skills/sm-causal-personalization/examples/aurora-airpurifier-category-config.json --format dashboard --output $env:TEMP\aurora-dashboard.html
```

Expected: both commands exit 0 and print `Report written to ...`.

- [ ] **Step 2: Inspect generated HTML text for core markers**

Run:

```bash
Select-String -Path $env:TEMP\sample-sku-dashboard.html -Pattern "decision-dashboard|Vela BrewPro B1|Channel Screen|Treatment Gates|Evidence Ledger"
Select-String -Path $env:TEMP\aurora-dashboard.html -Pattern "decision-dashboard|Aurora Air Purifiers|Tier Map|Diagnosis Lenses|SKU Matrix"
```

Expected: all markers found.

- [ ] **Step 3: Confirm existing report output still works**

Run:

```bash
python .claude/skills/sm-causal-personalization/scripts/generate_report.py --demo --output $env:TEMP\demo-report.html
```

Expected: existing report still renders and contains `Decision Memo`.

- [ ] **Step 4: Check git diff**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; changed files match the plan.
