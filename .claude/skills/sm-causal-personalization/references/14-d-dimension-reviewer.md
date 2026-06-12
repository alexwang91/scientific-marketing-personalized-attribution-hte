# 14 · D Dimension Generation + Causal Activation Reviewer

## Purpose

Specify how D dimensions are generated, what qualifies them for the heatmap, and
how the Causal Activation Reviewer challenges each one before budget is allocated.

---

## What Is a D Dimension?

A D dimension is an **operationalizable segmentation variable** that:
1. Is observable or inferable before the action is taken
2. Can be reached via a platform proxy (keyword, interest, behavior, lookalike)
3. Is mechanistically linked to a product feature or purchase barrier
4. Modifies a creative, bid, frequency, or suppression decision
5. Can have its incremental effect estimated via A/B, holdout, UTM, or split report

D dimensions are **not** demographics. Age group, gender, and income are starting
hints — they only enter the heatmap when linked to a behavioral proxy that satisfies
the 5 conditions above.

---

## Generation Protocol

**Step 1: Product mechanism scan**

For each product feature, ask:
> "Which type of person would respond *more* to this action because of this feature?"

Write the mechanism explicitly. "Runners respond to GPS" is not a mechanism.
"Runners who track route accuracy respond to GPS precision claims because their
current pain is pace drift on wrist-worn devices" is a mechanism.

**Step 2: Market path mapping**

For each mechanism, identify the local purchase path: how does this person search,
where do they compare, what channels exist to reach them?

**Step 3: Proxy validation**

For each mechanism + path, identify the reachable proxy:
- Keyword (e.g., "futoora" for running in Hungarian)
- Platform interest segment
- Content consumption signal (YouTube review viewer)
- Behavioral retargeting (cart abandon, product page visit)
- Retail category position (smartwatch category visitor on Alza)

**Step 4: Measurability check**

Is the incremental effect of targeting this proxy testable?
- A/B on creative or message
- Holdout group (no-contact arm)
- UTM + conversion tracking
- Platform lift study
- Geographic or time split

**Step 5: Sensitivity filter**

Check for:
- Body image / health language (especially weight, fitness goals)
- Age stereotyping
- Financial vulnerability signals
- Religious / ethnic targeting

Send any dimension that touches these to the Reviewer with a compliance flag before
including in the heatmap.

---

## Entry Gate

Dimension enters the heatmap iff ≥ 3 of 5 conditions are satisfied **and** it
passes the Reviewer with a verdict of "Retain" or "Retain (test)".

| Condition | Check |
|-----------|-------|
| Pre-deployment observable | Yes / Partially / No |
| Platform proxy exists | Yes / Estimate / No |
| Mechanism stated | Yes / Weak / No |
| Incrementality testable | Yes / Hard / No |
| Drives a decision change | Yes / Maybe / No |

Score 0/1 per condition. Threshold: ≥ 3.

---

## Full D Dimension Candidate Template

For each candidate, fill:

```
D{n}
name:          short label (≤ 5 words)
mechanism:     one sentence — why this dimension changes incremental response
proxy:         what platform signal represents this dimension locally
entry_score:   x/5 (cite which conditions pass)
reviewer_flag: none / compliance / sure-thing / ad-fatigue / low-proxy / weak-mechanism
verdict:       Retain / Retain (test only) / Demote S / Suppression only / Delete
```

---

## Causal Activation Reviewer

### Role

The Causal Activation Reviewer is a **built-in adversarial function** — not a
separate tool. It runs as part of D dimension processing and asks the hardest
question about each proposed H or T cell:

> "Why do you believe this dimension has *positive incremental effect* rather than
>  merely high correlation with purchase?"

### Five Verdict Types

| Verdict | Meaning | Heatmap treatment |
|---------|---------|-------------------|
| Retain | Evidence or mechanism is strong; proxy is deployable; risk is manageable | H or T as proposed |
| Retain (test only) | Plausible mechanism but weak proxy or unvalidated effect | Downgrade to T or S |
| Demote S | Proxy too broad or incrementality uncertain | Downgrade to S |
| Suppression only | Dimension identifies users to *exclude*, not target | Mark A in heatmap |
| Delete | Mechanism not stated; proxy is vanity metric; compliance risk | Remove from heatmap |

### Standard Challenges

The Reviewer always raises these challenges:

**1. Sure-thing check**
> "Are these users buying already regardless of the action? Would a holdout show zero
>  incremental lift?"

*Most common for*: brand keyword, retargeting, existing customer base.
*Resolution*: Retain with holdout design mandatory; flag sure-thing risk in guardrail.

**2. Correlation ≠ mechanism**
> "Is this dimension predictive of purchase (demographic correlation) or predictive of
>  incremental response to this specific action?"

*Most common for*: age groups, gender, income tiers.
*Resolution*: Retain only if a behavioral proxy is added (e.g., "25–34 AND
smartwatch-search" not "25–34").

**3. Platform proxy reality check**
> "Can you actually buy this signal on this platform in this market? What does it cost?
>  What is its minimum audience size?"

*Resolution*: If proxy is speculative, downgrade to T or S.

**4. Ad fatigue / sleeping-dog**
> "For retargeting and high-frequency prospecting: is there evidence that heavy
>  exposure harms high-intent users?"

*Resolution*: Frequency cap + no-contact arm required; mark as A if no frequency
control is possible.

**5. Compliance / sensitivity**
> "Does this dimension require inferring a health condition, financial state, or
>  other protected attribute? Is the creative claim within regulatory bounds?"

*Resolution*: Retain only if the proxy is behavior-based (e.g., "health content
viewer") not inferred attribute (e.g., "overweight user").

---

## Reviewer Output Format

The Reviewer's output is a table embedded in section 6 of the HTML report:

```
| Challenged dimension | Challenge raised | Current handling | Next evidence |
|---------------------|-----------------|-----------------|---------------|
| D7 Price compare    | Ad fatigue / deal-seeker inflation of ROAS | Primary budget with incremental margin guardrail | Discount vs proof vs no-contact comparison |
| D1 Brand search     | Sure-thing cannibalization | Low-intensity holdout mandatory | Brand keyword holdout or split bid control |
```

Followed by a **Reviewer conclusion** callout:
> "D dimensions are candidate operational variables, serving trial design and evidence
>  collection. Before entering primary budget, each must pass: deployable proxy,
>  testable incrementality, stated mechanism, no obvious compliance or margin risk."

---

## Handling Age and Gender Dimensions

Age and gender segments are **never standalone D dimensions**. They may appear in
the heatmap only as modifiers:

- "25–34 AND fitness-content viewer" (not "25–34")
- "Female AND lifestyle-watch interest" (not "Female")

Mechanism must reference why the age/gender group responds *differently to this
specific action*, not just why they might purchase.

---

## Compliance Dimension Rules

Any dimension that could require inferring:
- Medical condition or health risk
- Financial distress or vulnerability
- Religious belief or ethnic background
- Pregnancy or family status

→ Must be reviewed by human compliance team before heatmap inclusion. Tag as
  `Needs review` in the verification checklist.

Dimensions involving body image language ("weight loss", "slimming") must be
reviewed for local advertising standards. Default: Demote to S with strict creative
guardrails, or Delete.
