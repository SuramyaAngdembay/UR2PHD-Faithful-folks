# Current research state

Updated September 19, 2026. Research driver: Codex, following the user's explicit
handoff from the previous session. This file supersedes older orientation and
claims; it does not alter the historical frozen experiment.

Latest novelty-sweep audit: the published-detector reanalysis remains a useful
empirical next step, but the historical sweep contains material errors. Kallus-Zhou
is direct AUC-decomposition precedent; Matos explicitly gives an F1 decomposition
with detector-dependent weights. F1 collapsibility does not imply ranking stability.
The sweep's .726 incorrectness AUROC reproduces only on a selected 1,198-response
subset dropping 106 labels, including 80 faithful mistakes. On all 1,303 valid
native-correctness records it is .704 with the binary target or .697 with the
four-way-derived target. These are not comparable to published F1. BonaFide is
mostly incorrect in our audited population, contradicting the sweep's opposite
claim. A 2x2 taxonomy does not prove correctness constitutes faithfulness.
See the [independent corrections](notes/2026-09-19-stratified-novelty-independent-audit.md)
and `results/stratified_novelty_audit/2026-09-19/`. Census and mathematical checks
completed with a hash-verified archive; no inference or manuscript changes.

Latest methodology assessment: there is a plausible training direction based on
faithful/unfaithful comparisons matched on correctness, but neither a successful
method nor a SOTA advantage is established. CIE-Scorer and GeoFaith are relevant
published FaithCoT competitors; their accuracy/F1 results are not comparable to
our stratified AUROCs without matching populations and access. First establish
those baselines, then compare ordinary training, balancing, group DRO, and
within-correctness pair training with question-grouped selection and fresh
confirmation. Gold correctness must not enter a deployed judge/router. See the
[methodology and headroom assessment](notes/2026-09-19-methodology-headroom-and-baselines.md).
No new inference, training, or manuscript edits were made for this assessment.

Latest novelty assessment: the pasted comparison with BonaFide is mostly accurate
about which exact experiments differ, but this is not a general novelty clearance
or grounds to restore a universal two-regime claim. The composition identity is
evaluation analysis, not a new statistical method or proof of an internal mechanism.
The specific FaithCoT audit and construction-transfer tests remain contributions
with restricted scope; Young's classifier-sensitivity study and causal-diagnosticity
prior work also constrain broader claims. See the
[BonaFide novelty assessment](notes/2026-09-19-bonafide-novelty-assessment.md).
No inference or manuscript edits were made for this assessment.

Latest independent completed-run audit: all 420 replication requests and 840
historical pilot records pass request/parse checks; remote and local replication
hashes agree. Direct-pair recomputation reproduces the primary and SimpleQA
intervals; 70 tests pass. The A2-minus-A1 improvement survives within SimpleQA and
fixed weighting of the pooled task-pair types (new +.335 [.200,.478]). That latter
standardization is possible, although within-task AUROCs for DDXPlus/HLE remain
unavailable. SimpleQA A2 .832 versus .631 does not establish disagreement: the
exploratory between-cohort difference is +.200 [-.075,.481]. A missing baseline
matters: SimpleQA word-count AUROC is .950 in the pilot and .901 in the new sample;
new A2 minus words is -.069 [-.255,.133]. This does not prove A2 relies on length,
but length shortcuts remain unresolved. Confirmed broad exposure is 38/70 and
18/18 faithful; direct prior scoring alone is 29/70 and 17/18 faithful. Fresh
stateless calls rule out neither earlier adaptation nor all possible leakage.
Next priority: shared-schema rubric comparison, fresh within-task/generator
support with overlapping lengths, and simple baselines; another judge family is
useful within that design. See the
[completed independent audit](notes/2026-09-17-completed-pilot-replication-independent-audit.md)
and `results/pilot_replication_audit/2026-09-17-completed/`. No new inference.
This assessment supersedes the contradictory interpretations in the historical
Claude summary immediately below.

