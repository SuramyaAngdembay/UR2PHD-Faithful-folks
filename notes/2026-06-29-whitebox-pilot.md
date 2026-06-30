# White-box pilot (2026-06-29): the F1 frontier is internally (partially) decodable

*`scripts/whitebox_probe_v2.py`. Probe ft2 (post-hoc) vs ft1 (genuine) on CORRECT answers from
last-token hidden states: per-layer 5-fold CV with PCA(50)→logistic, and a 200-permutation test
on the max-over-layers AUROC (selection-corrected p). Results: `results/whitebox_*_results.json`.*

## Result
| model | n (ft2/ft1) | best layer | best AUROC | perm null mean | null p95 | **p (corrected)** |
|---|---|---|---|---|---|---|
| **Llama-3.1-8B** | 144 (84/60) | 27/32 | **0.709** | 0.590 | 0.662 | **0.010** ✓ sig |
| Qwen2.5-7B | 126 (63/63) | 23/28 | 0.616 | 0.598 | 0.675 | 0.323 (n.s.) |

Black-box baseline on ft1v2 = **0.50** (all signals; see rigorous-scaled-results).
Llama layer profile rises from ~0.50 (early) to 0.66–0.71 across layers 16–31 (peak L27).

## Reading it
- **Llama: significant internal signal (p=0.01).** The post-hoc-vs-genuine distinction is
  **behaviorally inaccessible (black-box 0.50) yet linearly decodable from activations (0.71)** —
  the black-box-vs-internals contrast that anchors the paper for BlackboxNLP.
- **Qwen: not significant (0.616 < null p95 0.675, p=0.32).** Decodability is **model-dependent** —
  present in Llama, not found in Qwen.

## Honest caveats (carry into the writeup)
- Small n (144 / 126); modest effect (0.71); a single permutation test per model.
- Qwen is "did not detect," **not** "absent" (underpowered).
- Only last-token pooling + PCA(50)→linear probe; one representation. Extensions: mean-pool /
  per-layer per-token, nonlinear probes, more models, the full GRACE set.
- The v1 raw-4096 probe (0.716, shuffled control 0.604) was selection/overfit-inflated; this PCA +
  permutation-test version is the trustworthy one.

## Effect on the paper
Upgrades **C1** from a pure null ("black-box at chance") to **"black-box blind, internally (partially)
decodable — significant in Llama, not Qwen."** White-box pilot = DONE. Remaining: full GRACE set,
writeup; optional probe extensions (pooling/layers/models) to firm up the asymmetry.
