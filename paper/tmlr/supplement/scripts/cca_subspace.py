"""
Direction/subspace geometry between constructions and the annotated incorrect regime --
the SAE-free answer to "what does the transferring direction share?" (follows the
instrument-limited SAE pass; see notes/2026-07-16-sae-what-transfers-pass1.md).

Per layer L (synth layer l == wbrep layer l+1), in RAW residual space:
  A. mean-difference directions d_set = norm(mu_pos - mu_neg):
     cos(d_hint, d_ft1v2), cos(d_instructed, d_ft1v2), cos(d_hint, d_instructed)
     + permutation null (labels shuffled within BOTH sets, 1000 perms, all layers;
       selection-corrected max-|cos|-over-layers AND layer-mean statistics, coupled perms)
  B. LR probe directions (standardized-space coef mapped back to raw): same cosines
     (descriptive; focus layers only, they are expensive to permute)
  C. rank-k discriminative subspaces (k=5, SVD over 20 bootstrap LR directions):
     mean squared canonical cosine between subspaces (focus layers, 100 perms)
Controls: cos with the QUESTION-ONLY (difficulty) direction from qacts, where available.
Output: ~/synth/results/cca_subspace_<model>.json
Run: python cca_subspace.py --model llama [--nperm 1000] [--focus 17 25 29]
"""
import argparse, json, os
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="llama")
ap.add_argument("--nperm", type=int, default=1000)
ap.add_argument("--focus", type=int, nargs="+", default=[9, 17, 25, 29])
ap.add_argument("--boot", type=int, default=20)
ap.add_argument("--rank", type=int, default=5)
args = ap.parse_args()
rng = np.random.default_rng(0)
SYNTH = os.path.expanduser("~/synth")

def load_sets(m):
    sets = {}
    d = np.load(os.path.join(SYNTH, f"acts_{m}.npz"), allow_pickle=True)
    sets["instructed"] = (d["X"].astype(np.float32), d["y"].astype(int))
    d = np.load(os.path.join(SYNTH, f"acts_{m}_hint.npz"), allow_pickle=True)
    sets["hint"] = (d["X"].astype(np.float32), d["y"].astype(int))
    w = np.load(os.path.expanduser(f"~/wbrep_{m}.npz"), allow_pickle=True)
    sets["ft1v2"] = (np.transpose(w["cot_end"], (1, 0, 2))[1:].astype(np.float32), w["y"].astype(int))
    q = os.path.join(SYNTH, f"qacts_{m}_hint.npz")
    if os.path.exists(q):
        d = np.load(q, allow_pickle=True)
        sets["qonly"] = (d["X"].astype(np.float32), d["y"].astype(int))
    return sets

def mdiff(X, y):
    d = X[y == 1].mean(0) - X[y == 0].mean(0)
    return d / (np.linalg.norm(d) + 1e-12)

def _proj(X):
    """Scaler+PCA-50 fit once; returns (Z, back) where back maps a PCA-space LR coef to a
    unit direction in RAW residual space: logit = w.(Pz) = (P^T w).z = ((P^T w)/sigma).x"""
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    sc = StandardScaler().fit(X)
    pc = PCA(n_components=min(50, X.shape[0] - 2), random_state=0).fit(sc.transform(X))
    Z = pc.transform(sc.transform(X))
    def back(w_pca):
        w = (pc.components_.T @ w_pca) / (sc.scale_ + 1e-9)
        return w / (np.linalg.norm(w) + 1e-12)
    return Z, back

def _lr_pca(Z, y):
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(max_iter=2000, C=1.0).fit(Z, y).coef_[0]

def lr_dir(X, y):
    Z, back = _proj(X)
    return back(_lr_pca(Z, y))

def subspace_from(Z, back, y, k, nboot):
    dirs, n = [], len(y)
    for _ in range(nboot):
        i = rng.integers(0, n, n)
        if len(set(y[i])) < 2: continue
        dirs.append(back(_lr_pca(Z[i], y[i])))
    U, _, _ = np.linalg.svd(np.array(dirs).T, full_matrices=False)
    return U[:, :k]

def sub_sim(U, V):                    # mean squared canonical cosine
    s = np.linalg.svd(U.T @ V, compute_uv=False)
    return float((s ** 2).mean())

sets = load_sets(args.model)
NL = min(s[0].shape[0] for s in sets.values())
PAIRS = [("hint", "ft1v2"), ("instructed", "ft1v2"), ("hint", "instructed")]
if "qonly" in sets:
    PAIRS += [("qonly", "ft1v2"), ("qonly", "hint")]
