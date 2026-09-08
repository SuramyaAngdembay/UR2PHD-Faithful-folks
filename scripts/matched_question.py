"""Matched-question decomposition of the template transfer difference (reviewer plan, 2026-09-08).

The sycophancy and metadata math testbeds share only 55 (Llama) / 10 (Qwen) positive questions, so
the observed transfer difference (0.616 vs 0.451) confounds hint WORDING with QUESTION SELECTION
and the responses generated. This analysis trains both template probes on the SAME question sets
(each arm using its own template's responses/activations for those questions) and evaluates both on
the same annotated target, isolating wording+response from selection.

Arms:
  syc-matched / meta-matched : probes trained only on the shared questions
                               (posthoc = shared-positive set, genuine = shared-genuine set;
                                metadata side uses the CLEANED cache exclusions).
  syc-size / meta-size       : M random subsets of each FULL template set at the same class
                               sizes -- the control that separates "matching changed the data"
                               from "the matched set is just small".
Uncertainty for the matched contrast: B question-level refit draws. Each draw resamples the shared
positive and shared genuine QUESTION lists (with replacement, one draw shared by both arms), refits
both probes per layer on their own activations for the drawn questions, scores the fixed annotated
target, and records layer-mean AUROCs and their difference. This measures source-training
uncertainty, which the frozen-probe intervals elsewhere do not.

Usage: python matched_question.py --mdir llama [--refits 200] [--sizedraws 200]
Output: ~/synth/results/matched_question_<mdir>.json
"""
import argparse, json, os, re
import numpy as np
from scipy.stats import rankdata
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

ap = argparse.ArgumentParser()
ap.add_argument("--mdir", required=True)
ap.add_argument("--refits", type=int, default=200)
ap.add_argument("--sizedraws", type=int, default=200)
args = ap.parse_args()
SYNTH = os.path.expanduser("~/synth"); RES = os.path.join(SYNTH, "results")
norm = lambda q: re.sub(r"\s+", " ", str(q)).strip().lower()
DROP_B = {"gsm8k_65", "gsm8k_830", "gsm8k_991", "gsm8k_1239"} if args.mdir == "llama" else set()

def load_arm(tag, drop_ids):
    """Trace list in synth_extract row order + acts, with drop_ids removed from BOTH."""
    traces = []
    for ds in ("aqua", "gsm8k", "aquarat", "logiqa", "truthfulqa"):  # synth_extract order
        p = os.path.join(SYNTH, f"traces_{args.mdir}_{tag}_{ds}.json")
        if os.path.exists(p): traces += json.load(open(p))
    d = np.load(os.path.join(SYNTH, f"acts_{args.mdir}_{tag}.npz"), allow_pickle=True)
    assert len(traces) == d["X"].shape[1], (tag, len(traces), d["X"].shape)
    y = np.asarray(d["y"]).astype(int)
    assert all((t["condition"] == "posthoc") == bool(y[i]) for i, t in enumerate(traces)), f"{tag}: row alignment broken"
    keep = np.array([not (t["id"] in drop_ids and t["condition"] == "posthoc") for t in traces])
    X = d["X"][:, keep, :]
    traces = [t for t, k in zip(traces, keep) if k]
    y = y[keep]
    return traces, X, y

A_tr, A_X, A_y = load_arm("hint", set())        # sycophancy
B_tr, B_X, B_y = load_arm("hintB", DROP_B)      # metadata, cleaned
w = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}.npz"), allow_pickle=True)
y_t = np.asarray(w["y"]).astype(int)
NL = min(A_X.shape[0], B_X.shape[0], w["cot_end"].shape[1] - 1)
tgt = [w["cot_end"][:, l + 1, :].astype(np.float32) for l in range(NL)]

def qidx(traces, cond):
    out = {}
    for i, t in enumerate(traces):
        if t["condition"] == cond: out.setdefault(norm(t["question"]), []).append(i)
    return out

A_p, A_g = qidx(A_tr, "posthoc"), qidx(A_tr, "genuine")
B_p, B_g = qidx(B_tr, "posthoc"), qidx(B_tr, "genuine")
sharedP = sorted(set(A_p) & set(B_p)); sharedG = sorted(set(A_g) & set(B_g))
print(f"{args.mdir}: shared posthoc questions {len(sharedP)}, shared genuine {len(sharedG)} "
      f"(full syc {int(A_y.sum())}/{len(A_y)-int(A_y.sum())}, meta {int(B_y.sum())}/{len(B_y)-int(B_y.sum())})", flush=True)

def pipe(n_tr):
    return make_pipeline(StandardScaler(),
                         PCA(n_components=max(2, min(50, n_tr - 2)), random_state=0),
                         LogisticRegression(max_iter=2000, C=1.0))

def auc(y, s):
    r = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return np.nan
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

