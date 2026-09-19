# Methodology opportunities and competitive baselines

Date: September 19, 2026. Literature and design assessment; no new inference,
training, result recomputation, or manuscript changes in this assessment.

## Judgment

A method motivated by correctness-conditioned failures is a reasonable research
direction. Existing evidence does not establish two distinct mechanisms, a
successful remedy, or that our current judges represent the best available
detectors. The strongest opening is a deployable detector that improves
faithfulness discrimination within incorrect answers, preserves performance on
correct answers, and transfers under a fixed, explicitly stated reference
standard. This can be motivated by the two-regime audit without requiring a
universal two-regime law.

The previously corrected selector comparison did not establish an advantage for
the proposed composition-aware selector. Do not present that selector or the
AUROC decomposition as an already validated method.

## Relevant published competitors

These are important competitors found in the primary literature, not a verified
exhaustive leaderboard. Their reported numbers are not directly comparable to
each other or to our AUROCs.

- **CIE-Scorer:** [paper](https://arxiv.org/pdf/2605.25603),
  [public repository](https://github.com/se7esx/CIE-Scorer). Table 1 reports
  accuracy/F1 (%) of 69.0/60.8 on LogicQA, 78.0/71.5 on TruthfulQA, 77.0/72.8 on
  AQuA, and 78.0/79.7 on HLE-Bio. The implementation uses circuits/transcoders
  matched to the Llama-3.1-8B-Instruct generator, GNN circuit representations,
  internal/external graph discrepancy, supervised margin training, and a
  validation threshold. These are not AUROCs on our full four-generator cohort.
  Section 4.4 already distinguishes post-hoc and spurious reasoning through
  associations with feature/structure discrepancy. Section 4.5 reports weaker
  transfer involving AQuA, with most relevant off-diagonal F1 transfer ratios
  below 0.5. Public source availability is not a completed reproduction audit.
- **GeoFaith:** [paper](https://arxiv.org/html/2605.26893v1). Table 1 reports
  FaithCoT-Bench F1 of 61.7, versus GPT-5 56.3 and DeepSeek-V3.2 59.1 under its
  protocol. It bootstraps step annotations using geometric and entropy signals
  and trains a detector. Its higher in-domain step-level results are different
  endpoints and must not be described as FaithCoT performance. A usable official
  checkpoint/reproduction path has not been established in this assessment.

Our manuscript reports judge AUROC .830 on correct and .679 on incorrect
answers on the full labeled population. This is evidence of a gap for that
tested procedure, not the current best achievable incorrect-regime score.
The nonperfect published scores and transfer weaknesses justify investigating
headroom; they do not identify how much error is reducible given the evidence
available to a detector and ambiguity of the reference labels.

Before claiming a state-of-the-art result, align response population, label field,
generator, train/test provenance, evidence access, and metric. Report the original
accuracy/F1 endpoints as well as our stratified AUROCs, with thresholds selected
on development data. Compare white-box and text-only procedures in explicit access
settings. A win on one correctness stratum must be named as such.

## Preferred first hypothesis: training on correctness-matched comparisons

Train one faithfulness detector using all four combinations of reference
faithfulness and answer correctness. In addition to a pointwise faithfulness
loss, train it to rank unfaithful above faithful responses **within the same
correctness group**. Match task, generator, and overlapping length where sample
support permits. These matches reduce specific shortcuts; they do not create
causal identification or guarantee removal of every confounder.

A candidate objective is a pointwise loss plus a weighted within-regime ranking
loss. Start with an average of the two ranking losses; test worst-regime weighting
only with suitable regularization and adequate support. Select hyperparameters
inside training/development partitions. Group all traces from the same question
together in splits, including synthetic variants.

Why this addresses the finding: a detector that only estimates correctness gives
equal scores to responses in the same correctness group and cannot solve their
faithful/unfaithful ranking problem. The training signal therefore explicitly
rewards discrimination that correctness alone cannot provide. This does not
prove the detector will find that signal or generalize.

Gold correctness is used for training groups and retrospective evaluation, not
provided to the detector or a router at test time. Do not force unconditional
score independence from correctness: a real population association can exist.
Pure within-group ranking leaves cross-group score offsets underdetermined;
retain pointwise supervision and evaluate calibration separately. Improving
both within-regime AUROCs alone does not guarantee improved pooled AUROC because
cross-regime positive-negative comparisons also contribute.

Balanced training, pairwise ranking, and worst-group objectives are established
ideas. [Group DRO](https://arxiv.org/abs/1911.08731) is a necessary conceptual and
experimental baseline, not a new name for our method. Its results also warn that
regularization matters for worst-group generalization. A method contribution
would require a useful task-specific training/data construction and convincing
gains beyond simple balancing and robust training, not merely this loss formula.

Training data quality is load-bearing. A wrong answer is not an unfaithfulness
label, and a correct answer is not a faithfulness label. Instructing a model to
rationalize, or editing an answer, does not by itself certify its internal causal
process. Our failed constructed-to-annotated transfer remains an explicit reason
to test both construction artifacts and natural-example transfer. Current small
annotated samples may support feasibility experiments but not reliable training
of a complex architecture from scratch.

## Other hypotheses, in priority order

1. **Complementary evidence:** compare a text judge, permitted representation
   features, and their combination using genuinely out-of-fold features and
   matched training budgets. A hybrid is justified only if it improves the hard
   regime beyond its stronger component. Re-encoding a completed trace must not
   be called access to original generation states. CIE-Scorer already occupies
   internal/external comparison, so a generic hybrid is not a novelty claim.
2. **Two experts with a learned router:** first test whether separately trained
   regime experts offer any diagnostic advantage using held-out gold routing.
   That routing is an oracle diagnostic, not a deployable result or a formal
   upper bound. If promising, compare a cross-fitted predicted-correctness router
   against a single capacity-matched model and random/shuffled groups. A gate
   that requires the gold answer at deployment is unsuitable for the intended
   setting. Different conditional AUROCs alone do not justify two experts.
3. **Additional evidence and abstention:** potentially useful where source or
   execution evidence is unavailable, with coverage/error/cost endpoints. This
   follows the evidence-access work more directly than the correctness regimes.
   Existing authored-control gains do not establish a native detector remedy.

## Bounded next campaign and decisions

1. **Establish matched baselines.** Inventory usable scores and released models;
   reproduce CIE-Scorer on the supported generator and test GeoFaith if artifacts
   permit. Include a current strong judge, a simple supervised text classifier,
   length, and correctness as an explicitly nondeployable oracle diagnostic.
   Record unavailable competitors rather than substituting guessed numbers.
   Freeze label fields and report binary/four-way disagreement sensitivities.
2. **Test the training hypothesis cheaply.** On question-grouped development
   splits, compare the same encoder/features under ordinary supervised training,
   four-cell balancing, group DRO, and correctness-matched pair training. Use
   nested selection, regularization, matched capacity, and repeated seeds. Test
   hybrid features only if they add held-out information. Do not expand to a
   broad architecture sweep before this comparison has a signal.
3. **Stress the explanation.** Compare within task/generator and overlapping
   lengths; report retained support. Report both within-regime and all four
   positive-negative correctness-pair cells. Evaluate predetermined mixture
   changes rather than choosing a mixture where the method looks best.
4. **Confirm on independent data.** Freeze the procedure, then test fresh
   questions/generators with both labels represented in both correctness groups
   under a common annotation definition. Existing BonaFide has no usable
   correct-answer stratum and has already informed development; GRACE addresses
   a different reference standard. Neither is automatically a clean two-regime
   confirmation. Use separate native-label transfer analyses where appropriate.

Primary success would be a paired, practically meaningful improvement in
incorrect-answer detection over the strongest access-matched baseline, without
material correct-regime harm, that survives independent transfer and simple
shortcut controls. Predeclare both the target improvement and tolerable harm,
then size the evaluation using question clusters and four-cell counts. Also
evaluate false accusations against faithful mistakes at a development-selected
threshold; do not conflate AUROC with operational precision or calibration.

Stop or redirect the method branch if gains are limited to pooled scores,
disappear against balancing/group DRO, depend on gold routing, or fail fresh
transfer. Such outcomes can strengthen the empirical paper but do not establish
a new corrective method. More compute alone does not solve label definition,
sample support, or unavailable evidence.
