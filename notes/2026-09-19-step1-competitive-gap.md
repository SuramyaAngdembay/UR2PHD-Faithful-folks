# Step 1 — competitive gap by regime: results (2026-09-19)

Spec frozen at `60a30d3` **before** running (`step1-competitive-gap-spec.md`). Cached public data
only, no new inference. Regimes keyed on `ft`, never on the misnamed `correct` field.
Script `scripts/step1_competitive_gap.py`; run on Aquaman for sklearn.

## Independent reproduction of the published table

Computed from a different code path than `audit_corrected.py`, and it lands on the same numbers:

| | this run | published |
|---|---:|---:|
| soft, correct regime | 0.667 | 0.6667 |
| avg_impact, correct regime | 0.659 | 0.6591 |
| nli_n_unsup, correct regime | 0.622 | 0.6259 |
| step count, correct / incorrect | 0.620 / 0.505 | 0.620 / 0.505 |
| judge, correct / incorrect | 0.830 / 0.679 | 0.830 / 0.679 |

## RETRACTION — my "correction" about the judge numbers was wrong

I told the user that Codex had misattributed 0.830, that it was "the pooled figure, not the
correct-answer figure", and that the regime values were "0.675 / 0.814". **All three were wrong.**

The paper reads: *"degrades exactly there **(0.830 → 0.679)**, robustly across prompts and judge
models"*, and separately reports Δ **0.152 [0.089, 0.211], p<0.001**. The "0.675 / 0.814" figures
belong to a *different* sentence — the ablation excluding the 340 traces GPT-4o-mini judged of its
own generations (*"full 0.777; regimes 0.675 / 0.814"*). My fresh computation independently gives
correct 0.830 / incorrect 0.679 / pooled 0.783.

**Codex's original statement was accurate.** Root cause: I grepped "regimes 0.675 / 0.814" and
assumed it was the main regime split without reading the sentence it sat in — and the truncated
grep hid the `(0.830 → 0.679)` parenthetical. The `0.151 vs 0.139` gap-inflation claim I made was
itself the fabricated quantity; the paper's own Δ is 0.152.

## The answer to the pre-registered question

**INCORRECT regime (n=514, 233 unfaithful) — everything computable:**

| detector | AUROC | 95% CI | |
|---|---:|---|---|
| **judgeA** | **0.679** | [0.629, 0.728] | clears chance |
| text baseline (TF-IDF, grouped CV) | 0.593 | [0.533, 0.648] | clears chance |
| words | 0.557 | [0.504, 0.604] | clears chance |
| nli_min_ent | 0.423 | [0.370, 0.476] | **inverted** |
| nli_mean_ent | 0.443 | [0.386, 0.496] | **inverted** |
| soft / hard / avg_impact / dag×2 / nli_n_unsup / nli_frac_con / n_steps | .476–.530 | all cover 0.5 | |

**The paired tests are what matter, and they close the question:**

| contrast | INCORRECT | CORRECT |
|---|---|---|
| **text − length** | +0.035 [−0.041, 0.111] | +0.035 [−0.042, 0.109] |
| **judge − text** | **+0.086 [+0.028, +0.152]** | **+0.137 [+0.073, +0.200]** |
| words − steps | +0.053 [−0.014, 0.119] | +0.038 [−0.030, 0.110] |

**A supervised text baseline is not distinguishable from word count, in either regime.** Its
nominal clearing of chance in the blind regime (0.593) is not evidence of extractable semantic
signal. **The judge beats both, significantly, in both regimes** — it is finding something a
bag-of-words model does not.

This is **pre-registered reading #1**: in the incorrect regime nothing computable beats length
except the judge. For the proposed correctness-matched training objective over these features,
there is nothing to recover. **The method door closes on evidence, not on prior.**

## Scoping — what this does NOT establish

- **TF-IDF is a weak text model.** "No signal beyond length extractable by a bag-of-words model"
  is not "no signal in the text." A fine-tuned encoder could find more; that is untested.
- It says nothing about **internals** — the white-box probe reaches 0.71 in this regime.
- It says nothing about methods operating at the **judge's** representational level, which is
  precisely where the only surviving signal lives.

## Two smaller findings

**Word count vs step count.** Word count nominally clears chance in the blind regime (0.557) where
step count does not (0.505), which would contradict the paper's *"in the incorrect regime not even
length carries signal."* But the **paired** difference is +0.053 [−0.014, 0.119] — not established.
**The paper's claim stands**, and I nearly committed the Gelman–Stern error I had flagged for
others four hours earlier.

