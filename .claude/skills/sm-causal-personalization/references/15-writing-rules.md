# 15 · Language, Tone, and Writing Rules

## Purpose

Writing rules for every output — chat, reports, treatment cards. The audience
is a business decision-maker who does not yet trust the analysis. Trust is
earned by checkability (ref 16) and by prose that says exactly what is known,
assumed, and unknown — in that order of prominence.

---

## Rule 1 — Language policy

Respond in the user's language (detected from their most recent message).
Technical terms, IDs, and verdicts stay English regardless: HTE, CATE, OPE,
Qini, AUUC, CAC, ROAS, holdout, propensity, T01/D1/C1, viable/undetermined,
GO/NO-GO. Currency and number formats follow the market in scope.

## Rule 2 — Numbers follow ref 16, with no prose escape hatch

The provenance contract (sourced / assumed / derived / missing) applies to
prose, not just tables. A sentence may state a number only if that number
exists in the registry; the generator's linter warns on currency amounts that
match no registry value. Never introduce a number in prose to make a sentence
more persuasive.

Specific bans carried over from hard experience:

- KOL/creator fees are never stated without "estimate pending direct quote"
- ROI/incrementality is never asserted without holdout or identification
  strategy — and never as a bare range in a table
- Platform ROAS is never called ROI; unmodified "CAC" is never used where
  "incremental CAC" is meant

## Rule 3 — Falsifiability obligation

Every major claim carries its overturn condition, every recommendation its
kill line:

> Wrong: "Social prospecting is not recommended."
> Right: "Social prospecting fails the screen (best-case benchmark CAC 47 RON
> vs 35.8 ceiling). This flips if margin is ≥ 40% or mesh attach exceeds 30%."

A report that cannot state what would change its mind is advocacy. The decision
memo's `overturn_conditions` field is mandatory, sourced from the top of the
sensitivity table.

## Rule 4 — Pyramid structure

Conclusion first, at every scale: the report leads with the memo; a section
leads with its finding; a paragraph leads with its point. The reader who stops
after one screen, one sentence, or one row should leave with a correct (if
coarse) picture — never a misleading one.

## Rule 5 — Honest-state vocabulary

| Say | Don't say |
|-----|-----------|
| "undetermined — interval spans the ceiling; pull CPC data first" | a confident midpoint |
| "missing; obtainable from X at zero cost" | a placeholder guess |
| "open challenge, blocks budget line T03" | silence about an unanswered objection |
| "this is the report's weakest point: …" | hoping the reader won't notice |

Uncertainty stated precisely reads as competence. Uncertainty papered over
reads as either ignorance or deception — and the reader can't tell which,
so they assume the worse.

## Rule 6 — Anti-slop list

Delete on sight; if removal changes nothing, the phrase was noise:

"it is worth noting that" · "as mentioned above" · "in conclusion" ·
"it is important to emphasize" · "comprehensive approach" · "this is a
complex topic" · "many factors to consider" · "leverage synergies" ·
"best-in-class" · "holistic view" · "delve into"

Also banned: passive evasions ("it was found that"), hedging chains ("may
potentially possibly"), and nominalization stacks ("operationalization of
the utilization").

## Rule 7 — Form budget

- Tables: max 4 columns; comparison of ≥ 3 items only. Otherwise prose or cards.
- One callout per section — for the single decision or the single blocking fact.
- Recommendation sentences ≤ 25 words; mechanism explanations may run longer.
- Pills are rationed (ref 12): verdict, channel verdicts, challenge statuses,
  block stamps. Nothing else gets a capsule.

## Rule 8 — Maturity honesty

State the maturity level (L0–L3) where conclusions are drawn, and respect its
ceiling: L0 supports trial design and channel screens, not CATE claims; L1
supports channel-level ATE, not per-segment optimization; L2 supports policy
comparison via OPE; only L3 supports continuous-optimization claims. A report
must never read one level more mature than its data.

---

## Pre-delivery checklist

- [ ] User's language; technical terms English
- [ ] Every prose number exists in the registry (lint clean)
- [ ] Every major claim has an overturn condition; every budgeted action a kill line
- [ ] Conclusion-first at report, section, and paragraph level
- [ ] At least one honestly-stated unknown (real projects always have them)
- [ ] Anti-slop list applied; form budget respected
- [ ] Maturity stated and not exceeded
