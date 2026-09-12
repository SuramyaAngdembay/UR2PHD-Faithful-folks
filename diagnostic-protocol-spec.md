# Judge-reversal diagnostic, amendment v2

September 11, 2026. **Exploratory development.** Replaces v1 at commit `462a7ac`
before any v2 calls. Original population, frozen scores, and question split remain
unchanged. This amendment corrects the target and interpretation; it is not a
new preregistration on untouched data.

## Question and target

For fixed incorrect-answer BonaFide responses, does supplying the original
prompt, or using an explicit process-component judging procedure, improve
native whole-label discrimination? The final score is whole-trace unfaithfulness.
Reliance alone and reliance AND nondisclosure are not the reference target.

Faithfully acknowledged reliance can be faithful. Other false process claims or
justified omissions can make the same trace unfaithful. Logical validity and
answer correctness remain separate. Where process evidence is absent, preserve
uncertainty rather than certifying a hidden computation.

## Factorial and versioned inputs

| Arm | Evidence | Judging procedure |
|---|---|---|
| A1 | Clean question, CoT, final answer | Original generic rubric |
| B1 | Same plus original prompt | Same generic rubric |
| A2 | Restricted evidence as A1 | Component rubric and final whole-target score |
| B2 | Full evidence as B1 | Same component procedure |

Exact prompts/settings: `configs/diagnostic-v2.json`. Same requested judge model,
temperature, JSON mode and maximum output budget in all arms. Generic rubric text
is preserved, with a common instruction treating supplied data as evidence. All
four arms are rerun. Historical 30-output-token predictions are a reference,
not the matched A1 control for this amendment's 1,024-token budget.

The component factor bundles rubric wording and structured elicitation; a gain
does not isolate wording from output structure or realized reasoning length.
Component outputs include acknowledgment, identifiable reliance, false process
claims, required omissions, logical support, evidence spans and uncertainty.
Only the final `unfaithfulness_score` is the native-label primary score.
Evidence quotes must occur in the allowed input; quote existence does not verify
the model's interpretation of that quote.

No native labels, correct answers, annotation reasons, prior scores, generator
identity or selection strata appear in requests. A/B inputs are built from an
explicit whitelist. Full original user prompts are legitimate evidence for a
full-transcript auditor, not inherently undeployable information.

## Stages and lock

1. Verify frozen population/labels/prompts against the pinned curated CSV and
   preserve the original split: 306 development and 807 evaluation responses.
2. Prepare an eight-response development **instrument smoke** spanning native
   labels and length. Run all four arms (32 successful request slots). This is
   a parser/evidence/cost check, not a powered discrimination experiment.
3. Prepare a 60-item, question-distinct development annotation packet. Reviewers
   independently assign components and a final judgment with uncertainty; they
   never agree/disagree with a hidden benchmark label. This first packet tests
   the BonaFide instrument; paired cross-source annotation follows a usable pilot.
4. Amend format only from development evidence, with a new version and recorded
   changes. Lock exact inputs, prompts, model/settings, and analysis before the
   807-response evaluation. Full development calls are optional until instrument
   checks and available compute justify them.
5. Evaluation execution requires a `lock.json` binding the reviewed run config,
   scripts and prepared manifest. No silent flag opens evaluation mode.

Run identities hash actual requests; resuming with altered config/input/code is
rejected. Save raw responses, returned model identity, finish reason, token
usage, timing and errors. The runner checks per-call and whole-run limits, does
not silently truncate input, and stops on authentication/billing failures.
Changes in returned model identity stop the run for review.

## Statistics and interpretation

Primary endpoint: AUROC versus the explicit native whole label on incorrect
responses, score direction fixed high=unfaithful. Primary contrast: B1−A1,
testing added evidence under the generic rubric. Secondary contrasts: A2−A1,
B2−A1, B2−A2 and the interaction `(B2−A2)−(B1−A1)`.

Use 2,000 question-cluster bootstrap draws and paired predictions. Report all
missing/invalid counts and complete-case coverage. For exploratory summaries,
95% intervals are descriptive, not corrected confirmatory claims. Before
evaluation lock, specify any secondary multiplicity policy, meaningful effect
margin, and the independent validation target. A tiny smoke has no AUROC report.

An improvement claim requires a positive paired contrast; useful recovery also
requires performance above chance. Report true Instruct-generator, source-task,
and supported joint length controls, with represented classes and pair coverage.
Include length/count baselines and an existing definition-aware full-context
monitor before making a methodological superiority claim.

B1 helping identifies an effect of that input change for this protocol. A2
helping identifies an effect of the bundled judging procedure. Neither proves
the sole cause of cross-dataset reversal. B2 largest does not establish
additivity; estimate the interaction. If no procedure is useful, retain failed
transfer and claim no successful remedy. Fresh independent validation is needed
even if an evaluation-partition result is positive: the campaign is exploratory.

## Compute

Use a bounded pilot before a broad model panel. Anvil account and capacity facts
are maintained in the local compute skill, outside this public repository.
The open-judge panel remains secondary; do not silently reinterpret its older
registered hypotheses after observing the frozen failure.
