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

## Experiment 3 — Judge ablations (qonly / cotonly): **VALIDATES the judge**

`judge_baseline.py` gained `--ablate {qonly,cotonly}` (SYSTEM prompt and message skeleton fixed;
only the withheld block changes). qonly = difficulty-only control (no CoT shown); cotonly = no
question/options (caveat: traces often restate the question — inherent leakage, noted in code).
Both arms run over all 1,303 labeled traces, gpt-4o-mini, T=0. Result: the OPPOSITE of the worry.
- **qonly at chance on everything**: full 0.487 [0.456,0.519]; incorrect regime 0.467; correct 0.552;
  and even score-vs-INCORRECTNESS 0.503 — the judge cannot predict difficulty/correctness from the
  question alone. (54% of qonly scores sit at midpoint 50; the differentiated rest carries nothing.)
- **cotonly keeps most signal**: full 0.693 [0.662,0.725]; blind regime 0.661 (of 0.679 full-judge);
  correct 0.769; while correctness-tracking collapses 0.684 -> 0.560.
=> The judge reads the trace, not the question. Its correctness inference requires the question;
its unfaithfulness signal is trace-internal. The "only behavioral signal to beat the oracle" claim
is STRENGTHENED, and the Limitations hedge is now bounded. Caveat: traces often restate the
question, so cotonly is an upper bound on question-independence.

## Second grid completion — qwen hintB: null (delta -0.002 [-0.085,+0.080], p=.537)
Grid final: 8 cells = 2 models x (math-sycophancy, math-metadata, LogiQA, TruthfulQA); 1 significant.
Qwen chain also run: instructed->hint 0.582 [0.529,0.633] — positive control passes in BOTH models.

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

## Paper impact — APPLIED (commit a0ba3eb)

