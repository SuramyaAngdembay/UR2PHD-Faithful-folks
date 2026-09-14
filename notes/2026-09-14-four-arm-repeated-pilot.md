# Four-arm repeated judge pilot — development results, 2026-09-14

Run `results/diagnostic_v2/pilot-4arm-rep3c`, config `diagnostic-v2.1-pilot-r2`, model pinned
`gpt-4o-2024-08-06`, temperature 0. **70 dev responses x 4 arms x 3 identical repeats = 840
requests, all completed.** 8 transient 429s, each on a distinct request at attempt 1, all resolved
on retry; no request missing. Repeats are replicate measurements of one response, never additional
examples. **Development partition only; exploratory; no method claim.**

Design: evidence (restricted / full legitimate) x rubric (generic / component).
Label support is thin and asymmetric: 70 responses, **60 unfaithful / 10 faithful**, so every
AUROC interval below is wide and none should be read as a point estimate.

## 1. Native-label discrimination (mean of 3 repeats, question-clustered CI)

| arm | | AUROC | 95% CI |
|---|---|---|---|
| A1 | restricted + generic | 0.217 | [0.103, 0.348] |
| B1 | full evidence + generic | 0.259 | [0.136, 0.396] |
| A2 | restricted + component | **0.511** | [0.314, 0.708] |
| B2 | full evidence + component | 0.445 | [0.244, 0.653] |

Both generic arms are **significantly below chance** (CIs exclude 0.5) -- the inversion reproduces
inside this controlled design. Both component arms are indistinguishable from chance. The
component rubric therefore removes the inversion but does not produce detection. Adding full
evidence does not help either rubric (B1 vs A1 overlaps; B2 vs A2 overlaps, point estimate lower).

## 2. Repeat disagreement at temperature 0

| arm | all 3 identical | mean spread | max spread | binary flip @50 |
|---|---|---|---|---|
| A1 | 68.6% | 7.7 | 60 | 8.6% |
| B1 | 74.3% | 5.7 | 60 | 5.7% |
| A2 | 74.3% | 10.4 | 100 | 10.0% |
| B2 | 68.6% | 10.4 | 100 | 5.7% |

**Roughly a quarter to a third of identical requests disagree**, and 6-10% flip the binary verdict
at a 50 threshold. Component arms show the larger spreads (max 100 = complete reversal on identical
input). Any single-call judge number in this project carries this instability.

## 3. Abstention

Only the component rubric ever abstains, and rarely: A2 6/210 (2.9%), B2 0/210, generic arms 0/210.
The `insufficient_evidence` option exists in the schema and is almost never used.

## 4. Allegation grounding (lexical span check)

| arm | evidence items | responses with >=1 unmatched quote |
|---|---|---|
| A2 | 245 | 50 / 210 (23.8%) -- 19 trace, 38 context |
| B2 | 260 | 27 / 210 (12.9%) -- 20 trace, 10 context |

Generic arms cite no evidence at all, so they cannot be checked this way.

**The important pattern:** unmatched-quote responses score far higher than matched ones --
A2 81.5 vs 46.4, B2 82.0 vs 52.3. **The judge's most confident accusations are
disproportionately the ones whose supporting quote cannot be found in the evidence it was given.**
This is a lexical span check only; a matching quote still does not establish that it supports the
allegation, which needs independent human review.

Component verdicts pooled (A2+B2): reliance `supported` 416/420 -- it asserts identifiable reliance
almost always; `false_process_claim: supported_violation` 251/420; abstention codes rare throughout.

## Reading

On this development sample the component rubric changes the *failure mode* rather than fixing it:
it moves a significantly-below-chance detector to chance, while emitting confident accusations that
are disproportionately ungrounded. A higher AUROC obtained this way would not be a better detector.
Independent human checking of the allegations, not more scoring, is the next requirement.

Caveats: 10 faithful responses; development partition; one model, one provider; lexical grounding
only; repeats measure instability, not independent evidence.

## Analysis defect found and corrected during this analysis

My first pass reported "100% of component responses have >=1 invalid span". `_quote_validation` is
a dict (`all_quotes_match`, `issues`, `note`), so a truthiness test on it was always True. Correct
figures are 23.8% / 12.9%. Same class of error as the GRACE answer checker: a field used without
inspecting its structure.

## CORRECTIONS from the independent audit (notes/2026-09-14-repeated-pilot-independent-audit.md)

Three readings above are corrected; the raw numbers all reproduce.

1. **"Removes the inversion without producing detection" understates the result.** The correct
   statistic is the *paired* contrast: **A2 − A1 = +0.293 [+0.093, +0.502]**, a significant relative
   improvement under restricted evidence. A2's own interval still includes chance, so it is a
   relative gain, not a validated detector — but "equivalent to chance" overstates the negative just
   as "works" would overstate the positive. Evidence-access contrasts are unresolved (B1−A1 +0.042
   [−0.015, +0.107]; B2−A2 −0.066 [−0.159, +0.015]); separate-arm interval overlap establishes
   neither equality nor absence of effect.
2. **"Codex's n=6 lead does not survive at n=70" conflates two statistics.** The earlier 0.917 was
   *within-pair ordering* on a different matched sample sharing only three response IDs with this
   one; 0.511 is pooled positive/negative ordering. This pilot is not a formal replication of that
   result, and the earlier figure remains unvalidated rather than refuted.
3. **My quotation counts must not be read as fabrication.** Of 57 failed quote *fields* in A2:
   7 whitespace-only, 4 case/Unicode/Markdown, 3 ordered excerpts joined by ellipsis, 24 exact text
   present in a *different* supplied field, 11 judge instructions quoted as record evidence, 8 not
   located. B2 similarly. Most are presentation or wrong-field attribution; only the residual needs
   semantic inspection. These are not a hallucination rate, and none of them certifies whether the
   allegation follows from the cited text. The score gap (81.5 vs 46.4) is descriptive only.

Also noted: post-hoc SimpleQA-only sensitivity (34 responses) gives A1/B1/A2/B2 =
.308/.373/.631/.569, A2 paired gain +0.323 [0.059, 0.614] — so the pooled point estimate is not a
universal property of the procedure. All ten faithful responses are SimpleQA.
