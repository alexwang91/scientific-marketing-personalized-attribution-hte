# 00 · Local Market Intelligence (Stage 0, mandatory pre-pipeline)

## Purpose

This is the step that was missing. Without it, Stage 1 (Evidence Pull, ref 13)
becomes a price-lookup exercise that inherits whatever the analyst *assumes* about
the market — and those assumptions are the ones most likely to be wrong.

> **The systematic failure this step prevents:**  
> Treating global brand recognition as local market share data.  
> (eMAG is the largest e-commerce in Romania, not Hungary. Alza dominates
> Czech and Slovak electronics online; it is major in Hungary. Telco stores
> are a significant device sales channel in almost every European market.
> A pipeline built on wrong channel assumptions is wrong from Stage 1 onward.)

Stage 0 must run before Stage 1. Its output populates the structural priors
that every downstream stage inherits. Six required sections; each has a
"must research, not assume" rule.

---

## The Six Sections

### A · Category Reception

What is the cultural attitude toward this *category* in this country?

Research questions:
- Is this category a status symbol, a practical utility, a niche hobbyist product,
  or an emerging mainstream product?
- What does the local consumer believe the product *does for them* (functional,
  emotional, social job)?
- What is the category penetration rate vs comparable markets? Growing / flat /
  declining?
- Is there a dominant local use case (e.g., GPS running is bigger in Scandinavia;
  health tracking resonates more in markets with high lifestyle disease awareness)?
- Are there cultural or economic blockers to adoption at this product's price point?

**Must research, not assume:** penetration rate and the dominant local job-to-be-done.
Global use case rankings do not transfer reliably to specific markets.

---

### B · Consumer Audience Map (rough)

Who actually buys this category in this country, and can they afford this product?

Research questions:
- Primary buyer profiles: age, gender skew, urban/rural split, income band.
- What is the country's average monthly salary and GDP per capita?
  Express the product price as a multiple of average monthly salary.
  *If the product costs more than 1× average monthly salary, it is a major purchase
  for the median consumer — this changes everything about messaging, channel, and
  conversion funnel length.*
- Which segments are reachable via paid channels (interest targeting, keyword intent)
  vs requiring brand or community channels?
- What psychographic tags describe the buyer (sport enthusiast, tech early adopter,
  health-conscious, gift buyer, Huawei ecosystem user, upgrade seeker)?
- What triggers a purchase decision: seasonal, event-driven, replacement cycle,
  new feature awareness?

**Must research, not assume:** average salary in the market (public data, easy to find).
Express price as ×salary ratio. Never analyze a >1× salary product without this anchor.

---

### C · Product Tier Analysis

Where does *this specific product* (not the brand) sit in the local market?

Research questions:
- Pull the actual competitive set from the local market's largest price comparison
  site (identified in Section D). Include all products in ±30% price band.
- What is directly above this product? Directly below?
- Is the product priced competitively for its feature set vs local alternatives?
  (A product that is "mid-range globally" may be "premium" in a lower-income market.)
- Is there a competitive white space this product can own, or is it fighting on a
  dimension where a stronger local competitor already wins?
- What are the functional substitutes (different category, same job)?

**Must research, not assume:** local competitor prices. Never use "the main competitors
are X, Y, Z" from product briefings without checking local prices and availability.
Competitors that are not sold locally are not competitors.

---

### D · Distribution & Channel Landscape

**This is the most commonly wrong section.** Global brand name recognition is not
local market share. Verify every channel claim with a source.

Research questions (for each country × category):

**Online retail:**
- Which platforms actually dominate for *this category* in this country?
  Do not default to Amazon (not in all markets), JD (not outside China), or
  the country's largest general e-commerce.
- Is there a country-specific specialist electronics retailer that outranks
  general e-commerce for this category? (Example: Alza for electronics in
  Czech Republic, Slovakia, Hungary, Austria.)
- What is the platform's seller model? (First-party / marketplace / both)
- Does the brand have a direct online store? What promotions/exclusives does
  it run there?

**Price comparison sites (research-stage influence):**
- Which price comparison sites do consumers use for this category in this country?
  These are country-specific, high-influence research touchpoints.
  (Examples: idealo.de for Germany; arukereso.hu + árgép.hu for Hungary;
  Heureka for Czech/Slovak; kelkoo.fr for France.)
- Are they crawled automatically or do retailers pay for inclusion?
- Do consumers use them to discover products or only to price-check a known product?

**Physical retail:**
- What retail chains carry this category? What is their consumer profile
  (price-sensitive, premium, broad)?
- Do they carry the full product range or only select SKUs?
- What is the estimated offline vs online split for this category?
  (In most CEE markets, electronics skew online but major purchase items
  like laptops and expensive wearables still see significant offline conversion.)

**Telco / operator channel:**
- In virtually every European and many Asian markets, telecom operators
  (carriers) have significant device sales share.
- Do local operators (telcos) sell wearables? As standalone or bundled?
- What is the estimated operator channel share for wearables/smartphones in
  this country?
- Operators often run exclusive promotions and have captive audiences at point
  of plan renewal — this affects both channel strategy and CAC benchmarks.

**Brand direct:**
- Does the brand operate a local direct e-commerce store?
- What exclusives, bundles, or promotions run only on brand direct?
- Is brand direct growing or shrinking share vs retail?

