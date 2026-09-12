# Current research state

Updated September 11, 2026. Research driver: Codex, following the user's explicit
handoff from the previous session. This file supersedes older orientation and
claims; it does not alter the historical frozen experiment.

## Scientific direction

Study when CoT faithfulness measurements transfer across evidence policies,
reference standards and selected populations. Begin with a repaired rubric ×
context diagnostic and independent component annotation. A new verification
method is conditional on validated gains; a general two-regime law is not shown.

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
- The branch includes 22 inherited local commits beyond origin/main; do not
  publish them incidentally. Collaborator PR #6 remains separate.
- Repair the v1 diagnostic's reliance-only target and overstrong mechanism
  claims. Preserve the 306-development / 807-evaluation response split.
- Build and verify label-blind input generation, manifest-bound resumption,
  matched-context contrasts, component outputs, and a small format pilot.
- Prepare a development-only independent annotation packet. Human review is
  not yet complete and model judgments will not be represented as human gold.
- Keep all new results under `results/diagnostic_v2/`; the original frozen
  evaluation stays untouched. Whole campaign remains exploratory.

## Compute and publication

Aquaman is reachable, its dedicated environment and data paths verified, and
its two 8GB GPUs were idle at takeover. Anvil own-account login and both GPU
associations work, but remaining GPU/AI allocations are nearly exhausted.
Detailed resource snapshots and alternate-account scope are in the local compute
skill; check live before a run. Continue CPU work and a bounded pilot meanwhile.

Current manuscript workspace: `paper/arr/main.tex`. Its title and several
interpretations still need a coordinated revision after the diagnostic direction
is resolved. Do not claim a new submission or successful method from a plan.