All folded into paper/arr/main.tex: (2) retitled "one model, one source, one template" + hintB
sentence; (1) chain control both models; (4) four-variant version ("the two most decodable transfer
least"); table now 8 rows, caption recounted, Bonferroni over 8 (still passes); abstract/
contribution/discussion/limitations counts updated; judge §5 + appendix ablation cells; skeptical-
reading paragraph moved Discussion -> Limitations (page budget + it is one). Body ends p8; 0 overfull.

New results files: contrast_llama_hintB.json, contrast_qwen_hintB.json, chain_llama_hint.json,
chain_qwen_hint.json, judge_baseline_qonly.json, judge_baseline_cotonly.json (+ raw jsonl).

## External review (Codex, 2026-09-07) — adjudication and response [added 2026-09-08]

An external audit (run at commit 5e6dbfd) found real problems the "nothing broken" sweep missed.
All five checkable factual claims verified TRUE against our own files:
1. n_boot=500 in the four original contrast cells (caption claimed 2,000; "p<.001" unjustified at
   that resolution — rule-of-three upper bound 0.006 vs Bonferroni-8 threshold 0.00625: undecided).
2. The July hint->FaithCoT permutation p is 0.017 (bridge3_perm_llama.json), not the 0.010 in
   CLAUDE.md/notes (transcription error; now corrected).
3. Equivalence bound overscoped: only Llama-instructed->incorrect is bounded (upper 0.502);
   Qwen upper 0.569, Llama->correct upper 0.647; lower tail 0.357 (no symmetric equivalence).
4. "Instructed is easiest to detect" contradicted by our own held-out numbers (0.739<0.752 llama,
   0.809<0.835 qwen). Defensible claim = breadth (all 7 models), not ease. Fixed at 4 sites.
5. hintBc (cleaned cache, 179 ph, held-out 0.731 = the paper's July figure) existed alongside the
   unfiltered hintB I used. Provenance failure, not wording.

Their follow-up pushback also correct on all five points (provenance != wording; bootstrap tail is
CI-inversion not a calibrated test; identical target != format-controlled probes; overlap direction
unknown; "decisive"/"addresses causal-label weakness" overpromised).

**Response experiments (13 jobs, all landed 2026-09-08):**
- 10k-draw bootstrap reruns: headline k=2/10000 -> add-one p<=0.0003. hintBc contrast: 0.451
  (vs unfiltered 0.452) — template failure is cache-robust.
- NEW contrast_perm.py (null-calibrated paired exchangeability test, rank-transformed columns,
  add-one convention per Phipson-Smyth): headline p=0.0005 (4/10000), survives Bonferroni-8;
  all 7 other cells p>=.09. The calibrated companion the claim needed.
- NEW wb_extract_raw.py + contrast --wbfile: matched (prefix-free) serialization target moves
  NOTHING (instructed 0.431->0.432, hint 0.616->0.614, delta +0.182 [+0.078,+0.286]).
  Differential-format-sensitivity alternative CLOSED empirically.
- NEW overlap_sensitivity.py (alignment verified elementwise vs npz y+domain): overlap-excluded
  shifts <=0.014, all conclusions unchanged; positive cell zero overlap.

Paper corrected accordingly (easiest->breadth, equivalence rescoped, calibrated p added, three
control paragraphs in appendix, hintBc lineage explicit, qonly "at chance" softened, "significant
at every layer" -> descriptive, gpt-4o scoped to tested judges, "independent binary label" ->
"separate binary field"). Uniform 10k table pending final 3 reruns.

**Open decision (user):** audit-led restructure/title pivot (both reviews recommend it; evidence
now leans that way). Matched construction experiment + reader-by-generator swap queued as the next
substantive experiments.

## Composition/selection analysis (direction-1 leg 1) — CORRECTED after review round 3 [2026-09-09]

v1 (composition_rankings.py, commit 38a41ee) claimed a 7x LODO selection-rule improvement.
**External review round 3 was right on all three flaws, verified by my own corrected rerun (v2):**
1. The correctness ORACLE was in the selection pool — it needs gold correctness, so "aggregate
   picks it 4/4" is a diagnostic of what aggregate AUC rewards, not a practitioner failure.
2. Judges were excluded from the pool explicitly because they'd mask the effect — pool selected
   to make the result visible.
3. Detectors were evaluated on different populations (633 vs 1303).

**v2 (composition_rankings2.py): oracle out, judges in, common examples, fixed baselines,
question-clustered bootstrap (341 clusters) that repeats selection per draw. Result: the
selection-rule benefit DOES NOT EXIST in any realistic pool** — reproducing the reviewer's
exploratory table nearly exactly:
- metrics-only common-633: aggregate 0.022 vs worst-regime 0.063 (REVERSED)
- metrics+judges common-633: 0.027 vs 0.038 (reversed)
- judges-only 1303: mean-regime 0.011 beats aggregate 0.040, but equals fixed "always judgeA"
All rule-vs-rule differences have clustered CIs crossing zero. Per the reviewer's own kill
criterion ("the selection procedure does not improve held-out decisions"), the REMEDY leg of
direction 1 failed its cheap test — discovered cheaply, exactly as prescribed.

**What survives (audit-strengthening, not a selection method):** the exact 4-cell AUC
decomposition (metric aggregate performance is carried by the cross cell: oracle 0.996, soft
0.700, PI 0.684); the oracle-as-illustration (top metric detector 0.696 at benchmark composition,
last under balanced/flipped reweighting with frozen per-pair behavior); real domain composition
variance (HLE-Bio [.89,.95] vs AQuA [.40,.19]). These fold into the audit paper as a sharpened
statement of the composition finding. Withdrawn: "7x", "all kill criteria cleared", "the
prospective test passes" (retrospective LODO on extensively-examined domains).

**Footgun discovered:** rigorous_features.json's `correct` field encodes PRE-correction semantics
(correct=1 iff ft in (1,2), which post-correction means INCORRECT). audit_corrected.py already
avoids it; composition analyses derive regimes from ft directly. Never consume that field.

Matched-question qualification (accepted): the genuine cohort also changed under matching, so
"the excluded sycophancy positives carry the signal" is not yet isolated even if the gap shrinks.

## MATCHED-QUESTION VERDICT (llama, landed 2026-09-09): the construction advantage is largely SELECTION

matched_question_llama.json (cleaned metadata cache, 54 shared positive / 361 shared genuine
questions, fixed annotated target, 200 question-level refits, 200-draw size controls per arm):

| arm | transfer |
|---|---|
| sycophancy FULL | 0.616 |
| sycophancy random-54/361 subsets (size control) | 0.590 +- 0.038, q[0.507, 0.646] |
| sycophancy SHARED questions | 0.509 (refit CI [0.456, 0.585] — includes 0.5) |
| metadata shared | 0.445 | metadata full 0.451 |

- **Not small-n**: random size-matched sycophancy subsets transfer at 0.590 — nearly the full-set
  level. The shared-54 probe (0.509) sits at ~the 2nd percentile of that distribution (z ~ -2.1).
- **Template contrast on identical questions: NULL** — delta +0.064, refit CI [-0.053, +0.102],
  p(delta<=0)=0.26. On shared questions the two templates are indistinguishable, and sycophancy
  transfer itself is not distinguishable from chance there.
- Reviewer's dichotomy resolved toward: "the advantage disappears under matching — evidence that
  sample selection created the apparent construction advantage." The transferable signal is
  carried by the sycophancy-SPECIFIC question cohort (questions that flip only under that
  template), not by hint wording.
- Open (isolation, running as matched_isolate.py): matching changed both cohorts; genuine overlap
  is 84% (361/428) vs positive overlap 29% (54/185), so the positive cohort is the prior suspect,
  but the B/C/D cross (sharedP+randomG vs randomP+sharedG vs randomP+randomG) closes it properly.
- Post-hoc HYPOTHESIS only (untested): shared questions = flip under BOTH templates = most
  suggestible; sycophancy-only questions = flip only under stronger social pressure — possibly a
  different, more annotated-like flip population. Testable against flip_stability resample data.

Consequence: the paper's construction section gets its third and final rescoping — not
"one template transfers" but "apparent construction transfer was substantially a question-
selection phenomenon; on matched questions no construction reaches the annotated regime."
This STRENGTHENS the audit-led thesis (both directions of the caution now have evidence:
within-distribution decodability doesn't predict transfer, and apparent transfer successes
can be selection artifacts). Qwen matched arm not rerun (n=10 shared positives).

## Isolation cross verdict + review round 4 corrections [2026-09-09]

matched_isolate_llama.json (verified against reviewer's independent read — exact match):
| positives | clean | transfer |
|---|---|---|
| shared | shared | 0.5085 |
| shared | random-361 | 0.5654 sd .024 |
| random-54 | shared | 0.5549 sd .040 |
| random-54 | random-361 | 0.5903 sd .037 |

**BOTH cohorts matter**: clean-cohort substitution alone recovers +0.057 (positives fixed);
positive-cohort substitution alone +0.046. My positive-only attribution ("the transferable signal
lives in the sycophancy-specific positive questions") is DISCONFIRMED by the experiment I queued
to test it. The clean-cohort effect is the notable part: a contrastive probe's transfer moves
substantially through its NEGATIVE training questions.

Domain-composition check (new): sharedP 15/54=27.8% aquarat vs pool 53/185=28.6%; sharedG 25.5%
vs 29.9% — the shared cohorts are NOT domain-skewed; that mundane alternative is closed. What
distinguishes the shared cohort remains unattributed (filtering/generation stochasticity not
separable from intrinsic question properties on this data).

Language corrections accepted (reviewer round 4, all valid):
- "small-n is dead" -> size costs ~0.026 on average; 0.5085 sits just INSIDE the size-control
  95% range [0.5074, 0.6455]; my "2nd percentile" was a normal approximation, not empirical.
- "template contrast is null" -> "no detected difference"; refit CI [-0.053,+0.102] permits
  meaningful effects; no equivalence margin was prespecified.
- "no construction reaches the annotated regime" -> overgeneralized (two hint constructions,
  one model; sycophancy matched CI [0.456,0.585] includes modest positive transfer; instructed
  was not an arm of the matched comparison).
- "best possible outcome" -> spin; honesty gains are not novelty gains.
- matched_isolate.py limitations acknowledged: arms not paired across draws, summaries only
  (no raw draws / per-target predictions), no target-side uncertainty. Paired rerun is the
  conditional follow-up ONLY if the paper needs a stronger attribution claim.

Adopted construction-section statement (reviewer's draft): "The observed sycophancy transfer
advantage attenuates on shared question cohorts. Size controls and cohort substitutions indicate
sensitivity to training-question selection in both classes. The matched comparison does not
establish a template advantage or equivalence."

Standing priority (unchanged, now unblocked): restructure around the correctness-stratified
audit; construction sensitivity as supporting evidence with its own limitations; then ONE frozen
independent evaluation of the central finding, specified before seeing results. Selection remedy
preserved as an unsuccessful exploratory analysis, not a contribution.
