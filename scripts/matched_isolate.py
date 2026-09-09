"""Isolate WHICH cohort change explains the matched-question transfer drop (reviewer qualification).

matched_question.py showed: sycophancy transfer 0.616 (full) -> 0.509 (shared questions), while
random size-matched subsets transfer at 0.590 +- 0.038 -- so the drop is not n. But matching
changed BOTH cohorts (positives: 54/185 shared; genuine: 361/428 shared), so the drop is not yet
attributed. This crosses the two factors for the SYCOPHANCY arm:

  A  sharedP + sharedG      (= matched point, recomputed for consistency)
  B  sharedP + randomG-361  (isolates the positive-cohort effect; M draws over randomG)
  C  randomP-54 + sharedG   (isolates the genuine-cohort effect; M draws over randomP)
  D  randomP-54 + randomG-361 (= size control, recomputed)

If B ~ A < C ~ D: the positive cohort drives the drop. If C ~ A < B ~ D: the genuine cohort.
Random draws are from the FULL sycophancy pools. Fixed annotated target throughout.

Usage: python matched_isolate.py --mdir llama [--draws 100]
Output: ~/synth/results/matched_isolate_<mdir>.json
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
ap.add_argument("--draws", type=int, default=100)
args = ap.parse_args()
SYNTH = os.path.expanduser("~/synth"); RES = os.path.join(SYNTH, "results")
norm = lambda q: re.sub(r"\s+", " ", str(q)).strip().lower()
DROP_B = {"gsm8k_65", "gsm8k_830", "gsm8k_991", "gsm8k_1239"} if args.mdir == "llama" else set()

def load_arm(tag, drop_ids):
    traces = []
    for ds in ("aqua", "gsm8k", "aquarat", "logiqa", "truthfulqa"):
        p = os.path.join(SYNTH, f"traces_{args.mdir}_{tag}_{ds}.json")
        if os.path.exists(p): traces += json.load(open(p))
    d = np.load(os.path.join(SYNTH, f"acts_{args.mdir}_{tag}.npz"), allow_pickle=True)
    assert len(traces) == d["X"].shape[1]
    y = np.asarray(d["y"]).astype(int)
    assert all((t["condition"] == "posthoc") == bool(y[i]) for i, t in enumerate(traces))
    keep = np.array([not (t["id"] in drop_ids and t["condition"] == "posthoc") for t in traces])
    return [t for t, k in zip(traces, keep) if k], d["X"][:, keep, :], y[keep]

A_tr, A_X, A_y = load_arm("hint", set())
B_tr, _, _ = load_arm("hintB", DROP_B)
w = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}.npz"), allow_pickle=True)
y_t = np.asarray(w["y"]).astype(int)
NL = min(A_X.shape[0], w["cot_end"].shape[1] - 1)
tgt = [w["cot_end"][:, l + 1, :].astype(np.float32) for l in range(NL)]

def qidx(traces, cond):
    out = {}
    for i, t in enumerate(traces):
        if t["condition"] == cond: out.setdefault(norm(t["question"]), []).append(i)
    return out

A_p, A_g = qidx(A_tr, "posthoc"), qidx(A_tr, "genuine")
B_p, B_g = qidx(B_tr, "posthoc"), qidx(B_tr, "genuine")
sharedP = sorted(set(A_p) & set(B_p)); sharedG = sorted(set(A_g) & set(B_g))
allP, allG = sorted(A_p), sorted(A_g)
nP, nG = len(sharedP), len(sharedG)
print(f"{args.mdir}: sharedP {nP} of {len(allP)}, sharedG {nG} of {len(allG)}", flush=True)

def pipe(n):
    return make_pipeline(StandardScaler(), PCA(n_components=max(2, min(50, n - 2)), random_state=0),
                         LogisticRegression(max_iter=2000, C=1.0))

def auc(y, s):
    r = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return np.nan
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

def transfer(qsP, qsG):
    rp = [i for q in qsP for i in A_p[q]]; rg = [i for q in qsG for i in A_g[q]]
    rows = rp + rg; lab = np.array([1] * len(rp) + [0] * len(rg))
    aucs = []
    for l in range(NL):
        m = pipe(len(rows)).fit(A_X[l][rows].astype(np.float32), lab)
        aucs.append(auc(y_t, m.predict_proba(tgt[l])[:, 1]))
    return float(np.mean(aucs))

rng = np.random.default_rng(0)
def rand(pool, k): return [pool[i] for i in rng.choice(len(pool), k, replace=False)]

out = {"model": args.mdir, "n_sharedP": nP, "n_sharedG": nG,
       "A_sharedP_sharedG": transfer(sharedP, sharedG)}
print("A (sharedP+sharedG):", round(out["A_sharedP_sharedG"], 4), flush=True)
for key, fP, fG in (("B_sharedP_randomG", lambda: sharedP, lambda: rand(allG, nG)),
                    ("C_randomP_sharedG", lambda: rand(allP, nP), lambda: sharedG),
                    ("D_randomP_randomG", lambda: rand(allP, nP), lambda: rand(allG, nG))):
    vals = [transfer(fP(), fG()) for _ in range(args.draws)]
    out[key] = {"mean": float(np.mean(vals)), "sd": float(np.std(vals)),
                "q2.5": float(np.percentile(vals, 2.5)), "q97.5": float(np.percentile(vals, 97.5))}
    print(f"{key}: mean {out[key]['mean']:.4f} sd {out[key]['sd']:.4f}", flush=True)

json.dump(out, open(os.path.join(RES, f"matched_isolate_{args.mdir}.json"), "w"), indent=2)
print(f"MATCHED ISOLATE DONE {args.mdir}", flush=True)