Claude's replication summary (September 17): 420/420, integrity verified, frozen analysis
run unchanged. **A2-A1 = +.323 [+.194, +.459]** against the pilot's +.293
[+.093, +.502] -- all three pre-registered criteria met. The generic inversion
replicates pooled (A1 = .277 [.153, .418]). **Detection remains unestablished** in
the pre-registered endpoint (A2 = .599 [.426, .747], includes chance). Post-audit
exploratory sensitivities, all in
[the results note](notes/2026-09-17-pilot-replication-results.md): my "unseen data"
framing is WITHDRAWN (38/70 responses and 18/18 faithful were previously scored or
packet-selected -- a foreseeable consequence of taking every available faithful);
task mix matched only in aggregate (unfaithful 24 vs 16 SimpleQA); faithful exist
only in SimpleQA in both samples, so the pooled AUROC contains cross-task pairs and
the pooled inversion is partly a task effect (SimpleQA-only A1 = .413, interval
includes chance). The contrast SURVIVES the within-task restriction in both samples
(+.323 [+.059,+.614] pilot, +.418 [+.238,+.633] replication). Post hoc and not to be
claimed: SimpleQA-only replication A2 = .832 [.666, .957] excludes chance for the
first time, but is inconsistent with the pilot's SimpleQA-only A2 (.631, includes
chance) and sits on the best-balanced subsample we have. An exposure sensitivity is
not computable: zero of the 32 unexposed responses are faithful.

Earlier live audit (during the run): Claude's frozen 420-call A1/A2 replication is running (117
successful requests at September 17, 21:32 UTC; subsequent check 118, with retryable
429s). Selection, payloads, run identity and pinned model pass audit; 70 tests pass.
Let it finish as an exploratory paired comparison, not unseen-data validation.
It is disjoint from the main pilot, but 19/70 responses were scored in earlier
diagnostic campaigns and 30/70 share their questions, including 15/18 faithful
responses. All 18 faithful responses remain SimpleQA. Matching overall task counts
changes the unfaithful task mix; AUROC prevalence invariance does not make the two
populations equivalent, and 936 reused cross-class pairs are not independent
observations. Preserve the frozen primary analysis; require all 420 expected
requests and add explicitly exploratory task-standardized, SimpleQA-only and
exposure sensitivities. No new scores or AUROCs were inspected in this audit.
See the [live replication validity assessment](notes/2026-09-17-live-pilot-replication-validity.md)
and `results/pilot_replication_audit/2026-09-17-live/`.

Previous direction assessment: v1's 576 calls and v1.3's 144 calls are complete;
raw parsing, request identity, hashes and all saved endpoints independently
recompute. Gains concern claim/status coding and insufficient-evidence handling
on authored controls, not established probability calibration, native detector
improvement or generator causality. Both procedures detect 18/36 absent-source
attributions in v1; verification still endorses one. The strong position prediction
failed, but zero position effect/determinism and a note-style mechanism are not
established. The 40-item review subset is optional annotation development:
accusation-bearing assessments only, 40 responses/32 questions, from the older
component pilot. It cannot estimate missed violations or causal CoT faithfulness;
κ measures agreement, not truth, and must not gate all further work. Prioritize
explicit source-predicate controls and fresh common-reference transfer tests;
full human packet completion does not block these. See the
[direction and review assessment](notes/2026-09-16-direction-and-review-packet-assessment.md)
and its `2026-09-16-direction-audit-validation.json` companion. The later dated
assessment supersedes stronger interpretations in historical entries below.

Latest repair: Claude's subsequent accusation audit (`b135d3c`) reads the wrong
prompt field and checks context quotations against the trace. Its full-context
63% unlocated finding is invalid: corrected on the same records, only 2/237 (0.8%)
remain unlocated. All 237 legacy full-context reviewer records lost the original
prompt. Do not use that packet. The repaired packet preserves exact judge evidence
and full qualitative outputs: 392 deduplicated assessments covering all 420
component calls. Deliver only `results/accusation_audit_repair/2026-09-14-final/reviewer/`.
192/473 legacy records allege no supported violation; textual recurrence is not
semantic accusation agreement. All 45 tests pass. No new inference or human
adjudication occurred. See the [independent repair](notes/2026-09-14-accusation-audit-independent-repair.md).
The 24 constructed pairs and the 576-call experiment were frozen and launched later
on September 14 (see the next section); the repair above was accepted in full
(`fb99b0e`), the legacy packet is marked SUPERSEDED, and the protocol carries the
repair's clarifications as amendments v1.1 and v1.2.

