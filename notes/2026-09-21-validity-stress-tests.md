# Validity stress tests on the two-regime result and the judge ceiling (2026-09-21)

Cached data only. Run while preparing a whole-campaign review. **Single-pass, not independently
audited** — treat every number here as Measured, not Verified. Exploratory; no spec preceded them.

## 1. The benchmark's two human label fields disagree 2.8x more often in the blind regime

`judge_join.json` carries both the binary `unf` field and the four-way `ft` code. They come from the
same annotation effort but are stored separately. The manuscript reports 95.7% co-occurrence overall.
Split by regime that figure is not uniform:

| regime | n | disagreements | rate |
|---|---|---|---|
| blind (ft1, ft2) | 514 | 36 | **7.00%** |
| correct (ft3, ft4) | 789 | 20 | 2.53% |

Within the blind regime the disagreement is almost entirely on one side: **32 of 281 ft1 traces
(11.4%)** — coded "faithful, incorrect" in the four-way field — are marked unfaithful by the binary
field, against 4 of 233 ft2 (1.7%).

Reading: "honest error versus unfaithful error" is a measurably fuzzier human judgement than
"genuine solution versus rationalisation". This is a **lower bound** on label noise, since two
fields from one annotation effort share most of their errors. It is also far too small on its own
to explain a 0.68 ceiling — a perfect detector under 7% label noise would still score above 0.9.
**The missing number is real inter-annotator agreement per regime**, which we do not have.

## 2. Judge errors in the blind regime are shared, not independent

If judges were independently noisy readings of a clean label, averaging them should help.

| regime | best single judge | 3 API judges averaged | 7 judges (>=7B) averaged | API-trio mutual Spearman |
|---|---|---|---|---|
| blind | 0.679 | 0.686 | 0.700 | **0.652** |
| correct | 0.834 | **0.879** | 0.840 | 0.589 |

In the correct regime, ensembling the three API judges lifts AUROC by +0.045. In the blind regime
it lifts it by +0.007, even though the judges agree with **each other** *more* there (0.652 against
0.589). They are consistently seeing something the labels do not reward. That pattern has two
readings this data cannot separate: a blind spot shared by every LLM judge, or labels that are less
reliable in this regime. Test 1 says the second is at least partly true.

**Consequence for the ceiling claim:** "no judge exceeds 0.679" is a statement about single judges;
a seven-judge ensemble reaches 0.700, inside noise of it. And a capability-invariant ceiling is
exactly what a label-reliability limit would produce, so the ceiling must not be presented as
evidence that the *problem* is intrinsically hard without that caveat.

## 3. The blind regime is not blind in mathematics

Blind-regime judge AUROC (ft1 v ft2) by domain:

| judge | AQuA (n=83) | HLE-Bio (149) | LogiQA (148) | TruthfulQA (134) |
|---|---|---|---|---|
| gpt-4o-mini | **0.880** | 0.636 | 0.624 | 0.604 |
| gpt-5.2 | **0.858** | 0.668 | 0.559 | 0.582 |
| gpt-4o | **0.793** | 0.680 | 0.612 | 0.571 |
| Qwen3-8B | **0.801** | 0.620 | 0.525 | 0.556 |
| Llama-3.1-8B | **0.750** | 0.658 | 0.574 | 0.536 |

For gpt-4o-mini, AQuA blind 0.880 against AQuA correct 0.905: **in mathematics there is essentially
no regime gap.** The pooled 0.679 is itself a composition over domains — the same critique the
manuscript levels at pooled benchmarks, one level down. The manuscript's appendix already reports
these per-domain figures; the main-text framing does not reflect that one domain shows no gap.

This suggests a sharper and more testable hypothesis than "incorrect answers are hard": unfaithful
errors are detectable where the steps are **checkable from the text** (arithmetic) and hard where
they are not (knowledge and informal logic). Untested. It also argues against a pure label-noise
account, unless annotation is itself harder outside mathematics.

## 4. Generator effect versus label effect, compared fairly

The campaign note compared a max-minus-min over four generator means against a single two-group
label contrast, which flatters the generator side (an order statistic over four groups against one
difference; the question-only control calibrates its floor but not its scale). The fair version is
variance uniquely explained, with question fixed effects, blind regime:

| judge | unique R² label (1 df) | unique R² generator (3 df) |
|---|---|---|
| gpt-4o-mini | 0.022 | 0.143 |
| gpt-4o | 0.022 | 0.097 |
| gpt-5.2 | 0.002 | 0.149 |
| Llama-3.1-8B | 0.010 | 0.167 |
| Qwen3-8B | 0.020 | 0.105 |
| question-only control | 0.001 | 0.002 |

Per degree of freedom the generator still explains more than the label for every competent judge.
**The direction of the earlier claim survives the fairer test**; the earlier ratio figures
(1.06x to 5.90x) should be replaced by these, since they were not on a common footing.
(numpy emitted spurious matmul warnings on a rank-deficient design; R² values are in range and the
control behaves, but this has not been independently re-implemented.)

## 5. A stale sentence in the manuscript

`paper/arr/main.tex` line 150 says "in the incorrect regime not even length carries signal" and that
a learned text baseline "also fails (0.446 / 0.474)". On the full blind regime (n=514) with
question-grouped CV, from the frozen step-1 run:

| signal | AUROC | 95% CI |
|---|---|---|
| step count | 0.505 | [0.451, 0.556] |
| **word count** | **0.557** | **[0.504, 0.604]** |
| **bag-of-words text baseline** | **0.593** | **[0.533, 0.648]** |

The sentence is true of step count and false of word count. The accurate claim is the paired one:
several cheap signals nominally clear chance, **none beats word count** (text - length
+0.035 [-0.041, +0.111]), and only the judge does.

---

## 6. Two method-motivating hypotheses, tested on cached data — both negative

Run to answer "is a methodology direction possible?". Exploratory, single-pass, Measured.

**6a. Does a judge detect unfaithful errors better on questions it answered correctly itself?**
Three of our judges are also FaithCoT generators, so each judge's own correctness per question is
known from its own trace. Blind regime, traces by the *other* three generators only.

| judge | it answered correctly | it answered wrong |
|---|---|---|
| gpt-4o-mini | 0.685 [0.571, 0.790] (n=111) | 0.659 [0.597, 0.723] (n=261) |
| Qwen2.5-7B | 0.761 [0.661, 0.845] (n=117) | 0.595 [0.530, 0.661] (n=256) |
| Llama-3.1-8B | 0.703 [0.582, 0.826] (n=74) | 0.590 [0.521, 0.655] (n=252) |

The pooled gap for the two local judges looks like support for the Krumdick et al. account, but it
is **mostly domain composition**: the "answered correctly" bucket is 41% / 32% AQuA against 5-6% in
the other bucket, and AQuA is the easy domain. Within domain the effect is small and inconsistent
(LogiQA +0.07 to +0.10 at n=25-37; TruthfulQA zero or negative). For gpt-4o-mini in AQuA the judge
scores 0.92 whether or not it got the question right itself (n=30 / n=22). **What matters is whether
the domain's steps are checkable from the text, not whether the judge knows the answer.** This lowers
the prior that a reference-guided ("solve-then-judge") method breaks the ceiling.

**6b. Does inter-judge agreement identify where blind-regime detection works?** Seven-judge ensemble,
abstaining on the items where judges disagree most (selection uses no labels).

| coverage | all domains | AQuA removed |
|---|---|---|
| 100% | 0.700 | 0.652 |
| 50% most-agreed | 0.710 | 0.636 |
| 33% most-agreed | 0.692 | 0.629 |
| 25% most-agreed | 0.656 | 0.576 |

Against random subsets of equal size at 33% coverage, non-math: observed 0.629, null mean 0.652,
p = 0.73. **Agreement carries no information about where the judges are right.** An
agreement-based abstaining monitor has no support.

**Reading the two nulls together with test 2.** In the non-mathematical blind regime the judges agree
with one another, are wrong together, gain nothing from being averaged, and give no behavioural
signal that separates the items they get right from the ones they get wrong. That is the signature
of a target that is either not observable from the text or not reliably labelled. If so, a better
*text-side* method cannot find it, which bears directly on the trained-detector direction. The one
signal in our data that is uncorrelated with the judge and still informative in this regime is the
internal probe (judge-probe Spearman 0.05; Llama held-out 0.67; combination 0.699 against the judge
alone, paired delta [+0.02, +0.19], n=144).
