"""Question-only (pre-CoT) probe on the hint testbed -> quantifies difficulty leakage.
Extracts last-token hidden states of [question(+options), generation prompt] at every layer,
then max-over-layers CV AUROC vs the genuine/posthoc label. If this approaches the CoT probe,
the probe is reading difficulty, not rationalization. Usage: --mdir llama --gpu 0"""
import argparse, json, os
import numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
ap = argparse.ArgumentParser()
ap.add_argument("--mdir", required=True); ap.add_argument("--gpu", type=int, default=0)
a = ap.parse_args()
MODELS = {"llama": "meta-llama/Llama-3.1-8B-Instruct", "qwen": "Qwen/Qwen2.5-7B-Instruct"}
torch.cuda.set_device(a.gpu); DEV = f"cuda:{a.gpu}"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(MODELS[a.mdir])
try: model = AutoModelForCausalLM.from_pretrained(MODELS[a.mdir], quantization_config=bnb, device_map={"": a.gpu}, dtype=torch.bfloat16)
except TypeError: model = AutoModelForCausalLM.from_pretrained(MODELS[a.mdir], quantization_config=bnb, device_map={"": a.gpu}, torch_dtype=torch.bfloat16)
model.eval()
NL = model.config.num_hidden_layers
traces = []
for ds in ("aqua", "gsm8k", "aquarat"):
    p = os.path.expanduser(f"~/synth/traces_{a.mdir}_hint_{ds}.json")
    if os.path.exists(p): traces += json.load(open(p))
y = np.array([1 if t["condition"] == "posthoc" else 0 for t in traces])
print(f"{a.mdir}: {len(traces)} traces, {int(y.sum())} posthoc", flush=True)
X = np.zeros((NL, len(traces), model.config.hidden_size), dtype=np.float16)
with torch.no_grad():
    for i, t in enumerate(traces):
        user = t["question"] + (("\n\nOptions:\n" + "\n".join(t["options"])) if t.get("options") else "")
        enc = tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True,
                                      return_tensors="pt", return_dict=True).to(DEV)
        hs = model(**enc, output_hidden_states=True).hidden_states
        for L in range(1, NL + 1): X[L-1, i] = hs[L][0, -1].float().cpu().numpy()
        if (i+1) % 100 == 0: print(f"  {i+1}/{len(traces)}", flush=True)
def cv(Xl, yy):
    skf = StratifiedKFold(5, shuffle=True, random_state=0); oof = np.zeros(len(yy))
    for tr, te in skf.split(Xl, yy):
        pipe = make_pipeline(StandardScaler(), PCA(min(50, len(tr)-2), random_state=0), LogisticRegression(max_iter=2000))
        oof[te] = pipe.fit(Xl[tr], yy[tr]).predict_proba(Xl[te])[:, 1]
    return roc_auc_score(yy, oof)
aucs = [cv(X[l].astype(np.float32), y) for l in range(NL)]
b = int(np.argmax(aucs))
res = {"model": a.mdir, "qonly_best_layer": b, "qonly_best_cv": float(aucs[b]),
       "qonly_mean_cv": float(np.mean(aucs)), "per_layer": [float(x) for x in aucs]}
json.dump(res, open(os.path.expanduser(f"~/synth/results/qonly_{a.mdir}.json"), "w"), indent=2)
print(f"QONLY DONE {a.mdir}: best question-only CV {aucs[b]:.3f} @L{b} (CoT probe was 0.733/0.832)", flush=True)
