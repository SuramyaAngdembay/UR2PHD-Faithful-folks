# The blind regime is hard invariantly across judge capability (2026-09-20)

> **CORRECTED 2026-09-21 — see `2026-09-21-independent-code-audit.md` and `2026-09-21-validity-stress-tests.md`.** "3.5x among the seven at 7B and above" excluded Olmo-3-7B, which is a 7B model — selection on the outcome; with it the ratio is 2.2x. The ten-judge table in the first update used a partial 594-row arm for Qwen2.5-3B-Instruct. The "greedy below all seeds" oddity is wrong for Qwen2.5-3B-Instruct and overstated for Llama-3.2-3B; the genuine outlier is Llama-3.1-8B blind. The 0.023 API noise figure is blind-regime only (correct regime 0.013). The ceiling is a pooled, single-judge, generic-prompt number: within generator it is ~0.64, in AQuA the blind regime reaches 0.75-0.88, a seven-judge ensemble reaches 0.700, and published work (BonaFide) shows a definition-informed judge far exceeding a generic one.


**EXPLORATORY.** Not pre-registered. Capability is proxied by model size, family and generation,
not measured. These judges differ in more than capability: instruct-tuning, 4-bit quantization,
vendor and training data all vary. The table supports a qualitative reading, not a scaling law.
Artefacts: `scripts/judge_capability_axis.py`, `results/judge_capability_axis.json`.

## Result

Eight distinct judge models, identical prompt A, identical 1,304 FaithCoT traces. Three frontier
API models and five local open-weight models run in 4-bit across 2x RTX 3070.

| judge model | blind (ft1v2) | correct (ft3v4) | gap |
|---|---|---|---|
| gpt-4o-mini | 0.679 [0.631, 0.725] | 0.830 [0.782, 0.870] | +0.152 |
| gpt-5.2 | 0.653 [0.600, 0.708] | 0.830 [0.783, 0.874] | +0.177 |
| gpt-4o | 0.669 [0.624, 0.715] | 0.786 [0.734, 0.836] | +0.116 |
| Meta-Llama-3-8B-Instruct | 0.624 [0.583, 0.669] | 0.695 [0.646, 0.745] | +0.071 |
| Llama-3.1-8B-Instruct | 0.642 [0.597, 0.692] | 0.688 [0.633, 0.741] | +0.046 |
| Qwen3-8B | 0.637 [0.590, 0.683] | 0.666 [0.605, 0.724] | +0.029 |
| Qwen2.5-7B-Instruct | 0.636 [0.587, 0.684] | 0.639 [0.586, 0.694] | +0.002 |
| Olmo-3-7B-Instruct | 0.547 [0.491, 0.603] | 0.543 [0.486, 0.601] | -0.005 |

**Seven of eight judges sit between 0.624 and 0.679 in the blind regime.** That band spans
GPT-5.2 and a 4-bit Meta-Llama-3-8B. The same seven span 0.639 to 0.830 in the correct regime.

| | spread across 7 judges | vs noise floor |
|---|---|---|
| blind regime | 0.054 | 2.4x |
| correct regime | 0.192 | 8.3x |

The noise floor is 0.023, measured earlier from two identical gpt-5.2 configurations. **The entire
blind-regime spread across seven judges is about twice the spread produced by running one judge
twice.** The correct-regime spread is four times larger than that.

## Why this matters more than the three-judge version

The manuscript argues the blind regime is hard. The natural objection is that we used weak or
poorly-prompted judges, and that a better judge would crack it. This answers that objection with
the strongest evidence the design allows: **blind-regime performance does not move with judge
capability, across eight models spanning a frontier reasoning model to 4-bit 8B open-weight
models, while correct-regime performance on the identical traces moves a great deal.**

The claim strengthens from "hard for our judges" to "invariant in judge capability over the range
we can test". Those are different claims and only the second is interesting.

It also sharpens what capability buys. It does not buy faithfulness detection. It buys performance
in the regime where the paper already shows the judge is largely tracking answer correctness. That
is consistent with the composition thesis rather than an independent finding: a more capable judge
infers correctness better, and correct-regime AUROC is the place that pays.

## Olmo-3-7B is the informative floor case

It is the only judge below the band, and it is near chance in **both** regimes: 0.547 and 0.543,
both intervals covering 0.5. It has no regime structure because it cannot detect in either regime.

That is the shape the capability reading predicts. Below some threshold a judge shows no two-regime
structure at all; above it, the correct regime opens up and the blind regime does not. Qwen2.5-7B
sits just above the floor with a +0.002 gap, Llama-3.1-8B at +0.046, the GPT family at +0.116 to
+0.177. **The regime gap is monotone-ish in capability while the blind regime is flat.**