print(f"[{args.model}] layers {NL}, sets {list(sets)}", flush=True)

res = {"model": args.model, "n_layers": NL, "nperm": args.nperm,
       "mean_diff": {}, "lr_dirs": {}, "subspace": {}}

# ---- A. mean-difference cosines, all layers + coupled permutation null ----
D = {name: np.stack([mdiff(X[l], y) for l in range(NL)]) for name, (X, y) in sets.items()}
obs = {f"{a}->{b}": np.array([float(D[a][l] @ D[b][l]) for l in range(NL)]) for a, b in PAIRS}
null_max, null_mean = {p: [] for p in obs}, {p: [] for p in obs}
for it in range(args.nperm):
    Dp = {}
    for name, (X, y) in sets.items():
        yp = rng.permutation(y)
        Dp[name] = np.stack([mdiff(X[l], yp) for l in range(NL)])
    for a, b in PAIRS:
        c = np.array([Dp[a][l] @ Dp[b][l] for l in range(NL)])
        null_max[f"{a}->{b}"].append(np.abs(c).max())
        null_mean[f"{a}->{b}"].append(c.mean())
    if (it + 1) % 200 == 0: print(f"  perm {it+1}/{args.nperm}", flush=True)
for p in obs:
    o = obs[p]; nm, nmn = np.array(null_max[p]), np.array(null_mean[p])
    res["mean_diff"][p] = {
        "per_layer_cos": [round(float(c), 4) for c in o],
        "max_abs_cos": round(float(np.abs(o).max()), 4),
        "max_layer": int(np.abs(o).argmax()),
        "mean_cos": round(float(o.mean()), 4),
        "p_max": float(((nm >= np.abs(o).max()).sum() + 1) / (args.nperm + 1)),
        "p_mean": float(((nmn >= o.mean()).sum() + 1) / (args.nperm + 1)),
        "null_max_p95": round(float(np.percentile(nm, 95)), 4)}
    print(f"[mean-diff] {p}: max|cos| {res['mean_diff'][p]['max_abs_cos']} @L{res['mean_diff'][p]['max_layer']} "
          f"(p={res['mean_diff'][p]['p_max']:.3f}) mean {res['mean_diff'][p]['mean_cos']} "
          f"(p={res['mean_diff'][p]['p_mean']:.3f})", flush=True)

out = os.path.join(SYNTH, "results", f"cca_subspace_{args.model}.json")
json.dump(res, open(out, "w"), indent=1)          # checkpoint after tier A

# ---- B. LR directions + C. subspaces at focus layers (PCA-space fits, raw-space geometry) ----
for L in args.focus:
    if L >= NL: continue
    pr = {name: _proj(X[L]) for name, (X, y) in sets.items()}
    lw = {name: pr[name][1](_lr_pca(pr[name][0], y)) for name, (X, y) in sets.items()}
    res["lr_dirs"][str(L)] = {f"{a}->{b}": round(float(lw[a] @ lw[b]), 4) for a, b in PAIRS}
    Us = {name: subspace_from(*pr[name], y, args.rank, args.boot) for name, (X, y) in sets.items()}
    ss = {}
    for a, b in PAIRS:
        o = sub_sim(Us[a], Us[b])
        nulls = []
        for _ in range(100):
            ya, yb = sets[a][1], sets[b][1]
            nulls.append(sub_sim(subspace_from(*pr[a], rng.permutation(ya), args.rank, max(8, args.boot // 2)),
                                 subspace_from(*pr[b], rng.permutation(yb), args.rank, max(8, args.boot // 2))))
        ss[f"{a}->{b}"] = {"sim": round(o, 4), "null_p95": round(float(np.percentile(nulls, 95)), 4),
                           "p": float((np.sum(np.array(nulls) >= o) + 1) / 101)}
    res["subspace"][str(L)] = ss
    json.dump(res, open(out, "w"), indent=1)      # checkpoint per layer
    print(f"[L{L}] lr-cos {res['lr_dirs'][str(L)]} | subspace " +
          " ".join(f"{k}:{v['sim']}(p={v['p']:.2f})" for k, v in ss.items()), flush=True)

json.dump(res, open(out, "w"), indent=1)
print(f"CCA_SUBSPACE DONE {args.model} -> {out}", flush=True)
