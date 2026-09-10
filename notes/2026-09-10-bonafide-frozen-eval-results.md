# Frozen BonaFide evaluation — results (2026-09-10)

Spec: frozen-eval-spec.md v1 + v1.1 + correction v1.2 (commits dd571e5 / cd8dc0e / 78a6d31).
Scripts committed before execution (d05a3d5, corrected 78a6d31). Stats stage run ONCE, after all
inputs completed. Per-example predictions: results/bonafide_predictions.json.

## Frozen endpoint outcomes (reported first, as pre-registered)

Population (corrected rules): incorrect regime n=1,113 (945 unfaithful / 168 faithful);
correct regime n=7 (counts only, as pre-registered).

| Signal | AUROC (incorrect regime) | 95% CI |
|---|---|---|
| judge A (gpt-4o-mini, primary) | **0.419** | [0.372, 0.464] |
| judge B (independent prompt) | 0.482 | [0.437, 0.530] |
| judge gpt-4o | **0.270** | [0.231, 0.310] |
| NLI unsupported steps | **0.826** | [0.795, 0.855] |
| step count | **0.878** | [0.852, 0.902] |
| soft (deletion, higher=unf) | **0.284** | [0.171, 0.401] (n=363 subset) |
| prefix instability (higher=unf) | **0.172** | [0.101, 0.265] (n=363) |

- **H1 (judge above chance): FAILED — below chance.** The primary judge is significantly
  ANTI-correlated with BonaFide's unfaithful labels; gpt-4o much more so (0.270).
- **H2 (metric nulls, margin 0.60): FAILED — no signal is null.** Two length-family signals
  discriminate strongly ABOVE chance (0.83/0.88); the two deletion-family signals sit far BELOW
  chance (i.e., their pre-registered inverted direction is itself inverted here; the H2
  "bounded_below_margin: true" flags for soft/pi are technically true and substantively
  misleading — they are inverted, not null).
- **H3**: length-family metrics dominate the judge by ~0.41–0.46 AUROC; the judge beats only the
  below-chance deletion metrics.

**Pre-registered interpretation (spec §5) applies as written:** the FaithCoT blind-regime
structure — metrics blind, judge informative — does NOT generalize to this operationalization.
The paper's blind-regime claims are hereby rescoped to expert-annotated unfaithfulness
(FaithCoT), explicitly.

## Post-hoc diagnostics (labeled as such; run after unblinding)

1. **The target population is itself heavily confounded.** ALL 168 faithful-incorrect responses
   come from instruct models (zero from thinking models), while 356/945 unfaithful come from
   thinking models; faithful traces are 2.5x shorter (5.8 vs 14.4 steps). The 0.88 step-count
   AUROC is therefore substantially a label-composition artifact of BonaFide's explicit-label
   subset — the exact class of surface confound our audit prescribes reporting, present at
   near-ceiling strength in the independent benchmark.
2. **Judges are actively fooled in the predicted direction.** gpt-4o rates honest incorrect
   traces MORE unfaithful (mean score 91.2/100) than hint-following rationalizations (61.2).
   Smooth unacknowledged-hint rationalizations look MORE faithful to a judge than honest errors
   do — the phenomenon of the paper's Figure 2, demonstrated at scale on an independent dataset,
   though entangled with the length/model-type confound above.
3. Class composition: 930/945 unfaithful are `hinting`; faithful-incorrect are 165 `hinting` +
   3 `complex`.

## What this means

The planned confirmation failed, and what replaced it is a sharper measurement finding: **two
operationalizations of instance-level "unfaithfulness" — expert annotation (FaithCoT) and
intervention-defined hint-following (BonaFide) — order every tested detector in OPPOSITE
directions.** Judge: best-behavioral <-> below chance. Step count: shallow carrier <-> 0.88
top signal. Deletion metrics: inverted one way <-> inverted the other. Detector rankings do not
transfer across label operationalizations at all; results phrased as "unfaithfulness detection"
without naming the operationalization are underdetermined. This slots into the paper as a
first-class finding of the measurement audit (and retroactively justifies the spec's "treat
disagreement between operationalizations as data").

Caveats: single independent dataset; its explicit-label subset carries the composition confound
of diagnostic (1); deletion-family numbers use the free-form answer-logprob readout (C2) on the
small-generator subset only; judges share one provider (the pre-registered Anvil S1 panel now
answers whether open judges also invert here — it just became the most interesting arm).
