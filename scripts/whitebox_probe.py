"""
White-box pilot on the F1 frontier (post-hoc rationalization on CORRECT answers, ft1 vs ft2).
Black-box signals are all at chance (~0.50) here. Q: is the signal INTERNAL?
For each open-weight model that generated the traces (llama, qwen): feed (question + its own CoT)
through the model, take last-token hidden states per layer, train 5-fold CV linear probes (L2)
to classify ft2 (post-hoc/unfaithful) vs ft1 (genuine/faithful). Report best-layer CV-AUROC vs
the 0.50 black-box baseline + a shuffled-label control. If probe >> 0.50 with control ~0.50,
the signal is inside the model even though behavior can't reveal it.
"""
import json, glob, os
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score

BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
DOMAINS = ["truthfulqa", "logiqa", "aqua", "HLE_BIO"]
MODELS = {"llama-3.1-8b-instruct": "meta-llama/Llama-3.1-8B-Instruct",
          "Qwen2.5-7B-Instruct": "Qwen/Qwen2.5-7B-Instruct"}
GPU = 0; DEV = f"cuda:{GPU}"
torch.cuda.set_device(GPU)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)

def load_traces(mdir):
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

@torch.no_grad()
def reps(model, tok, traces):
    X = []
    for t in traces:
        cot = "\n".join(f"Step {i+1}: {s}" for i, s in enumerate(t["steps"]))
        user = t["q"] + (("\n\nOptions:\n" + "\n".join(t["opts"])) if t["opts"] else "")
        enc = tok.apply_chat_template([{"role": "user", "content": user}, {"role": "assistant", "content": cot}],
                                      return_tensors="pt", return_dict=True).to(DEV)
        hs = model(**enc, output_hidden_states=True).hidden_states   # (L+1) x [1,seq,H]
        X.append(torch.stack([h[0, -1, :].float() for h in hs]).cpu().numpy())  # (L+1, H)
    return np.stack(X)

results = {}
for mdir, mname in MODELS.items():
    tr = load_traces(mdir); y = np.array([t["y"] for t in tr])
    print(f"\n=== {mdir}: n={len(tr)} (ft2={int(y.sum())}, ft1={int((y==0).sum())}) ===", flush=True)
    if len(tr) < 40 or y.sum() < 10 or (y == 0).sum() < 10:
        print("  too few; skip"); continue
    tok = AutoTokenizer.from_pretrained(mname)
    try:
        model = AutoModelForCausalLM.from_pretrained(mname, quantization_config=bnb, device_map={"": GPU}, dtype=torch.bfloat16)
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(mname, quantization_config=bnb, device_map={"": GPU}, torch_dtype=torch.bfloat16)
    model.eval()
    X = reps(model, tok, tr); nL = X.shape[1]
    print(f"  reps {X.shape}; probing {nL} layers (5-fold CV, L2)", flush=True)
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    def probe(XL, yy):
        clf = make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=3000))
        return cross_val_score(clf, XL, yy, cv=cv, scoring="roc_auc").mean()
    aucs = [probe(X[:, L, :], y) for L in range(nL)]
    bestL = int(np.argmax(aucs)); best = aucs[bestL]
    ysh = np.random.default_rng(0).permutation(y)
    ctrl = probe(X[:, bestL, :], ysh)
    sweep = {int(i): round(aucs[i], 3) for i in [0, nL//4, nL//2, 3*nL//4, nL-1]}
    print(f"  BEST layer {bestL}/{nL-1}: CV-AUROC {best:.3f}  | shuffled-label control {ctrl:.3f} | black-box ~0.50")
    print(f"  layer sweep: {sweep}")
    results[mdir] = dict(n=len(tr), n_ft2=int(y.sum()), best_layer=bestL, best_auroc=round(best, 3),
                         control=round(ctrl, 3), layer_aucs=[round(a, 3) for a in aucs])
    del model; torch.cuda.empty_cache()

json.dump(results, open(os.path.expanduser("~/whitebox_probe_results.json"), "w"), indent=1)
print("\nWHITEBOX PROBE DONE ->", "~/whitebox_probe_results.json")
