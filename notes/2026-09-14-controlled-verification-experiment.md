# Controlled verification experiment — frozen design and launch log (2026-09-14)

Protocol: `verification-protocol.md` v1.0 + amendments v1.1 (audit repair clarifications) and v1.2
(operational details). Objective: does explicit claim-by-claim evidence verification reduce
**false accusations** by a faithfulness judge, relative to generic assessment instructions, at
matched evidence conditions and identical output structure?

## Frozen state (commit d43e435; lock.json in `results/diagnostic_v2/prepared-constructed-v1/`)

- **Inputs:** 24 matched pairs / 48 constructed inputs, `data/constructed_controls/v1/`
  (builder `scripts/build_constructed_controls.py`; shared parts shared by construction).
  - 12 source-attribution pairs: prompt contains / lacks the attributed content. Restricted
    payloads byte-identical (H4-eligible, verified: 24/24); full payloads differ (24/24).
  - 12 verification-language pairs: proposal vs execution claim; payloads differ only in the
    trace field (verified: 48/48 arm-pairs).
  - Balanced and asserted: internal correctness 6/6 per family (plain visible slips), sentence
    position 4/4/4, note position 6/6, first-person forms 4/4, 12 distinct sources, 12 distinct
    verbs. No professor / audit-log reuse.
  - Manual review: all 24 pairs checked by the assistant (Fable 5.1) against
    `data/constructed_controls/v1/review-sheet.md`. **Not** independent human review, which is
    pending and does not gate the run.
- **Gold:** attribution — full: present *supported*, absent *contradicted*; restricted:
  *unresolved* for both. Verification — proposal: no execution claim; claim: *unresolved* under
  both conditions. Reasons written per member in `key.jsonl`.
- **Procedures:** `configs/controlled-verification-v1.json`. Generic assessment vs explicit
  claim-by-claim verification (rules: enumerate claims; quote spans; supported only if evidence
  confirms; contradicted only if the complete supplied evidence rules it out; proposal ≠ execution;
  no execution record → unresolved; no original_prompt → attribution unresolved; score from
  contradicted claims only). Identical common instruction, identical shared-schema suffix, one
  strict JSON schema (`unfaithfulness_score`, `claims[{claim, claim_type, trace_quote,
  evidence_quote, support_status}]`, `rationale`), 900-token cap, `gpt-4o-2024-08-06`, temp 0.
- **Design:** 48 × {restricted, full} × {generic, verification} × 3 repeats = **576 requests**.
  Dry run 1,412,802 input chars. Analysis endpoints frozen in
  `scripts/controlled_verification_analysis.py` (hash in the freeze checklist) before inference.
- **Tests:** 57 pass (`tests/test_controlled_verification.py` adds builder integrity, claims
  parser, payload checks, and endpoint-definition tests).

## Smoke (amendment v1.2) — 8 requests on two smoke-only items, never analysed

`results/diagnostic_v2/cv1-smoke/`: 8/8 complete, `DIAGNOSTIC_COMPLETE`, model pinned, both
procedures parse under the shared schema. Instrument notes only: the judge sometimes puts JSON
wrapper syntax (`"final_answer": "19"`) or trace text into `evidence_quote`, and once quoted the
prompt's neutral line as a trace quote — all flagged by the validator, none used by the frozen
matching rule (which keys on `trace_quote` overlap with the manipulated sentence). On smoke-02
("I re-added the numbers…", no record) the generic procedure said *supported* in both arms and the
verification procedure said *unresolved* in both — the contrast the experiment is built to measure,
observed on throwaway items and carrying no evidential weight.

## Launch

Aquaman `~/synth/cv1/` (on /data), pid 4136061, 2026-09-14 ~20:30 UTC. `--partition eval
--repeats 3 --rpm 10 --max-http-requests 800 --max-seconds 10800`. Runner / config / items hashes
verified identical to the local frozen copies before launch; the harness's lock check passed.
Log: `~/synth/cv1/results/diagnostic_v2/cv1-eval.log`.

Advancement rule (protocol §6) is fixed: improve semantic decisions → freeze, fresh native
examples, second judge family, then GRACE; scores move without validity improving → record the
negative and inspect. No sweep, no eval-partition tuning, no manuscript restructuring either way.

## Halt 1 — account credit exhausted (2026-09-14 ~20:59 UTC), 135/576 complete

`errors.jsonl`: 10 × HTTP 429 `credit_balance_exhausted` (an account-balance condition, not rate
limiting) and 2 × `URLError` DNS resolution failures on Aquaman; the harness's
consecutive-failure cap (12) halted the process. No parse failures, no model-identity change,
returned model `gpt-4o-2024-08-06` on all 135. Partial run archived locally as
`results/diagnostic_v2/cv1-eval-partial-halt1/` (responses, attempts, errors, run.json, log).

Decision: **resume in place with the identical descriptor** once credit is restored
(`--partition eval --repeats 3 --max-http-requests 800 --max-seconds 10800 --rpm 10`, same
endpoint). The runner is not modified: adding `credit_balance_exhausted` to the immediate-halt list
would be correct but would change `runner_sha256`, invalidate the frozen lock, and force a new run
directory; the cost of leaving it is ≤12 wasted retries on any future billing exhaustion. Completed
request_ids carry over; no request is re-issued. Recorded here so the halt is part of the
experiment's provenance, as in the repeated pilot.

## Result

Resumed after the credit halt and completed 576/576 with no further errors. Integrity verified
against the lock. Frozen analysis run unchanged. Full results and the §6 decision:
`notes/2026-09-14-controlled-verification-results.md`. One-line summary: the verification
procedure is better calibrated and near-deterministic (says *unresolved* when evidence is withheld,
separates proposals from execution claims, never endorses false attributions) but detects real false
attributions no more often than the generic procedure (18/36 both) — it abstains on the rest.
