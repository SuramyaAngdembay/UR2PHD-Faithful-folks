# Executed GRACE and BonaFide analysis repair — September 13, 2026

The repair is implemented and executed from the existing prediction caches. No
new LLM/API or GPU inference was required for these analyses. This supersedes the
pipeline status and heuristic-conditioned interpretations in the earlier repair
verification, not the preserved historical files themselves.

## Implemented

- `scripts/grace_answer_check.py`: one shared reference-equivalence checker,
  explicit option parsing, exact presentation normalization, numeric/date and
  boolean checks, and abstention on unsupported semantic equivalence. No first
  character, substring, or token-F1 acceptance. Every recorded review is bound to
  a hash of its correctness-only inputs.
- `configs/grace-answer-reviews-v3.json`: recorded assistant review of all 177
  automatic abstentions. The packet supplied only question/options/reference/
  final answer and ID/dataset, excluding native faithfulness labels, annotation
  rationales and NLI outputs. The reviewer knew the project history; this is
  **not independent human gold or a newly blinded confirmatory annotation**.
  All 54 automatically resolved free responses were also inspected.
- `scripts/grace_regime_analysis.py`: portable CLI, strict population/cache
  validation, reviewed and automatic-only cohorts, task-specific analyses using
  the same fraction/correlation endpoint, all five binary aggregation rules,
  conditional pair AUROC with pair coverage, and exhaustive assignment of the
  three unresolved answers. Both strata use the same question bootstrap draws.
- `scripts/grace_regime_test.py --stage stats` delegates to that analysis; the
  duplicate broken checker is gone. Its optional NLI stage now requires a pinned
  model revision and new output directory and records per-step scores and input
  hashes. **That GPU path was not executed in this repair.**
- `scripts/bonafide_reconcile_analysis.py`: four-arm response intersection,
  direct paired differences, incorrect-only sensitivity, and correct handling
  of the split's eligibility. `bonafide_reconcile.py --stage stats` delegates to
  it. Its legacy API inference stage was not rerun or comprehensively repaired;
  use the manifest-bound diagnostic harness for a new judge campaign.
- `scripts/reanalysis_common.py`: strict duplicate handling, fixed-count
  question bootstrap, explicit one-class/constant-score undefined values,
  exclusive artifact creation and input/code hashes. A nominal confidence
  interval is withheld if any bootstrap statistic is undefined; valid-resample
  percentiles are separately identified as conditional descriptive quantities.
- `scripts/render_reanalysis.py`: generated manuscript tables from result JSON,
  with source hashes in the TeX. Manuscript claims now distinguish non-detection
  from equivalence, the full pooled cohort from correctness-reviewed cohorts,
  and NLI cross-checks from a complete detector-panel replication.

## Final versioned runs

- `results/grace_reanalysis_v3/2026-09-13-final/`
- `results/bonafide_reconciliation_v2/2026-09-13-final/`

Each has `results.json` and `manifest.json`; GRACE also has every correctness
decision, and BonaFide has a response-level exposure report. Frozen historical
caches and result JSONs remain unchanged. Earlier development outputs from this
repair are preserved in the local review archive, not treated as final results.

```bash
python3 scripts/grace_regime_test.py --stage stats \
  --data-dir /path/to/GRACE-benchmark/dataset/test \
  --output-dir results/grace_reanalysis_v3/NEW-RUN --bootstrap 2000 --seed 0
python3 scripts/bonafide_reconcile.py --stage stats \
  --output-dir results/bonafide_reconciliation_v2/NEW-RUN --bootstrap 2000 --seed 0
python3 scripts/render_reanalysis.py \
  --grace-result results/grace_reanalysis_v3/2026-09-13-final/results.json \
  --bonafide-result results/bonafide_reconciliation_v2/2026-09-13-final/results.json \
  --exposure results/bonafide_reconciliation_v2/2026-09-13-final/exposure.json \
  --output-dir paper/arr/generated
python3 -m unittest discover -s tests -v
```

The GRACE data are from revision `63b6b2d57839bf4a44e9f74572b2f8c5898e3f39`;
individual JSONL content hashes are in the manifest. Default caches/configs
resolve relative to the repository, not a machine's home-directory layout.
Output directories must be new; the CLI refuses an existing directory.

## Corrected GRACE results

434 of 437 responses have resolved reference-equivalence labels: **280 correct,
154 incorrect, 3 unresolved**. Automatic-only: 260 (197/63). Relative to Claude's
saved containment/F1 repair, 9 former positives are now incorrect, 14 former
negatives correct, and 3 cases remain unresolved (26 changed dispositions).
These counts measure answer equivalence to released references, not independently
verified factual truth.

