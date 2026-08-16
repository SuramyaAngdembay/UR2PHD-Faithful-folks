"""Direct regime-difference tests + paired oracle-vs-metric comparisons (GPT round-8).
Reads results/rigorous_features.json (per-trace complete-feature subset, n=633).
(1) Two-sample bootstrap dAUROC (correct-regime minus incorrect-regime) per metric signal.
(2) Paired bootstrap dAUROC (incorrectness oracle minus metric) on the full 633.
Note: the stored 'correct' field's polarity encodes the incorrectness oracle directly
(auroc vs y = 0.696, matching Table 1). Output: results/regime_delta_tests.json."""
import json
import numpy as np

rows = [r for r in json.load(open('results/rigorous_features.json')) if r['ft'] in (1, 2, 3, 4)]
comp = [r for r in rows if all(r.get(k) is not None for k in ('soft', 'avg_impact', 'nli_n_unsup', 'dag_maxlb'))]

def auroc(y, s):
    y, s = np.asarray(y, float), np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    return float((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())

rng = np.random.default_rng(0)
SIG = [('answer_tracing_inv', 'soft'), ('prefix_instability_inv', 'avg_impact'), ('nli_support', 'nli_n_unsup')]
inc = [r for r in comp if r['ft'] in (1, 2)]; cor = [r for r in comp if r['ft'] in (3, 4)]
out = {"regime_delta_tests": {}, "paired_oracle_vs_metrics_n633": {}}
for name, k in SIG:
    yi = np.array([int(r['ft'] == 2) for r in inc]); si = np.array([r[k] for r in inc], float)
    yc = np.array([int(r['ft'] == 4) for r in cor]); sc = np.array([r[k] for r in cor], float)
    dd = []
    for _ in range(5000):
        i1 = rng.integers(0, len(yi), len(yi)); i2 = rng.integers(0, len(yc), len(yc))
        if len(set(yi[i1])) == 2 and len(set(yc[i2])) == 2:
            dd.append(auroc(yc[i2], sc[i2]) - auroc(yi[i1], si[i1]))
    dd = np.array(dd); lo, hi = np.percentile(dd, [2.5, 97.5])
    out["regime_delta_tests"][name] = {"inc": round(auroc(yi, si), 3), "cor": round(auroc(yc, sc), 3),
        "delta": round(auroc(yc, sc) - auroc(yi, si), 3), "ci95": [round(float(lo), 3), round(float(hi), 3)],
        "p_le0": round(float((dd <= 0).mean()), 4)}
y = np.array([r['y'] for r in comp]); so = np.array([r['correct'] for r in comp], float)
out["paired_oracle_vs_metrics_n633"]["oracle_auroc"] = round(auroc(y, so), 3)
for name, k in SIG:
    sm = np.array([r[k] for r in comp], float)
    dd = []
    for _ in range(5000):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i])) == 2: dd.append(auroc(y[i], so[i]) - auroc(y[i], sm[i]))
    lo, hi = np.percentile(dd, [2.5, 97.5])
    out["paired_oracle_vs_metrics_n633"][name] = {"metric_auroc": round(auroc(y, sm), 3),
        "delta": round(auroc(y, so) - auroc(y, sm), 3), "ci95": [round(float(lo), 3), round(float(hi), 3)]}
json.dump(out, open('results/regime_delta_tests.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
