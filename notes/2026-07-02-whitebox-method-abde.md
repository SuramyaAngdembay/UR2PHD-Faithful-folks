# White-box method — items (a),(b),(d),(e) done; (c) NOT done (2026-07-02)

> **⚠️ CORRECTION (2026-07-16):** The `faithful_type` regime labels used in this note are INVERTED
> relative to the released FaithCoT data: in the data, **ft1/ft2 = INCORRECT-answer regime, ft3/ft4 =
> CORRECT-answer regime** (the repo README's pairing is wrong; verified per-domain vs parsed answers and
> by reproducing the paper's own statistics; independently reported in FaithCoT-BENCH issue #3).
> All numbers in this note are valid; wherever it says "correct-answer regime / post-hoc-on-correct
> (ft1v2)" read "incorrect-answer regime". See `notes/2026-07-16-data-validation.md`.


*Firm-up program for the internal-probe faithfulness detector on the F1 frontier (post-hoc ft2 vs
genuine ft1, correct answers). Extractor `wb_extract.py` caches 3 positions × all layers to
`wbrep_{model}.npz` (Aquaman; ~90/61 MB, not committed — regenerable). Open-weight generators only
(Llama-3.1-8B, Qwen-2.5-7B); gpt-4o-mini/gemini closed → the 2-generator ceiling.*

## (a) representation/position sweep + pre-CoT answer-decodability  (`wb_probe_a.py`)
Probe = StandardScaler→PCA(50)→LogReg; permutation null = max over 3 positions × all layers.
- **llama:** cot_end 0.697 > cot_mean 0.662 > pre_cot 0.639; global best **cot_end L19 = 0.697, p=0.030** ✓
  - a2 pre-CoT answer-decodability: **NULL** — answer not pre-decodable (0.13<0.20 chance); post-hoc NOT
    more pre-decodable (MWU p=0.92). The "answer decided before CoT" story does **not** hold for llama.
- **qwen:** cot_end 0.706 > cot_mean 0.566 > pre_cot 0.533; best **cot_end L23 = 0.706, p=0.060** (borderline ns)
  - a2: post-hoc answers **more** pre-decodable, **MWU p=0.044** (one-sided, *uncorrected* → suggestive).
- *Caveat:* (a) sweep uses PCA-fit-once (label-free) for speed → mildly optimistic (qwen 0.71 here vs 0.62
  strict); the permutation p stays valid (matched null). Use the strict numbers below for headlines.

## (b) linear vs MLP  (`wb_probe_b.py`, STRICT PCA-in-CV @ best cot_end layer)
- **llama:** linear 0.685 | MLP 0.710 | shuffled-control 0.614
- **qwen:** linear 0.644 | MLP 0.598 | shuffled-control 0.514
- → nonlinear does **not** reliably help (marginal on llama, *overfits* on qwen). Signal ≈ linear + modest.

## (e) proper held-out evaluation as a detector  (`wb_probe_ed.py`, 25× stratified 70/30)
- **llama:** AUROC **0.704 ± 0.073**, **F1 0.702**  (black-box baseline 0.50)
- **qwen:** AUROC 0.581 ± 0.077, F1 0.515 (weak)

## (d) cross-domain generalization (leave-one-domain-out)
- **llama:** HLE_BIO 0.712 | aqua 0.641 | logiqa 0.611 | truthfulqa 0.598  (transfers, ~0.60–0.71)
- **qwen:** 0.53–0.62 (weak)

## Verdict
**Llama:** a real, reasonably robust internal detector — held-out **0.70 (F1 0.70)**, cross-domain
0.60–0.71, **linear**, permutation **p=0.03** — where every black-box signal is at **0.50**. Legitimate
"internals see what behavior can't."
**Qwen:** weak (held-out 0.58); direct signal borderline (p=0.06), though the pre-CoT answer-commitment
hint (a2) was significant-but-uncorrected. → the signal is **model-dependent**, and the *mechanism*
differs (Llama: end-of-CoT representation; Qwen: pre-CoT answer commitment).
**Honest caveats:** small n (144/126); (a)-sweep PCA-once inflation; a2 uncorrected; nonlinear gives nothing.

## (c) causal patching — NOT DONE (next)
Activation steering along the L19 post-hoc direction (diff-of-means / probe vector) with a behavioral
readout (answer confidence/flip). Compute is cheap: **~10 min** forward-pass version (Version A),
~30–90 min generation version (B). Risk is scientific (modest, small-n direction → possibly
inconclusive), not compute. Planned next.
