# Finding (2026-06-25): targeted-intervention v1 is null (and why)

> **⚠️ CORRECTION (2026-07-16):** The `faithful_type` regime labels used in this note are INVERTED
> relative to the released FaithCoT data: in the data, **ft1/ft2 = INCORRECT-answer regime, ft3/ft4 =
> CORRECT-answer regime** (the repo README's pairing is wrong; verified per-domain vs parsed answers and
> by reproducing the paper's own statistics; independently reported in FaithCoT-BENCH issue #3).
> All numbers in this note are valid; wherever it says "correct-answer regime / post-hoc-on-correct
> (ft1v2)" read "incorrect-answer regime". See `notes/2026-07-16-data-validation.md`.


*Harness: `scripts/intervention_harness.py` (heuristic DAG target, binary answer-flip
re-derivation, local Llama-3.1-8B, 188 LLaMA traces). Results:
`~/intervention_results.json` on Aquaman.*

## Result
`g = targeted_change − random_change` vs human `unfaithfulness` (AUROC):

| subset | n | %unfaith | **g** | tchg | soft (baseline) |
|---|---|---|---|---|---|
| POOLED | 188 | 45% | 0.534 | 0.505 | 0.672 |
| INCORRECT (Type 3v4) | 91 | 71% | **0.505** | 0.504 | 0.581 |
| CORRECT (Type 1v2) | 97 | 20% | 0.580 | 0.507 | 0.702 |

mean g: faithful −0.048, unfaithful −0.018.

## Interpretation — null, but it indicts the *setup*, not (yet) the hypothesis
- `g` ≈ chance everywhere; **0.505 in the incorrect regime** we targeted. Answer-tracing
  (`soft`) still wins. So v1 provides **no interventional signal**.
- **Diagnostic:** `g` is *more negative* for faithful traces → removing the heuristic
  "load-bearing" step changed the answer **less** than removing a random step. The
  heuristic DAG is selecting **anti-load-bearing** steps. This is the same crude-extraction
  failure seen in the observational test, now confirmed causally.
- Coarse metric: binary answer-flip (mean |g| ≈ 0.05) — single-step removal rarely flips a
  short multiple-choice answer, so the measure is insensitive.

## The pattern (3 nulls for DAG-based signals)
1. Observational DAG structure vs human label → null (AUROC 0.51–0.59).
2. Targeted intervention (heuristic) → null (this).
3. Only **answer-tracing** carries signal (~0.67–0.73), and it is **non-novel** and **at
   chance in the incorrect regime** (the regime we wanted to own).
Common thread: everything that uses the **heuristic** premise DAG fails; the one thing that
works never touches the DAG.

## Decision gate (next)
Before declaring the premise-DAG/intervention approach dead, run **one clean test** that
removes the two known confounds:
1. **LLM/PARC premise extraction** (not heuristic) → genuinely load-bearing target selection.
2. **Continuous probability-shift metric** (option-logit shift), not binary flip; consider a
   stronger intervention (remove load-bearing step + its descendants, or negate it).
Re-run on the incorrect regime. **If still null → pivot decisively** (per-step
premise-grounded NLI/evidence verification, or reframe the contribution away from the DAG).
If it shows signal → that is the paper.

## Caveats
Heuristic target selection (known weak); binary metric; 2 random controls; n=91 in the key
incorrect subset (noisy); LLaMA traces only (Qwen pass pending).


> ## ⚠️ REGIME LABELS IN THIS FILE CONTRADICT ITS SIBLING (flagged 2026-09-19)
> This file and `2026-06-25-finding-intervention-v2-bury.md` report the **same 188-trace pool**
> (POOLED n=188, 45% unfaithful, soft 0.672) but assign the regime names **crosswise**:
>
> | subset composition | this file calls it | the sibling calls it |
> |---|---|---|
> | ~71% unfaithful, soft ≈ 0.58 | INCORRECT (Type 3v4) | CORRECT (ft 1v2) |
> | ~20% unfaithful, soft ≈ 0.71 | CORRECT (Type 1v2) | INCORRECT (ft 3v4) |
>
> Both predate the 2026-07-16 label-semantics correction, so both use the README's inverted
> ft pairing. **`CLAUDE.md`'s blanket rule — "wherever they say correct-answer regime, read
> incorrect-answer regime" — is therefore UNSAFE for these two files**, because applying it
> yields opposite conclusions for the same subset. Under the verified data-side coding
> (ft1/ft2 = incorrect-answer regime), the **~71%-unfaithful subset is the true INCORRECT
> regime**, consistent with unfaithfulness concentrating in wrong answers.
>
> Scope of the damage: the *nulls* are unaffected — intervention g is weak in both subsets on
> either labelling (0.505/0.580 here, 0.606/0.554 in the sibling), so the "interventions are
> null/weak" conclusion stands. Any **regime-stratified** reading of these two tables is not
> reliable. The manuscript does not draw on them: its regime-stratified intervention figures
> come from `results/audit_corrected.json` (correct regime 0.6591, incorrect 0.4811), which
> postdates and supersedes the correction. See `notes/2026-09-19-holdout-and-phacking-audit.md`.
