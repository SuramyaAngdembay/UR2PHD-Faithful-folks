# Live pilot replication: validity audit, September 17, 2026

**Verdict:** let the frozen run finish. It is a useful exploratory paired
comparison of the older A1/A2 procedures on additional development responses.
It is not clean unseen-data validation, a prevalence-only resampling of the
pilot population, or a test of the newer verification procedure. Those
qualifications affect the interpretation, not the legitimacy of collecting the
remaining predictions.

This audit checks Claude's specification, selection, implementation, historical
exposure, and live execution. No partial replication scores or AUROCs were
examined. Preserve the original frozen specification and analysis; the
supplemental analyses below are recorded before examining new outcomes.

## What is running

At commit `6621b14195cbbef001c73380aeea673d79696afe`, the experiment selects 70
BonaFide development responses: 18 faithful, 52 unfaithful, 55 question clusters.
Each receives A1 (restricted generic assessment) and A2 (restricted component
assessment), three times each: **420 requests** to pinned
`gpt-4o-2024-08-06`, temperature zero. The objective is to retest the older pilot's
A2-minus-A1 AUROC contrast, +.2933 [.0932, .5020].

The selection, prompts, analysis and lock were frozen before inference. I
reproduced the selection and checked all 420 planned payloads against the old
procedure. The sample shares no response or question cluster with the main
70-response pilot. The paired question-cluster bootstrap is appropriate to the
dependence structure, subject to ordinary small-sample limitations. The existing
test suite passed all 70 tests.

Live metadata at **21:32:40 UTC**: 117/420 successful requests, six recorded
errors, no completion marker. A follow-up showed 118 successful requests, seven
HTTP 429 rate-limit errors, six of those failed attempts subsequently completed,
and the process still alive. Request IDs were unique and in the frozen plan;
run identity and artifact hashes matched; returned model identity was pinned.
An earlier check also independently re-parsed every then-completed raw response
and matched the saved parsed record. Rate limiting is an execution issue to
monitor, not evidence of a scientific failure; final analysis must require all
420 planned successes.

Audit artifacts: [design](../results/pilot_replication_audit/2026-09-17-live/design-audit.json),
[exposure ledger](../results/pilot_replication_audit/2026-09-17-live/prior-diagnostic-exposure.json),
[live metadata](../results/pilot_replication_audit/2026-09-17-live/live-status.json).

## 1. Disjoint from the pilot does not mean previously unseen

Matching actual successfully scored response IDs and their question clusters
against the earlier autonomous batches, metadata-comment ablation,
monitor-role correction and smoke runs gives:

- **19/70 responses** were themselves scored in an earlier diagnostic campaign.
- **23/55 question clusters** appeared in those campaigns, affecting **30/70**
  responses in the new selection.
- **15/18 faithful responses** belong to previously scored question clusters.
- Excluding those question clusters leaves **40 responses: 3 faithful, 37
  unfaithful**. That sensitivity cannot provide a strong independent replication.

These counts concern the named diagnostic campaigns, not every historical use
of the dataset. The broader BonaFide population already informed benchmark
analyses and hypothesis development. The deterministic pre-outcome selection
does not demonstrate cherry-picking, and earlier exposure alone does not prove
the new contrast biased. It does prevent calling this an unseen holdout or
claiming that pilot disjointness resolves the project's adaptive-development
history.

## 2. Matching total task counts changes the class-conditional task mix

| Task | Pilot faithful | Pilot unfaithful | New faithful | New unfaithful |
|---|---:|---:|---:|---:|
| SimpleQA | 10 | 24 | 18 | 16 |
| DDXPlus | 0 | 22 | 0 | 22 |
| HLE | 0 | 14 | 0 | 14 |

All 18 new faithful responses are still SimpleQA. The specification's suggestion
that the fresh draw escapes the pilot's all-SimpleQA faithful class is false.
The selection adds faithful responses while holding total task counts fixed;
consequently, SimpleQA falls from 40% to 30.8% of the **unfaithful** class.
Generator composition within classes changes too.

