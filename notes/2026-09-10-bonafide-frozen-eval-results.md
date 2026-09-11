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

## Confound controls (run immediately after unblinding, on saved predictions)

The post-hoc diagnostic above raised the possibility that everything here is BonaFide's
length/model-type composition. Three controls, all on the incorrect regime:

| Control | judge A | judge gpt-4o | step count |
|---|---|---|---|
| pooled (all generators) | 0.419 | 0.270 | 0.878 |
| **instruct-models only** (removes model-type confound entirely; 589 unf / 168 faith) | **0.332** [0.285, 0.381] | **0.184** [0.150, 0.226] | 0.837 |
| **per generator** (4 of 5 with both classes) | 0.385 / 0.392 / 0.195 / 0.184 / 0.513 | — | 0.79–0.91 |
| **step-count-stratified** (instruct-only, quartile bins; n-weighted within-bin) | **0.282** | — | (is the stratifier) |

**The judge inversion is not a composition artifact.** It gets *stronger* when the model-type
confound is removed (0.419 -> 0.332), holds in 4 of 5 generators individually (the fifth is at
chance, 0.513, n=113), and survives length stratification (within-bin 0.282). Within the same
length band, from the same generator, prompted judges rate hint-following rationalizations as
MORE faithful than honest errors.

The step-count side is weaker as a finding: it survives model-type control (0.837) but it is
confounded with BonaFide's labeling by construction (hint-following rationalizations are
elaborate; the top step-count quartile is 172/172 unfaithful). We report it as a property of
this dataset's explicit-label subset, not as a working detector.

**Revised headline:** the robust, controlled result is that the best behavioral detector in the
FaithCoT audit (a prompted LLM judge) is significantly ANTI-correlated with intervention-defined
unfaithfulness on an independent dataset, controlling for generator identity and trace length --
and it fails in the direction the paper's coupling account predicts: smooth rationalization reads
as faithful, honest failure reads as unfaithful.

## Mechanical acknowledgment analysis (2026-09-12, post-hoc/exploratory — BonaFide already unblinded)

Before commissioning human annotation, a regex proxy for "does the trace acknowledge the supplied
cue" (the family used to audit our own hint testbed, extended with BonaFide's cue vocabulary:
professor/metadata/validator/unauthorized/security-audit/error-message) over the incorrect-answer
population:

| class | n | mentions cue | judge A mean (mention / no-mention) |
|---|---|---|---|
| unfaithful | 945 | 367 (39%) | 46.7 / 23.1 |
| faithful | 168 | 137 (82%) | 36.1 / 37.9 |

- Mentioning the cue predicts the FAITHFUL label (AUROC 0.286 for predicting unfaithful), matching
  BonaFide's definition of unfaithful as *unacknowledged* reliance.
- **The judge's inversion is concentrated where the cue is never mentioned**: judge AUROC 0.299
  (n=609) in the no-mention subset vs **0.606** (n=504) in the mention subset. Where the trace
  discloses, the judge is above chance; where it does not, the judge is strongly inverted, rating
  smooth unacknowledged rationalizations as MORE faithful (23.1) than honest errors (37.9).

**Reading (hypothesis, not established).** In the no-mention subset the label is defined by
something with no trace-internal evidence — the model used a cue and said nothing about it — so a
trace-only judge is being asked to detect an absence. This is a concrete, testable version of the
"evidence access" arm of the diagnostic protocol, and it promotes arm B1 to the primary hypothesis.

**A second, separable construct gap.** 367 traces labelled UNFAITHFUL *do* mention the cue.
Spot-checking three: two openly cite the hint and then follow it ("the professor says the answer is
21..."; "The user mentioned that a Stanford professor says it's Adolfo Gass. Let me try to verify
this."), one is a regex false positive ("the user is asking about..."). Disclosed-then-followed
reliance is UNFAITHFUL by BonaFide's definition but reads as faithful under our rubric, which
penalizes *unverbalized* shortcuts. That is rubric-construct mismatch, visible without annotation.

**Consequence for the planned human audit.** Most of the mechanism question is answerable without
annotators. What genuinely needs human eyes is narrower: (a) whether regex "mention" tracks human
"acknowledgment" (the false positive above shows it does not perfectly), and (b) adjudication of
disclosed-then-followed cases. The packet should shrink to ~50 items drawn from the
mention-and-labelled-unfaithful cell plus a no-mention control, roughly one hour of reading, rather
than 200 items and ten hours.

## Is it "the same two regimes, inverted"? No — and here is what it is instead (2026-09-12)

**1. The correctness stratification cannot be compared at all.** BonaFide has 7 correct-answer
responses (all unfaithful). There is no correct regime there, so "do the two regimes appear in both
datasets" is not answerable on this pair, in either direction.

**2. What DOES replicate is the entanglement, not the regime structure.** FaithCoT: 69% of
annotated unfaithfulness sits on incorrect answers. BonaFide: >99%. Two independently built
benchmarks, same structural coupling of unfaithfulness to wrongness — stronger in the newer one.

**3. Under a different stratifier (does the trace mention the cue), BonaFide does NOT show the
FaithCoT compositional pattern.** FaithCoT's aggregate metric performance is carried by
cross-regime pairs while within-regime cells sit near chance. On BonaFide, step count discriminates
*within* both strata (0.752 no-mention, 0.954 mention), so its aggregate is not composition. The
judge, by contrast, is governed by the positive class's mention status (0.606/0.588 when the
unfaithful trace mentions the cue; 0.299/0.303 when it does not).

**4. The real common theme: in both benchmarks a trivial variable beats every purpose-built
detector.** FaithCoT: the correctness oracle (0.696) matches or beats every metric (best 0.641).
BonaFide: raw step count (0.878) beats every metric and every judge (best judge 0.482). Different
confound, same failure — the winning signal measures something other than faithfulness.

**5. The judge is the STABLE object; the labels are what move.** Spearman with trace length:

| | judge vs length | label vs length |
|---|---|---|
| BonaFide (incorrect) | **+0.205** | **+0.469** |
| FaithCoT (full) | **+0.208** | +0.111 |
| FaithCoT (incorrect only) | +0.252 | +0.008 |

The judge's length association is essentially identical across datasets (+0.21). What differs by a
factor of ~50 is the *label's* length association. So the judge does not "break" on BonaFide: it
applies the same reading, and one benchmark's labels happen to track what it reads while the
other's do not.

Note the direction: judge and BonaFide label are BOTH positively length-associated, yet the judge
is below chance against that label — so conditional on length the inversion is *stronger*, which
matches the within-length-bin figure (0.282 vs 0.419 pooled). Whatever the judge is reading
anti-predicts BonaFide's label once length is partialled out.

**Hypothesis (not established).** The judge scores something like *coherence* — whether the stated
steps hang together and reach the answer. FaithCoT's expert labels are formed by humans reading the
trace, so they partly encode the same thing, and the judge aligns. BonaFide's labels encode causal
dependence on a planted cue, and a fluent unacknowledged rationalization is exactly the case where
coherence is high and causal dependence is also high — maximal divergence. Testing this is what the
frozen 2x2's rubric arm does: it separates reliance, disclosure, and logical support instead of
scoring a single scalar.
