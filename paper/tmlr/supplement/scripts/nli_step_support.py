"""
NLI per-step SUPPORT verification (orthogonal to answer-tracing).
For each step: NLI(premise = question + prior steps, hypothesis = step) -> P(entail), P(contra).
Aggregate support per trace; test (1) AUROC vs human `unfaithfulness`, (2) whether it ADDS
to `soft` (answer-tracing) via partial Spearman controlling for soft (and for correctness).
Model-agnostic NLI (roberta-large-mnli). NL-reasoning domains only (truthfulqa, logiqa).
"""
import json, glob, os, math, statistics
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from scipy.stats import spearmanr

BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
NLI = "roberta-large-mnli"
GROUPS = [("truthfulqa", "llama-3.1-8b-instruct"), ("truthfulqa", "Qwen2.5-7B-Instruct"),
          ("logiqa", "llama-3.1-8b-instruct"), ("logiqa", "Qwen2.5-7B-Instruct")]
GPU = 0; DEV = f"cuda:{GPU}"
torch.cuda.set_device(GPU)
tok = AutoTokenizer.from_pretrained(NLI)
model = AutoModelForSequenceClassification.from_pretrained(NLI).to(DEV).eval()
id2label = {int(k): v.upper() for k, v in model.config.id2label.items()}
ENT = [i for i, l in id2label.items() if "ENTAIL" in l][0]
CON = [i for i, l in id2label.items() if "CONTRADICT" in l][0]
print("NLI loaded:", id2label, flush=True)

@torch.no_grad()
def nli(premises, hyps):
    enc = tok(premises, hyps, truncation="only_first", max_length=512, padding=True, return_tensors="pt").to(DEV)
    p = torch.softmax(model(**enc).logits, dim=-1)
    return p[:, ENT].tolist(), p[:, CON].tolist()

def auroc(scores, labels):
    n = len(scores); npos = sum(labels); nneg = n - npos
    if npos == 0 or nneg == 0: return None
    order = sorted(range(n), key=lambda i: scores[i]); ranks = [0.0]*n; i = 0
    while i < n:
        j = i
        while j+1 < n and scores[order[j+1]] == scores[order[i]]: j += 1
        r = (i+j)/2.0 + 1
        for k in range(i, j+1): ranks[order[k]] = r
        i = j+1
    return (sum(ranks[i] for i in range(n) if labels[i] == 1) - npos*(npos+1)/2)/(npos*nneg)

def spr(x, y):
    r = spearmanr(x, y).correlation; return r if r == r else 0.0
def partial(x, y, z):
    rxy, rxz, ryz = spr(x, y), spr(x, z), spr(y, z)
    return (rxy - rxz*ryz)/math.sqrt(max((1-rxz**2)*(1-ryz**2), 1e-9))

rows = []
for dom, m in GROUPS:
    for f in glob.glob(os.path.join(BASE, dom, m, "response_*.json")):
        d = json.load(open(f)); uf = d.get("unfaithfulness")
        if uf not in (0, 1): continue
        s = d["sample_0"]
        steps = [s[k] for k in sorted([k for k in s if k.startswith("step_")], key=lambda x: int(x.split("_")[1]))]
        if len(steps) < 2: continue
        q = d.get("question", "")
        prem = [q + (("\n" + "\n".join(steps[:i])) if i > 0 else "") for i in range(len(steps))]
        ent, con = nli(prem, steps)
        supp = [e - c for e, c in zip(ent, con)]
        ft = d.get("faithful_type")
        rows.append(dict(dom=dom, y=uf, ft=ft,
                         correct=(1 if ft in (1, 2) else 0 if ft in (3, 4) else None),
                         soft=s.get("soft_faithfulness"),
                         mean_ent=statistics.mean(ent), min_ent=min(ent),
                         mean_supp=statistics.mean(supp), min_supp=min(supp),
                         n_unsup=sum(1 for e in ent if e < 0.5), frac_con=statistics.mean(con)))

R = [r for r in rows if r["soft"] is not None]
y = [r["y"] for r in R]
print(f"\nn={len(R)} unfaithful={sum(y)} ({sum(y)/len(y):.0%})")
feats = ["soft", "mean_ent", "min_ent", "mean_supp", "min_supp", "n_unsup", "frac_con"]
def o(v): return None if v is None else (v if v >= 0.5 else 1 - v)
def fmt(v): return "  -  " if v is None else f"{v:.3f}"
Rc = [r for r in R if r["correct"] == 1]; Ri = [r for r in R if r["correct"] == 0]
print(f"\n{'feature':9s} {'AUROC':>7s} {'AUROC|cor':>10s} {'AUROC|inc':>10s} {'pSpear|soft':>12s} {'pSpear|cor':>11s}")
for k in feats:
    sc = [r[k] for r in R]
    a = o(auroc(sc, y)); ac = o(auroc([r[k] for r in Rc], [r["y"] for r in Rc])); ai = o(auroc([r[k] for r in Ri], [r["y"] for r in Ri]))
    ps_soft = partial(sc, y, [r["soft"] for r in R])
    ps_cor = partial(sc, y, [1 if r["correct"] else 0 for r in R])
    print(f"{k:9s} {fmt(a):>7s} {fmt(ac):>10s} {fmt(ai):>10s} {ps_soft:>+12.3f} {ps_cor:>+11.3f}")
print("\nAUROC oriented >=0.5. pSpear|soft = partial Spearman(feature, unfaithful | soft):")
print("nonzero => the support signal ADDS to answer-tracing. cor = | correctness.")
