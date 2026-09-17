# Pilot replication — results (2026-09-17)

Spec `pilot-replication-spec.md` (frozen `6621b14`, before inference). Run
`results/diagnostic_v2/rep-eval/` — 420/420, `gpt-4o-2024-08-06`, temp 0, no failed slots;
19 ledger errors, all `rate_limit_exceeded` on attempt 1 of distinct requests, longest
consecutive-failure streak 1 (cap 12), every one resolved on retry. Analysis
`results/controlled_verification/replication-analysis/` from `scripts/replication_analysis.py`
**run unchanged** (hash equal to the freeze checklist), which first reproduced the pilot's
published figures on the pilot's own data before touching the new sample.

Integrity: request ids equal the frozen plan in order, lock digest matches via the harness's own
`digest`, run identity equals the lock, responses hash equals the completion marker, single model.

## Result

| | pilot | replication |
|---|---:|---:|
| responses (faithful / unfaithful) | 70 (10 / 60) | 70 (**18 / 52**) |
| question clusters | 58 | 55 (**zero overlap**) |
| discordant pairs | 600 | **936** |
| task mix | 34 / 22 / 14 | 34 / 22 / 14 |
| **A1** restricted + generic | .2175 [.107, .345] | **.2767 [.153, .418]** |
| **A2** restricted + component | .5108 [.320, .694] | **.5994 [.426, .747]** |
| **A2 − A1** | **+.2933 [+.093, +.502]** | **+.3226 [+.194, +.459]** |

Pre-registered criteria, fixed before the run: **R1** sign positive and interval excludes zero —
**met**. **R2** replication point inside the pilot interval — **met**. **R3** pilot point inside the
replication interval — **met**. Intervals overlap.

## Reading

