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

## Documents

- [Research direction](research-direction.md)
- [Experimental plan](experimental-plan.md)
- [Literature map](literature-map.md)