Earlier audit: Claude's 840-call repeated four-arm development pilot is complete
and independently verified. On 70 responses (58 questions; U60/F10), mean-score
AUROCs A1/B1/A2/B2 are .2175/.2592/.5108/.4450. The restricted component procedure
improves over the generic procedure by +.293 [.093,.502] in the paired exploratory
analysis, but above-chance detection is not established. Full-evidence effects
remain unresolved. Exact quote failures are not semantic error rates: inspected
full-context outputs repeatedly deny source evidence they themselves quote
correctly. Next: independent allegation validation, matched output-schema controls,
source/process counterfactual pairs, and frozen cross-model/data validation.
39 tests pass. No new inference was launched by this audit. See the
[completed pilot audit](notes/2026-09-14-repeated-pilot-independent-audit.md) and
`results/repeated_pilot_audit/2026-09-14-final/`.

Earlier execution: the shared answer checker and both cached-data analyses are
implemented and run. GRACE now has 280 correct / 154 incorrect / 3 unresolved
reference-equivalence decisions (assistant-reviewed, not independent human gold).
Primary NLI regime differences are +.025 / +.113 / -.004, all with intervals
covering zero. Pooled NLI rho .226/.254 survives; majority-rule error lift is
1.606 [1.432, 1.804], while the all-unfaithful rule is not resolved. BonaFide's
four-arm common-150 AUROCs remain .319/.400/.367/.331 with direct paired intervals.
Final outputs: `results/grace_reanalysis_v3/2026-09-13-final/` and
`results/bonafide_reconciliation_v2/2026-09-13-final/`. Scripts reject stale reviews,
missing/duplicate records, and overwrites; undefined bootstrap samples are explicit.
32 tests pass. Manuscript tables are generated from these results. No new model
inference was needed. See [executed repair](notes/2026-09-13-executed-analysis-repair.md).

Earlier audit entries below are historical where superseded by that executed
repair. The prior containment/F1 labels and saved regime JSON stay preserved,
but are not the current correctness-stratified analysis. Reserved exposure is
204/807 responses across 156 questions (397 responses sharing those questions).

## Controlled verification experiment: frozen and launched (September 14, ~20:30 UTC)

Frozen before any inference at `d43e435`; log in
[the experiment note](notes/2026-09-14-controlled-verification-experiment.md).
24 matched pairs / 48 constructed inputs (`data/constructed_controls/v1/`): 12
source-attribution pairs whose restricted payloads are byte-identical (H4) and 12
verification-language pairs (proposal vs execution claim; claims are *unresolved*
by design). Balance asserted (internal correctness 6/6 per family with visible
slips, position 4/4/4, note position 6/6, first-person 4/4, 12 sources, 12 verbs).
All 24 pairs were manually reviewed by the assistant; independent human review is
pending and does not gate the run. Two procedures (generic assessment vs explicit
claim-by-claim verification) share one strict schema, token cap and pinned
`gpt-4o-2024-08-06`; the harness's `freeze` wrote `lock.json` only after the
checklist and payload checks (24/24/48) passed. Analysis endpoints are frozen and
hashed in `scripts/controlled_verification_analysis.py` (H1 unsupported-accusation
rate with the A3 denominator and an anti-abstention criterion; H2 claim-made; H3
status incl. unresolved coverage; pair ordering; repeat stability; pair-clustered
paired bootstrap). An 8-request smoke on two smoke-only items passed. **The 576-call
run completed** (one credit-exhaustion halt at 135, resumed in place; integrity
verified against the lock; analysis run unchanged). Result
([note](notes/2026-09-14-controlled-verification-results.md)): the verification
procedure is better calibrated and near-deterministic — unresolved when evidence is
withheld (.931 vs .611), proposals separated from execution claims (H2 +.19 [+.07,+.32]
restricted, +.11 [+.03,+.21] full), never endorses a false attribution, repeat
agreement .958 everywhere — but **detects real false attributions no better than the
generic procedure (18/36 both under full evidence)**; it abstains (unresolved 17/36)
where the generic is silent or wrongly says supported. Unsupported accusations fell
only where they existed (restricted attribution 11→5 of 72, item-level −.083
[−.250, .000]); the "fabricated verification" accusation never occurred for either
procedure on constructed controls. H4 leak check passed (12/12 exact ties).
§6 branch: semantic decisions improved → freeze the procedure and test on fresh
native examples + a second judge family. **Amendment v1.3 (September 15) tested the
prompt-position explanation of the 50% detection ceiling and refuted it** for the
verification procedure (after − before +.056 [.000, +.139]; the same six pairs
detected and the same six missed in both positions; per-pair counts replicate v1 in
12/12 pairs); position contributes modestly to the generic procedure only (+.194
[+.028, +.417], four pairs). The pre-registered prediction failed and is recorded as
such ([results](notes/2026-09-15-note-position-v1.3-results.md)). Post-hoc candidate,
not a finding: the six missed pairs are those whose absent note is a procedural
instruction rather than a data-bearing sibling of the cited source — an unbalanced
construction variable; a within-pair v1.4 (144 calls) would test it, only needed if
the paper claims anything about the procedure's detection. Calibration gains stand.
A 40-accusation calibration subset for two-annotator agreement is published
(`reviewer/calibration-40/`, GitHub Pages); κ decides whether full adjudication is
worthwhile. 61 tests pass. Constructed-control results are never pooled with native AUROC.

