# Finding (2026-06-25): `soft_faithfulness` is answer-tracing; the human label is the real target

> **⚠️ CORRECTION (2026-07-16):** The `faithful_type` regime labels used in this note are INVERTED
> relative to the released FaithCoT data: in the data, **ft1/ft2 = INCORRECT-answer regime, ft3/ft4 =
> CORRECT-answer regime** (the repo README's pairing is wrong; verified per-domain vs parsed answers and
> by reproducing the paper's own statistics; independently reported in FaithCoT-BENCH issue #3).
> All numbers in this note are valid; wherever it says "correct-answer regime / post-hoc-on-correct
> (ft1v2)" read "incorrect-answer regime". See `notes/2026-07-16-data-validation.md`.


*Run on Aquaman over the official FaithCoT-Bench data (`github.com/se7esx/FaithCoT-BENCH`,
cloned to `~/ur2phd/upstream/FaithCoT-BENCH`, extracted to `/tmp/fc`). Scripts:
`scripts/analyze_human_label.py`.*

## 1. Provenance resolved (the spec §4 blocker)
- Per the repo README, **`soft_faithfulness` / `hard_faithfulness` = step-removal AUC**:
  "progressively masking reasoning steps and observing shifts in answer probabilities."
  They are summaries of `intermediate_answer_probabilities` — i.e. **answer-tracing**.
- Dikshant's PoC headline (ρ=0.87, `avg_impact` vs `soft_faithfulness`) is therefore
  **mechanically circular**: both sides are summaries of the *same* probability trajectory.
  It is ≈ a self-correlation, not evidence the premise DAG predicts faithfulness.

## 2. The real ground truth exists in the data (Dikshant's loader skipped it)
Each `response_*.json` has **top-level human-annotation fields**, separate from the
computed `sample_0.soft/hard_faithfulness`:
- **`unfaithfulness`** ∈ {0=faithful, 1=unfaithful} — the human binary label (**our target**)
- `faithful_type` ∈ {1..4} (correct×faithful matrix), `faithful_score` ∈ {1..5} (Likert),
  `hardness` ∈ {0..3}
- Coverage: ~389/400 of the 4 PoC groups annotated; **39% unfaithful** pooled (healthy,
  vs the misleading 19% from Dikshant's `soft≥0.5` threshold on the circular metric).
- Full FINE-CoT on the box: aqua/logiqa/truthfulqa (100 each) + HLE_BIO (41), × 4 models
  (llama-3.1-8b, Qwen2.5-7B, gpt-4o-mini, gemini-2.5-flash).

## 3. Honest, NON-circular baseline — predictors vs the HUMAN `unfaithfulness` label (AUROC)

| Group | n | %unfaith | soft_faith | hard_faith | avg_impact | **correct** |
|---|---|---|---|---|---|---|
| **POOLED** | 389 | 39% | 0.727 | 0.669 | 0.693 | **0.757** |
| truthfulqa/llama-3.1-8b | 90 | 44% | 0.662 | 0.550 | 0.642 | 0.782 |
| truthfulqa/Qwen2.5-7B | 99 | 34% | 0.722 | 0.671 | 0.725 | 0.721 |
| logiqa/llama-3.1-8b | 100 | 44% | 0.673 | 0.625 | 0.620 | 0.739 |
| logiqa/Qwen2.5-7B | 100 | 32% | 0.823 | 0.815 | 0.747 | 0.779 |

## 4. Implications (these reframe the project)
1. **The 0.87 was illusory.** Against the *human* label, the answer-tracing metrics reach
   only **AUROC ≈ 0.69–0.73 pooled** — a moderate, noisy predictor, not 0.87.
2. **Correctness is the strongest single predictor (AUROC 0.757).** The Bentham (TMLR'24)
   "unfaithfulness = disguised accuracy" confound is real and large here. **Any faithfulness
   method must beat correctness AND answer-tracing, with correctness controlled.** This is
   now the explicit bar for our intervention experiment (Exp 1, H2).
3. **Polarity surprise:** `soft_faithfulness` is *higher* for human-**unfaithful** traces
   (pooled mean 0.351 vs 0.166 faithful) — it anti-aligns with its nominal "high=faithful"
   meaning. So Dikshant's `soft≥0.5 ⇒ faithful` split was likely **polarity-inverted** too.
   Worth confirming against the step-removal AUC definition in the pipeline code.
4. **Target locked:** Exp 1 (graph-targeted counterfactual interventions) will be evaluated
   against `unfaithfulness` (human), with `correct` + `avg_impact` as controlled baselines.

## 5. Caveats
Point estimates only (n≈90–389, no CIs / significance yet); AUROC orientation chosen to be
≥0.5 per predictor. Confirm `soft_faithfulness` polarity from the pipeline before quoting the
inversion as a result.

## 6. Data/compute location
Aquaman (`ssh aquaman-ts`): repo at `~/ur2phd/upstream/FaithCoT-BENCH`, data extracted at
`/tmp/fc/faithcot/<domain>/<model>/response_*.json`. Env: `~/ur2phd-venv` (torch cu121,
transformers 5.12, bitsandbytes; both 3070s run 4-bit 8B at ~5.8 GB peak).
