# Controlled verification experiment — results (2026-09-14)

Frozen design: `notes/2026-09-14-controlled-verification-experiment.md`; protocol
`verification-protocol.md` v1.0 + v1.1 + v1.2. Run `results/diagnostic_v2/cv1-eval/`
(576/576, `gpt-4o-2024-08-06`, temp 0, 3 identical repeats). Analysis
`results/controlled_verification/v1-analysis/` from `scripts/controlled_verification_analysis.py`
**run unchanged** (hash equal to the freeze checklist). Endpoints, matching rule and bootstrap were
fixed before the first request. **Constructed controls only; nothing here is pooled with native
benchmark AUROC.** 12 pairs per family → every interval is wide; read directions and counts, not
third decimals.

Integrity: all 576 request_ids equal the frozen plan in order; lock digest matches via the harness's
own `digest`; run identity equals the lock; responses hash equals the completion marker; one
returned model; 12 ledger errors, all from the credit halt (`credit_balance_exhausted`), none after
the resume. The harness does not persist the repeat index (recovered from the plan: 192/192/192;
no endpoint uses it — repeats are grouped by item and arm).

Cells: `gen` = generic assessment, `ver` = explicit claim-by-claim verification; `restr` = question
+ trace + answer, `full` = also the complete original prompt. 72 records per attribution cell
(24 items × 3 repeats), 72 per verification-family cell. Contrasts are ver − gen within an evidence
condition, pair-clustered paired bootstrap (2,000 draws, seed 0), 95% percentile intervals.

## Attribution family (12 pairs: prompt contains / lacks the content the trace attributes)

| endpoint | gen/restr | ver/restr | gen/full | ver/full | ver−gen restr | ver−gen full |
|---|---:|---:|---:|---:|---:|---:|
| target accusations (n) | 11 | 5 | 18 | 18 | | |
| …of which unsupported | 11 | 5 | 0 | 0 | | |
| H1 item-level unsupported-accusation rate | .153 | .069 | .000 | .000 | **−.083 [−.250, .000]** | .000 |
| H2 attribution claim surfaced | .819 | 1.000 | .792 | 1.000 | +.181 [.000, +.361] | **+.208 [+.056, +.403]** |
| H3 status accuracy | .611 | .931 | .667 | .750 | **+.319 [+.097, +.556]** | +.083 [.000, +.181] |
| unresolved coverage (gold unresolved / gold contradicted) | .746 / – | .931 / – | – / .185 | – / **.472** | | |
| mean unfaithfulness score | 49.0 | 38.9 | 26.1 | 25.0 | −10.1 [−21.3, +0.2] | −1.1 [−4.0, +1.7] |
| repeat agreement (judged status, 3/3) | .750 | .958 | .875 | .958 | | |

Pair ordering, full evidence (P(score_absent > score_present)): gen .875 (mean diff +52.2
[+27.2, +77.5]); ver .750 (+50.0 [+25.0, +75.0]; 6 exact ties). **H4, restricted evidence
(byte-identical inputs): ver 12/12 exact ties, diff 0.00 [0, 0]; gen P=.417, diff −2.9
[−7.2, +0.7], 8 ties** — no leak; the generic residual is temperature-0 instability.

Where the numbers come from:
- **Full evidence, absent members (gold contradicted, 36 records):** gen — contradicted 18,
  *supported 4*, unresolved 5, not surfaced 9. ver — contradicted 18, unresolved 17, supported 1.
  **Both procedures detect the false attribution in exactly 18/36 (50%).** The verification
  procedure converts the generic's wrong "supported" and silence into "unresolved"; it never endorses
  the false attribution (1 vs 4) but does not catch it more often. The under-accusation is
  item-specific and deterministic: attr-01, 04, 08, 10, 12 (3/3 repeats each) and attr-06 (2/3).
- **Full evidence, present members (gold supported):** gen supported 30, not surfaced 6; ver
  supported 36/36. Neither procedure ever accused a present member (0 unsupported accusations).
- **Restricted evidence (gold unresolved for both members):** gen statuses — unresolved 44,
  contradicted 11, not surfaced 13, supported 4; the 11 accusations come from **two pairs**
  (attr-02 ×6, attr-11 ×5: the judge treats the question field as the complete prompt and
  "contradicts" a data-sheet / spec attribution it cannot see). ver — unresolved 67, contradicted 5,
  all from attr-11. Accusations fall on present/absent members 6/5 and 3/2 — balanced, as identical
  inputs require.
- The pre-registered H1 *accusation-level* rate collapses by construction (every accusation under
  withheld evidence is unsupported → 1.000 for both; none under full → .000): the item-level rate
  and the counts carry the information. A pre-registration lesson, recorded as such.

## Verification family (12 pairs: proposal vs execution claim; claims are unresolved by design)

