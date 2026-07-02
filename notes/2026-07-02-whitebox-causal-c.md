# White-box item (c): causal activation-steering — weak/suggestive (2026-07-02)

*`scripts/wb_causal_c.py`. Post-hoc direction = diff-of-means of cot_end @ L19 on a TRAIN split
(Llama-3.1-8B); steer the residual stream (block 18 output) by ±α·σ on 51 held-out letter-MC
traces; read answer-option distribution. Compared to a random unit direction (same norms).*

## Dose-response (answer-flip rate | mean P(orig-answer))
| α (σ) | POST-HOC flip | RANDOM flip | POST-HOC P(orig) | RANDOM P(orig) |
|---|---|---|---|---|
| −6 | 0.16 | 0.20 | 0.714 | 0.763 |
| −4 | 0.08 | 0.14 | 0.825 | 0.815 |
| −2 | 0.04 | 0.06 | 0.867 | 0.862 |
| 0 | 0.00 | 0.00 | 0.878 | 0.878 |
| +2 | 0.04 | 0.04 | 0.865 | 0.869 |
| +4 | **0.16** | 0.06 | 0.808 | 0.852 |
| +6 | **0.22** | 0.08 | 0.748 | 0.815 |

## Verdict: weak/suggestive causal relevance
- Steering **toward** post-hoc (+α) flips answers **~2–3× more than a random direction** at large
  magnitude (+6σ: 0.22 vs 0.08) and lowers answer confidence more (P(orig) 0.748 vs 0.815). So the
  post-hoc direction is **functionally active** — the model is more sensitive to it than to a random
  axis — i.e. **not merely a passive correlate.**
- **But modest and caveated:** effect only at big perturbations (±4–6σ); low flip rates (≤0.22);
  n=51; indirect readout (answer-change ≠ post-hoc-ness); the −α side is mixed. Not a strong
  causal claim — a supporting datapoint consistent with the overall *modest* internal signal.

## Status
Completes the white-box firm-up: **a, b, c, d, e all done.** Full picture: Llama internal probe is a
real-but-modest, ~linear, cross-domain-generalizing (held-out 0.70) detector of post-hoc-on-correct,
with weak causal support; Qwen weak; model-dependent. Next: synthetic-construction generalization
(GSM8K/AQuA × open-model roster) with the FaithCoT↔synthetic transfer test as the validity bridge.
