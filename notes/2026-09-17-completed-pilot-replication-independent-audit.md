# Completed pilot replication: independent audit

Experiment completed September 17, 2026, 22:14 UTC. Audit performed that evening
US Central (September 18 UTC). Audited Claude commits `fe83e3a` and `31a97ff`.

**Assessment:** a substantive exploratory result survives: the restricted
component procedure improves native-label ranking over the restricted generic
procedure on two pilot-disjoint development samples, including within SimpleQA.
This strengthens a procedure-sensitivity finding. It does not establish a general
faithfulness detector or a corrective method. Claude correctly withdrew the
unseen-data framing, but several remaining statistical interpretations need
correction. The next design should test what produces the gain while controlling
simple data shortcuts; a second judge alone will not answer that question.

## Verification and reproducibility

All 420 replication requests completed, with 19 HTTP 429 errors resolved on retry
(439 total attempts). Local and remote hashes agree for responses, attempts,
errors, run metadata and completion marker. Independently reconstructed request
IDs match the freeze, all 420 raw outputs re-parse to the saved values, the model
is pinned, and the frozen analysis hash is unchanged. The historical pilot's
840 records also pass identity/parse checks; its resumed records are matched by
request identity rather than file order.

The independent script computes AUROC through direct positive-negative pair
comparisons, separately from Claude's rank-based implementation. Primary point
estimates and all paired bootstrap intervals reproduce. The SimpleQA-only
figures reproduce too. All 70 existing regression tests pass. No new inference
was launched, and no frozen inputs, predictions or analysis were changed.

Reproduce with:

```sh
python3 scripts/audit_completed_pilot_replication.py --out <new-output-directory>
```

Outputs, input hashes and an exposure ledger are under
[`results/pilot_replication_audit/2026-09-17-completed/`](../results/pilot_replication_audit/2026-09-17-completed/).
All supplemental intervals below are nominal exploratory intervals without
multiplicity adjustment. Resampling uses questions, not individual calls or
cross-class pairs. Each calculation makes 2,000 fixed attempts and reports
undefined draws; none occurred for these reported estimates.

## What Claude achieved

| Population and endpoint | Original pilot | New sample |
|---|---:|---:|
| Pooled A1 | .218 [.107, .345] | .277 [.153, .418] |
| Pooled A2 | .511 [.320, .694] | .599 [.426, .747] |
| **Pooled A2 minus A1** | **+.293 [.093, .502]** | **+.323 [.194, .459]** |
| SimpleQA A1 | .308 [.135, .487] | .413 [.196, .613] |
| SimpleQA A2 | .631 [.382, .869] | .832 [.666, .957] |
| **SimpleQA A2 minus A1** | **+.323 [.059, .614]** | **+.418 [.238, .633]** |

The frozen directional criterion and both descriptive interval-compatibility
criteria are met. The SimpleQA sensitivity matters because it shows that the
relative improvement cannot be explained **solely** by comparisons between
different tasks. It does not remove generator, length, selection or procedural
confounds. The two procedures differ in rubric and output requirements; the gain
does not identify which difference matters.

The pooled generic score is below chance in both cohorts. The component score's
pooled interval includes chance in both. Thus the primary result supports relative
improvement, not established above-chance pooled detection. In the new SimpleQA
subset, there is nominal exploratory evidence of above-chance native-label
ranking. That result should be reported with its subgroup and development scope,
not suppressed and not promoted to confirmatory generalization.

## Corrections to Claude's interpretation

**1. The two SimpleQA A2 results do not demonstrate disagreement.** Claude calls
.832 [.666, .957] inconsistent with .631 [.382, .869] because one interval excludes
chance and the other does not. Significance against .5 is not a test of the
difference between the estimates. An exploratory independent-question bootstrap
of new minus old A2 yields **+.200 [-.075, +.481]** (independent seeds 20260917 and
20260918). A difference is not resolved; equivalence is not established either.
Better class balance may influence precision, but this design does not establish
that it explains the difference in significance or point estimates.

