# Paper positioning — BlackboxNLP (EMNLP 2026 workshop)

**Target venue:** BlackboxNLP @ EMNLP 2026 (workshop on analyzing & interpreting neural
networks for NLP). Archival track. *Verify the 2026 CFP deadline (historically ~Aug).*
**Why it fits:** the work is an analysis / limits-of-black-box study with a metric critique
and a sharp negative-results component — squarely in BlackboxNLP's scope.

## Working title (pick one)
- *The Black-Box Frontier of Chain-of-Thought Faithfulness: Post-Hoc Rationalization on Correct Answers*
- *Answer-Tracing Is Most of What You Get: A Rigorous Audit of Black-Box CoT Faithfulness Detection*

## Thesis (one paragraph)
Instance-level detection of unfaithful chain-of-thought is, on current benchmarks, **saturated
by answer-tracing** and **confounded by answer correctness**. We rigorously test three further
black-box signal families — premise-DAG structure, graph-targeted counterfactual interventions,
and per-step NLI entailment support — and show none beat or meaningfully augment answer-tracing.
We then **localize where all black-box signals fail**: detecting *post-hoc rationalization on
correct answers* is at chance for every method (95% CIs include 0.5 across 4 domains × 4 models).
Finally, we show a **widely-used step-removal faithfulness metric anti-correlates with human
faithfulness**. Together these map the limits of black-box CoT-faithfulness detection and
motivate mechanistic (white-box) methods for the residual frontier.

## Contributions
- **C1 (frontier + black-box-vs-internals contrast).** Across 4 domains × 4 models (n=270 in-regime),
  **no black-box signal detects post-hoc rationalization on correct answers (ft1 vs ft2) above chance** —
  answer-tracing 0.545 [0.468,0.611], interventions 0.485, NLI 0.514, DAG 0.490; all CIs include 0.5.
  Mechanistic reason: post-hoc rationalizations are locally coherent and yield confident, stable answers,
  so they are externally indistinguishable. **Yet the information is internally (partially) present:** a
  linear probe on hidden states detects ft1-vs-ft2 in **Llama-3.1-8B (AUROC 0.71, layers 16–31,
  permutation p=0.01)** though **not significantly in Qwen-2.5-7B (0.62, p=0.32)**. So the distinction is
  *behaviorally inaccessible yet linearly decodable from activations in some models* — the
  black-box-vs-internals contrast that anchors the paper. (Caveat: small n, modest effect, model-dependent;
  Qwen is "not detected," not "absent.")
- **C2 (metric inversion).** The standard step-removal AUC metric (FaithCoT-Bench `soft_faithfulness`)
  **anti-correlates** with human faithfulness: mean diff +0.139 [+0.096, +0.182] (higher for
  *unfaithful* traces). A concrete caution for a widely-used family of interpretability metrics.
- **C3 (rigorous negatives + confound).** Premise-DAG structure (dag_lin 0.469, dag_maxlb 0.544;
  CIs include 0.5) and graph-targeted counterfactual interventions (v2 g 0.56–0.61, dominated)
  do not beat answer-tracing; **answer correctness is the single strongest predictor (0.697\*)** —
  the "unfaithfulness = disguised accuracy" confound, quantified. NLI support only weakly
  significant (0.570\*). Nuance reported honestly: DAG `max_lb` *is* weakly significant on **math**
  (aqua 0.636\*) where premise structure is explicit.
- **(Methodological) Circularity caution.** The benchmark's own faithfulness label is an
  answer-tracing metric; naively correlating a structural metric against it is near-circular
  (we reproduce the trap: ρ=0.87 that collapses to ~0.5–0.7 against the human label).

## Abstract sketch (draft)
> Chain-of-thought (CoT) faithfulness — whether a model's stated reasoning reflects the process
> that produced its answer — is increasingly central to oversight. We ask how far *black-box*
> signals can go at detecting instance-level CoT unfaithfulness. On FaithCoT-Bench (4 domains, 4
> models) and GRACE, we find instance-level detection is saturated by answer-tracing and strongly
> confounded by answer correctness; three further signal families (premise-DAG structure,
> graph-targeted counterfactual interventions, NLI step-support) fail to beat or augment it
> (bootstrap 95% CIs). We localize the failure: detecting *post-hoc rationalization on correct
> answers* is at chance for every black-box method, because such rationalizations are locally
> coherent and yield stable answers. We further show a widely-used step-removal faithfulness
> metric anti-correlates with human judgments. Our results bound black-box faithfulness detection
> and motivate mechanistic approaches for the residual frontier.

## Positioning vs prior work (the delta)
- **vs FaithCoT-Bench (ICLR 2026)** — they introduce the benchmark and show detectors are weak *in
  aggregate*. We (a) **localize** the failure to a specific regime (post-hoc-on-correct) with CIs;
  (b) show **their own metric inverts**; (c) test **three method families not in their 11**
  (premise-DAG structure, graph-targeted interventions, NLI support); (d) add a **second benchmark**.
- **vs PARC (ICML 2025)** — we repurpose its premise-DAG idea for faithfulness and show (with gold
  premise validation on PERL) that DAG structure does **not** transfer to faithfulness on NL reasoning.
- **vs GRACE (2026)** — used as an independent step-level faithfulness benchmark for replication.

## Experiment status (for the paper)
- DONE: scale (4×4, n=634 complete-feature / 1304 traces), bootstrap CIs, C1, C2, C3; heuristic
  extractor F1 0.57 vs PERL gold; **LLM extractor R 0.82 / F1 0.79 vs PERL gold** (licenses the v2
  fair-test claim — the intervention null is not an extraction artifact); **GRACE step-level NLI
  replication (preliminary)** — NLI ≈ chance (0.51–0.58), consistent with FaithCoT but only 8
  unfaithful steps in the public sample.
  **White-box pilot DONE:** internal linear probe detects ft1-vs-ft2 in Llama (AUROC 0.71, p=0.01),
  not significantly in Qwen (p=0.32) — C1 upgraded to the black-box-vs-internals contrast.
- REMAINING (in priority order):
  1. **Firm up the probe** — mean-pool / per-layer-per-token reps, nonlinear probes, more models, to
     pin the Llama-vs-Qwen asymmetry (currently small-n, single permutation test).
  2. Full GRACE eval set (437 traces) for a conclusive 2nd-benchmark claim (email authors / await release).
  3. Write-up.

## Honest acceptance read
With C1/C2 CI-backed (done) + GRACE + LLM-extraction validation + write-up → a **credible
BlackboxNLP submission** (it has two novel positive-flavored findings, not just nulls). The
white-box pilot would push it from borderline toward solid. Main residual risks: GRACE only ships
40 labeled examples publicly (second-benchmark evidence is preliminary until release); HLE_BIO n is
small. BlackboxNLP is selective for a workshop, so execution on the remaining items matters.

## Anticipated reviewer objections → responses
- *"Negative results — did you try hard enough?"* → four method families, **proper LLM extraction
  (validated vs gold)**, bootstrap CIs, 4 domains × 4 models; and C1/C2 are positive findings.
- *"Single benchmark."* → GRACE second benchmark (preliminary; full on release).
- *"Novelty over FaithCoT-Bench."* → failure **localization** + **metric inversion** + new methods.
- *"Small n in the key regime."* → ft1v2 now n=270 with CIs.
- *"Extraction was weak."* → heuristic F1 0.57 reported; v2 uses LLM extraction, **validated at
  0.82 recall / 0.79 F1 vs PERL gold** — so the intervention null is a fair test, not an artifact.
