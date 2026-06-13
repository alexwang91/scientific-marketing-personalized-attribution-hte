# 00 · Market Scoping Kernel (dynamic Stage 0)

## Why this is a kernel, not a checklist

A fixed checklist is itself a template. "Always answer these six questions" fails
the next time the cell changes — tablets in Romania, insurance in Brazil, EV
chargers in Indonesia — because each cell has its *own* idiosyncrasies that a
fixed list cannot anticipate. A longer list does not fix this; it just moves the
blind spot.

The real disease is **silent assumption transfer**: importing a belief that is
true in one cell (eMAG is #1 in Romania) into another cell (Hungary) without
flagging it as transferred. The cure is a reasoning procedure that (a) derives
the research plan from the specific cell, and (b) actively hunts the assumptions
it is borrowing from elsewhere.

> **A cell = (product category × country).** The kernel's job: turn a cell into a
> *custom, prioritized research plan* — not a filled-in form.

The kernel runs five moves. Moves 1–3 are pure thinking (no research yet); they
produce the plan. Moves 4–5 execute and adapt it.

---

## Move 1 — Characterize the cell (7 axes)

Position the cell on seven axes. Each position *fires* specific research threads.
You are answering "what KIND of problem is this?" — which determines what matters
before you look up a single fact.

| Axis | Positions | What the position fires |
|------|-----------|-------------------------|
| **1. Price ÷ local median monthly income** | impulse (<0.1×) / considered (0.1–0.5×) / major (>0.5×) | Major → financing, installment, telco bundling, return policy, trust signals, long funnel. Impulse → point-of-sale, broad reach. **Compute this ratio first — it reshapes everything downstream.** |
| **2. Category maturity in this market** | nascent / growing / saturated | Nascent → educate demand, map substitute behaviors. Growing → distribution land-grab. Saturated → displacement wedge, switching costs, competitor weakness |
| **3. Regulatory / claims load** | light / heavy (health, finance, kids, biometric data) | Heavy → claim rules, restricted features, disclosure law, data residency → these become **suppression dimensions**, not targeting dimensions |
| **4. Distribution structure** | online-concentrated / online-fragmented / offline-significant / **intermediary-present** | Intermediary (telco, bancassurance, dealer, pharmacy, carrier) → research whether it exists for THIS category. **Most-missed channel class.** Offline-significant → estimate offline share, never assume 0% |
| **5. Brand local position vs global** | local leader / challenger / unknown-despite-global-strength | Unknown-locally → trust gap, awareness build. Leader → loyalty, ecosystem lock-in. Challenger → identify exactly whose share you take |
| **6. Cultural specificity of the job-to-be-done** | universal / locally idiosyncratic | Idiosyncratic → local use cases, seasonality, gifting norms, status meaning differ from the analyst's home intuition |
| **7. Country commerce/digital infrastructure** | mature card+ecom / cash-on-delivery / mobile-money / low-card | Non-card → COD changes funnel, attribution, and return economics; fires payment + fulfillment threads a card-market analyst never thinks of |

The set of fired threads — not a fixed list — is the seed of the research plan.

---

## Move 2 — Transfer-assumption ledger (the core move)

This is the move that catches the eMAG-class error. **Before researching**, write
down everything you are tempted to assume, where each belief comes from, and its
transfer risk.

| Belief I'm tempted to hold | Where it comes from | Transfer risk | Action |
|---|---|---|---|
| "eMAG is the biggest e-commerce" | True in Romania | **HIGH** (retailer rank is country-specific) | Verify locally |
| "Telcos don't sell wearables" | My home market | **HIGH** | Verify — telco channel is common in EU |
| "Garmin is niche" | Global smartwatch share | **HIGH** (Garmin leads *sports* segment everywhere) | Segment the competitive set |
| "Margin ~40%" | User input | MEDIUM (declared assumption) | Tag `assumed`, flag in sensitivity |
| "GPS accuracy is the killer feature" | Product brief | MEDIUM | Test against local job-to-be-done |

**Default rule:** any belief sourced from *another country, the brand's home
market, a global ranking, or a different product* is **HIGH transfer risk** until
verified. Retailer rankings, channel mix, payment habits, category attitudes,
competitor sets, and price-tier perception almost never transfer across borders
intact. The ledger makes the borrowing visible so it can be checked instead of
shipped.

---

## Move 3 — Distinctiveness hypotheses

Ask one question: **where is THIS cell most likely to break my default model?**
Generate 3–5 hypotheses. These are the highest-value research targets, because
they sit where being wrong is both most likely and most costly.

Examples (smartwatch × Hungary):
- "There may be a dominant local electronics specialist that outranks the general
  marketplace I'd default to."
- "Telco device bundling may be a material channel I'd otherwise ignore."
- "27% VAT (EU-high) may push the real price tier above my assumption."

Each hypothesis becomes a priority thread in Move 4.

---

## Move 4 — Derive and rank the research plan

Assemble questions from the fired threads (Move 1) + the HIGH-risk ledger items
(Move 2) + the distinctiveness hypotheses (Move 3). Then **rank by
decision-impact × assumption-fragility**:

- **decision-impact**: does the answer change channel choice, CAC ceiling, budget,
  or message? (Low-impact facts can stay `undetermined`.)
- **assumption-fragility**: how likely is my default belief to be wrong here?

Research the top of the ranked list first. The thread bank below is your starting
menu — **extend it for the cell, don't just fill it in.**

---

## Move 5 — Execute and re-orchestrate

Research is a loop, not a single pass. Every finding does one of three things:

- **confirms** a belief → close the thread
- **surprises** (new fact on a high-impact axis) → spawn new threads, re-rank
- **contradicts** an assumption → revisit every downstream item that depended on it

A surprising finding on a high-impact axis (e.g., "telco channel is 40% of
category sales") re-opens the plan. Do not push findings into the shape the
original plan expected.

---

## Default thread bank (a menu the kernel draws from — never the whole list)

These are common high-yield threads. The kernel surfaces a *subset plus
cell-specific additions*; it does not run all of them every time.

**A · Category reception** — penetration rate vs comparable markets; local
job-to-be-done; adoption blockers at this price point.

**B · Consumer audience map** — buyer profiles (age/gender/urban/income); **price
÷ average monthly salary** (mandatory anchor, Axis 1); reachable-via-paid vs
brand/community segments; purchase triggers.

**C · Product tier analysis** — local competitive set pulled from the local price
comparison site (±30% band); what sits directly above/below; competitive white
space; functional substitutes. *Competitors not sold locally are not competitors.*

**D · Distribution & channel landscape** — verified #1 retailer for this category;
country-specific specialist retailers; **telco/operator channel** (Axis 4);
local price comparison sites; physical-retail share; brand-direct exclusives.

**E · Consumer buying journey** — discovery channel; research-cycle length (a
>0.5×-salary product has a long one); decision triggers; review sources that
carry weight locally; return behavior.

**F · Regulatory & compliance** — VAT and its effect on price tier; import duties;
health-claim rules for sensor features; comparative-ad and influencer-disclosure
law; biometric-data requirements beyond GDPR.

---

## Stage 0 gate (must be answerable before Stage 1)

1. Which retailer is #1 for this category in this country (with source)?
2. Does a telco/operator (or other intermediary) channel exist for this category?
3. What is the price as a multiple of average monthly income?
4. Which local price-comparison site(s) do consumers use for research?

Any "unknown" is acceptable — but it must be declared `undetermined` in
`market_facts`, never silently assumed.

---

## Worked contrast: same kernel, two cells, two plans

The proof that this is dynamic — the kernel produces *different* plans:

| | **Smartwatch × Hungary** | **Tablet × Romania** |
|---|---|---|
| Axis 1 (price/income) | ~100k HUF vs ~400k HUF net → ~0.25× considered | ~1,500 RON vs ~4,500 RON net → ~0.33× considered |
| Axis 4 (distribution) | Verify Alza vs MediaMarkt vs eMAG; **telco bundling likely material** | **eMAG genuinely dominant here** (this is its home market); dealer/retail chains |
| Axis 7 (commerce infra) | Mature card+ecom → standard funnel | **COD historically significant** → fires payment/fulfillment + return-economics threads |
| Regulatory | 27% VAT (EU-high) | 19% VAT (lower) → different price-tier math |
| Top distinctiveness hypothesis | "A local electronics specialist outranks the general marketplace" | "COD changes attribution and return rate" |

Same seven axes, same ledger discipline — **the fired threads differ**, so the
research plans differ. The eMAG belief is correct for Romania and wrong for
Hungary; the transfer ledger (Move 2) is exactly what distinguishes the two.

---

## Integration with Pipeline (ref 13)

Stage 0 runs before Stage 1 (Evidence Pull). It is not optional.

- **Structural blocker found** (product not sold locally; only viable channel needs
  brand-level budget) → pipeline may terminate before Stage 1, with a short memo.
- **User provides partial info** ("here are our channels") → Stage 0 validates and
  fills gaps; it verifies, it does not skip.

Stage 0 output (the ranked plan + findings) is the input to Stage 1, which adds
specific sourced prices and URLs on top of the validated structural framework.
