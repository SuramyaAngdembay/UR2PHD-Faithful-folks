# 2026-09-08 — Follow-up experiments (template replication, chain, judge ablations) + bug sweep

Context: after the Part III rewrite (commit 481a0c3), three follow-ups were chosen to close the
remaining attack surface, then a systematic bug sweep over all post-Sept-1 (unvalidated) code.

## Experiment 1 — Template replication of the ONE positive transfer cell: **FAILS**

The surviving transfer cell was Llama x math x *sycophancy* template (hint->annotated-incorrect
layer-mean 0.616; paired Delta vs instructed +0.185, p<.001). Re-running `contrast_test.py` with the
**template-B (impersonal metadata) math set** (`acts_llama_hintB.npz`, 617 traces / 183 post-hoc,
regenerated fully under template B in July):

- hintB -> annotated-incorrect: **0.452 [0.382, 0.519]** (vs 0.616 sycophancy)
- Delta vs instructed: **+0.021 [-0.046, +0.085], p=.271** — indistinguishable from instructed
- NOT a broken source: hintB is *more* decodable in-distribution than the sycophancy set
  (5-fold CV L13/L17/L25 = 0.781/0.765/0.774 vs 0.726/0.733/0.713)

Reading: the positive transfer is **template-specific** (1 of now-8 hint cells: 2 models x
(3 domains + 2nd template)). The bootstrap Delta test for the sycophancy cell still survives
Bonferroni over 8 (p<.0005), but the July permutation p for the transfer itself (0.010 layer-mean)
does not (x8 = .08). Cannot fully separate "template" from "different flip sample" (different
problems flip under different templates). Consistent with the thesis: the MORE decodable variant
(stronger surface tell, 0.704 vs 0.626 surface baseline) transfers LESS — a fourth data point for
the decodability-vs-transfer dissociation, and the sharpest one (same model, same domain, same
construction family, only the hint wording changed).

## Experiment 2 — Non-transitive chain (instructed positive control): **PASSES**

New `scripts/chain_test.py` (mirrors contrast_test.py; target = sycophancy hint testbed, paired
bootstrap): kills the "maybe the instructed probe is just bad" objection.

- **instructed -> hint: 0.627 [0.587, 0.665]** — the instructed probe DOES carry portable signal
- annotated(ft1v2) -> hint: 0.512 [0.483, 0.541] — chance (consistent with CCA non-alignment)
- So in Llama: instructed->hint works, hint(syc)->annotated works, instructed->annotated is
  **bounded null** (<0.55). The instructed null is specific, not estimator failure.

## Experiment 3 — Judge ablations (qonly / cotonly): see results JSONs when done

`judge_baseline.py` gained `--ablate {qonly,cotonly}` (SYSTEM prompt and message skeleton fixed;
only the withheld block changes). qonly = difficulty-only control (no CoT shown); cotonly = no
question/options (caveat: traces often restate the question — inherent leakage, noted in code).
Both arms launched over all 1,303 labeled traces, gpt-4o-mini, T=0.
Purpose: if qonly ~ full judge, the judge is largely doing difficulty/correctness prediction and
"only behavioral signal to beat the oracle" needs qualification.

## Bug sweep over unvalidated (post-Sept-1) code — NOTHING BROKEN FOUND

| Target | Checks | Verdict |
|---|---|---|
| `build_truthfulqa_problems.py` | gold-position shuffled after insertion; on-disk file: n=774, gold dist A162/B183/C171/D151/E107, 0 malformed prefixes, 0 out-of-range golds, ids unique | clean |
| `hint_generate.py` truthfulqa branch | identical logic to validated logiqa path; A–E parse fallback fine for <=5 options | clean |
| `synth_extract.py` (truthfulqa additions) | probed context provably excludes hint text (paper claim verified in code); y=1=posthoc consistent; layer idx skips embedding | clean |
| hintT trace sets (both models) | 0 MENTION leaks; 6 wider-sweep hits all false positives ("studies suggested..."); flip-consistency 0 violations; genuine all baseline-correct; 0 problem-pool overlap | clean |
| `wbrep_*_ft34.npz` label direction | y=1 iff ft==4 verified in builder AND counts match paper (Llama ft4 n=26, Qwen n=48). A flip here would have INVERTED the -0.126 conclusion (transfer AUROC is not flip-invariant) — the July-16 bug class, explicitly ruled out | clean |
| `contrast_test.py` / `chain_test.py` | loading convention == perm-tested bridge3 (`cot_end[:,l+1]`, layer 0 = embeddings, documented in 5 scripts); paired bootstrap guards degenerate resamples; PCA fit sizes correct | clean |
| `target_contrast.py` | unpaired design correctly declared; sign convention of Delta matches paper text | clean |
| `nonlinear_transfer.py` | source-only selection (no target leakage); note: grid CV'd at best-linear layer only, transfer reported layer-mean (economy, not bug — flag if the number is cited in an appendix) | clean |
| `judge_baseline.py` analysis | regime cells ft(1,2)/y=ft==2 and ft(3,4)/y=ft==4 — matches corrected semantics; tie-aware AUROC | clean |
| `results/regime_delta_tests.json` (was M in git) | zero numeric changes vs HEAD~1 — formatting-only rewrite | non-issue |
| Paper transcription audit | ALL 6 tab:bridge cells + equivalence 0.502 + nonlinear 0.431->0.474 + target-contrast deltas + the three CVs (0.773/0.733/0.645) + qonly 0.646/0.413 + embed 0.476 [0.382,0.573] verified against JSONs | all match |

## Paper impact (to fold in once judge arms land)

1. §7.3(2): scope to "one model, one source, **one template**"; add hintB failure with its
   in-distribution CV (the fragility IS the thesis).
2. §7.3(1): add the chain positive control (instructed->hint 0.627) — pre-empts "bad probe".
3. §7.3(4): the dissociation now has a same-domain, same-family fourth point (hintB).
4. Prescriptions/Limitations: transfer evidence is 1 of 8 cells; template-sensitivity explicit.
5. Judge section: fold in qonly/cotonly decomposition when the arms finish.

New results files: `contrast_llama_hintB.json`, `chain_llama_hint.json` (+ judge arms pending).
