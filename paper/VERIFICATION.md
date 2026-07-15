# Author verification guide — claim → paper location → code → artifact

*Page/line refs are from the 2026-07-14 compile ("submission (3)"). The latest commit rewrote the
abstract, thinned intro em-dashes, and folded the AI note into Ethics — so lines after the abstract
shift by a few; section anchors are stable. Recompile before final proofread.*

**Quick start:** `python3 scripts/paper_numbers.py` (repo root) recomputes every locally-derivable
number and prints `[PAPER]` vs `[RECOMPUTED]` side by side. CI edges may differ by ±0.005
(bootstrap seed); point estimates must match exactly.

---

## A. Claims and numbers, section by section

| # | Claim / number | Paper location | Code | Artifact / where it ran |
|---|---|---|---|---|
| 1 | Circularity trap: ρ=0.87 vs `soft_faithfulness` collapses against human labels | §3, p.3 L190–194 | `scripts/analyze_human_label.py` | Aquaman `~/analyze_human_label.py`; `notes/2026-06-25-finding-human-label-baseline.md` |
| 2 | Statistical standards (perm-test design, p≤1/201, in-fold PCA) | §3, p.3 L195–213 | perm design: `scripts/synth_analyze.py` (perm_maxauc), `scripts/bridge3_perm.py` | — (methodology; verify by reading code) |
| 3 | **Table 1** audit: correctness 0.696; soft intended 0.349; NLI/DAG ns | §4, p.4 + L232–241 | `scripts/rigorous_analysis.py` (original); `scripts/paper_numbers.py` (recompute) | `results/rigorous_features.json` (per-trace; regenerated on Aquaman by rigorous_analysis.py) |
| 4 | Extraction validation: LLM extractor 0.82 recall / 0.79 F1 vs 0.57 heuristic | §4 Signal families, p.3 L225–229 | `scripts/validate_extraction_llm.py`, `scripts/validate_extraction.py` | Aquaman logs; `notes/2026-06-29-validation-grace-and-extraction.md` |
| 5 | Interventions g=0.56–0.61 dominated | Table 1 caption, p.4 | `scripts/intervention_harness_v2.py` | `results/intervention_v2_results.json`; `notes/2026-06-25-finding-intervention-v2-bury.md` |
| 6 | Metric inversion +0.139 [+0.096,+0.182] | §4, p.4 L242–257 | `scripts/paper_numbers.py` block 2 | `results/rigorous_features.json` |
| 7 | **Table 2** frontier: all 4 signals at chance, n=270; ft-target variant 0.48–0.54 | §5, p.4 L258–272 | `scripts/paper_numbers.py` block 3 (both label targets) | `results/rigorous_features.json` |
| 8 | **Table 3** real-label probes: Llama CV 0.71 / held-out 0.70 / LODO 0.60–0.71 / perm 0.01–0.03; Qwen 0.62/0.58/p=0.32 | §6, p.4 L280–287 | `scripts/wb_probe_a.py` (CV+perm), `scripts/wb_probe_ed.py` (held-out+LODO), `scripts/whitebox_probe_v2.py` (pilot) | **Aquaman only**: `~/wbrep_llama.npz`, `~/wbrep_qwen.npz`; logs on server; `notes/2026-07-02-whitebox-method-abde.md`, `notes/2026-06-29-whitebox-pilot.md` |
| 9 | Steering 0.22 vs 0.08 at +6σ (weak/confirmatory) + **Table 6** | §6 L287–298; App. A p.8 | `scripts/wb_causal_c.py` | Aquaman log; `notes/2026-07-02-whitebox-causal-c.md` |
| 10 | **Table 4 / Fig 3** instructed construction, 7 models, all perm-sig; surface baselines | §7.1, p.5 L305–325 | generate: `scripts/synth_generate.py`; extract: `scripts/synth_extract.py`; analyze: `scripts/synth_analyze.py` | `results/synth_{qwen,gemma4,llama,qwen3,deepseek,gemma,dsr0528}.json`; raw traces+acts on Aquaman `~/synth/` (= `/data/suramya/ur2phd-synth`) |
| 11 | Hint construction: yields 185+428 / 70+464; mention filter; leakage audit; caveats (flip noise, difficulty confound) | §7.2, p.5 L326–360 | `scripts/hint_generate.py` (filter regex inside) | Aquaman `~/synth/traces_*_hint_*.json`; leakage audit = session log (re-runnable: grep keywords over traces); `notes/2026-07-11-hint-organic-bridge.md` |
| 12 | Hint decodability 0.752/0.835; surface 0.626/0.703; inversion 0.389 [0.301,0.481] / 0.251 [0.166,0.350] | §7.2, p.6 L362–371 | `scripts/synth_analyze.py --tag hint`; CIs: `scripts/paper_numbers.py` block 5 | `results/synth_llama_hint.json`, `results/synth_qwen_hint.json`, `results/hint_inversion_ci.json` |
| 13 | **Table 5 / Figs 4–5** three-way bridge: depth gradient L9/L17/L29; hint→annot mean 0.616 p=.017 (best 0.694 p=.049; 1000 perms — see row 23); synth→annot 0.431; Qwen null p=.741 | §7.3, p.6 L372–413 | `scripts/bridge3.py`; `scripts/bridge3_perm.py` | `results/bridge3_llama.json`, `results/bridge3_qwen.json`, `results/bridge3_perm_{llama,qwen}.json` |
| 14 | Robustness: no-PCA / target-scaler → hint 0.56–0.57 vs instructed 0.45 | §7.3, p.6 L404–408 | Aquaman `~/transfer_robust.py` (also printed by `paper_numbers.py`) | `results/transfer_robust_llama.json` |
| 15 | GRACE preliminary (App. C): NLI ≈ chance on 40-example sample | App. C, p.8–9 | `scripts/grace_nli_replication.py` (on Aquaman) | `notes/2026-06-29-validation-grace-and-extraction.md` |
| 16 | Concurrent-work characterizations (Related Work §2) | p.2–3 L133–156 | — | verify each arXiv id: 2605.25052, 2603.17199, 2605.25603, 2603.01437, 2511.17408, 2512.23032, 2402.14897, 2503.08679 |

