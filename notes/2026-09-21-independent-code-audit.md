# Independent code audit of the judge-identity campaign scripts (2026-09-21)

A fresh-context auditor read and re-ran the six analysis scripts written on 2026-09-19/20. Ten
findings; **three overturn conclusions that were reported to the team and written into notes and
the explainer page.** Verification status is stated per finding: *re-verified* means I reproduced
it independently today; *structurally confirmed* means it follows from reading my own code;
*auditor-only* means the numbers are the auditor's and have not been re-derived.

## Findings that change conclusions

**1. The "generator effect does not change rankings" test ran on two of four generators.**
*Re-verified.* `generator_ranking_shift.py` required non-null `soft`/`hard`/`avg_impact`. Those
exist only for the two open-weight generators (Qwen 326, Llama 307; gemini 0, gpt-4o-mini 0), so the
633-row subset contains **only the two generators that sit together in the high group** — the
population where the effect is smallest. I knew step-removal features were open-weight-only (it is
in the step-1 spec) and wrote the filter anyway.

On the full four-generator population, ten judges, pair-weighted within-generator AUROC:

| blind regime | pooled | rank | within-generator | rank |
|---|---|---|---|---|
| gpt-4o-mini | 0.679 | 1 | 0.634 | 2 |
| gpt-4o | 0.671 | 2 | 0.643 | 1 |
| gpt-5.2 | 0.655 | 3 | 0.630 | 3 |
| Llama-3.1-8B | 0.643 | 4 | 0.601 | 6 |
| Qwen3-8B | 0.637 | 5 | 0.623 | 4 |
| Qwen2.5-7B | 0.635 | 6 | 0.614 | 5 |

Spearman 0.939 with 4 of 45 inversions (blind); 0.976 with 2 of 45 (correct). **Every judge's
blind-regime AUROC is inflated by pooling across generators, by 0.014 to 0.045**, the leader changes,
and Llama-3.1-8B drops from 4th to 6th. Rank correlation stays high, so "leaderboards rank generator
style" remains too strong — but "nearly inert in ranking space" was wrong, and the withdrawal I
issued on 2026-09-20 rested on an invalid test. **The blind-regime ceiling within generator is
about 0.64, not 0.679.**

**2. Self-preference: "absent (Verified)" and "clean kill" are not supported.**
*Structurally confirmed; interval numbers auditor-only.* The script contains no
difference-in-differences code; I computed -4.89 / -9.26 / +7.72 by hand with no interval. The
non-self control sets double-count models (gpt-5.2 three times; for the Qwen and Llama rows,
gpt-4o-mini three times via `mini`/`promptB`/`cotonly`), and some controls are themselves
self-judges for traces inside the comparison pool. With a question-clustered bootstrap, the
pre-registered Bonferroni 98.33% intervals, and controls limited to the seven models that wrote no
traces, the auditor gets:

| self-judge | DiD | 98.33% CI |
|---|---|---|
| gpt-4o-mini | -4.70 | [-9.22, -0.29] |
| Qwen2.5-7B | -7.41 | [-14.26, -0.62] |
| Llama-3.1-8B | +13.83 | [+7.15, +20.56] |

All three exclude zero. But among 28 placebo cells formed by never-self judges, 29% also exclude
zero (median |DiD| 4.55, max 20.5), and cells at least as large as each self cell number 12, 5 and 2
of 28. **Defensible statement: own-generation effects are detectable, differ in sign, and cannot be
told apart from ordinary judge-by-generator interaction. This design cannot identify
self-preference.** "No consistent self-preference" stands; "absent" does not. I also reported 95%
intervals where the spec fixed Bonferroni 0.0167.

**3. The generator-vs-label ratio was not like-for-like, and the question-only control does not
calibrate its floor.** *Auditor-only, but consistent with my own variance decomposition of the same
day.* (i) A permutation null for max-minus-min gives 4.5 to 6.7 points for real judges, not 1.1: the
question-only arm reads 1.05 because its within-cell SD is 9.8 against 17-25 and 71% of its
questions are score-identical across generators. "18x to 29x the floor" is really **2.3x to 5.6x**.
Olmo-3-7B's spread is noise (p = 0.29); the other nine judges p <= 0.005. (ii) Label effect and
spread were computed on different question sets (86 vs 126, 67 shared) while the docstring says
"same questions". (iii) The label effect is confounded by generator composition — a score carrying
only the generator offset manufactures a 3.2 to 5.0 point "label effect". (iv) The spread is
attenuated because a trace is included in its own cell mean. In a symmetric two-way within-question
model the range-to-label ratio is 2.8 (gpt-4o-mini), 2.4 (gpt-4o), 10.6 (gpt-5.2). **"Generator at
least comparable to label" survives for strong judges and the old ratios understated it there; the
"1.1 floor", the "18-29x" figure and the Olmo row do not survive.**

