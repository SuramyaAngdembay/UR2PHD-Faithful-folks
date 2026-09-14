# Accusation audit of cached component outputs (protocol §3) — 2026-09-14

No new inference. Source: `pilot-4arm-rep3c` A2/B2 outputs, 70 development responses.
Script `scripts/accusation_audit.py`. Deliverables in `results/accusation_audit/`:
`automatic_counts.json`, `reviewer_packet.jsonl` (473 items, blinded), `audit_key.jsonl`.

**473 distinct accusation records** over 70 responses (A2 236 / B2 237), deduplicated across
repeats by (response, arm, normalised rationale + quotes) with every contributing request_id
retained. Repeat multiplicity: 446 appear once, 22 twice, 5 three times — i.e. **the same
accusation is rarely reproduced verbatim across identical repeats**, consistent with the measured
temp-0 instability.

## (a) Automatic: where does each cited quote actually occur?

**Trace quotes are overwhelmingly fine.**

| arm | benign presentation | wrong field | not located |
|---|---|---|---|
| A2 | 230 / 236 (97%) | 0 | 6 (2.5%) |
| B2 | 229 / 237 (97%) | 0 | 8 (3.4%) |

**Context quotes are where the problem is, and it is arm-specific.**

| arm | benign | wrong field (question) | not located | absent |
|---|---|---|---|---|
| A2 | 39 (17%) | **176 (75%)** | 12 (5%) | 9 |
| B2 | 24 (10%) | 63 (27%) | **150 (63%)** | 0 |

Read carefully, this is a **schema-misuse finding, not a fabrication finding**:

- Under **restricted** evidence (A2) there *is* no context field — the judge has only question,
  trace and answer. It fills `context_quote` anyway, 75% of the time by re-quoting the question.
  It is complying with the output schema rather than declining to cite absent evidence.
- Under **full** evidence (B2) the context field exists, and wrong-field attribution drops sharply
  (75% → 27%) while `not_located` rises (5% → 63%). The larger supplied prompt gives more material
  to paraphrase, and paraphrase is not lexically locatable.

So the earlier headline — "cites quotes absent from its evidence" — was measuring, mostly, a judge
forced to populate a field that has no referent in its condition. My original 23.8%/12.9% figures
conflated that with genuine sourcing failure.

## (b)-(d) Semantic questions: packet only, not answered here

Whether the trace makes the alleged claim, whether the evidence supports/contradicts/leaves it
unresolved, and whether the accusation follows, are **not** automatically checkable and are not
reported. `reviewer_packet.jsonl` carries 473 items with native labels, scalar scores and procedure
names withheld, and evidence boundaries preserved (a reviewer sees exactly what that judge saw).
Assistant annotations, if ever produced, go in a separate file and are never merged with human
adjudication.

**Quotation failures are not reported as a hallucination rate.**

## Defect found in my own audit code

The first blinding assertion was a substring test and fired on `"A2"` appearing in evidence text —
which turned out to be **chess board squares** ("pawns on A2, B2, C2..."), not procedure names.
Replaced with a structural check: allowed keys, and no value exactly equal to a procedure name or
label class. Same recurring error as the GRACE answer checker and the `_quote_validation`
truthiness bug — a crude string test standing in for a structural one.

## CORRECTIONS — this audit's headline was an audit-code artefact (2026-09-14, later the same day)

Independent repair: `notes/2026-09-14-accusation-audit-independent-repair.md`, commit 527be55.
I verified every claim in it against the data; all reproduce.

1. **Wrong prompt key.** My `visible()` read `prompt`/`full_prompt`; the data stores
   `original_prompt`. Every one of the 237 full-evidence records was audited against an **empty**
   prompt. Corrected B2 context-quote location: 229 literal, 6 whitespace-only, **2 unlocated
   (0.8%)** — not 150 (63%).
2. **Wrong reference field.** I checked context quotes against the *trace*. The rubric says
   `context_quote` is an exact span from **question/original_prompt**, and the harness validates
   exactly that. Quoting the question under restricted evidence was the *instructed* behaviour.
   "Wrong-field attribution" (75%) and "no legitimate referent" are withdrawn.
3. **"5 of 473 repeat" measured wording recurrence, not judgment.** Keyed on rationale text +
   quotes, it cannot say whether the judge repeats its accusation. Decision-code agreement across
   the three identical repeats: false-process code **60/70 (A2), 63/70 (B2)**; full five-component
   vector 39/70 / 51/70; identical rationale text 0/70 / 4/70. Textual recurrence, decision
   stability and semantic agreement must be reported separately.
4. **Units.** 192/473 of my "accusation records" allege no violation at all. They are
   quote-linked assessment records, not atomic accusations. "473 accusations" is withdrawn.

**Discarded:** "full context increases unlocatable paraphrasing"; "restricted judges have no
valid context to quote"; "accusations almost never repeat". **Retained:** generic inversion;
paired component gain without established detection; inspectable cases where the judge quotes
evidence correctly and then accuses contrary to it.

One check the repair did not make, which I add: of the 37 restricted-arm context quotes that do
not locate in the question, **0 land in the withheld `original_prompt`** (25 are in the trace, 12
nowhere) — no leak of withheld evidence into the restricted arm.

This is the third instance of the same error class in this project (GRACE answer checker,
`_quote_validation` truthiness, now field names): using a field without inspecting the data or
reusing the harness's existing definition. The fix that generalises is the one the repair applied —
reuse the frozen parser's `allowed_context` rather than re-deriving evidence boundaries.