**NLI inverts in the blind regime.** `nli_min_ent` 0.423 [0.370, 0.476] and `nli_mean_ent`
0.443 [0.386, 0.496] are both significantly *below* chance. The paper reports pooled mean-entailment
at 0.493 [0.447, 0.538]; whether the regime-specific inversion is already stated should be checked
before treating it as new.

## Repo hazard recorded

`results/rigorous_features.json` ships a field named `correct` defined as `1 if ft in (1,2)` — so
**`correct=1` means INCORRECT-answer**, the inverse of its name — while `results/judge_join.json`
uses the opposite convention. `audit_corrected.py` keys on `ft` and is safe; the display strings at
`rigorous_analysis.py:131-132` are stale pre-correction labels. Reading the field naively inverts
every regime result.

---

## FOLLOW-UP (same day) — the "NLI inversion" is WITHDRAWN, and a 14/14 exact reproduction

I flagged `nli_min_ent` 0.423 and `nli_mean_ent` 0.443 in the blind regime as a possible second
metric inversion. **It is not an inversion.** Both measure *entailment* — higher entailment means
more support, hence more faithful — so as predictors of **un**faithfulness their natural direction
is negated. `audit_corrected.py` applies exactly that (`("nli_mean_ent","nli_mean_ent",-1)`). My
step-1 table reported the **raw** direction, so values below 0.5 are the metric working correctly.

Contrast with the paper's genuine inversion: `soft_intended` at **0.3333** in the correct regime.
`soft_faithfulness` is *already oriented* so that higher = more faithful, and it still lands far
below chance. That is an inversion. Entailment sitting below 0.5 in its raw direction is not.

**Two causes of my discrepancy, both now resolved:** the sign convention above, and population —
`audit_corrected.py` filters to rows complete on all of `soft/nli_*/dag_*` (**n=633**, because
`soft` exists only for the two open-weight models), whereas my step-1 run used all 1,303 rows for
the NLI and DAG signals.

**Exact reproduction.** Applying the published sign map on the published subset, a fresh
implementation reproduces `audit_corrected.json` in **14 of 14 cells to 4 decimal places** across
both regimes (soft_raw, soft_intended, nli_n_unsup, nli_mean_ent, dag_lin, dag_maxlb,
interventions). Independent verification of the paper's central table.

### Does anything in the blind regime beat length once signed?

Tested on the **full labeled set** (n=514, 233 unfaithful) rather than the 270-row subset the
paper's "all n.s." claim rests on:

| signal (signed) | AUROC | 95% CI | |
|---|---:|---|---|
| nli_min_ent | 0.577 | [0.524, 0.630] | clears chance |
| nli_mean_ent | 0.557 | [0.504, 0.614] | clears chance |
| **words (length)** | 0.557 | [0.504, 0.604] | clears chance |
| nli_n_unsup | 0.518 | [0.464, 0.572] | covers 0.5 |

**Paired, signed nli_min_ent − words: +0.020 [−0.059, 0.102] — covers zero.**

So on the larger population several weak signals nominally clear chance, but **none is
distinguishable from a length baseline.** That is not a contradiction of the paper, whose claim is
scoped to the complete-feature subset; it is a power difference, and the paired test settles it the
same way as the text baseline (+0.035 [−0.041, 0.111]).

### Net effect on the step-1 conclusion: strengthened

Four things in the blind regime nominally clear chance — min-entailment, mean-entailment, word
count, and the TF-IDF text baseline. **In paired tests not one of them beats length.** The judge
(0.679) beats the text baseline by +0.086 [+0.028, +0.152] and remains the only detector that
significantly clears the length bar. The pre-registered reading holds, with a wider margin than the
first pass showed.

---

## Current-judge arm (gpt-5.2) — pre-registered reading, fixed before the run

Single-variable change to a frozen procedure: `scripts/judge_baseline.py`, **prompt A verbatim**,
same 1,303-trace population, same message skeleton; only `--model` differs. Prior arms:
gpt-4o-mini **0.679**, gpt-4o **0.670**, prompt-B **0.667** in the blind regime — flat within 0.012
across two models and two prompts.

API deltas forced by the model family (recorded as deviations): GPT-5 rejects `max_tokens` →
`max_completion_tokens=2000`; it has no `temperature` control → omitted. Everything else identical.
Default reasoning effort (smoke test showed **0 reasoning tokens** on a short item).

**Pre-registered readings:**
- **Blind regime stays ≈0.67–0.68** → the weakness is a property of the problem, not of 2024-era
  judges. The paper's claim strengthens to "stable across model generations."
