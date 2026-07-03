"""
Item (a): representation/position sweep + pre-CoT answer-decodability. Reads cached reps. CPU.
FAST design: PCA is label-free, so project each (position,layer) to 50-d ONCE, then the layer
sweep + 200-permutation null just refit logistic on 50-d (valid for a label-permutation null).
(a1) position {pre_cot, cot_end, cot_mean} x layer -> CV-AUROC for ft2; global best + perm p.
(a2) decode the model's ANSWER from the pre-CoT state; is it MORE decodable for post-hoc (ft2)?
"""
import os
from collections import Counter
import numpy as np
from scipy.stats import mannwhitneyu
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict

POSITIONS = ["pre_cot", "cot_end", "cot_mean"]

def project(X, nc):  # label-free standardize + PCA, fit once
    return PCA(n_components=nc, random_state=0).fit_transform(StandardScaler().fit_transform(X))

def cvauc(Z, y, cv):
    return cross_val_score(LogisticRegression(C=1.0, max_iter=1000), Z, y, cv=cv, scoring="roc_auc").mean()

for model in ["llama", "qwen", "deepseek"]:
    p = os.path.expanduser(f"~/wbrep_{model}.npz")
    if not os.path.exists(p):
        print(f"\n{model}: no cache"); continue
    z = np.load(p, allow_pickle=True)
    y = z["y"].astype(int); ans = z["ans"].astype(str)
    reps = {pos: z[pos].astype(np.float32) for pos in POSITIONS}
    n, L, d = reps["pre_cot"].shape
    nc = min(50, n - 25); cv = StratifiedKFold(5, shuffle=True, random_state=0)
    print(f"\n===== {model}: n={n} layers={L} d={d} ft2={int(y.sum())} =====", flush=True)
    Z = {(pos, l): project(reps[pos][:, l, :], nc) for pos in POSITIONS for l in range(L)}
    grid = {}
    for pos in POSITIONS:
        aucs = [cvauc(Z[(pos, l)], y, cv) for l in range(L)]
        bl = int(np.argmax(aucs)); grid[pos] = (bl, aucs[bl])
        print(f"  [{pos:8s}] best layer {bl:2d}/{L-1} AUROC {aucs[bl]:.3f}", flush=True)
    gpos, (gbl, gbest) = max(grid.items(), key=lambda kv: kv[1][1])
    rng = np.random.default_rng(0); nullmax = []
    for _ in range(200):
        yp = rng.permutation(y)
        nullmax.append(max(cvauc(Z[(pos, l)], yp, cv) for pos in POSITIONS for l in range(L)))
    nullmax = np.array(nullmax); pval = (np.sum(nullmax >= gbest) + 1) / (len(nullmax) + 1)
    print(f"  GLOBAL best: {gpos} L{gbl} AUROC {gbest:.3f} | null(max) mean {nullmax.mean():.3f} "
          f"p95 {np.percentile(nullmax,95):.3f} | p={pval:.4f}", flush=True)
    # (a2) pre-CoT answer-decodability
    prebl = grid["pre_cot"][0]
    valid = np.array([v not in ("?", "None", "", "nan") for v in ans])
    Xa, ya, yft = reps["pre_cot"][valid][:, prebl, :], ans[valid], y[valid]
    cnt = Counter(ya); keep = np.array([cnt[v] >= 5 for v in ya])
    Xa, ya, yft = Xa[keep], ya[keep], yft[keep]
    if len(set(ya)) < 2 or len(ya) < 20:
        print("  [a2] too few valid answers; skip"); continue
    yc = LabelEncoder().fit_transform(ya); folds = min(5, min(Counter(yc).values()))
    if folds < 2:
        print("  [a2] answer class too small; skip"); continue
    Za = project(Xa, min(50, Xa.shape[0] - 25))
    proba = cross_val_predict(LogisticRegression(C=1.0, max_iter=1000), Za, yc,
                              cv=StratifiedKFold(folds, shuffle=True, random_state=0), method="predict_proba")
    dec = proba[np.arange(len(yc)), yc]
    acc = (proba.argmax(1) == yc).mean(); chance = 1.0 / len(set(yc))
    d1, d2 = dec[yft == 0], dec[yft == 1]
    _, pu = mannwhitneyu(d2, d1, alternative="greater")
    print(f"  [a2 pre-CoT answer-decodability @L{prebl}] decode-acc {acc:.3f} (chance {chance:.3f}); "
          f"P(true|pre-CoT): genuine {d1.mean():.3f} vs post-hoc {d2.mean():.3f}; "
          f"MWU p(posthoc>genuine)={pu:.4f} (n1={len(d1)}, n2={len(d2)})", flush=True)
print("\nPROBE_A DONE", flush=True)
