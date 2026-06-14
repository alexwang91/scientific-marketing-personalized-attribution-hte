# 13 · Product-to-Country Pipeline (8 stages, may terminate early)

## Purpose

Turn "user gives a product + market" into a decision memo (ref 12). The
pipeline's defining property: **it is allowed to stop.** A pipeline that
always produces a full media plan regardless of what the data says is a
template, not an analysis — and readers can smell the difference.

```
Stage 0  Local market intelligence  category reception, audience, distribution
                                    landscape, buying journey — ref 00
         ── Outputs: channel list, competitor set, spending anchor ──
Stage 1  Evidence pull        prices, platforms, competitors — all with URL+date
Stage 2  Unit economics       pure math: margin → CAC ceiling → sensitivity
Stage 3  Channel screen       benchmark ranges vs ceiling → viable / not-viable /
                              undetermined
         ── POSSIBLE TERMINUS: if nothing is viable or undetermined-with-a-path,
            emit the short report: "don't spend; here are the levers" ──
Stage 4  Dimension generation D dimensions ONLY for surviving channels (ref 14)
Stage 5  Adversarial review   independent pass; immutable challenges (ref 14)
Stage 6  Test design          prediction / kill line / decision date + power calc
Stage 7  Render               provenance-validated config → generate_report.py
```

The stage order is the argument order: nothing downstream may run before its
upstream gate. **Stage 0 is not optional.** Starting at Stage 1 without a
validated channel landscape is the most common source of systematic error in
the output (wrong retailers, missing telco channel, wrong competitive set).

---

## Input: Required Product Facts

| Field | Example | Notes |
|-------|---------|-------|
| `product_name` | "HUAWEI WATCH FIT 5 Pro" | Full commercial name |
| `market` | "Hungary" | Country or region |
| `price` | 99990 (HUF) | Local retail price — Stage 0 verifies this |
| `margin_rate` | 0.40 | Gross margin (user input; tag as Assumption) |
| `budget` | 12000000 (HUF) | Total pilot budget |
| `key_features` | ["GPS", "10-day battery", "AMOLED"] | 3–6 product USPs |

Stage 0 will determine `local_retailers`, `platforms_available`, and
`competitor_products` — do not pre-fill these from general knowledge.

Optional but accelerates pipeline:
- `existing_audience_data`: first-party signals available
- `compliance_constraints`: product categories with local restrictions

---

## Stage 0 — Market Scoping Kernel (ref 00)

**See `references/00-local-market-intelligence.md` for the full kernel.**

Stage 0 is **not a checklist** — it is a five-move reasoning kernel that derives a
*custom research plan* for the specific cell (product category × country), instead
of running the same fixed questions every time. A fixed list would miss whatever
is idiosyncratic to the next cell (tablets in Romania, insurance in Brazil).

| Move | What it does |
|---|---|
| 1 · Characterize the cell | Position on 7 axes (price/income, category maturity, regulatory load, distribution structure, brand position, cultural specificity, commerce infra); each position *fires* specific research threads |
| 2 · Transfer-assumption ledger | Enumerate every belief being borrowed from another country/product/global ranking; mark transfer risk; **this catches the eMAG-in-Hungary class of error** |
| 3 · Distinctiveness hypotheses | "Where is THIS cell most likely to break my defaults?" → 3–5 priority targets |
| 4 · Derive & rank the plan | Rank questions by decision-impact × assumption-fragility; thread bank is a menu to extend, not fill |
| 5 · Execute & re-orchestrate | Research is a loop; surprising findings on high-impact axes re-open the plan |

**Stage 0 gate:** before Stage 1 begins, the analyst must be able to answer:
1. Which retailer is #1 for this category in this country (with source)?
2. Does a telco/operator (or other intermediary) channel exist for this category?
3. What is the price as a multiple of average monthly income?
4. Which local price-comparison site(s) do consumers use for research?

Any "unknown" is acceptable — but it must be declared `undetermined` in
`market_facts`, never silently assumed.

---

## Stage 1 — Evidence Pull

Collect, each with URL + access date (→ `facts` + `numbers` as **sourced**):

