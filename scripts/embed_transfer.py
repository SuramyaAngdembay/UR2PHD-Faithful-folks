"""Text-baseline TRANSFER control (temper Tier-2 #9): train frozen-RoBERTa-embedding LR
on hint labels (llama), test on annotated ft1v2 (llama). If ~chance, no mundane text
carrier explains the 0.616 activation transfer. Output: ~/synth/results/embed_transfer.json"""
import glob, json, os
import numpy as np, torch
from transformers import AutoModel, AutoTokenizer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score

DEV = "cuda:1"; torch.cuda.set_device(1)
tok = AutoTokenizer.from_pretrained("roberta-large-mnli")
enc = AutoModel.from_pretrained("roberta-large-mnli").to(DEV).eval()
@torch.no_grad()
def embed(texts):
    out = []
    for i in range(0, len(texts), 16):
        b = tok(texts[i:i+16], padding=True, truncation=True, max_length=512, return_tensors="pt").to(DEV)
        h = enc(**b).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1)
        out.append(((h * m).sum(1) / m.sum(1)).float().cpu().numpy())
    return np.vstack(out)

# train set: llama hint testbed (math)
tx, ty = [], []
for ds in ("aqua", "gsm8k", "aquarat"):
    p = os.path.expanduser(f"~/synth/traces_llama_hint_{ds}.json")
    if not os.path.exists(p): p = os.path.expanduser(f"~/synth/traces_llama_hint.json")
    if not os.path.exists(p): continue
    for t in json.load(open(p)):
        tx.append(t["question"] + "\n" + t["cot"]); ty.append(1 if t["condition"] == "posthoc" else 0)
if not tx:
    for p in glob.glob(os.path.expanduser("~/synth/traces_llama*hint*.json")):
        for t in json.load(open(p)):
            tx.append(t["question"] + "\n" + t["cot"]); ty.append(1 if t["condition"] == "posthoc" else 0)
ty = np.array(ty); print(f"hint train n={len(ty)} pos={ty.sum()}", flush=True)

# test set: annotated ft1v2 llama
BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
ex, ey = [], []
for dom in ("truthfulqa", "logiqa", "aqua", "HLE_BIO"):
    for f in glob.glob(os.path.join(BASE, dom, "llama-3.1-8b-instruct", "response_*.json")):
        d = json.load(open(f)); ft = d.get("faithful_type")
        if ft not in (1, 2): continue
        s = d["sample_0"]
        steps = [s[k] for k in sorted([k for k in s if k.startswith("step_")], key=lambda x: int(x.split("_")[1]))]
        if not steps: continue
        ex.append(d.get("question", "") + "\n" + "\n".join(steps)); ey.append(1 if ft == 2 else 0)
ey = np.array(ey); print(f"ft1v2 test n={len(ey)} pos={ey.sum()}", flush=True)

Xtr, Xte = embed(tx), embed(ex)
clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=1.0)).fit(Xtr, ty)
sc = clf.predict_proba(Xte)[:, 1]
a = roc_auc_score(ey, sc)
rng = np.random.default_rng(0); v = []
for _ in range(3000):
    i = rng.integers(0, len(ey), len(ey))
    if len(set(ey[i])) == 2: v.append(roc_auc_score(ey[i], sc[i]))
res = {"train_n": int(len(ty)), "test_n": int(len(ey)), "transfer_auroc": round(float(a), 3),
       "ci95": [round(float(q), 3) for q in np.percentile(v, [2.5, 97.5])]}
json.dump(res, open(os.path.expanduser("~/synth/results/embed_transfer.json"), "w"), indent=1)
print(json.dumps(res)); print("EMBED_TRANSFER DONE", flush=True)
