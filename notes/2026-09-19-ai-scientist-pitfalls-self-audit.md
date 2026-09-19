# Self-audit against Luo, Kasirzadeh & Shah, "The More You Automate, the Less You See" (2026-09-19)

Paper: arXiv 2509.08713, NeurIPS 2025 AI4Science. It names **four** pitfalls in AI-scientist systems
— inappropriate benchmark selection, data leakage, metric misuse, post-hoc selection bias — and
reports a **fifth** found during its own experiments, **dataset fabrication / undisclosed
subsampling** (§5.2). Its central empirical claim: trace logs and code detect these failures where
the final paper does not, so venues should require those artifacts.

This audits *our* workflow against all five. Evidence is from the repo, not recollection.

---

## P1 — Inappropriate benchmark selection · **LOW on datasets, MODERATE on our own controls**

Their RQ: do systems pick benchmarks that yield high performance more easily, ignoring harder ones?

**We did the opposite, and it is documented.** We ran the datasets where our claims died and
published the deaths: the BonaFide transfer failure (judge inverted, entanglement lift 1.00× —
withdrawn base-rate claim), GRACE non-detection of the regime difference, the synthetic↔FaithCoT
bridge failure, and the metadata-template replication failure (0.452 despite *higher*
in-distribution decodability). A system optimising for favourable benchmarks does not keep these.

**Where we are exposed:** the constructed controls (v1, v1.3) are a benchmark *we authored, with
gold we defined*. v1.3 demonstrated the risk concretely — an unbalanced construction variable
(procedural vs data-bearing absent note) drove detection 0/6 vs 6/6, and we had balanced position,
length, correctness and wording but not that. A benchmark whose hidden structure decides the result
is the same failure, self-inflicted.

**New finding from this audit:** in the native pilot, **faithful responses exist only in SimpleQA**
(both samples). The pooled AUROC is therefore computed partly across tasks, conflating
unfaithfulness with task identity. That is a benchmark-representativeness defect in the population
as used, not just a composition caveat.

## P2 — Data leakage · **STRUCTURALLY STRONG, EMPIRICALLY COMPROMISED**

Structural protections that actually hold: the run path **never opens the native-label key**
(`diagnostic_v2.py`: "Run does not need or open the native-label key"); `lock.json` binds
config+inputs+runner and is now enforced on any partition; prepared inputs are hash-checked before
every run; request identities are payload digests.

But the held-out set is not held out. Measured today across every artefact:

> **CORRECTED 2026-09-19, same day — the figures below were WRONG and far too low.**
> The true exposure is **807/807 (100%)**: `bonafide_predictions.json` carries `judge4o`,
> `judgeA`, `judgeB`, `nli_n_unsup` and `pi` for the entire population, and the frozen eval
> ran its hypothesis tests on n=1113 — dev and eval together — **three hours before the
> dev/eval split was created**. My sweep missed it because it parsed `.jsonl` files and
> `dict['rows']` only, and that file is a top-level JSON *list*. Full analysis:
> [holdout and p-hacking audit](2026-09-19-holdout-and-phacking-audit.md). The superseded
> figures are left below for provenance.

| | scored by a judge | + packet-selected | total touched |
|---|---:|---:|---:|
| eval responses (of 807) | 204 (25%) | +80 | ~~284 (35%)~~ → **807 (100%)** |
| question clusters | 156 | — | ~~203~~ → **425 (all)** |
| eval responses sharing a touched cluster | 397 | — | ~~483 (60%)~~ → **807 (100%)** |
Corrected in that file today.

Also: the replication sample's **18/18 faithful responses had been previously scored or selected**
(found 2026-09-17), and historically we used an unfiltered `hintB` cache when a cleaned one existed,
shipped an audit packet containing labels, and built a frozen-eval population that merged labels
across `question_id`. All were caught and recorded; all were real.

**Important difference from the paper's construct.** There is no training here, so this is not
train/test contamination inflating accuracy. It is *analyst* exposure inflating confidence through
repeated looking. The remedy is not a different split but an explicit ledger of what has been seen.

