# External cross-checks: GRACE is now released

Checked September 12, 2026. This supersedes historical notes saying only a
40-example GRACE sample was accessible. No new judge inference was performed.

## Verified GRACE release

Official repository: https://github.com/pvhoang14/GRACE-benchmark

Pinned revision: `63b6b2d57839bf4a44e9f74572b2f8c5898e3f39`, commit timestamp
2026-08-24T02:20:50Z. Downloaded all four test JSONLs and verified parsing/counts:

| Task | Traces | Steps | Distinct source question IDs |
|---|---:|---:|---:|
| LogiQA | 106 | 545 | 100 |
| MuSiQue | 106 | 486 | 103 |
| ReClor | 114 | 574 | 101 |
| 2WikiMultihop | 111 | 439 | 100 |
| Total | 437 | 2,044 | 404 task-qualified questions |

The authors describe test annotations as human and training annotations as LLM
consensus. Published metadata reports 766 unfaithful test steps (37.5%) and
6,915 training traces / 29,612 training steps. Training JSONLs were listed via
the pinned Git tree but not downloaded in this check. Test contexts, questions,
answers, steps, citations, and labels are present. Item-level explanations and
test performance were not inspected. Labels/explanations/gold answers must be
excluded from inference inputs.

Archive and file hashes are in the independent review workspace under
`grace-release-2026-09-12/manifest.json`. This is a schema/availability audit,
not a validation of label reliability or an experimental result.

## Scientific use

Prioritize GRACE as an external check of grounding and logical-inference
components. It does not supply hidden-process dependence labels or automatically
replicate the original two-regime claim. The test set deliberately includes
difficult verifier-disagreement cases, so it is not a natural prevalence sample.

Before evaluation, check overlap with the prior 40-example sample and shared
upstream questions, including FaithCoT LogiQA. Use train/development data for
format adaptation; freeze a versioned step-level protocol before test inference.
Our existing whole-trace instrument is not automatically a native step evaluator.

Compare generic and component procedures with the same evidence, plus NLI and
an appropriate grounding baseline. Retain context-withheld diagnostics separately
from the full-context native task. Report step detection/localization, false
allegations, task/error-category breakdowns, and question-cluster uncertainty.
The 2,044 steps are not 2,044 independent examples. Keep any derived whole-trace
aggregation explicit and separate from native whole labels in the other datasets.

## Other verified options

- FACE-Eval code: https://github.com/aryopg/FACE-Eval . Data and results repositories
  are public and ungated, with actual parquet/inference JSONL artifacts listed:
  https://huggingface.co/datasets/edinburgh-dawg/face-eval
  (`7d164709467403a9adb49325ecf9191ddb4ec124`) and
  https://huggingface.co/datasets/edinburgh-dawg/face-eval-results
  (`515627abb8e814be4ac13f59c8453b5d1fa9be2f`). This check listed artifacts rather
  than downloading all model trajectories. Use for cue adoption/disclosure and
  presentation-channel transfer. Separate behavior from verbalization, verify
  monitor/annotation provenance, and keep denominators explicit. Not whole-process
  ground truth. Paper: https://arxiv.org/html/2608.29464v2 .
- ProcessBench is public and ungated at https://huggingface.co/datasets/Qwen/ProcessBench
  (`3bdcd5371ed567559a78f559c01c13a6deee7604`), with GSM8K/MATH/OlympiadBench/
  Omni-MATH JSON files. Code: https://github.com/QwenLM/ProcessBench . Use for
  mathematical error detection/localization and final-answer correctness controls;
  not a reference for whether the trace caused the answer.
- C2-Faith remains a relevant design for consistency/coverage controls, but this
  check did not establish a downloadable official release. Do not mark it ready
  solely because the paper is accessible: https://arxiv.org/html/2603.05167v2 .

GRACE should enter the immediate plan alongside BonaFide replication. FACE-Eval
is the next complementary check. These can precede a large new corpus; they do
not eliminate the need for common-example reference comparison and independently
checkable process records.
