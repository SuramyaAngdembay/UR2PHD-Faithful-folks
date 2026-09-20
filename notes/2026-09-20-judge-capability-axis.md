# The blind regime is hard invariantly across judge capability (2026-09-20)

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
