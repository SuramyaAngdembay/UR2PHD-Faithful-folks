# Research roadmap after the completed diagnostic campaign

This is a proposed research design, not a record of newly launched jobs. All
four preceding API runs completed (226 calls). Removing compute constraints in
this plan does not establish availability or scope of a particular allocation.
The sample sizes below are planning scales; finalize precision and power through
question-cluster simulations before locking an evaluation.

## Current scientific position

The empirical backbone remains the FaithCoT audit and failed frozen BonaFide
transport test. Correctness-conditioned performance and released-score inversion
survive on FaithCoT. BonaFide does not replicate correctness entanglement: its
whole-label population is almost entirely incorrect already. Its class/task/
generator composition weakens the interpretation of strong pooled features.

The strict saved generator/task/word-bin audit gives primary judge .193, steps
.521, NLI count .603, and 1.40% pair support. These are restricted comparisons,
not a causal decomposition. SimpleQA-only step count remains .806. Neither
"task composition explains everything" nor "nothing works" is supported.

The six matched native pairs favor the restricted component procedure, but
rankings are sometimes accompanied by unsupported process allegations. The
visibility-comment ablation improved discovery cases without demonstrating the
predicted reduction on twelve fresh questions. Identical-input instability was
observed. Neither a generic context repair nor a validated method is established.

Four explanations remain separable research targets: population composition,
reference-label differences, missing decisive evidence, and errors interpreting
available evidence. More scoring alone cannot identify all four.

## A. Replicate the fixed judging comparison

First repeat fixed procedures on a prespecified development sample spanning
labels, generators, source tasks, and reference reasons. Include randomly
selected cases as well as separately reported diagnostic cases. Five actual
calls per condition is a useful initial repeat design; do not select repeats
or aggregate policies from favorable outcomes.

Then freeze the 2x2 (generic/component procedure crossed with restricted/full
original prompt), corrected definition-aware comparator, primary contrast,
secondary multiplicity policy, treatment of invalid outputs, and analysis.
The existing primary comparison is B1 minus A1; amendments must be explicit.

Run all 807 reserved responses, with three judge families and three repeats per
arm as a concrete initial scale: 807 x 4 x 3 x 3 = 29,052 calls, before baseline
calls. Preserve the exact historical GPT-4o anchor. Choose other model snapshots
for family/capability diversity, and keep each model's results separate.

Report single-call expected performance and the separately specified repeated-
call aggregation; question-cluster uncertainty, invalid/abstention coverage,
native AUROC, supported conditional comparisons, and per-question stability.
Three calls are repeated measurements, not three independent examples.

The 807 split is reserved from this new instrument, not an untouched scientific
holdout: older full-population outcomes already informed hypotheses. A new
external sample remains necessary for a strong generalization claim. Small
faithful support in some cells cannot be repaired by more judge calls.

## B. Apply both reference procedures to common examples

Start with roughly 400 question-distinct examples, 200 from each source, sampled
to expose both agreement and failure while retaining sampling weights and a
representative component. For each example use the same permitted evidence
under both rubrics; record unavailable evidence explicitly.

Use two independent trained human reviewers per rubric, followed by adjudication
without forcing a binary label where evidence is insufficient. Blind native
labels, prior judge outputs, and annotation reasons. Counterbalance assignment
to prevent memory of another rubric's judgment. Models can assist triage, but
their votes do not replace independent human validation.

Label shared components separately: disclosed reliance, supported source claim,
contradicted source/execution claim, logical correctness, completeness where a
reference exists, and evidence sufficiency. Retain each rubric's own whole-label
rule. Applying instructions to new data is an adaptation, not reconstruction of
the original annotation event or unavailable generating computation.

Measure rubric disagreement, within-rubric reliability, insufficient-evidence
coverage, and agreement with independently checkable records. Human agreement
alone does not certify internal process truth. This study distinguishes a target
difference from a detector's failure to predict the same target.

## C. Build a fresh corpus that supplies missing comparison cells

