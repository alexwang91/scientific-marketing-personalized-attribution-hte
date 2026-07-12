# 18 · Audience Card (Define → Size → Reach)

## When to Use

When the report has to answer **"who exactly, how many of them, where do we
reach them, and are they worth touching"** — and a one-line audience label is
not enough. This is the layer that turns *"人群 D"* from a name into a **sized,
graded, reachable number with a route to it**.

It sits inside chapter 3 (打法 / The Play) next to the D-dimension reviewer
(ref 14) and the channel map. The D-dimension reviewer asks *is this a real
causal cut*; this reference asks *how big is it, how do I reach it, and how
sure am I of the size*. Use both: a dimension that passes the reviewer but has
no reachable pool is a research note, not a budget line.

```
Product/SKU + market, "who do I target and how much of a pool is there"
  → ref 45-style product read (does the product encode the market?)
  → 20-dimension audience card (define)
  → four-layer sizing (how many, with a grade)
  → platform activation (where, with what match quality)
  → causal filter (ref 05: how many are actually persuadable)
```

## Core Principle: Read the Product Before You Reach for Demographics

Many products already encode their market. A mobile hotspot and a home router
are different competitive fields even though both are "routers" — the buyer,
the demand job, and the shelf are different. Starting from age/gender bands
when the product design already tells you the use case throws away the
sharpest signal you have.

The order is:

```
product meaning → demand job → observable proxy → causal segment → treatment → measure
```

Audience demographics are **downstream** of product-market meaning, not a
substitute for it. Before filling a 20D card, ask: is this product positioned
by a use case, occasion, body context, environment, or performance claim
(sport, commute, sleep, travel, gaming, outdoor, baby care)? Do search queries
carry that modifier? Do marketplace filters expose it? Do reviews keep naming
it? If yes, the audience is *"people facing that job"*, and the platform proxy
is a product/category/query signal — not an interest band.

This maps the sibling module's product-market-semantics + audience-taxonomy +
platform-activation chain onto this skill's evidence contract (credit below).

## The 20-Dimension Audience Card (Define)

Describe an audience in **our own dimensions first**, then map to whatever a
platform happens to expose. A platform segment is an **activation proxy, not
the audience** — never write the audience *as* "Meta in-market: routers".

| # | Dimension | Operator question |
|---|-----------|-------------------|
| 1 | Country / sub-region | Where do they buy? |
| 2 | Language | What language is the shelf and the ad in? |
| 3 | Age band | Only if it changes the play — otherwise skip |
| 4 | Gender | Only where allowed and relevant |
| 5 | Household / life stage | Who else is in the buying decision? |
| 6 | Income / price tier | Which price band can they clear? |
| 7 | Device / OS / connection | What are they shopping on? |
| 8 | Category interest | Are they in this category at all? |
| 9 | In-market / purchase intent | Are they shopping *now*? |
| 10 | Search / query intent | What do they type? |
| 11 | Product / SKU interest | Which of your SKUs are they near? |
| 12 | Competitor / substitute interest | Whose product are they comparing? |
| 13 | Brand familiarity | Cold / aware / engaged / customer / loyal |
| 14 | Funnel state | Unaware → problem-aware → comparing → ready → post-purchase |
| 15 | Recency | Recent viewer / cart / lapsed / dormant |
| 16 | Frequency / intensity | Heavy user / occasional / deal-seeker / repeat buyer |
| 17 | Price sensitivity | Discount-only, or will they pay for proof? |
| 18 | Content / creator affinity | Whose word do they trust? |
| 19 | Channel preference | Search / social video / marketplace / retail / sales |
| 20 | **Causal role** | Persuadable / sure-thing / lost-cause / sleeping-dog / unknown (ref 05) |

Dimension 20 is the one that decides budget. A precise 19-dimension portrait of
a **sure-thing** is a precise portrait of wasted spend. Do not fill the causal
role from platform data alone — it comes from a holdout / uplift read (ref 04),
or it is written `unknown` and the plan is exploration.

