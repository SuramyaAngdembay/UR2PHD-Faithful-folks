"""
Analyze synthetic genuine/post-hoc detection for one model. Cheap (numpy/sklearn).

Reports, for detecting POST-HOC (y=1) vs GENUINE (y=0):
  WHITE-BOX  : per-layer 5-fold CV AUROC; best layer; held-out (70/30) AUROC;
               max-over-layers permutation p (project-once null).
  BLACK-BOX  : (i) answer-tracing soft_faithfulness AUROC (AQuA only);
               (ii) surface-feature LR CV AUROC (both datasets).
  TRANSFER   : (a) cross-dataset within model (train AQuA -> test GSM8K and vice versa, best layer);
               (b) FaithCoT ft1v2 <-> synthetic (validity bridge): train on real annotated reps,
                   test on constructed reps, and reverse.  Uses wbrep_<mdir>.npz cot_end.
Usage: python synth_analyze.py --mdir llama [--nperm 200]
"""
import argparse, json, os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline

ap = argparse.ArgumentParser()
ap.add_argument("--mdir", required=True)
ap.add_argument("--nperm", type=int, default=200)
args = ap.parse_args()
SYNTH = os.path.expanduser("~/synth")
RES = os.path.expanduser("~/synth/results")
os.makedirs(RES, exist_ok=True)
rng = np.random.default_rng(0)

d = np.load(os.path.join(SYNTH, f"acts_{args.mdir}.npz"), allow_pickle=True)
X, y, ds, soft, surf = d["X"], d["y"], d["dataset"], d["soft"], d["surface"]
NL = X.shape[0]
print(f"=== {args.mdir}: {X.shape[1]} traces, {NL} layers, "
      f"{(y==1).sum()} posthoc / {(y==0).sum()} genuine; "
      f"aqua {(ds=='aqua').sum()} gsm8k {(ds=='gsm8k').sum()} ===", flush=True)

def clf(): return make_pipeline(StandardScaler(),
                                PCA(n_components=min(50, X.shape[2]), random_state=0),
                                LogisticRegression(max_iter=2000, C=1.0))
def clf_plain(): return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))

def cv_auroc(Xl, yy, seed=0, factory=None):
    factory = factory or clf
    skf = StratifiedKFold(5, shuffle=True, random_state=seed)
    oof = np.zeros(len(yy))
    for tr, te in skf.split(Xl, yy):
        m = factory().fit(Xl[tr], yy[tr]); oof[te] = m.predict_proba(Xl[te])[:, 1]
    return roc_auc_score(yy, oof)

# ---- white-box: per-layer CV, best layer, held-out, permutation ----
layer_auc = np.array([cv_auroc(X[l].astype(np.float32), y) for l in range(NL)])
best = int(np.argmax(layer_auc)); print(f"[WB] best layer {best} CV AUROC {layer_auc[best]:.3f}", flush=True)
print("[WB] per-layer CV AUROC:", " ".join(f"{l}:{layer_auc[l]:.2f}" for l in range(0, NL, 2)), flush=True)

Xb = X[best].astype(np.float32)
Xtr, Xte, ytr, yte = train_test_split(Xb, y, test_size=0.3, stratify=y, random_state=0)
m = clf().fit(Xtr, ytr); heldout = roc_auc_score(yte, m.predict_proba(Xte)[:, 1])
print(f"[WB] held-out (70/30) AUROC @L{best}: {heldout:.3f}", flush=True)

# max-over-layers permutation (project-once: PCA per layer on full data, permute labels)
proj = []
for l in range(NL):
    p = make_pipeline(StandardScaler(), PCA(n_components=min(50, X.shape[2]), random_state=0))
    proj.append(p.fit_transform(X[l].astype(np.float32)))
def perm_maxauc(yy):
    return max(cv_auroc(proj[l], yy) for l in range(NL))
obs = perm_maxauc(y)
null = np.array([perm_maxauc(rng.permutation(y)) for _ in range(args.nperm)])
pval = float((1 + (null >= obs).sum()) / (1 + args.nperm))
print(f"[WB] max-over-layers obs {obs:.3f}, perm p={pval:.3f} (n={args.nperm})", flush=True)

