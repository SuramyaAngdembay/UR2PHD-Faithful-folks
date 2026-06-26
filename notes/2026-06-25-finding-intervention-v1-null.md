# Finding (2026-06-25): targeted-intervention v1 is null (and why)

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
