# 11 · Production Platform Architecture

## When to Use

When building or evaluating a production-scale causal personalization system;
when asked "how do Snap / LinkedIn / Netflix / Spotify do this at scale?";
when planning data engineering, serving, retraining, or multi-team orchestration;
when designing the overall system rather than a single model or experiment.

---

## The Core Insight: Platform > Single Model

A single well-trained CATE model is not the goal. A production causal
personalization platform is a **compounding learning infrastructure** where:

- Every experiment adds to a reusable pool of causal estimates
- Every policy deployment generates propensity logs for future OPE
- Retraining is incremental (not rebuild-from-scratch)
- τ̂(x) scores are first-class data assets reused across teams

**Single-model teams** hit a ceiling: the next model improvement is marginal;
the real bottleneck is measurement bandwidth, experiment throughput, and data
reuse. **Platform teams** compound: the 50th experiment benefits from all
prior 49.

Reference: Snap HTE Platform (arXiv 2512.03060) — "platform > single model"
in production.

---

## Four-Layer Reference Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  LAYER 1: Data & Experiment Asset Store                            │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐   │
│  │ RCT / GCG    │  │ Propensity   │  │ Historical τ̂(x)      │   │
│  │ experiment   │  │ logs         │  │ estimates + CIs       │   │
│  │ records      │  │ P(t|x,time)  │  │ per experiment        │   │
│  └──────────────┘  └──────────────┘  └───────────────────────┘   │
│                                                                    │
│  Key property: every completed experiment is immutably archived.  │
│  Downstream layers can reuse as evaluation assets.                │
├────────────────────────────────────────────────────────────────────┤
│  LAYER 2: Effect Estimation (offline, periodic retraining)        │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Meta-learner stack                                      │     │
│  │  DR-learner / Causal Forest (binary Y)                  │     │
│  │  ZILN two-head model (revenue Y)                        │     │
│  │  X-learner (GCG imbalanced splits)                      │     │
│  │                                                          │     │
│  │  Cross-validated on holdout; AUUC + bootstrap CI gate   │     │
│  │  Incremental retraining (new experiments → update,      │     │
│  │  not full rebuild) — Snap platform pattern              │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                    │
│  Output: τ̂(x) score files → registered in asset store           │
├────────────────────────────────────────────────────────────────────┤
│  LAYER 3: Decision & Allocation Engine                             │
│                                                                    │
│  ┌──────────────────────┐  ┌────────────────────────────────┐     │
│  │  Policy optimizer    │  │  OPE gate                      │     │
│  │  argmax + λ*         │  │  SNIPS / DR + support check   │     │
│  │  knapsack / LP       │  │  Large action space: MIPS/OBP │     │
│  │  monotonicity check  │  │  Conformal CI for small n      │     │
│  └──────────────────────┘  └────────────────────────────────┘     │
│                                                                    │
│  Two-stage default (estimate then optimize).                       │
│  E3IR / ranking metalearner as L2+ option.                        │
│  Safe OPG conservative constraints on first deployment.           │
├────────────────────────────────────────────────────────────────────┤
│  LAYER 4: Serving & Generation (optional, L2+)                    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  CDP / Journey orchestration (Braze / Iterable / custom) │     │
│  │  ↑ reads π(x) decisions from Layer 3                    │     │
│  │                                                          │     │
│  │  GenAI copy layer (if deployed):                        │     │
│  │  LLM receives: {treatment_card, τ̂ score, user_segment} │     │
│  │  LLM generates: personalized copy variants              │     │
│  │  LLM does NOT: make policy decisions or declare effects │     │
│  └──────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────┘
```

---

## Snap HTE Platform Pattern (arXiv 2512.03060)

Snap's production architecture introduced three concepts now considered
best practice:

1. **Incremental retraining over full rebuild**: when new experiment data
   arrives, update the causal estimator incrementally rather than re-running
   the full training pipeline. Reduces compute cost and stabilizes production
   τ̂ scores across retraining cycles.

2. **τ̂ scores as first-class data products**: CATE score files are versioned,
   registered in a feature store, and made available to all downstream teams
   (policy optimizer, reporting, allocation, A/B holdout design). This is
   what transforms a research prototype into organizational infrastructure.

3. **Cross-experiment pooling**: experiments on similar populations / treatments
   share statistical strength via a hierarchical model. Data-thin segments get
   informed priors from structurally similar experiments rather than defaulting
   to zero-effect priors.

---

## LinkedIn CPOG Architecture (arXiv 2505.09847)

LinkedIn's **Causal Personalization on Graph** system is the most detailed
published production B2B reference:

```
Step 1: Causal prediction layer
  - Estimate τ̂ at member × account × product grain
  - Graph-structured features: member→account, member→company connections
  - Output: τ̂ scores + uncertainty estimates registered in feature store

