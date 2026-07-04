---
name: sm-causal-personalization
description: >
  Causal personalization / HTE / uplift / incrementality decision system for
  marketing and sales. Trigger when the user asks about: marketing lift,
  uplift modeling, HTE, CATE, incrementality, coupon / discount strategy,
  experiment design, holdout, global control group (GCG), geo-lift, next best
  action / treatment, policy learning, off-policy evaluation (OPE), contextual
  bandit, attribution vs incrementality, lead routing, discount approval,
  ABM experiments, or mentions "scientific marketing", "causal inference in
  marketing", or "personalized attribution".
  Also trigger on the plain-language versions a founder or marketer would
  actually type: "should I give this customer a discount / coupon", "is my
  campaign / ad actually working", "who should I target — and who should I
  skip", "is this channel worth the spend", "did the promo really drive sales
  or would they have bought anyway", "which customers deserve a retention
  offer", "why isn't my targeting working".
  Also trigger when the user brings a whole category line-up in a market and
  wants a portfolio diagnostic: "how is my <category> doing in <country>",
  "which SKU should I push, hold, harvest, or kill", "build me the 4P matrix
  across my models", "diagnose my product line-up / price bands / competitors".
  Covers the full chain: category portfolio diagnostic → problem framing →
  experiment design → HTE estimation → uplift segmentation → policy
  optimization → governance / compliance.
---

# Scientific Marketing: Causal Personalization Decision System

## Language Policy

**Always detect the user's language from their message and respond in the same
language.** If the user writes in Chinese, respond in Chinese. If in English,
respond in English. Mixed or ambiguous input: default to the user's dominant
language. Technical terms (HTE, CATE, GCG, OPE, Qini, etc.) stay in English
regardless of response language.

---

## Core Mental Model

**Traditional personalization asks "who is most likely to buy."
Causal personalization asks "who bought MORE because of my action."**

This is an AI-assisted causal decisioning system, not a single model:

- **AI's role**: generate treatment variants, extract context from unstructured
  data (reviews, support logs, sales calls), write experiment docs, explain
  models, monitor drift
- **Causal methods**: estimate whether actions have incremental value
  (τ(x) = E[Y(1)−Y(0)|X=x])
- **Hard line**: AI must not declare an action "effective" without experimental
  or identification-strategy support. LLM evaluation does not replace holdout.
- **Hard line**: honest blanks beat fabricated completeness. Every number in
  every deliverable is sourced, assumed (basis stated), derived (chain shown),
  or missing (no value displayed) — there is no fifth state (→ ref 16).
  "Undetermined" and "don't spend" are legal, common, and often the most
  valuable conclusions.

### Three-Layer Relationship

| Question | Tool | Level |
|----------|------|-------|
| How to split budget across channels | MMM | Channel/budget level |
| Which touchpoint gets credit for a conversion | Attribution / MTA | Touchpoint level (correlation) |
| How much incremental lift does this action give this person | HTE / uplift | Individual level (causal) |

HTE is "individual-level incrementality" — the thing attribution tries and
fails to approximate.

---

## Maturity Ladder (three levels; do not skip)

- **L1**: Global Control Group (GCG) + retrospective uplift analysis.
  Starting point for all teams.
- **L2**: Offline policy learning + OPE validation + periodic retraining.
  Most teams should stay here for a long time.
- **L3**: Contextual bandit with online learning. Only needed when actions
  are numerous and the environment changes fast.

**Hard rule**: Without randomized data, the first step is always to build the
experiment infrastructure (GCG / geo-test), not to estimate CATE from
observational logs. Marketing logs carry severe confounding — who gets
targeted is determined by the existing targeting policy. Observational methods
are a fallback and must include explicit identification assumptions (→ ref 03).

---

