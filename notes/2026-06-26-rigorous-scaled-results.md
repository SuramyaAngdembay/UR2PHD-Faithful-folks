# Rigorous scaled results (2026-06-26): F1 & F2 confirmed with CIs

> **⚠️ CORRECTION (2026-07-16):** The `faithful_type` regime labels used in this note are INVERTED
> relative to the released FaithCoT data: in the data, **ft1/ft2 = INCORRECT-answer regime, ft3/ft4 =
> CORRECT-answer regime** (the repo README's pairing is wrong; verified per-domain vs parsed answers and
> by reproducing the paper's own statistics; independently reported in FaithCoT-BENCH issue #3).
> All numbers in this note are valid; wherever it says "correct-answer regime / post-hoc-on-correct
> (ft1v2)" read "incorrect-answer regime". See `notes/2026-07-16-data-validation.md`.


*`scripts/rigorous_analysis.py` — all 4 domains × 4 models, 1,304 traces extracted, n=634
with complete answer-tracing features. AUROC vs human `unfaithfulness` with bootstrap 95% CI;
`*` = CI excludes 0.5 (significant). Features cached: `~/rigorous_features.json` on Aquaman.*

## ALL domains+models (n=634, 38% unfaithful)
| signal | AUROC | 95% CI | sig |
|---|---|---|---|
| **correct** | **0.697** | [0.662, 0.733] | * |
| soft (answer-tracing) | 0.652 | [0.611, 0.696] | * |
| avg_impact | 0.627 | [0.585, 0.670] | * |
| hard | 0.612 | [0.572, 0.656] | * |
| nli_n_unsup | 0.570 | [0.524, 0.617] | * |
| dag_maxlb | 0.544 | [0.495, 0.590] | ns |
| nli_min_ent | 0.494 | [0.446, 0.545] | ns |
| dag_lin | 0.469 | [0.423, 0.519] | ns |

→ **F4/F5 confirmed with CIs:** DAG structure features are **not significant** (CIs include 0.5);
correctness is the strongest predictor; answer-tracing modest. NLI only weakly significant (0.570).

## F1 FRONTIER — ft1v2 (post-hoc rationalization on CORRECT answers), n=270, 60% unfaithful
| signal | AUROC | 95% CI |
|---|---|---|
| soft | 0.545 | [0.468, 0.611] |
| avg_impact | 0.485 | [0.410, 0.556] |
| nli_n_unsup | 0.514 | [0.448, 0.585] |
| dag_maxlb | 0.490 | [0.420, 0.561] |
| (all others) | ~0.49–0.55 | CI includes 0.5 |

→ **F1 confirmed with rigor: EVERY signal's CI includes 0.5 (n=270).** Nothing detects post-hoc
rationalization on correct answers above chance. This is the clean, statistically-backed frontier.

## ft3v4 (INCORRECT answers), n=363, 22% unfaithful
soft 0.666* / avg_impact 0.659* / nli_n_unsup 0.600* significant; dag features ns. → answer-tracing's
overall signal is carried by the incorrect regime, not the post-hoc-on-correct regime.

## Per-domain (AUROC, * sig)
- logiqa (n=200): soft 0.756* | correct 0.760* (strongest)
- truthfulqa (n=189): soft 0.698* | correct 0.755* | nli_n_unsup 0.627*
- aqua/math (n=165): soft 0.624* | **dag_maxlb 0.636*** (DAG structure has signal ONLY on math) | nli_n_unsup 0.629*
- HLE_BIO (n=80): **everything ns** (all CIs include 0.5) — a second frontier (hard knowledge-intensive; small n)

## F2 METRIC INVERSION (rigorous)
mean(`soft`|unfaithful) − mean(`soft`|faithful) = **+0.139, 95% CI [+0.096, +0.182]** → the standard
step-removal AUC metric **significantly anti-correlates** with human faithfulness (higher for
unfaithful). Clean, novel methodological finding.

## Honest nuance to report
DAG structure is genuinely uninformative on NL reasoning (logiqa/truthfulqa) but **weakly significant on
math (aqua, dag_maxlb 0.636*)** — where premise structure is explicit. Report this rather than a blanket
"structure never helps."

## Remaining
- Validate the **LLM** extractor on PERL (heuristic was F1 0.57; v2 used LLM — need its recall to license v2).
- **GRACE** step-level NLI replication (40 examples, preliminary 2nd-benchmark check).