Step 2: Constrained optimization + bandit
  - Lagrangian knapsack under capacity, fairness, and editorial constraints
  - Contextual bandit handles exploration for newly launched content types
  - Editorial approval gates treatment types before they enter the bandit arm pool

Step 3: GenAI serving layer
  - LLM receives: {π(x) decision, τ̂ context, treatment card}
  - LLM generates: member-personalized content copy
  - LLM does NOT access: raw member graph data, policy optimization logic
  - Hard-line: LLM is a copywriter, not a decision-maker (ref 09 AI hard lines)
```

**B2B-specific adaptations**:
- Account-level cluster randomization for all ABM experiments (ref 03)
- Pipeline value (continuous) as outcome, not binary win/loss (higher power)
- Salesperson-level τ̂ calibration (VALOR 2026: individual rep context
  predicts discount swing factor better than deal-level attributes)

---

## Maturity-Gated Build Order

Build layers in order. Do not build Layer 4 before Layer 1 is solid.

```
Month 1–3 (L1):
  □ Layer 1: GCG + propensity logging + experiment archive schema
  □ Layer 2: First τ̂ estimation on one triggered-campaign dataset

Month 3–12 (L2):
  □ Layer 3: OPE gate + policy optimizer + λ* constraint
  □ Dual holdout launch process
  □ Incremental retraining pipeline

Month 12+ (L2/L3):
  □ Layer 1: Cross-experiment pooling activated
  □ Layer 3: Large-action-space OPE (if action library > 100 arms)
  □ Layer 4: GenAI serving layer (if copy personalization required)
  □ L3 bandit (only if all four ref 07 criteria are met)
```

---

## Data Engineering Contracts (the invisible prerequisite)

Without these, all layers above fail:

| Contract | Owner | SLA |
|----------|-------|-----|
| `user_id` stable across sessions | Infra | 99.9% match |
| Propensity log P(t\|x) written at action decision time | Backend | Real-time |
| Experiment group flag on all event records | Experiment platform | 100% |
| Treatment card version on all exposure records | CRM / CDP | 100% |
| Outcome events (purchase, churn, etc.) join-able to exposure log | Data Eng | T+24h |
| τ̂ score file versioned + timestamped in feature store | ML Eng | At model deploy |

Any missing contract is debt that makes the next layer impossible to build
correctly. Audit all six at project kickoff.

---

## Common Failure Modes

- **Layer 4 without Layer 1**: GenAI personalization deployed; no propensity
  logs; no holdout; no way to measure if it works. Impressively visible,
  measurably useless.
- **τ̂ scores not versioned**: policy deployed at week 3; model retrained at
  week 8; audit at week 12 cannot reconstruct which score version drove
  which decision.
- **Incremental retraining without data quality gate**: corrupted experiment
  data silently enters the training pool; τ̂ drifts; no one notices until a
  catastrophic policy decision.
- **Cross-experiment pooling before standardization**: pooling τ̂ estimates
  from experiments with different outcome definitions or treatment granularity
  produces methodological garbage.
- **GenAI layer making editorial decisions**: "the LLM decided to include a
  discount" — discount decisions must come from Layer 3, not Layer 4.

---

## Acceptance Checklist

- [ ] All six data engineering contracts audited and live
- [ ] Layer 1 archive schema defined; first experiment archived completely
- [ ] τ̂ score files versioned and registered in feature store
- [ ] OPE gate in Layer 3 before any policy goes live
- [ ] GenAI layer (if used) receives causal scores as input; does not make
      policy decisions
- [ ] Maturity-gated build order documented; current layer clearly defined
- [ ] Cross-experiment pooling (if active) applies only to standardized outcomes

---

## Literature

- Snap HTE Platform (arXiv 2512.03060) — "platform > single model"; incremental
  retraining; τ̂ as data asset
- LinkedIn CPOG (arXiv 2505.09847) — three-layer B2B production architecture;
  graph-structured causal estimation
- Wang et al. (2026, arXiv 2604.02472) "VALOR" — B2B causal lead scoring at
  scale; salesperson-level calibration
- Bompaire et al. (2024, WWW / Spotify) — LOPE + Impatient Bandits; delayed
  reward integration in production
- Kiyohara et al. (2021) "Open Bandit Pipeline" — OBP reference for large
  action space OPE
- Farias et al. (2024) "Netflix Surrogate Index Benchmark" — 200-experiment
  validation of surrogate screening
