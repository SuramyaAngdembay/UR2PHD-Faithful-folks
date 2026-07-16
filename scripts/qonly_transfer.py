"""THE reviewer-priority control: does a QUESTION-ONLY probe trained on hint labels transfer to
the annotated regime? If hint->annotated transfer (0.616) were difficulty leakage, this should
transfer too; if it is ~chance while the CoT probe transfers, difficulty is ruled out as the
carrier. Trains on hint question-only reps, tests on FaithCoT pre_cot reps; layer-mean + best,
coupled permutation p (project-once). Usage: --mdir llama --gpu 0"""
import argparse, json, os
import numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
ap = argparse.ArgumentParser()
ap.add_argument("--mdir", required=True); ap.add_argument("--gpu", type=int, default=0)
ap.add_argument("--nperm", type=int, default=500)
a = ap.parse_args()
MODELS = {"llama": "meta-llama/Llama-3.1-8B-Instruct", "qwen": "Qwen/Qwen2.5-7B-Instruct"}
torch.cuda.set_device(a.gpu); DEV = f"cuda:{a.gpu}"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(MODELS[a.mdir])
try: model = AutoModelForCausalLM.from_pretrained(MODELS[a.mdir], quantization_config=bnb, device_map={"": a.gpu}, dtype=torch.bfloat16)
except TypeError: model = AutoModelForCausalLM.from_pretrained(MODELS[a.mdir], quantization_config=bnb, device_map={"": a.gpu}, torch_dtype=torch.bfloat16)
model.eval()
NL_m = model.config.num_hidden_layers
traces = []
for ds in ("aqua", "gsm8k", "aquarat"):
    p = os.path.expanduser(f"~/synth/traces_{a.mdir}_hint_{ds}.json")
    if os.path.exists(p): traces += json.load(open(p))
y = np.array([1 if t["condition"] == "posthoc" else 0 for t in traces])
X = np.zeros((NL_m, len(traces), model.config.hidden_size), dtype=np.float16)
with torch.no_grad():
    for i, t in enumerate(traces):
        user = t["question"] + (("\n\nOptions:\n" + "\n".join(t["options"])) if t.get("options") else "")
        enc = tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True,
                                      return_tensors="pt", return_dict=True).to(DEV)
        hs = model(**enc, output_hidden_states=True).hidden_states
        for L in range(1, NL_m + 1): X[L-1, i] = hs[L][0, -1].float().cpu().numpy()
        if (i+1) % 150 == 0: print(f"  extract {i+1}/{len(traces)}", flush=True)
np.savez_compressed(os.path.expanduser(f"~/synth/qacts_{a.mdir}_hint.npz"), X=X, y=y)
w = np.load(os.path.expanduser(f"~/wbrep_{a.mdir}.npz"), allow_pickle=True)
pre, fy = w["pre_cot"], w["y"]; NL = min(NL_m, pre.shape[1] - 1)
PROJ = []
for l in range(NL):
    sc = StandardScaler().fit(X[l].astype(np.float32))
    pc = PCA(max(2, min(50, X.shape[1]-2)), random_state=0).fit(sc.transform(X[l].astype(np.float32)))
    PROJ.append((pc.transform(sc.transform(X[l].astype(np.float32))),
                 pc.transform(sc.transform(pre[:, l+1, :].astype(np.float32)))))
def sweep(yy):
    return np.array([roc_auc_score(fy, LogisticRegression(max_iter=2000, C=1.0)
                     .fit(PROJ[l][0], yy).predict_proba(PROJ[l][1])[:, 1]) for l in range(NL)])
obs = sweep(y)
rng = np.random.default_rng(0)
nm, nb = [], []
for i in range(a.nperm):
    pm = sweep(rng.permutation(y)); nm.append(pm.mean()); nb.append(pm.max())
    if (i+1) % 100 == 0: print(f"  perm {i+1}", flush=True)
res = {"model": a.mdir, "qonly_transfer_mean": float(obs.mean()),
       "qonly_transfer_best": float(obs.max()), "best_layer": int(obs.argmax()),
       "p_mean": (1 + sum(m >= obs.mean() for m in nm)) / (1 + a.nperm),
       "p_best": (1 + sum(m >= obs.max() for m in nb)) / (1 + a.nperm)}
json.dump(res, open(os.path.expanduser(f"~/synth/results/qonly_transfer_{a.mdir}.json"), "w"), indent=2)
print(f"QONLY_TRANSFER DONE {a.mdir}: mean {obs.mean():.3f} p={res['p_mean']:.3f} | best {obs.max():.3f} p={res['p_best']:.3f}", flush=True)
