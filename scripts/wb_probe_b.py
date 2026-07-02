"""
Item (b): does a NONLINEAR probe recover more post-hoc signal than a linear one?
At the best cot_end layer (from item a), compare LogisticRegression vs a small MLP, using
STRICT PCA-in-CV (PCA refit inside each fold -> no leakage; trustworthy absolute AUROC).
Shuffled-label control included. Reads cache. CPU.
"""
import os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score

BESTLAYER = {"llama": 19, "qwen": 23}  # best cot_end layer from item (a)
for model in ["llama", "qwen"]:
    p = os.path.expanduser(f"~/wbrep_{model}.npz")
    if not os.path.exists(p):
        print(f"{model}: no cache"); continue
    z = np.load(p, allow_pickle=True)
    y = z["y"].astype(int)
    X = z["cot_end"].astype(np.float32)[:, BESTLAYER[model], :]
    cv = StratifiedKFold(5, shuffle=True, random_state=0); nc = min(50, len(y) - 25)
    def run(clf, yy):
        return cross_val_score(make_pipeline(StandardScaler(), PCA(nc), clf), X, yy, cv=cv, scoring="roc_auc").mean()
    lin = run(LogisticRegression(C=1.0, max_iter=2000), y)
    mlp = run(MLPClassifier((64,), alpha=1.0, max_iter=1500, random_state=0), y)
    ysh = np.random.default_rng(0).permutation(y)
    ctrl = run(LogisticRegression(C=1.0, max_iter=2000), ysh)
    print(f"{model} (cot_end L{BESTLAYER[model]}, strict PCA-in-CV): "
          f"linear {lin:.3f} | MLP {mlp:.3f} | shuffled-control {ctrl:.3f}", flush=True)
print("PROBE_B DONE", flush=True)
