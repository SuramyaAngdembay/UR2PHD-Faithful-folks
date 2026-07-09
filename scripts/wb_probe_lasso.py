"""
Lasso Probe for Neuron Isolation (EXPLORATORY).
Runs L1-regularized Logistic Regression directly on the full-dimensional hidden states
(no PCA) to isolate the sparse set of neurons/features carrying the post-hoc signal.
Runs on the FaithCoT-Bench white-box reps (real ft1/ft2), which exist only for llama/qwen.
CAVEAT: the reported best-layer AUROC is selected over ~33 layers with NO permutation
correction, so it is optimistically biased; treat it as descriptive (which neurons / how
sparse), not as a headline detection number, until run through the selection-corrected test.
"""
import os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score

for model in ["llama", "qwen"]:
    p = os.path.expanduser(f"~/wbrep_{model}.npz")
    if not os.path.exists(p):
        print(f"\n{model}: no cache"); continue
    
    z = np.load(p, allow_pickle=True)
    y = z["y"].astype(int)
    # Focus on cot_end which was the most predictive position
    X_all_layers = z["cot_end"].astype(np.float32)
    n, L, d = X_all_layers.shape
    
    print(f"\n===== {model} (Lasso Neuron Isolation): n={n} layers={L} d={d} ft2={int(y.sum())} =====", flush=True)
    
    # We will just run this on the previously established best layer to see how many neurons are active
    # (For llama it was L19, qwen L23. We can just sweep or pick the best layer from cvauc)
    
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    best_auroc = 0; best_layer = 0
    best_clf = None
    
    for l in range(L):
        X = StandardScaler().fit_transform(X_all_layers[:, l, :])
        # L1 regularization (Lasso) forces weights to exactly 0
        clf = LogisticRegression(penalty='l1', solver='liblinear', C=0.1, max_iter=1000, random_state=0)
        auc = cross_val_score(clf, X, y, cv=cv, scoring="roc_auc").mean()
        
        if auc > best_auroc:
            best_auroc = auc
            best_layer = l
            
    print(f"  [cot_end] Best Layer {best_layer}/{L-1} L1-AUROC {best_auroc:.3f}", flush=True)
    
    # Fit on the whole dataset for the best layer to see the actual non-zero neurons
    X_best = StandardScaler().fit_transform(X_all_layers[:, best_layer, :])
    final_clf = LogisticRegression(penalty='l1', solver='liblinear', C=0.1, max_iter=1000, random_state=0)
    final_clf.fit(X_best, y)
    
    coefs = final_clf.coef_[0]
    nonzero_idx = np.where(coefs != 0)[0]
    nonzero_weights = coefs[nonzero_idx]
    
    print(f"  Total Neurons (dimensions): {d}")
    print(f"  Active Neurons (L1 non-zero): {len(nonzero_idx)}")
    
    # Print the top 5 most important neurons
    if len(nonzero_idx) > 0:
        top_indices = nonzero_idx[np.argsort(-np.abs(nonzero_weights))][:5]
        print("  Top Neurons (Index: Weight):")
        for idx in top_indices:
            print(f"    - Neuron {idx}: {coefs[idx]:.4f}")
print("\nPROBE_LASSO DONE", flush=True)
