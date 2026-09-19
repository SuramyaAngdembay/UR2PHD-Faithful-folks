# P-hacking and research-integrity failure modes — reference synthesis (2026-09-19)

Compiled for the project self-audit. Every bibliographic record below was checked against Crossref
or a publisher/proceedings page. Items that could not be verified are flagged at the end. Used by
`2026-09-19-holdout-and-phacking-audit.md`.

## Core failure modes

**Researcher degrees of freedom.** Simmons, Nelson & Simonsohn (2011), *False-Positive Psychology*,
Psychological Science 22(11) 1359–1366, doi:10.1177/0956797611417632. Their simulation: combining
four common freedoms (two DVs, optional stopping, a gender covariate, dropping a condition) raises
the false-positive rate at p<.05 from 5% to **60.7%**. Crucially: "This exploratory behavior is not
the by-product of malicious intent, but rather the result of (a) ambiguity in how best to make these
decisions and (b) the researcher's desire to find a statistically significant result." Six author
requirements (stopping rule declared; ≥20/cell or justification; list all variables; report all
conditions including failed manipulations; report results with excluded observations included;
report results without covariates). Reviewer guideline worth internalising: *"Underpowered studies
with perfect results are the ones that should invite extra scrutiny."* They concede their fix cannot
address the file drawer.

**Garden of forking paths.** Gelman & Loken, unpublished manuscript dated 14 Nov 2013
(sites.stat.columbia.edu/gelman/research/unpublished/p_hacking.pdf); peer-reviewed counterpart
*The Statistical Crisis in Science*, American Scientist 102(6) 460, doi:10.1511/2014.111.460. The
load-bearing contribution is a four-procedure taxonomy: (1) a single pre-chosen test; (2) a test
chosen from a **pre-registered** set; (3) **researcher degrees of freedom without fishing** — one
test computed, in an environment where different data would have produced a different test; (4)
fishing. *"Our claim is that researchers are doing #3, but the confusion is that, when we say this,
researchers think we're accusing them of doing #4."* Diagnostic: *"if the data analysis protocol
really were decided ahead of time, why not preregister it?"* Preferred remedy where preregistration
is infeasible: pre-publication replication, and analysing **all** relevant comparisons rather than
the significant ones.