1. Local retail price(s) — actual listings, noting the spread across SKUs/retailers
2. Dominant retail platforms and price-comparison sites for the market
3. Direct competitor products and price positions
4. Structural demand facts (e.g., "ISPs bundle free routers" — the kind of fact
   that caps the addressable market)
5. Local compliance constraints on claims (health, speed, finance)

Also establish market context from public sources or user input:
- Which 3–5 retail platforms command the highest GMV share?
- Which paid channels are locally effective (Google vs Yandex vs Naver, etc.)?
- Are there local compliance constraints on health, finance, or performance claims?
- What is the local currency, and are all monetary inputs in local denomination?

Tag each fact: `Evidence` if sourced, `Assumption` if user-provided.

Anything not obtainable goes into the registry as **missing** with
`needed_from` + `cost_to_get` — not as a guess. User-supplied inputs (margin,
budget envelope) register as **assumed** with basis.

---

## Stage 2 — Unit Economics

Pure derivation, zero new assumptions beyond declared ones:

```
unit_margin = price × margin_rate
cac_ceiling = unit_margin × cac_share_of_margin   (share itself is a declared assumption)
```

Then the **sensitivity table**: for each assumption, what change flips the
conclusion, ranked. This ranking becomes (a) the thesis's overturn conditions,
(b) the sort order of the Missing ledger, (c) the verification order in
stage 6. Low-ticket products live or die here: a 60 RON unit margin is itself
the report's central finding.

---

## Stage 3 — Channel Screen (the gate that may end the report)

For each candidate channel, attempt `CAC = cost-per-touch ÷ conversion-per-touch`
with whatever provenance is available.

**Benchmark asymmetry**: benchmarks may prove **not-viable**, never **viable**.
A benchmark range that clears the ceiling gives no confidence that actual CAC
will clear it — it only establishes that the channel is not yet ruled out.
A benchmark range that fails the ceiling even at its optimistic end rules the
channel out.

Map each available channel to:
- **Proximity to purchase** (1 = closest, 5 = furthest)
- **Primary task** (capture / build / convert / suppress)
- **Local proxy availability** (High / Medium / Low)
- **Incrementality risk** (sure-thing / ad-fatigue / deal-seeker)

Sort by proximity × proxy quality. Channels with Low proxy and far proximity enter
the heatmap as S or N only.

**Channel proximity reference**:

```
Retail Media       → proximity 1, capture, High proxy
Search brand/cat   → proximity 1–2, capture, High proxy
Shopping/PMax      → proximity 2, convert, High proxy
Retargeting        → proximity 2, top-up, High (needs 1P data)
YouTube Review     → proximity 3, build proof, Medium proxy
KOL / Creator      → proximity 3–4, build proof, Medium proxy
Social Prospecting → proximity 4–5, expand, Medium–Low proxy
```

| Verdict | Meaning | Downstream |
|---------|---------|-----------|
| viable | local data shows CAC < ceiling | proceeds to stage 4 |
| undetermined | interval spans ceiling, or inputs missing | proceeds ONLY as a data-acquisition action |
| not-viable | best case still fails the ceiling | one line in rejected options |
| role-only | non-acquisition role (objection-answering content, proof asset) | small envelope, no CAC claim |

**Termination rule**: if no channel is viable and no undetermined channel has a
cheap data path, stop. Emit the short report (ref 12): verdict no-go, the math,
the levers, the Missing ledger. This is a complete, successful deliverable.

---

## Stage 4 — Dimension Generation (survivors only)

Run ref 14's generation protocol per surviving channel. Expect few dimensions —
quality over coverage. The failure mode is 32 dimensions for an unscreened
channel list: maximal surface, zero verified depth.

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

**Entry threshold**: dimension must pass ≥ 3 of the 5 checks in ref 14.

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

## Stage 5 — Adversarial Review

Independent pass per ref 14. Input: the data and the screen — **not** the
recommendations (the reviewer must not anchor on what the analysis wants).
Output: immutable challenges with status; `open-blocking` challenges stamp
dependent actions in the report.

Standard challenge library: sure-thing, deal-seeker, correlation≠mechanism,
proxy-reality, fatigue/sleeping-dog, compliance, market-ceiling.

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

## Stage 6 — Test Design

Every surviving action gets the three-piece set:

