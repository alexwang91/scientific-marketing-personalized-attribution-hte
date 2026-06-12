# 13 · Product-to-Country Pipeline

## Purpose

Transform user-supplied product inputs into a complete campaign config:
product facts → country/channel map → audience proxy → treatment cards →
experiment gate → HTML report.

---

## Input: Required Product Facts

| Field | Example | Notes |
|-------|---------|-------|
| `product_name` | "HUAWEI WATCH FIT 5 Pro" | Full commercial name |
| `market` | "Hungary" | Country or region |
| `price` | 99990 (HUF) | Local retail price |
| `margin_rate` | 0.40 | Gross margin (user input; tag as Assumption) |
| `budget` | 12000000 (HUF) | Total pilot budget |
| `key_features` | ["GPS", "10-day battery", "AMOLED"] | 3–6 product USPs |
| `local_retailers` | ["Alza", "eMAG", "MediaMarkt"] | Top local e-commerce platforms |
| `platforms_available` | ["Google", "Meta", "TikTok", "YouTube"] | Active ad platforms |

Optional but accelerates pipeline:
- `competitor_products`: list of direct alternatives
- `existing_audience_data`: first-party signals available
- `compliance_constraints`: product categories with local restrictions

---

## Step 1 — Country / Market Context

**Output**: local e-commerce landscape, platform reach, regulatory notes.

Questions to answer from public sources or user input:
1. Which 3–5 retail platforms command the highest GMV share?
2. Which paid channels are locally effective (Google vs Yandex vs Naver, etc.)?
3. Are there local compliance constraints on health, finance, or performance claims?
4. What is the local currency, and are all monetary inputs in local denomination?

Tag each fact: `Evidence` if sourced, `Assumption` if user-provided.

---

## Step 2 — Channel Map

Map each available channel to:
- **Proximity to purchase** (1 = closest, 5 = furthest)
- **Primary task** (capture / build / convert / suppress)
- **Local proxy availability** (High / Medium / Low)
- **Incrementality risk** (sure-thing / ad-fatigue / deal-seeker)

Sort by proximity × proxy quality. Channels with Low proxy and far proximity enter
the heatmap as S or N only.

```
Retail Media       → proximity 1, capture, High proxy
Search brand/cat   → proximity 1–2, capture, High proxy
Shopping/PMax      → proximity 2, convert, High proxy
Retargeting        → proximity 2, top-up, High (needs 1P data)
YouTube Review     → proximity 3, build proof, Medium proxy
KOL / Creator      → proximity 3–4, build proof, Medium proxy
Social Prospecting → proximity 4–5, expand, Medium–Low proxy
```

---

## Step 3 — Audience Proxy (D Dimension Generation)

Generate candidate D dimensions by crossing:

```
Product mechanism  ×  Local purchase path  ×  Platform proxy  ×  Measurability
```

**Generation protocol**:
1. List every product feature that could change a person's response to the action
2. For each feature, identify who would respond differently (mechanism, not correlation)
3. Check if that person type is reachable via a platform proxy in this market
4. Check if the dimension is measurable (A/B, holdout, UTM, platform split)
5. Flag any dimension touching sensitive attributes (health, body image, age, religion)
   → send to Causal Activation Reviewer (ref 14) before including

**Entry threshold**: dimension must pass ≥ 3 of the 5 checks in ref 12 heatmap rules.

**Standard D dimension candidates** (always evaluate, not always include):
- Brand/OS affinity (D: brand loyal)
- Smartwatch in-market (D: category intent)
- Key sport segment (D: running / cycling / gym / outdoor)
- Health / sleep tracking (D: health habit)
- Long battery pain (D: battery pain vs competitor)
- Price compare (D: comparison shopper)
- Competitor alternative (D: switching consideration)
- Cart abandon (D: near-purchase)
- Tech review reader (D: proof-seeker)
- Gift buyer (D: gift intent, seasonal)
- Ad fatigue (D: suppression, not prospecting)
- Deal-only buyer (D: suppression, negative margin risk)

---

## Step 4 — Treatment Cards

For each H-score cell in the heatmap, generate a Treatment Card with:

```
T{id}
action:        plain-language description
audience:      D dimension + proxy
baseline:      what happens without the action (holdout / organic / no campaign)
cost_formula:  CPC + X / CPM + Y / creator fee + usage rights
mechanism:     one sentence — why this changes incremental purchase probability
guardrail:     the main way this wastes budget (sure-thing / fatigue / deal-seeker)
measurement:   how to estimate incremental effect
```

Number of Treatment Cards = number of H-score cells. If > 8, consolidate by grouping
channels with the same mechanism.

---

## Step 5 — Experiment Gate

Before any budget is committed, check:

| Gate | Input needed | Script |
|------|-------------|--------|
| Sample size | baseline CVR, MDE, eligible users/day | `power_analysis.py` |
| Propensity log ready | eligible treatment set, assignment probability | manual |
| Attribution method | holdout flag, cost, outcome | manual |
| OPE support | propensity log p(t\|x) | `ope_estimators.py` |
| AUUC > 0 | uplift model predictions | `qini_auuc.py` |

Gates are binary: pass / not-ready. A "not-ready" gate does not block trial spend
but blocks scale-up.

---

## Step 6 — Generate HTML Report

Pass the assembled config to `generate_report.py`:

```python
# Minimum config from this pipeline:
config = {
    "product": product_name,
    "market": market,
    "budget": budget_display,
    "price": price,
    "margin_rate": margin_rate,
    "product_facts": [...],   # Step 1 output
    "channels": [...],        # Step 2 output
    "dimensions": [...],      # Step 3 output
    "heatmap": {...},          # Step 3 output
    "treatments": [...],      # Step 4 output
    "execution_gates": [...], # Step 5 output
    "power_analysis": {       # Step 5 inputs for script bridge
        "baseline_cvr": 0.02,
        "mde_abs": 0.004,
        "eligible_per_day": 10000,
    },
    # ... budget, plays, measurement, suppression, sources, checklist
}
```

Then:
```bash
python scripts/generate_report.py --config config.json --output report.html
```

---

## Common Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| All dimensions enter as H | Skipped mechanism check | Re-run Step 3 with reviewer (ref 14) |
| Budget allocated before gates | Skipped Step 5 | Gates are non-negotiable; label pre-gate numbers as Hypothesis |
| KOL ROI treated as Evidence | No holdout or UTM | Re-tag as Assumption or Needs test |
| Heatmap has > 20 H cells | No prioritization | Rank H cells by (proxy quality × mechanism clarity); keep top 8–10 |
| Price / CAC missing tags | Draft from LLM | Every number with currency symbol must be tagged before delivery |
