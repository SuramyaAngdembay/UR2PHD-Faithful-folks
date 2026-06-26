# Experiment 1 spec — Graph-targeted counterfactual interventions for faithfulness

*Status: design (pre-code). Owner: Suramya. Compute: local GPU, 8B models.
Motivated by Dikshant's PoC (commit 598429e) and [related-work-and-positioning.md](../related-work-and-positioning.md) §3, extension #1.*

## 1. Why this test
Dikshant's PoC established two things on 400 FINE-CoT traces: (a) the **observational
answer-tracing** signal is strong (`avg_impact` vs `soft_faithfulness`, ρ≈0.87), and
(b) **passive premise-DAG structure adds almost nothing** (linearity −0.11, load-bearing
+0.19). Both are derived from the same intermediate answer-probabilities, so the 0.87 is
largely circular and the DAG, used passively, is dead weight.

That leaves exactly one untested, novel, non-circular claim — the project's actual
contribution: **active, graph-targeted counterfactual interventions reveal faithfulness
that passive observation cannot.** This experiment tests it directly and is designed so a
clean *negative* result is still informative (it would falsify the core bet and redirect
us to localization or evidence-grounding).

## 2. Hypotheses (falsifiable)
- **H1 (signal).** The interventional sensitivity gap `g = Δ(targeted) − Δ(random)`
  is larger for human-labeled *faithful* traces than *unfaithful* ones, and `g` detects
  the expert faithfulness label with AUROC meaningfully above chance.
- **H2 (added value — make-or-break).** `g` beats the answer-tracing baseline
  (`avg_impact`) and undirected perturbation (Lanham) at predicting the expert label,
  **and retains predictive value after partialling out `avg_impact` and final-answer
  correctness.** This is the test that the *interventional, graph-targeted* signal adds
  something observation can't.
- **H3 (targeting matters).** DAG-selected load-bearing interventions cause larger,
  more appropriate answer changes than random/peripheral or position-based selection.
- **H4 (localization, optional).** The first step whose targeted intervention flips the
  answer aligns with FINE-CoT step-level evidence better than baselines.

## 3. Intuition (why g should track faithfulness)
- *Faithful* trace: the answer genuinely depends on the reasoning → removing a
  load-bearing premise flips/shifts the answer (Δ targeted high), removing an irrelevant
  step does not (Δ random low) → **g large**.
- *Unfaithful / post-hoc* trace: the answer was decided independent of the stated
  reasoning → intervening anywhere barely moves it (Δ targeted ≈ Δ random ≈ low) →
  **g ≈ 0**.
- This is *interventional appropriate-sensitivity*, distinct from observational
  answer-tracing — the two can diverge, which is the entire point.

