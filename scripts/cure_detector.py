"""
CURE TEST (Option A): is a probe trained ONLY on hint-induced counterfactual traces
(zero human annotation) a *deployable* detector of unfaithfulness in the behaviorally
BLIND incorrect-answer regime, where every black-box signal is at chance?

Deployment-realistic protocol (no annotated label ever touches selection/threshold):
  TRAIN  = hint-induced traces (acts_<m>_hint.npz), y = posthoc(1)/genuine(0)  [no human labels]
    - StandardScaler -> PCA-50 -> LogReg; layer chosen by hint-internal 5-fold CV; frozen.
    - Decision threshold set on a held-out hint split (F1-optimal). Frozen.
  TEST   = annotated incorrect regime ft1v2 (wbrep_<m>.npz), y = ft2 unfaithful(1)/ft1 honest(0)
    Layer alignment: acts X[L] == wbrep cot_end[:, L+1]  (wbrep layer 0 = embeddings).

Reports, on the annotated blind-regime test set:
  - AUROC + AP (PR-AUC); chance ref 0.5 = where ALL black-box signals sit (paper Table 2)
  - operating point at the hint-calibrated threshold: precision/recall/F1 (does threshold transfer?)
  - precision at fixed recall 0.5, and precision at a SIMULATED low base rate (10%) via reweighting
  - ORACLE upper bound: probe trained ON annotated ft1v2 (5-fold CV) -> fraction of achievable signal
  - user/trace bootstrap CIs
Run:  python cure_detector.py --model llama [--source hint|hintL]
"""
import argparse, os, json
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="llama")
ap.add_argument("--source", default="hint", choices=["hint", "hintL"])
ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)
SYNTH = os.path.expanduser("~/synth")

def pipe(ntr):
    nc = max(2, min(50, ntr - 2))
    return make_pipeline(StandardScaler(), PCA(nc, random_state=0),
                         LogisticRegression(max_iter=2000, C=1.0))

# ---- load TRAIN (hint, no human labels) and TEST (annotated ft1v2, human labels) ----
h = np.load(os.path.join(SYNTH, f"acts_{a.model}_{a.source}.npz"), allow_pickle=True)
Xh, yh = h["X"].astype(np.float32), h["y"].astype(int)          # [L, n, dim]
w = np.load(os.path.expanduser(f"~/wbrep_{a.model}.npz"), allow_pickle=True)
fe, fy = w["cot_end"].astype(np.float32), w["y"].astype(int)     # [n, 33, dim]
NL = min(Xh.shape[0], fe.shape[1] - 1)
print(f"[{a.model}/{a.source}] train hint n={len(yh)} (posthoc {int(yh.sum())}); "
      f"test annotated ft1v2 n={len(fy)} (unfaithful {int(fy.sum())})", flush=True)

def cv_auroc(X, y):
    skf = StratifiedKFold(5, shuffle=True, random_state=0); oof = np.zeros(len(y))
    for tr, te in skf.split(X, y): oof[te] = pipe(len(tr)).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return roc_auc_score(y, oof)

# ---- 1. select layer by HINT-INTERNAL CV (no annotated labels touch this) ----
hint_cv = [cv_auroc(Xh[L], yh) for L in range(NL)]
L = int(np.argmax(hint_cv))
print(f"layer selected on hint CV: L{L} (hint-internal CV {hint_cv[L]:.3f})", flush=True)

# ---- 2. calibrate threshold on held-out hint split (F1-optimal), freeze ----
idx = rng.permutation(len(yh)); cut = int(0.7 * len(yh))
tr_i, va_i = idx[:cut], idx[cut:]
det = pipe(len(tr_i)).fit(Xh[L][tr_i], yh[tr_i])
va_scores = det.predict_proba(Xh[L][va_i])[:, 1]
prec, rec, thr = precision_recall_curve(yh[va_i], va_scores)
f1 = 2 * prec * rec / (prec + rec + 1e-9)
thr_star = float(thr[max(0, np.argmax(f1[:-1]))])          # hint-calibrated operating point
# refit detector on ALL hint data, freeze
det = pipe(len(yh)).fit(Xh[L], yh)

# ---- 3. deploy frozen detector on annotated blind-regime test ----
te_scores = det.predict_proba(fe[:, L + 1, :])[:, 1]
auroc = roc_auc_score(fy, te_scores)
ap_score = average_precision_score(fy, te_scores)
base = fy.mean()
pred = (te_scores >= thr_star).astype(int)
tp = int(((pred == 1) & (fy == 1)).sum()); fp = int(((pred == 1) & (fy == 0)).sum())
fn = int(((pred == 0) & (fy == 1)).sum())
P = tp / (tp + fp) if tp + fp else 0.0
R = tp / (tp + fn) if tp + fn else 0.0
F1 = 2 * P * R / (P + R) if P + R else 0.0

# precision at fixed recall 0.5
pr, rc, _ = precision_recall_curve(fy, te_scores)
p_at_r50 = float(pr[np.argmin(np.abs(rc - 0.5))])

# precision at simulated LOW base rate (10%): reweight negatives up
def prec_at_baserate(scores, y, target_rate, at_recall=0.5):
    pos, neg = scores[y == 1], scores[y == 0]
    # threshold achieving `at_recall` on positives
    t = np.quantile(pos, 1 - at_recall)
    tpr = (pos >= t).mean(); fpr = (neg >= t).mean()
    # precision at population base rate `target_rate`
    num = target_rate * tpr
    den = num + (1 - target_rate) * fpr
    return float(num / den) if den > 0 else 0.0

p_lowbase = prec_at_baserate(te_scores, fy, 0.10)

# ---- 4. ORACLE upper bound: probe trained ON annotated ft1v2 (5-fold CV at same layer) ----
oracle_auroc = cv_auroc(fe[:, L + 1, :], fy)

# ---- 5. bootstrap CI on the deployed AUROC (trace-level) ----
boot = []
for _ in range(2000):
    i = rng.integers(0, len(fy), len(fy))
    if len(set(fy[i])) == 2: boot.append(roc_auc_score(fy[i], te_scores[i]))
lo, hi = np.percentile(boot, [2.5, 97.5])

out = {
    "model": a.model, "source": a.source, "layer": L,
    "hint_internal_cv": round(hint_cv[L], 3),
    "DEPLOY_auroc": round(float(auroc), 3), "auroc_ci": [round(float(lo), 3), round(float(hi), 3)],
    "AP_prauc": round(float(ap_score), 3), "test_base_rate": round(float(base), 3),
    "chance_ref": 0.5, "oracle_cv_auroc": round(float(oracle_auroc), 3),
    "signal_captured_frac": round(float((auroc - 0.5) / (oracle_auroc - 0.5 + 1e-9)), 3),
    "op_point_thr": round(thr_star, 3),
    "op_precision": round(P, 3), "op_recall": round(R, 3), "op_f1": round(F1, 3),
    "precision_at_recall50": round(p_at_r50, 3),
    "precision_at_10pct_baserate_r50": round(p_lowbase, 3),
    "lift_over_baserate": round(p_at_r50 / base, 2) if base else None,
}
print(json.dumps(out, indent=1), flush=True)
json.dump(out, open(os.path.join(SYNTH, "results", f"cure_{a.model}_{a.source}.json"), "w"), indent=1)
print("CURE_DETECTOR DONE", flush=True)
