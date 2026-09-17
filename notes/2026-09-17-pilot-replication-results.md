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
