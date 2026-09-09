# Frozen independent evaluation — specification v1 (2026-09-09)

Written and committed BEFORE any signal, metric, judge, or probe value is computed against the
target data. Purpose: independent confirmation (or disconfirmation) of the paper's central
correctness-stratified finding, with endpoints, data, exclusions, and analysis fixed in advance.

## 1. What has and has not been looked at (disclosure)

Inspected on 2026-09-09, before this spec: BonaFide (`yoavgurarieh/BonaFide`, HF, 2026-05-26
snapshot) **schema and counts only** — column names; `label_type` / `target_model` / `src_type` /
`hint_type` marginals; question-level crosstab of derived correctness (string-normalized
`model_answer == correct_answer`) against any-unfaithful-label. **Not computed**: any detector,
metric, judge, probe, surface, or length value against any label. The crosstab was necessary for
the go/no-go and endpoint choice below and reveals no detector outcome.

Key feasibility facts: 3,066 labeled rows over 864 unique questions; 10 open generator models
(Olmo-3/3.1, Qwen3-4B/30B instruct+thinking, R1-Distill-70B, Llama-3.3-70B) — **zero generator
overlap with FaithCoT-Bench**; labels are task-based/intervention-defined (sentence spans +
trace-level UNFAITHFUL_COT/FAITHFUL_COT), a different operationalization from FaithCoT's expert
annotation. Question-level correctness×label cells: incorrect-unfaithful 645, incorrect-faithful
172, correct-faithful 41, **correct-unfaithful 6**.

## 2. Go/no-go consequences of the counts

- **GO — blind-regime endpoint.** The incorrect-answer regime has 645/172 questions: powered
  (AUROC SE ≈ 0.02 at this n).
- **NO-GO — full regime-difference endpoint on BonaFide.** The correct regime has 47 questions
  (6 unfaithful), below any defensible floor (pre-set floor: ≥50 unfaithful and ≥50 faithful per
  regime). BonaFide's hint designs couple unfaithfulness to incorrectness (99% of unfaithful
  questions are incorrect) — an independent instance of the correctness–label entanglement the
  paper documents, reported as an observation, not used as a test.
- The full regime-difference claim therefore requires **Arm B** (fresh annotation, §7) and is not
  tested here.

## 3. Claim under test

On incorrect-answer traces (the regime holding most annotated unfaithfulness, where FaithCoT
metric families are at chance and the judge is degraded-but-informative):

- **H1 (judge retains blind-regime signal).** The fixed prompted judge discriminates unfaithful
  from faithful incorrect-answer traces above chance on an independent, task-based-labeled,
  generator-disjoint dataset.
- **H2 (metric blindness).** Each pre-registered metric-family signal fails to discriminate:
  95% CI includes 0.5; additionally report whether the upper bound is below the 0.60 margin
  (bounded) or not (unbounded null). Margin fixed here, before data: **0.60**.
- **H3 (judge > metrics, paired).** Judge AUROC minus each metric's AUROC > 0 (paired bootstrap
  on the same questions).

## 4. Frozen measurement definitions

- **Population**: all BonaFide questions with derivable correctness = incorrect and a trace-level
  faithfulness label; instance label = UNFAITHFUL_COT present (else faithful). Answer-normalization
  rule frozen as: lowercase, strip, exact match (ambiguous/missing answers excluded and counted).
- **Exclusions (computed before any scoring, reported)**: questions with normalized text exactly
  matching any FaithCoT-Bench question or any question in our hint/instructed testbeds.
- **Judge**: `gpt-4o-mini`, temperature 0, `max_tokens` 30, JSON-forced, **prompt A verbatim**
  from the paper (Appendix, System message unchanged); shown question + options/prompt + full CoT,
  never the gold answer. Snapshot pinned from API response; the 2024-07-18 snapshot predates
  BonaFide's release. Secondary (reported, not primary): prompt B, `gpt-4o`.
- **Metric signals** (published fixed directions, no re-selection): step-removal answer-tracing
  (soft, inverted direction), prefix instability (inverted), NLI unsupported-step count
  (RoBERTa-large-MNLI), raw step count. Deletion/prefix metrics require generator logprobs:
  computed with the generator itself for models that fit Aquaman (Olmo-3-7B, Qwen3-4B variants;
  4-bit), and **pre-registered as restricted to that subset** — the subset is fixed by hardware,
  not by outcomes; NLI, step count, and judge cover all models.
- **Statistics**: AUROC with tie convention as published; 2,000-draw bootstrap CIs clustered by
  question; paired judge-minus-metric deltas on common questions; no layer/threshold/prompt
  selection of any kind on this data. All numbers reported regardless of direction.

## 5. Interpretation, fixed in advance

- H1 holds & H2 holds: the blind-regime structure (metrics blind, judge informative-but-limited)
  generalizes across benchmark, annotation operationalization, and generator set — the paper's
  central practical claim confirmed independently.
- H1 fails: the judge's blind-regime signal is FaithCoT-specific; the paper's judge claim is
  rescoped accordingly.
- H2 fails (a metric works here): metric blindness is FaithCoT-specific; rescope, and report which
  metric and by how much.
- Any outcome: label-operationalization differences are treated as data; no pooling of BonaFide
  and FaithCoT numbers into single estimates.

## 6. Freeze mechanics

1. This spec is committed before the evaluation script exists.
2. The evaluation script is committed before it is run on target labels.
3. One run; per-example predictions saved; deviations (if any forced by data realities) documented
   in the results note before results are interpreted.

## 7. Arm B (full regime-difference; not started)

Fresh expert annotation of a stratified sample from generators outside FaithCoT, sized ≥50
unfaithful + ≥50 faithful per correctness regime, annotated blind to all detector outputs with the
FaithCoT rubric; inter-annotator agreement reported; disagreement with intervention-defined labels
reported as data. This is the arm that can confirm the full two-regime contrast; it is a larger
undertaking and is specified separately before collection begins.
