# Experimental Plan

## 1. Primary Dataset

Use **FaithCoT-Bench / FINE-CoT** as the primary benchmark because it is designed
for instance-level CoT faithfulness and includes expert annotations and
step-level evidence.

Prioritize:

- TruthfulQA and HLE-Bio for knowledge-intensive reasoning;
- LogicQA for logical dependencies; and
- AQuA for mathematical reasoning.

GSM8K may be used as a supplementary controlled math dataset, but it should not
be the only dataset because ordinary GSM8K labels measure answer correctness,
not CoT faithfulness.

## 2. Experimental Conditions

Compare the proposed method against:

1. final-answer correctness;
2. whole-trace LLM-as-judge;
3. step-level LLM-as-judge;
4. random or position-based counterfactual perturbation;
5. premise graph without evidence retrieval;
6. evidence checks without a premise graph; and
7. the complete premise-grounded detector.

Useful ablations:

- remove graph-guided perturbation;
- remove external evidence;
- replace inferred premise links with gold links when available;
- compare small and strong premise extractors;
- compare structured JSON orchestration with an MCP implementation; and
- test whether verifier and generator model families should differ.

## 3. Metrics

### Detection

- macro F1;
- precision and recall for unfaithful traces;
- AUROC or AUPRC when confidence scores are available; and
- calibration error.

### Localization

- first-error identification accuracy;
- step-level precision, recall, and F1;
- premise-link precision and recall; and
- evidence attribution accuracy.

### Intervention

- answer-flip rate after perturbing a load-bearing premise;
- inappropriate stability when critical evidence changes;
- inappropriate sensitivity to irrelevant perturbations; and
- counterfactual consistency.

### Practical Cost

- inference tokens;
- number of verifier or retrieval calls;
- latency; and
- estimated cost per example.

Report confidence intervals and paired significance tests rather than relying
only on point estimates.

## 4. Success Criteria

An encouraging pilot result would be one of:

- at least 5 absolute F1 points over a strong judge baseline on a targeted
  knowledge-intensive subset;
- a clear improvement in first-error or step-level localization;
- substantially better sensitivity to critical perturbations without increased
  sensitivity to irrelevant perturbations; or
- comparable detection performance using a smaller or cheaper judge.

Small gains in answer accuracy alone are not sufficient because the proposed
method primarily targets detection and auditability.

## 5. Minimum Viable Study

1. Reproduce one or two FaithCoT-Bench baselines.
2. Segment traces and infer premise links.
3. Implement premise-restricted step verification.
4. Add graph-guided perturbation.
5. Evaluate on one logical and one knowledge-intensive subset.
6. Run ablations and analyze common failure cases.

This version avoids model training and deep mechanistic analysis. It is suitable
for obtaining initial results before expanding the project.

## 6. Optional Mechanistic Extension

If time and compute permit, use an open-weight model to probe answer formation:

- before evidence is supplied;
- after evidence retrieval;
- before CoT generation;
- during the reasoning trace; and
- before the final answer.

This can test whether premise-grounded evidence changes the model's internal
answer representation or merely changes its written explanation. Begin with
linear probes; treat activation patching as a later extension.

## 7. Suggested Work Sequence

### Phase 1: Baselines

Read the benchmark code, reproduce reported evaluation, and identify the weakest
task/model combinations.

### Phase 2: Structural Detector

Implement CoT segmentation, premise-link prediction, and local verification.

### Phase 3: Evidence and Interventions

Add evidence retrieval for factual claims and target counterfactual tests using
the premise graph.

### Phase 4: Evaluation

Run ablations, significance tests, cost analysis, and qualitative error
analysis.

