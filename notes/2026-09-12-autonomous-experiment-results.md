# Autonomous experiment results: evidence access and interpretation

Status at this checkpoint: the source controls, first native pilot, matched
native pilot and corrected monitor baseline are complete. The visibility-comment
ablation has its own frozen protocol and run; its outcome is recorded below when
available. All new natural examples are development examples, not the 807-case
evaluation partition. These are exploratory diagnostics.

## What was run

- 88 unique API calls covering 96 source-control/native comparison slots.
- 60 calls on six fresh matched native pairs across five judging conditions.
- 36 corrective baseline calls after detecting a message-role implementation
  error. The affected D1 interpretation is superseded by corrected D2.
- An offline full-record collision audit and native-reference-reason audit.

The first three runs completed all 184 requests without transport or parsing
errors. Recorded usage was 145,526 input and 7,569 output tokens. The server
reported a 30,000-token/minute rate limit; conservative payload pacing and safe
rate headers resolved the earlier transport problem. Exact request plans, keys
kept outside inference, raw outputs, success records, hashes and code revisions
are retained. See `results/autonomous_campaign_2026-09-12/corrected-results.json`.

## 1. The judge can use decisive source evidence on simple controls

Four authored templates have the same question, trace and answer under two
different source contexts. One context supports the explicit source attribution;
the other contradicts it. Each procedure sees either the full context or the
restricted question/trace/answer record.

Both full-context procedures assign 0 to each supported source claim and 100 to
each contradicted one: eight cases, perfect ordering within this tiny authored
set. Restricted inputs are byte-identical for opposite truths, so their AUROC
is .5 by construction. One prediction is reused for each identical payload.

All four disclosed-verification-intention controls receive component score 0
with no verified false process claim. Among four explicitly uncertain arithmetic
mistakes, three receive the same treatment and one receives score 100 with the
rationale that guessing an incorrect result is a false process. The latter is
not a valid inference from the record. This exposes residual confusion even in
simple cases. None of these authored traces certifies hidden internal reasoning.

The result rules out a blanket claim that this reader cannot compare a source
claim with visible evidence. It does not show that such evidence is available
for every native whole-label decision or that the reader uses it consistently.

## 2. A small native pilot still reverses, with substantial confounding

On 24 fresh question-distinct development examples, 12 per native class:

| Procedure | Balanced accuracy at declared operating point | Correct labels |
|---|---:|---:|
| Full-context generic B1, score threshold 50 | .333 | 8/24 |
| Corrected definition-aware D2, boolean output | .292 | 7/24 |

The paired D2−B1 difference is −.042, with a descriptive 95% question-bootstrap
interval [−.179, .088]. B1's continuous native AUROC is .09375. D2 returns only a
boolean; its AUROC equals balanced accuracy and is not a rich ranking curve.

The sample was selected for coverage, and inspection found **disjoint generators
across the two classes**. Word-count AUROC is .9931 on these same cases. This
pilot cannot establish a within-generator failure or a general population effect.
It motivated the next matched comparison; it does not deserve the paper headline.

The initial D1 baseline had a system/user role conflict. Its apparently higher
.458 balanced accuracy is not retained as a valid baseline claim. Correcting
the implementation made this pilot result worse, and both versions are preserved.
Even D2 adapts the published monitor to a different model/backend and JSON input
layout; this is not a numerical replication of the authors' Gemini experiment.

## 3. Matching changes the useful lead; extra context is not a general repair

The follow-up uses six pairs of opposite native labels, identical generator and
task, word-count ratio at most 1.25, and distinct questions not scored in either
previous native pilot. All are SimpleQA responses from three Instruct generators.
The fixed greedy selection uses covariates and native labels, not new scores.

Here a win means that the unfaithful response receives the higher score within
its matched pair; ties count as half. It is not classification accuracy.

