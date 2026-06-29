"""
GRACE second-benchmark replication (step-level). GRACE ships per-step human faithfulness
labels + citations + passages. We test whether NLI step-support predicts the human step
label -- the same mechanism that was weak on FaithCoT-Bench -- on an INDEPENDENT, step-level
benchmark. Premise = question + cited passages + prior steps; hypothesis = the step.
NOTE: only ~40 labeled examples are public, so this is a PRELIMINARY cross-benchmark check.
"""
import json, os, statistics
import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from scipy.stats import rankdata

GRACE = os.path.expanduser("~/ur2phd/upstream/grace/data/grace_examples.json")
NLI = "roberta-large-mnli"; GPU = 0; DEV = f"cuda:{GPU}"
torch.cuda.set_device(GPU)
tok = AutoTokenizer.from_pretrained(NLI)
model = AutoModelForSequenceClassification.from_pretrained(NLI).to(DEV).eval()
id2 = {int(k): v.upper() for k, v in model.config.id2label.items()}
ENT = [i for i, l in id2.items() if "ENTAIL" in l][0]; CON = [i for i, l in id2.items() if "CONTRADICT" in l][0]
print("NLI loaded", flush=True)

@torch.no_grad()
def nli(prem, hyp):
    enc = tok([p[:4000] for p in prem], [h[:2000] for h in hyp], truncation=True, max_length=512,
              padding=True, return_tensors="pt").to(DEV)
    p = torch.softmax(model(**enc).logits, dim=-1)
    return p[:, ENT].tolist(), p[:, CON].tolist()

def auroc(scores, labels):
    labels = np.asarray(labels); npos = labels.sum(); nneg = len(labels) - npos
    if npos == 0 or nneg == 0: return None
    rk = rankdata(scores)
    return (rk[labels == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg)

data = json.load(open(GRACE))
rows = []
for rec in data:
    q = rec.get("question", "") or ""
    passages = {p["ref_id"]: p.get("text", "") for p in rec.get("passages", [])}
    prev = ""
    prem, hyp, ys, tr = [], [], [], []
    for s in rec.get("steps", []):
        cites = "\n".join(passages.get(r, "") for r in (s.get("citations") or []))
        context = q + (("\n" + cites) if cites else "") + (("\n" + prev) if prev else "")
        prem.append(context); hyp.append(s.get("step_text", ""))
        lab = s.get("faithfulness", "")
        ys.append(1 if lab == "unfaithful" else 0 if lab == "faithful" else None)
        tr.append(rec.get("track"))
        prev += "\n" + s.get("step_text", "")
    if not hyp: continue
    ent, con = nli(prem, hyp)
    for e, c, y, t in zip(ent, con, ys, tr):
        if y is None: continue
        rows.append(dict(entail=e, contra=c, supp=e - c, y=y, track=t))

print(f"\nGRACE step-level: {len(rows)} labeled steps from {len(data)} traces; "
      f"unfaithful={sum(r['y'] for r in rows)} ({sum(r['y'] for r in rows)/max(len(rows),1):.0%})")
def rep(R, name):
    if len(R) < 10: print(f"  [{name}] n={len(R)} (too few)"); return
    y = [r["y"] for r in R]
    print(f"  [{name}] n={len(R)} unfaithful={sum(y)}")
    for k in ["entail", "supp", "contra"]:
        a = auroc([r[k] for r in R], y)
        if a is None: continue
        print(f"      AUROC {k:6s} = {(a if a>=0.5 else 1-a):.3f} ({'higher' if a>=0.5 else 'lower'}->unfaithful)")
rep(rows, "ALL")
rep([r for r in rows if r["track"] == "evidence"], "evidence track")
rep([r for r in rows if r["track"] == "deductive"], "deductive track")
print("\n(Preliminary: GRACE ships only ~40 labeled examples publicly. Compare to FaithCoT NLI ~0.57.)")