| NLI signal | Correct rho | Incorrect rho | Difference | Paired 95% CI |
|---|---:|---:|---:|---|
| Context unsupported rate | .241 | .216 | +.025 | [-.177, +.219] |
| Negative context mean entailment | .273 | .159 | +.113 | [-.088, +.312] |
| Prior-step unsupported rate | .081 | .085 | -.004 | [-.220, +.210] |

No primary NLI regime difference is resolved; the intervals allow meaningful
effects. This is neither equivalence nor evidence that regimes cannot occur
outside FaithCoT. Pooled, correctness-independent context NLI rho remains
.225797/.253778 on all 437 traces.

Answer-error lift is 1.159/1.387/1.606/1.705/1.295 over any, >.25, >=.5, >.5,
and all-unfaithful rules. Majority lift CI [1.432, 1.804]; all-unfaithful CI
[.832, 1.723]. Association is supported under several rules, not uniformly
resolved across all rules. It concerns this selected population and operational
labels, not a causal or population-wide law.

Assigning the three unresolved answers in every possible way yields context-rate
differences .015–.040, negative mean-entailment differences .108–.117, and
prior-rate differences -.018–.016. Those ambiguities alone do not explain a large
change. This does **not** bound review error in other answers.

The automatic-only subset has regime differences -.131/-.141/-.046, all with
wide intervals. It is heavily selected: 206 multiple-choice versus 54 free-form
answers, with only four free-form incorrect answers. It is a sensitivity analysis,
not evidence that review caused a detector effect.

Task-specific context unsupported rates can be nearly constant: only 1,096/2,000
Wiki2Multihop and 1,719/2,000 MuSiQue resamples yield a defined regime difference.
The script withholds their confidence intervals. Treating just the defined
Wiki2Multihop resamples as a nominal 95% CI would create a misleading negative
finding. All 2,000 pooled primary resamples are defined.

Length is still relevant: pooled step-count rho with unfaithful fraction is
-.223; binary step-count AUROC ranges .184–.491. Dataset-by-track pair AUROC is
a separate binary estimand, not an adjusted Spearman correlation.

## Corrected BonaFide comparison

Exactly 150 common responses, 123 questions, U85/F65. All arms score towards
unfaithfulness, without post-hoc complementation.

| Arm | Common-cohort AUROC | 95% CI |
|---|---:|---|
| A: generic/full prompt | .319 | [.229, .412] |
| B: generic/local hint stripping | .400 | [.307, .490] |
| C: our rubric/full prompt | .367 | [.278, .456] |
| D: historical GPT-4o/clean question | .331 | [.242, .418] |

Paired A−B = −.081 [−.178, +.015]; A−C = −.048 [−.128, +.036]; C−D = +.036
[−.023, +.093]. These do not establish a context/rubric remedy, harmful context
as a general effect, or equivalence. A=.352 on 284 responses is retained only as
an unmatched descriptive estimate.

On the 143 common incorrect responses, A/B/C/D are .335/.419/.370/.332. B−D is
+.087 [.006, .161], a nominal exploratory result among six contrasts. It combines
a rubric/input difference with a historical comparator, B's own interval crosses
chance, and it is not independent validation of an effective method. Preserve
this result rather than claiming every sensitivity interval includes zero.

Reconciliation exposure: 204/807 eligible evaluation responses, 156 questions;
397 evaluation responses share those questions. The seven correct answers are
outside the original incorrect-only split, not new evaluation exposures.

## Validation and remaining limits

32 unit/regression tests passed, including original first-character/substring/date
bugs, option conflicts, stale reviews, missing labels/cache entries, pairwise ties,
identical-arm contrasts, whole-question resampling, undefined-bootstrap handling,
and the seven-response split eligibility bug. Both historical stats entry points
ran successfully against real caches. The direct GRACE CLI was also run from a
different working directory and checked against the wrapper. Independent SciPy
correlations and explicit positive/negative pair comparisons verify headline point
estimates. Input/code/artifact hashes are checked against disk.

The manuscript includes generated results and removes the stale claim that the
full GRACE release was unavailable. TeX inputs and table consistency were checked;
a PDF rebuild was not performed because no TeX engine is installed locally.

The next scientific step is independent checking of answer-equivalence decisions
and alleged native faithfulness violations, followed by a frozen, repeated
common-example rubric/evidence judge comparison. The legacy NLI cache still has
4,000-character/512-token limits and no original request hashes, and the judge
score caches do not contain outputs needed to validate their rationales. New
inference should use the existing manifest-bound diagnostic harness, with this
exposure history retained. No successful corrective method is established here.
