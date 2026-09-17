# Pilot replication — frozen 2026-09-17, before any new inference

**Objective.** The four-arm pilot's headline result — restricted component vs restricted generic,
**ΔAUROC +0.293 [+0.093, +0.502]** — rests on a single draw of 70 development responses that has
since been inspected repeatedly. This replicates that one contrast on a question-cluster-disjoint
sample under byte-identical procedures.

## Why a fresh draw, given we already bootstrap

The cluster bootstrap is nominally an estimate of sampling variability, so this is not about
"having no interval". Three things the bootstrap on that sample cannot do:

1. **Approximation quality at 10 positives.** Percentile intervals undercover when resamples
   frequently contain almost no minority-class responses.
2. **Anything constant within the sample.** All ten faithful responses are SimpleQA; every
   resample inherits that. A fresh draw does not.
3. **Inspection contamination.** Those 70 responses were mined repeatedly (accusation audits,
   quote analyses, rationale reading). A disjoint sample is the only clean test.

Reseeding was rejected: a new shuffle of the 306-response dev pool would overlap the pilot by
~16 responses in expectation, and the deterministic next-70 slice shares **23 question clusters**
with the pilot. Disjointness is enforced on clusters, not merely on responses.

## Population

Frozen selection rule (`scripts/build_pilot_replication.py`, no new randomness): shuffle the dev
partition with the pilot config's seed (this reproduces the pilot's own ordering, asserted against
its recorded rids) → drop every response in a pilot question cluster → take **every** available
faithful response, then unfaithful responses per task until the pilot's task composition is matched.

| | pilot | replication |
|---|---:|---:|
| responses | 70 | 70 |
| faithful / unfaithful | 10 / 60 | **18 / 52** |
| discordant pairs (the AUROC's effective sample) | 600 | **936** |
| question clusters | 58 | 55 |
| task mix (SimpleQA / DDXPlus / HLE) | 34 / 22 / 14 | **34 / 22 / 14** |
| response overlap | — | 0 |
| question-cluster overlap | — | 0 |

**Declared deviations from a like-for-like replication.**
1. *Minority class enriched* (all 18 available disjoint faithful responses taken rather than a
   prefix). Licensed because AUROC is a ranking statistic over discordant pairs and is
   prevalence-invariant in expectation, so this raises precision without biasing the estimate.
   Prevalence-dependent quantities — mean score above all — are therefore **not** comparable across
   the two samples and are reported per sample only.
2. *Arms restricted to A1/A2.* The B (full-evidence) arms tested evidence access, which the pilot
   left unresolved and which is not the claim under test. Procedures, model, temperature, token cap
   and schema are byte-identical to the pilot (asserted at freeze by re-deriving each payload from
   the pilot config).

The evaluation partition is not touched. This adds 70 dev responses / 55 clusters to the set of
inspected development data.

## Design and endpoints

70 × {A1, A2} × 3 identical repeats = **420 requests**, pinned `gpt-4o-2024-08-06`, temperature 0.
Estimator, fixed in `scripts/replication_analysis.py` and hashed into the freeze checklist:
per-response mean over its three repeats → rank AUROC per arm → contrast A2 − A1 → question-cluster
bootstrap, 2,000 draws, seed 0, percentile 95%, the same resampled clusters for both arms. The
script aborts unless it first reproduces the pilot's published figures on the pilot's own data.

## Pre-registered criteria (fixed now; all reported whichever way they come out)

- **R1** the sign of the replication contrast, and whether its interval excludes zero;
- **R2** whether the replication point estimate falls inside the pilot interval [+.093, +.502];
- **R3** whether the pilot point estimate (+.2933) falls inside the replication interval.

None of these is a project gate. A replication that fails R1–R3 means the pilot contrast is not
established and must be reported as a single-sample exploratory result; a replication that meets
them makes it a two-sample exploratory finding on development data — still not a method claim, and
still not evidence of native detection, since A2's own interval in the pilot included chance.

## What this cannot do

936 discordant pairs is better than 600, not a lot. This can show the contrast is consistent or
refute a large effect; it cannot pin a magnitude. It says nothing about the verification procedure
of `verification-protocol.md` (a different rubric on constructed controls), nothing about detection
of adjudicated violations, and nothing about the generator's actual reasoning process.