## 4. Data & ground truth
- **Traces:** FINE-CoT, TruthfulQA + LogiQA, LLaMA-3.1-8B-Instruct + Qwen2.5-7B-Instruct,
  100/cell = 400 (matches Dikshant's run for direct comparison). Reuse his loader.
- **Ground truth = the human/expert instance-level faithfulness annotation**, NOT
  `soft_faithfulness`/`hard_faithfulness` (those are answer-tracing-style *detector
  outputs* and become baselines, not labels).
- **Phase-0 blocker:** confirm from the FaithCoT-Bench data/code the exact definition and
  provenance of `soft_faithfulness`, `hard_faithfulness`, and whether the expert labels
  (and step-evidence) are in the release. If only computed scores are available, we either
  (i) obtain the expert labels, or (ii) generate our own ground truth via the
  biasing-feature paradigm (plant a hint that changes the answer; faithful CoT verbalizes
  it). Do not proceed to scaled eval until the target label is non-answer-tracing-derived.

## 5. Pipeline
1. **Load trace** (reuse Dikshant's loader) → steps, question, options, final answer,
   expert label.
2. **Premise DAG via LLM extraction** (PARC *Aggregative*: prompt the 8B model to list,
   per step, the prior steps/question it depends on). Keep the regex heuristic as a cheap
   ablation; validate extraction quality on a gold set (FOLIO / a hand-checked sample).
3. **Select intervention targets:**
   - *targeted* = top load-bearing premise (DAG out-degree × descendants);
   - *random* = k randomly chosen non-target steps (average over k≥3 to control variance);
   - *peripheral* = lowest load-bearing step (secondary control).
4. **Counterfactual intervention + re-generation (local 8B):** for each target Sk, build
   the counterfactual prefix (delete Sk / negate Sk / replace Sk), **re-run the model**
   from that point to regenerate the remaining chain and final answer A′. Greedy decoding
   (or average over a few samples with a fixed seed).
5. **Δ measurement:** answer flip (A′≠A) and, where option logits exist, distributional
   shift; `Δ(set) = mean change over that set`.
6. **Score:** `g = Δ(targeted) − Δ(mean random)`; also keep `Δ(targeted)` alone.
7. **Detect & evaluate** against the expert label.

## 6. Baselines & conditions
1. Final-answer correctness (trivial floor).
2. Whole-trace LLM-as-judge ("is this CoT faithful?").
3. **Answer-tracing `avg_impact`** (Dikshant's observational signal) — the key baseline.
4. **Undirected perturbation (Lanham)** = our *random* arm alone, no contrast.
5. Targeted-Δ alone (no random subtraction).
6. **Ours: `g` = targeted − random contrast.**

**Ablations:** LLM vs heuristic premises; intervention type (delete/negate/replace);
number of random controls k; gold DAG (FOLIO) vs inferred; greedy vs sampled regeneration.

## 7. Metrics
- **Detection:** AUROC and **AUPRC** (positive/faithful rate ≈19% → AUPRC matters),
  macro-F1 at a tuned threshold; per domain×model breakdown.
- **Effect size:** mean `g` faithful vs unfaithful + Mann–Whitney U and bootstrap CIs.
- **Added value (H2):** logistic regression `label ~ correct + avg_impact` (baseline)
  vs `+ g` (full) → ΔAUROC + likelihood-ratio test; equivalently partial correlation of
  `g` with the label controlling for {`avg_impact`, `correct`}.
- **Cost:** GPU-hours, generations/trace (≈ 1 targeted + k random re-generations).

## 8. Success / decision criteria
- **Go (core result):** `g` detects the expert label with AUROC clearly > the
  `avg_impact` baseline **and** stays significant after controlling for `avg_impact` +
  correctness (H2), with targeted > random (H3). → this is the paper's headline.
- **Pivot:** if `g` ≈ answer-tracing once controlled, the interventional-DAG bet is
  falsified cheaply → redirect to step-level localization (H4) or evidence-grounding.
- Either outcome is a publishable finding; we report with the correctness/answer-bias
  control throughout (Bentham "disguised accuracy" caveat).

## 9. Threats to validity & mitigations
- *Circularity* → expert label as target; answer-tracing only as a baseline; control for it.
- *Surface-form confound* (deletion changes answer just by shortening) → targeted−random
  **contrast** + multiple random controls average out generic perturbation effects.
- *Premise-extraction noise* → gold-DAG ablation (FOLIO); report extraction precision/recall.
- *Generation stochasticity* → greedy or fixed-seed averaging.
- *Compute* → start on a 40-trace dev slice (1 domain × 1 model), then scale to 400.

## 10. Milestones
- **Phase 0 (day 1): environment + data.**
  - *Compute split:* heavy 400-trace generation + ablations on **Aquaman** (remote, via
    Tailscale `100.110.44.32`; 2× RTX 3070 @ 8 GB, 64 cores, 256 GB RAM, ~100 GB free).
    8 GB VRAM ⇒ **4-bit quantized** inference (AWQ or bitsandbytes), *not* bf16/fp16 —
    run one model per GPU (Qwen → cuda:0, Llama → cuda:1). **local Apple-Silicon Mac**
    only for harness dev on the 40-trace slice (MLX, 4-bit).
  - *Precision caveat:* FINE-CoT traces were generated at full precision; 4-bit
    re-generation can diverge. **Mitigation:** re-derive each trace's *baseline* answer
    under the *same* quantized model and take the targeted−random contrast within that
    model, so quantization cancels in the contrast (never compare 4-bit A′ to the
    original-precision answer). A ≥24 GB GPU would let us use fp16 and drop the caveat.
  - *Models:* `Qwen/Qwen2.5-7B-Instruct` (open, Apache-2.0, no gating) and
    `meta-llama/Llama-3.1-8B-Instruct` (**gated** — accept Meta license on the HF model
    page + HF read token). Use the *same* models that generated the traces.
  - *HF auth:* create read token, accept Llama license, `huggingface-cli login`; download
    weights to the remote box (not the Mac) to avoid a wasted ~32 GB.
  - *Stack:* venv (Python ≥3.10); remote: torch+transformers+accelerate+vllm; local:
    mlx-lm. Smoke-test one generation per model before scaling.
  - resolve label provenance (§4 blocker); lock ground truth; reuse loader/DAG; carve a
    40-trace dev slice.
- **Phase 1 (days 2–4):** LLM premise extraction + load-bearing selection + intervention/
  re-generation harness on local 8B; sanity-check on the dev slice.
- **Phase 2 (days 5–7):** scale to 400; compute baselines + `g`; primary eval + added-value
  regression + controls.
- **Phase 3 (days 8–10):** ablations, per-group + qualitative analysis, write results,
  go/pivot decision.
- **Stretch:** localization (H4); gold-DAG on FOLIO.

## 11. Deliverables
`src/` intervention harness (premise extraction → DAG selection → intervene+regenerate →
score); a results JSON (comparable to `src/poc_results.json`); a results note; and an
explicit go/pivot call on H2.