Optional dimensions when they change the play: business role / company size /
seniority / buying committee (B2B, ref 10); sensitive-category constraints
(ref 09); local trust source; inventory / shipping availability.

**Do not overbuild.** Add a dimension only if a platform, feed, search, review,
or catalog signal supports it *and* the targeting or creative decision changes
because of it. A dimension no channel can express and no buyer uses is a
qualitative note, not a card field.

## Four-Layer Sizing (How Many, With a Grade)

Estimate the pool **in layers, never as one number**. Each layer narrows the
one above it, and each carries its own source and grade.

```
Layer 1  Country universe        population → adults → internet → smartphone →
                                  category buyers → ecommerce buyers
Layer 2  Platform reachable      what the ad account / retailer says it can reach
                                  (label it "account estimate", not true population)
Layer 3  Category / intent filter category interest × in-market × query demand ×
                                  competitor-shopper × lapsed-buyer share
Layer 4  Causal filter           persuadable / sure-thing / lost-cause / sleeping-dog
                                  share — from holdout / uplift, never platform data
```

The sizing chain, written so a reader can see every multiplier:

```
reachable_target_size   = country_reachable_users
                          × category_or_intent_share
                          × activation_match_rate
                          × eligibility_rate

expected_persuadable    = reachable_target_size × persuadable_share

expected_treatable      = expected_persuadable − suppressed − governance_blocked
```

If there is no causal read, set `persuadable_share = unknown` and label the
plan exploration. Report the reachable size; do **not** invent a persuadable
number to fill the box.

## Confidence Grade = This Skill's Provenance Contract, Applied to Size

Every audience size carries a grade. We use **the same four states** the rest
of the report uses (ref 16), so a sized audience is audited exactly like a CAC
number — no separate vocabulary:

| Audience grade | Means | Provenance state (ref 16) | Prose label (ref 15) |
|----------------|-------|---------------------------|----------------------|
| **A** | platform estimate + first-party or experiment support | `sourced` | Evidence |
| **B** | platform estimate + category / search data | `assumed` | Assumption |
| **C** | third-party report + platform proxy | `assumed` (basis stated) | Hypothesis |
| **D** | assumption only | `missing` if it drives budget | Needs test |

**The one rule that keeps sizing honest: never hide a D-grade assumption inside
a precise percentage.** "12.4% of the market" written from a guess is a lie with
a decimal point. Write "roughly a tenth, D-grade — needs a reach-planner pull"
instead. This is Rule 2 (evidence labels) and the severity cap (ref 17) applied
to audience size.

## Platform Activation (Where, With What Match Quality)

A causal segment does not exist inside an ad platform until you translate it
into an available control — and the translation almost always loses something.
For each audience, name the proxy **and** grade the fit:

| Match quality | Means | What the report must add |
|---------------|-------|--------------------------|
| **High** | first-party list or internal bidder expresses the segment directly | — |
| **Medium** | close proxy (in-market category, keyword, product targeting) | say what leaks in (e.g. includes sure-things) |
| **Low** | loose proxy (broad interest, demographic stand-in) | prioritize learning over scale |
| **Unavailable** | no legal or practical control exists | do not claim you can target it |

Targeting priority order (use the highest available):

1. Product / category / search / SKU / feed targeting when the use case is
   product-encoded (ref 45).
2. First-party or internal-bidder segment, if consented.
3. Retargeting on product / category behavior, if the segment is behavioral.
4. Search / query / contextual, if intent is explicit.
5. Custom segment from keywords / URLs / competitor signals.
6. Lookalike from a validated seed.
7. Interest / affinity / in-market proxy.
8. Broad / automated with strong creative **and a holdout**.
9. Creator / KOL when trust, demonstration, or community entry is the job
   (ref 02 KOL gate).

If only weak proxies exist, the recommendation is **learn, not scale**.

## Measurement Is Not Optional

