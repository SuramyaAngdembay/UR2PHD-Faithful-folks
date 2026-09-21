# Judge scores encode WHO WROTE the trace, not just whether it is unfaithful (2026-09-19)

> **CORRECTED 2026-09-21 — read `2026-09-21-independent-code-audit.md` first.** An independent audit overturned three things in this note. (1) The "LIMITING RESULT" ranking test ran on a subset containing only two of the four generators; on the full population pooling inflates every blind-regime judge AUROC by 0.014-0.045 and the leader changes (rank correlation 0.94, not 0.99). (2) Self-preference is **not identifiable** with this design, not "absent": all three differenced effects exclude zero at the pre-registered Bonferroni level but differ in sign, and 29% of placebo cells do too. (3) The question-only arm is not a valid floor for the spread statistic; the permutation floor is 4.5-6.7, so "18x-29x" is 2.3x-5.6x, the range across nine distinct judges is 8.1-29.1 not 19.5-31.7, Olmo's spread is noise, and the partition is **not** unanimous across seed arms. The direction of the generator-vs-label comparison survives a fair variance decomposition. Original text preserved below for provenance.


**Status: EXPLORATORY.** This was not the pre-registered hypothesis. It is what the pre-registered
falsification test in `self-preference-spec.md` turned up when the hypothesis it was guarding
failed. The order of events is recorded in full below because that is what makes the finding
usable rather than a post-hoc rescue. Cached judge outputs only; no new inference.

## Order of events

1. Froze `self-preference-spec.md` to test whether judges favour their own generations, having
   verified from record identifiers that FaithCoT's four generators are Qwen2.5-7B-Instruct,
   gemini-2.5-flash, gpt-4o-mini and llama-3.1-8b-instruct, three of which are judges we have or
   are running.
2. The spec argued the naive design is wrong: AUROC is rank-based within a subset, so a constant
   self-preference offset leaves within-generator AUROC unchanged. Primary endpoint became a
   matched score offset (E1m), with **E2m as an explicit falsification test** — the same offset for
   judges the generator is *not* self for, which must be centred on zero.
3. Amended to a question- *and* label-matched design after finding 295 of 341 questions carry all
   four generators with byte-identical question text. Still no judge quantity computed.
4. Ran it. **The self-preference reading failed its own falsification test**, and E2m revealed
   something much larger.

## The self-preference result, stated plainly: it fails

gpt-4o-mini scoring its own generations, blind regime, matched on question and true label:
**-8.63 [-14.57, -2.89]**, replicating under a second prompt at **-9.89 [-16.13, -3.42]**.
Negative is the Panickssery direction (scores its own traces as more faithful) and the interval
excludes zero.

But E2m says this is not self-preference. Qwen3-8B, a different family entirely, scores the same
gpt-4o-mini traces at **-6.56 [-13.32, -0.51]**, and gpt-4o at -5.66. The self-judge's offset is
only modestly larger than a cross-family judge's. **Per the spec's own advancement rule, the
self-preference reading fails**: the effect belongs to the traces, not to self-status.

## What is actually there

On **the same question**, with **the same human faithfulness label**, judges score traces very
differently depending only on which model wrote them. Blind (incorrect-answer) regime, 86 questions:

| judge | label effect | generator spread | ratio |
|---|---|---|---|
| gpt-4o-mini | 15.2 [9.7, 20.7] | 23.9 [19.1, 29.1] | 1.58 [1.07, 2.52] |
| gpt-4o-mini prompt B | 17.8 [10.8, 24.7] | 28.7 [22.9, 34.9] | 1.62 [1.06, 2.84] |
| gpt-4o-mini CoT-only | 15.4 [10.0, 21.0] | 26.4 [20.4, 32.2] | 1.71 [1.13, 2.81] |
| gpt-4o | 19.7 [11.4, 28.1] | 25.2 [19.5, 33.2] | 1.28 [0.83, 2.44] |
| gpt-5.2 | 8.0 [0.7, 15.5] | 29.1 [24.1, 36.1] | 3.61 [1.59, 20.5] |
| gpt-5.2 prompt B | 9.0 [1.7, 16.2] | 29.9 [24.6, 36.6] | 3.31 [1.69, 12.5] |
| gpt-5.2 repeat | 5.4 [-2.4, 12.8] | 31.7 [25.4, 38.5] | uninterpretable |
| Qwen3-8B (local, 4-bit) | 16.1 [7.8, 24.6] | 19.5 [12.4, 26.8] | 1.21 [0.66, 2.59] |
| **question-only control** | **-1.1 [-3.7, 1.4]** | **1.1 [0.8, 5.3]** | — |