## Completed repeated pilot (September 14, 01:13 UTC)

Claude completed 70 BonaFide dev responses × four arms × three repeats (840
requests) on pinned GPT-4o. All raw outputs, carried predictions and request-plan
identities match. The retry guard was fixed before completion; reconstructed
lineage has 857 recorded attempts and 17 transient 429 errors, eight in the final
continuation. Results: `results/diagnostic_v2/pilot-4arm-rep3c/`.

The rubric contrast also changes output schema; all ten faithful examples are
SimpleQA, and evidence-insufficient outputs still require scores. SimpleQA-only
A2 AUROC is .631 [.382,.869], a post-hoc sensitivity, not replication. The earlier
six-pair ordering statistic is not directly comparable to pooled 70-response
AUROC. This pilot adds no evaluation-partition exposure. Preserve the
[historical live audit](notes/2026-09-13-live-pilot-alignment.md); use the completed
audit above for current conclusions.

## Scientific direction

Study when CoT faithfulness measurements transfer across evidence policies,
reference standards and selected populations. Current experiments compare
evidence access and its interpretation; rubric and output structure still change
together in the completed pilot. A component procedure is a development
lead; a validated new method and a general two-regime law are not shown.

The user has authorized autonomous selection and execution of needed bounded
experiments. Do not wait for individual prompts to run an appropriate next
diagnostic. Human annotations remain independent evidence and are not simulated.

The independent comprehensive report and scripts live at
`~/Ur2Phd-review-2026-09-07/deep-research-2026-09-11/`.

## Evidence that survives

- FaithCoT correctness-conditioned detector differences and released-score
  inversion remain scoped empirical findings.
- The prompted judge transfers poorly to the frozen BonaFide incorrect subset:
  primary .419, alternate mini .482, GPT-4o .270; steps .878, NLI count .826.
- Source construction decodability does not establish annotated transfer. The
  .616 Llama hint bridge attenuates to .509 on matched questions; corrected
  selector comparisons do not establish the claimed superiority.
- A general judge advantage, distinct internal mechanisms, or proof that the
  datasets assign contradictory labels to the same cases is unsupported.
- The 69%-to-99% comparison is not replicated correctness entanglement: almost
  all selected BonaFide traces are already incorrect. The judge also beats the
  correctness oracle on a common FaithCoT population (.771 versus .696).

## Data constraints