```
Prediction:    falsifiable, with a number and a direction
Test:          duration / spend / cell structure; power_analysis.py for sample size
Kill line:     the result that declares the hypothesis dead (numeric, dated)
Decision date: when this line must become Sourced or be declared dead
```

Plus a decision calendar: the single date when the go/no-go re-evaluation
happens, named in the memo's checkpoint decisions.

---

## Stage 7 — Render

Assemble the config (schema: `examples/ax3-romania-config.json`), then:

```bash
python scripts/generate_report.py --config config.json --validate-only   # must pass
python scripts/generate_report.py --config config.json --output report.html
```

Minimum config from this pipeline:

```python
config = {
    "product": product_name,
    "market": market,
    "budget": budget_display,
    "price": price,
    "margin_rate": margin_rate,
    "market_facts": [...],    # Stage 0 output — scoping kernel: verified retailer
                              #   rank, telco channel, price/income ratio, VAT,
                              #   category penetration (each sourced or undetermined)
    "channels": [...],        # Stage 0 seeds the candidate list; Stage 3 screens it
    "numbers": {              # Stage 0 sources competitor prices into the registry,
        # competitor_X_price: {... "provenance": "sourced", ...}   #  Stage 2 uses
    },
    "product_facts": [...],   # Stage 1 output
    "dimensions": [...],      # Stage 4 output (Stage 0 audience map seeds candidates)
    "heatmap": {...},          # Stage 4 output
    "treatments": [...],      # Stage 4 output
    "execution_gates": [...], # Stage 5 output
    "power_analysis": {       # Stage 5 inputs for script bridge
        "baseline_cvr": 0.02,
        "mde_abs": 0.004,
        "eligible_per_day": 10000,
    },
    # ... budget, plays, measurement, suppression, sources, checklist
}
```

**Stage 0 → config mapping** (so the kernel's output is not lost):

| Kernel output | Config destination |
|---|---|
| Verified retailer rank, telco channel, price-comparison sites | `market_facts[]` + candidate `channels[]` |
| Competitor prices (sourced) | `numbers` registry → feeds Stage 2 tier analysis |
| Price ÷ income ratio, VAT | `market_facts[]` + `decision_memo` framing |
| Audience segments | candidate `dimensions[]` (Stage 4 screens them) |
| Regulatory / claim limits | `suppression_rules[]` + suppression `dimensions[]` |
| Unanswered gate questions | `market_facts[]` tagged `undetermined` (honest blanks) |

Build failure = a number broke the provenance contract. Fix the analysis,
not the validator.

---

## Failure Modes

| Failure | Smell | Fix |
|---------|-------|-----|
| Stage 0 skipped | Channel map built from global brand knowledge; "eMAG is biggest" with no local source; no telco channel; no price/income ratio | Run the scoping kernel (ref 00); fill the transfer-assumption ledger before any lookup |
| Assumption transferred silently | A retailer rank / competitor set / channel mix imported from another country or the brand's home market | Move 2 ledger: mark cross-border beliefs HIGH risk, verify before shipping |
| Template completeness | Full 17-section report for a product whose math died in Stage 2/3 | Use short-report mode: Memo + The Math + Missing ledger (ref 12) |
| Screen skipped | Dimensions/heatmaps for channels never tested against the ceiling | Re-run stage 3; delete unearned detail |
| Costume numbers | Play tables with CAC/ROI ranges and no formulas | Ref 16; registry or deletion |
| Reviewer anchoring | Challenges that read like endorsements | Stage 5 sees data, not recommendations |
| No terminus fear | Analyst pads the report to justify the effort spent | The short report IS the deliverable; say so |
| All dimensions enter as H | Skipped mechanism check | Re-run Stage 4 with reviewer (ref 14) |
| Budget allocated before gates | Skipped Stage 5 | Gates are non-negotiable; label pre-gate numbers as Hypothesis |
| KOL ROI treated as Evidence | No holdout or UTM | Re-tag as Assumption or Needs test |
| Heatmap has > 20 H cells | No prioritization | Rank H cells by (proxy quality × mechanism clarity); keep top 8–10 |
| Price / CAC missing tags | Draft from LLM | Every number with currency symbol must be tagged before delivery |
