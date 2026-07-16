"""Strict-subset analysis (run AFTER flip_stability2): keep genuine traces + posthoc traces whose
problems failed ALL baseline resamples. Recompute (a) within-hint CV at swept layers, (b) the
hint->FaithCoT transfer sweep (best + mean) + coupled permutation p on the mean (500 perms).
Usage: python strict_subset.py --mdir llama"""
import argparse, json, os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
ap = argparse.ArgumentParser(); ap.add_argument("--mdir", required=True)
ap.add_argument("--nperm", type=int, default=500)
a = ap.parse_args()
SYNTH = os.path.expanduser("~/synth")
h = np.load(os.path.join(SYNTH, f"acts_{a.mdir}_hint.npz"), allow_pickle=True)
X, y = h["X"], h["y"]
ids = []
for ds in ("aqua", "gsm8k", "aquarat"):
    p = os.path.join(SYNTH, f"traces_{a.mdir}_hint_{ds}.json")
    if os.path.exists(p): ids += [t["id"] for t in json.load(open(p))]
assert len(ids) == X.shape[1]
fs = {r["id"]: r["resample_correct"] for r in json.load(open(os.path.join(SYNTH, "results", f"flip_stability_{a.mdir}.json")))}
strict_ph = {i for i, r in fs.items() if not any(r)}
mask = np.array([(yy == 0) or (i in strict_ph) for i, yy in zip(ids, y)])
Xs, ys = X[:, mask, :], y[mask]
print(f"{a.mdir}: strict set {int(mask.sum())} traces, posthoc {int(ys.sum())} (was {int(y.sum())})", flush=True)
def pipe(ntr): return make_pipeline(StandardScaler(), PCA(max(2, min(50, ntr-2)), random_state=0),
                                    LogisticRegression(max_iter=2000, C=1.0))
def cv(Xl, yy):
    skf = StratifiedKFold(5, shuffle=True, random_state=0); oof = np.zeros(len(yy))
    for tr, te in skf.split(Xl, yy):
        oof[te] = pipe(len(tr)).fit(Xl[tr], yy[tr]).predict_proba(Xl[te])[:, 1]
    return roc_auc_score(yy, oof)
NL_h = Xs.shape[0]
curve = [cv(Xs[l].astype(np.float32), ys) for l in range(NL_h)]
b = int(np.argmax(curve))
print(f"within-strict CV best {curve[b]:.3f} @L{b}", flush=True)
w = np.load(os.path.expanduser(f"~/wbrep_{a.mdir}.npz"), allow_pickle=True)
fe, fy = w["cot_end"], w["y"]; NL = min(NL_h, fe.shape[1] - 1)
# project once per layer (scaler+PCA are label-free), then permute labels over LR only
PROJ = []
for l in range(NL):
    sc = StandardScaler().fit(Xs[l].astype(np.float32))
    pc = PCA(max(2, min(50, Xs.shape[1]-2)), random_state=0).fit(sc.transform(Xs[l].astype(np.float32)))
    PROJ.append((pc.transform(sc.transform(Xs[l].astype(np.float32))),
                 pc.transform(sc.transform(fe[:, l+1, :].astype(np.float32)))))
def sweep(yy):
    aucs = []
    for l in range(NL):
        Xtr, Xte = PROJ[l]
        m = LogisticRegression(max_iter=2000, C=1.0).fit(Xtr, yy)
        aucs.append(roc_auc_score(fy, m.predict_proba(Xte)[:, 1]))
    return np.array(aucs)
obs = sweep(ys)
rng = np.random.default_rng(0)
null_means, null_maxs = [], []
for i in range(a.nperm):
    pm = sweep(rng.permutation(ys))
    null_means.append(pm.mean()); null_maxs.append(pm.max())
    if (i+1) % 100 == 0: print(f"  perm {i+1}/{a.nperm}", flush=True)
p_mean = (1 + sum(m >= obs.mean() for m in null_means)) / (1 + a.nperm)
p_best = (1 + sum(m >= obs.max() for m in null_maxs)) / (1 + a.nperm)
res = {"model": a.mdir, "n_strict": int(mask.sum()), "n_posthoc_strict": int(ys.sum()),
       "within_cv_best": float(curve[b]), "within_best_layer": b,
       "transfer_mean": float(obs.mean()), "transfer_best": float(obs.max()),
       "transfer_best_layer": int(obs.argmax()), "p_mean": p_mean, "p_best": p_best}
json.dump(res, open(os.path.join(SYNTH, "results", f"strict_{a.mdir}.json"), "w"), indent=2)
print(f"STRICT DONE {a.mdir}: transfer mean {obs.mean():.3f} p={p_mean:.3f} | best {obs.max():.3f} p={p_best:.3f}", flush=True)
