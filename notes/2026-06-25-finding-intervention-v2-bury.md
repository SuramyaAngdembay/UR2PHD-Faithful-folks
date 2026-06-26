# Decision-gate (2026-06-25): premise-DAG / targeted-intervention line — BURIED

*Harness: `scripts/intervention_harness_v2.py` (LLM/PARC Aggregative extraction, continuous
option-probability-shift metric, load-bearing+descendants ablation vs size-matched random,
local Llama-3.1-8B, 188 LLaMA traces). Results: `~/intervention_v2_results.json` on Aquaman.*

## Result (AUROC vs human `unfaithfulness`)
| subset | n | %unfaith | **g** | imp_t | soft |
|---|---|---|---|---|---|
| POOLED | 188 | 45% | 0.563 | 0.505 | 0.672 |
| INCORRECT (ft 3v4) | 99 | 20% | 0.606 | 0.549 | 0.713 |
| CORRECT (ft 1v2) | 89 | 72% | 0.554 | 0.534 | 0.578 |

mean g: faithful +0.022, unfaithful −0.005.

## Verdict: BURY
- With proper LLM extraction the **sign is correct** (faithful → higher g), so the mechanism
  isn't noise — but **g is weak (0.56–0.61) and `soft` (answer-tracing) beats it everywhere.**
- Pre-registered rule was "beat `soft` → build, else bury." It fails → **the premise-DAG and
  targeted-counterfactual-intervention line is buried as a primary signal.**
- Three rigorous strikes: (1) observational DAG structure null; (2) v1 intervention null;
  (3) v2 intervention weak & dominated.

## Correction (important)
The earlier "incorrect regime is wide open / answer-tracing at chance (0.50)" finding was a
**stratification artifact** of the noisy `parsed_final_answer==label` correctness flag. Using
the *annotated* `faithful_type` correctness split, **`soft` retains strong signal in the
incorrect regime (0.713)**. So there is NO regime where everything fails and a DAG method
uniquely wins — which removes the core motivation for the intervention angle.

## Where the signal actually is (the honest landscape)
- **Answer-tracing (`soft`) is the one real signal**, ~0.67–0.71 AUROC vs the human label —
  but it is FaithCoT-Bench's own metric, so reproducing it is not a contribution.
- **Correctness is a strong confound** (~0.76).
- **Premise-DAG structure & interventions add nothing** beyond these.
- To contribute we must **beat or augment `soft`** with a genuinely different signal.

## Pivot options (next)
1. **Per-step premise-grounded SUPPORT verification (NLI/entailment)** — does "does each step
   actually follow from its premises/context?" (REVEAL/ReCEval/VeriCoT-style) beat or add to
   `soft`? Last untested mechanism that is genuinely different from answer-tracing. Cheap-ish
   (NLI model + per-step entailment). **Recommended next test.**
2. **Learned multi-signal detector** (soft + NLI-support + perplexity, correctness-controlled)
   — engineering a detector that beats `soft`; solid but less novel.
3. **Reframe to a rigorous analysis / negative-results contribution** — "structure and
   interventions don't help; the accuracy confound; an honest baseline of what works for
   instance-level CoT faithfulness." We have most of this already. Strong fallback.
