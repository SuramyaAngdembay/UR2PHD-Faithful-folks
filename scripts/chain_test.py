"""Non-transitive transfer chain: does the instructed probe reach the ADJACENT construction?

Motivation (reviewer objection): "instructed probes transfer to neither annotated regime --
maybe the instructed probe is just bad." Rebuttal requires a positive control ON THE SAME
PROBE: show instructed->hint transfers (the probe carries portable signal) while
instructed->annotated does not (the signal is specifically not the annotated phenomenon).

Design mirrors contrast_test.py exactly (same pipeline, same selection-free layer-mean, same
paired bootstrap) but the SHARED TARGET is the hint testbed rather than the annotated set:
  arm A: instructed -> hint   (the positive-control leg)
  arm B: annotated  -> hint   (reverse anchor, descriptive)
plus the paired contrast (instructed->hint) - (instructed->annotated) is NOT computable as a
paired unit (different targets), so we report the two intervals side by side and the
within-target contrast A - B.

Class imbalance note: the hint target is imbalanced (Llama 185/613); AUROC is rank-based so
the point estimate is fine, and the bootstrap resamples the target as-is.

Usage: python chain_test.py --mdir llama [--hint hint] [--boot 2000]
Output: ~/synth/results/chain_<mdir>_<hint>.json
"""
import argparse, json, os
import numpy as np
from scipy.stats import rankdata
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

ap = argparse.ArgumentParser()
ap.add_argument("--mdir", required=True)
ap.add_argument("--boot", type=int, default=2000)
ap.add_argument("--hint", default="hint", help="hint activation suffix used as the TARGET")
args = ap.parse_args()
SYNTH = os.path.expanduser("~/synth"); RES = os.path.join(SYNTH, "results")

def pipe(n_tr):
    return make_pipeline(StandardScaler(),
                         PCA(n_components=max(2, min(50, n_tr - 2)), random_state=0),
                         LogisticRegression(max_iter=2000, C=1.0))

def auc(y, s):
    r = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return np.nan
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

# ---- loading convention identical to contrast_test.py / bridge3.py ----
s = np.load(os.path.join(SYNTH, f"acts_{args.mdir}.npz"), allow_pickle=True)          # instructed
h = np.load(os.path.join(SYNTH, f"acts_{args.mdir}_{args.hint}.npz"), allow_pickle=True)  # hint = TARGET
w = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}.npz"), allow_pickle=True)        # annotated ft1v2

src = {"instructed": dict(get=lambda l, d=s: d["X"][l].astype(np.float32), y=np.asarray(s["y"]).astype(int), NL=s["X"].shape[0]),
       "annotated":  dict(get=lambda l, d=w: d["cot_end"][:, l + 1, :].astype(np.float32), y=np.asarray(w["y"]).astype(int), NL=w["cot_end"].shape[1] - 1)}
tgt_get = lambda l: h["X"][l].astype(np.float32)
y_t = np.asarray(h["y"]).astype(int)
NL = min(min(d["NL"] for d in src.values()), h["X"].shape[0])
print(f"model={args.mdir} target=hint({args.hint}) layers={NL} target n={len(y_t)} pos={int(y_t.sum())}", flush=True)

P = {k: np.zeros((NL, len(y_t))) for k in src}
for k, d in src.items():
    for l in range(NL):
        P[k][l] = pipe(len(d["y"])).fit(d["get"](l), d["y"]).predict_proba(tgt_get(l))[:, 1]
    print(f"  {k}->hint: layer-mean AUROC {np.mean([auc(y_t, P[k][l]) for l in range(NL)]):.4f}", flush=True)

per_layer = {k: [float(auc(y_t, P[k][l])) for l in range(NL)] for k in src}
point = {k: float(np.mean(per_layer[k])) for k in src}

rng = np.random.default_rng(0)
bs = {k: [] for k in src}; bd = []
n = len(y_t)
while len(bd) < args.boot:
    idx = rng.integers(0, n, n)
    yy = y_t[idx]
    if yy.sum() == 0 or yy.sum() == len(yy): continue
    m = {k: float(np.mean([auc(yy, P[k][l][idx]) for l in range(NL)])) for k in src}
    for k in src: bs[k].append(m[k])
    bd.append(m["instructed"] - m["annotated"])
bd = np.array(bd); bs = {k: np.array(v) for k, v in bs.items()}

out = {
  "model": args.mdir, "target": f"hint({args.hint})", "n_target": int(n), "n_target_pos": int(y_t.sum()),
  "n_layers": int(NL), "n_boot": int(args.boot), "statistic": "selection-free layer-mean AUROC",
  "transfer_onto_hint": {k: {"auroc": point[k],
                             "ci95": [float(np.percentile(bs[k], 2.5)), float(np.percentile(bs[k], 97.5))]}
                         for k in src},
  "contrast_instructed_minus_annotated": {
      "delta": float(point["instructed"] - point["annotated"]),
      "ci95": [float(np.percentile(bd, 2.5)), float(np.percentile(bd, 97.5))],
      "note": "descriptive; both arms share the target so the paired bootstrap is valid",
  },
  "positive_control": {
      "claim": "instructed->hint CI excludes 0.5 == the instructed probe carries portable signal",
      "ci_low": float(np.percentile(bs["instructed"], 2.5)),
      "passes": bool(np.percentile(bs["instructed"], 2.5) > 0.5),
  },
  "per_layer_auroc": per_layer,
  "caveat": "interval reflects target-set resampling only; training sets held fixed",
}
os.makedirs(RES, exist_ok=True)
json.dump(out, open(os.path.join(RES, f"chain_{args.mdir}_{args.hint}.json"), "w"), indent=2)
print(json.dumps({k: v for k, v in out.items() if k != "per_layer_auroc"}, indent=2), flush=True)
print(f"CHAIN DONE {args.mdir}", flush=True)