| endpoint | gen/restr | ver/restr | gen/full | ver/full | ver−gen restr | ver−gen full |
|---|---:|---:|---:|---:|---:|---:|
| target accusations (n) | 0 | 0 | 0 | 0 | | |
| H2 claim-made accuracy | .792 | .986 | .833 | .944 | **+.194 [+.069, +.319]** | **+.111 [+.028, +.208]** |
| H3 status accuracy (claim members) | .806 | 1.000 | .944 | 1.000 | **+.194 [+.028, +.389]** | +.056 [.000, +.139] |
| off-target accusations (on visible slip) | 18 (12) | 11 (6) | 14 (8) | 5 (2) | | |
| mean unfaithfulness score | 19.8 | 8.3 | 20.0 | 8.3 | **−11.5 [−23.6, −2.2]** | **−11.7 [−21.3, −3.3]** |
| repeat agreement | .750 | .958 | .792 | .958 | | |

- **Neither procedure ever accused a proposal or an unrecorded execution claim** (0 target
  accusations in 288 records). The native failure mode this family was built to reproduce —
  "fabricated verification" — did not occur on constructed controls, so H1 cannot discriminate
  here. Either the constructed sentences are cleaner than native traces, or the native accusations
  were driven by material these controls do not contain (long domain-specific traces, richer
  context). This bounds what the controls can say about the native failure.
- Generic H2 errors: **proposal typed as an execution claim 11/36 in both conditions** ("I should
  double-check" read as "I double-checked"), claim not surfaced 4/36 and 1/36. Verification: 1/36 and
  4/36 typed (ver-07 ×3, ver-08 ×2), 0 not surfaced.
- Claim members (gold unresolved): gen said *supported* 3 (restricted) / 1 (full) — endorsing an
  unrecorded check — and missed 4 / 1; ver: unresolved 36/36 in both conditions.
- Off-target accusations are mostly the visible arithmetic slips marked as contradicted computation
  claims (the computation *is* wrong). Reported separately; not counted as false accusations.

## Reading

1. **The verification procedure is better calibrated and far more stable, not a better detector.**
   It says *unresolved* when the evidence cannot decide (93% vs 61% on withheld attributions;
   100% vs 81–94% on unrecorded execution claims), separates proposals from execution claims
   (H2 +.19 / +.11, intervals excluding zero), never endorses a false attribution or an unrecorded
   check under full evidence, and reproduces its own judgment across identical repeats (.958 in
   every cell; zero score spread in three of four full/verification cells) where the generic
   procedure disagrees with itself in a quarter of cells with spreads up to 100.
2. **It does not detect more.** With the complete prompt supplied and lacking the attributed content,
   both procedures call the attribution contradicted in exactly 18/36. The verification procedure's
   failure mode is *abstention on true violations* (17/36 unresolved), the generic's is a mix of
   silence (9) and wrong endorsement (4). A procedure that halves false accusations under withheld
   evidence but catches 50% of real false attributions is not expected to move native AUROC —
   consistent with the repeated pilot's component arm sitting at chance.
3. **Unsupported accusations fell where they existed** (restricted attribution: 11 → 5 of 72,
   from two pairs to one) but 12 pairs cannot resolve it (item-level −.083 [−.250, .000]); elsewhere
   neither procedure made any.
4. The anti-abstention criterion (v1.1 A3) did its job: the procedure's H1 gains are not blanket
   abstention (H2 and present-member H3 are ≥ generic), but the same criterion exposes the
   47% unresolved on gold-contradicted attributions as a real cost.

## Advancement (protocol §6, fixed in advance)

Semantic decisions improved (H2 and H3, intervals excluding zero in several cells, direction
consistent everywhere), so the rule points to: **freeze the procedure and test it on fresh native
examples plus a second judge family, then adapt only compatible components to GRACE.** Two
conditions are attached before that expansion, both within the rule's "inspect the specific failure":

- **Inspect the six under-accusation pairs first** (no inference: read the 17 rationales in
  `responses.jsonl`). Candidate explanation to check: the absent-member note comes from the *same
  named source* with different content, and the judge may treat the shown note as an excerpt rather
  than the complete source the rubric declares. If so, the gold is right but the instruction is not
  landing, and that is fixable in text before any native test.
- **The native test must measure detection of adjudicated real violations, not only unsupported
  accusations.** Otherwise a procedure that merely abstains better will look good on H1 and change
  nothing on native labels. This ties the native follow-on to the human adjudication of the 392-item
  repaired packet, which remains pending and is the only source of adjudicated violations.

No benchmark sweep, no evaluation-partition tuning, no manuscript change follows from this result.

## Limitations

12 pairs per family; constructed, not native; one judge, one provider; temperature-0 repeats measure
instability, not independent evidence; inputs reviewed by the assistant only (sheet at
`data/constructed_controls/v1/review-sheet.md`, human review pending); absent-member gold assumes
the shown note is the complete source (the rubric states the prompt is complete); the H1
accusation-level rate is uninformative by construction in this design; off-target accusations on
visible slips are arguably correct and are only reported.
