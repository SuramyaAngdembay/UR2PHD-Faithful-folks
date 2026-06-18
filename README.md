# ChainTrackers Research Notes

## Proposed Topic

**Premise-Grounded Detection of Unfaithful Chain-of-Thought Reasoning**

This project studies whether an LLM's visible chain-of-thought (CoT) is supported
by the problem, earlier reasoning steps, and relevant external evidence. The main
goal is to improve the detection and localization of unfaithful reasoning rather
than merely checking whether the final answer is correct.

## Core Idea

Existing faithfulness detectors often judge an entire CoT as unstructured text.
Our proposed method instead represents the CoT as a graph:

- Each node is an individual reasoning step.
- Each edge identifies a premise used by that step.
- External evidence is attached to factual claims where needed.
- Counterfactual tests target the premises most likely to affect the answer.

The resulting structural and evidence-based signals are combined to determine
whether the reasoning trace is faithful and which step first becomes unsupported.

## Primary Research Question

> Can premise graphs, evidence checks, and targeted counterfactual interventions
> detect unfaithful chain-of-thought reasoning better than current whole-trace
> LLM-as-judge and perturbation-based methods?

## Scope

The initial project will focus on detection and evaluation, not on proving that
the written CoT exactly represents the model's hidden computation. A later
white-box extension may use linear probes or activation interventions to study
when the model forms its answer internally.

MCP may be used as implementation infrastructure for tool calls, evidence
retrieval, and trace logging. It is not the primary research contribution and
does not replace RAG or provide faithfulness by itself.

## Datasets

**Primary target: FaithCoT-Bench / FINE-CoT** (ICLR 2026) — the only instance-level CoT
*faithfulness* benchmark, with expert annotations and step-level evidence. Its four domains define
our core evaluation: **LogiQA** (logical), **TruthfulQA** (factual / common misconceptions),
**AQuA** (math word problems), and **HLE-Bio** (biomedical, knowledge-intensive). Instance-level
detection is scored by F1 / accuracy / Cohen's κ; localization is scored against the step-level
evidence annotations.

**Potential / supporting datasets**, grouped by role (rationale in
[related-work-and-positioning.md](related-work-and-positioning.md) §4):

| Role | Datasets |
|---|---|
| Faithfulness-labeled (evaluation) | **FaithCoT-Bench / FINE-CoT** *(primary)*, GRACE, RFEval |
| Step-error / first-error localization (baselines) | ProcessBench, DeltaBench, REVEAL, PRM800K, PRMBench, BIG-Bench Mistake |
| Gold premises → clean counterfactual interventions | FOLIO (FOL-verified premises), StrategyQA (gold decomposition + per-step Wikipedia evidence), EntailmentBank |
| Knowledge-intensive substrate (trace source / retrieval; *no* faithfulness labels) | CRAG benchmark, HotpotQA, 2WikiMultiHopQA, MMLU-Pro |
| Controlled math errors | PARC's **PERL** (premise + error annotations) |

**Deprioritized:** plain GSM8K as a faithfulness set — it measures answer correctness, not CoT
faithfulness; use PERL for controlled math-error checks instead. Always report synthetic-corruption
vs. real-error results **separately** (synthetic negatives are systematically easier to detect).

## Documents

- [Research direction](research-direction.md)
- [Experimental plan](experimental-plan.md)
- [Related work & positioning](related-work-and-positioning.md)
- [Literature map](literature-map.md)

