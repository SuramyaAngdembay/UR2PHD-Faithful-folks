"""Multiplicity ledger: which reported claims survive correction, and in which family.

Action 3 of notes/2026-09-19-holdout-and-phacking-audit.md, which required this "before anything
enters the manuscript".

METHOD AND ITS LIMIT, stated first because it bounds every number below. The paper reports
percentile bootstrap intervals, not standard errors or p-values. To put claims on a common scale
this converts each interval to an approximate z by SE = (hi - lo) / (2 * 1.96), z = (est - null)/SE.
That assumes an approximately normal, symmetric sampling distribution. It is a TRIAGE TOOL, not a
re-analysis: it is least trustworthy for AUROCs near 0 or 1 and for small-n cells, where percentile
intervals are visibly asymmetric. A claim that lands near a threshold here needs a real corrected
test, not this arithmetic. Claims far from a threshold are safe to read off.

The ledger's actual point is not the z values. It is that CORRECTION FAMILY IS A CHOICE, and the
defensible choice is fixed by when the claim was committed. A pre-registered claim belongs in the
pre-registered family; it does not inherit the multiplicity of exploratory work done elsewhere in
the same paper. Lumping everything into one family is not conservatism, it is a category error that
punishes the one panel that was done right.

Run: python scripts/multiplicity_ledger.py    Out: results/multiplicity_ledger.json
"""
import json, hashlib
from pathlib import Path
from math import sqrt
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
ND = NormalDist()

# (family, claim, estimate, lo, hi, null, preregistered, note)
CLAIMS = [
 # --- FAMILY: BonaFide pre-registered external test (the only confirmatory panel) ---
 ("bonafide_prereg", "judge AUROC inverted on BonaFide", 0.419, 0.372, 0.464, 0.5, True, "ABSTRACT headline"),
 ("bonafide_prereg", "second judge prompt near chance",  0.482, 0.437, 0.530, 0.5, True, "null"),
 ("bonafide_prereg", "gpt-4o judge far below chance",    0.270, 0.231, 0.310, 0.5, True, ""),
 ("bonafide_prereg", "step count discriminates",         0.878, 0.852, 0.902, 0.5, True, "ABSTRACT headline"),
 ("bonafide_prereg", "NLI unsupported-step count",       0.826, 0.795, 0.855, 0.5, True, ""),
 ("bonafide_prereg", "answer-tracing below chance",      0.284, 0.171, 0.401, 0.5, True, "4-generator subset"),
 ("bonafide_prereg", "prefix instability below chance",  0.172, 0.101, 0.265, 0.5, True, "4-generator subset"),

 # --- FAMILY: FaithCoT Table 1, signal vs chance (exploratory) ---
 ("faithcot_table1", "answer incorrectness (oracle)",    0.696, 0.662, 0.734, 0.5, False, ""),
 ("faithcot_table1", "answer-tracing (inverted)",        0.651, 0.611, 0.695, 0.5, False, ""),
 ("faithcot_table1", "prefix instability (inverted)",    0.626, 0.583, 0.670, 0.5, False, ""),
 ("faithcot_table1", "NLI unsupported steps",            0.569, 0.523, 0.615, 0.5, False, ""),
 ("faithcot_table1", "NLI mean entailment",              0.493, 0.447, 0.538, 0.5, False, "null"),
 ("faithcot_table1", "trace length",                     0.575, 0.527, 0.618, 0.5, False, ""),
 ("faithcot_table1", "DAG linearity",                    0.530, 0.483, 0.577, 0.5, False, "null"),
 ("faithcot_table1", "DAG max lookback",                 0.543, 0.496, 0.588, 0.5, False, "null"),
 ("faithcot_table1", "prompted judge",                   0.782, 0.756, 0.808, 0.5, False, ""),
 ("faithcot_table1", "soft_faithfulness intended dir",   0.349, 0.305, 0.389, 0.5, False, "ABSTRACT headline (inversion)"),

 # --- FAMILY: FaithCoT Table 6, signal x regime vs chance (exploratory) ---
 ("faithcot_regimes", "judge, blind regime",             0.679, 0.633, 0.721, 0.5, False, "ABSTRACT headline"),
 ("faithcot_regimes", "judge, correct regime",           0.830, 0.786, 0.872, 0.5, False, "ABSTRACT headline"),
 ("faithcot_regimes", "answer-tracing, correct",         0.667, 0.592, 0.736, 0.5, False, ""),
 ("faithcot_regimes", "prefix instability, correct",     0.659, 0.588, 0.730, 0.5, False, ""),
 ("faithcot_regimes", "NLI, correct",                    0.626, 0.556, 0.696, 0.5, False, ""),
 ("faithcot_regimes", "trace length, correct",           0.622, 0.552, 0.691, 0.5, False, ""),
 ("faithcot_regimes", "DAG max lookback, correct",       0.562, 0.491, 0.634, 0.5, False, "null"),
 ("faithcot_regimes", "DAG linearity, correct",          0.535, 0.462, 0.609, 0.5, False, "null"),
 ("faithcot_regimes", "answer-tracing, blind",           0.530, 0.462, 0.598, 0.5, False, "null"),
 ("faithcot_regimes", "prefix instability, blind",       0.481, 0.408, 0.549, 0.5, False, "null"),
 ("faithcot_regimes", "NLI, blind",                      0.541, 0.476, 0.608, 0.5, False, "null"),
 ("faithcot_regimes", "DAG, blind",                      0.493, 0.424, 0.561, 0.5, False, "null"),
 ("faithcot_regimes", "soft, blind (uninformative)",     0.470, 0.402, 0.538, 0.5, False, "null"),
 ("faithcot_regimes", "soft, correct (inverted)",        0.333, 0.264, 0.408, 0.5, False, ""),

 # --- FAMILY: regime-difference contrasts (exploratory) ---
 ("regime_deltas", "judge regime gap",                   0.152, 0.089, 0.211, 0.0, False, "ABSTRACT headline"),
 ("regime_deltas", "answer-tracing regime gap",          0.136, 0.035, 0.235, 0.0, False, ""),
 ("regime_deltas", "prefix instability regime gap",      0.178, 0.078, 0.279, 0.0, False, ""),

 # --- FAMILY: 8-cell transfer grid (Bonferroni ALREADY applied in the paper) ---
 ("transfer_grid", "Llama math-sycophancy transfer",     0.185, 0.081, 0.289, 0.0, False, "the one positive cell"),
 ("transfer_grid", "Llama math-metadata",                0.020, -0.045, 0.084, 0.0, False, "null"),
 ("transfer_grid", "Llama LogiQA",                       0.038, -0.055, 0.133, 0.0, False, "null"),
 ("transfer_grid", "Llama TruthfulQA",                   0.021, -0.048, 0.090, 0.0, False, "null"),
 ("transfer_grid", "Qwen math-sycophancy",              -0.031, -0.103, 0.042, 0.0, False, "null"),
 ("transfer_grid", "Qwen math-metadata",                -0.002, -0.085, 0.082, 0.0, False, "null"),
 ("transfer_grid", "Qwen LogiQA",                        0.038, -0.019, 0.095, 0.0, False, "null"),
 ("transfer_grid", "Qwen TruthfulQA",                    0.009, -0.052, 0.069, 0.0, False, "null"),

 # --- FAMILY: judge ablations (exploratory) ---
 ("judge_ablations", "question-only, full",              0.487, 0.456, 0.519, 0.5, False, "null (intended)"),
 ("judge_ablations", "question-only, blind",             0.467, 0.421, 0.512, 0.5, False, "null (intended)"),
 ("judge_ablations", "question-only, correct",           0.552, 0.503, 0.600, 0.5, False, "grazes 0.5"),
 ("judge_ablations", "CoT-only, full",                   0.693, 0.662, 0.725, 0.5, False, ""),
 ("judge_ablations", "CoT-only, blind",                  0.661, 0.614, 0.704, 0.5, False, ""),
 ("judge_ablations", "CoT-only, correct",                0.769, 0.720, 0.817, 0.5, False, ""),
 ("judge_ablations", "CoT-only vs incorrectness",        0.560, 0.530, 0.590, 0.5, False, ""),

 # --- FAMILY: post-unblinding BonaFide controls (disclosed post-hoc) ---
 ("bonafide_posthoc", "judge inversion, instruct-only",  0.332, 0.285, 0.381, 0.5, False, "ABSTRACT headline, POST-HOC"),
 ("bonafide_posthoc", "NLI under strictest conditioning",0.603, 0.570, 0.638, 0.5, False, "1.4% of pairs"),
]

