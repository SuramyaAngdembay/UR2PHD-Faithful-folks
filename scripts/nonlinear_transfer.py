"""Tier-2 item 7 (corrected): nonlinear transfer, with the probe selected on the SOURCE only.

First attempt used a fixed 32-unit MLP and failed its positive control: hint->incorrect fell
0.616 -> 0.521, and a within-distribution check showed the MLP trailing logistic regression by
0.08-0.15 AUROC on the source tasks themselves. Its nulls therefore measured the estimator, not
the representations.

Corrected design: for each source, sweep a small family of nonlinear heads on identical PCA-50
features and pick the best by 5-fold CV ON THE SOURCE DISTRIBUTION ONLY (no target involvement, so
no leakage). A nonlinear probe is only allowed to speak about transfer if it first matches the
linear probe in-distribution. If none does, that is itself the finding: at n~500 this data regime
does not support nonlinear probing, and the paper's linearity caveat stands as a real limitation
rather than an untested one.

Usage: python nonlinear_transfer.py --mdir llama
Output: ~/synth/results/nonlinear_transfer_<mdir>.json
"""
import argparse, json, os, warnings
import numpy as np
from scipy.stats import rankdata
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
warnings.filterwarnings("ignore")

ap = argparse.ArgumentParser(); ap.add_argument("--mdir", required=True)
args = ap.parse_args()
SYNTH = os.path.expanduser("~/synth"); RES = os.path.join(SYNTH, "results")

def head(n, kind):
    pre = [StandardScaler(), PCA(n_components=max(2, min(50, n - 2)), random_state=0)]
    if kind == "linear":            clf = LogisticRegression(max_iter=2000, C=1.0)
    elif kind.startswith("mlp"):
        _, hs, al = kind.split(":")
        hs = tuple(int(x) for x in hs.split(","))
        clf = MLPClassifier(hidden_layer_sizes=hs, alpha=float(al), max_iter=2000,
                            early_stopping=True, n_iter_no_change=25, random_state=0)
    elif kind.startswith("svc"):    clf = SVC(kernel="rbf", C=float(kind.split(":")[1]), gamma="scale", probability=True, random_state=0)
    elif kind == "hgb":             clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.06, random_state=0)
    return make_pipeline(*pre, clf)

GRID = ["mlp:16:1e-1", "mlp:32:1e-2", "mlp:64:1e-2", "mlp:32,16:1e-2",
        "svc:1.0", "svc:10.0", "hgb"]

def auc(y, s):
    r = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    return np.nan if n1 == 0 or n0 == 0 else (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
def cv(X, y, kind):
    skf = StratifiedKFold(5, shuffle=True, random_state=0); oof = np.zeros(len(y))
    for tr, te in skf.split(X, y):
        oof[te] = head(len(tr), kind).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return roc_auc_score(y, oof)

s  = np.load(os.path.join(SYNTH, f"acts_{args.mdir}.npz"), allow_pickle=True)
h  = np.load(os.path.join(SYNTH, f"acts_{args.mdir}_hint.npz"), allow_pickle=True)
wi = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}.npz"), allow_pickle=True)
wc = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}_ft34.npz"), allow_pickle=True)
SRC = {"instructed": (lambda l, d=s: d["X"][l].astype(np.float32), np.asarray(s["y"]).astype(int), s["X"].shape[0]),
       "hint":       (lambda l, d=h: d["X"][l].astype(np.float32), np.asarray(h["y"]).astype(int), h["X"].shape[0]),
       "incorrect":  (lambda l, d=wi: d["cot_end"][:, l+1, :].astype(np.float32), np.asarray(wi["y"]).astype(int), wi["cot_end"].shape[1]-1),
       "correct":    (lambda l, d=wc: d["cot_end"][:, l+1, :].astype(np.float32), np.asarray(wc["y"]).astype(int), wc["cot_end"].shape[1]-1)}
TGT = {"incorrect": (lambda l, d=wi: d["cot_end"][:, l+1, :].astype(np.float32), np.asarray(wi["y"]).astype(int), wi["cot_end"].shape[1]-1),
       "correct":   (lambda l, d=wc: d["cot_end"][:, l+1, :].astype(np.float32), np.asarray(wc["y"]).astype(int), wc["cot_end"].shape[1]-1)}
NL = min(min(v[2] for v in SRC.values()), min(v[2] for v in TGT.values()))
print(f"model={args.mdir} layers={NL}", flush=True)

out = {"model": args.mdir, "n_layers": int(NL),
       "design": "nonlinear head chosen by source-only 5-fold CV; must match linear in-distribution to be trusted on transfer",
       "sources": {}}
for sk, (sget, sy, _) in SRC.items():
    lin_curve = [cv(sget(l), sy, "linear") for l in range(NL)]
    bl = int(np.argmax(lin_curve)); lin_cv = float(lin_curve[bl])
    scores = {k: float(cv(sget(bl), sy, k)) for k in GRID}
    best_k = max(scores, key=scores.get); best_cv = scores[best_k]
    passes = best_cv >= lin_cv - 0.02
    rec = {"best_linear_layer": bl, "linear_source_cv": lin_cv,
           "nonlinear_grid_source_cv": scores, "best_nonlinear": best_k,
           "best_nonlinear_source_cv": best_cv,
           "matches_linear_in_distribution": bool(passes)}
    print(f"  {sk}: linear CV {lin_cv:.3f} @L{bl} | best nonlinear {best_k} CV {best_cv:.3f} -> "
          f"{'USABLE' if passes else 'NOT USABLE (cannot learn source)'}", flush=True)
    if passes:
        rec["transfer"] = {}
        for tk, (tget, ty, _) in TGT.items():
            if tk == sk: continue
            for kind, lab in ((best_k, "nonlinear"), ("linear", "linear")):
                aucs = [auc(ty, head(len(sy), kind).fit(sget(l), sy).predict_proba(tget(l))[:, 1]) for l in range(NL)]
                rec["transfer"].setdefault(tk, {})[lab] = float(np.nanmean(aucs))
            t = rec["transfer"][tk]
            print(f"     -> {tk}: linear {t['linear']:.3f} | nonlinear {t['nonlinear']:.3f} | diff {t['nonlinear']-t['linear']:+.3f}", flush=True)
    out["sources"][sk] = rec

json.dump(out, open(os.path.join(RES, f"nonlinear_transfer_{args.mdir}.json"), "w"), indent=2)
print(f"NONLINEAR-CORRECTED DONE {args.mdir}", flush=True)
