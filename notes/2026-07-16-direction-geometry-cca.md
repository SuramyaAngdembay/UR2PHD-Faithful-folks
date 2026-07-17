# Direction-geometry (CCA/subspace) study — the transfer is NOT a dominant shared axis (2026-07-16)

**Harness:** `scripts/cca_subspace.py` → `results/cca_subspace_{llama,qwen}.json`. Three tiers on
stored activations (SAE-free follow-up to the instrument-limited SAE pass).

## Tier A — mean-difference direction cosines (valid; 1000 coupled perms, all 32 layers, Llama)
| pair | mean cos | max \|cos\| | p (mean) |
|---|---|---|---|
| hint ↔ instructed | **+0.633** | 0.706 | **.001** |
| instructed ↔ ft1v2 | **−0.315** | 0.464 | .999 (= sig. anti-aligned) |
| hint ↔ ft1v2 | −0.114 | 0.268 | .870 (null) |
| qonly ↔ ft1v2 | −0.032 | 0.079 | .951 (clean control) |
| qonly ↔ hint | +0.123 | 0.215 | .001 (small difficulty component in hint, as known) |

**Positive control passes** (hint↔instructed geometric +0.63 matches their behavioral transfer
0.61–0.63) ⇒ tier A is a working instrument.

## Tiers B/C — LR-direction cosines & rank-5 bootstrap subspace similarity (INSENSITIVE — no inference)
The same positive control FAILS here (hint↔instructed LR-cos ≤0.08; subspace sim 0.03–0.06, ns),
so these statistics lack the sensitivity to detect even known-shared structure; their nulls for
hint↔ft1v2 are uninformative, not evidence of absence. (LR directions in 4096-d are high-variance;
bootstrap subspaces are noise-dominated.) Qwen mirrors this (all ns).

## The finding (geometrically consistent triangle, Llama)
hint ≈ instructed (+0.63) · instructed ⊥⁻ ft1v2 (−0.32) · hint ~ ft1v2 (−0.11) — AND YET
behaviorally hint→ft1v2 transfers (0.616, p=.017) while instructed→ft1v2 anti-transfers (0.431).

⇒ **The two constructions share their DOMINANT class-separation axis** (presumably the
construction/format signature) **and that axis is anti-aligned with the annotated regime.**
What differentiates the hint construction — the thing that actually bridges to annotated
unfaithful errors — is **not the dominant axis but lower-variance, covariance-aligned structure**
that the PCA-50+LR probe pipeline exploits and mean-difference geometry cannot see.
Instructed's transfer failure IS visible as raw-space anti-alignment; hint's transfer success is
invisible at the dominant-axis level. This sharpens C4: the "bridge" lives in subtle components,
not the loud construction signature.

## Consequences
- **SAE scope decision:** any useful dictionary must resolve non-dominant components on OUR
  distribution — off-the-shelf SAEs (fail reconstruction) and dominant-axis analyses both miss it.
  If pursued in Phase 2: fit SAE on our all-token CoT activations, or work directly in whitened
  space (e.g., principal angles between LDA-whitened discriminants) with a validated positive control.
- **Paper:** 2 sentences added to §7.3 (instructed anti-alignment confirms the signed version of
  the no-positive-alignment claim; hint transfer not explained by dominant-axis alignment).
- Methodological lesson: geometry tiers need a positive control before their nulls mean anything —
  tier B/C nulls would have read as "nothing shared" without it.
