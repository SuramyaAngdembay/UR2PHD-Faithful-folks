# Judge scores encode WHO WROTE the trace, not just whether it is unfaithful (2026-09-19)

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
