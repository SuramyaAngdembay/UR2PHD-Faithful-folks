"""Reviewer-fix evaluation: (a) problem-GROUPED train/test splits (paired construction) and
(b) NESTED layer selection (layer chosen on train only, inner 3-fold). 10x grouped 70/30
splits per instructed model; 25x for FaithCoT (unique problems, nested only).
Output: ~/synth/results/grouped_nested.json"""
import json, os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit, GroupKFold, StratifiedShuffleSplit, StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
SYNTH = os.path.expanduser("~/synth")
def pipe(ntr): return make_pipeline(StandardScaler(), PCA(max(2, min(50, ntr - 2)), random_state=0),
                                    LogisticRegression(max_iter=2000, C=1.0))
def nested_eval(X, y, groups, n_splits, layers):
    """grouped outer splits; inner 3-fold (grouped) picks layer on train only."""
    outer = (GroupShuffleSplit(n_splits=n_splits, test_size=0.3, random_state=0).split(X[0], y, groups)
             if groups is not None else
             StratifiedShuffleSplit(n_splits=n_splits, test_size=0.3, random_state=0).split(X[0], y))
    aucs, picked = [], []
    for tr, te in outer:
        best_l, best_a = layers[0], -1
        inner = (GroupKFold(3).split(X[0][tr], y[tr], np.asarray(groups)[tr]) if groups is not None
                 else StratifiedKFold(3, shuffle=True, random_state=1).split(X[0][tr], y[tr]))
        inner = list(inner)
        for l in layers:
            oof = np.zeros(len(tr))
            okfold = True
            for itr, ite in inner:
                if len(np.unique(y[tr][itr])) < 2 or len(np.unique(y[tr][ite])) < 2: okfold = False; break
                m = pipe(len(itr)).fit(X[l][tr][itr], y[tr][itr])
                oof[ite] = m.predict_proba(X[l][tr][ite])[:, 1]
            if not okfold: continue
            a = roc_auc_score(y[tr], oof)
            if a > best_a: best_a, best_l = a, l
        m = pipe(len(tr)).fit(X[best_l][tr], y[tr])
        aucs.append(roc_auc_score(y[te], m.predict_proba(X[best_l][te])[:, 1])); picked.append(best_l)
    return float(np.mean(aucs)), float(np.std(aucs)), picked
out = {}
# instructed construction: 7 models, grouped by problem id
for mdir in ("qwen", "gemma4", "llama", "qwen3", "deepseek", "gemma", "dsr0528"):
    d = np.load(os.path.join(SYNTH, f"acts_{mdir}.npz"), allow_pickle=True)
    X, y = d["X"].astype(np.float16), d["y"]
    ids = []
    for ds in ("aqua", "gsm8k", "aquarat"):
        p = os.path.join(SYNTH, f"traces_{mdir}_{ds}.json")
        if os.path.exists(p): ids += [t["id"] for t in json.load(open(p))]
    assert len(ids) == X.shape[1], f"{mdir}: id/row mismatch {len(ids)} vs {X.shape[1]}"
    NL = X.shape[0]; layers = list(range(0, NL, 2))
    Xf = {l: X[l].astype(np.float32) for l in layers}
    mean, std, picked = nested_eval(Xf, y, np.array(ids), 10, layers)
    out[f"instructed_{mdir}"] = {"grouped_nested_auroc": mean, "std": std,
                                 "picked_layers": picked}
    print(f"instructed {mdir}: grouped+nested held-out {mean:.3f} +/- {std:.3f} (layers picked {sorted(set(picked))})", flush=True)
# FaithCoT real labels: nested only (each trace a distinct question)
for m in ("llama", "qwen"):
    w = np.load(os.path.expanduser(f"~/wbrep_{m}.npz"), allow_pickle=True)
    fe, fy = w["cot_end"], w["y"]; NL = fe.shape[1] - 1
    layers = list(range(0, NL, 2))
    Xf = {l: fe[:, l + 1, :].astype(np.float32) for l in layers}
    mean, std, picked = nested_eval(Xf, fy, None, 25, layers)
    out[f"faithcot_{m}"] = {"nested_auroc": mean, "std": std, "picked_layers": picked}
    print(f"faithcot {m}: nested held-out {mean:.3f} +/- {std:.3f}", flush=True)
json.dump(out, open(os.path.join(SYNTH, "results", "grouped_nested.json"), "w"), indent=2)
print("GROUPED_NESTED DONE", flush=True)
