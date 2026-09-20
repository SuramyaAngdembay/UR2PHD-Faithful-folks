# Step 1 — competitive gap by regime: frozen spec (2026-09-19, before running)

**Question (pre-registered).** Across every detector we can compute without new inference, what is
the **ceiling in the incorrect-answer regime**, and does anything there beat a length baseline?

This is the experiment that decides whether the method direction is worth pursuing. If nothing
computable clears chance in the blind regime except signals we already have, a new training
objective has nothing to recover and the method door closes on evidence rather than on prior.

## Population and strata

FaithCoT-Bench, 1,303 traces with a valid four-way code. Regimes are keyed on **`ft`**, never on
the `correct` field — see the hazard note below.

- **INCORRECT regime** = ft ∈ {1,2}, n=514. Target: unfaithful = ft2.
- **CORRECT regime** = ft ∈ {3,4}, n=789. Target: unfaithful = ft4.
- Pooled: target unfaithful = ft ∈ {2,4}.

This matches `scripts/audit_corrected.py` exactly, so results are comparable to the published table.

> **HAZARD (found 2026-09-19).** `results/rigorous_features.json` ships a field named `correct`
> that is defined as `1 if ft in (1,2)` — i.e. **`correct=1` means INCORRECT-answer**, the inverse
> of its name. It is derived from `ft`, not computed from answers (zero cross-cells).
> `results/judge_join.json` uses the opposite, name-consistent convention. Reading the field
> naively inverts every regime result. The published analysis is safe because
> `audit_corrected.py` keys on `ft`; the display strings in `rigorous_analysis.py:131-132` are
> stale pre-correction labels and should not be trusted.

## Detectors evaluated (all per stratum)

**Algorithmic** (`rigorous_features.json`): soft, hard, avg_impact (n=634 — the two open-weight
models only, since step-removal needs token probabilities); dag_lin, dag_maxlb, nli_n_unsup,
nli_min_ent, nli_mean_ent, nli_frac_con (n=1304).

**Length/surface baselines**: n_steps, trace word count, trace character count. *These are the bar
every purpose-built detector must clear to be interesting.*

**Prompted LLM judge**: judgeA from `judge_join.json` (n=1303).

**Supervised text baseline**: TF-IDF (word 1–2 grams, min_df=2) + logistic regression, evaluated by
**question-grouped** cross-validation — all traces sharing a question text stay in the same fold,
since the same questions recur across the four generator models. Hyperparameters fixed in advance
(C=1.0, liblinear, class_weight balanced); **no tuning against the evaluation folds.**

## Endpoints

Per detector × stratum: AUROC against the stratum target, with a **question-grouped bootstrap**
(2,000 draws, seed 0, percentile 95%). Raw AUROC is reported with its sign — a value below 0.5 is
an inversion and is reported as such, not flipped.

Reported alongside: pooled AUROC, and the within-/cross-stratum decomposition
(Kallus & Zhou 2019, Prop. 1 — cited, not claimed).

## Pre-registered readings (fixed before seeing results)

- **Nothing in the incorrect regime clears chance except the judge** → the method direction closes;
  report the ceiling as the finding.
- **A length/surface baseline matches or beats the purpose-built detectors in a regime** → that
  regime's published detector performance is substantially surface-explainable.
- **The supervised text baseline clears chance in the incorrect regime** → there *is* extractable
  signal in the text that current detectors miss, and a method has something to recover.

All three are informative. No outcome is the one we need.

## Scope

Exploratory reanalysis of cached, public data. No new inference. Does not reproduce
FaithCoT-Bench's own eleven-detector F1 comparison (their per-instance detector outputs are not in
the release — verified by enumerating all 1,364 files). F1 and AUROC are not interchangeable here;
see `notes/2026-09-19-stratified-eval-precedent.md`.
