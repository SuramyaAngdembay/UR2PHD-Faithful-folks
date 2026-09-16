# Current direction and the role of the reviewer packet

September 16, 2026. This assessment addresses the completed controlled verification
run, its note-position follow-up, and whether human review is necessary or causally
informative. No new inference or human adjudication was performed.

**Decision:** the bounded experimental direction is useful. Treat it as testing
evidence interpretation by a judge. A successful native faithfulness detector and
a causal explanation of the generator's reasoning remain unestablished. The full
reviewer packet is not a prerequisite for continuing controlled experiments.
The 40-item subset is an annotation feasibility exercise, not a gate on the whole
research program and not a source of causal ground truth.

## What the latest runs establish

The 576-call v1 experiment and 144-call v1.3 experiment are complete. I verified
unique request/API IDs, exact request-plan order, completion/output hashes, raw
parsing, and equality of the current analysis-code hashes to the pre-inference
checklists. Every saved record-level endpoint recomputes under the frozen rules.
This validates the computation conditional on the authored labels and matching
rule; it does not independently validate those assumptions. Verification is saved
in `notes/2026-09-16-direction-audit-validation.json`.

The useful v1 findings are improved claim-type/status coding on constructed
examples and more consistent judgments. Restricted attribution-status accuracy
is .931 versus .611; execution-claim status accuracy is 1.000 versus .806 restricted
and .944 full. Claim-made accuracy improves by .194 restricted and .111 full, with
the reported nominal paired intervals excluding zero. These are small authored
sets with 12 pairs per family, not native-data validation.

The primary unsupported-accusation endpoint provides much weaker evidence:
restricted attribution accusations fall from 11 to 5 among 72 calls per procedure,
with a paired item-level difference of −.083 [−.250, .000]. The conditional
accusation-level rate is 1 for both procedures in that condition. Neither procedure
makes a target accusation in the verification-language family, so the intended
native fabricated-verification failure is not reproduced there.

Under full evidence, both procedures detect 18/36 absent-source attributions.
The verification procedure returns 17 unresolved and **one supported**; generic
returns five unresolved, four supported and nine not surfaced. The prose claim
that verification "never endorses a false attribution" is therefore incorrect
even under the experiment's own authored labels. No better detection is shown.

The v1.3 intervention was a good next experiment: it tests a proposed explanation
directly and preserves its failure. Verification detection is 17/36 before versus
19/36 after, difference +.056 [.000, .139], sign-test p=.50. Generic is 12/36 versus
19/36, difference +.194 [.028, .417], sign-test p=.125. The strong predicted
verification-position pattern did not materialize. This does **not** prove zero
position effect or determinism: two verification pairs change counts and the
interval permits a modest effect. Matching aggregate counts across days is
repeatability evidence, not a mathematical property of the model.

The note-style explanation is post hoc. It should remain a hypothesis, not become
"detection is content-dependent" as an established mechanism. Whether the absent
note is procedural text may affect how a judge identifies the cited source; this
requires a within-pair manipulation and an explicit source-identity definition.
Do not revise labels selectively because particular examples were missed.

## Additional interpretation limits

**Claim codes and semantic readings differ.** Some generic outputs tagged as
`execution` explicitly describe the trace as *suggesting* a check. For instance,
the `ver-09-Pr` output says the trace suggests substituting the solution back into
the original equation but assigns `claim_type: execution`. This violates the
intended type convention, but does not itself demonstrate that the judge believed
the check happened. Other examples do assert completed execution incorrectly.
The entire 11/36 type-error count should not be narrated as eleven established
instances of reading "I should" as "I did". Shared schema alone also does not mean
the procedures receive equally explicit type definitions; the candidate explains
the intention/execution distinction while the generic rubric does not.

**"Calibration" needs qualification.** The experiment measures categorical
support decisions, unresolved use, scores and repeat agreement. It does not test
whether numeric scores are calibrated probabilities. Describe the supported gain
as better handling of insufficient evidence or improved agreement with the
specified claim/status labels. The candidate explicitly tells the judge to base
scores only on contradicted claims; unknown claims do not raise its score. Such a
score measures detected, evidence-supported violations and is not automatically
a probability that the entire trace is faithful or unfaithful.

**BonaFide is not merely a hint-use label.** Claude's session description that its
labels say whether a model used the hint collapses the project's established
distinctions. Acknowledged reliance can be faithful; native whole-trace labels
also concern misrepresented process/source claims. This matters when deciding
which existing labels can support a native follow-up.

## Reviewing a judge is legitimate, but answers a narrower question

There is no statistical prohibition on evaluating an evaluator. A reviewer can
check a judge's factual allegation against a supplied record, just as one can
evaluate a classifier against a reference label. For example, whether a prompt
contains the professor attribution is an observable property of that prompt. It
does not require knowing the generator's internal computation.