Both quantities are measured the same way, as deviations from the within-question mean, so the
ratio means something. Label effect = mean score on unfaithful traces minus faithful traces, within
a question. Generator spread = max minus min across generators of the mean deviation, holding
question *and* true label fixed.

**The control is load-bearing and must be quoted with the result.** Max-minus-min of four group
means cannot be negative and has a positive expectation under a pure null, so the spread statistic
is biased upward by construction. The question-only arm calibrates that bias exactly: it sees only
the question and options, which are byte-identical across generators for all 341 questions
(verified against the raw FaithCoT records), so its inputs within a matched cell are identical.
**It reads 1.1.** The real judges read 19.5 to 31.7 — roughly 18x to 29x the null floor.

## What survives, and what does not

**Survives.** The generator effect is large, robust, and present for every judge: all eight
intervals sit far above the 1.1 control floor. And the judges *agree on the ordering*:

| generator | deviation (gpt-4o-mini judge) | rank agreement across all 8 judges |
|---|---|---|
| gemini-2.5-flash | -11.7 | lowest for **8 of 8** |
| gpt-4o-mini | -4.7 | second-lowest for **8 of 8** |
| Qwen2.5-7B-Instruct | +2.2 | top two, order varies |
| llama-3.1-8b-instruct | +12.2 | top two, order varies |

Eight judges spanning three model families, two vendors, and both API and local 4-bit open-weight
inference place gemini's traces lowest and gpt-4o-mini's second-lowest, unanimously. Only the top
two swap, and they are close.

**Does not survive.** The clean claim "the generator effect is larger than the label effect for
every judge". The ratio interval excludes 1 for five of eight judges (both gpt-4o-mini prompts,
CoT-only, and both gpt-5.2 prompts), covers 1 for gpt-4o and Qwen3-8B, and is uninterpretable for
the gpt-5.2 repeat whose label effect itself covers zero. **Honest version: the generator effect is
at least comparable to the label effect for every judge, and larger for most.**

## It is not trace length

The obvious confound, and the one our own paper already establishes as a strong baseline. It fails
cleanly here, for a structural reason: **the two longest-trace generators sit at opposite extremes.**
gemini averages 361 words and scores lowest; llama-3.1-8b averages 345 words and scores highest.

Regressing the within-pair score difference on the within-pair word difference across 284 matched
pairs, length explains **7.7%** of the gemini-llama gap for gpt-4o-mini, 16.1% for gpt-4o, 15.8% for
gpt-5.2, 7.9% for Qwen3-8B. The length slope is negative (longer reads as more faithful) and
gemini is the longer of the pair, so length pushes in the same direction and still accounts for at
most a sixth of it.

## Why it matters

FaithCoT's detector rankings are computed by pooling across all four generators. If judge scores
carry a generator-identity offset of 20 to 30 points while the faithfulness signal they are meant to
carry is 5 to 20 points, then a pooled ranking is partly ranking generator style. That is the same
structure as the correctness-composition result already in the manuscript — a covariate the judge
tracks better than the target, inflating the pooled number through cross-stratum pairs — with
generator identity as a second such covariate. The AUROC decomposition licensing this reading is
Kallus & Zhou 2019 Prop. 1 (**as stated**, not as proved; see the citation note), and Matos et al.
2026 prove AUC non-collapsible in exactly this way.

The composition gap it produces is measurable and modest: pooled AUROC minus the size-weighted mean
of within-generator AUROCs runs +0.010 to +0.055 in the blind regime and +0.010 to +0.039 in the
correct regime, largest for the gpt-4o-mini prompts. So generator identity inflates pooled numbers
less than correctness does, but in the same direction and by a non-trivial amount.

## What this does NOT establish

- **Not a hallucination or validity verdict on any single judgement.** A systematic offset across
  a generator's traces is consistent with those traces genuinely differing in ways the human
  annotation does not capture. We cannot tell, from scores alone, whether the judges are wrong
  about gemini or the labels are.
- **Not causal.** Generator identity is confounded with everything about how each model writes.
  Length is ruled out; hedging, structure, formatting, self-corrections and refusal style are not.
