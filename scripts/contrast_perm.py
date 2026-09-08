"""Null-calibrated paired permutation test for the construction contrast.

The bootstrap tail fraction reported by contrast_test.py is confidence-interval inversion, not a
calibrated Monte Carlo test under a null (Phipson & Smyth 2010 applies to the finite-simulation
correction; the deeper issue is that a bootstrap distribution is not a null distribution). This
script supplies the calibrated companion:

  H0: the two source probes (hint-trained, instructed-trained) are EXCHANGEABLE with respect to
      the annotated target -- i.e., which probe produced which score column carries no information.

Procedure. Fit both probes per layer exactly as contrast_test.py does; score the shared target.
Rank-transform each probe's scores per layer (so exchangeability concerns ordering information,
not the two probes' different calibration scales). Observed statistic:
  Delta = layer-mean AUROC(hint) - layer-mean AUROC(instructed).
Null draws: for each target example independently, swap the two probes' full layer-column with
probability 1/2 (the full column, preserving within-probe layer correlation). One-sided p with
the add-one convention: (1 + #{Delta_perm >= Delta_obs}) / (nperm + 1).

Scope caveat (recorded in output): like the bootstrap, this conditions on the fitted source
probes; it does not model source-generation or source-training variability.

Usage: python contrast_perm.py --mdir llama --hint hint [--nperm 10000]
Output: ~/synth/results/cperm_<mdir>_<hint>.json
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
ap.add_argument("--hint", default="hint")
ap.add_argument("--nperm", type=int, default=10000)
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

s = np.load(os.path.join(SYNTH, f"acts_{args.mdir}.npz"), allow_pickle=True)
h = np.load(os.path.join(SYNTH, f"acts_{args.mdir}_{args.hint}.npz"), allow_pickle=True)
w = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}.npz"), allow_pickle=True)
src = {"instructed": dict(get=lambda l, d=s: d["X"][l].astype(np.float32), y=np.asarray(s["y"]).astype(int), NL=s["X"].shape[0]),
       "hint":       dict(get=lambda l, d=h: d["X"][l].astype(np.float32), y=np.asarray(h["y"]).astype(int), NL=h["X"].shape[0])}
tgt_get = lambda l: w["cot_end"][:, l + 1, :].astype(np.float32)
y_t = np.asarray(w["y"]).astype(int)
NL = min(min(d["NL"] for d in src.values()), w["cot_end"].shape[1] - 1)
n = len(y_t)
print(f"model={args.mdir} hint={args.hint} layers={NL} target n={n}", flush=True)

P = {}
for k, d in src.items():
    M = np.zeros((NL, n))
    for l in range(NL):
        M[l] = pipe(len(d["y"])).fit(d["get"](l), d["y"]).predict_proba(tgt_get(l))[:, 1]
        M[l] = rankdata(M[l]) / n  # rank-transform per layer: shared marginal scale
    P[k] = M
    print(f"  {k}: layer-mean AUROC {np.mean([auc(y_t, M[l]) for l in range(NL)]):.4f}", flush=True)

def delta(Ph, Pi):
    return float(np.mean([auc(y_t, Ph[l]) for l in range(NL)]) -
                 np.mean([auc(y_t, Pi[l]) for l in range(NL)]))

obs = delta(P["hint"], P["instructed"])
rng = np.random.default_rng(0)
ge = 0
for b in range(args.nperm):
    swap = rng.random(n) < 0.5          # per-example column swap
    Ph = np.where(swap[None, :], P["instructed"], P["hint"])
    Pi = np.where(swap[None, :], P["hint"], P["instructed"])
    if delta(Ph, Pi) >= obs: ge += 1
    if (b + 1) % 2000 == 0: print(f"  perm {b+1}/{args.nperm} (ge={ge})", flush=True)

p = (ge + 1) / (args.nperm + 1)
out = {"model": args.mdir, "hint_source": args.hint, "n_target": int(n), "n_layers": int(NL),
       "statistic": "layer-mean AUROC difference, per-layer rank-transformed scores",
       "null": "per-example exchangeability of the two probes' score columns",
       "nperm": int(args.nperm), "observed_delta": obs,
       "n_perm_ge_obs": int(ge), "p_one_sided_add_one": float(p),
       "caveat": "conditions on fitted source probes; source-training variability not modeled"}
os.makedirs(RES, exist_ok=True)
json.dump(out, open(os.path.join(RES, f"cperm_{args.mdir}_{args.hint}.json"), "w"), indent=2)
print(json.dumps(out, indent=2), flush=True)
print(f"CPERM DONE {args.mdir} {args.hint}", flush=True)
