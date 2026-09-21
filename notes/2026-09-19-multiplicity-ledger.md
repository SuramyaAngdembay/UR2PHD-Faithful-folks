# Multiplicity ledger (2026-09-19)

> **CORRECTED 2026-09-21 — see `2026-09-21-independent-code-audit.md` finding 9.** The BonaFide judge inversion is **not** "the one pre-registered headline": the registered hypothesis was the opposite (judge above chance) and it failed. 0.419 is the outcome of a registered analysis, not a confirmed registered claim; the correction-family argument applies to the analysis, the framing below does not. Family sizes were counted from this ledger's own rows, three tests appear twice as mirrors, and "every null below 2.1" skips question-only/correct at z = +2.10. No verdict flips; the answer-tracing regime gap (z = 2.67) is fragile to family size.


Action 3 of `notes/2026-09-19-holdout-and-phacking-audit.md`, which required this "before anything
enters the manuscript". Artefacts: `scripts/multiplicity_ledger.py`,
`results/multiplicity_ledger.json`.

## Method, and the limit on it

The paper reports percentile bootstrap intervals, not standard errors. To put claims on one scale
the ledger converts each interval to an approximate z via `SE = (hi - lo) / 3.92`. **That assumes
an approximately normal, symmetric sampling distribution, so this is a triage tool, not a
re-analysis.** It is least trustworthy for AUROCs near 0 or 1 and for small-n cells where the
percentile intervals are visibly asymmetric. **A claim landing near a threshold here needs a real
corrected test; a claim far from one can be read off.** Exactly one claim lands near a threshold,
and it is flagged below.

## Inventory

From a full pass over `paper/arr/main.tex`: **83 distinct inferential claims**, about **115
interval-bearing estimates** once paired rows are expanded. Of these:

- **7 pre-registered** — the BonaFide external panel, with endpoints, population, margin and
  analysis committed before any value was computed.
- **2 explicitly disclaimed as post-hoc** — the BonaFide post-unblinding controls.
- **1 explicitly disclaimed as not pre-registered** — the GRACE check.
- **73 carry no pre-registration statement either way.**

Corrections the paper already applies: Bonferroni over the 8-cell transfer grid, and
selection-corrected layer permutation for every probe claim. It explicitly declines a correction
family for ΔAUROC comparisons, calling them "descriptive, not a confirmatory family".

## The central result: correction family is a choice, and ours is defensible

Two thresholds bracket the question. Within-family Bonferroni is the standard practice. A single
whole-paper Bonferroni over all 115 estimates, needing |z| > 3.52, is a stress test no paper
actually applies, included here only to see what breaks.

**Every abstract headline clears whole-paper Bonferroni except one.**

| abstract claim | z | own family | whole paper |
|---|---|---|---|
| metric inversion, 0.349 | -7.05 | pass | pass |
| judge blind regime, 0.679 | +7.97 | pass | pass |
| judge correct regime, 0.830 | +15.04 | pass | pass |
| regime gap, 0.152 | +4.88 | pass | pass |
| BonaFide step count, 0.878 | +29.63 | pass | pass |
| BonaFide instruct-only inversion, 0.332 | -6.86 | pass | pass |
| **BonaFide judge inversion, 0.419** | **-3.45** | **pass** | **fails (needs 3.52)** |

**The one headline that needs its correction family to be drawn honestly is the one claim in the
paper that was pre-registered.** Its family is the 7-test BonaFide panel, needing |z| > 2.69, which
it clears with room. That is not a lucky escape; it is the entire argument for pre-registration.
A confirmatory claim committed in advance does not inherit the multiplicity of exploratory work
done elsewhere in the same manuscript, and lumping them together would punish the one panel that
was done right.

**It is also the single claim to state most carefully.** At z = -3.45 it is the only headline
close enough to a threshold that the normal approximation could matter, and its interval
[0.372, 0.464] sits nearer 0.5 than any other headline. The paper should keep its pre-registration
prominent beside it rather than treating it as one result among many.

## What passes its own family but not the stress test

Secondary claims, all correctly framed as secondary already:

| claim | z | family threshold |
|---|---|---|
| prefix-instability regime gap, +0.178 | 3.47 | 2.39 |
| Llama math-sycophancy transfer, +0.185 | 3.49 | 2.73 |
| trace length in correct regime, 0.622 | 3.44 | 2.91 |
| trace length overall, 0.575 | 3.23 | 2.81 |
| NLI unsupported steps, 0.569 | 2.94 | 2.81 |
| answer-tracing regime gap, +0.136 | 2.67 | 2.39 |

The transfer-grid cell is the one worth watching, because it is the paper's only positive cell out
of eight and the manuscript already rests a claim on it. **The paper's own framing — Bonferroni
over the eight-cell grid — is the correct family and it passes.** It would not survive a whole-paper
correction, which is a reason to keep describing it as one significant cell in a grid, never as a
standalone finding.

## Nulls

Every null in the ledger is comfortably null: |z| below 2.1 throughout, most below 1.5. The
question-only judge ablation behaves exactly as intended (-0.81, -1.42), which is the designed
negative control passing. **No null in the paper is a near-miss being reported as absence**, and
the manuscript's repeated "not detected, not absent" phrasing is the right description of them.

## What this ledger does not do

- It does not address the **garden of forking paths**, which the p-hacking audit correctly calls
  the real residual risk. Counting the tests we ran says nothing about the analyses we could have
  run. No arithmetic fixes that; only pre-registration does, and only 7 of 115 estimates have it.
- It does not cover the two `\input` files (`generated/bonafide_reconciliation`,
  `generated/grace_reanalysis`), whose statistics were not inventoried.
- It does not cover the **new** exploratory work from today (generator identity, self-preference,
  stratified regime gaps). Those carry their own pre-registered family of three primary tests at
  Bonferroni 0.0167, recorded in `self-preference-spec.md`, and everything else in them is labelled
  exploratory.

## Action

Nothing in the manuscript needs to be withdrawn or weakened on multiplicity grounds. Two changes
are warranted:

1. **State the correction family for each claim family explicitly in the paper**, rather than
   leaving 73 of 115 estimates with no pre-registration statement. The families are already
   coherent; they are just not named.
2. **Keep the pre-registration of the BonaFide panel adjacent to its headline number.** It is doing
   real work there, and a reader cannot tell that from the current placement.
