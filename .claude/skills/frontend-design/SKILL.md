---
name: frontend-design
description: >
  Visual design methodology for creating distinctive, non-templated web UI.
  Trigger when the user asks to design, redesign, or improve the look of a
  web page, HTML report, dashboard, or component — especially when the current
  result looks generic, AI-generated, or too academic.
  Source: https://github.com/anthropics/skills/tree/main/skills/frontend-design
---

# Frontend Design Guidance

## Core Philosophy

**Ground every decision in the subject.** Before picking a color or typeface,
answer three questions:
1. What is the concrete subject? (not "a report" — what *kind* of report, for whom)
2. Who is the audience and what is their emotional state when they arrive?
3. What is the page's single job? (one verb + one object)

The product's own world — its materials, vernacular, visual artifacts — should
inform the palette, type, and layout. A GPS running watch decision memo lives in
a different world than a fintech dashboard or a medical SaaS.

---

## Two-Pass Process

**Pass 1 — Design Plan (before writing any code)**

Write a compact brief covering:
- **Palette**: 2–3 colors max. Name the emotional register each carries.
- **Typefaces**: Display face (headings, verdict) + body face. Pair deliberately,
  not by reflex.
- **Layout concept**: What is the spatial logic? Pyramid? Grid? Card stack?
- **Signature element**: The one thing the reader will remember. Spend boldness
  here; keep everything else disciplined.

**Pass 2 — Critique before build**

Ask: *Could this design belong to any other project?* If yes, it is too generic.
Push the palette, the type, or the signature element further toward the subject.

---

## Typography

- Pair display and body deliberately, not by default.
- Display face carries personality; body face carries readability.
- Size contrast is the primary tool for hierarchy — not bold alone.
- Monospace is for code and precise derivations; prose never uses monospace.

---

## Color

- Start with the subject's world, not a trend.
- One accent color. Everything else is neutral.
- Avoid the three AI-generated clustering defaults:
  1. Cream background + serif + terracotta accents
  2. Near-black background + acid green/yellow accents
  3. Broadsheet newspaper layout (dense columns, thin rules everywhere)
- Verdicts and status pills should use color with meaning: green = proceed,
  amber = conditional/caution, red = stop/blocked.

---

## Structure

Structure is information. Every structural device — numbering, dividers, labels,
eyebrows — should encode something true about the content, not decorate it.

- Section numbers encode sequence and dependency, not decoration.
- Tables are for comparison. If you have one row, use prose or a card.
- Cards are for parallel objects (Treatment Cards, test plans).
- The most important fact goes first — always. The reader who stops after one
  screen should leave with a correct (if coarse) picture.

---

## Restraint

> "Spend your boldness in one place."

Let the signature element be memorable. Keep everything else disciplined and
subordinate. Remove non-functional decoration. If removing an element changes
nothing about comprehension, remove it.

**Animation**: Only when it aids comprehension. Extra animation reads as
AI-generated; static reads as confident.

---

## Writing in Design

Copy is design material.

- Active voice. Specific language. No hedging chains.
- Controls say exactly what happens: "Run validation" not "Submit".
- Errors and empty states are directional, not apologetic.
- Every number in a visual carries its provenance marker — not hidden in a
  footnote, not missing.
- Academic language signals "I am protecting myself." Business language signals
  "I am helping you decide." Choose the latter.

---

## Applied to Decision Memos

The specific failure modes of analytically-generated reports:

| Academic smell | Fix |
|---------------|-----|
| "This analysis supports X but not Y" disclaimers | State maturity level once at the top; don't repeat in every section |
| Methodology explanation before conclusion | Pyramid: conclusion first, method last |
| Monospace blocks for everything | Monospace for derivation chains only; prose for everything else |
| Every section has an intro paragraph | Lead with the finding; cut the intro |
| 50 evidence tags | Ration pills; use superscript markers for numbers |
| Dense table grid (borders everywhere) | Hairline rules, generous padding, alternating row tint |

---

## Quick Checklist

- [ ] Can I name the subject's world in one noun? (e.g., "GPS running watch")
- [ ] Does the palette come from that world?
- [ ] Is there exactly one signature element?
- [ ] Does the first screen alone give a correct (coarse) picture?
- [ ] Have I removed all non-functional decoration?
- [ ] Does the copy sound like a colleague, not a disclaimer?
