# Verification of the GRACE checker repair

Commits `36445ad` and `512d866` replace the saved correctness labels and update
the manuscript. The new reported arithmetic reproduces exactly conditional on
those labels, but the labels still contain systematic semantic errors and the
repository analysis scripts still run the old checker. The repair is incomplete.

Independent reconstruction of the checker from its recorded implementation
reproduces all 437 saved labels and the 277/160 split. Using the saved NLI cache
and 2,000 paired question-bootstrap replicates reproduces:

| Quantity | Recomputed result |
|---|---|
| Context-NLI unsupported-rate regime difference | +.046455, CI [−.144509, .240687] |
| Inverted mean-entailment regime difference | +.090965, CI [−.100424, .295179] |
| Prior-step NLI-rate regime difference | +.006781, CI [−.199915, .213662] |
| Entanglement lift across five rules | 1.169–1.670 |

These reproduce the new manuscript's numbers; they do not independently validate
the correctness field used to create the strata. Four concrete remaining errors
in `results/grace_correctness_fixed.json` are:

| Trace ID | Reference | Why the saved correct label is unsupported |
|---|---|---|
| `grace_test_musique_875ff9b4` | October 28, 2012 | Response says October 29, 2012; token overlap passes the .6 F1 threshold despite the wrong day. |
| `grace_test_musique_85559bbb` | 1915 | Response mentions 1915 for a different country and concludes that the country asked about did not enter the war. Containment accepts it. |
| `grace_test_wiki2multihop_74f895f8` | Me Agtsom | Response says the requested grandfather cannot be determined, while mentioning the reference in its explanation. Containment accepts it. |
| `grace_test_wiki2multihop_6a38af19` | Ottokar I of Bohemia | Response mentions the person but follows the wrong family relation and concludes that the grandfather cannot be specified. Containment accepts it. |

The checker therefore has defects beyond imperfect alias coverage: high token
overlap can accept an incorrect value, and mentioning the answer is mistaken for
asserting it as the answer. Fourteen inspected random judgments do not validate
these decision branches. The reported 63.4% is the fraction this checker calls
correct, not a measurement of the checker's accuracy against independent gold.
The previous "52 spurious matches" count also should not be read as 52 verified
errors: nonidentical answers sharing a first character can still be equivalent.

Implementation repair is also unfinished. Both `scripts/grace_regime_test.py`
and `scripts/grace_regime_analysis.py` retain the first-character fallback and
do not load `grace_correctness_fixed.json`. The tracked
`results/grace_regime_results.json` still contains the old 246/191 split. The
new calculation was executed through session commands rather than integrated
into the saved analysis pipeline. A normal rerun reproduces the old bug.

Before treating the revised claims as established, implement a shared task-aware
checker, retain its decision reasons and unresolved cases, validate free-response
answer equivalence, and regenerate versioned analysis outputs from those labels.
Do not tune a similarity threshold to preserve the desired conclusion. Even with
valid labels, an interval spanning zero does not prove equivalent strata or that
the original effect is unique to FaithCoT. Pooled NLI correlations remain
independent of correctness and continue to stand.

**Correction to the independent audit's partition count.** Claude is right that
the reconciliation touched 204 of the original 807 evaluation responses across
156 question clusters. The earlier independent count of 211/161 incorrectly
included seven correct-answer responses outside the 1,113 incorrect-response
population defining the 306/807 split. These exposed clusters cover 397 of the
807 evaluation responses. Across all 284 scored responses, the correct categories
are 73 development, 204 evaluation, and seven outside that split. This correction
does not change the 150-case paired AUROCs or the finding of partial exposure.

The independently recomputed common-population BonaFide comparison remains
.319/.400/.367/.331. The upstream score-direction issue remains an interface
inconsistency with unverified impact on the published AUROC. The reconciliation
script and its older note still contain the earlier unmatched table and .68
CoT-level description, despite the session accepting the corrections verbally.

Reproduction code, complete error examples, hashes, and numerical results are
stored in the independent review archive at `grace-repair-audit-2026-09-13/`.
No new inference or human annotation was performed in this verification.