## B. Figures

| Figure | What to check | Source of truth |
|---|---|---|
| **Fig 1** (example pair, p.2) | The two traces are REAL: baseline answer E, hinted CoT text, gold B | Aquaman `~/synth/traces_llama_hint_aquarat.json` — the "population increases by 5%" item (search "78000"); confirm the CoT excerpt in main.tex matches the stored trace verbatim (ellipses aside) |
| **Fig 2** (audit two-panel, p.3) | Bar values = Table 1/Table 2 values | `paper/make_paper_figs2.py` (values hardcoded from results — cross-check against `paper_numbers.py` output) |
| **Fig 3** (7-model dumbbells, p.5) | Circles = held-out, diamonds = surface, per model | reads `results/synth_*.json` directly — rerun `python3 paper/make_paper_figs2.py` |
| **Fig 4** (depth curves, p.6) | Peaks at L9 / L17 / L29 | reads `results/synth_llama.json`, `results/synth_llama_hint.json`, `results/faithcot_perlayer.json` — rerun `python3 paper/make_paper_figs.py` |
| **Fig 5** (transfer heatmap, p.6) | Diagonal = own CV (0.77/0.73/0.70), off-diag = layer-means | reads `results/bridge3_llama.json` — rerun `make_paper_figs2.py` |

## C. Suggested verification order (half a day)

1. `python3 scripts/paper_numbers.py` — mechanical check of Tables 1, 2, 4, 5 + inversions (15 min).
2. Read `scripts/hint_generate.py` end to end (the mention filter, the counterfactual keep-rule, the
   clean stored question) — this is the paper's most novel construction and §7.2's caveats must match
   what the code actually does (45 min).
3. Read `scripts/bridge3.py` + `scripts/bridge3_perm.py` — layer alignment (`X[l]` ↔ `cot_end[:,l+1]`)
   and the coupled-permutation null; §7.3's precision paragraph should match (45 min).
4. On Aquaman: spot-check 5 hint traces yourself (`~/synth/traces_llama_hint_aquarat.json`) for silent
   rationalization + confirm the Fig 1 trace verbatim (30 min).