Prioritize tasks with retained sources, executable arithmetic/code, and complete
tool-call records. Generate responses to the same questions across multiple
model families. Randomize cue/source/tool conditions; include cue-absent and
honest-error controls. Keep all attempts and certification failures.

Seek both correct and incorrect outcomes with supported and contradicted claims
within task/generator cells. Do not force whole-faithfulness labels to fill a
table. Maintain a natural-prevalence cohort and a separately selected challenge
set. Challenge-set balance does not estimate deployment prevalence.

A planning scale is 600 questions across three evidence types, four generators,
four randomized conditions and three samples: 28,800 generated trajectories.
The independent units remain questions, and sample sizes may need adjustment
when particular outcomes are rare. Reserve entire task templates and generator
families; do not rely solely on random response splits.

Test answer correctness separately from claim truth: a correct answer with a
fabricated tool claim; an incorrect answer honestly reporting a real tool result;
disclosed reliance without a false source claim; a fluent unsupported attribution.
Label only what records establish. An empty complete tool log can contradict
"I ran this tool"; it cannot establish that no mental arithmetic occurred.

Keep naturally generated records separate from edited challenge traces. For
hint-dependence studies, repeated randomized conditions estimate behavioral
effects; a single answer flip is not a deterministic latent process label.

## D. Isolate evidence access, presentation, and elicitation

On the new corpus, compare restricted trace evidence, full original prompt, and
full prompt plus decisive source/execution record. Each evidence package is
identical across judging procedures. Missing evidence should permit uncertainty.

Pair relevant evidence with equally long irrelevant-context controls to separate
evidence benefit from context burden. Randomize placement and truthful role
labels without changing the underlying record. Retain omitted-evidence tests.

Unbundle the component procedure: generic instructions with matched structured
output; component instructions without compulsory explanation; and the complete
procedure. Match requested output budgets and report realized tokens. Compare
cost/performance at specified budgets rather than attributing a bundle effect
to decomposition alone.

These interventions can show whether the limiting factor is evidence access,
reader interpretation, or elicitation under the tested conditions. They do not
identify the sole cause of the historical cross-dataset difference.

## E. Develop a verifier only after independent labels exist

Candidate procedure: identify a checkable claim, locate admissible records,
classify supported/contradicted/insufficient, then apply a declared aggregation
rule. No verified contradiction is not proof of complete faithfulness.

Compare against generic and definition-aware judges given the same records,
simple features, and direct tool/source checking. If retrieval is part of the
method, evaluate retrieval separately and include a baseline with the same
retrieved evidence. Measure contradiction precision/recall, false allegations,
localization, calibration, and risk versus coverage, alongside native labels.

Train or tune on one source and test on the other using both native targets and
independently validated shared components. Report A-to-A, A-to-B, B-to-A, and
B-to-B; reserve a fresh third environment. Name any target-label adaptation.

## Decision rules for the paper

- Stable component improvement with independently correct allegations supports
  developing and validating a narrowly defined verifier.
- Native totals fail to transfer while shared components transfer supports a
  reference-standard/aggregation contribution.
- Decisive evidence helps while prompts alone do not supports a measured
  evidence requirement, with uncertainty and coverage central.
- Effects disappear with repeated or matched evaluation supports a focused
  measurement/selection audit, not a forced methodology contribution.

The original step-removal result also permits a separate causal project on
answer re-solving versus use of supplied steps, using original generation
records and controlled interventions. Do not add a large mechanistic branch to
this paper before the common-target diagnostic clarifies its central question.

## Related-work boundary

BonaFide already studies failures and transfer of faithfulness metrics:
https://arxiv.org/abs/2605.25052 . C2-Faith already separates logical step
consistency and coverage and tests detection versus localization:
https://arxiv.org/abs/2603.05167 . Logical consistency in that operationalization
is different from causal dependence of the generator on its trace. Monitorability
work already evaluates intervention, process, and outcome-property targets:
https://openai.com/index/evaluating-chain-of-thought-monitorability/ .

Our potential contribution must go beyond a component rubric or another judge
leaderboard: isolate a transfer failure, validate which claims are knowable,
and show a useful correction under genuinely fresh conditions if one exists.
