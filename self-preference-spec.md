# Judge self-preference and generator-identity composition — spec frozen before analysis

**Status.** Frozen 2026-09-19, before any per-generator quantity has been computed. Analysis runs
on cached judge outputs plus the local open-weight arms now in flight. No new API inference.

## 0. Disclosure of what was already known when this was written

Honesty about ordering, per `notes/2026-09-19-holdout-and-phacking-audit.md`:

- **Known.** Per-*regime* pooled AUROCs for the existing arms (gpt-4o-mini 0.679, gpt-4o 0.670,
  prompt-B 0.667, gpt-5.2 0.653/0.630/0.660, Qwen3-8B blind 0.637 / correct 0.666), the judge
  run-to-run noise floor (±0.023 blind), and the correctness-composition result.
- **Known (design facts, computed to size this study, not outcomes).** The four FaithCoT generator
  models and the per-generator cell sizes and class balances in §2.
- **NOT known, and genuinely unexamined at freeze time.** Every per-generator judge quantity:
  no per-generator AUROC, no per-generator mean score, no own-vs-other contrast of any kind has
  been computed for any judge.

This spec is therefore a genuine pre-registration *for the per-generator analysis only*. It is not
a pre-registration of the regime analysis, which is already reported.

## 1. The question, and why the obvious design is wrong

Panickssery et al. report that LLM judges favour their own generations. The naive test — compare a
judge's AUROC on its own generations against its AUROC on others' — **does not measure that**.

AUROC is rank-based *within* the evaluated subset. A pure self-preference bias is a constant
downward shift in unfaithfulness score on own-generations. **A constant shift leaves within-subset
AUROC exactly unchanged.** So within-generator AUROC answers a discrimination question, not a
preference question, and a null there is not evidence against self-preference.

Where a self-preference offset *does* surface is in the **pooled** AUROC, because it moves
own-traces relative to other-traces across the pooled ranking. That is the same structure as the
correctness-composition finding already in the manuscript: generator identity is a covariate, and
pooling over it mixes within-stratum and cross-stratum comparisons (Kallus & Zhou 2019, Prop. 1,
cited not claimed). **Self-preference, if present, is a composition effect in the decomposition we
already use.** This spec tests it as one.

## 2. Population and cells

FaithCoT, n=1304, four generators x two regimes. Regimes keyed on `ft` only, NEVER on the misnamed
`correct` field (see `step1-competitive-gap-spec.md`). Blind regime = ft1v2 (incorrect answers),
correct regime = ft3v4.

| generator | n | blind n | blind unfaithful | correct n | correct unfaithful |
|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | 327 | 126 | 63 | 200 | 48 |
| gemini-2.5-flash | 330 | 103 | 33 | 227 | 18 |
| gpt-4o-mini | 340 | 141 | 53 | 199 | 15 |
| llama-3.1-8b-instruct | 307 | 144 | 84 | 163 | 26 |

**Power ruling, fixed now.** Blind-regime cells (33-84 positives) are the primary analysis.
**Correct-regime cells for gemini-2.5-flash (18 positives) and gpt-4o-mini (15 positives) are
declared underpowered in advance**; they are reported with intervals but no correct-regime cell is
eligible to carry a headline claim. This ruling is made before seeing any outcome.

## 3. Judge arms and their self-status

Self-status is a property of the data, verified from record identifiers, not assumed.

| judge | self-generator cell | status |
|---|---|---|
| gpt-4o-mini | gpt-4o-mini | SELF (cached) |
| gpt-4o | none | same family, cached |
| gpt-5.2 (3 arms) | none | same family, later gen, cached |
| Qwen2.5-7B-Instruct | Qwen2.5-7B-Instruct | SELF (in flight) |
| Llama-3.1-8B-Instruct | llama-3.1-8b-instruct | SELF (in flight) |
| Qwen3-8B | none | same family, later gen, cached |
| Qwen2.5-3B | none | same family, smaller | 
| Meta-Llama-3-8B | none | same family, earlier gen (queued) |
| Llama-3.2-3B | none | same family, later gen (queued, access pending) |
| OLMo-3-7B | none | unrelated family (queued) |

gemini-2.5-flash generations have no matching judge; that cell is a control for all judges.

## 4. Endpoints

**E1 (primary) — label-matched own-vs-other score offset.** For judge J, within the blind regime,
compare J's mean unfaithfulness score on own-generation traces against other-generation traces,
**separately within each true label** (faithful ft1, unfaithful ft2) so that differing base rates
cannot produce the effect. Report the label-averaged offset. Negative = scores its own traces as
more faithful = self-preference in the Panickssery direction.