## Four-Layer Production Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1 · Data & Experiment Assets                             │
│  RCT logs + propensity P(t|x) + GCG + historical experiments   │
│  (ref 03)  ← pool across campaigns; each experiment is a       │
│             reusable evaluation asset (Snap, arXiv 2512.03060) │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2 · Effect Estimation                                    │
│  τ̂(x) via DR-learner / Causal Forest / X-learner             │
│  (ref 04)  ← calibrated AND ranked; ZILN loss for revenue Y   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3 · Decision & Allocation                               │
│  Policy π(x): argmax + λ* budget constraint + OPE gate        │
│  (ref 06)  ← two-stage default; E3IR end-to-end for L2+;      │
│             large action space: MIPS/OffCEM/embedding OPE      │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4 · Generation & Serving (optional, L2+)                │
│  LLM embeddings as features (not decision-makers);             │
│  GenAI serving layer for copy personalization                  │
│  (LinkedIn CPOG, arXiv 2505.09847)                             │
└─────────────────────────────────────────────────────────────────┘
```

**Architecture position**: two-stage (estimate then optimize) is the default
for auditability and declarative constraints. End-to-end decision-focused
training (E3IR, Booking 2024) is a L2+ performance option when calibration
is less critical than rank quality.

## Decision Tree: Which Reference Applies?

```
FIRST — what scope did the user bring?
├─ A whole CATEGORY + country + a list of in-market SKUs
│   ("how is my <category> line-up doing in <country>; which SKU to push / kill")
│   → 17-category-portfolio-diagnostic  (diagnose the portfolio, verdict each SKU;
│       "Grow" SKUs then descend into 13 → 04 below)
└─ A single SKU / campaign + country → continue to the tree below
```

```
What is the user asking about?
├─ "Is this campaign / program worth it? How do I define metrics?"
│   → 01-problem-framing
├─ "How to design actions / creatives / coupons; too many AI variants to test"
│   → 02-treatment-design
├─ "How to design experiments; no experimental data; how much sample do I need?"
│   → 03-experiments
├─ "How to estimate who is affected; which model to use; how to validate"
│   → 04-hte-estimation
│     ├─ Need calibrated τ̂ (profit optimization) → standard path
│     └─ Need ranking only (budget rank-list) → decision-focused learner
├─ "How to segment users; who to target and who to skip"
│   → 05-uplift-segmentation
├─ "Which action to give each user; budget constraints; evaluate before launch"
│   → 06-policy-nbt
│     └─ Large action space (>100 arms) → 06 large-action-space OPE section
├─ "Should we use a bandit; how to do online learning"
│   → 07-bandits-online
├─ "Short-term works, what about long-term? LTV, surrogate metrics"
│   → 08-long-term-value
├─ "Compliance, fairness, privacy, which features are allowed"
│   → 09-governance  (always run this at project kickoff)
├─ "How to roll this out org-wide; marketing/sales team alignment; KPI design"
│   → 10-org-playbook
├─ "How to build or evaluate a production-scale platform (data eng, retraining,
│   serving, CPOG-style architecture)"
│   → 11-production-architecture
│
│  ── Output & Delivery layer ───────────────────────────────────────────────
├─ "Generate a deliverable report / campaign brief / HTML output"
│   → 12-html-report-output  (five-question chapter spine + 6-element memo,
│       provenance rendering, pill budget, short-report mode; generate_report.py
│       enforces the contract and localizes every heading via L())
├─ "User gives a product + country; needs channel map, audience, treatment plan"
│   → 13-product-country-pipeline  (8 stages: **Stage 0 local market intelligence
│       [mandatory, see ref 00]** → evidence → unit economics →
│       channel screen [may terminate here] → dimensions → review → tests → render)
├─ "Need to research a new product × country before the pipeline; how to avoid
│   transferring wrong assumptions (retailer rank, channels) across markets"
│   → 00-local-market-intelligence  (dynamic 5-move scoping kernel: characterize
│       cell on 7 axes → transfer-assumption ledger → distinctiveness hypotheses
│       → rank plan → re-orchestrate; generates a custom plan per cell, not a list)
├─ "Where do the four forces / D dimensions actually come from; mine real
│   customer reviews, social, competitor sentiment instead of inventing them"
│   → 00b-customer-voice-competitor-scan  (engagement-ranked listening: resolve
│       posts → extract verbatim quotes into Push/Pull/Habit/Anxiety + candidate
│       dimensions + competitor map; hard line: voice is Hypothesis-grade, it
│       generates what to TEST, never proves incrementality)
├─ "How to generate / challenge D dimensions; adversarial review"
│   → 14-d-dimension-reviewer  (generation gate; independent review pass,
│       immutable challenges, open-blocking → BLOCKED budget linkage)
├─ "How should the output be written; language; how to state uncertainty"
│   → 15-writing-rules  (language policy, falsifiability obligation,
│       honest-state vocabulary, anti-slop, form budget)
├─ "Where does this number come from; estimates; benchmarks; sensitivity"
│   → 16-estimation-discipline  (four provenance states, Fermi chains,
│       benchmark asymmetry, sensitivity-sorted Missing ledger)
└─ "Diagnose my whole category line-up in this market; which SKU to push / kill;
│   build the 4P matrix" (operator brings a category + SKU list, not one product)
    → 17-category-portfolio-diagnostic  (6 audit lenses [2 market + 4 audited-P],
        severity capped by evidence grade, SKU verdicts Grow/Hold/Harvest/Exit;
        report_type=category_portfolio in generate_report.py; feeds 13 → 04)
