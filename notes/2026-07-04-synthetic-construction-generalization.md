# Synthetic-construction generalization: white-box detectable in BOTH models, but does NOT bridge to real post-hoc (2026-07-04)

> **⚠️ CORRECTION (2026-07-16):** The `faithful_type` regime labels used in this note are INVERTED
> relative to the released FaithCoT data: in the data, **ft1/ft2 = INCORRECT-answer regime, ft3/ft4 =
> CORRECT-answer regime** (the repo README's pairing is wrong; verified per-domain vs parsed answers and
> by reproducing the paper's own statistics; independently reported in FaithCoT-BENCH issue #3).
> All numbers in this note are valid; wherever it says "correct-answer regime / post-hoc-on-correct
> (ft1v2)" read "incorrect-answer regime". See `notes/2026-07-16-data-validation.md`.


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

## Result 1 — white-box probe: significant in ALL SEVEN models across 3 families, 2024→2026
Detecting post-hoc vs genuine from last-token hidden states (StandardScaler→PCA(50)→LogReg):

| model | family / era | pairs | best L | 5-fold CV | held-out 70/30 | perm p (n=200) | surface BB | xds a→g / g→a |
|---|---|---|---|---|---|---|---|---|
| Qwen-2.5-7B | Qwen · 2024 (bridge) | 277 | 10 | 0.758 | **0.809** | **0.005** | 0.545 | 0.72 / 0.72 |
| Gemma-4-12B (sharded) | Gemma · 2026 | 248 | 23 | 0.776 | **0.797** | **0.005** | 0.665 | 0.65 / 0.54 |
| Llama-3.1-8B | Llama · 2024 (bridge) | 229 | 9 | 0.770 | **0.739** | **0.005** | 0.639 | 0.66 / 0.73 |
| Qwen3-8B (no-think) | Qwen · 2025 | 175 | 10 | 0.713 | **0.716** | **0.005** | 0.535 | 0.62 / 0.56 |
| DeepSeek-R1-Distill-Qwen-7B | DeepSeek/reasoning · 2025 | 251 | 7 | 0.645 | **0.617** | **0.005** | 0.534 | 0.56 / 0.52 |
| Gemma-2-9b-it | Gemma · 2024 | 243 | 5 | 0.586 | **0.600** | **0.020** | 0.548 | 0.53 / 0.60 |
| DeepSeek-R1-0528-Qwen3-8B | DeepSeek/reasoning · 2026 | 81 | 22 | 0.675 | 0.558¹ | **0.025** | 0.473 | — (aqua n=8) |

¹ held-out noisy at n=81 (test≈24); the permutation read (obs 0.688, p=0.025) is the reliable one.

**All seven permutation-significant.** The signal is internal (real): surface baseline ≈0.47–0.55 for
five of seven, so the probe beats surface; **Llama (0.639) and Gemma-4 (0.665) carry a partial surface
tell** — but their held-out AUROCs (0.74, 0.80) still clear surface by ~0.10–0.13, so there is real
internal signal on top. **Effect is strongly model-dependent, and the pattern is interpretable:** the
strongest are Qwen2.5 (0.81), the newest **Gemma-4-12B (0.80)**, and Llama (0.74); **reasoning-distilled
models (DeepSeek ×2, 0.56–0.62) and the older Gemma-2 (0.60) are weak-but-significant.** Note the sharp
**within-family jump Gemma-2 0.60 → Gemma-4 0.80** (newer/larger model far more decodable — partly the
higher surface tell, partly a genuinely stronger internal axis). Notably **Qwen2.5 was n.s. on the noisy
FaithCoT human labels (pilot p=0.32)** yet strong here on clean labels ⇒ that null was largely
label-noise/small-n.

**Cross-dataset transfer within a model (AQuA↔GSM8K, same probe):** strong for Qwen2.5/Llama (0.66–0.73),
moderate for Qwen3 (0.56–0.62), weak for the reasoning distills and Gemma (0.52–0.60). The synthetic
post-hoc axis generalizes across math datasets in the standard instruct models; less so otherwise.

### Roster / hardware notes
- **Design:** bridge (Result 3) is Llama/Qwen2.5-only — FaithCoT-Bench released real traces for exactly
  4 models (Llama-3.1-8B, Qwen2.5-7B, +closed Gemini-2.5-flash / GPT-4o-mini). The generalization roster
  deliberately spans **2024 → 2026 SOTA** to show the internal-decodability result isn't a single-
  generation artifact. Latest models serve Result 1 only (no real annotated post-hoc exists for them).
- **DeepSeek-R1-0528-Qwen3-8B (2026):** its long `<think>` reasoning overflows the 1024-token budget, so
  only 81 matched pairs parsed (biased toward shorter/easier problems) — small-n caveat; still sig.
- **Gemma-4-12B (2026) runs via 2-GPU pipeline sharding** (`scripts/gemma4_shard_test.py`,
  `synth_{generate,extract}.py --shard`). Single-card 4-bit loading peaks 7.83 GB (no extraction
  headroom) and the E4B variant OOMs in generation — but `device_map="auto"` splits the ~7 GB of 4-bit
  weights across the 2× RTX 3070, so a 1613-token extraction-style forward peaks **only 5.4 GB/card, zero
  CPU offload.** That put the actual 2026 Gemma-4 flagship-class (12B, multimodal-unified) in the roster
  on the existing 8 GB hardware (slower: pipeline-parallel serializes across the PCIe link, and one model
  occupies both cards). *(ZeRO/FSDP are training-memory techniques → N/A for inference; plain Accelerate
  pipeline sharding is what works.)* Gemma-4-31B / 26B-MoE and DeepSeek-V4 still exceed aggregate 16 GB.

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
1. **C1 reinforced + extended:** internal decodability of post-hoc-on-correct is now shown in **seven
   models across three families spanning 2024→2026** (Llama-3.1, Qwen2.5/Qwen3, Gemma-2/**Gemma-4-12B**,
   DeepSeek-R1-Distill ×2 incl. the 2026 R1-0528) on a **clean, large, ground-truth synthetic benchmark**
   (held-out 0.56–0.81, all permutation-significant), generalizing across two math datasets — where every
   black-box behavioral signal is at chance. Effect is model-dependent (strongest in Qwen2.5, Gemma-4,
   Llama; weak-but-significant in reasoning-distilled models and the older Gemma-2).
2. **New methodological caution:** synthetic answer-first/reason-first constructions — a common cheap
   proxy — do **not** transfer to real annotated post-hoc (different layer, ~chance cross-transfer).
   The real frontier is late-layer, weaker, and model-dependent (Llama > Qwen on real labels). Reported
   as a validity result, not hidden. This is what keeps the two buckets honest: we tested the bridge and
   it does not hold, so we do not claim the synthetic study "generalizes the FaithCoT finding" — we claim
   it (a) independently confirms internal decodability under clean labels, and (b) bounds the proxy.

## Caveats
Synthetic surface confound in Llama (0.639, others ≈0.54); AQuA yields thin for Llama (27 pairs) —
synthetic AQuA is GSM8K-dominated; soft_faithfulness uncomputed on synthetic (numeric options);
FaithCoT-aqua n tiny (19 Llama / 10 Qwen) so domain-matched transfer is underpowered. **Bridge is
Llama/Qwen2.5-only** — FaithCoT-Bench released real traces for only 4 models (Llama, Qwen2.5, +closed
Gemini/GPT-4o-mini), so the 2025–2026 models get within-synthetic + cross-dataset only, no real↔synthetic
bridge. Reasoning-distilled models' long traces make their post-hoc/genuine boundary diffuse (weakest
signals); R1-0528 also has small n=81 (reasoning overflowed the 1024-tok budget). Surface tell in Llama
(0.639) and **Gemma-4 (0.665)** (WB still clears it by ~0.1). **Gemma-4-12B runs via 2-GPU sharding**
(5.4 GB/card) — the earlier "not viable" was single-card only. Disk constraint resolved 2026-07-05 (HF
cache moved to /data, 5.6 TB free).