Stated carefully, because "monotone" is exactly the kind of claim this project has had to withdraw
before: the gap ordering is Olmo -0.005, Qwen2.5-7B +0.002, Qwen3-8B +0.029, Llama-3.1 +0.046,
Llama-3 +0.071, gpt-4o +0.116, gpt-4o-mini +0.152, gpt-5.2 +0.177. Several of those differences are
inside the noise floor and the intervals overlap heavily. **The local/API separation is the durable
part; the within-group ordering is not.**

## What would falsify it

A judge substantially above 0.70 in the blind regime. Nothing in this set is close, and the ceiling
candidates here are the ones with the most capability. The queued seed arms will also put
within-model error bars on each row, which is what the current table most lacks.

## Caveats

- Local models run 4-bit. Quantization could depress them uniformly, which would not explain the
  regime asymmetry but would affect absolute levels.
- Prompt A was written and tuned against GPT judges. Local models were given it verbatim for
  comparability, which is the right choice for this contrast and may understate them.
- `Qwen/Qwen2.5-3B` is **excluded**: a base model rather than instruct-tuned, with 265/1304 (20.3%)
  unparsed and strongly non-random missingness (43.2% on LogiQA against 1.4% on AQuA, and
  differential by generator). Since generator identity is the covariate under study elsewhere in
  this campaign, that composition shift is disqualifying. A Qwen2.5-3B-**Instruct** arm has been
  queued in its place.
- Olmo-3-7B has 5 unparsed of 1304, which is negligible.
- Eight judges, one benchmark, one prompt.

---

## Update: all 26 arms complete. Two additions, one of which REFINES the claim above.

### 1. Local greedy judges are exactly reproducible. API judges at temperature 0 are not.

Qwen3-8B was run twice under identical greedy decoding, same prompt, same 1,304 traces.

| | result |
|---|---|
| identical item scores | **1304 / 1304 = 100.00%** |
| mean absolute difference | 0.000 |
| blind AUROC, run 1 vs run 2 | 0.6366 vs 0.6366 |
| correct AUROC, run 1 vs run 2 | 0.6660 vs 0.6660 |

Set against the API measurements from the same campaign:

| judge | identical scores on a repeat | mean abs difference |
|---|---|---|
| Qwen3-8B, local greedy | **100.0%** | 0.000 |
| gpt-4o-mini, temperature 0 | 83.9% | 6.19 |
| gpt-5.2, identical configuration | 25.9% | 4.3 |

**This is a methodological result worth reporting on its own.** A single-run API judge AUROC carries
roughly ±0.023 of run-to-run noise that cannot be removed by setting temperature to zero, because
the provider does not guarantee determinism. A local open-weight judge under greedy decoding has
exactly zero. Any reported difference between two API judge configurations smaller than about 0.05
is not interpretable from single runs, and the field routinely reports such differences.

Sampled local decoding at temperature 0.7, three seeds per model, gives a median AUROC spread of
**0.014** across twelve model-by-regime cells, maximum 0.053. **Sampling locally at 0.7 is less
noisy in AUROC terms than the API is at temperature 0.**

### 2. The capability picture with all ten judges

Adding Llama-3.2-3B-Instruct and Qwen2.5-3B-Instruct changes the reading, so the section above is
narrowed rather than confirmed.

| judge | blind | correct | gap |
|---|---|---|---|
| gpt-4o-mini | 0.679 | 0.830 | +0.152 |
| gpt-4o | 0.669 | 0.786 | +0.116 |
| gpt-5.2 | 0.653 | 0.830 | +0.177 |
| Llama-3.1-8B-Instruct | 0.642 | 0.688 | +0.046 |
| Qwen3-8B | 0.637 | 0.666 | +0.029 |
| Qwen2.5-7B-Instruct | 0.636 | 0.639 | +0.002 |
| Meta-Llama-3-8B-Instruct | 0.624 | 0.695 | +0.071 |
| Llama-3.2-3B-Instruct | 0.561 | 0.648 | +0.087 |
| Qwen2.5-3B-Instruct | 0.553 | 0.535 | -0.018 |
| Olmo-3-7B-Instruct | 0.547 | 0.543 | -0.005 |

**WITHDRAWN as stated: "blind-regime performance does not move with judge capability."** With only
the eight larger judges the blind spread was 0.054 and that reading looked safe. The three small or
weak judges sit at 0.547 to 0.561, so across all ten the blind spread is 0.132. Blind-regime
performance *does* move with capability. The earlier sentence overreached on a truncated sample and
is retracted rather than rephrased.