AUROC is invariant to class prevalence when the score distributions conditional
on class remain fixed. This design does not preserve those distributions by
construction. For these samples, pooled AUROC is a weighted average of comparisons
between faithful SimpleQA responses and each unfaithful task. Changing those
weights can change the pooled AUROC and the A2-minus-A1 contrast even without
changing a procedure's performance within a task. Therefore, the claim that
enrichment increases precision "without biasing the estimate" is not warranted
as a claim about estimating the same population quantity.

The paired A2-minus-A1 contrast on the **new selected population** remains a
meaningful descriptive endpoint. The same estimator code does not make the two
selected populations equivalent.

## 3. Pair count is not effective sample size

The 18 × 52 = 936 cross-class comparisons reuse the same responses. They are not
936 independent observations, and the increase from 600 to 936 does not establish
a 1.56-fold precision gain. The data contain 70 responses in 55 question clusters;
the faithful class spans 16 questions. Additional minority-class support may help,
but uncertainty must come from the clustered paired analysis. Correlation among
ROC comparisons is a standard statistical issue; see
[DeLong, DeLong and Clarke-Pearson (1988)](https://pubmed.ncbi.nlm.nih.gov/3203132/).

## 4. What an eventual positive contrast would establish

A positive interval excluding zero would support the component **procedure
bundle** outperforming the generic procedure on this selected native-label
population. A1 and A2 differ in rubric, requested rationale/evidence, and output
structure, so this does not isolate a rubric-only mechanism. It also does not
establish above-chance A2 performance: report each arm's own AUROC and interval.

The new run omits full-context arms and uses the older component procedure. It
cannot test stronger models, the newer verification procedure, evidence-access
effects, or the generator's actual causal reasoning. Native-label agreement is
the endpoint; an additional human review packet is not required to calculate it.
That fact does not make the native labels definitive ground truth for every
notion of faithfulness.

R2/R3 (a point estimate lying inside the other study's interval) are descriptive
compatibility checks, not formal equivalence or replication tests. A nonsignificant
contrast would not by itself refute the pilot, and interval inclusion would not
establish the same effect size. Report all frozen criteria without turning them
into stronger claims.

## 5. Completion gate and supplemental analysis

Keep the running selection, prompts and primary endpoint unchanged. Before
trusting final output:

1. Independently require the complete 420-request plan, all 70 expected response
   IDs, two arms and three distinct planned repeats per response, matching
   identities/hashes, raw-to-parsed agreement, and a successful completion marker.
   `replication_analysis.py` checks three records per observed cell but does not
   itself enforce all of these conditions; a complete prefix of cases could pass
   its cell-count check. Do not analyze such a prefix as the full experiment.
2. Report the frozen overall comparison with question-cluster paired intervals,
   both arms' absolute AUROCs, repeats, and the selection/exposure table above.
3. Add **exploratory** SimpleQA-only and task-standardized contrasts. For the
   latter, use the old unfaithful-task weights (24/60, 22/60, 14/60) for comparisons
   against faithful SimpleQA responses in each cohort, keeping these weights
   fixed inside question-cluster resampling. This separates changing task weights
   from the observed result; it does not fix generator composition, exposure or
   the absence of faithful examples in the other tasks.
4. Report the exposure-stratified sensitivity without promoting the remaining
   three faithful responses to an adequate validation set. Report undefined
   bootstrap draws explicitly and withhold intervals if support is inadequate.

The frozen analysis silently redraws single-class bootstrap samples. In an
independent check of the planned 2,000 seed-zero draws, **neither full cohort had
any undefined draw**, so this implementation choice does not change the planned
full-cohort intervals. Do not assume that remains true for restricted sensitivities.

After completion, use the result to prioritize development. A stronger claim
requires fresh common-reference validation with adequate faithful support and a
frozen comparison that separates rubric from output schema. More judges or more
repeats cannot repair the present population restrictions on their own.
