# Independent audit of the stratified-evaluation novelty sweep

Date: September 19, 2026. This assessment supersedes conflicting interpretations
in `2026-09-19-stratified-eval-precedent.md` and its historical commit messages.
The older note remains preserved. The verdict-driving primary sources and
release calculations were checked; this is not certification of every reference
in the long pasted search transcript.

## Verdict

The proposed published-detector reanalysis is useful empirical work. The general
statistics are established, so it is not a new AUROC decomposition or a newly
invented stratification method. This does not eliminate the value of discovering
a consequential failure in a particular benchmark. A correctness-conditioned
ranking reversal remains a hypothesis for the published eleven detectors until
their outputs are obtained or the evaluations are reproduced.

The sweep contains several important errors: an unsupported claim about
correctness constituting faithfulness; a reversed description of BonaFide's
correctness support; comparisons of an oracle AUROC with published F1; an
incomplete reading of F1 collapsibility; and overinterpretation of a selected
1,198-response census. Do not use those claims to redesign the paper.

## Primary-source findings

- [Kallus and Zhou, 2019](https://arxiv.org/html/1902.05826), Proposition 1,
  explicitly decomposes aggregate AUC into within- and cross-group terms with
  class-conditional group weights. This is direct relevant prior art. Cite it;
  do not claim the identity as new. This does not prove ownership of the earliest
  historical derivation or preempt a specific CoT benchmark result.
- [Matos et al., 2026](https://arxiv.org/html/2608.30568v1), Table 1 and Appendix
  A.1.9, explicitly gives a positive-class F1 decomposition with model-dependent
  weights. Its AUC discussion does not establish the sweep's proposed
  cross-metric diagnostic rule. Collapsibility is not invariance to prevalence
  or a guarantee of detector-ranking stability.
- [FaithCoT-Bench v2](https://arxiv.org/html/2510.04040v2), Section 4.2 and
  Tables 1-3, reports the headline judge advantage using F1. AUC from step-removal
  is a different quantity from detection AUROC. Its Appendix B.1 reports
  association on 1,183 examples; a different release/subset cannot directly
  correct that number. Its table already contains domain-specific exceptions to
  the broad judge-superiority wording. Those exceptions are not a demonstrated
  correctness-stratified reversal or explanation of the headline advantage.
- [BonaFide](https://arxiv.org/html/2605.25052v1), Sections 3.2 and 4.1,
  filters diversionary examples for following an incorrect hint, not for giving
  the correct answer. Our frozen whole-label population is 1,113 incorrect
  responses plus seven correct responses, all seven unfaithful. The statement
  that BonaFide lives entirely in the correct-answer regime is false.
- [Deviyani and Diaz, 2025](https://arxiv.org/abs/2503.19828) and
  [Stowe and Patil, 2026](https://arxiv.org/abs/2604.16607) are relevant adjacent
  work on context-sensitive metric effectiveness and detector rankings. Neither
  abstract certifies an exhaustive novelty verdict for our exact experiment.

## Executed release audit

The latest GitHub commit changing `faithcot.zip` was checked read-only through
the repository API: `5112797173f3ff7573f030bca28411a596fd52e8`. The pinned remote
archive and our existing local archive have identical SHA256:
`9ef674e33cae2654b2fe00ee2a00610f595eedb4ae649c4ed6a277b4a7eb6eba`.

The archive has 1,364 response JSONs, 1,304 binary-labeled responses, and 1,303
responses with valid four-way types. One binary-labeled response has type 0.
Stored soft/hard step-removal scores occur on 682 responses. No aligned set of
all eleven detector prediction vectors was found in these response records.
The existence of `faithful_score` annotation fields must not be mistaken for
the missing eleven-method prediction release.

The pasted 1,198-response calculation is reproducible, but it excludes every
missing parsed answer, keeps the invalid-type record, and defines correctness
using normalized exact answer strings. Of the 106 excluded labeled responses,
80 are type 1 (faithful incorrect), 25 type 2 (unfaithful incorrect), and one
type 3 (faithful correct). Most are from HLE-Bio (53) and AQuA (49). This
selection materially changes the quantity being estimated.

| Population and target | n | Incorrectness-oracle AUROC | Phi |
|---|---:|---:|---:|
| Pasted subset, binary target, exact-string correctness | 1,198 | .726489 | .436417 |
| Same subset excluding type 0, native correctness | 1,197 | .727556 | .439003 |
| All valid types, binary target, native correctness | 1,303 | .704272 | .380523 |
| All valid types, four-way-derived target and correctness | 1,303 | .696749 | .353569 |

Only five parseable valid-type records disagree between exact-string and native
correctness. The larger issue here is selection, not a demonstrated widespread
semantic answer-equivalence failure. Native categories are the established
analysis convention, not an independent re-adjudication of correctness. The
binary and four-way-derived faithfulness labels disagree on 56 valid records;
they must remain separately named targets.

These calculations neither resolve the older 1,183-example paper population
nor show that a .726 AUROC beats any detector's F1. Phi is a valid measure of
binary association; it is insufficient by itself to assess a detector comparison,
but calling it the wrong statistic categorically is unjustified.

## Statistical corrections

For binary positive-class F1 on pooled confusion counts,

`F1_pool = sum_g w_g F1_g`, where
`w_g = (2 TP_g + FP_g + FN_g) / sum_h (2 TP_h + FP_h + FN_h)`.

Thus there is a decomposition, although it is not the AUROC pair decomposition.
The weights depend on the detector. Our executable counterexample uses the same
two subgroup class populations for two detectors: A has subgroup F1 .160/.534
and B .080/.477, yet their pooled scores are .398/.413. A wins in both groups
and loses pooled. This is consistent with each detector's F1 being a weighted
average of its own subgroup values because its weights differ from B's.

At fixed TPR `t`, FPR `f`, and prevalence `pi`,
`F1(pi) = 2 pi t / [pi (1+t) + (1-pi) f]`.
The pasted .418-to-.728 toy example is arithmetically correct at prevalences
.154/.574 and sensitivity/specificity .7/.7. It illustrates prevalence
dependence; it neither proves actual benchmark inflation nor identifies
discrimination changes. F1 does not always change with prevalence, and neither
metric is universally more sensitive to every kind of composition shift.

Sensitivity and specificity .7 at one threshold do not fix a continuous-score
AUROC at .7. Our constructive check yields AUROC .49 or .91 with that same
operating point. The .7 conclusion holds if the binary predictions themselves
are used as the score. Stable AUROC plus changing F1 is compatible with
prevalence/threshold effects, but equality of one area does not imply identical
ROC curves. Divergent F1/AUROC ranking changes are not automatically causal
diagnostics or evidence against noise. Estimate direct paired uncertainty.

Association between correctness and faithfulness does not force pooled AUROC
upward. Direction also depends on the detector's score distributions. Report
the actual pair components rather than claiming a universal direction.

## Conceptual and novelty corrections

- Crossing correctness with faithfulness in a taxonomy does not establish that
  correctness constitutes the binary faithfulness construct. Faithful incorrect
  and unfaithful correct examples are explicitly allowed. Any claim of definitional
  dependence needs the actual annotation rules and evidence of their application.
- Subgroup reporting, prevalence standardization, and covariate-adjusted ROC are
  different estimands. Do not describe the Janes-Pepe construction as the only
  formal interpretation of stratification. Choose the evaluation population and
  operational objective explicitly; observed heterogeneity alone does not make
  the original pooled estimate biased for its own population.
- Extending this same manuscript from its arXiv preprint is not, by itself,
  self-plagiarism or loss of our contribution. The relevant issue is external
  prior art and accurately identifying what the new revision adds. ARR explicitly
  accommodates preprints in its [author guidelines](https://aclrollingreview.org/authors).
- A finite search supports “no direct external study found,” not “nobody has
  done this.” The mathematical identity is old; an important new empirical
  application can still be publishable without a new statistical theorem.
- The absent probability fields on closed-model examples do not show all
  step-removal methods require model weights. The paper itself reports
  closed-model Removing Steps results. Access requirements depend on whether
  the protocol uses probabilities, sampled answers, or internal activations.

## Correct next experiment and relationship to a new detector

Keep the proposed published-detector audit as a bounded first stage:

1. Pin the original evaluation response IDs, annotation revision, positive class,
   F1 averaging convention, thresholds, and domain/model aggregation. Obtain
   released predictions where possible; otherwise name a rerun as a rerun. The
   current archive does not supply the full prediction matrix. No author message
   was sent during this audit.
2. Reproduce the published F1 comparison before attributing its reported lead to
   composition. Add ROC/AUROC only when proper continuous scores are available;
   label hard-prediction AUC separately. Report TPR/FPR and confusion matrices.
3. Evaluate within correctness groups on common examples. Keep original
   thresholds for primary F1, and estimate F1 at a shared prespecified prevalence
   using each group's operating characteristics. Use question-clustered paired
   uncertainty and control the scope of multiple ranking comparisons.
4. Report all four correctness-conditioned positive-negative pair terms for
   AUROC. Separately vary declared group mixtures while holding conditional
   behavior fixed. Do not conflate observed conditional differences with a causal
   effect of correctness.
5. Include modern competitors where feasible, with explicit evidence-access
   constraints. A reanalysis of eleven historical methods is not a current-SOTA
   evaluation by itself. If a substantive wrong-answer gap persists, test the
   correctness-matched training proposal from the earlier methodology note.

The worthwhile outcome is learning which detector conclusions survive these
choices and whether there is a reproducible deficiency worth fixing. A reversal
is not guaranteed and must not be a success condition that drives selective
reporting. This audit can strengthen an empirical paper; it becomes support for
a new detector only after a separate method demonstrably improves performance.

## Reproduction and completion

Script: `scripts/audit_stratified_novelty_claims.py`.
Outputs: `results/stratified_novelty_audit/2026-09-19/results.json` and manifest.
Run with the pinned archive and `--output-dir` pointing to a new directory.
The script checks the archive hash, refuses overwrites, preserves label-field
distinctions, and verifies the F1 identity/reversal example by assertions.
No model inference, independent annotation, manuscript revision, or external
communication occurred.
