"""
SAE what-transfers study (Phase 2, Llama-3.1-8B) -- decompose the probe directions and ask
WHICH sparse features carry (a) the hint->annotated-incorrect-regime transfer and (b) why the
instructed construction does not transfer.

Sets (last-CoT-token residuals, already extracted):
  instructed  ~/synth/acts_llama.npz        X[L, n, 4096]  (peak L9)
  hint        ~/synth/acts_llama_hint.npz   X[L, n, 4096]  (peak L17)
  ft1v2       ~/wbrep_llama.npz             cot_end[n, 33, 4096], layer l_synth == l_wbrep-1  (peak L29)

SAEs: Llama Scope residual, 8x (32768 feats), via sae_lens; layers 9/17/25/29.
CAVEAT (log + report): Llama Scope SAEs are trained on the BASE model over pretraining data;
our activations come from the 4-bit-quantized INSTRUCT model -> reconstruction quality is
reported per layer (frac. variance explained) and all findings are conditional on it.

Analyses per layer:
  1 per-set feature separation: Cohen's d per SAE feature, top-K per set
  2 top-K overlap between sets (Jaccard) -- do hint and ft1v2 share features that instructed lacks?
  3 residual probe direction -> decoder decomposition: cos(w, W_dec[f]); top-K aligned features
  4 SAE-space transfer: LR on set A features -> AUROC on set B (hint->ft12 vs instructed->ft12)
Output: ~/synth/results/sae_transfers_llama.json  (feature ids saved for Neuronpedia lookup)
Run (CPU ok):  python sae_transfers.py [--layers 9 17 25 29] [--topk 32]
"""
import argparse, json, os, traceback
import numpy as np
import torch

ap = argparse.ArgumentParser()
ap.add_argument("--layers", type=int, nargs="+", default=[9, 17, 25, 29])
ap.add_argument("--topk", type=int, default=32)
ap.add_argument("--device", default="cpu")
args = ap.parse_args()

SYNTH = os.path.expanduser("~/synth")
OUT = os.path.join(SYNTH, "results", "sae_transfers_llama.json")

def load_sets():
    sets = {}
    d = np.load(os.path.join(SYNTH, "acts_llama.npz"), allow_pickle=True)
    sets["instructed"] = (d["X"], d["y"].astype(int))            # X[L, n, dim]
    d = np.load(os.path.join(SYNTH, "acts_llama_hint.npz"), allow_pickle=True)
    sets["hint"] = (d["X"], d["y"].astype(int))
    w = np.load(os.path.expanduser("~/wbrep_llama.npz"), allow_pickle=True)
    ce = np.transpose(w["cot_end"], (1, 0, 2))[1:]               # drop embedding layer -> [32, n, dim]
    sets["ft1v2"] = (ce, w["y"].astype(int))
    for k, (X, y) in sets.items():
        print(f"[sets] {k}: X{X.shape} pos={int(y.sum())}/{len(y)}", flush=True)
    return sets

def load_sae(layer):
    from sae_lens import SAE
    last = None
    for rel, sid in [("llama_scope_lxr_8x", f"l{layer}r_8x"),
                     ("llama_scope_lxr_32x", f"l{layer}r_32x")]:
        try:
            try:
                sae = SAE.from_pretrained(rel, sid, device=args.device)
            except ValueError:
                sae, _, _ = SAE.from_pretrained(rel, sid, device=args.device)
            print(f"[sae] L{layer}: loaded {rel}/{sid}", flush=True)
            return sae
        except Exception as e:
            last = e
            print(f"[sae] L{layer}: {rel}/{sid} failed: {type(e).__name__}: {e}", flush=True)
    raise last

@torch.no_grad()
def encode(sae, X):
    xb = torch.tensor(np.asarray(X, dtype=np.float32), device=args.device)
    F = sae.encode(xb)
    rec = sae.decode(F)
    fvu = ((xb - rec).var() / xb.var()).item()                   # frac. variance UNexplained
    return F.cpu().numpy(), 1.0 - fvu