BonaFide curated: 3,066 label rows, 2,177 response keys, 1,120 whole labels.
Primary population: 1,113 incorrect responses (U945/F168), 567 questions.
Seven correct responses are all U, so correct-stratum AUROC is undefined.
Faithful source support: SimpleQA 160, HLE 5, complex tasks 3; no graph whole labels.
Extended has the same 168 faithful responses, 6,475 unfaithful whole labels, and
recovers U whole labels for 376 curated step-only responses. It is a selection
audit resource, not an independent test.

Exploratory generator×task×word-bin conditional pair AUROCs: primary judge .193,
GPT-4o .188, steps .521, NLI .603. Only 1.40% of original pairs remain. These are
restricted comparisons, not causal adjustment or a replacement headline.

## Active work

- Branch `codex/faithfulness-transfer-diagnostics`, starting at `462a7ac`.
- On September 14, at the user's request, the branch was pushed to origin and
  `main` was fast-forwarded to it (`f1598d8`; main had no unique commits; secret
  scan clean). `main` and `codex/faithfulness-transfer-diagnostics` are now the
  same commit; commit on either and keep them in sync, or retire the branch.
  Collaborator PR #6 (`dikshant/dr-rahimi-feedback` → main) remains open and now
  targets the moved main. The
  repaired reviewer packet and its local HTML review form are on GitHub under
  `results/accusation_audit_repair/2026-09-14-final/reviewer/`.
- Corrected the v1 reliance-only target; verified all 1,120 frozen labels/prompts
  against their own upstream responses and preserved the 306/807 split.
- Implemented and tested label-blind inputs, manifest-bound resumption, four
  matched arms, component outputs and bounded execution. Setup: `b77c15c`.
- v2.0 stopped with four valid outputs and three format/quote failures. Amendment
  `be65cf9` records semantic clarification, strict schemas and model pinning.
- v2.1 returned 18 schema-valid outputs, then stopped after three HTTP 429s.
  Five of nine component outputs have nonmatching quotes; semantic inspection
  still finds unsupported process allegations. No AUROC is reported. See
  [pilot result](notes/2026-09-11-diagnostic-v2.1-pilot-result.md).
- A 60-question, development-only independent annotation packet is ready at
  `results/diagnostic_v2/audit/reviewer/index.html`; deliver only the reviewer
  directory or its reviewer-only archive. No human annotations are complete.
- Autonomous batch 1 completed 88 unique calls (96 slots). Full-context generic
  and component judges separate four authored source-claim pairs perfectly;
  restricted inputs are indistinguishable by construction. The 24-case native
  pilot remains confounded by disjoint generators and a strong length association.
- Autonomous batch 2 completed 60 calls on six fresh matched SimpleQA pairs.
  Within-pair ordering: A1 .333, B1 .000, A2 .917, B2 .583. Corrected definition-
  aware D2 gives .500. Six pairs and questionable rationales prevent a method claim.
- A D1 baseline message-role error was found and corrected with 36 separate D2
  calls. D1 performance claims are superseded. Use
  `scripts/monitor_role_correction.py` for the corrected instruction/evidence roles.
- The metadata-comment intervention separately tests two discovery and 12 fresh
  questions, including two actual unchanged-original repeats per case. All 42
  calls completed. Discovery mean score change is −70, but fresh mean is +6.67
  (95% bootstrap −2.5 to 17.5); the simple explanation did not generalize. One
  discovery original changes from 0 to 80 on repeat. Do not claim a cleaning remedy.
- Exact-record audit finds no conflicting full-input twins within either target
  and no exact shared full-input cases between the datasets. The synthetic .5
  ceiling is not a real-data impossibility theorem. Native reason flags overlap.
- Current report: [autonomous results](notes/2026-09-12-autonomous-experiment-results.md).
  Coordinated manuscript plan: `paper/arr/measurement-study-outline.md`.
- GRACE full release now verified and archived: 437 human-annotated test traces,
  2,044 steps across four tasks; historical unreleased/sample-only notes are stale.
  No new GRACE inference yet. Use as a grounding/inference-component cross-check,
  with prior-sample/question-overlap checks and a frozen step-level adaptation.
  FACE-Eval data/results and ProcessBench are also publicly accessible. See
  [release audit](notes/2026-09-12-external-dataset-release-check.md).
