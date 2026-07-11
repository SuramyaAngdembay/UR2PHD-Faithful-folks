"""
Three-way representational bridge: FaithCoT (human-annotated organic) <-> HINT-induced
(organic, causal labels) <-> SYNTHETIC (instructed answer-first). Per model, all six directed
transfers, swept over ALL layers (best + mean reported), plus each distribution's own
per-layer CV curve (depth comparison).

The decisive question: does HINT <-> FaithCoT transfer where SYNTHETIC <-> FaithCoT failed?
  If yes: instructed rationalization is the artifact; spontaneous rationalization shares the
          real representation -> C4 sharpens, and the hint set externally validates the frontier.
  If no:  even organic-but-elicited rationalization differs from annotated organic -> the
          regime is representationally fragmented; report as such.

Layer convention: acts_*.npz X is [NL, n, dim] with block-layer l = hidden_states[l+1];
wbrep_*.npz cot_end is [n, NL+1, dim] with index L = hidden_states[L]. Shared layer l uses
X[l] and cot_end[:, l+1, :].
Usage: python bridge3.py --mdir llama   -> results/bridge3_<mdir>.json
"""
import argparse, json, os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline

ap = argparse.ArgumentParser()
ap.add_argument("--mdir", required=True)
args = ap.parse_args()
SYNTH = os.path.expanduser("~/synth"); RES = os.path.join(SYNTH, "results")

def pipe(n_tr): return make_pipeline(StandardScaler(),
                                     PCA(n_components=max(2, min(50, n_tr - 2)), random_state=0),
                                     LogisticRegression(max_iter=2000, C=1.0))

def cv(Xl, yy):
    skf = StratifiedKFold(5, shuffle=True, random_state=0); oof = np.zeros(len(yy))
    for tr, te in skf.split(Xl, yy):
        oof[te] = pipe(len(tr)).fit(Xl[tr], yy[tr]).predict_proba(Xl[te])[:, 1]
    return roc_auc_score(yy, oof)

# ---- load the three distributions as layer-indexed accessors ----
dists = {}
s = np.load(os.path.join(SYNTH, f"acts_{args.mdir}.npz"), allow_pickle=True)
dists["synthetic"] = dict(get=lambda l, d=s: d["X"][l].astype(np.float32), y=s["y"], NL=s["X"].shape[0])
h = np.load(os.path.join(SYNTH, f"acts_{args.mdir}_hint.npz"), allow_pickle=True)
dists["hint"] = dict(get=lambda l, d=h: d["X"][l].astype(np.float32), y=h["y"], NL=h["X"].shape[0])
w = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}.npz"), allow_pickle=True)
dists["faithcot"] = dict(get=lambda l, d=w: d["cot_end"][:, l + 1, :].astype(np.float32),
                         y=w["y"], NL=w["cot_end"].shape[1] - 1)
NL = min(d["NL"] for d in dists.values())
for name, d in dists.items():
    print(f"{name}: n={len(d['y'])} posthoc={int(d['y'].sum())}", flush=True)

# ---- own-distribution per-layer CV (depth signatures) ----
curves = {}
for name, d in dists.items():
    curves[name] = [cv(d["get"](l), d["y"]) for l in range(NL)]
    b = int(np.argmax(curves[name]))
    print(f"[{name}] own-best block-layer {b} CV {curves[name][b]:.3f}", flush=True)

# ---- all six directed transfers, swept over layers ----
transfers = {}
names = list(dists)
for a in names:
    for b in names:
        if a == b: continue
        da, db = dists[a], dists[b]
        aucs = []
        for l in range(NL):
            m = pipe(len(da["y"])).fit(da["get"](l), da["y"])
            aucs.append(roc_auc_score(db["y"], m.predict_proba(db["get"](l))[:, 1]))
        aucs = np.array(aucs); bl = int(np.argmax(aucs))
        transfers[f"{a}->{b}"] = {"best": float(aucs[bl]), "best_layer": bl, "mean": float(aucs.mean())}
        print(f"[{a} -> {b}] best {aucs[bl]:.3f} @L{bl} | mean {aucs.mean():.3f}", flush=True)

out = {"model": args.mdir, "n_layers_shared": NL,
       "n": {k: int(len(d["y"])) for k, d in dists.items()},
       "n_posthoc": {k: int(d["y"].sum()) for k, d in dists.items()},
       "own_best": {k: {"layer": int(np.argmax(c)), "cv": float(max(c))} for k, c in curves.items()},
       "curves": {k: [float(x) for x in c] for k, c in curves.items()},
       "transfers": transfers}
json.dump(out, open(os.path.join(RES, f"bridge3_{args.mdir}.json"), "w"), indent=2)
print(f"BRIDGE3 DONE {args.mdir}", flush=True)
