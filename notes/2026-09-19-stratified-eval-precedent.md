# Novelty sweep: the correctness-stratification methodology is NOT novel (2026-09-19)

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