```

---

## Scripts (all validated)

| Script | Purpose | Report bridge |
|--------|---------|--------------|
| `power_analysis.py` | Uplift experiment power: sample size to detect incremental difference (~4× a standard A/B) | Section 9 gate + section 13 duration |
| `qini_auuc.py` | Qini curve, AUUC + bootstrap CI, decile calibration, two-model comparison | Section 11 AUUC launch gate |
| `hte_starter.py` | T/X/DR-learner starter templates (sklearn, drop-in replaceable with EconML / CausalML) | — |
| `ope_estimators.py` | IPS / SNIPS / Doubly Robust off-policy evaluation + support check | Section 14 OPE support check |
| `policy_budget.py` | λ* budget-constrained allocation (ref 06 knapsack / shadow price), IPW policy value on a randomized holdout, profit-vs-budget curve | Layer 3 decision tool |
| `generate_report.py` | Decision-memo HTML generator (v2). **Enforces the provenance contract**: build fails on any number that is not sourced / assumed / derived / missing; renders derivation chains; stamps BLOCKED on actions gated by open-blocking challenges; short-report mode when the pipeline terminates at the channel screen. **Depth modes**: `quick` (decision-critical sections only), `standard` (full report, default), `deep` (full + consolidated validation roadmap §18, built only from existing config data). **Category mode**: `report_type=category_portfolio` renders the ref 17 portfolio diagnostic (6 audit lenses, SKU verdicts, 4P matrix) instead of the single-SKU report | **Entry point for HTML output** |

```bash
python scripts/generate_report.py --config config.json --validate-only  # contract check
python scripts/generate_report.py --config config.json --output report.html
python scripts/generate_report.py --config config.json --depth quick      # executive view: verdict + math + gate + evidence
python scripts/generate_report.py --config config.json --depth deep       # full report + validation roadmap (§18)
python scripts/generate_report.py --demo > demo.html
# Worked example: examples/sample-sku-en-config.json
```

---

## Six Prerequisites (self-check before any project kickoff)

1. **Experimental data**: Without RCT / holdout / geo-test / credible
   quasi-experiment, you cannot claim "marketing caused this"
2. **Action definition**: "Send a marketing message" is too coarse.
   "30%-off coupon + urgency copy + WeChat + 48-hour window" is learnable
3. **Profit metric**: Incremental profit = incremental revenue × margin
   − subsidy cost × redemption rate − channel cost − long-term negative effects
4. **Sample size**: CATE is data-hungry. Too-granular segments are pure noise
   (run `power_analysis.py` first)
5. **Data engineering**: user ID, exposure / action / outcome logs, timestamps,
   costs, experiment-group flag, **propensity log P(action|x)**
6. **Organizational execution**: the marketing team must accept
   "don't target some high-conversion users" — a counter-intuitive conclusion
   (messaging guide → ref 10)

---

## Shared Structure of All References

Each reference follows: when to use → decision tree → minimum necessary math →
step-by-step operations → common failure modes → acceptance checklist →
literature pointers. Decision guide, not textbook.