Platform-reported conversions do not measure incrementality. Every audience
card names one real measurement route: holdout, geo / market split,
suppressed-audience incrementality test, matched-market test, or an internal
margin read after joining exposure logs. When platform automation delivers the
ad, the holdout sits **outside** the automated system where possible (ref 03).

## Audience Card Output (the rendered artifact)

One card per target audience, rendered in ch3:

- Audience name (operator language, not a platform segment id).
- 20D definition (only the dimensions that change the play).
- Country + reachable size + **grade A/B/C/D**.
- Persuadable size (or `unknown` + exploration flag).
- Platform proxy + **match quality**.
- Recommended targeting path.
- Suppression rule (who to exclude — ref 05 sure-things / sleeping-dogs).
- Measurement plan.
- **Weakest assumption** (the one line that, if wrong, breaks the card).

## Config Schema (audience_schema.py / generate_report.py)

`audience_cards[]` on any config (single-SKU or `category_portfolio`) renders
the section. Each card: `name`, `causal_role`
(`persuadable`/`sure_thing`/`lost_cause`/`sleeping_dog`/`unknown`),
`dimensions{}` (any subset of the 20, operator-labelled), a `sizing` chain
(`country_reachable`, `category_or_intent_share`, `activation_match_rate`,
`eligibility_rate`, `persuadable_share`, each with a `grade` A–D and a
`source`), `reach[]` (per-platform `proxy` + `match_quality` +
`what_leaks`), `suppression`, `measurement`, and `weakest_assumption`.
The renderer computes `reachable_target_size` and `expected_persuadable` from
the chain — they are **derived, never raw input** — and stamps the lowest grade
in the chain onto the card (a chain is only as sound as its weakest multiplier).
`audience_schema.py` rejects a card that states a persuadable size with no
causal source, or a precise share carrying a D grade with no `needed_from`.

## Common Failure Modes

- **Platform segment written as the audience**: "Meta in-market: home networking"
  is a proxy, not a who. Define in the 20D first, map second.
- **One number, no layers**: a single "market size" with no chain and no grade —
  unauditable, usually a D dressed as an A.
- **Persuadable share from platform data**: causal role is a holdout output
  (ref 04/05), never an in-market segment.
- **Demographics before product read**: filling age/gender when the product
  already encodes the use case (ref 45).
- **High match quality assumed**: a broad-interest proxy called "targeted" — say
  what leaks in, or drop to Low and learn.
- **Card with no weakest assumption**: every sizing chain has one; hiding it
  doesn't remove the risk, it just moves it to the reader's budget.

## Acceptance Checklist

- [ ] Product-market read done first when the product encodes a use case
- [ ] Each audience defined in the 20D card before any platform segment named
- [ ] Every size estimate carries a grade A/B/C/D; no D-grade precise percentage
- [ ] Reachable size shown as a layered chain, not a single number
- [ ] Persuadable share comes from a causal read, or is written `unknown`
- [ ] Each platform proxy carries a match quality; medium/low says what leaks
- [ ] Causal role (dim 20) set for every card; sure-things/sleeping-dogs suppressed
- [ ] Each card names one real measurement route (not platform conversions)
- [ ] Each card states its single weakest assumption

## Literature & Credit

- Pattern credit: the 20-dimension audience taxonomy, four-layer country sizing,
  product-market semantics, and platform-activation adapter adapt the
  audience-definition moves from the sibling module
  (`alexwang91/scientific-marketing`, refs 44 / 45 / 42), re-grounded on this
  skill's provenance contract (ref 16) so an audience size stays Assumption
  until a reach planner or experiment promotes it, and a causal role stays
  `unknown` until a holdout fills it.
- Ascarza (2018) and the persuadable / sleeping-dog taxonomy — see ref 05.
- See also ref 14 (D-dimension reviewer — is the cut real), ref 45-style
  product read, ref 02 (treatment + KOL gate), ref 03 (holdout), ref 16
  (provenance states), ref 17 (category diagnostic — buckets SKUs by purchase
  decision, which is this reference's product read applied to a whole line-up).