## Findings that change numbers but not conclusions

4. **Parse-rate filters accepted a partial in-flight arm.** *Re-verified in part* (I saw 0.553/0.535
   become 0.568/0.524). Rate was scored/present rather than scored/1304, so
   `qwen25_3b_instruct` entered at 594-595 rows. The committed `generator_identity.json` holds it at
   n_questions 40, spread 26.6; the complete arm gives 86 and 16.0. The campaign summary's "2.2x"
   came from the partial arm; the final value is 2.3x. `self_preference_analysis.py` still uses the
   `< 1300` cutoff I called a bug elsewhere, so Olmo — the spec's only unrelated-family control —
   is missing from `results.json`.
5. **Mixed sign conventions** in `generator_ranking_shift.py`: `soft`/`hard` at -1 (intended
   direction) but `avg_impact` at +1 (the paper's inverted direction); `dag_lin` mirrored against
   `audit_corrected.py`. With the paper's signs the conclusion holds and the numbers move.
6. **The note contradicts its own artefact.** "Every real judge, ratios 1.06 to 5.90": Olmo reads
   1.01, 0.52, 0.64. "Partition without exception": it fails in three committed seed arms
   (`llama3_8b_s0`, `olmo3_7b_s0`, `qwen25_7b_s2`), greedy margins at the boundary are 0.5-0.6
   points, and the question-only control satisfies the partition too. "19.5 to 31.7 across nine
   judges" is the range over the first eight arms; across nine distinct judges it is **8.1 to 29.1**.
7. **"3.5x among the seven at 7B and above" omitted Olmo-3-7B, which is a 7B model.** With it the
   ratio is 2.2x. I excluded it by calling it a floor case, which is selection on the outcome.
8. **Noise floor.** The hard-coded 0.023 is the blind-regime API delta only; the correct-regime API
   delta is 0.013, *below* the local median seed spread of 0.014, so "local sampling is less noisy
   than the API at temperature 0" holds in one regime only. My "greedy below all seeds" oddity is
   wrong for Qwen2.5-3B-Instruct (greedy is inside its seed range) and overstated for Llama-3.2-3B;
   the one genuine outlier is Llama-3.1-8B blind, which the note does not mention.
9. **Ledger.** Family sizes were counted from the ledger's own 52 rows; three tests appear twice as
   mirrors; interval-less family members are omitted. No verdict flips, one fragile case
   (answer-tracing regime gap, z = 2.67). "Every null below 2.1" skips question-only/correct at
   z = +2.10. **Conceptual error:** I called the BonaFide judge inversion "the one pre-registered
   headline". The registered H1 was the *opposite* — judge above chance. The 0.419 is the failure of
   a registered hypothesis under a registered analysis, not a registered claim that was confirmed.
   The correction family argument still applies to the analysis; the framing was wrong.
10. **Composition gaps used size weights**, not the pair weights (n1 x n0) the AUROC decomposition
    implies. With pair weights the correct-regime gaps roughly halve. "Control floor ±1.03" was a
    transcription slip; the artefact says 0.82 (blind) and 1.74 (correct).

## Checked and fine

No script reads the inverted `correct` field; positive class is `ft in (2,4)` throughout; the
`ft=0` row is excluded. The AUROC implementation and the clustered bootstraps are correct, and
paired quantities share draws. `matched_offset` has no leakage or double counting. Four of six
committed outputs reproduce byte-for-byte. The ledger's z conversion, Bonferroni thresholds and all
52 estimate-interval triplets match the manuscript. The length analysis (7.7% / 16.1% / 15.8% /
7.9%) reproduces exactly, though it has no committed code and rests on 38 gemini-llama pairs.
The greedy repeat is byte-identical — which is what determinism predicts but also what a file copy
would look like; the Aquaman run log shows `qwen3_8b_greedy2` starting 00:19:18 and phase 1 ending
00:41:15 on 2026-09-20, a genuine 22-minute run, but **that log is not committed**.

## The pattern

Seven of ten findings share one cause: **a consequence or summary sentence was written before, or
without, the computation that would check it** — and three of them were already-corrected claims
whose correction was itself unchecked. Negative controls and assertions caught real bugs this week
(the question-only arm, the parse-rate check); hand-computed summary numbers and prose ranges are
where the errors concentrated. Rule going forward: no number enters a note unless a committed script
printed it, and no range is quoted without the script that enumerates it.
