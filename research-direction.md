# Research Direction

## 1. Motivation

Large language models can produce fluent reasoning that does not reflect the
information that caused their answer. A model may:

- reach an answer before producing its explanation;
- construct plausible reasoning after committing to an answer;
- rely on an unstated or invalid premise;
- ignore supplied evidence while appearing to cite it; or
- produce a correct answer through an invalid reasoning path.

Final-answer accuracy cannot reveal these failures. A useful detector must
inspect both the reasoning structure and the evidence supporting each step.

## 2. Proposed Problem

Given a question, a generated CoT, and its final answer, predict:

1. whether the reasoning trace is faithful;
2. which step first becomes unsupported or causally irrelevant; and
3. which premise or evidence item is responsible for the failure.

The project targets **observable trace faithfulness**: whether the stated
reasoning is sufficiently supported and affects the answer as claimed. This is
different from the stronger mechanistic claim that the text exactly describes
the model's internal computation.

## 3. Proposed Method

### Step A: Decompose the CoT

Split the reasoning into atomic steps. Each step should express one claim,
inference, calculation, or conclusion.

### Step B: Construct a Premise Graph

For every step, identify the minimum set of dependencies:

- facts from the original question;
- earlier reasoning steps;
- retrieved external evidence; and
- applicable rules, formulas, or definitions.

This produces a directed acyclic graph similar to a proof or argument graph.

### Step C: Verify Local Support

Check whether each step follows from its declared premises. The verifier can use
a combination of:

- an LLM judge constrained to inspect only the declared premises;
- symbolic calculation for arithmetic steps;
- natural-language inference;
- claim extraction and evidence retrieval; and
- contradiction or entailment scoring.

### Step D: Test Causal Relevance

Use the graph to select load-bearing premises. Remove, replace, or contradict a
selected premise and observe whether the downstream reasoning and answer change
appropriately.

Random perturbations often modify irrelevant text. Graph-guided perturbations
should produce a stronger faithfulness signal because they target dependencies
the model itself claims to use.

### Step E: Aggregate the Signals

Combine features such as:

- unsupported-step count;
- premise entailment score;
- evidence coverage;
- contradiction score;
- sensitivity to targeted perturbations;
- consistency between the graph and final answer; and
- location of the first invalid step.

The first version can use a transparent weighted score or lightweight
classifier. A large training run is not required.

## 4. Main Hypotheses

**H1:** Premise-aware verification will outperform whole-trace judging for
instance-level unfaithfulness detection.

**H2:** Graph-guided counterfactual interventions will outperform random or
position-based perturbations.

**H3:** Evidence grounding will provide the largest gains on knowledge-intensive
tasks, where a fluent judge cannot reliably verify factual claims from its own
memory.

**H4:** The combined method will improve error localization even when gains in
final-answer accuracy are small.

## 5. Expected Contribution

The intended contribution is not a new general-purpose reasoning model. It is a
faithfulness detector that:

- converts free-form CoT into an auditable dependency structure;
- checks factual and logical support at the step level;
- selects causally meaningful counterfactual interventions; and
- reports both an instance label and an explanation of the detected failure.

## 6. Why This Direction Has Upside

Recent benchmarks indicate that current detectors remain imperfect, especially
for knowledge-intensive questions and convincing traces produced by stronger
models. Premise-based methods have independently improved reasoning-error
identification, but their structure has not been fully combined with
evidence-grounded and causally targeted faithfulness detection.

This creates a plausible opening for measurable gains without training a
frontier-scale model.

## 7. Boundaries and Risks

- Better external verification does not prove mechanistic faithfulness.
- Premise extraction errors can propagate into the detector.
- An LLM verifier may share the generator's factual mistakes.
- Retrieval quality may be confused with reasoning faithfulness.
- Tool and graph construction overhead may outweigh small gains.
- A structured JSON implementation must be included as a baseline so any gains
  are not incorrectly attributed to MCP.

The project should be reconsidered if a pilot cannot improve detection or
localization over strong judge baselines by a meaningful margin.

