# Validation runs (2026-06-29): LLM-extractor quality + GRACE 2nd-benchmark

*Scripts: `scripts/validate_extraction_llm.py`, `scripts/grace_nli_replication.py`. Run on Aquaman.*

## Item 3 — extractor validation vs PERL gold premise links (DONE, favorable)
| extractor | precision | recall | F1 |
|---|---|---|---|
| heuristic (regex) | 0.56 | 0.58 | 0.57 |
| **LLM Aggregative (Llama-3.1-8B 4-bit, = v2)** | **0.76** | **0.82** | **0.79** |
| PARC (reported, larger models) | — | ~0.90 | — |

(160 PERL math records, 866 scored steps.)
**Why it matters:** the v2 decision-gate intervention selected load-bearing targets from a DAG built
with the LLM extractor (0.82 recall) — so the "graph-targeted interventions don't beat answer-tracing"
null is a **fair test**, not an extraction artifact. Directly answers the "did you try hard enough?"
reviewer objection. Caveat: PERL gold is **math-only**; NL-domain (truthfulqa/logiqa) extraction is
validated only by proxy (the prompt/model are the same).

## Item 2 — GRACE step-level NLI replication (DONE, preliminary)
GRACE public examples: 40 traces, **171 labeled steps, only 8 unfaithful (5%)**, all *evidence* track.
NLI step-support vs the human step label:
| signal | AUROC |
|---|---|
| entailment | 0.512 |
| support (entail−contra) | 0.522 |
| contradiction | 0.581 |

→ **NLI step-support ≈ chance on GRACE too**, directionally consistent with the FaithCoT finding
(NLI ~0.57). **Caveat: only 8 unfaithful steps → directional, not conclusive** (wide CIs; evidence-track
only). A conclusive 2nd-benchmark claim needs GRACE's full 437-trace eval set (email authors / await
release).

## Net effect on the BlackboxNLP plan
- Item 3 ✅ (extractor validated → v2 null is fair). Item 2 ✅ preliminary (NLI weak replicates).
- Remaining: **white-box pilot** on ft1v2 (highest upside), full GRACE set, write-up.