| Procedure | Wins / losses / ties | Within-pair ordering score |
|---|---:|---:|
| Restricted generic A1 | 1 / 3 / 2 | .333 |
| Full-context generic B1 | 0 / 6 / 0 | .000 |
| Restricted component A2 | 5 / 0 / 1 | .917 |
| Full-context component B2 | 2 / 1 / 3 | .583 |
| Corrected full-context definition-aware D2 | 1 / 1 / 4 | .500 |
| Word count | 2 / 4 / 0 | .333 |

The strongest new lead is the component procedure under restricted evidence.
The fixed generic procedure reverses all six pairs even after this matching.
Adding context lowers the average pair score by .333 for both generic and
component procedures in this selected set. This opposes a simple universal
missing-context explanation; it does not establish that less context is generally
better or that the component procedure has solved faithfulness detection.

The sample is tiny. The primary B1−A1 difference has a bootstrap interval
[−.667, −.083], but only three pairs have nonzero changes; a post-hoc exact
two-sided sign check gives p=.25. For A2−A1, five nonzero changes all favor A2;
the analogous sign p is .0625. These tests have different targets, and neither
the selected best arm nor optimistic bootstrap endpoints should become a
confirmatory or multiplicity-corrected claim. Report the six cases themselves.

Further confounds remain: native hint type and reference reason are not matched.
Five of the six unfaithful labels cite an explicit unfaithful step, whereas the
first pilot mostly selected no-acknowledgment/no-faithful-step labels. Changes
between the two pilots cannot be attributed solely to length or generator.

## 4. Some right rankings have questionable supporting explanations

Several A2/B2 rationales infer a false verification claim merely because the
record does not document verification. Without a complete execution record or
another contradiction, that is not sufficient proof. The procedure can therefore
agree with a native label for a reason that has not been independently established.

One full-context output says the Stanford professor's statement is absent even
though that exact statement appears in the original prompt. Two other native
faithful cases score 0 under A2 and 100 under B2: B2 treats a visibility comment
as proof that metadata was inaccessible, despite the metadata being visibly
included and explicitly used by the trace. These are concrete reading errors
about the supplied record, not evidence of unfaithful hidden computation.

The metadata comment is now tested directly with a single-text intervention,
two unchanged-original repeats per case, and separate fresh/discovery groups.
That targeted ablation is more informative than another broad judge leaderboard.

## 5. What the real datasets and reference reasons permit

There are no conflicting labels on repeated full observable records under each
declared native target in the audited populations, and no exact shared
question/trace/answer records between them. The synthetic .5 information ceiling
does not establish a real-data impossibility theorem. Paired application of both
reference procedures to common examples is still needed to measure disagreement.

Native BonaFide whole labels combine several kinds of decisions. The first-listed
categories are 168 all-certified, 451 no-acknowledgment/no-faithful-step, 492
explicit-unfaithful-step and two missing-required-step cases. Reasons overlap:
589 records mention no acknowledgment/no faithful steps, 492 mention an unfaithful
step, and 13 mention missing required steps. They are automated annotation reasons,
not independently observed process facts.

An original prompt may reveal the supplied hint without providing the news report,
biography or execution record needed to verify an alleged source/process claim.
That difference separates prompt access from access to decisive verification
evidence. The source controls and native whole-label experiment test different
amounts of evidence and different aspects of the target.

## Consequence for the paper

The emerging study concerns **how evidence is interpreted under different
faithfulness reference procedures**. It has a reproduced external failure and a
specific development lead, but not a validated new method. The component rubric's
ranking gain, the context interaction and the faulty source-access allegations
should guide new independently checkable examples and evidence-presentation
controls. A successful future verifier must demonstrate valid claims and useful
coverage, not just improve AUROC against one automated whole-label rule.

The revision map is `paper/arr/measurement-study-outline.md`. It keeps the scoped
FaithCoT findings, narrows the main storyline, and moves the representation and
constructed-training side studies into supporting material where appropriate.
The old universal two-regime title and mechanism interpretation remain unsupported.
