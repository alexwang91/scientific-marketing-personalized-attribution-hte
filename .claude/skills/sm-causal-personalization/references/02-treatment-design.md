# 02 · Treatment Design & Action Library

## When to Use

When designing marketing actions, creatives, or coupons; when AI-generated
variants outpace your ability to test them; when a model "isn't learning
anything" and you suspect the action definition is the problem.

## Core Principle

**Poorly defined treatments produce unlearnable models.**
"Send a marketing message" is too coarse.
"30%-off coupon + urgency framing + WeChat service account + 48-hour window"
is a learnable action.

## Treatment Card Template (one card per action in the library)

```yaml
treatment_id: T-2026-031          # versioned; any dimension change = new ID
channel: WeChat service account   # push / SMS / email / WeChat / outbound call / ad
incentive: 30%-off, cap ¥30, valid 48h
content: urgency-framing copy     # messaging frame, tone, length
timing: 2h after add-to-cart without checkout
frequency_cap: ≤2 same-type actions within 7 days
cost: channel_cost(¥0.05) + coupon_value × expected_redemption_rate
audience_constraint: exclude users with complaint in last 30 days
status: live / in-experiment / retired
```

## Decision Tree

```
How granular should actions be?
├─ Few combinations (<20 arms) → test each arm independently (standard multi-arm)
├─ Exploding combinations (channel × coupon × copy × timing)
│   ├─ Interactions likely between dimensions → factorial design
│   └─ Variants mainly differ in creative / copy → treatment featurization (see below)
└─ LLM continuously generating new variants → treatment featurization + arm count cap
```

## The LLM-Era Treatment Space Explosion

When creative production cost approaches zero, **the bottleneck shifts from
"making creatives" to "measurement bandwidth."** Testing each variant
independently requires linearly growing sample. Solutions:

1. **Treatment featurization**: model effect as a function of action attributes,
   τ(x, z) where z = (discount_depth, channel, copy_type, urgency_level, …).
   New variants don't need to be tested from scratch — interpolate in attribute
   space and validate with small traffic.

2. **Hierarchical models / partial pooling**: similar actions share statistical
   strength, giving usable estimates even with small per-variant samples.

3. **Cap concurrent live arms**: the action library can be large; the number of
   arms simultaneously in experiment should be bounded (heuristic: each arm
   should reach the power-required sample within 2–4 weeks — run
   `scripts/power_analysis.py`).

4. **LLM-as-judge for pre-screening only**: LLM can filter obviously inferior
   or policy-violating variants. LLM scores are not evidence of causal effect.
   All variants must pass through experiment before launch. (Red line → ref 09.)

## Defining the Control Group (the most error-prone detail)

- **"No action" vs "placeholder content" are two different controls**: the
  former measures the full effect of the action (including the act of reaching
  out); the latter measures only content differences. Choose deliberately.
- Control group users must be **reachable but randomly withheld** — using
  "users with no phone number" as control is classic confounding.
- Controls must be immune to **all similar actions**, not just this campaign
  (cross-campaign contamination is a persistent problem without global
  frequency control → ref 03 GCG).

## Step-by-Step

1. Write all existing actions as treatment cards; version and register them.
2. AI generates variants → auto-populate card fields (structured attributes) →
   LLM pre-screen → enter testing queue.
3. Select experiment structure per decision tree
   (independent arms / factorial / featurized).
4. Tag each action with cost; feeds into policy optimization (ref 06).

## Common Failure Modes

- **Treatment definition drift**: copy or coupon value changed mid-experiment —
  pre/post data is incomparable; the entire experiment is void
- **No versioning**: at analysis time you can't reconstruct what users actually
  received
- **Control group contamination**: control users touched by another team's
  campaign (requires global frequency control — see ref 03 GCG)
- **AI declares effective**: "LLM rates this copy better" used as launch
  justification — LLM judges text quality, not causal effect
- **Confounded dimensions**: changed channel and copy simultaneously —
  effect attribution is impossible

## Acceptance Checklist

- [ ] Every action has a treatment card with cost and version number
- [ ] Control group definition explicit (no-action vs placeholder); immune to
      similar actions
- [ ] Concurrent live arms ≤ measurement bandwidth
      (validated via `power_analysis.py`)
- [ ] LLM-generated variants go through "pre-screen → experiment" queue,
      not directly to launch
- [ ] Dimensions orthogonal: one dimension changed at a time, or explicit
      factorial design

## Literature

- Box, Hunter & Hunter, *Statistics for Experimenters* — factorial design
- Gelman & Hill, *Data Analysis Using Regression and Multilevel/Hierarchical
  Models* — partial pooling
- Amazon Science: causal contextual bandits series — treatment featurization
  in industry
