# Hint-testbed extension cycle: template-B + LogiQA + source-domain bridge (2026-07-17)

Three runs, all landed; paper §7.2/§7.3 updated; VERIFICATION V10–V12. All perm p from
1000-permutation selection-corrected tests unless noted.

## 1. Template-B ("answer key" metadata note) — template robustness CONFIRMED
| | template A (sycophancy) | template B (metadata, clean) |
|---|---|---|
| Llama held-out | 0.752 | 0.731 (CV 0.785; n=613, 179 ph) |
| Qwen held-out | 0.835 | 0.824 (n=574, 104 ph) |
| Llama inversion (intended) | 0.389 | **0.390** |
| Qwen inversion (intended) | 0.251 | 0.270 |

Deference re-audit with widened patterns: llama 4/183 excluded (verbalized "the given answer"
paraphrase — missed by generation filter; inspected, all real deference); qwen 0. Filtered set =
`acts_llama_hintBc.npz` → `synth_llama_hintBc.json`. Llama surface rose (0.704 vs 0.626) —
metadata phrasing carries a stronger style fingerprint; caveat carried in paper.

## 2. LogiQA domain (sycophancy template, full 651-item test) — construction generalizes off-math
- Llama: 283 genuine + **231** organic-posthoc (57% baseline-wrong; 63% flip rate; 2 rejects).
- Qwen: 300 + 129. Deference rescan: **0 hits in 360 posthoc traces.**
- Decodable: llama held-out 0.672 (surface 0.547), qwen 0.793 (surface 0.607), both p≤.001.
  Surface gaps healthier than math. `soft` not computable on logiqa (analyze mcname limitation).

## 3. Source-domain bridge (hintL → annotated ft1v2; results/hintL_bridge_*.json)
| source → ft1v2 | Llama | Qwen |
|---|---|---|
| math-hint (orig, bridge3_perm) | **0.616 p=.017** | 0.484 p=.741 |
| logiqa-hint, all targets | 0.469 p=.687 | **0.553 p=.046** |
| logiqa-hint → logiqa-annotated | 0.429 p=.932 | **0.599 p=.016** (n=37) |

**Finding: the effective transfer source is model-dependent and complementary** — Llama bridges
from math-hint only; Qwen from the domain-matched LogiQA source only (which is also its larger
source: 129 vs 70 ph — domain vs size vs power not separable). Consequences:
- BOTH models now show hint→annotated transfer from some source (Qwen's old null = source
  limitation, not absent target signal).
- Transfer INTO qwen ft1v2 labels ⇒ external evidence that regime is decodable in Qwen
  (within-probe "not detected" p=.32 reads under-powered, not absent). Table 3 wording unchanged
  (within-probe claim), §7.3 (2b) carries the qualification.
- Caution: p-values uncorrected across the 3 target splits; llama domain-matched cell n=46.

## Ops lessons this cycle
- pgrep self-match strikes again: a wait-loop's OWN bash -c string contained the pattern it
  polled for (hintBc stall). Check patterns against the polling process's own cmdline.
- Post-hoc deference rescans with template-adapted patterns are now a standing step for any new
  hint template ("the given answer" catch). Generation-time filter updated? NOT yet — add
  "given answer" to MENTION before any future generation run.
