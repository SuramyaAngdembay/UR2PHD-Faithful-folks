# Live four-arm pilot alignment audit

Checked September 13, 2026, at 22:22–22:23 UTC. This is a read-only audit of the
running experiment; no inference was launched, stopped, or reconfigured.

## Verdict

Aligned with the proposed repeated four-arm **development pilot**, but not yet
the cross-dataset, independently validated experiment. Preserve and finish this
pilot. Interpret its rubric contrast as a bundled procedure contrast because the
response schemas differ. Do not treat lexical quote checks as allegation truth.

## Verified execution

- Actual Aquaman process is active, using `configs/diagnostic-v2.1-pilot-r.json`.
- 70 BonaFide incorrect-answer development responses, 58 question clusters.
- A1 restricted/generic; B1 full-context/generic; A2 restricted/component;
  B2 full-context/component. All four arms have the same 70 response IDs.
- Three byte-identical payload repeats per response/arm, with distinct request
  identities: 840 planned calls, 210 per arm. Repeats are not new examples.
- Pinned requested and returned model: `gpt-4o-2024-08-06`; temperature 0;
  `max_tokens=1024` in every arm.
- At 22:22 UTC: 324 valid unique responses, exactly 81 per arm. At 22:23:04 UTC:
  327 valid responses, process alive, no completion marker, two recorded 429s.
- The on-server prepared-data and runner identities match the run descriptor;
  reconstructing the plan reproduces all request IDs in order.
- All 178 responses carried from the previous run are exactly unchanged, occur
  once, and have corresponding attempt-ledger records. Resume did not replace
  these predictions or accidentally reuse one output for multiple repeats.
- Local/server runner SHA256 agrees:
  `3032f2f018c42f7793bc84adce03130c6d544a3419d15e67971330b114d9342f`.
- 34 repository tests pass; actual request reconstruction also verifies repeats,
  shared populations, and input/output policies rather than only digest behavior.

## Scientific qualifications

1. **The rubric contrast also changes the requested output.** A1/B1 return only
   `unfaithfulness_score`. A2/B2 additionally return evidence status, five component
   assessments, quotes, and rationale. The context contrast is controlled within
   each procedure; the between-procedure contrast cannot isolate wording from
   structured reasoning/output elicitation. A subsequent control should match
   the output format and deliberation request when isolating rubric effects.
2. **The sample is useful for development, weak for generalization.** It has
   U60/F10; all ten faithful examples are SimpleQA. Unfaithful examples comprise
   SimpleQA 24, DDXPlus 22, HLE 14. No within-DDXPlus or within-HLE AUROC is possible
   here. Pairing controls which examples receive which arm, but does not establish
   transfer beyond this selected composition. Report question-level uncertainty
   and the SimpleQA subset separately; never count 840 calls as 840 examples.
3. **Insufficient evidence is not implemented as abstention.** The component
   schema still requires a numeric score, and inspected insufficient-evidence
   outputs contain one. Report the insufficiency rate separately unless an
   explicit decision policy maps it to abstention and reports resulting coverage.
   Generic arms have no evidence-status field, so a four-arm abstention comparison
   is unavailable under this protocol.
4. **Quote validation is only lexical.** At the 324-output snapshot, 42 of 162
   component responses failed exact-span checking (16 B2, 26 A2), across repeated
   measurements of only 27 fully processed items. This is provisional output
   quality information, not a semantic false-allegation rate. Matching text, or
   empty evidence, does not establish that a claimed violation is supported.
   Generic outputs contain no allegations to audit under the current schema.
5. Only BonaFide and one judge model are included. Independent answer-equivalence
   review, independent allegation validation, a second model family, and a GRACE
   preparation/adaptation remain separate outstanding tasks.

## Operational issue: the retry amendment does not remove the halt condition

The verified live runner initializes `failures=0` once, increments it on each
error, and raises at `failures>=3` (lines 248, 288–289). It never resets the counter
on success. Therefore it stops after three **cumulative**, not consecutive,
errors per invocation. Raising `max_attempts_per_request` from 2 to 6 does not
remove that guard. With two errors already in this invocation, another transient
error can stop it again.

Pacing still uses `time.sleep(60/args.rpm)`, not a token-window limiter. Slowing
to four requests/minute can help but does not directly handle bursts of long
inputs, especially three adjacent identical repeats. A separately versioned
runner amendment should handle transient rate-limit resets and token-aware
pacing while retaining terminal stops for authentication, billing, invalid
requests, and model drift. Do not silently edit the live manifest or its code.

The future analysis should freeze repeat aggregation and direct paired contrasts
before examining complete native-label results. Preserve failed slots and report
output validity, quote validity, evidence insufficiency, and repeat instability
alongside discrimination. This pilot does not by itself validate a new method.
