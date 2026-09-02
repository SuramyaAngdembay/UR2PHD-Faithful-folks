"""Tier-1 statistical hardening of the construction-transfer contrast.

The paper's central claim is a COMPARISON: probes trained on the instructed construction do not
transfer onto the annotated regime, while probes trained on the hint-induced construction do.
Currently that is reported as two separate tests (hint p=.017; instructed n.s.), which never tests
whether the two differ. This script tests the difference directly.

Both probes are evaluated on the SAME annotated target examples, so the target set can be
bootstrapped as a paired unit:
  (1) CONTRAST   Delta = layer-mean AUROC(hint->annotated) - layer-mean AUROC(instructed->annotated)
                 with a percentile CI and a one-sided bootstrap p for Delta <= 0.
  (2) EQUIVALENCE  one-sided bound on the instructed transfer: can we reject that it reaches a
                 small-effect margin (default 0.55)? Turns "failed to reject" into a bounded claim.
  (3) POWER      the same interval for each cell, so nulls (notably Qwen) are reported with the
                 effect size they could actually have detected.

Primary statistic is the selection-free layer mean, matching the paper. Caveat recorded in the
output: the interval reflects target-set uncertainty, not variability in the training sets.

Usage: python contrast_test.py --mdir llama [--boot 2000] [--margin 0.55]
Output: ~/synth/results/contrast_<mdir>.json
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
ap.add_argument("--margin", type=float, default=0.55)
ap.add_argument("--hint", default="hint", help="hint activation suffix: hint (math) or hintL (LogiQA)")
args = ap.parse_args()
SYNTH = os.path.expanduser("~/synth"); RES = os.path.join(SYNTH, "results")

def pipe(n_tr):
    return make_pipeline(StandardScaler(),
                         PCA(n_components=max(2, min(50, n_tr - 2)), random_state=0),
                         LogisticRegression(max_iter=2000, C=1.0))

def auc(y, s):
    """Mann-Whitney AUROC with tie-averaged ranks."""
    r = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return np.nan
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

# ---- identical loading convention to bridge3.py ----
s = np.load(os.path.join(SYNTH, f"acts_{args.mdir}.npz"), allow_pickle=True)
h = np.load(os.path.join(SYNTH, f"acts_{args.mdir}_{args.hint}.npz"), allow_pickle=True)
w = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}.npz"), allow_pickle=True)
src = {"instructed": dict(get=lambda l, d=s: d["X"][l].astype(np.float32), y=s["y"], NL=s["X"].shape[0]),
       "hint":       dict(get=lambda l, d=h: d["X"][l].astype(np.float32), y=h["y"], NL=h["X"].shape[0])}
tgt_get = lambda l: w["cot_end"][:, l + 1, :].astype(np.float32)
y_t = np.asarray(w["y"]).astype(int)
NL = min(min(d["NL"] for d in src.values()), w["cot_end"].shape[1] - 1)
print(f"model={args.mdir} hint={args.hint} layers={NL} target n={len(y_t)} pos={int(y_t.sum())}", flush=True)

# ---- per-layer, per-example predictions on the shared target ----
P = {k: np.zeros((NL, len(y_t))) for k in src}
for k, d in src.items():
    for l in range(NL):
        P[k][l] = pipe(len(d["y"])).fit(d["get"](l), d["y"]).predict_proba(tgt_get(l))[:, 1]
    print(f"  {k}: layer-mean AUROC {np.mean([auc(y_t, P[k][l]) for l in range(NL)]):.4f}", flush=True)

per_layer = {k: [float(auc(y_t, P[k][l])) for l in range(NL)] for k in src}
point = {k: float(np.mean(per_layer[k])) for k in src}
n_exceed = int(sum(1 for l in range(NL) if per_layer["hint"][l] > per_layer["instructed"][l]))
delta_point = point["hint"] - point["instructed"]

# ---- paired bootstrap over target examples ----
rng = np.random.default_rng(0)
bs = {k: [] for k in src}; bd = []
n = len(y_t)
while len(bd) < args.boot:
    idx = rng.integers(0, n, n)
    yy = y_t[idx]
    if yy.sum() == 0 or yy.sum() == len(yy): continue
    m = {k: float(np.mean([auc(yy, P[k][l][idx]) for l in range(NL)])) for k in src}
    for k in src: bs[k].append(m[k])
    bd.append(m["hint"] - m["instructed"])
bd = np.array(bd); bs = {k: np.array(v) for k, v in bs.items()}

out = {
  "model": args.mdir, "hint_source": args.hint, "n_target": int(n), "n_target_pos": int(y_t.sum()),
  "n_layers": int(NL), "n_boot": int(args.boot), "statistic": "selection-free layer-mean AUROC",
  "transfer": {k: {"auroc": point[k],
                   "ci95": [float(np.percentile(bs[k], 2.5)), float(np.percentile(bs[k], 97.5))]}
               for k in src},
  "contrast_hint_minus_instructed": {
      "delta": float(delta_point),
      "ci95": [float(np.percentile(bd, 2.5)), float(np.percentile(bd, 97.5))],
      "p_one_sided_delta_le_0": float((bd <= 0).mean()),
  },
  "equivalence_instructed": {
      "margin": args.margin,
      "ci95_upper": float(np.percentile(bs["instructed"], 97.5)),
      "rejects_reaching_margin": bool(np.percentile(bs["instructed"], 97.5) < args.margin),
      "note": "if true, instructed transfer is bounded below the margin rather than merely unproven",
  },
  "per_layer_auroc": per_layer,
  "layers_hint_exceeds_instructed": {"count": n_exceed, "of": int(NL),
      "note": "descriptive only; layers are highly correlated so this is not a valid significance test"},
  "caveat": "interval reflects target-set resampling only; training sets held fixed",
}
os.makedirs(RES, exist_ok=True)
json.dump(out, open(os.path.join(RES, f"contrast_{args.mdir}_{args.hint}.json"), "w"), indent=2)
print(json.dumps(out, indent=2), flush=True)
print(f"CONTRAST DONE {args.mdir}", flush=True)