- **Not pre-registered.** Five of the eight ratio intervals exclude 1, but these are eight judges
  on one benchmark in one regime, chosen after seeing that E2m failed.

## Next, if this is pursued

Write a fresh spec first. The obvious tests: whether the ordering survives on GRACE and BonaFide
(different generators, different annotation protocol); whether a judge told the generator's name
shifts further; whether surface features beyond length (hedging markers, step count, markdown
structure) absorb the effect. The local arms now in flight add five more judges including two that
ARE self-judges (Qwen2.5-7B, Llama-3.1-8B), which will also re-test the failed self-preference
reading with proper power.

Artefacts: `results/self_preference/results.json`, `results/self_preference/generator_identity.json`,
`scripts/self_preference_analysis.py`, `scripts/generator_identity_effect.py`.

---

## Update (2026-09-19, later): the Qwen2.5-7B self-judge arm lands

`qwen25_7b` completed clean (1304 rows, 0 unparsed). Qwen2.5-7B-Instruct **is** one of FaithCoT's
four generator models, so this is the second of the three pre-registered primary tests.

**Primary test 2 of 3: NULL.** Matched own-vs-other offset, blind regime:
**-1.06 [-7.20, 5.44]**, 95 pairs over 95 questions. The interval covers zero comfortably, so it is
null at any stricter Bonferroni level too. For context on the same generator's traces, the
cross-family Qwen3-8B judge gives **+2.37** and gpt-4o-mini gives **+4.36**, both also covering
zero, while the question-only control floor is **+0.82**. The self-judge is the most negative of
the Qwen-generator column but is not distinguishable from its neighbours.

Scoreboard on the pre-registered hypothesis, two tests down:

| self-judge | matched offset, blind | verdict |
|---|---|---|
| gpt-4o-mini | -8.63 [-14.57, -2.89] | excludes zero, but **fails E2m**: non-self judges show -5.66 and -6.56 on the same traces |
| Qwen2.5-7B-Instruct | -1.06 [-7.20, 5.44] | **null** |
| Llama-3.1-8B-Instruct | running | pending |

**The self-preference reading is now clearly dead**, not merely unsupported by one cell. One cell
was significant and failed its own falsification test; the second is flat.

**The generator-identity effect replicates on the new judge**, which matters because this judge was
never involved in discovering it:

| | value |
|---|---|
| generator spread | 22.0 [15.54, 28.26] |
| label effect | 8.3 [1.96, 14.38] |
| ratio | 2.66 [1.31, 10.56] |

The ratio interval excludes 1, bringing that to **six of nine** real judges. The generator ordering
is unchanged: gemini -17.58, gpt-4o-mini -3.17, Qwen2.5-7B -1.06, llama-3.1-8b +18.96. Gemini
lowest and llama highest, as for every other judge.

**Unrelated observation worth keeping.** Qwen2.5-7B's **correct-regime** pooled AUROC is **0.639**,
against 0.786 to 0.830 for the GPT judges and 0.666 for Qwen3-8B. That extends the earlier reading
that judge capability buys correct-regime performance and buys nothing in the blind regime: its
blind AUROC is 0.637, identical to Qwen3-8B's 0.637 despite being a different model of a different
generation. Its correct-regime composition gap is -0.002, the only near-zero gap among real judges,
so its pooled correct-regime number is almost entirely within-generator discrimination.

---

## Does the paper's headline regime gap survive stratification by generator?

**Yes, and pooling was understating it.** This is the check the stratified-evaluation literature
demands of anyone who makes our argument, applied to our own central claim. EXPLORATORY: 4
generators x 3 judges = 12 gap estimates, no correction applied.

The manuscript's headline is the regime gap for `judgeA` (gpt-4o-mini): correct-regime AUROC 0.830
minus blind-regime 0.679 = **+0.152**. A fresh implementation here reproduces it at
**+0.152 [0.089, 0.215]** against the paper's [0.089, 0.211] — independent verification of the
central number, the small upper-bound difference being bootstrap draws.

Stratified by who wrote the trace, judge gpt-4o-mini:

