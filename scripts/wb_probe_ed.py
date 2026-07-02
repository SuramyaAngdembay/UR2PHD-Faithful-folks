"""
Item (e): proper evaluation as a DETECTOR -- repeated stratified 70/30 held-out splits (not
in-sample CV) -> mean held-out AUROC +/- std and F1, vs the black-box baseline (0.50 on ft1v2).
Item (d): cross-domain generalization -- leave-one-domain-out (train on 3 domains, test on the
held-out one) -> per-domain held-out AUROC. Both at the best cot_end layer. Strict pipeline.
"""
import os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import roc_auc_score, f1_score

BESTLAYER = {"llama": 19, "qwen": 23}
def pipe(nc): return make_pipeline(StandardScaler(), PCA(n_components=nc), LogisticRegression(C=1.0, max_iter=2000))

for model in ["llama", "qwen"]:
    p = os.path.expanduser(f"~/wbrep_{model}.npz")
    if not os.path.exists(p):
        print(f"{model}: no cache"); continue
    z = np.load(p, allow_pickle=True)
    y = z["y"].astype(int); dom = z["domain"].astype(str)
    X = z["cot_end"].astype(np.float32)[:, BESTLAYER[model], :]
    nc = min(50, len(y) - 30)
    print(f"\n=== {model} (cot_end L{BESTLAYER[model]}, n={len(y)}) ===", flush=True)
    # (e) repeated held-out
    sss = StratifiedShuffleSplit(n_splits=25, test_size=0.3, random_state=0)
    aucs, f1s = [], []
    for tr, te in sss.split(X, y):
        clf = pipe(nc).fit(X[tr], y[tr]); pr = clf.predict_proba(X[te])[:, 1]
        aucs.append(roc_auc_score(y[te], pr)); f1s.append(f1_score(y[te], (pr >= 0.5).astype(int)))
    print(f"  (e) held-out 25x70/30: AUROC {np.mean(aucs):.3f}+/-{np.std(aucs):.3f} | "
          f"F1 {np.mean(f1s):.3f} | vs black-box baseline 0.50", flush=True)
    # (d) leave-one-domain-out
    print("  (d) leave-one-domain-out:", flush=True)
    for held in sorted(set(dom)):
        trm, tem = dom != held, dom == held
        if tem.sum() < 8 or len(set(y[tem])) < 2 or len(set(y[trm])) < 2:
            print(f"      test={held:11s} n={int(tem.sum())} (skip: too few/one-class)"); continue
        clf = pipe(min(nc, int(trm.sum()) - 30)).fit(X[trm], y[trm]); pr = clf.predict_proba(X[tem])[:, 1]
        print(f"      train!={held:11s} -> test {held:11s}: AUROC {roc_auc_score(y[tem], pr):.3f} "
              f"(n_test={int(tem.sum())}, %ft2={y[tem].mean():.2f})", flush=True)
print("\nPROBE_ED DONE", flush=True)