def cohens_d(F, y):
    a, b = F[y == 1], F[y == 0]
    sd = np.sqrt((a.var(0) + b.var(0)) / 2) + 1e-9
    return (a.mean(0) - b.mean(0)) / sd

def lr_fit(F, y):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    sc = StandardScaler().fit(F)
    m = LogisticRegression(max_iter=2000, C=1.0).fit(sc.transform(F), y)
    return sc, m

def auroc(y, s):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, s))

sets = load_sets()
res = {"topk": args.topk, "layers": {}, "caveat": "Llama Scope SAEs trained on BASE model; acts from 4-bit INSTRUCT"}
for L in args.layers:
    try:
        sae = load_sae(L)
        W_dec = sae.W_dec.detach().cpu().numpy()                 # [n_feat, dim]
        lay = {"recon_var_explained": {}, "top_features": {}, "overlap_jaccard": {},
               "probe_decomposition": {}, "sae_space_transfer": {}}
        feats, ys = {}, {}
        for name, (X, y) in sets.items():
            F, ve = encode(sae, X[L])
            feats[name], ys[name] = F, y
            lay["recon_var_explained"][name] = round(ve, 4)
            d = cohens_d(F, y)
            top = np.argsort(-np.abs(d))[: args.topk]
            lay["top_features"][name] = [{"feat": int(f), "d": round(float(d[f]), 3)} for f in top]
        # 2 overlap
        tops = {n: {t["feat"] for t in lay["top_features"][n]} for n in feats}
        for a, b in [("hint", "ft1v2"), ("instructed", "ft1v2"), ("instructed", "hint")]:
            inter = tops[a] & tops[b]
            lay["overlap_jaccard"][f"{a}&{b}"] = {
                "jaccard": round(len(inter) / len(tops[a] | tops[b]), 3),
                "shared_feats": sorted(int(f) for f in inter)}
        # 3 residual-direction decomposition (LR in residual space, no PCA, standardized)
        for name, (X, y) in sets.items():
            sc, m = lr_fit(X[L].astype(np.float32), y)
            w = (m.coef_[0] / (sc.scale_ + 1e-9))
            w = w / np.linalg.norm(w)
            cos = W_dec @ w / (np.linalg.norm(W_dec, axis=1) + 1e-9)
            top = np.argsort(-np.abs(cos))[: args.topk]
            lay["probe_decomposition"][name] = [{"feat": int(f), "cos": round(float(cos[f]), 3)} for f in top]
        pd_tops = {n: {t["feat"] for t in lay["probe_decomposition"][n]} for n in feats}
        for a, b in [("hint", "ft1v2"), ("instructed", "ft1v2")]:
            inter = pd_tops[a] & pd_tops[b]
            lay["overlap_jaccard"][f"probe:{a}&{b}"] = {
                "jaccard": round(len(inter) / len(pd_tops[a] | pd_tops[b]), 3),
                "shared_feats": sorted(int(f) for f in inter)}
        # 4 SAE-space transfer
        for a, b in [("hint", "ft1v2"), ("instructed", "ft1v2"), ("hint", "instructed")]:
            sc, m = lr_fit(feats[a], ys[a])
            lay["sae_space_transfer"][f"{a}->{b}"] = round(
                auroc(ys[b], m.predict_proba(sc.transform(feats[b]))[:, 1]), 3)
        res["layers"][str(L)] = lay
        print(f"[L{L}] ve={lay['recon_var_explained']} | "
              f"jacc hint&ft12={lay['overlap_jaccard']['hint&ft1v2']['jaccard']} "
              f"instr&ft12={lay['overlap_jaccard']['instructed&ft1v2']['jaccard']} | "
              f"sae-transfer hint->ft12={lay['sae_space_transfer']['hint->ft1v2']} "
              f"instr->ft12={lay['sae_space_transfer']['instructed->ft1v2']}", flush=True)
    except Exception:
        print(f"[L{L}] FAILED:\n{traceback.format_exc()}", flush=True)
        res["layers"][str(L)] = {"error": traceback.format_exc(limit=2)}
    json.dump(res, open(OUT, "w"), indent=1)
print(f"SAE_TRANSFERS DONE -> {OUT}", flush=True)