| generator | blind | correct | gap | 95% CI |
|---|---|---|---|---|
| Qwen2.5-7B-Instruct | 0.641 | 0.863 | **+0.223** | [0.114, 0.328] |
| gpt-4o-mini | 0.657 | 0.883 | **+0.226** | [0.095, 0.344] |
| llama-3.1-8b-instruct | 0.599 | 0.818 | **+0.219** | [0.075, 0.356] |
| gemini-2.5-flash | 0.642 | 0.676 | +0.034 | [-0.115, 0.188] |
| pooled | 0.679 | 0.830 | +0.152 | [0.089, 0.215] |

**Three of four generators show a gap around +0.22, half again larger than the pooled +0.152.**
Pooling across generators *attenuates* the regime gap rather than manufacturing it. So the
composition concern that applies to the judge's raw scores does **not** undermine the headline; if
anything the published number is conservative. That is a meaningful robustness result and worth
stating in the paper, since a referee who accepts our own composition argument will immediately ask
whether it eats our main claim. It does not.

### Two genuine heterogeneities it exposes

**1. Gemini-generated traces show no regime structure, consistently.** The gap is +0.034 for
gpt-4o-mini, -0.064 for gpt-5.2, +0.017 for Qwen2.5-7B. Three independent judges, all near zero.
**Do not overread it:** that cell has only 18 correct-regime positives and every interval is wide
enough to cover the other generators' +0.22. It is suggestive, underpowered, and exactly the kind
of cell the spec's power ruling already barred from carrying a claim. Worth a targeted test, not a
sentence in the abstract.

**2. The regime gap requires a capable judge.** Qwen2.5-7B-Instruct as judge shows **no gap at
all**: pooled +0.002 [-0.068, 0.074], and within every generator the gap is between -0.001 and
+0.066, every interval covering zero.

| judge | pooled blind | pooled correct | gap |
|---|---|---|---|
| gpt-4o-mini | 0.679 | 0.830 | +0.152 |
| gpt-5.2 | 0.653 | 0.830 | +0.177 |
| Qwen2.5-7B-Instruct | 0.637 | 0.639 | +0.002 |

This sharpens the capability reading rather than contradicting it. All three judges sit at
0.64-0.68 in the blind regime, so blind-regime performance is flat in capability as the paper
already argues. What capability buys is the **correct** regime, 0.830 for both GPT judges against
0.639 for Qwen2.5-7B. A judge too weak to exploit the correct regime shows no two-regime structure,
because it is near chance in both. **The two regimes are a property of judges that can detect at
all, not of the data alone** — which is a claim the paper does not currently make and should,
because it is the natural objection to "the blind regime is hard": maybe the correct regime is
easy only for strong judges. On this evidence, yes.

Caveat on direction of inference: three judges is not a capability sweep, and Qwen2.5-7B differs
from the GPT judges in more than capability. The remaining local arms (Llama-3.1-8B, Meta-Llama-3,
Llama-3.2-3B, Qwen3-8B, Qwen2.5-3B, OLMo-3-7B) give a much better-populated capability axis, and
this table should be recomputed across all of them before anything is claimed.

---

## FINAL: all three pre-registered self-preference tests are complete. The hypothesis is dead.

`llama31_8b` landed clean (1304 rows, 0 unparsed). Llama-3.1-8B-Instruct is a FaithCoT generator,
so this is the third and last primary test, and it kills the hypothesis in the most informative way
available: **it is significant in the OPPOSITE direction.**

| self-judge | own-generation offset, blind | direction |
|---|---|---|
| gpt-4o-mini | -8.63 [-14.57, -2.89] | toward self-preference |
| Qwen2.5-7B-Instruct | -1.06 [-7.20, 5.44] | null |
| Llama-3.1-8B-Instruct | **+25.22 [18.90, 31.41]** | **away from self-preference** |

