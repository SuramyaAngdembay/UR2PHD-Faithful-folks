"""Item 16: does a construction transfer PREFERENTIALLY to one annotated regime?

The paper reports hint->incorrect 0.616 (p=.017) and hint->correct 0.555 (p=.108), then concludes
the hint construction aligns with the incorrect-answer regime. That is the same untested-comparison
error as the hint-vs-instructed contrast: significant vs non-significant is not a tested difference.

Here each source probe is fit once per layer and scored on BOTH annotated targets, then

    Delta_target = layer-mean AUROC(source -> incorrect regime) - layer-mean AUROC(source -> correct regime)

Unlike the construction contrast, the two targets are DIFFERENT example sets, so this cannot be a
paired bootstrap. Each target is resampled independently and the difference taken per draw, which is
less powerful; a null here is correspondingly weak evidence.

Usage: python target_contrast.py --mdir llama [--boot 2000]
Output: ~/synth/results/target_contrast_<mdir>.json
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
h = np.load(os.path.join(SYNTH, f"acts_{args.mdir}_hint.npz"), allow_pickle=True)
wi = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}.npz"), allow_pickle=True)        # ft1v2
wc = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}_ft34.npz"), allow_pickle=True)   # ft3v4

src = {"instructed": dict(get=lambda l, d=s: d["X"][l].astype(np.float32), y=s["y"], NL=s["X"].shape[0]),
       "hint":       dict(get=lambda l, d=h: d["X"][l].astype(np.float32), y=h["y"], NL=h["X"].shape[0])}
tgt = {"incorrect": dict(get=lambda l, d=wi: d["cot_end"][:, l + 1, :].astype(np.float32),
                         y=np.asarray(wi["y"]).astype(int), NL=wi["cot_end"].shape[1] - 1),
       "correct":   dict(get=lambda l, d=wc: d["cot_end"][:, l + 1, :].astype(np.float32),
                         y=np.asarray(wc["y"]).astype(int), NL=wc["cot_end"].shape[1] - 1)}
NL = min(min(d["NL"] for d in src.values()), min(d["NL"] for d in tgt.values()))
for k, d in tgt.items():
    print(f"target {k}: n={len(d['y'])} pos={int(d['y'].sum())}", flush=True)
print(f"model={args.mdir} shared layers={NL}", flush=True)

# fit each source probe once per layer, score on both targets
P = {sk: {tk: np.zeros((NL, len(tgt[tk]["y"]))) for tk in tgt} for sk in src}
for sk, sd in src.items():
    for l in range(NL):
        m = pipe(len(sd["y"])).fit(sd["get"](l), sd["y"])
        for tk, td in tgt.items():
            P[sk][tk][l] = m.predict_proba(td["get"](l))[:, 1]
    print(f"  fitted {sk}", flush=True)

rng = np.random.default_rng(0)
out = {"model": args.mdir, "n_layers": int(NL), "n_boot": int(args.boot),
       "statistic": "selection-free layer-mean AUROC",
       "targets": {tk: {"n": int(len(td["y"])), "pos": int(td["y"].sum())} for tk, td in tgt.items()},
       "design_note": "targets are different example sets; unpaired bootstrap, lower power than a paired test",
       "sources": {}}

for sk in src:
    point = {tk: float(np.mean([auc(tgt[tk]["y"], P[sk][tk][l]) for l in range(NL)])) for tk in tgt}
    bt = {tk: [] for tk in tgt}; bd = []
    while len(bd) < args.boot:
        draw = {}
        ok = True
        for tk, td in tgt.items():
            n = len(td["y"]); idx = rng.integers(0, n, n); yy = td["y"][idx]
            if yy.sum() == 0 or yy.sum() == len(yy): ok = False; break
            draw[tk] = float(np.mean([auc(yy, P[sk][tk][l][idx]) for l in range(NL)]))
        if not ok: continue
        for tk in tgt: bt[tk].append(draw[tk])
        bd.append(draw["incorrect"] - draw["correct"])
    bd = np.array(bd)
    out["sources"][sk] = {
        "to_incorrect": {"auroc": point["incorrect"],
                         "ci95": [float(np.percentile(bt["incorrect"], 2.5)), float(np.percentile(bt["incorrect"], 97.5))]},
        "to_correct":   {"auroc": point["correct"],
                         "ci95": [float(np.percentile(bt["correct"], 2.5)), float(np.percentile(bt["correct"], 97.5))]},
        "delta_incorrect_minus_correct": {
            "delta": float(point["incorrect"] - point["correct"]),
            "ci95": [float(np.percentile(bd, 2.5)), float(np.percentile(bd, 97.5))],
            "p_one_sided_delta_le_0": float((bd <= 0).mean())},
    }
    d = out["sources"][sk]["delta_incorrect_minus_correct"]
    print(f"  {sk}: ->incorrect {point['incorrect']:.3f}  ->correct {point['correct']:.3f}  "
          f"delta {d['delta']:+.3f} [{d['ci95'][0]:+.3f},{d['ci95'][1]:+.3f}] p={d['p_one_sided_delta_le_0']:.4f}", flush=True)

json.dump(out, open(os.path.join(RES, f"target_contrast_{args.mdir}.json"), "w"), indent=2)
print(f"TARGET CONTRAST DONE {args.mdir}", flush=True)