5. Read `scripts/synth_generate.py` + `synth_extract.py` prompts vs Appendix B wording (20 min).
6. Skim `wb_probe_ed.py` (Table 3 hygiene: pipeline fit on train only) + `wb_causal_c.py` (Table 6) (30 min).
7. Verify the 8 concurrent-work arXiv ids and our one-line characterizations of each (30 min).
8. Full-paper prose proofread with the PDF and this table side by side.

---

# UPDATE 2026-07-15 — review-response additions (verify these too)

*The page/line refs in section A above are from the 07-14 compile; the review-response edits
(abstract, §5–§7.3, Tables 3–5, Limitations, Appendix D) shifted lines — recompile and use
section anchors. `python3 scripts/paper_numbers.py` now also prints every artifact below.*

## D. New claims from the review response

| # | Claim / number | Paper location | Code | Artifact |
|---|---|---|---|---|
| 17 | Nested-layer held-out: Llama 0.67±0.08 / Qwen 0.55±0.08 (Table 3 row); instructed Nested column 0.63–0.79 (Table 4) — problem-grouped 10× splits, layer chosen by inner CV on train only | §6 + Tables 3–4 | `scripts/grouped_eval.py` | `results/grouped_nested.json` |
| 18 | Learned text baseline FAILS on annotated frontier (0.446/0.474); instructed 0.502/0.564; hint 0.611/**0.751 (Qwen — disclosed 3×)** | §5, Table 4 caption, §7.2, Limitations | `scripts/embed_baseline.py` (frozen roberta-large-mnli + LR) | `results/embed_baseline.json` |
| 19 | Question-only probes within hint testbed: 0.646/0.664 (difficulty is decodable from the question) | §7.2 | `scripts/qonly_extract.py` | `results/qonly_{llama,qwen}.json` |
| 20 | **Difficulty-carrier control: question-only probe does NOT transfer** (Llama mean 0.413 p=0.996; Qwen 0.503) while CoT probe transfers 0.616 p=0.017 | §7.3 (after strict-subset sentence) | `scripts/qonly_transfer.py` | `results/qonly_transfer_{llama,qwen}.json` |
| 21 | Flip stability: 59% solved on 1 resample; strict = fail-both-resamples: 47/185 (25.4%) Llama, 20/70 (28.6%) Qwen | §7.2, Limitations, App. D | `scripts/flip_stability2.py` | `results/flip_stability_{llama,qwen}.json` |
| 22 | **Appendix D strict subset**: within-CV rises (0.818/0.837); Llama transfer magnitude preserved (mean 0.596, best 0.699) but underpowered (p=0.078/0.066); Qwen null (0.494, p=0.605) | App. D | `scripts/strict_subset.py` | `results/strict_{llama,qwen}.json` |
| 23 | 1000-permutation headline p-values: transfer mean p=0.017, best p=0.049 (Table 5, abstract); hint decodability p≤0.001 | §3, §7.2, §7.3, Table 5 | `scripts/bridge3_perm.py --nperm 1000`; `synth_analyze.py --tag hint --nperm 1000` | `results/bridge3_perm_*.json`, `results/synth_*_hint.json` |
| 24 | Cluster bootstrap over 8 model×domain cells: correctness [0.616, 0.753], inverted-soft [0.575, 0.728]; HLE-Bio ≈ chance per cell | Limitations | inline in this repo (see `paper_numbers.py` macro block + cluster snippet in session notes) | `results/cluster_bootstrap.json` (incl. per-cell values) |
| 25 | Bridge robustness to preprocessing (no-PCA / target-fit scaler: hint 0.56–0.57 vs instructed 0.45) | §7.3 | Aquaman `~/transfer_robust.py` | `results/transfer_robust_llama.json` |

## E. Terminology audit (2nd review) — spot-check these while proofreading
- Zero remaining: "organic post-hoc", "causal labels", "silent rationalization" (grep the tex to confirm)
- "is at chance" survives nowhere except quotes; frontier claims phrased as "no reliable above-chance discrimination"
- Proxy claim + depth gradient are Llama-scoped in abstract, §7.3, Fig 4 caption
- Hint traces named "hint-induced (unverbalized-flip)"; released set = "255 unverbalized hint-flip traces"
- Title decision (keep vs. "…Correctness Confounds and Unverbalized Hint Dependence") — pending author/advisor call
