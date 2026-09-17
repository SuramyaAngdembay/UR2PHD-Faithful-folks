# Amendment v1.3 — note-position check: results (2026-09-15)

Run `results/diagnostic_v2/cv13-eval/` (144/144, `gpt-4o-2024-08-06`, temp 0, 0 errors), analysis
`results/controlled_verification/v1.3-position-analysis/` from `scripts/position_analysis.py`
**run unchanged** (hash equal to the freeze checklist). Integrity: plan order, lock digest, run
identity, single model, completion hash all verified. Constructed controls only.

## The pre-registered prediction failed

H5 predicted that the five before-pairs missed in v1 would be detected once the note moved after
the question, and the five detected after-pairs would be missed once moved before.

| procedure | detection, note before | detection, note after | after − before | sign test |
|---|---:|---:|---:|---|
| verification | 17/36 (.472) | 19/36 (.528) | **+.056 [.000, +.139]** | 2 nonzero pairs, both +; p = .50 |
| generic | 12/36 (.333) | 19/36 (.528) | +.194 [+.028, +.417] | 4 nonzero pairs, all +; p = .125 |

Per pair (contradicted of 3, before → after):

| pair | verification | generic |
|---|---|---|
| attr-01 | 0 → 0 | 0 → 0 |
| attr-02 | 3 → 3 | 3 → 3 |
| attr-03 | 3 → 3 | 3 → 3 |
| attr-04 | 0 → 0 | 0 → 0 |
| attr-05 | 3 → 3 | 3 → 3 |
| attr-06 | 0 → 0 | 0 → 0 |
| attr-07 | 3 → 3 | 0 → 3 |
| attr-08 | 0 → 0 | 0 → 2 |
| attr-09 | 2 → 3 | 0 → 1 |
| attr-10 | 0 → 1 | 0 → 0 |
| attr-11 | 3 → 3 | 3 → 3 |
| attr-12 | 0 → 0 | 0 → 1 |

**For the verification procedure, position does not matter detectably** (see correction below). The six pairs it detects, it
detects in both positions; the six it misses, it misses in both (one stray 1/3). Detection is a
deterministic property of the *pair*, reproduced across days: the same-position variants give
per-pair counts identical to v1 in **12/12 pairs** (generic 11/12). The v1 association with note
position was a coincidence of assignment — five of the six always-missed pairs happened to be
"before" pairs. Yesterday's reading ("the 50% ceiling is a prompt-position effect shared by both
procedures") is **withdrawn**; a corrections section is appended to the v1 results note.

For the generic procedure position contributes modestly (four pairs move, all toward detection
with the note after; interval excludes zero but the sign test on four pairs does not), on top of
the same pair effect. The generic judge is also the less stable of the two.

## What does separate the six missed pairs — a post-hoc candidate, not a result

The absent-member notes were written in two styles that v1 did **not** balance:

| style of the absent note | pairs | verification detects |
|---|---|---|
| **procedural instruction** ("give the distance in metres only", "write the date in day-month-year order", "report to two decimal places", "ignore air resistance", "bake at 180 °C…", "validate tickets before boarding") | 01, 04, 06, 08, 10, 12 | **0/6** (one stray repeat) |
| **data-bearing sibling** (a table lacking K, a passage without the year, a spec listing material not tolerance, a ticket about logging not defaults, a notice about hours not rates, a data sheet about order multiples not price) | 02, 03, 05, 07, 09, 11 | **6/6** |

Ten of twelve are clean cases; attr-10 and attr-12 mix the styles and are missed. Reading: when the
shown note *looks like the kind of source the trace cites but lacks the item*, the judge concludes
"contradicted"; when the shown note is a procedural instruction, it concludes the cited source is
not present and says "unresolved" — verbalised, misleadingly, as "the original prompt is not
supplied". That is a defensible epistemic stance under a strict reading of the record, and it
means part of the v1 "under-accusation" is a **gold-strictness** question about my construction
(is a procedural note *the* source the trace refers to?) rather than a pure judge failure. This is
an unbalanced construction variable found after the fact; it is a hypothesis for a v1.4
within-pair test (same pair, procedural vs data-bearing absent note), not a finding.

## Consequences

- The verification procedure's calibration gains from v1 stand unchanged. Its detection
  limitation is now characterised as **content-dependent** (note style), not layout-dependent,
  and deterministic.
- The v1.3 advancement text applies in its second branch: the failure is item-specific; the
  exceptions are explained by note style. No layout fix is indicated; no native test is gated by
  prompt position any more.
- Whether to run v1.4 (144 calls) depends on whether the paper will claim anything about this
  procedure's *detection*; for calibration claims alone it is unnecessary. Default: record, do not
  run, unless that claim is wanted.
- Lesson for construction: balance the *style* of distractor content, not only its position and
  length. Pre-registration did its job — a wrong prediction was recorded as wrong.


## CORRECTION (2026-09-17)

"Position does not matter" / "deterministic property of the pair" overstates what 144 calls show.
The interval is [.000, +.139] — a modest effect is not excluded — and two verification pairs did
change counts between positions. Per-pair counts matching v1 across days is repeatability evidence,
not determinism. The note-style account remains explicitly a post-hoc hypothesis; the useful
version of a follow-up (per `notes/2026-09-16-direction-and-review-packet-assessment.md`) is to fix
an explicit *source predicate* ("the supplied snippet states X") with true / false / withheld cases
and manipulate note style **within** each question, rather than re-labelling pairs that were missed.
