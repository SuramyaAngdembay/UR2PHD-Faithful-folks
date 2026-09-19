# Assessment of the pasted BonaFide novelty comparison

**Verdict:** broadly correct as a comparison against one paper, but too reassuring
as a judgment of the current project's overall novelty and evidential strength.
Different experiments are not automatically a strong new contribution. The
assessment does not justify restoring a general two-regime claim.

Checked the cited [BonaFide paper](https://arxiv.org/pdf/2605.25052), especially
§2.3, §4.2, Figure 2a and §5.1, against `paper/arr/main.tex`, current project
state and the completed-run audits. Its reported metric values and generic versus
definition-informed judge comparison match the pasted assessment. The broad
metric-failure finding and distinction between importance and faithfulness are
prior work. Its definition-informed judge is explicitly presented as a skyline,
not independent evidence of a winning detector.

## Distinct experiments versus strong claims

| Project claim | Assessment |
|---|---|
| FaithCoT correctness-stratified discrimination | A concrete, scoped empirical contribution; not an established universal division of unfaithfulness into two regimes. |
| Exact correctness-mixture AUROC decomposition | Useful evaluation analysis; the identity follows from partitioning positive-negative pairs, not new statistical methodology. |
| Human-label step-removal inversion and localization | A specific empirical result; the proposed answer-reconstruction explanation remains a hypothesis. |
| Regime-specific probes and cross-regime transfer | A distinct experimental comparison; re-encoded representations and limited power do not identify separate generating mechanisms. |
| Constructed-to-annotated probe transfer | A worthwhile transportability test; failure is conditional on the tested constructions, representations, learners and populations. |
| FaithCoT/BonaFide judge reversal | An observed failure to transport the tested ranking; changing labels, tasks, generators and selection together does not isolate the label definition as its cause. |
| Component judging as a new remedy | Not established by the current results. |

The mathematical identity is

`AUROC = sum_(c,d) P(C=c | U) P(C=d | F) AUC(U_c versus F_d)`.

It shows how class-conditional correctness composition can change pooled ranking
with pairwise behavior fixed. Its research value comes from quantifying the
effect on actual detectors and the decisions an evaluator would make. It does
not explain which internal process produced a trace. A superiority claim for a
composition-aware selector also cannot be inferred from this identity; the
earlier corrected selector comparison did not establish that superiority.

The manuscript currently says the decomposition "supplies a mechanism" and that
the constructed result "confirms" the coupling account. Those phrases are
stronger than the evidence supports. Baseline-solvable and hint-flip examples
come from selected question pools; sampled flips are not controlled individual
counterfactuals. Re-encoding the completed text is also not recovery of its
original generation state. Preserve the distinction between measured score
behavior, an explanatory hypothesis and a causal identification claim.

## Current evidence the pasted assessment underweights

- BonaFide does not supply a usable correct-answer whole-label stratum for our
  two-regime comparison. Its incorrect subset challenges transfer of the
  FaithCoT detector ordering, not the existence of both regimes within BonaFide.
- GRACE's repaired NLI analysis leaves all three primary correctness-stratum
  difference intervals crossing zero. This is neither replication nor proof of
  zero difference, and correctness decisions include assistant review.
- The component-versus-generic gain repeats on two development cohorts and
  within SimpleQA, but procedure and output structure change together. In the
  newer SimpleQA sample A2 is .832 while word count is .901; their difference is
  unresolved. This is no validated general method.
- Human faithfulness annotations are a different reference standard, not direct
  observation of internal computation. An empirical finding against them must
  remain explicitly about that standard.

See the [completed replication audit](2026-09-17-completed-pilot-replication-independent-audit.md)
and [GRACE repair](2026-09-13-executed-analysis-repair.md).

The pasted phrase "3,066 labeled CoTs" also needs care for our experiments:
the audited release has 3,066 annotation rows, 2,177 response keys and 1,120
explicit whole-trace labels. Step and whole-trace entries cannot be treated as
3,066 independent binary whole-trace examples.

## Novelty must be assessed beyond this pair of papers

[Young's classifier-sensitivity study](https://arxiv.org/pdf/2603.20172) changes
classifiers on identical traces and reports different faithfulness rates and
model-ranking reversals. Those are not the same endpoints as our detector AUROCs,
but they directly limit a broad claim that measurement choices change conclusions.

[Zaman and Srivastava's causal-diagnosticity work](https://aclanthology.org/2025.emnlp-main.1496/)
already supplies controlled explanation pairs for evaluating metrics. A proposal
to hold answers fixed and change explanatory provenance needs to distinguish
itself from that design. Neither reference makes our particular experiments
redundant; neither can be omitted from an overall novelty argument.

## Recommended position

Lead with one measured failure and its consequences for evaluation: aggregate
faithfulness discrimination can conceal weak within-correctness discrimination
on FaithCoT, and promising detector/construction results need explicit validation
on the intended population and reference standard. Use the composition analysis
and transfer experiments to substantiate that argument. Keep the two-regime
pattern scoped to FaithCoT and the mechanistic account tentative.

Pairwise overlap with BonaFide is substantial for the broad narrative and smaller
for our exact experiments. Overall publication novelty remains conditional on
whether those experiments explain a consequential failure or support a validated
evaluation improvement. Rewording the contribution list alone cannot establish
either. No new experiments or manuscript edits were performed for this assessment.
