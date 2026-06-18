# Literature Map

## Core Papers

### FaithCoT-Bench

**FaithCoT-Bench: Benchmarking Instance-Level Faithfulness of Chain-of-Thought
Reasoning**

- Role in this project: primary benchmark and source of detector baselines.
- Key opening: existing detection approaches remain imperfect, especially on
  knowledge-intensive tasks and plausible traces from stronger models.
- Link: <https://openreview.net/forum?id=lN3yKqqzF1>

### Premise-Augmented Reasoning Chains

**Premise-Augmented Reasoning Chains Improve Error Identification in Math
Reasoning**

- Role in this project: motivates converting linear CoT into explicit premise
  dependencies.
- Key opening: apply premise structure to faithfulness detection, targeted
  interventions, and knowledge-intensive reasoning rather than only math-error
  identification.
- Links:
  - <https://proceedings.mlr.press/v267/mukherjee25a.html>
  - <https://arxiv.org/abs/2502.02362>

### Decoding Answers Before Chain-of-Thought

**Decoding Answers Before Chain-of-Thought**

- OpenReview title/version: **Post-Hoc Reasoning in Chain-of-Thought**.
- Role in this project: shows why fluent written reasoning cannot automatically
  be treated as a faithful account of internal computation.
- Key opening: test whether structured evidence and premise verification reduce
  post-hoc rationalization or merely make it easier to detect.
- Links:
  - <https://arxiv.org/abs/2603.01437>
  - <https://openreview.net/forum?id=UMUYpeXtJQ>

## Related Direction: Mechanistic Verification

Mechanistic methods use internal activations, attribution graphs, probes, or
causal interventions to study reasoning. They can support stronger causal
claims, but they require open model weights, substantial implementation care,
and more compute.

For the initial project, mechanistic analysis should be treated as an optional
extension rather than the core method. The premise-grounded detector can first
be evaluated as a model-agnostic black-box or gray-box approach.

## Relationship to RAG and MCP

RAG is a retrieval pattern: relevant information is retrieved and supplied to a
model. MCP is a protocol for exposing tools and data sources to an agent. They
are not direct replacements for each other.

For this project:

- retrieval can supply evidence for factual verification;
- structured tool calls can preserve provenance;
- MCP can standardize retrieval and verification tools;
- logs can record which evidence was available at each step; but
- neither retrieval nor MCP guarantees that the model used the evidence.

The research question is therefore whether premise- and evidence-aware
verification improves faithfulness detection, not whether MCP itself improves
reasoning.

## Literature Questions to Track

While reading new papers, record:

- What definition of faithfulness is used?
- Is faithfulness measured at the trace, step, or mechanistic level?
- Are interventions random or causally targeted?
- Does the benchmark provide human labels or synthetic corruption?
- Does the method require model internals?
- How does it separate retrieval failure from reasoning failure?
- Does it evaluate knowledge-intensive tasks?
- Are gains significant after accounting for cost and judge-model size?

