"""Overlap-excluded sensitivity for the transfer cells (reviewer item: source/target question overlap).

Some hint-source questions recur verbatim in the annotated target (TruthfulQA source ~23/144 Llama
target questions; instructed ~5). Direction of bias is NOT assumed: shared questions could help,
hurt, or do nothing depending on what the probe learned. This script measures it.

Steps:
 1. Reconstruct the wbrep_<m>.npz row->question alignment by replaying wb_extract.py's collection
    loop (same glob, same ft filter, same skip rule). Alignment is VERIFIED by requiring the
    reconstructed y and domain sequences to match the npz arrays elementwise; abort on mismatch
    (glob order is directory order, not guaranteed stable -- so this check is mandatory).
 2. For each source (instructed / hint / hintL / hintT), collect its normalized question set from
    the trace JSONs actually used to build its acts file.
 3. Fit the source probe per layer (identical pipeline to contrast_test.py), score the full target,
    and report layer-mean AUROC on (a) all target rows, (b) target rows whose question does not
    occur in the source, with a bootstrap CI on (b).

Usage: python overlap_sensitivity.py --mdir llama [--boot 2000]
Output: ~/synth/results/overlap_sens_<mdir>.json
"""
import argparse, glob, json, os, re
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
BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
MDLDIR = {"llama": "llama-3.1-8b-instruct", "qwen": "Qwen2.5-7B-Instruct"}[args.mdir]
DOMAINS = ["truthfulqa", "logiqa", "aqua", "HLE_BIO"]  # EXACT wb_extract.py order

norm = lambda q: re.sub(r"\s+", " ", str(q)).strip().lower()

# ---- 1. reconstruct target questions; verify alignment against npz ----
recs = []
for dom in DOMAINS:
    for f in glob.glob(os.path.join(BASE, dom, MDLDIR, "response_*.json")):
        d = json.load(open(f)); ft = d.get("faithful_type")
        if ft not in (1, 2): continue
        s = d["sample_0"]
        steps = [s[k] for k in sorted([k for k in s if k.startswith("step_")], key=lambda x: int(x.split("_")[1]))]
        if not steps: continue
        recs.append(dict(dom=dom, q=norm(d.get("question", "")), y=1 if ft == 2 else 0))
w = np.load(os.path.expanduser(f"~/wbrep_{args.mdir}.npz"), allow_pickle=True)
y_t = np.asarray(w["y"]).astype(int)
dom_t = np.asarray(w["domain"]).astype(str)
assert len(recs) == len(y_t), f"row count mismatch: rebuilt {len(recs)} vs npz {len(y_t)}"
assert all(r["y"] == int(y_t[i]) for i, r in enumerate(recs)), "y sequence mismatch -- glob order changed; DO NOT TRUST"
assert all(r["dom"] == dom_t[i] for i, r in enumerate(recs)), "domain sequence mismatch -- glob order changed; DO NOT TRUST"
q_t = [r["q"] for r in recs]
print(f"target alignment verified: n={len(q_t)} (y and domain sequences match npz elementwise)", flush=True)

# ---- 2. source question sets ----
def qs_from(files):
    out = set()
    for p in files:
        fp = os.path.join(SYNTH, p)
        if os.path.exists(fp):
            for t in json.load(open(fp)): out.add(norm(t["question"]))
    return out

SRcfg = {
    "instructed": dict(acts=f"acts_{args.mdir}.npz",
                       files=[f"traces_{args.mdir}_aqua.json", f"traces_{args.mdir}_gsm8k.json"]),
    "hint":       dict(acts=f"acts_{args.mdir}_hint.npz",
                       files=[f"traces_{args.mdir}_hint_aquarat.json", f"traces_{args.mdir}_hint_gsm8k.json"]),
    "hintL":      dict(acts=f"acts_{args.mdir}_hintL.npz", files=[f"traces_{args.mdir}_hintL_logiqa.json"]),
    "hintT":      dict(acts=f"acts_{args.mdir}_hintT.npz", files=[f"traces_{args.mdir}_hintT_truthfulqa.json"]),
}

def pipe(n_tr):
    return make_pipeline(StandardScaler(),
                         PCA(n_components=max(2, min(50, n_tr - 2)), random_state=0),
                         LogisticRegression(max_iter=2000, C=1.0))

def auc(y, s):
    r = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return np.nan
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

tgt_get = lambda l: w["cot_end"][:, l + 1, :].astype(np.float32)
out = {"model": args.mdir, "n_target": int(len(y_t)), "sources": {}}
rng = np.random.default_rng(0)
for sk, cfg in SRcfg.items():
    a = np.load(os.path.join(SYNTH, cfg["acts"]), allow_pickle=True)
    ys = np.asarray(a["y"]).astype(int); NL = min(a["X"].shape[0], w["cot_end"].shape[1] - 1)
    sqs = qs_from(cfg["files"])
    keep = np.array([q not in sqs for q in q_t])
    n_ov = int((~keep).sum())
    P = np.zeros((NL, len(y_t)))
    for l in range(NL):
        P[l] = pipe(len(ys)).fit(a["X"][l].astype(np.float32), ys).predict_proba(tgt_get(l))[:, 1]
    full = float(np.mean([auc(y_t, P[l]) for l in range(NL)]))
    rec = {"n_source_questions": len(sqs), "n_target_overlap": n_ov, "layer_mean_full": full}
    if n_ov and keep.sum() and y_t[keep].sum() not in (0, keep.sum()):
        sub = float(np.mean([auc(y_t[keep], P[l][keep]) for l in range(NL)]))
        bs = []
        idx_all = np.where(keep)[0]
        while len(bs) < args.boot:
            idx = rng.choice(idx_all, len(idx_all), replace=True)
            yy = y_t[idx]
            if yy.sum() in (0, len(yy)): continue
            bs.append(float(np.mean([auc(yy, P[l][idx]) for l in range(NL)])))
        rec.update({"layer_mean_excl_overlap": sub, "n_excl": int(keep.sum()),
                    "excl_ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                    "shift": sub - full})
    else:
        rec["layer_mean_excl_overlap"] = None if n_ov else full
        rec["note"] = "no overlap" if not n_ov else "excluded subset degenerate"
    out["sources"][sk] = rec
    print(f"  {sk}: overlap {n_ov}/{len(y_t)} | full {full:.4f} | excl {rec.get('layer_mean_excl_overlap')}", flush=True)

os.makedirs(RES, exist_ok=True)
json.dump(out, open(os.path.join(RES, f"overlap_sens_{args.mdir}.json"), "w"), indent=2)
print(f"OVERLAP SENS DONE {args.mdir}", flush=True)