**What survives, and it is still the useful claim:**

| | range across 10 judges |
|---|---|
| blind regime | 0.132 |
| correct regime | 0.295 |

Capability buys **2.2x more** in the correct regime than in the blind regime. Restricted to the
seven judges at 7B and above the asymmetry is sharper, 0.055 against 0.191, a ratio of 3.5.

**And the simplest form is the strongest, because it needs no capability proxy at all: no judge of
the ten exceeds 0.679 in the blind regime.** That set includes a frontier reasoning model. The same
ten reach 0.830 in the correct regime. The blind-regime ceiling is low and is not lifted by
anything we can put against it.

That is what the manuscript should claim. It is a ceiling result, which is falsifiable by a single
counterexample, rather than a flatness result, which the 3B judges already falsified.

### Revised reading of the floor cases

Three judges sit near chance in the blind regime. Two of them, Qwen2.5-3B-Instruct (-0.018) and
Olmo-3-7B (-0.005), are near chance in **both** regimes and show no regime structure, consistent
with being below the threshold to detect anything. **Llama-3.2-3B is not that case**: blind 0.561
but correct 0.648, a gap of +0.087 larger than Llama-3.1-8B's. So low blind performance does not
imply an inability to exploit the correct regime, and the floor is specific to the blind regime
rather than general incompetence.

One oddity worth flagging rather than explaining: Llama-3.2-3B's greedy blind AUROC of 0.561 sits
*below* all three of its sampled seeds (0.578, 0.602, 0.603), a gap of about 0.042 that exceeds its
own seed spread of 0.025. Greedy decoding appears to land in a worse mode than sampling for this
model. Not investigated.

### Housekeeping

`Qwen/Qwen2.5-3B` base-model arms are excluded and confirmed as the right call: the base model had
265/1304 unparsed and its three seed arms 337-339 each, while **Qwen2.5-3B-Instruct parses
1304/1304**. The diagnosis that the missing `-Instruct` suffix caused the parse failures is
verified, not inferred.

---

## FINAL (2026-09-20): campaign complete, 41 arms, 10 judge models

Qwen2.5-3B-Instruct replacement arms landed clean (1304 rows, 0-1 unparsed against the base
model's 265-339). Final table is the one above with Qwen2.5-3B-Instruct at blind 0.568
[0.522, 0.611] and correct 0.524 [0.483, 0.565].

| | across 10 judge models |
|---|---|
| blind regime | 0.547 to **0.679**, spread 0.132 |
| correct regime | 0.524 to **0.830**, spread 0.307 |
| ratio | **2.3x** |

**The ceiling claim in final form: the best blind-regime AUROC achieved by any of ten judge models
is 0.679.** The same set reaches 0.830 in the correct regime.

### An awkward detail worth reporting rather than burying

**gpt-4o-mini attains the ceiling in BOTH regimes** — 0.679 blind and 0.830 correct. It is the
cheapest and among the oldest models in the set, and it is not beaten in either regime by gpt-4o
(0.669 / 0.786) or by gpt-5.2 (0.653 / 0.830).

Do not overread it. The three GPT judges span 0.026 in the blind regime against a measured
run-to-run noise floor of 0.023, so they are not separable there, and 0.830 versus 0.830 is a tie.
This project has already withdrawn one "monotone across model generations" claim for exactly this
reason. **The correct statement is that the three API judges are indistinguishable from each other
in both regimes, and the API-versus-local separation is the only judge difference in this campaign
that clears the noise.**

It does, however, kill any suggestion that the blind-regime ceiling is an artefact of using a cheap
judge. The cheap judge is the best one here.

### Final within-model noise floors

Fourteen model-by-regime cells, three seeds each at temperature 0.7:

| | value |
|---|---|
| median seed spread | 0.014 |
| max seed spread | 0.053 (Olmo-3-7B correct regime, a near-chance cell) |
| greedy repeat, Qwen3-8B | **0.000** |
| API identical-config repeat, gpt-5.2 | 0.023 |

Two cells show a greedy-versus-sampled gap larger than their own seed spread: Llama-3.2-3B blind
(greedy 0.561 against seeds 0.578-0.603) and Qwen2.5-3B-Instruct blind (greedy 0.568 against seeds
0.521-0.569, spread 0.048). Both are small models in the blind regime. Greedy decoding appears less
stable than sampling for small models on this task. Flagged, not explained.
