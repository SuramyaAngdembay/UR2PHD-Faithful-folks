"""
Computes the label-permutation p-value for the hint -> faithcot layer-mean AUROC.
Addresses the TODO in notes/2026-07-11-hint-organic-bridge.md.
Usage: python bridge3_perm.py --mdir llama --nperm 200
"""
import argparse, os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from tqdm import tqdm

ap = argparse.ArgumentParser()
ap.add_argument("--mdir", required=True)
ap.add_argument("--nperm", type=int, default=200)
args = ap.parse_args()

SYNTH = os.path.expanduser("~/synth")

# Load distributions
print(f"Loading data for {args.mdir}...")
h = np.load(os.path.join(SYNTH, f"acts_{args.mdir}_hint.npz"), allow_pickle=True)
hint_get = lambda l, d=h: d["X"][l].astype(np.float32)
hint_y = h["y"]

w = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}.npz"), allow_pickle=True)
fc_get = lambda l, d=w: d["cot_end"][:, l + 1, :].astype(np.float32)
fc_y = w["y"]

NL = min(h["X"].shape[0], w["cot_end"].shape[1] - 1)

print(f"Layers: {NL}, Hint n={len(hint_y)} (ph={int(hint_y.sum())}), FaithCoT n={len(fc_y)} (ph={int(fc_y.sum())})")

rng = np.random.default_rng(42)
perms = [rng.permutation(hint_y) for _ in range(args.nperm)]

obs_aucs = np.zeros(NL)
null_aucs = np.zeros((args.nperm, NL))

print("Computing PCA projections and running permutations per layer...")
for l in tqdm(range(NL)):
    Xh = hint_get(l)
    Xf = fc_get(l)
    
    # Precompute Scaling and PCA
    scaler = StandardScaler()
    Xh_sc = scaler.fit_transform(Xh)
    Xf_sc = scaler.transform(Xf)
    
    nc = max(2, min(50, len(hint_y) - 2))
    pca = PCA(n_components=nc, random_state=0)
    Xh_pca = pca.fit_transform(Xh_sc)
    Xf_pca = pca.transform(Xf_sc)
    
    # Observed AUROC
    lr = LogisticRegression(max_iter=2000, C=1.0)
    lr.fit(Xh_pca, hint_y)
    obs_aucs[l] = roc_auc_score(fc_y, lr.predict_proba(Xf_pca)[:, 1])
    
    # Permutations
    for i, p_y in enumerate(perms):
        lr_null = LogisticRegression(max_iter=2000, C=1.0)
        lr_null.fit(Xh_pca, p_y)
        null_aucs[i, l] = roc_auc_score(fc_y, lr_null.predict_proba(Xf_pca)[:, 1])

obs_mean = obs_aucs.mean()
null_means = null_aucs.mean(axis=1)

pval = (1 + (null_means >= obs_mean).sum()) / (1 + args.nperm)

print(f"\n=== RESULTS FOR {args.mdir} ===")
print(f"Observed hint->faithcot layer-mean AUROC: {obs_mean:.3f}")
print(f"Permutation p-value (n={args.nperm}): {pval:.3f}")

