"""Domain-matched bridge: LogiQA hint-construction -> annotated ft1v2 (which includes LogiQA
traces). Full layer sweep, selection-free layer-mean + best, 1000 coupled perms (project-once).
Also splits the ft1v2 target by domain: logiqa-only vs other-domains (the domain-matched vs
domain-transfer contrast). Usage: python hintL_bridge.py --mdir llama [--nperm 1000]"""
import argparse, json, os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ap = argparse.ArgumentParser()
ap.add_argument("--mdir", required=True)
ap.add_argument("--nperm", type=int, default=1000)
a = ap.parse_args()
S = os.path.expanduser("~/synth")

d = np.load(os.path.join(S, f"acts_{a.mdir}_hintL.npz"), allow_pickle=True)
Xs, ys = d["X"], d["y"].astype(int)
w = np.load(os.path.expanduser(f"~/wbrep_{a.mdir}.npz"), allow_pickle=True)
fe, fy = w["cot_end"], w["y"].astype(int)
fdom = w["domain"] if "domain" in w else None
NL = min(Xs.shape[0], fe.shape[1] - 1)

targets = {"ft12_all": np.arange(len(fy))}
if fdom is not None:
    lg = np.array([str(x).lower().startswith("logiqa") for x in fdom])
    if lg.sum() >= 20 and len(set(fy[lg])) == 2:
        targets["ft12_logiqa"] = np.where(lg)[0]
    if (~lg).sum() >= 20 and len(set(fy[~lg])) == 2:
        targets["ft12_other"] = np.where(~lg)[0]

# project-once per layer: fit scaler+PCA on hintL source, transform both
PR = []
for l in range(NL):
    sc = StandardScaler().fit(Xs[l].astype(np.float32))
    pc = PCA(max(2, min(50, Xs.shape[1] - 2)), random_state=0).fit(sc.transform(Xs[l].astype(np.float32)))
    PR.append((pc.transform(sc.transform(Xs[l].astype(np.float32))),
               pc.transform(sc.transform(fe[:, l + 1, :].astype(np.float32)))))

out = {"model": a.mdir, "nperm": a.nperm, "n_src": int(len(ys)), "src_pos": int(ys.sum())}
rng = np.random.default_rng(0)
for tname, tidx in targets.items():
    yt = fy[tidx]
    def sweep(yy):
        return np.array([roc_auc_score(yt, LogisticRegression(max_iter=2000, C=1.0)
                        .fit(PR[l][0], yy).predict_proba(PR[l][1][tidx])[:, 1]) for l in range(NL)])
    obs = sweep(ys)
    nm, nb = [], []
    for _ in range(a.nperm):
        p = sweep(rng.permutation(ys)); nm.append(p.mean()); nb.append(p.max())
    pm = (1 + sum(m >= obs.mean() for m in nm)) / (1 + a.nperm)
    pb = (1 + sum(m >= obs.max() for m in nb)) / (1 + a.nperm)
    out[tname] = {"n_target": int(len(yt)), "pos": int(yt.sum()),
                  "mean": float(obs.mean()), "p_mean": pm,
                  "best": float(obs.max()), "best_layer": int(obs.argmax()), "p_best": pb}
    print(f"[hintL->{tname}] {a.mdir}: mean {obs.mean():.3f} p={pm:.3f} | "
          f"best {obs.max():.3f} @L{int(obs.argmax())} p={pb:.3f} (n_t={len(yt)})", flush=True)
json.dump(out, open(os.path.join(S, "results", f"hintL_bridge_{a.mdir}.json"), "w"), indent=1)
print(f"HINTL_BRIDGE DONE {a.mdir}", flush=True)