**2. One specific task-standardization is possible.** A task-standardized average
of *within-task* AUROCs across all three tasks is unavailable because DDXPlus and
HLE have no faithful examples. That is different from the live audit's proposed
fixed weighting of the pooled pair types. For each arm, compare unfaithful
responses from each task against faithful SimpleQA, and apply the old unfaithful
task weights (24/60, 22/60, 14/60) in both cohorts and all bootstrap draws.

This yields A2-minus-A1 **+.293 [.094, .506]** in the pilot and **+.335 [.200,
.478]** in the new sample. The new observed pooled contrast was +.323. Therefore
the change in these task weights is not sufficient to explain the positive
contrast. These standardized comparisons still contain cross-task pairs; they
are not estimates of within-task detection on DDXPlus or HLE, and do not repair
generator composition or exposure.

**3. Fresh API calls do not eliminate every possible leakage or adaptation
channel.** The input audit finds no direct native-label injection or prior-score
injection into these calls. Earlier inspection could nevertheless influence
procedure and sample choices. Neither its presence nor its effect is identified
by this run. The absolute statement that there is "no leakage channel" is too
broad; the claim should be limited to the audited request contents.

**4. Distinguish scoring from packet selection.** I reproduce **38/70 responses
and all 18 faithful** as previously scored, packet-selected or included in
retrospective context among the named development artifacts. Direct prior scoring
alone covers **29/70 responses and 17/18 faithful**. Packet selection is not proof
that a human reviewed a case. All faithfully labelled responses are exposed under
the broader definition, so the remaining 32 responses have no faithful class and
cannot support an AUROC.

The 45/70 question-exposure figure counts clusters derived only from directly
overlapping new responses. Including other historical responses in the named
files whose questions match new responses raises this to **50/70**. These are
scope-specific exposure counts, not proof that exposure caused the result.

**5. An observed narrower interval does not identify enrichment as its cause.**
The cohorts differ in more than class balance. The realized narrowing is real;
attribution to the selection choice alone is not established.

## A missing baseline changes the next-step priority

Word count, scored in the previously used direction (longer means more
unfaithful), is highly predictive even within SimpleQA:

| SimpleQA native-label AUROC | Original pilot | New sample |
|---|---:|---:|
| Word count | **.950 [.871, 1.000]** | **.901 [.742, .994]** |
| Step count | .810 [.672, .927] | .823 [.652, .944] |
| Component A2 | .631 [.382, .869] | .832 [.666, .957] |

New-sample A2 minus word count is **-.069 [-.255, +.133]**. The data do not resolve
which is better there. In the pilot, the corresponding difference is -.319
[-.588, -.069]. Pooled word-count AUROCs are .970 and .954, also exceeding the
component scores. A further exploratory sanity check reverses the generic score:
its new pooled AUROC is .723 versus component .599; A2 minus reversed A1 is
-.124 [-.390, +.126]. This is not a newly validated detector or an instruction
to reverse scores in deployment.

The length baseline does **not** prove that A2 itself uses length, or that length
measures causal faithfulness. It shows that task restriction alone has not
removed easy correlates of the selected labels. A high native-label AUROC on
this subset is therefore insufficient evidence of improved semantic assessment.

## Direction from here

Preserve the completed experiment as two-sample exploratory evidence of a
procedure effect. Report the subgroup result transparently, alongside basic
baselines and the exposure/selection limitations.

For the next discriminating experiment, freeze generic versus component
instructions under a **shared output schema and token budget**, so the rubric
contrast can be interpreted. Use fresh questions with faithful and unfaithful
support within the same task/generator and overlapping lengths. If natural data
lack that support, collect it or use separately reported controlled pairs with
independently checkable source/claim predicates; do not call a tiny unmatched
residual a validation set. Keep native-label and controlled-predicate endpoints
separate. Include word/step-count baselines and genuine violation sensitivity,
false accusation rates and insufficient-evidence handling as appropriate to each
endpoint.

A second judge family is useful as an additional dimension of this design,
after checking current resource availability. Running it on the same confounded
population would test model dependence of the observed association; it would not
resolve why the association exists or establish native-label truth. Human review
of the older accusation packet does not gate the frozen native-label comparison
or independently checkable source controls.
