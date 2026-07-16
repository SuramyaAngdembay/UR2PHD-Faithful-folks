# Hint-induced organic post-hoc: the bridge PARTIALLY HOLDS where synthetic failed (2026-07-11)

> **⚠️ CORRECTION (2026-07-16):** The `faithful_type` regime labels used in this note are INVERTED
> relative to the released FaithCoT data: in the data, **ft1/ft2 = INCORRECT-answer regime, ft3/ft4 =
> CORRECT-answer regime** (the repo README's pairing is wrong; verified per-domain vs parsed answers and
> by reproducing the paper's own statistics; independently reported in FaithCoT-BENCH issue #3).
> All numbers in this note are valid; wherever it says "correct-answer regime / post-hoc-on-correct
> (ft1v2)" read "incorrect-answer regime". See `notes/2026-07-16-data-validation.md`.


*Scripts: `hint_generate.py` (Turpin-style biased-context construction), `synth_extract.py --tag hint`,
`synth_analyze.py --tag hint`, `bridge3.py`. Results: `results/synth_{llama,qwen}_hint.json`,
`results/bridge3_{llama,qwen}.json`. Motivation: GRACE-independent external validation of the frontier
(see 2026-07-10 discussion) + the "is instructed rationalization the artifact?" question left by the
synthetic bridge failure.*

## Construction (organic, causally labeled)
Baseline pass: model solves clean; correct → GENUINE (capped 300/dataset). Hint pass on baseline-WRONG
problems: re-ask with "I think the answer is {gold}, but I'm not sure." Keep as ORGANIC POST-HOC iff the
model flips to gold (**causal label** — it could not solve unhinted, so the hint, not the reasoning,
produced the answer) AND the CoT never references the hint (regex mention filter; rejects logged as honest
deference). Stored/probed context is CLEAN (no hint text) ⇒ symmetric conditions. Full AQuA-RAT test (254)
+ full GSM8K test (1319).

Yields: **Llama 428 genuine + 185 organic post-hoc** (2 mention-rejects); **Qwen2.5 464 + 70** (1 reject).
Exhaustive keyword-leakage audit over all kept traces: clean (hits were "we are told that…", generic-you
word problems, and "tro**user**s").

## Result 1 — organic post-hoc is internally decodable (both models, p=0.005)
| model | n (ph/gen) | best L | CV | held-out | perm p | surface BB |
|---|---|---|---|---|---|---|
| Llama-3.1-8B | 185/428 | 17 | 0.733 | **0.752** | 0.005 | 0.626 |
| Qwen-2.5-7B | 70/464 | 21 | 0.832 | **0.835** | 0.005 | 0.703¹ |

¹ Qwen's organic set carries a substantial surface tell (0.703) — probe clears it by ~0.13 but flag it.
Cross-dataset within model: Llama 0.62/0.66, Qwen 0.69/0.85.

## Result 2 — C2's metric inversion REPLICATES on causally-labeled organic data
`soft_faithfulness` in its intended direction (low coupling ⇒ unfaithful), on the letter-MC organic pairs:
**Llama 0.389 [95% CI 0.301, 0.481], Qwen 0.251 [0.166, 0.350]** — both CIs entirely below chance
(2,000-resample bootstrap, 2026-07-12); inverted 0.611/0.749. On traces where we *know*
the reasoning didn't produce the answer, the standard metric confidently points the wrong way. This is
the strongest form of the inversion yet (previous evidence used human labels; this uses causal labels).

## Result 3 — the THREE-WAY BRIDGE: organic↔organic partially holds; instructed is the artifact (Llama)
Depth signatures (own-best block-layer): **instructed-synthetic L9 → hint-organic L17 → annotated-organic
L29** (Qwen: L10 → L21 → L22). A monotone gradient from instructed to organic.

Directed transfers, swept over all layers (best | mean-over-layers). Llama (the model with a real
annotated signal):

| train → test | best | mean | verdict |
|---|---|---|---|
| **hint → faithcot** | **0.694** (@L25) | **0.616** | **bridges** (mean is selection-free) |
| faithcot → hint | 0.627 | 0.512 | weak-positive (FC train n=144) |
| synthetic → faithcot | 0.531 | 0.431 | fails (as before) |
| faithcot → synthetic | 0.554 | 0.476 | fails |
| synthetic ↔ hint | 0.65 / 0.65 | 0.61–0.63 | moderate |

**The hint→FaithCoT layer-MEAN of 0.616 (vs 0.431 for synthetic→FaithCoT) is the key number** — no
layer-selection optimism, computed on the same target set. Spontaneous (hint-elicited) rationalization
shares representation with human-annotated organic post-hoc; instructed answer-first does not.

**Permutation-tested (2026-07-12, `bridge3_perm.py`, PR #4 + fixes):** null = probes retrained on
permuted hint labels, permutations coupled across layers. Llama layer-mean **p=0.010**; best-of-layers
0.694 with max-over-layers (selection-corrected) null **p=0.050**. Qwen layer-mean 0.484 **p=0.741**
(confirms inconclusive/null). The organic bridge in Llama is statistically significant.

Qwen: hint→faithcot best 0.583 / mean 0.484 — **inconclusive, not negative**: the FaithCoT anchor itself
is weak in Qwen (own CV 0.617, never significant on human labels) and hint-posthoc n=70; you cannot
measure transfer onto a signal that barely exists in the target.

## What this buys the paper
1. **External validation of the frontier without GRACE** — a second, independent, *organic*,
   causally-labeled testbed replicates: internal decodability (both models, p=0.005), the metric
   inversion (both models, extreme), and black-box weakness (soft inverted; surface ≤0.70 vs probes
   0.75–0.84).
2. **C4 sharpens from "synthetic ≠ real" to a mechanism:** *instructed* rationalization is the
   artifact (early-layer, non-transferring); *spontaneously elicited* rationalization is
   representationally continuous with the annotated organic phenomenon (mid→late layers, transferring
   at 0.62 layer-mean in Llama). The depth gradient (L9→L17→L29) is the interpretive picture.
3. **The dataset itself is a contribution**: 255 causally-labeled, leakage-audited organic post-hoc
   traces + 892 matched genuine controls, at ~zero annotation cost — the collection protocol the
   field lacks (and RQ3's pilot, already done in v1 form).

## Caveats (report all)
Hint→FC best-of-layers has selection optimism (mean is the primary claim: 0.616, p=0.010; best 0.694
corrected p=0.050); FC target n=144/126; Qwen inconclusive (weak anchor, n=70, surface 0.703; perm
p=0.741); class imbalance in hint sets (185/428, 70/464 — AUROC tolerant but report); single hint
template (sycophancy phrasing) — template-robustness unchecked; math-only domains.