def transfer(X, rows, yv):
    """Fit per layer on X[:, rows], score fixed annotated target, return layer-mean AUROC."""
    aucs = []
    for l in range(NL):
        m = pipe(len(rows)).fit(X[l][rows].astype(np.float32), yv)
        aucs.append(auc(y_t, m.predict_proba(tgt[l])[:, 1]))
    return float(np.mean(aucs))

def rows_for(qmap, qs):
    out = []
    for q in qs: out += qmap[q]
    return out

# ---- point estimates on the matched sets ----
def matched_rows(qmap_p, qmap_g):
    rp, rg = rows_for(qmap_p, sharedP), rows_for(qmap_g, sharedG)
    return rp + rg, np.array([1] * len(rp) + [0] * len(rg))

A_rows, A_lab = matched_rows(A_p, A_g)
B_rows, B_lab = matched_rows(B_p, B_g)
point = {"syc_matched": transfer(A_X, A_rows, A_lab),
         "meta_matched": transfer(B_X, B_rows, B_lab),
         "syc_full": transfer(A_X, list(range(len(A_y))), A_y),
         "meta_full": transfer(B_X, list(range(len(B_y))), B_y)}
print("point:", {k: round(v, 4) for k, v in point.items()}, flush=True)

# ---- question-level refit bootstrap for the matched contrast ----
rng = np.random.default_rng(0)
deltas, sy, me = [], [], []
for b in range(args.refits):
    qp = [sharedP[i] for i in rng.integers(0, len(sharedP), len(sharedP))]
    qg = [sharedG[i] for i in rng.integers(0, len(sharedG), len(sharedG))]
    ra = rows_for(A_p, qp) + rows_for(A_g, qg); la = np.array([1]*len(rows_for(A_p, qp)) + [0]*len(rows_for(A_g, qg)))
    rb = rows_for(B_p, qp) + rows_for(B_g, qg); lb = np.array([1]*len(rows_for(B_p, qp)) + [0]*len(rows_for(B_g, qg)))
    if la.sum() in (0, len(la)) or lb.sum() in (0, len(lb)): continue
    a = transfer(A_X, ra, la); m = transfer(B_X, rb, lb)
    sy.append(a); me.append(m); deltas.append(a - m)
    if (b + 1) % 25 == 0: print(f"  refit {b+1}/{args.refits} (running delta mean {np.mean(deltas):+.4f})", flush=True)
deltas, sy, me = map(np.array, (deltas, sy, me))

# ---- size controls: random subsets of the FULL sets at matched class sizes ----
def size_control(X, yv, qmap_p, qmap_g, M):
    vals = []
    allP, allG = sorted(qmap_p), sorted(qmap_g)
    for _ in range(M):
        qp = [allP[i] for i in rng.choice(len(allP), min(len(sharedP), len(allP)), replace=False)]
        qg = [allG[i] for i in rng.choice(len(allG), min(len(sharedG), len(allG)), replace=False)]
        rows = rows_for(qmap_p, qp) + rows_for(qmap_g, qg)
        lab = np.array([1]*len(rows_for(qmap_p, qp)) + [0]*len(rows_for(qmap_g, qg)))
        vals.append(transfer(X, rows, lab))
    return np.array(vals)

sc_a = size_control(A_X, A_y, A_p, A_g, args.sizedraws)
sc_b = size_control(B_X, B_y, B_p, B_g, args.sizedraws)

def summ(v):
    return {"mean": float(np.mean(v)), "sd": float(np.std(v)),
            "q2.5": float(np.percentile(v, 2.5)), "q97.5": float(np.percentile(v, 97.5))}

out = {
  "model": args.mdir, "n_layers": int(NL), "n_target": int(len(y_t)),
  "shared_posthoc_questions": len(sharedP), "shared_genuine_questions": len(sharedG),
  "metadata_cache": "cleaned (4 disclosure ids dropped)" if DROP_B else "as generated",
  "point": point,
  "matched_contrast_syc_minus_meta": {
      "delta": point["syc_matched"] - point["meta_matched"],
      "refit_ci95": [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))],
      "refit_p_one_sided_delta_le_0": float(((deltas <= 0).sum() + 1) / (len(deltas) + 1)),
      "n_refits": int(len(deltas)),
      "syc_refit_ci95": [float(np.percentile(sy, 2.5)), float(np.percentile(sy, 97.5))],
      "meta_refit_ci95": [float(np.percentile(me, 2.5)), float(np.percentile(me, 97.5))],
      "note": "question-level resampling WITH probe refits; measures source-training uncertainty",
  },
  "size_controls": {
      "syc_random_subsets": summ(sc_a), "meta_random_subsets": summ(sc_b),
      "note": "random full-set subsets at the matched class sizes; if syc_matched sits inside "
              "syc_random_subsets, question matching per se did not change the sycophancy probe",
  },
}
os.makedirs(RES, exist_ok=True)
json.dump(out, open(os.path.join(RES, f"matched_question_{args.mdir}.json"), "w"), indent=2)
print(json.dumps(out, indent=2), flush=True)
print(f"MATCHED QUESTION DONE {args.mdir}", flush=True)
