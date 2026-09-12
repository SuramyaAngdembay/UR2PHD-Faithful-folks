# GRACE two-regime test (third reference standard) — 2026-09-13

Data: GRACE test split, github.com/pvhoang14/GRACE-benchmark @ 63b6b2d, 437 traces / 2,044 steps,
10 generator models, 4 context-grounded datasets, human step-level faithfulness labels.
Scripts: `scripts/grace_regime_test.py` (NLI pass), `scripts/grace_regime_analysis.py`.

## Why GRACE is a better external target than BonaFide

| | FaithCoT | BonaFide | GRACE |
|---|---|---|---|
| step count -> label | ~chance | **0.878** | **0.491** |
| length by class | — | 14.4 vs 5.8 steps | **4.68 vs 4.65** |
| both classes both regimes | yes | no (7 correct) | yes (under a non-degenerate rule) |
| entanglement lift | 1.74x | 1.00x (selection) | **1.15–1.65x** |

The length confound that dominated every BonaFide result is absent here.

## Aggregation is a researcher degree of freedom — disclosed, not concealed

GRACE's native label is step-level. A trace-level label requires an aggregation rule, and the rule
moves the 2x2 hard: "any non-faithful step" starves the faithful-incorrect cell to **9**; a majority
rule gives 112/79/55/191. I inspected those counts before analysing, so no pre-registration is
claimed. Two defences instead:
  1. **Primary is threshold-free**: Spearman rho(signal, FRACTION of non-faithful steps).
  2. **All five thresholds reported as a band**; anything that flips inside it is not a finding.

Self-correction during analysis: unsupported-step **counts** against a **fraction** target are
mechanically length-confounded (n_steps itself scored rho -0.223). Rate versions are the
like-for-like signals; counts retained only for reference.

## Result: the two-regime pattern does NOT replicate on GRACE

Primary (threshold-free Spearman vs fraction non-faithful):

| signal | pooled | correct | incorrect | correct − incorrect |
|---|---|---|---|---|
| grounding NLI, frac unsupported | **+0.226** [0.133, 0.312] | +0.216 [0.085, 0.342] | +0.122 [−0.022, 0.274] | +0.094 [−0.091, 0.289] |
| grounding NLI, mean entailment (inv) | **+0.254** [0.169, 0.335] | +0.230 [0.099, 0.349] | +0.103 [−0.040, 0.243] | +0.127 [−0.058, 0.318] |
| prior-step NLI, frac unsupported | +0.093 [−0.002, 0.187] | +0.076 | +0.111 | −0.035 [−0.237, 0.162] |
| words | −0.030 | −0.080 | +0.040 | −0.120 [−0.311, 0.061] |
| frac_cited (inv) | +0.112 [0.023, 0.202] | +0.119 | +0.083 | +0.036 [−0.148, 0.224] |

**Every regime difference CI crosses zero.** No signal shows the FaithCoT pattern (works on correct
answers, blind on incorrect). Grounding NLI works *weakly in both regimes*, slightly stronger on
correct answers, but the difference is not detected.

Threshold stability: mean-entailment is stable in both regimes (0.597–0.632 correct, 0.545–0.578
incorrect); frac-unsupported is stable on correct answers (0.577–0.600) but crosses 0.5 on
incorrect (0.485–0.594). Under dataset x track conditioning everything falls to 0.42–0.56.

## What this adds

1. **The two-regime contrast is now FaithCoT-specific across two external standards.** BonaFide
   could not test it (no correct regime); GRACE can test it and does not reproduce it.
2. **The entanglement survives externally** — lift 1.15–1.65x under every aggregation rule, against
   FaithCoT's 1.74x. This is the first genuine external support for that claim (the earlier
   BonaFide "replication" was a base-rate error, retracted 2026-09-13).
3. **A grounding signal does detect GRACE's labels** (+0.23/+0.25 pooled, CIs excluding 0), which
   also refutes any blanket "nothing detects faithfulness" reading — but it decays to ~0.52–0.56
   under composition conditioning.
4. Only the judge is still missing here; it is queued behind the BonaFide reconciliation.
