# SAE what-transfers study — pass 1 result: instrument-limited negative (2026-07-16)

**Question** (Phase 2, from the two-regime paper's discussion): which sparse features carry the
hint→annotated-incorrect-regime transfer (0.616 layer-mean, p=.017), and why does the instructed
construction not transfer?

**Setup:** Llama Scope residual SAEs (off-the-shelf, trained on Llama-3.1-8B **base** over
pretraining text) applied to our stored last-CoT-token activations (Llama-3.1-8B **Instruct**,
4-bit NF4) for the three sets (instructed / hint / ft1v2), layers 9, 17, 25, 29. Both dictionary
widths. Harness: `scripts/sae_transfers.py`; artifacts `results/sae_transfers_llama{,_32x}.json`.

## Result: the instrument fails before the question can be asked
- **Reconstruction variance explained ~0.41–0.49 (L9/17/25) and ~0.23–0.26 (L29), IDENTICAL for
  8x and 32x dictionaries.** Width did not help ⇒ the ceiling is **distribution shift** (base→
  instruct, fp16→4-bit, generic-text→last-CoT-token position), not dictionary capacity.
- Consequently: hint→ft1v2 transfer does **not** survive the SAE bottleneck (0.48–0.59 across
  layers/widths vs 0.616 residual; instructed→ft1v2 fluctuates 0.40–0.61, sometimes *above*
  hint — noise at this VE). Top-feature Jaccard overlaps are uninterpretable for the same reason.

## Interpretation (honest)
The transferring direction lives substantially in the 50–75% of variance these SAEs discard.
No feature-level claim (positive or negative) about what the direction encodes is licensed.
Portable observation: **off-the-shelf base-model SAEs are a poor instrument for
instruct-model, quantized, reasoning-position activations** — relevant caveat for any
"grab Llama Scope and decompose" workflow.

## Options for pass 2 (deferred until after the paper)
1. SAE fit on our own distribution: extract activations at ALL CoT token positions (~180k
   vectors from the hint set alone) and train a narrow SAE per layer of interest. Feasible on
   the 3070s; days of work.
2. Supervised subspace alternatives that need no SAE: shared-subspace analysis between the
   hint direction and ft1v2 direction (principal angles / CCA), reconstruction-error probing
   as a control.
3. Neuronpedia lookup of the few stable high-|d| features anyway (exploratory only).

**Paper impact:** one Discussion sentence — feature-level identification remains open;
off-the-shelf base-model SAEs reconstruct these activations too poorly (VE ≤ 0.49) to
decompose the direction.
