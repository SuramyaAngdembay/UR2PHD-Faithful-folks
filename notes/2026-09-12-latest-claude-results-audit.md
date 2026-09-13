# Audit of the latest GRACE and BonaFide results

Reviewed commits `6af00b5`, `79d3ab6`, and `0080a89` against saved predictions,
the pinned GRACE release, and current BonaFide metric code. The reconciliation
preserves a useful negative result after a paired correction. The full GRACE
correctness-stratified conclusions are invalidated by an answer-parsing bug.
Historical artifacts remain intact; the interpretations below supersede them.

**GRACE correctness is incorrectly computed on free-response tasks.** Both
`scripts/grace_regime_test.py` and `scripts/grace_regime_analysis.py` apply
`letter()` to every answer. Outside a leading multiple-choice pattern, it returns
the first character. The release contains 220 multiple-choice traces and 217
free-response traces. This does not mean all 217 labels are wrong, but the
procedure used to derive their correctness is invalid.

| Trace ID | Reference answer | Model answer incorrectly marked correct |
|---|---|---|
| `grace_test_musique_e13f9668` | Juan Manuel Santos | John F. Kennedy |
| `grace_test_musique_138f30b3` | 2015 | 2010 |
| `grace_test_musique_875ff9b4` | October 28, 2012 | October 29, 2012 |

Conversely, correct answers can begin with introductory words or Markdown and
be classified as incorrect. Substring matching is not a sufficient repair: some
responses mention a reference answer while explicitly denying it.

The full-set correctness-stratified correlations, differences, binary regimes,
and correctness-entanglement lifts must be withdrawn pending repair. This
includes the +.094 regime contrast and 1.15–1.65 lift band. GRACE has not yet
supplied the claimed external entanglement replication or a valid full-set test
of the regime contrast.

Pooled correlations do not depend on correctness and reproduce: context-NLI
unsupported fraction versus annotated unfaithful fraction is .2258, and inverted
mean entailment is .2538. These remain scoped associations for the saved NLI
procedure. A diagnostic limited to 219 strictly parsed multiple-choice responses
gives NLI-rate regime difference −.120, question-bootstrap CI [−.406, .192], and
mean-entailment difference −.086 [−.382, .251]. One response answering that none
of the options is necessarily true is excluded. This exploratory subset does
not replace the corrected full analysis or demonstrate equality of regimes.

**The length claim is too broad.** Step-count AUROC .491 is correct for the
derived label "any unfaithful step." It changes to .391 at >.25, .386 at >=.5,
.416 at >.5, and .184 for all steps unfaithful. Step count correlates −.223 with
the fraction target. Thus "no length confound" is unsupported across the tested
targets. Fractions still specify an aggregation rule and equal step weighting.

The NLI pass caps context at 4,000 characters and input pairs at 512 tokens.
Its question-plus-prior-steps arm omits external passages. These are material
evidence conditions for grounding. Only NLI and surface signals have been scored;
this is not a complete external run of the original detector panel. BonaFide
lacks a usable correct-answer stratum, so it cannot count as a second completed
external test of the correctness-regime contrast.

**BonaFide arm A used a different population in the reported comparison.** The
saved files contain 284 unique A scores and 150 each for B and C, all tagged
GPT-4o. Their intersection has 150 responses from 123 question clusters, U85/F65,
143 incorrect and seven correct. Recomputing every arm on that intersection:

| Arm | Condition | AUROC | Question-bootstrap 95% interval |
|---|---|---:|---|
| A | Generic monitor prompt, original prompt/hint visible | .319 | [.229, .408] |
| B | Generic monitor prompt, hint stripped | .400 | [.309, .490] |
| C | Our rubric, original prompt/hint visible | .367 | [.269, .457] |
| D | Historical GPT-4o judge on clean question | .331 | [.241, .414] |

The original A=.352 reproduces on all 284 responses, but should not be compared
directly with the other 150-response estimates. Paired differences from 2,000
common question resamples are A−B=−.081 [−.174,.015], A−C=−.048 [−.129,.036],
C−D=+.036 [−.018,.092], and A−D=−.012 [−.104,.086]. All four point estimates
remain below chance on the 143 incorrect-only cases (.335/.419/.370/.332).

These results do not support the proposed prompt-based rescue of GPT-4o on this
pilot. They do not establish condition equivalence, that visibility necessarily
worsens detection, or that evidence access cannot matter elsewhere. The pilot
oversamples faithful responses; D is historical, not a fresh randomized repeat.

The run uses a model alias and a 700-token output limit and retains scores without
raw responses, finish reasons, request hashes, or per-response usage. Semantic
and reproducibility checks are correspondingly limited. The generic template
has whitespace differences from upstream. The fallback stripping marker also
differs, although it changes none of the 150 common inputs. Ten common inputs
are unchanged by stripping. Upstream `monitor_no_hint` inherits its definition-
aware monitor; local B is a generic-prompt ablation rather than that exact class.

**The upstream sign concern is real; the published-error claim is unconfirmed.**
At pinned revision `e5f2a87ecfe590d8aa4c73ba06cd92c39051bf87`, the base interface
documents higher scores as more faithful, while the generic parser returns
normalized suspicion through it. The CLI writes that score without a correction.
This is an interface inconsistency, but does not establish how the final
unpublished evaluation oriented scores and labels. [Base interface](https://github.com/yoavgur/BonaFide/blob/e5f2a87ecfe590d8aa4c73ba06cd92c39051bf87/metrics/base.py),
[monitor implementation](https://github.com/yoavgur/BonaFide/blob/e5f2a87ecfe590d8aa4c73ba06cd92c39051bf87/metrics/monitor/metric.py).

The paper's generic-monitor CoT result is .67 ± .04; .68 ± .02 is the step
result. The CoT complement is .33. Its proximity to our results is compatible
with a sign error, not proof: the published judge uses Gemini, the populations
differ, and the final scoring path is unavailable. These are related GPT-4o
configurations on overlapping examples, not independent replications. The
definition-aware .82 result uses a separate output path. [Published table](https://arxiv.org/html/2605.25052).

The decisive evidence is the original generic-monitor evaluation code or aligned
native-label/raw-score pairs, including positive-label and orientation choices.
A technical author clarification is appropriate; no message was sent. Until
verified, keep the code inconsistency and the published-score discrepancy
separate. Our inversion is not yet independently corroborated by their monitor.

**The reserved split has new exposure (count corrected September 13).** Across
the 284 distinct scored responses, 73 are development, 204 belong to the original
807-response evaluation partition, and seven correct-answer responses are outside
the population defining that split. The common intersection contains 39
development, 104 evaluation, and seven outside-split responses. The 204 evaluation
responses span 156 question clusters, covering 397 evaluation responses. The
earlier independent count of 211/161 incorrectly included the seven ineligible
rows; Claude correctly identified this. Preserve the split and attach
exposure flags; do not call the entire partition unexposed or attempt to restore
independence by moving examined cases between splits.

**Next work.** Validate correctness by task and answer equivalence, including
unresolved free responses, then rerun GRACE from cached NLI scores. Use the
paired reconciliation table and obtain the final upstream orientation evidence.
Amend manuscript GRACE conclusions before relying on them. The original FaithCoT
audit and frozen BonaFide inversion are not invalidated by the new parsing bug.

The independent review archive contains `recompute.py`, `audit-results.json`,
input hashes, and pinned upstream source files under
`latest-claude-audit-2026-09-12/`. No new inference was launched for this audit.