N_TOTAL_PAPER = 115   # interval-bearing estimates in the paper, from the claim inventory

def z_of(est, lo, hi, null):
    se = (hi - lo) / (2 * 1.959963985)
    return None if se <= 0 else (est - null) / se

def zcrit(m, alpha=0.05):
    return ND.inv_cdf(1 - alpha / (2 * m))

fams = {}
for f, *_ in CLAIMS:
    fams[f] = fams.get(f, 0) + 1

rows, out = [], {"method": "percentile CI -> approximate z; triage only, see module docstring",
                 "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 "n_estimates_in_paper": N_TOTAL_PAPER, "families": {}, "claims": []}

zc_paper = zcrit(N_TOTAL_PAPER)
print(f"whole-paper Bonferroni over {N_TOTAL_PAPER} estimates needs |z| > {zc_paper:.2f}")
print(f"uncorrected 0.05 needs |z| > 1.96\n")
print(f"{'family':18s} {'claim':36s} {'z':>7} {'own-fam':>8} {'paper':>7}  note")
for f, name, est, lo, hi, null, prereg, note in CLAIMS:
    z = z_of(est, lo, hi, null)
    zc_fam = zcrit(fams[f])
    own = abs(z) > zc_fam
    pap = abs(z) > zc_paper
    print(f"{f:18s} {name:36s} {z:7.2f} {('PASS' if own else '  --'):>8} {('PASS' if pap else '  --'):>7}  {note}")
    out["claims"].append({"family": f, "claim": name, "estimate": est, "ci95": [lo, hi],
                          "null": null, "preregistered": prereg, "z_approx": round(z, 3),
                          "survives_own_family_bonferroni": bool(own),
                          "survives_whole_paper_bonferroni": bool(pap),
                          "family_size": fams[f], "note": note})
for f, m in sorted(fams.items()):
    out["families"][f] = {"n_tests": m, "bonferroni_z_threshold": round(zcrit(m), 3)}

(ROOT / "results/multiplicity_ledger.json").write_text(json.dumps(out, indent=2) + "\n")
print(f"\nfamily sizes / thresholds:")
for f, m in sorted(fams.items()):
    print(f"  {f:18s} n={m:2d}  needs |z| > {zcrit(m):.2f}")
print(f"\nwrote results/multiplicity_ledger.json")
