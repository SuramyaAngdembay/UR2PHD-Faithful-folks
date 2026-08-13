"""Appendix extras for submission: (1) AUPRC robustness for the regime comparisons,
(2) model x domain forest plot data + figure (heterogeneity transparency).
Reads results/rigorous_features.json; writes results/appendix_extras.json + paper/figs/forest.pdf."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rows = [r for r in json.load(open('results/rigorous_features.json')) if r['ft'] in (1, 2, 3, 4)]

def auroc(y, s):
    y, s = np.asarray(y, float), np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    if not len(pos) or not len(neg): return float('nan')
    return (pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()

def auprc(y, s):
    y, s = np.asarray(y, float), np.asarray(s, float)
    o = np.argsort(-s); y = y[o]
    tp = np.cumsum(y); prec = tp / np.arange(1, len(y) + 1); rec = tp / (y.sum() or 1)
    ap, last = 0.0, 0.0
    for p, rc in zip(prec, rec):
        ap += p * (rc - last); last = rc
    return ap

def ci(fn, y, s, B=2000, seed=0):
    rng = np.random.default_rng(seed); y, s = np.asarray(y, float), np.asarray(s, float); v = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i])) == 2: v.append(fn(y[i], s[i]))
    return np.percentile(v, [2.5, 97.5])

out = {"auprc": {}, "forest": {}}
# ---- AUPRC on the complete-feature regimes (signals as in Table 2, empirically-oriented dirs)
comp = [r for r in rows if all(r.get(k) is not None for k in ('soft', 'avg_impact', 'nli_n_unsup', 'dag_maxlb'))]
SIG = [("soft_inv", lambda r: r['soft']), ("prefix_inst_inv", lambda r: r['avg_impact']),
       ("nli_n_unsup", lambda r: r['nli_n_unsup'])]
for regime, fts in [("incorrect", (1, 2)), ("correct", (3, 4))]:
    rr = [r for r in comp if r['ft'] in fts]
    y = [1 if r['ft'] in (2, 4) else 0 for r in rr]
    prev = sum(y) / len(y)
    out["auprc"][regime] = {"n": len(rr), "prevalence": round(prev, 3), "signals": {}}
    for name, f in SIG:
        s = [f(r) for r in rr]
        a = auprc(y, s); lo, hi = ci(auprc, y, s)
        out["auprc"][regime]["signals"][name] = [round(float(a), 3), round(float(lo), 3), round(float(hi), 3)]
        print(f"AUPRC {regime:9s} {name:16s} {a:.3f} [{lo:.3f},{hi:.3f}] (prev {prev:.3f})")

# ---- forest: NLI (all 4 models) + soft-inv (open models) per model x domain x regime
MODELS = sorted({r['model'][:12] for r in rows})
DOMS = ["truthfulqa", "logiqa", "aqua", "HLE_BIO"]
entries = []
for regime, fts in [("incorrect", (1, 2)), ("correct", (3, 4))]:
    for m in MODELS:
        for dom in DOMS:
            rr = [r for r in rows if r['ft'] in fts and r['model'][:12] == m and r['dom'] == dom
                  and r.get('nli_n_unsup') is not None]
            y = [1 if r['ft'] in (2, 4) else 0 for r in rr]
            if len(rr) < 10 or len(set(y)) < 2: continue
            s = [r['nli_n_unsup'] for r in rr]
            a = auroc(y, s); lo, hi = ci(auroc, y, s, B=1000)
            entries.append(dict(regime=regime, model=m, dom=dom, sig="NLI", n=len(rr),
                                auroc=float(a), lo=float(lo), hi=float(hi)))
            if r0 := [r for r in rr if r.get('soft') is not None]:
                if len(r0) >= 10 and len(set(1 if r['ft'] in (2,4) else 0 for r in r0)) == 2:
                    y0 = [1 if r['ft'] in (2, 4) else 0 for r in r0]; s0 = [r['soft'] for r in r0]
                    a0 = auroc(y0, s0); lo0, hi0 = ci(auroc, y0, s0, B=1000)
                    entries.append(dict(regime=regime, model=m, dom=dom, sig="soft-inv", n=len(r0),
                                        auroc=float(a0), lo=float(lo0), hi=float(hi0)))
out["forest"] = entries
json.dump(out, open('results/appendix_extras.json', 'w'), indent=1)

# ---- figure: two columns (incorrect | correct regime), rows = model x domain cells
plt.rcParams.update({"font.size": 7.5, "figure.dpi": 200, "savefig.bbox": "tight"})
fig, axes = plt.subplots(1, 2, figsize=(6.6, 4.6), sharex=True)
for ax, regime, title in [(axes[0], "incorrect", "Incorrect regime (honest vs. unfaithful error)"),
                          (axes[1], "correct", "Correct regime (faithful vs. post-hoc)")]:
    es = [e for e in entries if e['regime'] == regime]
    es.sort(key=lambda e: (e['sig'], e['model'], DOMS.index(e['dom'])))
    ys = np.arange(len(es))
    for i, e in enumerate(es):
        c = "#3b6fb6" if e['sig'] == "NLI" else "#3b8a5a"
        ax.errorbar(e['auroc'], i, xerr=[[e['auroc'] - e['lo']], [e['hi'] - e['auroc']]],
                    fmt='o', ms=3, color=c, elinewidth=1, capsize=2)
    ax.axvline(0.5, color='k', ls='--', lw=0.8)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{e['sig']} | {e['model'][:8]} | {e['dom'][:8]} (n={e['n']})" for e in es], fontsize=6)
    ax.set_title(title, fontsize=8); ax.set_xlabel("AUROC")
    ax.set_xlim(0.05, 1.0); ax.invert_yaxis()
    ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout()
fig.savefig('paper/figs/forest.pdf')
print(f"forest cells: {len(entries)} -> paper/figs/forest.pdf")
