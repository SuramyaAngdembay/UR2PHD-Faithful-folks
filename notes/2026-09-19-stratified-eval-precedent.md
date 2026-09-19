# Novelty sweep: the correctness-stratification methodology is NOT novel (2026-09-19)

**Historical assessment: material claims below are superseded by the
[independent audit](2026-09-19-stratified-novelty-independent-audit.md).** In
particular, do not reuse the interpretations of F1 collapsibility, the selected
.726 AUROC as a full-population result or comparison to F1, BonaFide as entirely
correct, correctness as constitutive from a 2x2 taxonomy, or extension of our
own preprint as self-plagiarism. Original text is preserved for provenance.

Prompted by my own proposal that restratifying FaithCoT-Bench's detector ranking would be "a
measurement standard that changes published conclusions." **That framing was wrong.** Every element
of the methodology is established prior art in three separate literatures, and **none of it is cited
in `paper/arr/ur2phd.bib`** (41 entries; verified zero hits on spectrum / Ransohoff / Mulherin /
Janes / Pepe / covariate-adjusted / case-mix / Simpson / xAUC / Kallus / Borkan / disaggregated /
Barocas / Buolamwini / Geirhos / Zech / van Elteren / Suresh).

## What is prior art — and must be cited rather than claimed

**The phenomenon (1978).** Ransohoff & Feinstein, "Problems of spectrum and bias in evaluating the
efficacy of diagnostic tests," *NEJM* 299(17):926–930, doi:10.1056/NEJM197810262991705. Sensitivity
and specificity are properties of *a test in a case mix*, not of a test.

**The remedy we proposed (2002).** Mulherin & Miller, "Spectrum bias or spectrum effect? Subgroup
variation in diagnostic test evaluation," *Ann Intern Med* 137(7):598–602. Verbatim: *"subgroup
variation is not a bias if appropriate analyses are conducted … Heterogeneity can be addressed with
relatively simple stratification procedures."* They explicitly prescribe stratified sensitivity/
specificity, stratified likelihood ratios and **stratified ROC curves**. They also prefer "spectrum
*effect*" to "spectrum *bias*" for mere heterogeneity.

**The AUROC decomposition is Kallus & Zhou 2019, Proposition 1.** "The Fairness of Risk Scores
Beyond Classification: Bipartite Ranking and the xAUC Metric," *NeurIPS 32*, arXiv:1902.05826:
`AUC = Σ_b' P(A=b'|Y=0) Σ_a' P(A=a'|Y=1) P(R₁^{a'} > R₀^{b'})` — the within-stratum / cross-stratum
split by the law of total probability. **If our paper writes this decomposition down, it is theirs.**
NLP-native equivalent: Borkan et al., WWW'19, Subgroup AUC / BPSN / BNSP — standard in toxicity
classification since 2019. Statistical ancestor: van Elteren (1960) stratified Wilcoxon.

**The formal estimand.** Janes & Pepe, "Adjusting for covariate effects on classification accuracy
using the covariate-adjusted ROC curve," *Biometrika* 96(2):371–382 (2009); Pepe (2003) ch. 6.
Covariate-*specific* ROC = per stratum; covariate-*adjusted* ROC (AROC) = the single adjusted
summary. Known bias direction: the pooled ROC is **over-optimistic** relative to stratum-specific
ROCs when the covariate is associated with the outcome.

**Ranking reversal under aggregation.** Simpson's paradox; Prost et al. arXiv:2210.07755 (per-user
vs aggregated recommender fairness give "opposite conclusions"); Mishra & Arunkumar, *AAAI* 2021
35(15):13561–13569 (difficulty reweighting **changes model rankings**); Suresh & Guttag, EAAMO'21,
name it **aggregation bias** and **evaluation bias**.

**Already applied to a learned detector.** Tseng et al., *Eur Heart J Digit Health* 2(4):561–567
(2021): CNN AUC 0.91 → 0.86 moving from extreme spectrum to full spectrum.

**Concurrent and close.** Stowe & Patil, "Spotlights and Blindspots: Evaluating Machine-Generated
Text Detection," arXiv:2604.16607 (Apr 2026, preprint): detector "model rankings variance ranges
from 0.77 to 15.25 over 15 models" across metrics and label distributions. Detector-evaluation
ranking instability, four months before our v1.

## What actually survives as novel