- **Blind regime rises materially (say ≥0.75)** → the "metric-blind regime" framing weakens and the
  manuscript needs revision before submission.
- **Correct regime moves but blind regime does not** → the gap widens; the regime asymmetry is the
  durable finding.

Cost: gpt-5.2 at $1.75/1M in, $14/1M out ⇒ ≈$2.15 for 1,303 calls. Pilot (n=30) returned 17
distinct scores spanning 8–95, so the judge is grading rather than degenerate.

---

## Current-judge arm — RESULT (gpt-5.2-2025-12-11, 1303/1303, 0 errors)

| judge | correctness-tracking | pooled | **blind** | correct | regime gap |
|---|---:|---:|---:|---:|---:|
| gpt-4o-mini (prompt A) | 0.684 | 0.782 | 0.679 [.633,.721] | 0.830 | 0.151 |
| gpt-4o (prompt A) | 0.745 | 0.790 | 0.670 [.623,.713] | 0.786 | 0.116 |
| gpt-4o-mini (prompt B) | 0.662 | 0.745 | 0.667 [.623,.712] | 0.786 | 0.119 |
| **gpt-5.2 (prompt A)** | **0.816** | **0.819** | **0.653 [.606,.699]** | **0.830** | **0.177** |

**Paired, same 1,303 traces, question-grouped bootstrap (gpt-5.2 − gpt-4o-mini):**

| | 5.2 | 4o-mini | paired diff | |
|---|---:|---:|---|---|
| blind regime | 0.653 | 0.679 | **−0.026 [−0.067, +0.015]** | covers 0 |
| correct regime | 0.830 | 0.830 | **−0.000 [−0.051, +0.046]** | covers 0 |
| **score vs incorrectness** | 0.814 | 0.683 | **+0.131 [+0.106, +0.159]** | **SIGNIFICANT** |

### The finding

**A frontier judge is dramatically better at inferring answer correctness and no better at
detecting unfaithfulness in either regime.** The only significant paired change across a
two-generation capability jump is correctness inference (+0.131). Both faithfulness endpoints are
flat.

Yet the **pooled** score rises 0.782 → 0.819, making gpt-5.2 the best judge on the aggregate
leaderboard number. That gain is composition, not detection: pooled AUROC is fed by cross-regime
pairs, and the judge got better at exactly the covariate that separates those pairs. This is the
paper's own composition thesis demonstrated on a frontier model — **the aggregate metric rewards
correctness inference, not faithfulness detection.**

Monotone across three model generations: correctness-tracking 0.684 → 0.745 → 0.816, pooled
0.782 → 0.790 → 0.819, blind regime 0.679 → 0.670 → 0.653.

### Against the pre-registered readings

**Reading #1 holds**: the blind regime stays ≈0.65–0.68 — the paired difference covers zero, so
this is *no improvement*, not a decline. The weakness is a property of the problem, not of
2024-era judges, and the paper's claim strengthens to **stable across model generations and two
prompts** (four arms now span 0.653–0.679, a range of 0.026).

Not established: that gpt-5.2 is *worse* in the blind regime. −0.026 [−0.067, +0.015] covers zero
and must not be reported as a decline.

### Scope

One prompt (A) for the new arm; prompt B untested on gpt-5.2. Two API deviations forced by the
model family and recorded at freeze: `max_completion_tokens` replaces `max_tokens`, and GPT-5 has
no `temperature` control (the 2024 arms used temperature 0). Default reasoning effort. One
provider — a non-OpenAI frontier judge remains untested, and Kim et al. (ICML 2025) warn that
error correlation *rises* with capability, so cross-provider is the meaningful independence test.

### What this settles for the method direction

Combined with the earlier finding that nothing computable beats a length baseline in the blind
regime except the judge, and that the judge itself does not improve with two generations of
capability: **there is no evidence of accessible headroom in the blind regime from stronger
general-purpose judging.** Step 1 is complete. Steps 2–4 of the Codex track remain closed for the
feature-based proposal; what stays open is internals (the probe reaches 0.71 there) and
cross-provider judging.

## Two further arms — frozen before running

Cross-provider is unavailable (only an OpenAI key exists on Aquaman; Anvil is down), so the
independence test against Kim et al. must wait. The two most informative OpenAI-only arms:

- **gpt-5.2, prompt A, repeat.** GPT-5 has no `temperature` control, so this measures run-to-run
  stability of a nominally fixed configuration. Non-trivial: the BonaFide judge showed 25–31%
  disagreement across *identical* temperature-0 repeats, so "deterministic" is an assumption to
  test, not to rely on.