**HARKing.** Kerr (1998), Personality and Social Psychology Review 2(3) 196–217,
doi:10.1207/s15327957pspr0203_4. "Presenting a post hoc hypothesis in the introduction of a research
report as if it were an a priori hypothesis." **Correction to the common account: Kerr did not coin
SHARKing or CHARKing** (Wikipedia attributes them to him; that is wrong). His framework is a 3×2
table with five named Versions (Pure HARKing; + Straw Man, creating "an illusion of competitive
hypothesis testing"; Suppress Loser Hypotheses; Post Hoc Plausibility; Empirical Inspiration).
CHARKing/RHARKing/SHARKing are Rubin (2017), Review of General Psychology 21(4) 308–320,
doi:10.1037/gpr0000128; THARKing is Hollenbeck & Wright (2017), Journal of Management 43(1) 5–18,
doi:10.1177/0149206316679487. Kerr is explicit that detection is structurally hard — "A judgment of
HARKing involves challenging what somebody claims he or she was thinking in the past" — and names
**hindsight bias** as the mechanism that makes it feel honest. His individual remedy (fn. 9) is the
ancestor of preregistration: keep "written journals recording the temporal development of our
theoretical ideas." Distinct from p-hacking: HARKing operates at the **reporting** layer and need
not change any number; it conceals the forking path that p-hacking walks.

**Selective reporting / inflation bias.** Head, Holman, Lanfear, Kahn & Jennions (2015), PLoS
Biology 13(3) e1002106. Text-mined p-value distributions; p-hacking signature = excess in
0.045<p<0.05 vs 0.04<p<0.045. Found detectable p-hacking but concluded its effect is "weak relative
to the real effect sizes." **Contested** by Bishop & Thompson (2016), PeerJ 4 e1715 — their ghost-
variable simulation showed p-hacked data can produce a *flat* or even *left-skewed* curve, so
"the absence of a bump in the p-curve is not indicative of lack of p-hacking." Do not cite the 2015
prevalence figure without the 2016 critique.

## Diagnostic and robustness toolkit

- **P-curve**: Simonsohn, Nelson & Simmons (2014), JEP:General 143(2) 534–547, doi:10.1037/a0033242.
  Valid only on hand-selected sets meeting three criteria (tests the hypothesis of interest; uniform
  under the null; statistically independent). Requires a p-curve disclosure table.
- **Specification curve analysis**: Simonsohn, Simmons & Nelson (2020), Nature Human Behaviour 4(11)
  1208–1214, doi:10.1038/s41562-020-0912-z. Three steps, and step 3 — **joint inference across all
  specifications** — is what separates it from a hand-picked robustness table.
- **Multiverse analysis**: Steegen, Tuerlinckx, Gelman & Vanpaemel (2016), Perspectives on
  Psychological Science 11(5) 702–712. Varies **data-construction** choices rather than analysis
  choices.
- **Many-analysts**: Silberzahn et al. (2018), AMPPS 1(3) 337–356. 29 teams, one dataset, one
  question; odds ratios 0.89–2.93. The empirical measurement of the forking-paths space.
- **Type-M/Type-S**: Gelman & Carlin (2014), Perspectives on Psychological Science 9(6) 641–651.
  Conditional on significance in low power, magnitude is systematically overestimated.
- **Interaction fallacy**: Gelman & Stern (2006), The American Statistician 60(4) 328–331,
  doi:10.1198/000313006X152649. Directly governs any "works in A but not B" claim.
- **Checklist**: Wicherts et al. (2016), Frontiers in Psychology 7:1832 — 34 enumerated degrees of
  freedom across five research phases.

## Machine-learning strand

- **Adaptive data analysis**: Dwork, Feldman, Hardt, Pitassi, Reingold & Roth (2015), STOC 2015
  117–126, doi:10.1145/2746539.2746580. **Theorem 3: sample complexity scales with rounds of
  adaptivity r, not with the number of queries m** — n₀ = O(r log m / τ²). Thresholdout (NeurIPS 28,
  arXiv:1506.02629) is the reusable-holdout mechanism; the *Science* version (349(6248) 636–638) is
  framing only.
- **⚠️ Adaptive overfitting — the most miscited result here.** Recht, Roelofs, Schmidt & Shankar
  (2019), ICML 2019 PMLR 97 5389–5400, and the CIFAR-10 companion (arXiv:1806.00451), both concluded
  **against** adaptive overfitting: "the relative order of models is almost exactly preserved on our
  new test sets… Adaptivity is therefore an unlikely explanation for the accuracy drops." Slopes >1.
  The transplantable diagnostic: **a drop in absolute numbers is not evidence of test-set mining —
  scrambled ordering is.** See also Roelofs et al. (2019), NeurIPS 32: "little evidence of
  substantial overfitting," with risk concentrated in small effective test sets and non-i.i.d.
  splits.
- **Leakage taxonomy**: Kapoor & Narayanan (2023), Patterns 4(9) 100804. Eight types in three
  groups — L1 no clean separation (incl. L1.4 duplicates across partitions), L2 illegitimate
  features, L3 test set not from the distribution of interest (**L3.2 non-independence from group
  structure** is the one that bites clustered data). Remedy: model info sheets — "none of these
  errors could have been caught by reading the papers."
- **Contamination ≠ exploitation**: Magar & Schwartz (2022), ACL 2022 Short 157–165,
  doi:10.18653/v1/2022.acl-short.18 — contaminated models sometimes "memorize the contaminated data,
  but do not exploit it." Black-box detection: Oren, Meister, Chatterji, Ladhak & Hashimoto (2024),
  ICLR 2024, arXiv:2310.17623 — exchangeability/ordering test with exact false-positive guarantees,
  no weights or pretraining data needed.
- **Tuning budget as a confound**: Dodge, Gururangan, Card, Schwartz & Smith (2019), EMNLP-IJCNLP
  2185–2194 — a single test number conflates method quality with search budget; report expected
  validation performance as a function of budget. Lucic et al. (2018), NeurIPS: "improvements can
  arise from a higher computational budget and tuning more than fundamental algorithmic changes."
- **Splits**: Gorman & Bedrick (2019), ACL 2019 2786–2791 — "we fail to reliably reproduce some
  rankings when we repeat this analysis with randomly generated training-testing splits."
- **Multi-dataset multiplicity**: Dror, Baumer, Bogomolov & Reichart (2017), TACL 5 471–486,
  doi:10.1162/tacl_a_00074 — **replicability analysis** is the correct object for "significant in k
  of m datasets," not per-cell p-values.
- **Power in NLP**: Card, Henderson, Khandelwal, Jia, Mahowald & Jurafsky (2020), EMNLP 9263–9274.

## LLM-as-judge validity

- Zheng et al. (2023), NeurIPS D&B, arXiv:2306.05685 — position, verbosity, self-enhancement biases
  and limited reasoning. Their ~80% judge–human agreement is **ceiling-setting** (human–human is
  also ~80%) on open-ended preference, not a correctness claim.
- Panickssery, Bowman & Feng (2024), NeurIPS 2024, arXiv:2404.13076 — **self-preference**, shown
  causally, not merely correlationally. Implication: judge/subject family overlap is a live confound.
- Bavaresco et al. (2024/2025), JUDGE-BENCH, arXiv:2406.18403 — judge reliability measured on
  human-written text **does not transfer** to model-generated text.
- Wu & Aji (2025), COLING 297–312 — injected-flaw study; **factual errors were rated more favourably
  than shortness or grammatical errors.**

## Corrections to commonly-repeated claims

1. Kerr (1998) did **not** coin SHARKing/CHARKing (Rubin 2017 did); THARKing is Hollenbeck & Wright.
2. Recht et al. concluded **against** adaptive overfitting; citing them as evidence of test-set
   mining inverts their finding.
3. Blum & Hardt, *The Ladder*, is **ICML 2015** (PMLR v37 1006–1014), not 2016.
4. Dodge et al. C4 documentation is **EMNLP 2021**, not 2020.
5. Head et al.'s prevalence estimate is contested by Bishop & Thompson (2016).

## Unverified — do not cite without checking

Gelman & Loken American Scientist page range (Crossref records start page 460 only); the full
12-item Kerr cost list (verified in part from p. 212, remainder from a secondary source); Head et
al.'s "~37% of meta-analyses" figure; Dwork et al. NeurIPS 2015 page numbers (BibTeX `pages` is
empty); Kapoor & Narayanan paper count (arXiv says 329, published version widely cited as 294);
Sculley et al. "Winner's Curse?" quotations.

## The 55-item self-audit checklist

Grouped A–J: (A) endpoints and hypotheses; (B) sample definition, exclusions, stopping; (C) outcome
and metric selection; (D) analysis specification; (E) multiplicity across the contrast family;
(F) holdout and test-set hygiene; (G) measurement instrument (judges, probes); (H) compute budget
and tuning; (I) reporting and narrative; (J) the honest residual — *"write down the one claim in the
paper you would least want a referee to probe, and say why."*

Items settled for this project are recorded in `2026-09-19-holdout-and-phacking-audit.md` §5.
