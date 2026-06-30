"""
White-box probe v2 (RIGOROUS). Detect ft2 (post-hoc) vs ft1 (genuine) on CORRECT answers
from internal activations -- the F1 frontier where all black-box signals are at 0.50.
Fixes v1's issues: PCA(50)->logistic (kills high-dim overfitting that inflated the null),
and a PERMUTATION TEST (max-over-layers null) for a proper p-value that corrects best-layer
selection. One model per process (avoids OOM); caches hidden states. CV/permutation on CPU.
Usage: --model {llama|qwen} --gpu N --nperm 200
"""
import json, glob, os, argparse
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True, choices=["llama", "qwen"])
ap.add_argument("--gpu", type=int, default=0)
ap.add_argument("--nperm", type=int, default=200)
ap.add_argument("--pca", type=int, default=50)
a = ap.parse_args()

BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
DOMAINS = ["truthfulqa", "logiqa", "aqua", "HLE_BIO"]
MODELS = {"llama": "meta-llama/Llama-3.1-8B-Instruct", "qwen": "Qwen/Qwen2.5-7B-Instruct"}
MDIR = {"llama": "llama-3.1-8b-instruct", "qwen": "Qwen2.5-7B-Instruct"}
mname, mdir = MODELS[a.model], MDIR[a.model]
DEV = f"cuda:{a.gpu}"
Xp = os.path.expanduser(f"~/wbX_{a.model}.npy"); yp = os.path.expanduser(f"~/wby_{a.model}.npy")

def load_traces():
    out = []
    for dom in DOMAINS:
        for f in glob.glob(os.path.join(BASE, dom, mdir, "response_*.json")):
            d = json.load(open(f)); ft = d.get("faithful_type")
            if ft not in (1, 2): continue
            s = d["sample_0"]
            steps = [s[k] for k in sorted([k for k in s if k.startswith("step_")], key=lambda x: int(x.split("_")[1]))]
            if not steps: continue
            out.append(dict(q=d.get("question", ""), opts=d.get("options", []), steps=steps, y=1 if ft == 2 else 0))
    return out

if os.path.exists(Xp):
    X = np.load(Xp); y = np.load(yp); print(f"loaded cached X {X.shape}", flush=True)
else:
    torch.cuda.set_device(a.gpu)
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    tok = AutoTokenizer.from_pretrained(mname)
    try:
        model = AutoModelForCausalLM.from_pretrained(mname, quantization_config=bnb, device_map={"": a.gpu}, dtype=torch.bfloat16)
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(mname, quantization_config=bnb, device_map={"": a.gpu}, torch_dtype=torch.bfloat16)
    model.eval()
    tr = load_traces(); y = np.array([t["y"] for t in tr])
    print(f"{a.model}: n={len(tr)} ft2={int(y.sum())} ft1={int((y==0).sum())}", flush=True)
    Xs = []
    with torch.no_grad():
        for t in tr:
            cot = "\n".join(f"Step {i+1}: {s}" for i, s in enumerate(t["steps"]))
            user = t["q"] + (("\n\nOptions:\n" + "\n".join(t["opts"])) if t["opts"] else "")
            enc = tok.apply_chat_template([{"role": "user", "content": user}, {"role": "assistant", "content": cot}],
                                          return_tensors="pt", return_dict=True).to(DEV)
            hs = model(**enc, output_hidden_states=True).hidden_states
            Xs.append(torch.stack([h[0, -1, :].float() for h in hs]).cpu().numpy())
    X = np.stack(Xs); np.save(Xp, X); np.save(yp, y)
    del model; torch.cuda.empty_cache()
    print(f"extracted+cached X {X.shape}", flush=True)

cv = StratifiedKFold(5, shuffle=True, random_state=0)
ncomp = min(a.pca, X.shape[0] - 25)
def layer_aucs(yy):
    return [cross_val_score(make_pipeline(StandardScaler(), PCA(n_components=ncomp), LogisticRegression(C=1.0, max_iter=2000)),
                            X[:, L, :], yy, cv=cv, scoring="roc_auc", n_jobs=5).mean() for L in range(X.shape[1])]

real = layer_aucs(y); bestL = int(np.argmax(real)); best = real[bestL]
print(f"real: best layer {bestL}/{X.shape[1]-1} AUROC {best:.3f} (PCA{ncomp})", flush=True)
rng = np.random.default_rng(0); nullmax = []
for i in range(a.nperm):
    nullmax.append(max(layer_aucs(rng.permutation(y))))
    if (i + 1) % 50 == 0: print(f"  perm {i+1}/{a.nperm}", flush=True)
nullmax = np.array(nullmax)
pval = (np.sum(nullmax >= best) + 1) / (a.nperm + 1)
print(f"\n[{a.model}] best-layer CV-AUROC {best:.3f} (layer {bestL}/{X.shape[1]-1})")
print(f"  permutation null (max-over-layers): mean {nullmax.mean():.3f}, 95th pct {np.percentile(nullmax,95):.3f}")
print(f"  p-value (selection-corrected) = {pval:.4f}")
print(f"  layer profile: {[round(v,3) for v in real]}")
json.dump(dict(model=a.model, n=int(X.shape[0]), n_ft2=int(y.sum()), best_layer=bestL,
               best_auroc=round(best, 3), null_mean=round(float(nullmax.mean()), 3),
               null_p95=round(float(np.percentile(nullmax, 95)), 3), p_value=round(float(pval), 4),
               layer_profile=[round(float(v), 3) for v in real]),
          open(os.path.expanduser(f"~/whitebox_{a.model}_results.json"), "w"), indent=1)
print("DONE")