**Must research, not assume:**
- Which specific platform is #1 for this category in this country.
- Whether the telco channel is material (it usually is, and is usually missed).
- Local price comparison sites — these are invisible to analysts outside the market.

---

### E · Consumer Buying Journey

How do consumers discover, research, and decide in this category in this country?

Research questions:
- Discovery: organic search / social / comparison site / in-store / influencer /
  carrier recommendation? Which channel's influence is strongest?
- Research depth: do consumers spend 1 day or 3 weeks between awareness and
  purchase? (High-price products in price-sensitive markets: long research cycles.)
- Decision triggers: price drop, feature review, gifting occasion, product launch?
- Return / refund behavior: relevant for wearables with short trial periods.
- Review sources: which review sites, YouTube channels, or social communities
  carry weight for this category in this country?

**Must research, not assume:** length of the consideration cycle for this price tier.
A product that costs >1× monthly salary has a long consideration cycle; campaign
timing and retargeting windows must reflect this.

---

### F · Regulatory & Compliance Notes

Research questions:
- VAT rate and how it affects retail price (especially in high-VAT markets like
  Hungary at 27%).
- Import duties or trade restrictions on products in this category.
- Health claim regulations: for any product with health or medical sensor features
  (ECG, SpO2, women's health), what claims are restricted?
- Advertising law: comparative advertising rules, influencer disclosure requirements,
  health claim standards (differs materially across EU member states in practice).
- Data privacy: any local requirements beyond GDPR for health/biometric data
  collection through wearable devices?

**Must research, not assume:** VAT rate (easily sourced) and health claim rules
for any product with health sensor features.

---

## Output Format

Stage 0 output populates these config sections before Stage 1 runs:

| Stage 0 Section | Config destination |
|---|---|
| A · Category Reception | `market_facts[]` + `decision_memo.weakest_point` priors |
| B · Consumer Audience Map | `product_facts[]`, `dimensions[]` (initial candidates) |
| C · Product Tier Analysis | `market_facts[]`, `numbers` (competitor prices, sourced) |
| D · Distribution Landscape | `channels[]` (channel list), `market_facts[]` |
| E · Consumer Buying Journey | `dimensions[]` (D13 回访 etc.), `measurement_plan` |
| F · Regulatory / Compliance | `suppression_rules[]`, `dimensions[]` (suppression dims) |

**Sourcing standard:** every channel name, retailer rank, competitor price, and
market share figure must carry a source or be explicitly tagged `assumption`.
"I believe Alza is larger" → tag as assumption and flag for Stage 1 verification.

---

## Common Failure Modes (with examples)

| Failure | Hungary × Smartwatch example | Rule |
|---|---|---|
| Wrong #1 retailer | "eMAG is the largest" (eMAG is #1 in Romania; Alza is dominant for electronics in Hungary) | Always check local sources; do not transfer platform rankings across borders |
| Telco channel invisible | No mention of Yettel / Telekom Hungary for device sales | Add telco channel to every device/wearable analysis by default; find local operator names |
| Missing price comparison sites | Used argep.hu but not arukereso.hu (both are major in HU) | Research "biggest price comparison site [country] [category]" as a specific step |
| Global market share ≠ local | "Garmin is a niche brand" (Garmin dominates sports watch segment in every EU market) | Segment the local competitive set; sports ≠ smartwatch ≠ fitness band |
| Price tier blindness | Analyzing Pro as "mid-range" when 99,990 HUF ≈ 1.5× avg Hungarian monthly salary | Always compute price / avg monthly salary before any audience sizing |
| Assumed category penetration | "Smartwatch penetration ~10%" with no source | Source penetration or tag it `assumption` and flag in weakest_point |
| Ignored offline | Channel map shows only online platforms | Estimate offline share or declare `undetermined`; never assume 0% offline |

---

## Research Protocol

**Three rounds, approximately in this order:**

**Round 1 — Structure** (30–45 min, web search):
Identify the local distribution landscape, major retailers, price comparison sites,
and telco operators. Search in local language where possible.
→ Sections A, D, E (channel structure)

**Round 2 — Numbers** (20–30 min, site fetches):
Fetch actual product and competitor prices from local retailers identified in Round 1.
Confirm retailer ranking by checking traffic/popularity where possible.
→ Sections B (salary data), C (competitor prices), D (verify retailer share)

**Round 3 — Verify + Gaps** (15 min):
Cross-check any claim that directly affects budget, CAC, or channel selection
across at least 2 sources. Flag anything with a single source as `assumed`.
List open questions for Stage 1 to resolve.
→ Section F (regulatory), and any single-source facts from rounds 1–2

---

## Integration with Pipeline (ref 13)

Stage 0 runs before Stage 1 (Evidence Pull). It is not optional.

**When Stage 0 reveals a structural blocker** (e.g., the product is not sold in
the country at all, or the only viable channel requires brand-level budget this
campaign cannot reach), the pipeline may terminate before Stage 1 completes —
with a short memo explaining the structural constraint.

**When the user provides partial information** (e.g., "here are the channels we
use"), Stage 0 validates the provided list and fills in what is missing. It does
not skip; it verifies.

The Stage 0 output (structured intelligence card) is the input to Stage 1.
Stage 1 then adds specific sourced prices and URLs on top of the structural
framework Stage 0 established.
