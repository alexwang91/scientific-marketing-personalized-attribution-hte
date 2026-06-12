# 12 · HTML Report Output: The Decision Memo Contract

## Purpose

Specifies the deliverable report format. The governing idea:

> **A good report is a document that lets someone who does not trust you
> check your reasoning.**

A report is a display of reasoning, not a display of conclusions. Credibility
comes from checkability, not from labels claiming credibility. Estimation
rules live in ref 16; this file covers structure and rendering.

---

## The Six Sections (replaces the old 15)

```
1. Decision Memo      ONE SCREEN: verdict badge + thesis + decisions
                      (now / at checkpoint / never) + overturn conditions
                      + the report's own weakest point
2. The Math           Derivation chains (unit economics → CAC ceiling)
                      → sensitivity table → channel viability screen
3. Actions            Cards (4 fields: mechanism / guardrail / test / budget)
                      only for screen survivors; rejected options listed
                      with one-line reasons; BLOCKED stamps live here
4. Adversarial Review Challenge table with resolved / open / open-blocking
                      status; open-blocking links to stamped actions
5. Test Plan          Prediction–test–kill-line–decision-date cards
                      + power_analysis.py bridge output
6. Evidence & Gaps    Sourced facts (with access dates) + assumption
                      register + Missing ledger sorted by sensitivity
```

Removed from v1, deliberately:
- The empty "H-Main Breakdown" pass-through section (template smell)
- The standalone KOL procurement section — it only exists when unit economics
  support it; when they don't, KOL appears once in rejected options
- The 4-tag evidence legend — replaced by the provenance marker system
- The semantic heatmap as a default section — dimension detail is only earned
  **after** a channel passes the viability screen; it can attach as an appendix
  for viable channels, never before

### Why the order matters

The report is a pyramid: a reader gets the conclusion in 30 seconds (section 1),
the reasoning in 3 minutes (section 2), and full auditability in 30 minutes
(sections 3–6). The single most important insight must be the first sentence
of the thesis — not buried in a reviewer table on page 4.

---

## Section 1 requirements (Decision Memo)

| Field | Rule |
|-------|------|
| `verdict` | go / no-go / conditional — rendered as a badge; no hedged fourth option |
| `thesis` | ≤ 3 sentences; contains the central number(s); must be falsifiable |
| `decisions` | Each tagged now / checkpoint / never. "Now" items should mostly be zero-cost data pulls |
| `overturn_conditions` | Taken from the top of the sensitivity table. A report that cannot say what would change its mind is advocacy |
| `weakest_point` | The report names its own weakest link before the reader finds it |

---

## Number rendering (enforced by generate_report.py)

Every number lives in the config's central `numbers` registry with provenance
sourced / assumed / derived / missing (ref 16). The generator **fails the build**
on any violation: unsourced "sourced" numbers, value-carrying "missing" numbers,
formulas referencing unregistered inputs, circular derivations.

- Derived numbers render as three-line chains: symbolic formula → substituted
  values with provenance markers → result.
- Range inputs propagate as intervals (corner evaluation). Never midpoint.
- Missing numbers render as a gray dashed placeholder. Never a guessed value.
- Markers are superscripts (`S/A/D/M`), not pills — they don't count against
  the pill budget.
- A prose linter warns when body text contains a currency amount matching no
  registry value.

---

## Pill budget and verdict vocabulary

Pills (colored capsules) are rationed because 50 tags = 0 tags. Only four
families exist:

| Family | Values |
|--------|--------|
| Report verdict | GO / NO-GO / CONDITIONAL (exactly one) |
| Channel verdict | viable / not-viable / undetermined / role-only |
| Challenge status | resolved / open / open-blocking |
| Block stamp | ⊘ BLOCKED by C{n} |

Target: **fewer than 20 pills in a full report.** `undetermined` is a legal and
common channel verdict — see ref 16 on why honest blanks beat fabricated
completeness. `role-only` marks channels evaluated for a non-acquisition role
(e.g., review content that answers an objection) where CAC math doesn't apply.

---

## Readability budget

- Tables: **maximum 4 columns.** More fields → cards (the generator renders
  actions and test plans as cards natively).
- One callout per section, maximum.
- Derivation chains in monospace blocks; prose in sentences.
- Language follows the user (ref 15); markers, verdicts, and IDs stay English.

---

## Short-report mode

If the pipeline terminated at the viability screen (ref 13, stage 3), config
carries a `termination` block and the generator renders only sections 1, 2, 6
plus a termination notice. **A short report is a success state**, not a
failure: "the math says don't spend; here are the levers that would change
the math" is often the most valuable deliverable.

---

## Usage

```bash
python scripts/generate_report.py --config config.json --output report.html
python scripts/generate_report.py --config config.json --validate-only   # contract check
python scripts/generate_report.py --demo > demo.html                     # minimal schema demo
```

Worked example config: `examples/ax3-romania-config.json`.

---

## Acceptance checklist (apply to every generated report)

- [ ] First screen alone tells the verdict, the central math, and the next action
- [ ] Zero numbers without provenance — `--validate-only` passes, no lint warnings
- [ ] At least one honest `undetermined` or Missing entry on any real project
      (a registry with no unknowns is lying)
- [ ] Unresolved blocking challenges are visible and stamp their dependent actions
- [ ] Sensitivity table present; Missing ledger sorted by it
- [ ] Every budgeted action has a kill line and a decision date
- [ ] Pill count < 20; no table wider than 4 columns
