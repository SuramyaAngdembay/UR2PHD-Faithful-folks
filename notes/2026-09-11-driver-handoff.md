# Research driver handoff and execution record

Local date: September 11, 2026. Remote run timestamps use UTC (September 12).

## Recovered context

The active repository is `SuramyaAngdembay/UR2PHD-Faithful-folks`. Work continues
on `codex/faithfulness-transfer-diagnostics` from local `462a7ac`. At takeover,
GitHub main was `4252263`, with 22 inherited local commits beyond it. The open
collaborator PR #6 is separate. Setup and the instrument amendment are local
commits `b77c15c` and `be65cf9`; no publication is implied.

Recovery covered the main Claude research session, its experiment artifacts and
memory, the independent September 11 review, previous Codex compute sessions,
and the relevant Anvil material in the separate insider-threat session. The
current entry points are `AGENTS.md` and `CURRENT_STATE.md`. Historical claims
in `CLAUDE.md`, commit messages and manuscript drafts remain historical.

Two installed local skills persist decision-relevant context:

- `ur2phd-research`: repository, manuscript and session map; verified label
  definitions; surviving findings; study and interpretation constraints.
- `ur2phd-compute`: verified host/environment/cache paths, resource snapshots,
  allocation scope and a reusable read-only status script.

Access details and session paths are local skill references, not public code.
The public research and compute documentation is supplemented by live SSH
verification; an old successful run is not evidence of present resources.

## Work now implemented

1. Verified every one of the 1,120 frozen whole-label responses against its own
   upstream label and original prompt. Prepared 1,113 incorrect responses with
   the existing question-group split: 306 development and 807 evaluation.
2. Implemented label-blind request construction, four matched arms, input/config/
   runner hashes, request-identity resumption, bounded calls and saved failures.
3. Ran the initial instrument check, preserved its failure, and recorded v2.1
   before the bounded retry. See the separate instrument amendment and versioned
   raw results. These small, deliberately selected samples do not estimate AUROC.
4. Built the independent development annotation packet described below.

## Independent annotation packet

Build script: `scripts/diagnostic_audit_packet.py`.
Local output: `results/diagnostic_v2/audit/reviewer/`.
The reviewer directory contains an offline form, instructions, input records,
and an empty CSV. It is the only directory to deliver to a reviewer. The parent
contains the withheld native-label and sampling key.

The 60 items represent distinct development questions: 26 native faithful and
34 native unfaithful, spanning 49 SimpleQA, eight HLE and three DDXPlus cases.
Selection prioritizes class and generator/source/length coverage. It is not a
representative population sample, and not yet the cross-source study. Source
coverage is limited by the available faithful examples. No human annotations
have been completed or simulated.

Use two independent reviewers on all 60 pilot items if feasible. Each records
acknowledgment, identifiable reliance, a supported false process claim, justified
omissions, logical support, an overall process judgment, evidence spans and
uncertainty. Reviewers should finish their own copy before discussing cases.
Compare their judgments only afterward with each other, native labels and the
judge. Report raw agreement, class/uncertainty confusion tables and adjudication
outcomes; neither consensus nor the benchmark label observes hidden computation.

This first packet validates the instrument on BonaFide. The next packet must
include FaithCoT and apply both explicit reference procedures to the same
examples under a declared common evidence policy. Randomize review order and
keep judgments independent to reduce carryover. Compare native targets only
afterward. Missing process evidence remains insufficient evidence; it cannot be
repaired by forcing the reviewer to choose a binary label.

## Next decisions for the paper

The main path is **measurement transfer across evidence policies and reference
procedures**. Component verification is a candidate remedy requiring evidence.

| Gate | Required result | Consequence |
|---|---|---|
| Instrument | Valid records and sensible component interpretations on reviewed development cases | Freeze the procedure before broader scoring. Formatting success alone does not pass the scientific gate. |
| Reference audit | Independent reviewers can identify the intended components and explain uncertainty | Proceed with paired cross-source annotation; otherwise collect process logs or narrow the target. |
| Matched diagnostic | Paired context/rubric contrasts, complete-case coverage, count baselines and a definition-aware full-context baseline | Identify what change helps under a fixed population and endpoint. Do not infer the sole cause of the original reversal. |
| Independent transfer | Gains on checkable process components in fresh tasks, templates or generators | A reusable verification procedure becomes plausible. If gains disappear, retain a scoped empirical audit. |

The prepared evaluation partition stays closed until the instrument, model,
settings and analysis are fixed. Its 807 examples are not a fresh confirmatory
benchmark for this already exploratory campaign. A small external logged-process
collection can provide the missing independent target: separately vary whether
a process claim is true, whether reasoning is logically valid, and whether the
answer is correct. Tool absence alone must not define the label; the target is
a false assertion about an operation. Natural responses, retained logs and
held-out templates matter more than another benchmark name.

Larger model panels follow these gates. Additional GSM8K volume and BonaFide
Extended do not supply process truth or new faithful comparison cells by
themselves. The existing source/selection audit already constrains that choice.

## Compute consequence

Aquaman is available for CPU work and small models, with two 8GB RTX 3070 GPUs;
new outputs use its data volume. The bounded API smoke uses the established
judge setup. The own Anvil accounts have only 2.3 A100 and 2.6 H100 service units
remaining at the recorded check, and the project is near its file-count quota.
Another session uses separate allocations for an active project; their use for
UR2PhD remains unresolved. This does not block annotation, CPU analyses or the
current bounded pilot, but larger self-hosted judge runs need an available
allocation with an explicitly established UR2PhD scope.

## Verification and pilot checkpoint

The v2.1 pilot stopped after 18 schema-valid responses and three HTTP rate-limit
errors. Direct inspection still finds unsupported process allegations; see
`2026-09-11-diagnostic-v2.1-pilot-result.md`. This is a reason to validate the
instrument before scaling, not a new population-performance result.

Nine integrity tests pass. The packet was rebuilt in a temporary directory and
matched the delivered records; checks verified independent development questions,
the allowed reviewer fields, empty answers, archive exclusion of the key, and
protection against overwriting existing annotations. Its JavaScript passes a
syntax check; the browser interaction has not been manually tested. Both skills
pass their validators and their status script has run against both hosts.
Downloaded raw run artifacts match the remote SHA256 hashes. The frozen
population, original prompt mapping and split remain byte-identical.
