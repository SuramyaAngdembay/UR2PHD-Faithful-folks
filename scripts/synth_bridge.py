"""
Diagnose the FaithCoT(real) <-> synthetic(constructed) transfer failure, controlling for the
obvious confounds (domain shift; layer depth). FaithCoT reps span truthfulqa/logiqa/aqua/HLE_BIO
(mostly NON-math); synthetic is all-math. And real vs synthetic post-hoc may live at different
DEPTHS. So we: (1) find each distribution's own best layer by CV; (2) sweep ALL shared layers for
transfer and report the BEST layer's AUROC (gives the bridge its best shot); (3) domain-match by
restricting FaithCoT to aqua-only; (4) contrast with FaithCoT non-math.
Transfer at a shared layer L uses FaithCoT wbrep index L and synthetic block-layer L-1 (== the same
hidden_states[L]). Cheap; numpy/sklearn only.  Usage: python synth_bridge.py --mdir llama
"""
import argparse, json, os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline

ap = argparse.ArgumentParser(); ap.add_argument("--mdir", required=True); args = ap.parse_args()
SYNTH = os.path.expanduser("~/synth"); RES = os.path.expanduser("~/synth/results")

d = np.load(os.path.join(SYNTH, f"acts_{args.mdir}.npz"), allow_pickle=True)
X, y, ds = d["X"], d["y"], d["dataset"]          # X: [NL, n, dim], synth block-layers 0..NL-1
w = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}.npz"), allow_pickle=True)
fe, fy, fdom = w["cot_end"], w["y"], w["domain"]  # fe: [n, NL+1, dim], index0=embed

def pipe(ncomp): return make_pipeline(StandardScaler(), PCA(n_components=ncomp, random_state=0),
                                      LogisticRegression(max_iter=2000, C=1.0))
def ncomp_for(n): return max(2, min(50, n - 2))   # safe PCA dim given sample count

def cv(Xl, yy):
    skf = StratifiedKFold(5, shuffle=True, random_state=0); oof = np.zeros(len(yy))
    nc = ncomp_for(int(len(yy) * 0.8))
    for tr, te in skf.split(Xl, yy):
        oof[te] = pipe(nc).fit(Xl[tr], yy[tr]).predict_proba(Xl[te])[:, 1]
    return roc_auc_score(yy, oof)

def xfer(Xtr, ytr, Xte, yte):
    if len(ytr) < 12 or len(np.unique(ytr)) < 2: return None
    m = pipe(ncomp_for(len(ytr))).fit(Xtr, ytr)
    return float(roc_auc_score(yte, m.predict_proba(Xte)[:, 1]))

NL = X.shape[0]
# own-best layers by CV
synth_layer_cv = [cv(X[l].astype(np.float32), y) for l in range(NL)]
sbest = int(np.argmax(synth_layer_cv))
fc_layer_cv = [cv(fe[:, L, :].astype(np.float32), fy) for L in range(1, NL + 1)]  # align to block-layers
fbest = int(np.argmax(fc_layer_cv))  # index into block-layers 0..NL-1  (wbrep index = fbest+1)
print(f"=== {args.mdir} ===", flush=True)
print(f"synth own-best block-layer {sbest} CV {synth_layer_cv[sbest]:.3f}", flush=True)
print(f"FaithCoT own-best block-layer {fbest} (wbrep L{fbest+1}) CV {fc_layer_cv[fbest]:.3f}", flush=True)
print(f"FaithCoT domains: {dict(zip(*[list(v) for v in np.unique(fdom, return_counts=True)]))}", flush=True)

aq_f = (fdom == "aqua"); aq_s = (ds == "aqua"); nonmath_f = (fdom != "aqua")

def sweep(fmask, smask, tag):
    """best-over-layers transfer FaithCoT[fmask] -> synth[smask], and reverse."""
    fyy = fy[fmask]; syy = y[smask]
    if fmask.sum() < 12 or smask.sum() < 12 or len(np.unique(fyy)) < 2 or len(np.unique(syy)) < 2:
        print(f"  [{tag}] skipped (fc n={int(fmask.sum())}, synth n={int(smask.sum())})", flush=True); return {}
    fwd, rev = [], []
    for l in range(NL):
        Xf = fe[fmask, l + 1, :].astype(np.float32); Xs = X[l][smask].astype(np.float32)
        fwd.append(xfer(Xf, fyy, Xs, syy)); rev.append(xfer(Xs, syy, Xf, fyy))
    fwd = np.array(fwd, float); rev = np.array(rev, float)
    bf, br = int(np.nanargmax(fwd)), int(np.nanargmax(rev))
    print(f"  [{tag}] FC->synth best AUROC {fwd[bf]:.3f} @L{bf} (mean {np.nanmean(fwd):.3f}) | "
          f"synth->FC best {rev[br]:.3f} @L{br} (mean {np.nanmean(rev):.3f}) "
          f"[fc n={int(fmask.sum())}, synth n={int(smask.sum())}]", flush=True)
    return {"fc2s_best": fwd[bf], "fc2s_best_layer": bf, "fc2s_mean": float(np.nanmean(fwd)),
            "s2fc_best": rev[br], "s2fc_best_layer": br, "s2fc_mean": float(np.nanmean(rev)),
            "fc_n": int(fmask.sum()), "synth_n": int(smask.sum())}

allmask_f = np.ones(len(fy), bool); allmask_s = np.ones(len(y), bool)
out = {"model": args.mdir, "synth_best_layer": sbest, "synth_best_cv": float(synth_layer_cv[sbest]),
       "faithcot_best_layer": fbest, "faithcot_best_cv": float(fc_layer_cv[fbest]),
       "sweep_all": sweep(allmask_f, allmask_s, "FC-all -> synth-all"),
       "sweep_aqua_matched": sweep(aq_f, aq_s, "FC-aqua -> synth-aqua (domain-matched)"),
       "sweep_nonmath": sweep(nonmath_f, allmask_s, "FC-nonmath -> synth-all (contrast)")}
json.dump(out, open(os.path.join(RES, f"bridge_{args.mdir}.json"), "w"), indent=2)
print(f"BRIDGE DONE {args.mdir}", flush=True)