1. **The contrast replicates on a question-cluster-disjoint sample.** +.293 → +.323, both intervals
   excluding zero, each point estimate inside the other's interval. The pilot result was not an
   artefact of that particular draw, and it survives a sample the analysis had never seen (the
   pilot's 70 had been mined repeatedly by then; these 70 had not).
2. **The generic inversion replicates too**, and it is the sturdier half: A1 = .2767 [.153, .418],
   an interval excluding .5 from below, matching the pilot's .2175 [.107, .345]. A judge scoring
   *backwards* against native labels is now a two-sample finding on development data.
3. **Detection is still not established.** A2 = .5994 with interval [.426, .747] — it includes
   chance, as it did in the pilot. The point estimate rose (.511 → .599) but the intervals overlap
   heavily and the samples differ; **nothing should be read into that movement.** What replicates is
   a *relative* shift away from an inverted baseline, not a detector.
4. **The interval tightened as designed** (width .409 → .266), which is the minority-class
   enrichment doing its job. Mean scores are prevalence-dependent and are **not** compared across
   the samples; the analysis output labels them accordingly.

## What this does not touch

Nothing here concerns the verification procedure of `verification-protocol.md` — a different rubric
on constructed controls. Nothing here measures detection of adjudicated violations, native
accusation validity, or the generator's actual reasoning process. Still one model, one provider,
development data only; the 807-response evaluation partition remains unused by this run, which adds
70 dev responses / 55 clusters to the inspected development set.

## Status of the claim

"Restricted component vs restricted generic, ΔAUROC ≈ +.29 to +.32" moves from a single-sample
exploratory result to a **two-sample exploratory result on development data, replicated under
byte-identical procedures on disjoint questions**. It remains exploratory: no multiplicity control
across the family of contrasts run in this project, one judge family, and A2's absolute performance
is indistinguishable from chance in both samples.

## CORRECTIONS AND SENSITIVITIES (same day, after the independent live audit `101e117`)

The frozen primary analysis above is unchanged. Everything in this section is **exploratory and
post hoc**, prompted by an audit that caught a claim I had not checked.

### 1. "These 70 had not been mined" is false

I checked disjointness only against the four-arm pilot. Sweeping every result artefact:

| exposure | count |
|---|---|
| responses previously scored or selected in an earlier campaign | **38 / 70** |
| responses sharing a question cluster with one | 45 / 70 |
| **faithful responses previously exposed** | **18 / 18** |

Sources: the diagnostic audit withheld key (24), BonaFide reconciliation arms A/B/C (21/13/13),
the audit packet key (12), autonomous batch 1 (10), the metadata-comment ablation (6), and others.
The live audit reported 19/70 and 15/18; my broader sweep, which counts packet selection as well as
scoring, finds worse. **This was a foreseeable consequence of my own enrichment rule**: dev holds
only 40 faithful responses, earlier campaigns had sampled them heavily, so "take every available
faithful" guaranteed maximal exposure.

What this does and does not undercut. The judge calls here are fresh — new request ids, temperature
0, no memory across calls — so there is **no leakage channel** from prior scoring into these scores,
and the result stands as an out-of-sample test with respect to the pilot's questions. What it
undercuts is reason 3 of the spec (*inspection contamination*): I cannot claim these responses were
unseen by the project. This replication tests the **sample**, not the **campaign**.

### 2. "Task mix identical" was true only in aggregate

Matching overall task counts while enriching the minority class necessarily shifted the *unfaithful*
composition: pilot unfaithful 24 SimpleQA / 22 DDXPlus / 14 HLE, replication unfaithful **16** / 22 /
14. The two populations are not equivalent, and prevalence-invariance of AUROC does not make them so.

### 3. The pooled AUROC contains cross-task pairs — and that matters

**Faithful responses exist only in SimpleQA, in both samples.** So task-standardisation is not
possible, and the pooled AUROC is computed partly from cross-task pairs (a SimpleQA faithful against
a DDXPlus unfaithful), which conflates unfaithfulness with task identity. The only within-task
estimand available is SimpleQA-only:

| | pilot (10f/24u) | replication (18f/16u) |
|---|---|---|
| A1 generic | .3083 [.135, .487] | **.4132 [.196, .613]** |
| A2 component | .6312 [.382, .869] | **.8316 [.666, .957]** |
| **A2 − A1** | **+.3229 [+.059, +.614]** | **+.4184 [+.238, +.633]** |

Three readings, in order of confidence:

- **The contrast survives within-task in both samples** and is, if anything, larger there. So the
  headline contrast is not a task-discrimination artefact. This is the most reassuring result here.
- **The pooled inversion is partly a task effect.** Pooled A1 = .277, but SimpleQA-only A1 = .413
  with an interval that includes chance. Part of what the pooled number measures is that the judge
  scores DDXPlus/HLE responses differently from SimpleQA ones. This caveat applies to the *pilot's*
  pooled figures too. It is not evidence against the inversion generally — the separate frozen
  BonaFide evaluation found the judge inversion **strengthening** under model×task×word-band
  conditioning (.419 → .260 → .193) — but the pooled pilot AUROCs should not be quoted as if
  within-task.
- **A2 = .832 [.666, .957] in the replication's SimpleQA-only subsample excludes chance** — the
  first time component detection has cleared chance with an interval. It is **post hoc**, on 34
  responses, **not** the pre-registered endpoint, and **not** consistent with the pilot's SimpleQA-only
  A2 (.631, interval includes chance). The subsample is also the best-balanced data the project has
  had (18f/16u), so better power is a sufficient explanation. Report it; do not claim detection.

### 4. An exposure sensitivity is impossible on this sample

Of the 32 responses never previously scored or selected, **zero are faithful**. A contrast
restricted to unexposed responses is therefore not computable, and I cannot empirically bound an
exposure effect here. Acknowledged, not resolved.

### What still stands

The pre-registered result is unaffected: the contrast replicates on a pilot-disjoint sample, meeting
R1–R3, and it survives the within-task restriction in both samples. What I withdraw is the framing
of this sample as *unseen* data, and the implication that its pooled AUROCs are task-clean.