1. **The empirical fact, not the method.** Correctness is the dominant covariate on FaithCoT; the
   purpose-built signals largely re-detect it; detection splits into a detectable correct-answer
   regime and an at-chance incorrect-answer regime holding ~69% of annotated unfaithfulness. Frame
   as *applying a known diagnostic and finding something surprising*.
2. **The genuinely thin point — the covariate is CONSTITUTIVE, not a nuisance.** In the classical
   framing the covariate (age, severity) is exogenous and AROC adjusts it away. Here FaithCoT's
   label taxonomy *is* the 2×2 of {faithful, unfaithful} × {correct, incorrect}: correctness is
   entangled with the construct's definition, so "adjust it out" is not obviously right and AROC is
   not obviously the right estimand. **When is stratification the correct remedy, and when does the
   construct itself need redefining?** That question is much less covered than the machinery.
3. **A reporting standard instantiated for this subfield**: mandatory correctness-stratified AUROC
   plus "answer-incorrectness alone" as a required baseline control (the Zech et al. 2018 move —
   show the trivial confound can do it). Positioned as an instantiation of Barocas et al. (AIES'21)
   and Mitchell et al. (FAT*'19), not as an invention.
4. An exhibited reordering among published detectors, **if** we obtain their per-instance outputs —
   reported as "aggregation bias manifests here," citing Prost and Mishra & Arunkumar.

## Terminology to adopt

"Spectrum effect" (heterogeneity) vs "spectrum bias" (unrepresentative mix). "Covariate-specific
ROC" / "stratified AUROC" for per-stratum; "covariate-adjusted ROC (AROC)" only for the specific
Janes–Pepe estimand. "Within-group / cross-group (xAUC)" for the decomposition. "Aggregation bias"
or "Simpson's paradox" for the reversal — **not** "metric inversion," which we already use for the
soft_faithfulness polarity result and would confuse readers. Hazard: in ML venues "spectrum bias"
collides with *spectral* bias (Rahaman et al., ICML 2019); gloss on first use.

## Action

`paper/arr/ur2phd.bib` needs these additions before the ARR submission. This is a live risk: the
paper is already public (arXiv:2607.23458 v2, 2026-08-23) and writes the decomposition without
Kallus & Zhou and prescribes stratification without the diagnostic-testing literature. A referee
from clinical epidemiology or FAccT recognises the gap on sight.

---

# Part 2 — CoT-specific sweep (2026-09-19)

## The finding that reframes the whole proposal: half is already OUR OWN public work

arXiv:2607.23458 **v2** contribution (1) already reads: *"a correctness-stratified evaluation
protocol for instance-level faithfulness detection … with the finding that aggregate detector
scores are largely composition."* So the stratified-protocol leg is **self-published**. Presenting
it as fresh would be self-plagiarism a reviewer finds in one search.

But `reorder`, `leaderboard`, `inflat` and `exact decomposition` return **zero hits in v2** — they
appear only in the unpublished `paper/arr/main.tex`, whose contribution (1) claims *"exact
composition decomposition of aggregate scores, and the demonstration that detector rankings reorder
under composition alone."* **The reorder leg is the genuine increment over our own public record,
and it is the only leg novel against the field.**

## VERIFIED hook: FaithCoT-Bench measured the confound, used the wrong statistic, and dismissed it

Their Appendix B.1 reports φ = 0.286 and mutual information 0.057, concluding *"only weak
association between correctness and faithfulness."* Recomputed directly from their released
`faithcot.zip` (1,198 labelled traces with parseable answers):

| quantity | value |
|---|---:|
| P(incorrect \| unfaithful) | **0.661** |
| P(incorrect \| faithful) | **0.208** |
| **AUROC of incorrectness alone as an unfaithfulness detector** | **0.726** |
| φ (2×2: 236 / 121 / 175 / 666) | **0.436** |

Two things follow. **(a)** φ on the current release is 0.436, not the 0.286 their appendix reports —
consistent with the release-revision history our own paper already documents (release census 1,303
vs the paper's 1,183). **(b)** More important than the φ discrepancy: **a correlation coefficient is
the wrong statistic for a detection confound.** Converted to the units their own Table 1 is scored
in, incorrectness alone reaches AUROC 0.726 — competitive with or above most of their eleven
detectors. *The benchmark measured the confound, summarised it with a statistic that cannot express
detector-equivalent strength, and concluded it was negligible.* That is a much sharper framing than
"prior work was unstratified."

**Caveat on my computation:** correctness is exact-string match of `parsed_final_answer` against
`label`; 106 of 1,304 labelled traces lacked a parseable answer and were dropped. For free-response
items (HLE-Bio) exact match under-counts correctness. Given this project's history with answer
checkers (the GRACE incident), this needs a proper checker before it appears in the paper.

## Second hook, from their own Table 1 — needs no data from them

Their Observation ❶ asserts *"LLM-as-judge methods consistently outperform alternatives, while
logit-based methods perform the worst."* Yet in their own table: HLE-Bio/LLaMA-3.1 — Answer Tracing
(logit-based) **76.2** vs Step-Judge 69.2; HLE-Bio/Gemini — Removing Steps **66.7** and Early
Answering **63.2** beat *both* judges (36.7, 42.5). **A universal ordering narrated over numbers
that already reorder by domain in the source table.** This means the reordering demonstration does
not require their per-instance outputs at all.

## Prior art that must be cited (none currently in the bib)

- **Matos et al. (2026), "Collapsibility of Performance Metrics in Clinical Predictive AI,"
  arXiv:2608.30568 (31 Aug 2026)** — *"The AUC … decomposes into within- and cross-group AUC terms
  … may fall outside the range of subgroup specific AUCs."* Our identity, three weeks old. It also
  hands us a free robustness argument: **F1 and accuracy are collapsible, AUROC is not** — so a rank
  flip in AUROC but not F1 is diagnostic rather than noise.
- **Kallus & Zhou (2019)** xAUC — the ML-side origin of the machinery.
- **Jadidinejad, Macdonald & Ounis (2021), arXiv:2104.08912** — Simpson's paradox in offline
  recommender evaluation: stratify by a confounder, show the pooled ranking is an artifact, propose
  conditioning as protocol, validate by Kendall rank correlation. Our argument end to end, in
  another field. Also our best armour: "yes, and nobody has done it for explanation faithfulness."
- **Deviyani & Diaz (2025), NAACL Findings** — *"local metric accuracies vary both in absolute value
  and relative effectiveness as we shift across evaluation contexts."* The general normative claim.
  **Do not claim the general insight.**
- **Young (2026), arXiv:2603.20172** — *"Classifier choice can also reverse model rankings."* Closest
  on rhetoric. Required distinction: Young varies the **instrument** and reorders **models**; we hold
  the instrument fixed, vary the **stratum**, and reorder **detectors**.
- Also uncited: Mulherin & Miller, Oakden-Rayner ("hidden stratification" — the best existing name
  for our phenomenon), Dehghani (Benchmark Lottery), Pfohl et al.

## Counter-evidence that must be addressed, not ignored

**Han, Lee & Do (2026), "RFEval," ICLR 2026 poster, arXiv:2602.17053** — 7,186 instances, 12 LRMs:
*"accuracy is neither a sufficient nor a reliable proxy for faithfulness: once controlling for model
and task, the accuracy–faithfulness link is weak and statistically insignificant."* Their labels are
intervention-constructed, ours are human annotations. Combined with FaithCoT's own B.1 **and our own
intervention-labelled failure on BonaFide (judge 0.419)**, the honest scope is: **the
correctness-coupling premise is annotation-standard-dependent**, and at least two ICLR 2026 papers
assert the opposite on intervention labels. This is the single strongest reviewer objection and the
paper must meet it head-on.

**BonaFide structurally excludes our axis** — Gur-Arieh et al. filter for correct answers, so they
live entirely in the correct-answer regime and never report the incorrect one.

## Two hard requirements before the reorder claim holds

1. **A significance test for a reversal** — A > B pooled *and* B > A within strata — not two
   per-stratum gaps with overlapping CIs. Our own GRACE notes already flag the overlapping-interval
   problem.
2. **Pfohl et al. (NeurIPS 2025, arXiv:2506.04193)**: disaggregation alone can mislead without
   explicit causal assumptions. A reviewer who knows it will ask what our strata are confounded by.

## Housekeeping

- `arcuschin2025wild` is still `@article{... arXiv preprint ... year=2025}`; reported to be **ICML
  2026**. Verify and update.
- **Do not harvest citations from `PKU-PILLAR-Group/CoT-Faithfulness-Survey`** — six of its §2 arXiv
  IDs resolve to unrelated papers (cosmology, battery prognostics, lattice theory, elliptic-curve
  cryptography). Lead-generation only, per our own citation-verification rule.
