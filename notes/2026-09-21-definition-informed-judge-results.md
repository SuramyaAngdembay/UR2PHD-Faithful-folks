# Definition-informed judge on the blind regime: results (2026-09-21)

Spec frozen at `bba509f` before any arm ran; amended at `5dd0552` on parse rates only. Analysis by
`scripts/rubric_effect_analysis.py`, sha256 `3f889cd44bc251ad…`, unchanged since the spec and
verified before running. Every number below was printed by that script or by the one follow-up
check in this note. Nine arms, all complete: D1 and R on four judges, D2 on gpt-4o-mini.

## Pre-registered verdict: ROBUST

Rubric D1 — FaithCoT-Bench's own annotator instruction sheet, Definitions 2 and 3, and all eight
fine-grained subtype definitions, verbatim — against the generic prompt A on the same traces:

| judge | A | D1 | Δ blind | 95% CI | Bonferroni (4) CI |
|---|---|---|---|---|---|
| gpt-4o-mini | 0.679 | **0.682** | +0.003 | [−0.023, +0.030] | [−0.030, +0.038] |
| Llama-3.1-8B | 0.642 | 0.638 | −0.004 | [−0.043, +0.033] | [−0.056, +0.041] |
| Qwen2.5-7B | 0.637 | 0.626 | −0.010 | [−0.053, +0.031] | [−0.066, +0.042] |
| Qwen3-8B | 0.637 | 0.620 | −0.016 | [−0.050, +0.021] | [−0.059, +0.029] |

Every judge is flat; none approaches the strong criterion (Δ ≥ +0.05 and D1 ≥ 0.72). The
best definition-informed blind AUROC of any judge is **0.682**. The ceiling holds for prompted
judges under both a generic rubric and the annotators' own criteria. My recorded prior was 30% on
the rubric-bound outcome; it did not materialise.

The within-generator (pair-weighted) figures move the same way, and no domain flips: on AQuA, where
the blind regime is easiest, gpt-4o-mini goes 0.880 → 0.890 and the others drift down.

## The benchmark's own evaluation prompt (D2) is worse, not better

gpt-4o-mini under the FaithCoT authors' published LLM-judge prompt (three-way 0/1/2 output):
blind **0.638** (Δ −0.041 [−0.076, −0.006]), correct **0.741** (Δ −0.089 [−0.125, −0.055]). The
biggest single drop is on AQuA (0.880 → 0.767). Part of this is instrument: a 0/1/2 label carries
far less ranking information than a 0–100 score, and ties are counted as half. So this does not
show that the authors' prompt is a worse rubric; it shows that a coarse output destroys AUROC, and
that no rubric text tested here lifts the blind regime.

## Revealing the gold answer makes the judge WORSE in the blind regime, and the reason is mechanical

Rubric R is prompt A with the correct answer appended. It is the direct test of the objection that
judges fail on incorrect answers because they cannot tell the answer is wrong (Krumdick et al.).

| judge | A blind | R blind | Δ | 95% CI |
|---|---|---|---|---|
| gpt-4o-mini | 0.679 | 0.617 | −0.061 | [−0.120, −0.006] |
| Llama-3.1-8B | 0.642 | 0.585 | −0.056 | [−0.106, −0.008] |
| Qwen2.5-7B | 0.637 | 0.567 | −0.070 | [−0.124, −0.013] |
| Qwen3-8B | 0.637 | 0.579 | −0.057 | [−0.124, +0.006] |

Four of four move down, three significantly at 95%. The correct regime is unchanged (gpt-4o-mini
0.830 → 0.836).

**Why (one follow-up check, not pre-registered).** With the answer visible the judge's score
becomes a correctness grader: its AUROC against *incorrectness* jumps from 0.683 to **0.918**
(gpt-4o-mini), 0.641 → 0.901 (Qwen3-8B), 0.630 → 0.834 (Llama). Mean score on incorrect-answer
traces rises for honest errors and unfaithful errors **together** — gpt-4o-mini: ft1 24 → 69,
ft2 40 → 79 — so within the blind regime the two classes stay as far apart as before while the
judge's attention has moved to the wrong variable. Correct-answer traces are untouched (ft3 14 → 9).

This is the paper's composition mechanism produced on demand: give a judge a correctness signal and
it grades correctness. It also disposes of the objection it was designed to test. The judges' blind
regime failure is not that they cannot tell the answer is wrong; telling them makes it worse.

## What this settles and what it does not

- **Settled for prompted judges:** the blind-regime ceiling is not a rubric artefact. Generic
  prompt, annotators' criteria, the benchmark's own prompt, and answer-revealed prompt all sit at or
  below 0.68. The "maybe the ceiling is prompt-bound" threat from BonaFide's definition-informed
  result does not transfer to this benchmark.
- **The Krumdick objection is answered in the wrong direction for it:** reference access hurts.
- **Not settled:** trained detectors (the CIE-Scorer reproduction is in progress on Anvil), and
  whether the ceiling is a label-reliability limit — the two label fields still disagree 7% of the
  time here, and no rubric can beat noisy labels. That remains the strongest alternative reading.
- **Not claimed:** that D1 is a fair rendering of what the annotators actually did. The
  instruction sheet is verbatim, but Round II and III discussion is not reproducible in a prompt.

Artefacts: `results/rubric_effect/results.json`; raw arms `results/judge_raw_{qwen3_8b,llama31_8b,
qwen25_7b,mini}_{D1,R}.jsonl`, `results/judge_raw_mini_D2.jsonl`; rubric texts and hashes in
`scripts/judge_rubrics.py`. Cost: about $0.70 of API credit and two hours of local GPU.
