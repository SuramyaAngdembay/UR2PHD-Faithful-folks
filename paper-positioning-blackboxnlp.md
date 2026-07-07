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
- **C4 (synthetic-proxy caution + 7-model internal replication).** With ground-truth *constructed*
  labels (answer-first vs reason-first CoT on AQuA+GSM8K), the post-hoc-on-correct distinction is
  **internally decodable and permutation-significant in ALL SEVEN models across three families spanning
  2024→2026** — Qwen2.5 0.81, Gemma-4-12B (2026) 0.80, Llama 0.74, Qwen3 0.72, DeepSeek-R1-Distill 0.62,
  Gemma-2 0.60, DeepSeek-R1-0528 (2026) 0.56/perm-obs 0.688 (held-out) — generalizing across math datasets
  (0.52–0.73), effect model-dependent (strong in Qwen2.5/Gemma-4/Llama; weak-but-sig in reasoning-distills
  + Gemma-2; sharp within-family jump Gemma-2 0.60→Gemma-4 0.80). Surface baseline ≈0.47–0.55 for five of
  seven ⇒ genuinely internal (Llama 0.64, Gemma-4 0.665 partial tell, WB clears by ~0.1). Independently
  confirms C1's internals leg under clean labels, and recovers a Qwen signal that was n.s. on noisy human
  labels. (Gemma-4-12B run via 2-GPU pipeline sharding on the 8 GB cards; R1-0528 n=81 from reasoning
  overflow.) **But a
  probe trained on real FaithCoT post-hoc does NOT transfer to the synthetic construction (or vice
  versa): ~chance even best-of-layers and domain-matched, and the two peak at different depths
  (synthetic early L9/L10, real late L29/L22).** ⇒ prompt-induced answer-first is **not a
  representational proxy** for organic post-hoc rationalization — a caution for the common practice of
  training/evaluating faithfulness detectors on synthetically-constructed unfaithfulness.
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
  **White-box pilot + firm-up (a,b,d,e) DONE:** Llama **held-out AUROC 0.70 / F1 0.70** (25×70/30),
  **cross-domain 0.60–0.71** (leave-one-domain-out), signal **~linear** (MLP no gain), perm p=0.03; Qwen
  weak (held-out 0.58); mechanism **model-dependent** (pre-CoT answer-commitment sig in Qwen p=0.044
  uncorrected, null in Llama). C1 = the black-box-vs-internals contrast. **Item (c) causal steering
  (2026-07-02): weak/suggestive** — post-hoc direction perturbs answers ~2–3× more than random at +6σ
  (functionally active but modest; n=51, large-α only). **All white-box a–e done.**
  **Synthetic-construction generalization DONE (2026-07-04, scaled to 4 models 2026-07-05):** matched
  genuine (reason-first, keep-if-correct) vs post-hoc (answer-first, rationalize gold) CoT on **AQuA+GSM8K**
  across **7 models / 3 families spanning 2024→2026** — Qwen2.5-7B (277), Gemma-4-12B/2026 (248),
  Llama-3.1-8B (229), Qwen3-8B (175), DeepSeek-R1-Distill-7B (251), Gemma-2-9b (243), DeepSeek-R1-0528/2026
  (81). **WB probe permutation-significant in ALL SEVEN** (held-out 0.81/0.80/0.74/0.72/0.62/0.60/0.56),
  generalizing across AQuA↔GSM8K (0.52–0.73), model-dependent (strong Qwen2.5/Gemma-4/Llama, weak-but-sig
  reasoning-distills + Gemma-2); surface baseline ≈0.47–0.55 (Llama 0.64, Gemma-4 0.665 caveat). Gemma-4-12B
  run via 2-GPU sharding on the 8 GB cards. **But the FaithCoT↔synthetic bridge
  FAILS** (Llama/Qwen2.5 only — FaithCoT has no real traces for the newer models) — synthetic post-hoc peaks
  early (L9/L10), real ft1v2 late (L29/L22); cross-distribution transfer ~chance even best-of-layers/
  domain-matched (Llama 0.55, Qwen 0.60). ⇒ synthetic answer-first is NOT a representational proxy for
  organic post-hoc (**C4**).
- REMAINING (in priority order):
  1. **Write-up** — fold in synthetic 7-model WB (0.56–0.81, all perm-sig, incl. 2026 Gemma-4-12B) and C4.
  2. Full GRACE eval set (437 traces) for a conclusive 2nd-benchmark claim (email authors / await release).
  3. *(optional, needs aggregate >16 GB)* Gemma-4-31B / 26B-MoE / DeepSeek-V4 — exceed 2×8 GB even sharded.

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
