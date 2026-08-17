"""
Judge-probe COMPLEMENTARITY in the metric-blind regime (Llama ft1v2, n=144).

Question (revision review, 2026-08-16): a black-box judge call scores 0.679 pooled in the
metric-blind regime, ~matching the Llama probe's 0.67 +- 0.08 -- does the probe add anything
over the judge? Apples-to-apples on the SAME traces:
  - judge AUROC on the 144 Llama ft1v2 traces (its weakest per-model cell: 0.599)
  - probe OOF AUROC (5-fold CV @ disclosed full-data best layer; + nested variant)
  - Spearman(judge, probe) score correlation
  - combined (rank-mean of z-scored signals; and 2-feature CV logistic)
  - paired bootstrap deltas: probe-judge, combined-judge
  - probe AUROC on the judge-ambiguous middle tercile

Alignment: reconstructs wb_extract.py's exact trace order (DOMAINS loop + unsorted glob,
ft in {1,2}, non-empty steps) and VALIDATES against the npz's stored dom/y/ans/correct
sequences; aborts on any mismatch. Run on the GPU server (CPU-only).
"""
import json, glob, os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr

BASE = os.path.expanduser("~/project/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
DOMAINS = ["truthfulqa", "logiqa", "aqua", "HLE_BIO"]
MDIR = "llama-3.1-8b-instruct"
RAW = os.path.expanduser("~/synth/results/judge_raw.jsonl")
OUT = os.path.expanduser("~/synth/results/judge_probe_comp.json")

# ---- 1. reconstruct wb_extract order with rids ----
recs = []
for dom in DOMAINS:
    for f in glob.glob(os.path.join(BASE, dom, MDIR, "response_*.json")):
        d = json.load(open(f)); ft = d.get("faithful_type")
        if ft not in (1, 2): continue
        s = d["sample_0"]
        steps = [k for k in s if k.startswith("step_")]
        if not steps: continue
        recs.append(dict(rid=f"{dom}/{MDIR}/{os.path.basename(f)}", dom=dom,
                         y=1 if ft == 2 else 0, ans=str(s.get("parsed_final_answer", "?")),
                         correct=1 if s.get("parsed_final_answer") == d.get("label") else 0))
w = np.load(os.path.expanduser("~/wbrep_llama.npz"), allow_pickle=True)
fe, fy = w["cot_end"].astype(np.float32), w["y"].astype(int)
assert len(recs) == len(fy), f"count mismatch {len(recs)} vs {len(fy)}"
for i, r in enumerate(recs):
    assert r["dom"] == str(w["domain"][i]), f"dom mismatch at {i}"
    assert r["y"] == int(fy[i]), f"y mismatch at {i}"
    assert r["ans"] == str(w["ans"][i]), f"ans mismatch at {i}"
    assert r["correct"] == int(w["correct"][i]), f"correct mismatch at {i}"
print(f"alignment VALIDATED: {len(recs)} traces, all 4 fields match", flush=True)

# ---- 2. judge scores ----
js = {}
for line in open(RAW):
    d = json.loads(line); js[d["rid"]] = d["score"]
judge = np.array([js[r["rid"]] for r in recs], float)
y = fy.astype(int)

# ---- 3. probe OOF scores ----
def pipe(ntr):
    return make_pipeline(StandardScaler(), PCA(min(50, ntr - 2), random_state=0),
                         LogisticRegression(max_iter=2000))
def oof_at(L, seed=0):
    X = fe[:, L, :]
    skf = StratifiedKFold(5, shuffle=True, random_state=seed)
    o = np.zeros(len(y))
    for tr, te in skf.split(X, y): o[te] = pipe(len(tr)).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return o
NL = fe.shape[1]
cv = [roc_auc_score(y, oof_at(L)) for L in range(1, NL)]
Lbest = int(np.argmax(cv)) + 1
probe = oof_at(Lbest)
# nested variant: inner CV picks layer per outer fold
skf = StratifiedKFold(5, shuffle=True, random_state=1)
probe_nested = np.zeros(len(y))
for tr, te in skf.split(fe[:, 0, :], y):
    inner = []
    for L in range(1, NL):
        Xtr = fe[tr][:, L, :]
        io = np.zeros(len(tr))
        ik = StratifiedKFold(3, shuffle=True, random_state=0)
        for itr, ite in ik.split(Xtr, y[tr]): io[ite] = pipe(len(itr)).fit(Xtr[itr], y[tr][itr]).predict_proba(Xtr[ite])[:, 1]
        inner.append(roc_auc_score(y[tr], io))
    Lf = int(np.argmax(inner)) + 1
    probe_nested[te] = pipe(len(tr)).fit(fe[tr][:, Lf, :], y[tr]).predict_proba(fe[te][:, Lf, :])[:, 1]
print(f"probe: best layer L{Lbest} (CV {max(cv):.3f}); nested OOF {roc_auc_score(y, probe_nested):.3f}", flush=True)

# ---- 4. combination + stats ----
def z(x): return (x - x.mean()) / (x.std() + 1e-9)
comb_rank = z(judge) + z(probe)
comb_rank_n = z(judge) + z(probe_nested)
# 2-feature CV logistic
skf = StratifiedKFold(5, shuffle=True, random_state=2)
F = np.stack([z(judge), z(probe_nested)], 1)
comb_lr = np.zeros(len(y))
for tr, te in skf.split(F, y):
    comb_lr[te] = LogisticRegression(max_iter=1000).fit(F[tr], y[tr]).predict_proba(F[te])[:, 1]

rng = np.random.default_rng(0)
def pboot(s1, s2, B=5000):
    """paired bootstrap CI for AUROC(s1)-AUROC(s2)"""
    ds = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i])) < 2: continue
        ds.append(roc_auc_score(y[i], s1[i]) - roc_auc_score(y[i], s2[i]))
    return [round(float(q), 3) for q in np.percentile(ds, [2.5, 97.5])]

terc = np.argsort(np.argsort(judge)) / len(judge)
mid = (terc >= 1/3) & (terc < 2/3)
res = {
 "n": len(y), "pos": int(y.sum()),
 "judge_auroc_same_traces": round(roc_auc_score(y, judge), 3),
 "probe_bestlayer_auroc": round(roc_auc_score(y, probe), 3), "best_layer": Lbest,
 "probe_nested_auroc": round(roc_auc_score(y, probe_nested), 3),
 "spearman_judge_probe": round(float(spearmanr(judge, probe_nested).statistic), 3),
 "combined_rankmean_auroc": round(roc_auc_score(y, comb_rank_n), 3),
 "combined_rankmean_bestlayer_auroc": round(roc_auc_score(y, comb_rank), 3),
 "combined_logistic_auroc": round(roc_auc_score(y, comb_lr), 3),
 "delta_probe_minus_judge_ci": pboot(probe_nested, judge),
 "delta_combined_minus_judge_ci": pboot(comb_rank_n, judge),
 "probe_on_judge_middle_tercile": {"n": int(mid.sum()),
     "auroc": round(roc_auc_score(y[mid], probe_nested[mid]), 3) if len(set(y[mid])) == 2 else None},
}
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(res, indent=1))
print("COMP DONE", flush=True)
