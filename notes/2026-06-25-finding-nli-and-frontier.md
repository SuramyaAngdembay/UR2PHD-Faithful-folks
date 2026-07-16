# Finding (2026-06-25): NLI step-support null + the real open frontier

> **⚠️ CORRECTION (2026-07-16):** The `faithful_type` regime labels used in this note are INVERTED
> relative to the released FaithCoT data: in the data, **ft1/ft2 = INCORRECT-answer regime, ft3/ft4 =
> CORRECT-answer regime** (the repo README's pairing is wrong; verified per-domain vs parsed answers and
> by reproducing the paper's own statistics; independently reported in FaithCoT-BENCH issue #3).
> All numbers in this note are valid; wherever it says "correct-answer regime / post-hoc-on-correct
> (ft1v2)" read "incorrect-answer regime". See `notes/2026-07-16-data-validation.md`.


*Harness: `scripts/nli_step_support.py` (roberta-large-mnli, model-agnostic, 389
truthfulqa+logiqa traces). Per-step NLI(question+prior steps -> step) -> support aggregates.*

## Result (AUROC vs human `unfaithfulness`)
| feature | AUROC | AUROC\|cor (ft1v2) | AUROC\|inc (ft3v4) | pSpear\|soft |
|---|---|---|---|---|
| soft (answer-tracing) | 0.727 | 0.509 | 0.710 | +0.000 |
| n_unsup | 0.581 | 0.506 | 0.596 | +0.042 |
| min_ent | 0.531 | 0.566 | 0.557 | +0.084 |
| mean_supp | 0.521 | 0.545 | 0.503 | −0.011 |

## Verdict: NLI step-support is weak and does NOT add to answer-tracing
- Best support feature AUROC 0.581 vs `soft` 0.727; partial Spearman | soft only +0.04–0.08.
- **Conceptual reason:** post-hoc rationalizations are *locally coherent* — each step entails
  from the prior ones; they just don't causally drive the answer. **Local entailment ≠
  faithfulness**, so NLI is structurally blind to the dominant failure mode.
- This is the **4th method** to fail to beat answer-tracing (after DAG structure, intervention
  v1, intervention v2).

## The real open frontier (corrected, using annotated `faithful_type`)
- Earlier "incorrect regime is the open one" was an artifact of the noisy `parsed==label`
  correctness flag. With the annotated split:
  - **ft1 vs ft2 (CORRECT answers: faithful vs post-hoc rationalization): AUROC ≈ 0.51 for
    EVERY signal** (soft, NLI, interventions, structure). This is the genuinely open problem.
  - ft3 vs ft4 (incorrect answers): `soft` does fine (0.71); `soft`'s headline 0.727 is
    carried by this regime.
- **Sharp problem statement:** *is a correct answer's stated reasoning genuine, or a post-hoc
  story?* No deployable signal we tested detects this above chance.

## Strategic implication
Instance-level faithfulness detection on FaithCoT is **saturated by answer-tracing** (its own
metric); four orthogonal method families fail to beat or augment it. The "beat soft" method
path is exhausted. Highest-value pivots:
1. **Analysis / reframing paper** anchored on: (a) the negative results (structure /
   intervention / NLI all fail); (b) the **post-hoc-on-correct (ft1v2) frontier** at chance
   for all signals; (c) the `soft` **polarity inversion** (higher for unfaithful). Novel,
   honest, low-risk.
2. **Localization** (use FaithCoT step-level evidence) — a different, less-saturated task.
3. (Higher-effort) **white-box / mechanistic** detection of post-hoc rationalization on
   correct answers — the one thing black-box signals can't see (would need open-weights probes
   / activation analysis on the ft1v2 cases).
