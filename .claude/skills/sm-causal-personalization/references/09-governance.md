# 09 · Governance & Red-Team (Front-loaded, Not Afterthought Compliance)

## When to Use

**Before writing any code for any project** (ref 01, step 5 points here);
before a new feature enters a model; before a new treatment type goes live;
when asked "is this compliant?"

## Why Front-Loaded

Causal personalization's core capability is "treating different people
differently and knowing that difference is effective" — this capability is
itself a risk surface. Compliance review after the fact can only take the model
offline. Front-loaded governance prevents "the model has already been using a
proxy for a protected attribute to set prices" from becoming a fait accompli.

## Feature Review: Four Questions (run for every X feature before it enters a model)

```
1. Legal — Does the data source have user consent? Does the use
   satisfy the purpose-limitation requirements of PIPL / GDPR / CCPA?

2. Stable — Will the distribution shift seasonally? Who owns the
   upstream instrumentation?

3. Explainable — Can you articulate to a regulator or user why this
   feature influences this decision?

4. Available at decision time — Can you actually retrieve it when the
   decision needs to be made? (A feature you can't serve at runtime is
   useless regardless of its predictive value.)
```

**Proxy variable audit**: zip code, device model, surname, shopping time-of-day
can all be proxies for protected attributes (ethnicity, income, gender). Check
by training a classifier to predict the protected attribute from the candidate
feature. High predictive accuracy → route to manual review before use.

## Red-Team Checklist (run for every new treatment type / policy before launch)

- [ ] **Price fairness**: does the policy charge different prices (or
      effectively do so via coupons) to different users for the same product?
      Differential pricing for new vs. existing customers has drawn regulatory
      action in multiple jurisdictions.

- [ ] **Vulnerable populations**: does the policy systematically steer high-
      risk actions (lending products, impulse-category goods) toward minors,
      elderly users, or financially fragile segments?

- [ ] **Discriminatory exclusion**: does the do-not-disturb / lost-cause list
      systematically exclude any protected group from promotions?
      Validate with disaggregated fairness audits.

- [ ] **False claims**: does AI-generated copy exaggerate efficacy, fabricate
      scarcity ("only 3 left" — is it?), or manufacture social proof?

- [ ] **Dark patterns / manufactured anxiety**: countdown clocks that create
      artificial urgency, buried unsubscribe paths, confirm-shaming. Recast
      causally, these all inflate the **Anxiety force** (ref 02). Beyond the
      compliance exposure, anxiety-inflation can drive *negative* incremental
      effect — lower conversion or higher post-purchase churn. A treatment
      whose only mechanism is manufactured anxiety fails both the red-team and
      the τ(x) test; there is no version of it that is merely "aggressive but
      effective."

- [ ] **Frequency harm**: after stacking all campaigns, does any user's
      aggregate contact frequency exceed the guardrail cap?

## Suppression Is a Governed Decision (the anti-persona list)

"Who *not* to target" is as much a governed artifact as who to target. Two
distinct reasons to suppress, with different owners and different failure modes:

| Reason | Basis | Owner | Risk if ungoverned |
|--------|-------|-------|--------------------|
| **Won't move** (effectiveness) | Resistance forces dominate — Habit-bound, or already-decided with Pull maxed; the treatment yields τ ≈ 0 | Policy (ref 06) + Reviewer (ref 14) | Wasted budget, attribution credit for sure-things |
| **Must not move** (compliance) | Vulnerable population, protected-attribute proxy, or only-available lever is manufactured Anxiety | This doc | Regulatory action, real-world harm |

The **anti-persona list** is the operational union of the two — the people the
program deliberately leaves alone. It is a **structured input** produced during
dimension generation (ref 14, Step 6), not a leftover of margin arithmetic.

But suppression is not automatically safe: run the **discriminatory-exclusion
check** (above) on the anti-persona list itself. A do-not-disturb rule that
systematically removes a protected group from *beneficial* offers is a fairness
failure even when every individual rule looked locally reasonable. Suppression
decisions enter the same audit log as targeting decisions.

## AI Role Hard Lines (enforce in system permissions, not just in prompts)

**AI may**:
- Generate treatment variants (output must enter the ref 02
  "pre-screen → experiment" queue)
- Extract context features from unstructured data (output must pass the
  four-question feature review)
- Write experiment documentation, interpret model output, run policy simulations
- Monitor drift, anomalies, and guardrail metrics

**AI must not**:
- Declare an action "effective" without experimental or identification-strategy
  support
- Use LLM evaluation — including multi-agent simulation (AgentA/B) — as a
  substitute for holdout / experiment to justify launch. Simulation results
  are pre-screening evidence only.
- Autonomously expand the target audience or modify treatment parameters and
  deploy without approval
- Generate policy-evading copy variants (e.g., synonym-swap to bypass
  restricted-keyword filters)

**How to enforce**: these four prohibitions belong in agent tool permissions
and approval workflows — not just in the system prompt.

## Audit Log (what you need when a regulator asks)

Every decision must be reproducible: anonymized user ID, timestamp, context
snapshot, candidate action set, propensity, selected action, approval-chain
version (policy version number + treatment card version number).
The propensity log from ref 03 and this audit log are the same infrastructure.

## Common Failure Modes

- **Compliance as final step**: model has been live for six months; Legal finds
  the coupon policy constitutes price discrimination; full rollback + retroactive
  remediation.
- **Proxy variables in production**: "we don't use sensitive attributes" — but
  the model uses device model + zip code + shopping timestamp, effectively
  reconstructing an income score.
- **Red-team run once**: the treatment library adds new actions weekly; the
  red-team checklist hasn't been touched since launch day.
- **AI hard lines only in prompt**: a prompt injection or jailbreak immediately
  removes the constraint; only permission-layer enforcement holds.

## Acceptance Checklist

- [ ] All model features pass the four questions + proxy audit
- [ ] Red-team checklist completed for every treatment type, with records
- [ ] AI hard lines enforced at system permission / approval workflow level
- [ ] Audit log can replay any individual decision
- [ ] Disaggregated fairness audit (action distribution + τ̂ distribution by
      sensitive dimension) on a quarterly cadence

## Literature

- Barocas, Hardt & Narayanan, *Fairness and Machine Learning* —
  fairness framework
- PIPL (China) / GDPR (EU) / FTC dark-patterns enforcement reports (US) —
  consult the latest applicable jurisdiction's text
- Wachter et al. (2017) "Counterfactual Explanations Without Opening the Black
  Box" — technical path to explainability obligations
