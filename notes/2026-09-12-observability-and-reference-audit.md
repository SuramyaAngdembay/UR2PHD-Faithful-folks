# What the observable-record and reference-reason audits establish

This offline audit accompanies the autonomous API experiments. Reproduce with
`scripts/observable_collision_audit.py`, passing the pinned FaithCoT source
directory and curated BonaFide CSV. File hashes and machine-readable outputs
are under `results/observable_collision_audit/`.

## Exact records do not establish conflicting full-input labels

The 1,303 joined FaithCoT traces and 1,113 frozen incorrect BonaFide traces are
each distinct within their respective populations. No repeated full observable
record has opposite labels within either population. This remains true for both
the native FaithCoT binary field and the four-way-derived field, considered
separately. Those two fields still disagree on some individual records; that
stored-field inconsistency is a different question from repeated observations
under one declared target.

There are no shared normalized question texts or exact question/trace/answer
records between these two audited populations. This is an exact-text audit, not
proof that underlying semantic questions never overlap. It confirms that the
present evidence is not a paired demonstration of two reference procedures
labeling the very same observable cases oppositely.

Question-only records do have conflicting labels: 200 FaithCoT binary-label
question groups and 43 BonaFide incorrect question groups. This is expected when
different responses to the same question have different process labels. It is
not benchmark corruption. The accompanying in-sample majority-lookup ceilings
are descriptive properties of the finite table; they are not held-out model
performance or evidence of learnable generalization.

## The synthetic impossibility statement is narrow

In the authored controls, the source context changes while the question, CoT
and answer remain fixed. Under restricted evidence each pair therefore has the
same model payload and opposite literal source-claim truth. A function of that
payload must assign the same score to both. With one positive and one negative
at every distinct payload, the empirical score distributions are identical,
so AUROC is exactly .5. A randomized decision independent of the hidden context
also has expected accuracy .5 on this balanced construction.

This demonstrates an information loss deliberately introduced by that evidence
policy. It cannot prove that the real benchmarks are intrinsically incompatible,
that a particular model is optimal, or that adding evidence will solve their
native-label discrimination problem. Absence of conflicting observed twins in
the real corpus does not prove that its labels reveal hidden computation either.

## Whole-label aggregation mixes different reference reasons

The frozen BonaFide incorrect population contains these native whole-label
reasons, classified by the first listed reason in the pinned release's annotation
text. Multiple reasons can coexist; the machine-readable audit also counts their
overlapping flags:

| Released reason category | Responses |
|---|---:|
| All sentences certified faithful, acknowledged or inert | 168 |
| No acknowledgment and no faithful steps | 451 |
| Contains an unfaithful step | 492 |
| Missing required steps | 2 |

These are the annotation system's reasons, not independent process observations.
They nevertheless explain why a literal source-contradiction test and a native
whole-label test need not behave alike. The whole target includes both alleged
violations and certification/omission judgments. A detector can recognize a
source contradiction yet fail to reproduce the broader reference decision.

Batch 1's native unfaithful cases comprise ten no-acknowledgment/no-faithful-step
labels and two explicit-step labels. Batch 2's six matched unfaithful cases
comprise five explicit-step labels and one no-acknowledgment label. These counts
were inspected after selection; the examples were not selected for their reason
or new judge score. Their difference is a further limit on attributing any
between-batch performance change solely to length or generator matching.

The useful next diagnostic is agreement on a particular alleged violation and
the evidence supporting it, separating no verified violation from proof that
the entire trace is faithful. Native reason text can help localize retrospective
review, but must remain outside detector prompts and independent reviewer input.
