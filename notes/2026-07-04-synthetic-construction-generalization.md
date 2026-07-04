# Synthetic-construction generalization: white-box detectable in BOTH models, but does NOT bridge to real post-hoc (2026-07-04)

*Scripts: `synth_generate.py` (matched genuine/post-hoc CoT), `synth_extract.py` (per-layer
last-token acts + black-box signals), `synth_analyze.py` (probe + baselines + naive bridge),
`synth_bridge.py` (layer-swept, domain-controlled bridge). Results: `results/synth_{llama,qwen}.json`,
`results/bridge_{llama,qwen}.json`.*

## Design
For each math problem (question, gold answer a*), elicit two matched CoT traces from the SAME model:
- **GENUINE** (reason-first): "solve step by step, then answer" → **kept only if the model is correct**.
  Reasoning causally produced the answer ⇒ faithful, correct.
- **POST-HOC** (answer-first): "the correct answer is a*, justify it step by step" ⇒ rationalization
  of a correct answer it was handed ⇒ unfaithful, correct.

Both conditions end at the **same correct answer** ⇒ matched on correctness and final answer; the only
difference is whether reasoning *caused* the answer. This is the FaithCoT **post-hoc-on-correct
(ft1 vs ft2) frontier**, constructed with ground-truth labels, at scale, across datasets (AQuA/GSM8K)
and models. Decoding: sampling (T=0.7, top_p=0.9, rep_penalty=1.1, seed=0) — greedy degenerates into
repetition loops on math; a hard `no_repeat_ngram` ban wrecks arithmetic (tested, both rejected).
Probed context is **symmetric** (question + generated CoT, no "answer is a*" leakage — that lived only
in the post-hoc *generation* prompt), so the signal is how the CoT was produced, not what it contains.

Yields: **Llama** 229 matched pairs (27 AQuA + 202 GSM8K); **Qwen2.5** 277 pairs (60 + 217).

## Result 1 — white-box probe: STRONG in BOTH models (reinforces C1, extends to Qwen)
Detecting post-hoc vs genuine from last-token hidden states (StandardScaler→PCA(50)→LogReg):

| model | best block-layer | 5-fold CV | held-out 70/30 | max-over-layers perm p (n=200) |
|---|---|---|---|---|
| Llama-3.1-8B | 9 | 0.770 | **0.739** | **0.005** |
| Qwen-2.5-7B | 10 | 0.758 | **0.809** | **0.005** |

Both models robustly decodable — including **Qwen, which was n.s. on the noisy FaithCoT human labels
(pilot p=0.32)**. With clean construction labels the internal post-hoc signal is clearly present in
both ⇒ the earlier Qwen null was (at least partly) label-noise / small-n, not absence of signal.

**Cross-dataset transfer within a model (AQuA↔GSM8K, same probe):** Llama aqua→gsm8k 0.661,
gsm8k→aqua 0.728; Qwen 0.719 / 0.721. The synthetic post-hoc axis **generalizes across math datasets.**

## Result 2 — black-box baselines
- **Answer-tracing (soft_faithfulness):** could NOT be computed on synthetic AQuA — the option lists
  here are numeric value strings (`['12','13',…]`), not letter-prefixed, so the single-token letter
  readout has ~0 coverage. (The black-box-at-chance claim already stands on FaithCoT with CIs; not
  re-litigated here.)
- **Surface-feature LR** (n_steps, cot_tokens, n_numbers, hedge/self-ref): Llama **0.639**, Qwen 0.545.
  → Llama's post-hoc CoTs carry a modest *surface* tell. Honest caveat: part of the within-synthetic
  white-box number is surface-correlated. This is exactly why the transfer-to-real test (below) is the
  load-bearing validity check — real annotated post-hoc lacks the synthetic's surface artifacts.

## Result 3 — the FaithCoT(real) ↔ synthetic bridge FAILS (the key validity finding)
**Depth mismatch:** synthetic post-hoc peaks EARLY (Llama block-L9, Qwen L10); real FaithCoT ft1v2
peaks LATE (Llama L29 CV 0.702, Qwen L22 CV 0.617). Different depths.

**Transfer ≈ chance even given every advantage** (best-over-all-32-layers, domain-matched):

| direction | Llama best (mean) | Qwen best (mean) |
|---|---|---|
| FaithCoT-all → synth-all | 0.554 (0.476) | 0.595 (0.495) |
| synth-all → FaithCoT-all | 0.531 (0.431) | 0.579 (0.515) |
| FC-aqua → synth-aqua (domain-matched) | 0.639 (0.505)* | skipped (fc n=10) |

\* Llama domain-matched trains on **n=19** with layer selection over 32 layers; near-chance mean (0.505)
⇒ selection noise, not signal. FaithCoT-nonmath→synth is likewise ~chance (0.566 / 0.605 best).

**Interpretation.** The synthetic answer-first construction is internally coherent and strongly,
cleanly detectable *within itself* — but it is **NOT a representational proxy for organic post-hoc
rationalization**: the two are encoded at different depths and along non-transferring directions
(cross-distribution AUROC ~chance even domain-matched and best-layer-selected). Prompt-induced
"answer-first" ≠ naturally-occurring ft2.

## Bottom line (for the paper)
1. **C1 reinforced + extended:** internal decodability of post-hoc-on-correct is now shown in **two
   models** on a **clean, large, ground-truth synthetic benchmark** (held-out 0.74 / 0.81, p=0.005),
   generalizing across two math datasets — where every black-box behavioral signal is at chance.
2. **New methodological caution:** synthetic answer-first/reason-first constructions — a common cheap
   proxy — do **not** transfer to real annotated post-hoc (different layer, ~chance cross-transfer).
   The real frontier is late-layer, weaker, and model-dependent (Llama > Qwen on real labels). Reported
   as a validity result, not hidden. This is what keeps the two buckets honest: we tested the bridge and
   it does not hold, so we do not claim the synthetic study "generalizes the FaithCoT finding" — we claim
   it (a) independently confirms internal decodability under clean labels, and (b) bounds the proxy.

## Caveats
Synthetic surface confound in Llama (0.639); AQuA yields thin for Llama (27 pairs) — synthetic AQuA is
GSM8K-dominated; soft_faithfulness uncomputed on synthetic (numeric options); FaithCoT-aqua n tiny
(19 Llama / 10 Qwen) so domain-matched transfer is underpowered. Two models so far (Llama, Qwen2.5);
DeepSeek-R1-Distill / Qwen3-8B / Gemma deferred (disk-gated: 34 GB free → download-run-delete needed).
