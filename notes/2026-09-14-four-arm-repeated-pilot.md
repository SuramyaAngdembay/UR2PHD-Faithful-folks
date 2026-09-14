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
