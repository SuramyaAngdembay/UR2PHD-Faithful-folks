# Working paper structure after the September 12 diagnostics

This is a revision map, not a submission-ready manuscript or a claim that the
small development pilots constitute validated generalization. The current
`main.tex` retains historical framing and needs a coordinated rewrite.

Working title: **Evidence Access and Interpretation in Chain-of-Thought
Faithfulness Evaluation**. Keep the title provisional until the main result has
independent support. Do not preserve an unqualified universal two-regime headline.

## One central question

When does a faithfulness judgment track the intended process property, and when
does it track a different property of the evidence or reference procedure?

The paper should move from a documented cross-benchmark failure to controlled
diagnosis. Correctness-conditioned FaithCoT results motivate the question, but
do not establish two internal mechanisms. BonaFide is an external reference
standard with different support and aggregation, not proof of a contradictory
label for the same observable case.

## Proposed main-text sequence

1. **Define the target and allowed observations.** Separate answer correctness,
   logical support, source-claim truth, execution claims, reporting completeness
   and causal dependence. Whole-trace faithfulness is not equivalent to detecting
   one supported violation. Explain what original-prompt access adds and what
   it cannot supply, such as the original news article or hidden computation.
2. **Reproduce the scoped empirical failure.** Present the verified FaithCoT
   correctness-conditioned results, released-score direction and the frozen
   BonaFide transfer outcome on explicitly defined populations. Report the
   binary/four-way discrepancy and support limits. Do not imply correct-stratum
   BonaFide AUROC exists or compare unsupported cells.
3. **Show why a simple explanation is inadequate.** Original prompt access
   resolves deliberately constructed source twins, but does not automatically
   repair native discrimination. Describe the source/generator/length support
   audit. The current six matched pairs suggest that the component procedure
   and evidence policy interact; they are development evidence that needs more
   support, not the main paper's conclusive table.
4. **Identify a concrete interpretation error.** The auditor sometimes treats
   metadata described as inaccessible as actually unavailable despite its
   presence in the input and the trace's disclosure of its use. A controlled
   visibility-comment intervention with unchanged-input repeats tested that
   candidate explanation: the effect appeared in the two discovery cases but
   did not generalize to twelve fresh cases. Preserve this failure and the
   unstable repeated judgment. It is a diagnostic limit and cannot anchor a
   successful remedy claim. Evidence availability and its interpretation remain
   distinct questions requiring a broader, independently checked test.
5. **Validate a narrowly defined corrective procedure, if justified.** A source
   or execution-claim verifier should cite the relevant statement and admissible
   record, return uncertainty where the record is missing, and distinguish a
   contradiction from lack of certification. It must improve the intended target
   on independently checkable natural cases and beat matched baselines. Existing
   full-context/definition-aware prompts and simple features are mandatory
   comparisons. Structured JSON or a component rubric alone is not a new method.
6. **State the limits and practical consequence.** A monitor's score is indexed
   by target, evidence policy, reader procedure and selected population. The
   recommendation must follow tested contrasts; no general impossibility theorem
   or blanket claim that adding context helps is currently established.

## What belongs in the appendix or supporting material

- Full provenance, label fields and correction history; frozen population and
  question split; omitted or failed calls; exact prompts and model snapshot.
- The AUROC composition identity and sensitivity to the weighting of comparison
  cells, with a clear distinction from a causal mechanism.
- The historical representation and synthetic-transfer controls, including the
  attenuated matched hint result and failed selector claims. Keep this evidence
  if it rules out an apparent remedy, but it should not create a second main
  storyline about representation learning.
- Every pilot pair, small-sample uncertainty, original-repeat variation,
  metadata-comment outcomes and known instrument errors. Mark obsolete D1
  baseline results as superseded by the role-corrected D2 experiment.
- The exact-record collision audit. Its synthetic .5 ceiling is an elementary
  information-policy example, not a novel impossibility result for both datasets.

## Claims that must remain conditional

The restricted component judge ranks five of six matched native pairs correctly
and ties one, but some rationales still equate undocumented verification with a
verified false process. Ranking agreement can therefore occur for a questionable
reason. It is not enough to select the best arm and rename it a method.

The role-corrected definition-aware prompt also uses a different model/backend
from the published BonaFide monitor. Its selected pilot results do not refute
the authors' reported experiment. No pilot estimate should be presented as a
population result, particularly the batch-1 sample whose generators are disjoint
across labels.

The strongest next validation target is a particular observable claim, with a
retained source or complete execution record and an independently checked label.
Cross logical correctness with claim truth, include honest uncertainty and
disclosed reliance, and reserve fresh templates or generators for validation.
Do not derive all labels from whether a hint was acknowledged or a tool existed.

If no validated correction emerges, publish a focused measurement/transfer
audit. A successful methodology contribution requires additional evidence; it
cannot be created by organizing the same pilot results differently.
