# 12 · HTML Report Output Adapter

## When to use

Trigger when the user asks for a deliverable report, campaign brief, trial plan, or
formatted output after working through the pipeline. This reference specifies the
canonical section structure, evidence labeling rules, and how to pipe script outputs
into the report.

---

## Section Map (canonical 15 sections)

| # | Section | Required | Script input |
|---|---------|----------|--------------|
| 1 | Core decision + KPI strip | Yes | — |
| 2 | Evidence tag legend | Yes (always static) | — |
| 3 | Product & market facts | Yes | — |
| 4 | Assumption register | Yes | — |
| 5 | Local channel map | Yes | — |
| 6 | D dimension table + Causal Activation Reviewer | Yes | — |
| 7 | Semantic heatmap (channel × dimension) | Yes | — |
| 8 | H-main breakdown | Yes | — |
| 9 | Execution gates + Treatment Cards | Yes | `power_analysis.py` → sample size gate |
| 10 | Budget allocation | Yes | — |
| 11 | Priority plays + ROI scenarios | Yes | `qini_auuc.py` → AUUC gate (if model data available) |
| 12 | KOL / Creator sourcing | Conditional | — |
| 13 | Measurement plan | Yes | `power_analysis.py` → duration |
| 14 | Suppression & risk rules | Yes | `ope_estimators.py` → support check |
| 15 | Sources + Verification checklist | Yes | — |

---

## Evidence Tag Semantics

Every claim in the report must carry exactly one tag. No untagged ROI, CAC, or KOL
price is allowed.

| Tag | Class | Meaning |
|-----|-------|---------|
| `Evidence` | `.evidence` | Sourced fact, stable method, or validated result |
| `Assumption` | `.assumption` | Scenario input or estimate provided by user |
| `Hypothesis` | `.hypothesis` | Semantic prior or unvalidated HTE inference |
| `Needs test` | `.needs-test` | A judgment that will change budget, channel, or KOL decisions |

**Hard rule**: any number with a currency symbol or "%" that affects budget, CAC, or
ROI must be tagged. No exceptions.

---

## Heatmap Score Semantics

| Score | CSS class | Meaning |
|-------|-----------|---------|
| H | `.hm-high` | Primary investment: strong mechanism, deployable proxy, testable |
| T | `.hm-test` | Test slot: weaker signal or proxy; small budget to learn |
| S | `.hm-small` | Small exploratory test only |
| N | `.hm-none` | Not a focus this round |
| A | `.hm-avoid` | Actively suppress: ad fatigue, sure-thing, compliance risk |

A dimension enters the heatmap only if it satisfies ≥ 3 of:
1. Observable before deployment
2. Reachable via a platform proxy
3. Mechanistically linked to a product feature or barrier
4. Measurable via A/B, holdout, UTM, or platform report
5. Changes a creative, bid, frequency, or suppression decision

---

## Script Bridge: How to Embed Script Outputs

### Section 9 — Sample Size Gate (power_analysis.py)

```python
from power_analysis import n_per_arm_ate, n_per_cell_hte, experiment_duration_days

n_ab  = n_per_arm_ate(baseline_rate=cfg["baseline_cvr"], mde_abs=cfg["mde_abs"])
n_hte = n_per_cell_hte(
    baseline_rate_a=cfg["baseline_cvr"], baseline_rate_b=cfg["baseline_cvr"],
    uplift_a=cfg["mde_abs"] * 2, uplift_b=cfg["mde_abs"]
)
days = experiment_duration_days(4 * n_hte, cfg["eligible_per_day"])
```

Embed in execution gate row "Sample size":

```html
<span class="tag evidence">Script</span>
ATE: {n_ab:,}/arm · HTE: {n_hte:,}/cell · ~{days}d at {eligible_per_day:,}/day
```

### Section 11 — AUUC Gate (qini_auuc.py)

If uplift model scores are available:

```python
from qini_auuc import auuc_bootstrap_ci
import numpy as np

auuc, lo, hi = auuc_bootstrap_ci(y_true, w, tau_hat)
gate_passes = lo > 0
```

Embed in priority plays table:

```html
<span class="tag evidence">Script</span>
AUUC = {auuc:.1f}  95% CI [{lo:.1f}, {hi:.1f}]
→ {"Gate PASSED" if gate_passes else "Gate FAILED — do not scale"}
```

### Section 14 — OPE Support Check (ope_estimators.py)

Before any policy evaluation:

```python
from ope_estimators import support_check
result = support_check(t_logged, p_logged, pi_new)
# embed result["verdict"] in the gate row
```

---

## Programmatic Generation

Use `scripts/generate_report.py` for config-driven HTML output:

```bash
# Built-in demo
python scripts/generate_report.py --demo > campaign_report.html

# From config file
python scripts/generate_report.py --config my_config.json --output report.html
```

Config schema: see `DEMO_CONFIG` in `generate_report.py` and ref 13 (product pipeline)
for how config is built from product inputs.

---

## Writing Rules for Report Text

All report text follows ref 15. Key obligations:

1. **Language**: match user's language; technical terms stay English
2. **No untagged numbers**: every ROI / CAC / KOL price / budget figure carries a tag
3. **Decision-first**: lead with the recommendation, evidence second
4. **No filler**: strip "it is worth noting that", "in conclusion", "as mentioned above"
5. **Callout usage**: use `.callout` only for the single most important decision or
   reviewer finding per section; do not put general summaries in callouts

---

## Acceptance Checklist

- [ ] Every section present and non-empty
- [ ] All monetary figures tagged Evidence / Assumption / Hypothesis / Needs test
- [ ] Heatmap legend rendered with correct color swatches
- [ ] Causal Activation Reviewer table present in section 6/7
- [ ] At least one script output embedded (power_analysis.py sample size minimum)
- [ ] Treatment Cards cover all H-main channel/dimension pairs
- [ ] Measurement plan states explicit scale-up and pause rules
- [ ] Verification checklist covers propensity log, compliance claims, holdout gate