## P3 — Dataset fabrication / undisclosed subsampling · **LOW — our cleanest pitfall**

This is what sank both systems in the paper: they subsampled or synthesised data and **the final
paper did not disclose it**.

We do both of those things. The diagnostic line is restricted to incorrect-answer responses
(`if r['correct']!=0: continue`), the pilot capped at 70 via `--max-items`, and the constructed
controls are entirely synthetic. Every one is disclosed: the correctness restriction appears in the
notes from June onward, `max_items` is recorded in the run descriptor *and* the lock, and the
constructed controls carry "constructed controls; not benchmark data; never pooled with native
AUROC" in the protocol, the manifest and the analysis output. Synthetic results have never been
reported as native.

## P4 — Metric misuse · **MODERATE, with instances, mostly self-caught**

Documented instances in our own work: calling a categorical-decision improvement "better
calibrated" when nothing about probability calibration was measured; a pre-registered
accusation-level H1 rate that is **1.000/0.000 by construction** and carries no information;
pooled AUROC over cross-task pairs (above); treating a bootstrap tail as a calibrated p-value; and
`n_boot=500` supporting "p<.001".

Protections that worked: endpoints are frozen and hashed *before* inference, so metrics cannot be
swapped after seeing results — and when the pre-registered H1 turned out uninformative we
**reported it as uninformative** rather than substituting a better-looking metric. On GRACE we
report a threshold-free primary plus all five thresholds as a band. We also caught BonaFide's own
score-orientation inconsistency (their `score_cot` contract says higher = more faithful while the
monitor returns `suspicion_score/100`).

## P5 — Post-hoc selection bias · **HIGHEST RESIDUAL RISK**

Their finding: a reward function that sees test performance shifts selection toward
test-favourable candidates (top candidate chosen 78.5% → 43.5% when test scores were inverted).

Our analogue is the analyst, and we have a history of it: the **7× selection-rule improvement that
was an oracle-in-pool artefact**; "cleanest/easiest to detect" contradicted by held-out results;
the note-position "effect" that was read off a balanced covariate after the fact. All withdrawn.

Protections now in place are real: frozen specs, analysis scripts hashed into a checklist before
the first request, `lock.json`, and — the strongest evidence — **v1.3 recorded a pre-registered
prediction that FAILED**, which a selection-biased process does not produce.

**Unremediated exposure:** there is **no multiplicity control across the project's family of
contrasts.** Bonferroni was applied inside the 8-cell transfer grid and nowhere else; ~100 AUROC
figures appear across the notes. Every individual interval is nominal. This is the single clearest
instance where we still do what the paper describes.

## Meta — the paper's core recommendation is already our practice

It asks venues to require trace logs and full code because the final paper hides these failures.
We have: every run in git with request-level ledgers, attempt logs, input/runner/config hashes,
manifests, frozen pre-inference specs, and repeated independent audits. On the artifact-submission
bar we would pass.

**But the mismatch it describes has a sentence-level form here.** Our prose has repeatedly drifted
from our own numbers *in the same file*: "never endorses a false attribution" beside "(1 vs 4)";
"these 70 had not been mined" when 38/70 had; "position doesn't matter at all" over an interval
permitting 14 points. **76 of 253 commits record a correction.** That ratio is the workflow's real
signature — a high error rate paired with a high detection-and-disclosure rate. The paper's thesis
is that only the second half is visible to reviewers, and only if the artifacts are shipped.

## Actions

1. **Superseded:** the eval-exposure figures were corrected again the same day to 807/807 (100%) — see the holdout audit. The 284/203/483 figures were an artefact of a sweep that skipped JSON lists.
2. **Before any eval-partition use:** the set is 100% scored, so decide whether it can still serve
   as held-out, and if so define the cluster-clean subset *now*, in advance.
3. **Build a multiplicity ledger** — enumerate every contrast the project has reported, with its
   correction status — before any of them enters the manuscript.
4. **Add a prose-vs-numbers check** to the note-writing step; the recurring defect is narrative
   drifting from the table directly above it.
5. Treat constructed-control construction variables the way we treat confounds: balance them, or
   test them within-pair (the v1.4 design already drafted).