The review becomes circular if the judge's own verdict defines the reference or
if annotators simply endorse its persuasive explanation. Anchor judgments in
the original evidence, separate source presence from claim truth, and retain
unresolved cases. For a stronger reference set, have annotators identify claims
and evidence status before showing the judge's assessment, then compare it.

Three different targets must remain separate:

| Target | Suitable evidence | What the current packet provides |
|---|---|---|
| Does a judge's accusation follow from the visible record? | Defined source/claim criteria and independently checked references | Potential annotations of this narrower target |
| How accurately does a procedure detect violations, including missed ones? | Common reference cases/claims selected independently of its accusations | Insufficient by itself: current questions audit emitted assessments |
| Did the generator's CoT reflect or causally mediate its answer computation? | Generator-side interventions or suitable execution records, with explicit assumptions | No identification of that causal quantity |

An intervention on what the **judge** sees can estimate an effect on judge outputs
for the constructed cases. It does not identify the effect of the original
**generator's** reasoning on its answer. Generator-side CoT perturbation and
continuation experiments address a different question; even those interventions
need a defined estimand and do not automatically recover the original hidden
computation. See [Lanham et al., Measuring Faithfulness in Chain-of-Thought
Reasoning](https://arxiv.org/abs/2307.13702) for an intervention-based precedent.

## What the 40-item subset can and cannot support

I checked the selector and packet: it contains 40 accusation-bearing assessments
from 40 distinct responses but **32 distinct source questions**, split 20 per
evidence condition. These are outputs from the earlier component pilot, not the
new v1 verification procedure. No completed human annotation files were found.

The subset can test whether reviewers understand the instructions consistently
and reveal ambiguity in the annotation questions. It does not estimate a general
native false-accusation rate without accounting for its selection rule. In
particular, it samples response then qualitative assessment within evidence arm,
not every emitted accusation or API call with equal probability. The two arms
also use different responses and are not a matched causal comparison.

It can at most inform something like "warranted assessments among the selected
accusation-bearing assessments." It cannot measure missed violations because
the selection excludes cases without accusations. The full 392-assessment packet
contains such cases, but its questions still judge the model's assessment rather
than independently enumerate every violation. A detector evaluation needs that
additional reference construction. Group uncertainty by source question; forty
responses are not forty independent questions.

Humans are not guaranteed to make errors independent of the judge, one another,
or the authors' preferred explanation. Separate annotation is useful but does not
establish statistical error independence. Cohen's kappa measures agreement under
its chance model, not truth or causal validity. Category prevalence and ambiguity
matter; neither a high kappa nor a low kappa alone should decide the project.
[Artstein and Poesio's agreement survey](https://aclanthology.org/J08-4004.pdf),
especially §2.1, explicitly distinguishes agreement/reliability from validity.
Report raw agreement, category counts, unresolved rates, uncertainty and concrete
disagreements together. The current agreement script reports point estimates and
confusion counts, not uncertainty or a proof that the labeling construct is valid.

Thus the earlier suggestion that the packet is the "only source of adjudicated
real violations" overstates its role. Credible reference evidence is needed for
claims about native accusation validity, but it need not be all 392 items, this
particular form, or exclusively a second model's opinion. Existing suitable
annotations, explicit source facts, verified execution records and constructed
controls serve different reference needs. None should be silently substituted
for causal ground truth.

## Recommended direction

1. **Keep the main experimental question bounded:** does explicit verification
   improve source/process claim assessment under defined evidence conditions?
   Do not market this as recovered causal CoT faithfulness.
2. **Park full packet completion.** The 40-item exercise is optional annotation
   development. It should not block independent controls or become the main
   deliverable the user must finish before research resumes.
3. **Clarify the source predicate before further interpretation.** Test explicitly
   bounded attributions such as "the supplied snippet states X," with true,
   false and evidence-withheld cases. If testing note style, manipulate it within
   each question while preserving that predicate and its answer. Retain the
   distinct unresolved endpoint for unobserved execution. This is the useful
   version of v1.4; freeze it before inference and keep it small.
4. **Require sensitivity as well as restraint.** Evaluate true violations,
   nonviolations and insufficient-evidence cases on common examples. Fewer
   accusations or lower scores alone cannot establish a better method. Use
   fresh question/template families and another judge family before generalizing.
5. **For native transfer, create a small common reference independently of the
   procedures' emitted accusations.** Annotate observable claims/status first,
   then compare both procedures on the same records. Evaluate native whole labels
   separately. Human review can be confined to semantic cases that need it.
6. **Only add a generator-causality experiment if that is a desired paper claim.**
   Predefine the intervention and outcome (e.g., answer changes after a controlled
   CoT edit with matched continuations). It is a distinct research axis and must
   not be represented as a conclusion of a judge audit.

The next work need not wait for another permission round. Existing authorization
covers bounded controls. This assessment itself only inspects cached evidence and
records the narrowed interpretation; it does not claim new experimental outcomes.