# ---- black-box baselines ----
bb = {}
amask = (ds == "aqua") & ~np.isnan(soft)
print(f"[BB] soft coverage: {amask.sum()} aqua traces with non-nan soft (of {(ds=='aqua').sum()} aqua)", flush=True)
if amask.sum() > 10 and len(np.unique(y[amask])) == 2:
    s = soft[amask]; ys = y[amask]
    # soft high = more faithful => predicts genuine (y=0); AUROC for posthoc uses -soft
    bb["soft_auroc_aqua"] = float(roc_auc_score(ys, -s))
    print(f"[BB] answer-tracing soft_faithfulness AUROC (AQuA, n={amask.sum()}): {bb['soft_auroc_aqua']:.3f}", flush=True)
sc = surf.astype(np.float32)
bb["surface_auroc"] = float(cv_auroc(sc, y, factory=clf_plain))
print(f"[BB] surface-feature LR CV AUROC (both ds): {bb['surface_auroc']:.3f}", flush=True)

# ---- transfer (a): cross-dataset within model ----
xds = {}
for tr_ds, te_ds in (("aqua", "gsm8k"), ("gsm8k", "aqua")):
    m1 = (ds == tr_ds); m2 = (ds == te_ds)
    if m1.sum() > 20 and m2.sum() > 20 and len(np.unique(y[m1])) == 2 and len(np.unique(y[m2])) == 2:
        mdl = clf().fit(Xb[m1], y[m1]); a = roc_auc_score(y[m2], mdl.predict_proba(Xb[m2])[:, 1])
        xds[f"{tr_ds}->{te_ds}"] = float(a)
        print(f"[TRANSFER-xds] train {tr_ds} -> test {te_ds} @L{best}: AUROC {a:.3f}", flush=True)

# ---- transfer (b): FaithCoT ft1v2 <-> synthetic (validity bridge) ----
fc = {}
wp = os.path.expanduser(f"~/wbrep_{args.mdir}.npz")
if os.path.exists(wp):
    w = np.load(wp, allow_pickle=True)
    fc_end, fc_y = w["cot_end"], w["y"]           # [n, NL+1, dim], layer0=embeddings
    Lf = best + 1                                  # synth layer `best` == wbrep layer best+1
    if Lf < fc_end.shape[1]:
        Xf = fc_end[:, Lf, :].astype(np.float32)
        # fit pipeline on FaithCoT, test on ALL synthetic (real -> constructed)
        mf = clf().fit(Xf, fc_y); a1 = roc_auc_score(y, mf.predict_proba(Xb)[:, 1])
        # reverse: fit on synthetic, test on FaithCoT (constructed -> real)
        ms = clf().fit(Xb, y); a2 = roc_auc_score(fc_y, ms.predict_proba(Xf)[:, 1])
        fc = {"faithcot->synth": float(a1), "synth->faithcot": float(a2),
              "faithcot_n": int(len(fc_y)), "layer": int(Lf)}
        print(f"[TRANSFER-bridge] FaithCoT(real,n={len(fc_y)}) -> synth: AUROC {a1:.3f} | "
              f"synth -> FaithCoT: AUROC {a2:.3f}  (@wbrep L{Lf})", flush=True)
else:
    print(f"[TRANSFER-bridge] no wbrep_{args.mdir}.npz -> skipped", flush=True)

out = {"model": args.mdir, "n": int(X.shape[1]), "n_posthoc": int((y == 1).sum()),
       "wb_best_layer": best, "wb_cv_auroc": float(layer_auc[best]), "wb_heldout_auroc": float(heldout),
       "wb_perm_obs": float(obs), "wb_perm_p": pval, "black_box": bb,
       "transfer_cross_dataset": xds, "transfer_bridge": fc,
       "per_layer_cv_auroc": [float(x) for x in layer_auc]}
json.dump(out, open(os.path.join(RES, f"synth_{args.mdir}.json"), "w"), indent=2)
print(f"SYNTH_ANALYZE DONE {args.mdir} -> results/synth_{args.mdir}.json", flush=True)