Differenced against the judges for whom that generator is not self (E2, the spec's control):

| self-judge | self | non-self mean | non-self range | DiD |
|---|---|---|---|---|
| gpt-4o-mini | -8.63 | -3.74 | [-10.8, +1.3] | -4.89 |
| Qwen2.5-7B | -1.06 | +8.20 | [+1.7, +16.7] | -9.26 |
| Llama-3.1-8B | +25.22 | +17.49 | [+10.5, +25.1] | **+7.72** |

**Two DiDs point one way, one points the other.** With three pre-registered tests at Bonferroni
0.0167 and signs that disagree, there is no effect to report. Against a control floor of ±1.03,
each self-judge's raw offset sits inside or barely outside the spread of the seven non-self judges
looking at the same traces.

**Why this is a clean kill rather than an underpowered null.** Self-status is held fixed across
the three rows, and the offset still ranges from -8.6 to +25.2, a span of 34 points. What moves it
is entirely *which generator happens to be self*. A judge looking at Llama-3.1-8B's traces scores
them harshly whether or not it wrote them; a judge looking at Gemini's scores them leniently in
every arm. **Generator identity explains the offsets; self-status adds nothing detectable on top.**

The verdict on the pre-registered question is therefore not "we could not detect self-preference".
It is "the variance that would have been attributed to self-preference is fully accounted for by a
covariate we can measure, and which is far larger".

### Consequence for the paper

Reviewers will raise Panickssery et al., because our primary judge wrote 26.1% of the traces it
grades. The answer is now three pre-registered tests deep and is stronger than a disclaimer: we
tested it, it is absent, and the confound that *is* present is one the same analysis measures. That
turns an anticipated objection into a contribution.

Standing caveats, unchanged: this is one benchmark, four generators, and an association rather than
a cause. Length is ruled out; hedging, structure, formatting and refusal style are not.

---

## Update (2026-09-20): nine distinct judge models. Unanimity claim CORRECTED and narrowed.

All 26 overnight arms complete. The generator-identity effect now has nine distinct judge models
across three vendors, API and 4-bit local, plus seed replicates.

### Correction to an earlier claim in this note

Earlier, on eight arms that were mostly OpenAI prompt variants, I wrote that all judges "rank
gemini lowest and gpt-4o-mini second-lowest, unanimously". **With nine distinct judge models that
is no longer exactly true and is corrected here.**

Per-generator deviation from the matched question-and-label mean, blind regime:

| judge | gemini-2.5-flash | gpt-4o-mini | Qwen2.5-7B | llama-3.1-8b |
|---|---|---|---|---|
| gpt-4o-mini | -11.7 | -4.7 | +2.2 | +12.2 |
| gpt-4o | -16.3 | -2.9 | +6.8 | +8.9 |
| gpt-5.2 | -20.3 | -1.5 | +8.8 | +8.3 |
| Qwen2.5-7B-Instruct | -10.5 | -1.7 | -1.1 | +11.6 |
| Qwen3-8B | -9.1 | -3.6 | +0.8 | +10.4 |
| Llama-3.1-8B-Instruct | -12.8 | -5.6 | +1.7 | +14.7 |
| Meta-Llama-3-8B-Instruct | -7.6 | +0.2 | +0.7 | +5.2 |
| Llama-3.2-3B-Instruct | -6.6 | -1.4 | +4.7 | +1.8 |
| Olmo-3-7B-Instruct | -2.0 | -4.4 | +2.6 | +3.7 |
| **question-only control** | **-0.4** | **-0.5** | **+0.3** | **+0.5** |

- **Gemini lowest: 8 of 9**, not 9 of 9. The dissenter is Olmo-3-7B, the only judge near chance in
  both regimes, which puts gpt-4o-mini marginally lower (-4.4 against -2.0).
- **llama-3.1-8b highest: 7 of 9.** gpt-5.2 puts Qwen2.5-7B marginally higher (+8.8 against +8.3)
  and Llama-3.2-3B does so more clearly (+4.7 against +1.8).

### What IS unanimous, and it is the claim to make

**The two-group partition holds for all nine judges without exception.** Gemini-2.5-flash and
gpt-4o-mini traces are always scored more faithful than Qwen2.5-7B and llama-3.1-8b traces, on the
same questions with the same human label. No judge crosses a trace between the groups.

That is weaker than a total order and stronger than "most judges agree". It is also the version
that survives the noise: the within-pair differences that break the fine-grained ordering are 0.5
to 3 points, at or below the run-to-run noise, while the between-group gaps are 6 to 29 points.

### The effect scales with judge capability

Generator spread, blind regime, tracks judge strength the same way correct-regime AUROC does:

| judge | generator spread | label effect |
|---|---|---|
| gpt-5.2 | 29.1 | 8.0 |
| Llama-3.1-8B | 27.5 | 12.3 |
| gpt-4o | 25.2 | 19.7 |
| Qwen2.5-7B | 22.0 | 8.3 |
| Qwen3-8B | 19.5 | 16.1 |
| Meta-Llama-3-8B | 12.8 | 4.8 |
| Llama-3.2-3B | 11.3 | 7.6 |
| Olmo-3-7B | ~8 | low |

A weaker judge shows less of everything, which is what a near-chance scorer must do. **So the
generator effect is not a failure mode of weak judges. It is largest in the strongest judge
tested.** gpt-5.2 has the biggest generator spread of any arm and one of the smallest label
effects, giving it the worst ratio in the set.

**Every real judge has a generator spread exceeding its label effect**, ratios 1.06 to 5.90, and
the seed replicates reproduce each model's value within its own noise. The question-only control
stays at 1.1.

### Determinism cross-check

`qwen3_8b` and `qwen3_8b_greedy2` return byte-identical values on every quantity here: spread 19.5,
label 16.1, ratio 1.21. That is a second confirmation of exact greedy reproducibility, arriving
through a completely different analysis path.

### Method fix applied

`generator_identity_effect.py` filtered arms by an absolute count of 1300 scored rows, which
silently dropped Olmo-3-7B for having five unparsed items out of 1304. Replaced with a 0.95 parse
**rate** and an explicit skip message. The real exclusion criterion is heavy, non-random
missingness, which is the Qwen2.5-3B base-model case, not five stray rows.

---

## LIMITING RESULT (2026-09-20): the generator effect does NOT change detector rankings

The actionable worry raised in the "Why it matters" section above was this: if judge scores carry a
20-to-30-point generator-identity offset while the faithfulness signal is 5 to 20 points, then a
pooled leaderboard is partly ranking generator style. **That inference was tested and it does not
hold on our data. The section above overstates the consequence and is corrected here.**

Eighteen detectors (nine judges, nine metric signals) on the 633 complete-feature rows scored by
every judge. Pooled AUROC against the size-weighted mean of within-generator AUROCs, and the two
induced rankings compared:

| regime | Spearman(pooled rank, within rank) | pairwise inversions |
|---|---|---|
| blind (ft1v2), n=270 | **0.9897** | 4 of 153 (2.6%) |
| correct (ft3v4), n=363 | **0.9835** | 4 of 153 (2.6%) |

Composition gaps per detector are small and, more importantly, **similar across detectors**: mostly
±0.001 to 0.016 in the blind regime and within ±0.014 in the correct regime, against generator
score offsets of 20 to 30 points. No detector in the blind regime moves more than 2 rank positions.

### Why the large score effect is nearly inert on rankings

AUROC is rank-based within the evaluated set, and a generator offset shifts **all** of that
generator's traces together, faithful and unfaithful alike. It therefore degrades cross-generator
pairs symmetrically rather than favouring any particular detector. The effect is large in score
space and close to neutral in ranking space, and those are different spaces.

This is the same structural point the spec made at the outset about AUROC being invariant to a
constant offset. It applied to the self-preference endpoint then; it applies to the leaderboard
consequence now. **We should have predicted this and did not** — the "Why it matters" paragraph was
written before the test.

### The one exception worth recording

**Judge Qwen2.5-7B moves 3 rank positions in the correct regime**, pooled 0.608 against
within-generator 0.650, a gap of -0.041 and the largest single shift in either table. Pooling
*understates* that judge. It is one detector of eighteen, and it is the self-judge cell, which is
worth keeping in mind though the self-preference study found nothing.

### What the generator finding is now, stated at its correct scope

**Survives:** judge scores carry a large, systematic, cross-vendor generator-identity offset.
Holding question and human label fixed, traces are scored 19.5 to 31.7 points apart by author
model, against a 1.1-point control floor. The two-group partition is unanimous across nine judges.
The effect is largest in the strongest judge tested. This is a real property of LLM-judge scores
and a caution for anyone who interprets an individual judge score as a faithfulness measurement.

**Does not survive:** any claim that this destabilises benchmark detector rankings, or that
published leaderboards are ranking generator style. On our data the ranking is near-perfectly
preserved under generator stratification.

**Consequence for the paper.** This is a scoping result, not a headline, and it should be written
as one. It belongs beside the run-to-run noise finding as a measurement caution about judge scores,
not in the composition argument, where the correctness covariate does the work and generator
identity demonstrably does not. Reporting it honestly also pre-empts a reviewer who notices the
generator effect and assumes we ignored its consequences: we measured them, and they are small.
