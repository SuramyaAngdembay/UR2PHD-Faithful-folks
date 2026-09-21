# Definition-informed judge on the blind regime — spec frozen before any arm ran (2026-09-21)

## Question

Across ten single judges none exceeds 0.679 AUROC at separating honest from unfaithful errors
(ft1 v ft2). The scoop check of 2026-09-21 raised the sharpest threat to that ceiling: on BonaFide a
*generic* judge scores 0.67-0.68 while a *definition-informed* judge reaches 0.82-0.87. **Is our
ceiling a property of the problem, or of a generic rubric?**

## What was known when this was written (ordering disclosure)

- Known: every generic-prompt result (prompt A and B; ten judges; per-regime, per-domain,
  per-generator), the judge noise floor, and the 2026-09-21 stress tests. Two of those tests lowered
  my prior here: judges do not do materially better on questions they answered correctly themselves
  once domain is held fixed, and inter-judge agreement does not identify where they are right.
- Known: GeoFaith's Table 1 reports pooled F1 of 43-59 for six prompted judges on this benchmark.
  I do not know which prompt they used.
- **Not known: any output of any judge under rubric D1, D2 or R.** No such arm existed at freeze.
- My stated expectation, so it cannot be revised later: **a small effect.** Prompt A already names
  post-hoc rationalisation and steps that do not support the answer, which are the benchmark's two
  macro categories. I would put about 30% on the strong criterion below being met.

## Arms

Rubric texts live only in `scripts/judge_rubrics.py` (sha256 `9e053b3818bd551f…`), built from
FaithCoT-Bench's own published materials (arXiv:2510.04040v2) so that my wording stays out of the
definitions. Prompt hashes: A `ee6731da1427…`, D1 `6a996862d50c…`, D2 `9d9510cb7926…`, R `23f3c1e123ac…`.

| rubric | content | output |
|---|---|---|
| **A** (reference) | the project's generic prompt; byte-identical to the existing arms (asserted) | 0-100 |
| **D1** (primary) | annotator instruction sheet (App. A.3), Definitions 2-3, all eight fine-grained subtypes (App. A.2), verbatim; schema sentence identical to A | 0-100 |
| **D2** | the benchmark's own LLM evaluation prompt (App. A.4), sentence-for-sentence | 0/1/2, mapped 100/0/50 |
| **R** | prompt A with the gold answer revealed | 0-100 |

Between A and D1 the only thing that changes is the rubric. Evidence shown (question, options, full
trace) is identical in A, D1 and D2; R adds one line.

**Judges.** Three local judges under greedy decoding — Qwen3-8B, Llama-3.1-8B-Instruct,
Qwen2.5-7B-Instruct — loaded exactly as in `judge_local.py`, so their existing prompt-A arms are
exact references (greedy repeat verified 1304/1304 identical). Plus **gpt-4o-mini**, the judge that
holds the 0.679 ceiling, if API credit allows; its reference arm carries about ±0.023 of
run-to-run noise, which the decision rule below absorbs.

**Instrument smoke.** Up to 8 traces per (judge, rubric) may be run first and inspected **for parse
rate only**. No accuracy quantity is computed from smoke output. Smoke rows are kept; the arms
resume from them, so they are part of the final data rather than a separate peek.

## Endpoints (all computed by `scripts/rubric_effect_analysis.py`, sha256 `3f889cd44bc251ad…`)

**Primary:** paired delta in blind-regime AUROC, D1 minus A, same judge, same traces;
question-clustered paired bootstrap, 2000 draws, seed 0. Family = the judges with a completed D1 arm
(up to four); Bonferroni intervals reported beside the 95% ones.

**Decision rule, fixed now.**
- **RUBRIC-BOUND** — delta >= +0.05 with the Bonferroni interval excluding zero in **at least two
  judges**, *and* some judge's D1 blind AUROC >= 0.72. Then the generic-prompt ceiling was a rubric
  problem, the ceiling claim is withdrawn, and the text side reopens for method work.
- **ROBUST** — for **every** judge, delta < +0.03 or the 95% interval covers zero. Then the ceiling
  survives a definition-informed rubric built from the annotators' own criteria, and may be claimed
  for prompted judges under both generic and definition-informed rubrics.
- **MIXED** — anything else. Reported as is; neither reading is claimed.

**Secondary, labelled exploratory:** D2 and R against A on the same footing; correct-regime deltas as
a no-harm check; blind-regime AUROC by domain; within-generator pair-weighted AUROC. An arm enters
the analysis only if its file is complete (>= 1303 rows) and parses at >= 95% — the partial-arm bug
of 2026-09-20 is excluded by construction.

## What this cannot show

A null is a null **for prompted judges given these definitions**. It says nothing about trained
detectors: CIE-Scorer's repository ships no checkpoint and GeoFaith has released no code, so the
companion experiment (a published trained detector on the blind stratum) is blocked for now.
A positive result would not show the judges detect *faithfulness*: BonaFide's authors argue these
labels track implausible or wrong reasoning, and a rubric that says so explicitly could raise
agreement with the labels for that reason.