- Literature reassessment: classifier-sensitivity work already includes ranking
  reversals and criterion differences, so another reversal is insufficient
  novelty. The hint-verbalization paper's ~90% result is success across multiple
  samples, not a per-response rate established by longer outputs. It does not
  invalidate the full BonaFide target or certify false source/process claims.
  Prioritize common-example reason validation, the frozen GRACE cross-check,
  and same-answer evidence pairs; targeted causal replay is complementary.
  CausalDiagnosticity supplies useful design/code precedents, and NSF-CoT is a
  close comparator for component verification. See the
  [literature and experiment assessment](notes/2026-09-12-literature-and-experiment-direction.md).
  These are research recommendations; no new inference was launched in this audit.
- Claude's later GRACE NLI pass returned 437 cached results. Independent audit
  reproduces pooled rho .226/.254, but finds an invalid first-character answer
  checker on free-response tasks. Correctness-stratified effects and the claimed
  external entanglement replication must be redone. "No length confound" is also
  unsupported across aggregation rules. GRACE judge inference is not established
  by these artifacts; no new inference was launched by the independent audit.
- The September 13 saved checker repair assigns 277 correct / 160 incorrect.
  Independent recomputation matches new differences .046/.091/.007 and lift
  1.169–1.670 conditional on those heuristic labels. Known containment/F1 errors
  remain; these are not validated correctness labels. The scripts and analysis
  JSON have not been updated to consume the replacement labels.
- Claude's reconciliation saved 584 scores on 284 distinct responses. On the
  150-response intersection, A/B/C/historical-D AUROCs are .319/.400/.367/.331;
  A=.352 uses 284 examples and is not the paired estimate. Paired intervals do
  not establish equivalence or a harmful context effect. The public generic-
  monitor interface has a score-direction inconsistency, but its impact on the
  published AUROC remains unverified. The paper's CoT baseline is .67, not .68
  (the latter is step-level). The new audit records exact source and input hashes.
- All four API runs are complete: 226 calls, no transport/parse errors. Next
  priority is fixed-procedure repetition of the component/generic comparison
  and independent checking of alleged violations, retaining fresh validation.
- Versioned new results are under `results/diagnostic_v2/`, `autonomous_batch1/`,
  `autonomous_batch2/`, `monitor_role_correction/`, `metadata_comment_ablation/`
  and `autonomous_campaign_2026-09-12/`. The original frozen evaluation stays
  untouched. The original 807-response partition now includes 204 responses
  scored in Claude's reconciliation, spanning 156 question clusters. A
  2026-09-19 audit established that **the eval partition was never held out at
  all**: `bonafide_predictions.json` carries judge4o/judgeA/judgeB/NLI/PI scores
  for all 1,120 responses, and the frozen eval tested H1/H2/H3 on n=1113 -- dev
  and eval together -- at 20:38 on 2026-09-09, **three hours before
  `dev_clusters.json` created the split at 23:45**. Exposure is **807/807
  (100%)**, not the 204 or the later 284 previously recorded. The partition is a
  **procedure-specific holdout only**: every diagnostic_v2 run (pilot,
  replication, v1, v1.3) is dev-only, so it is unexposed to the component and
  verification procedures, but it is fully exposed for judge4o/judgeA/judgeB/NLI/PI.
  Never call it held out without naming the procedure. See
  [the holdout and p-hacking audit](notes/2026-09-19-holdout-and-phacking-audit.md). Preserve the split and record new exposure;
  do not describe the entire partition as unopened. The whole campaign remains
  exploratory; freeze exact requests before subsequent inference.

## Compute and publication

Aquaman is reachable, its dedicated environment and data paths verified, and
its two 8GB GPUs were idle at takeover. Anvil own-account login and both GPU
associations work, but remaining GPU/AI allocations are nearly exhausted.
Detailed resource snapshots and alternate-account scope are in the local compute
skill; check live before a run. Continue CPU work and a bounded pilot meanwhile.

Current manuscript workspace: `paper/arr/main.tex`. Its title and several
interpretations still need a coordinated revision after the diagnostic direction
is resolved. Do not claim a new submission or successful method from a plan.
