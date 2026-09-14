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