- **gpt-5.2, prompt B** (the independently-worded rubric already used for gpt-4o-mini). Completes a
  2×2 of {4o-mini, 5.2} × {A, B} and separates "current model" from "current model + this prompt."

Together with the completed arm this gives three gpt-5.2 measurements.

**Pre-registered:** the blind-regime figure is expected to stay within ≈0.63–0.70. A repeat that
moves it outside that band would mean the single-run numbers in this table carry more noise than
their bootstrap intervals suggest, and every judge comparison here would need repeat-averaging.

## Three gpt-5.2 arms — RESULT, and a withdrawal

| arm | corr-track | pooled | blind | correct |
|---|---:|---:|---:|---:|
| gpt-4o-mini A | 0.684 | 0.782 | 0.679 [.633,.721] | 0.830 |
| gpt-4o A | 0.745 | 0.790 | 0.670 [.623,.713] | 0.786 |
| gpt-4o-mini B | 0.662 | 0.745 | 0.667 [.623,.712] | 0.786 |
| gpt-5.2 A | 0.816 | 0.819 | 0.653 [.606,.699] | 0.830 |
| **gpt-5.2 A (repeat)** | 0.823 | 0.811 | **0.630 [.581,.676]** | 0.817 |
| gpt-5.2 B | 0.815 | 0.810 | 0.654 [.606,.701] | 0.797 |

### The headline: an identical configuration does not reproduce itself

Paired, same 1,303 traces, **gpt-5.2 prompt A run twice with no configuration change whatsoever**
(GPT-5 has no temperature control):

| | run 1 | run 2 | paired diff | |
|---|---:|---:|---|---|
| **blind regime** | 0.653 | 0.630 | **+0.023 [+0.002, +0.044]** | **SIGNIFICANT** |
| correct regime | 0.830 | 0.817 | +0.013 [−0.004, +0.029] | covers 0 |
| correctness-tracking | 0.814 | 0.822 | −0.007 [−0.014, −0.000] | marginally sig |

**Two runs of the same configuration differ significantly by the same bootstrap procedure used to
compare different models.** Item-level: the two runs give an **identical score on only 25.9%** of
1,303 traces, mean |Δ| = 4.3 on a 0–100 scale (max 77), Spearman 0.957. That closely matches the
25–31% temp-0 repeat disagreement measured on the BonaFide judge — the same property, a different
dataset, and two model generations apart.

**Consequence, and it is a retraction.** I described the arms as *"monotone across three model
generations: blind 0.679 → 0.670 → 0.653."* That spread is **0.026**; the spread between two
identical runs is **0.023**. The apparent trend is not distinguishable from run-to-run noise and
the "monotone decline" framing is **withdrawn**. (The paired model-vs-model test already covered
zero, so the hedge was right; the narrative around it was not.)

### Prompt sensitivity is regime-specific

| gpt-5.2, prompt A vs B | diff | |
|---|---|---|
| blind regime | −0.001 [−0.030, +0.025] | covers 0 |
| correct regime | **+0.033 [+0.013, +0.055]** | **SIGNIFICANT** |
| correctness-tracking | +0.001 [−0.009, +0.011] | covers 0 |

The blind regime is **essentially prompt-invariant** (−0.001) while the correct regime is
prompt-sensitive. So the blind-regime weakness is not an artefact of rubric wording.

### What survives, and what it means for the paper

**Survives easily.** Correctness-tracking across the three gpt-5.2 arms is 0.816 / 0.823 / 0.815 —
spread 0.008, a third of the blind-regime run noise — and the gap to gpt-4o-mini is **+0.131
[+0.106, +0.159]**, roughly six times the noise floor. *A frontier judge is much better at inferring
answer correctness and no better at detecting unfaithfulness* stands, and is now measured against a
known noise floor rather than assumed stable.

**Strengthened.** The blind-regime weakness holds across three model generations, two prompts and a
repeat: six arms spanning 0.630–0.679. "Stable" is the claim; "declining" is not.

**New methodological finding, and it applies to our own manuscript.** Single-run judge AUROCs carry
≈±0.023 of run-to-run noise in the blind regime, which is *larger than most cross-model differences
anyone would want to report*. The paper's judge table is single-run. The headline regime gap
(Δ 0.152 [0.089, 0.211]) is ~6.5× the noise floor and is safe; smaller judge comparisons in this
project are not, and should be repeat-averaged before they are quoted.