**E2 (primary) — difference-in-differences against non-self judges.** E1 confounds self-status with
"this generator's traces are easy/unusual". Control with the judges for whom that generator is NOT
self: 
`DiD(J,G) = offset(J on G) - mean over J' with G not self of offset(J' on G)`.
This is the effect that survives generator-difficulty differences. **E2, in the blind regime, is
the single primary comparison.**

**E3 — composition decomposition.** Pooled AUROC minus the size-weighted mean of within-generator
AUROCs, per judge per regime, quantifying how much of each judge's pooled number is cross-generator
comparison rather than discrimination.

**E4 (secondary) — within-generator AUROC**, own vs other. Reported for completeness with the
explicit caveat from §1 that a null here does not bear on self-preference.

## 5. Inference

Question-clustered bootstrap (cluster = source question, matching the existing harness), 2000
draws, seed 0. Intervals are percentile. **Primary comparison is E2 in the blind regime for the two
self-judges that complete (Qwen2.5-7B, Llama-3.1-8B) plus the cached gpt-4o-mini self cell: three
primary tests, Bonferroni alpha 0.0167.** Everything else in §4 is secondary and labelled
exploratory; secondary results may not be promoted to a headline claim without a new spec.

**Seed arms are the noise floor, not extra tests.** Multi-seed arms for a given model estimate
within-model run-to-run spread. Any between-judge difference smaller than that spread is reported
as not distinguishable from noise, exactly as the gpt-5.2 repeat arm forced.

## 6. Advancement rule, fixed now

- E2 significant and negative for the self-judges, null for non-self judges: report as a
  generator-identity composition effect, sized against the correctness composition effect already
  in the paper. Does not change any regime conclusion.
- E2 null: report the null. The FaithCoT leaderboard includes judges scoring their own generations;
  a credible null is itself worth stating, given that the benchmark's own detector rankings pool
  across generators.
- Either way: no manuscript restructuring, no sweep, no new inference beyond the queued arms.

---

## Amendment v1.1 (2026-09-19) — matched-pair design, added before any outcome was computed

**Order of events, stated here because it is what makes this legitimate.** After freezing v1 and
before computing any judge score, an inspection of record identifiers showed that FaithCoT's four
generators answer *the same questions*: 295 of 341 question keys carry all four generators, and the
question text is byte-identical across them (verified on samples). v1's design controlled for
generator difficulty by differencing against non-self judges. The shared-question structure permits
something strictly stronger, so the design is upgraded. **No judge quantity had been computed when
this amendment was written.** The upgrade is driven by data structure, not by a result.

**E1m (new primary) — question- and label-matched own-vs-other offset.** For judge J with
self-generator G, take every question where G produced a trace with true label L and at least one
other generator produced a trace with the *same* label L in the *same* regime. Compare J's
unfaithfulness score on the self trace against its scores on those matched other traces, paired by
question. Averaging over pairs gives an offset in which question difficulty and true label are both
held fixed by construction. Negative = self-preference in the Panickssery direction.

This controls more than v1's E2 did: E2 removed generator-level difficulty, E1m removes
question-level difficulty *and* label composition simultaneously.

**Power, computed as a design fact before any outcome.** Label-matched pairs available:

| self-generator | blind pairs (questions) | correct pairs (questions) |
|---|---|---|
| Qwen2.5-7B-Instruct | 155 (95) | 363 (155) |
| gpt-4o-mini | 152 (94) | 397 (180) |
| llama-3.1-8b-instruct | 139 (85) | 336 (140) |

A fallback rule was fixed before these were computed: E1m is primary if it retains at least 40
blind-regime pairs, else v1's E1 is primary. All three cells clear it by a wide margin, so **E1m is
the primary endpoint** and v1's E1/E2 become secondary corroboration.

**E2m (retained control).** The same matched offset computed for judges for whom G is NOT self.
Under the self-preference hypothesis E1m is negative and E2m is centred on zero. If E2m is also
non-zero, the effect belongs to the generator's traces rather than to self-status, and the
self-preference reading fails. **E2m is a falsification test, not a supporting statistic.**

**Inference unchanged from v1 section 5.** Question-clustered bootstrap, 2000 draws, seed 0.
Three primary tests (the three self-judges), Bonferroni alpha 0.0167. Correct-regime underpower
ruling from section 2 stands: it applies to per-generator *AUROC* cells and does not bar the
matched-offset endpoint, which is a paired mean difference and is well powered there.

**Scope.** gemini-2.5-flash has no matching judge and is a pure control generator throughout.
Two of the three self-judges (Qwen2.5-7B, Llama-3.1-8B) are still in flight; the gpt-4o-mini self
cell is computable from cached data now and will be reported first, with the other two appended
when their arms land. Reporting one cell before the others are available is disclosed rather than
hidden, and the Bonferroni correction is applied over all three regardless of arrival order.
