"""Learned raw-text behavioral baseline: frozen roberta-large-mnli encoder embeddings
(mean-pooled) + logistic regression, 5-fold CV, on (a) FaithCoT ft1v2, (b) instructed
construction, (c) hint testbed, for llama+qwen sets. Usage: --gpu 1"""
import argparse, glob, json, os
import numpy as np, torch
from transformers import AutoModel, AutoTokenizer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
ap = argparse.ArgumentParser(); ap.add_argument("--gpu", type=int, default=1); a = ap.parse_args()
DEV = f"cuda:{a.gpu}"; torch.cuda.set_device(a.gpu)
tok = AutoTokenizer.from_pretrained("roberta-large-mnli")
enc_model = AutoModel.from_pretrained("roberta-large-mnli").to(DEV).eval()
@torch.no_grad()
def embed(texts):
    out = []
    for i in range(0, len(texts), 16):
        b = tok(texts[i:i+16], padding=True, truncation=True, max_length=512, return_tensors="pt").to(DEV)
        h = enc_model(**b).last_hidden_state
        mask = b["attention_mask"].unsqueeze(-1)
        out.append(((h * mask).sum(1) / mask.sum(1)).float().cpu().numpy())
    return np.vstack(out)
def cv_auc(X, y):
    skf = StratifiedKFold(5, shuffle=True, random_state=0); oof = np.zeros(len(y))
    for tr, te in skf.split(X, y):
        p = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=1.0))
        oof[te] = p.fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return roc_auc_score(y, oof)
res = {}
BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
MDIR = {"llama": "llama-3.1-8b-instruct", "qwen": "Qwen2.5-7B-Instruct"}
for m, mdir in MDIR.items():
    texts, y = [], []
    for dom in ("truthfulqa", "logiqa", "aqua", "HLE_BIO"):
        for f in glob.glob(os.path.join(BASE, dom, mdir, "response_*.json")):
            d = json.load(open(f)); ft = d.get("faithful_type")
            if ft not in (1, 2): continue
            s = d["sample_0"]
            steps = [s[k] for k in sorted([k for k in s if k.startswith("step_")], key=lambda x: int(x.split("_")[1]))]
            if not steps: continue
            texts.append(d.get("question", "") + "\n" + "\n".join(steps)); y.append(1 if ft == 2 else 0)
    y = np.array(y)
    res[f"faithcot_{m}"] = {"n": len(y), "auroc": float(cv_auc(embed(texts), y))}
    print(f"faithcot {m}: n={len(y)} embed-LR AUROC {res[f'faithcot_{m}']['auroc']:.3f}", flush=True)
for tag, label in (("", "instructed"), ("_hint", "hint")):
    for m in ("llama", "qwen"):
        texts, y = [], []
        for ds in ("aqua", "gsm8k", "aquarat"):
            p = os.path.expanduser(f"~/synth/traces_{m}{tag}_{ds}.json")
            if not os.path.exists(p): continue
            for t in json.load(open(p)):
                texts.append(t["question"] + "\n" + t["cot"]); y.append(1 if t["condition"] == "posthoc" else 0)
        y = np.array(y)
        res[f"{label}_{m}"] = {"n": len(y), "auroc": float(cv_auc(embed(texts), y))}
        print(f"{label} {m}: n={len(y)} embed-LR AUROC {res[f'{label}_{m}']['auroc']:.3f}", flush=True)
json.dump(res, open(os.path.expanduser("~/synth/results/embed_baseline.json"), "w"), indent=2)
print("EMBED_BASELINE DONE", flush=True)
