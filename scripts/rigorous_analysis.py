"""
Rigorous, scaled observational analysis (ALL 4 domains x ALL 4 models).
Per annotated trace: human y (unfaithfulness), ft, ft-based correctness, soft, hard,
avg_impact, heuristic DAG features, NLI step-support features, n_steps.
Reports AUROC + bootstrap 95% CI (significance = CI excludes 0.5) for each signal vs the
human label, broken out overall / ft1v2 (post-hoc-on-correct) / ft3v4 / per-domain.
Caches per-trace features to ~/rigorous_features.json so stats can be re-run without NLI.
"""
import json, glob, os, re, statistics, sys
from collections import defaultdict
import numpy as np
from scipy.stats import rankdata, spearmanr
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
NLI = "roberta-large-mnli"
FEAT = os.path.expanduser("~/rigorous_features.json")
DOMAINS = ["truthfulqa", "logiqa", "aqua", "HLE_BIO"]
MODELS = ["llama-3.1-8b-instruct", "Qwen2.5-7B-Instruct", "gpt-4o-mini", "gemini-2.5-flash"]
GPU = 0; DEV = f"cuda:{GPU}"

def extract_premises(steps):
    prem = {}
    for i, step in enumerate(steps):
        sl = step.lower(); s = set()
        for m in re.findall(r'step\s*(\d+)', sl):
            j = int(m) - 1
            if 0 <= j < i: s.add(j)
        if i > 0 and any(c in sl for c in ['therefore','thus','hence','so,','because','this means','it follows','the answer','consequently']):
            s.add(i - 1)
        pn = set(re.findall(r'\b[A-Z][a-z]+\b', step)); nm = set(re.findall(r'\b\d+\.?\d*\b', step))
        for j in range(i):
            if len(pn & set(re.findall(r'\b[A-Z][a-z]+\b', steps[j]))) >= 2 or len(nm & set(re.findall(r'\b\d+\.?\d*\b', steps[j]))) >= 2: s.add(j)
        if not s and i > 0: s.add(i - 1)
        if i == 0: s.add(-1)
        prem[i] = sorted(s)
    return prem

def dag_feats(n, prem):
    adj = defaultdict(list)
    for c, ps in prem.items():
        for p in ps: adj[p].append(c)
    dc = {}
    def cd(x):
        if x in dc: return dc[x]
        t = len(adj.get(x, []))
        for ch in adj.get(x, []): t += cd(ch)
        dc[x] = t; return t
    for i in range(-1, n): cd(i)
    lb = max((len(adj.get(i, [])) * (1 + dc.get(i, 0)) for i in range(n)), default=0)
    lin = sum(1 for i in range(1, n) if prem.get(i, []) == [i - 1]) / max(n - 1, 1)
    return {"dag_lin": round(lin, 3), "dag_maxlb": lb}

def avg_impact(s):
    probs = s.get("intermediate_answer_probabilities") or []
    sh = [sum(abs(probs[i-1].get(k, 0) - probs[i].get(k, 0)) for k in set(probs[i-1]) | set(probs[i]))
          for i in range(1, len(probs)) if probs[i-1] and probs[i]]
    return sum(sh) / len(sh) if sh else None

# ---- build features (cache) ----
if os.path.exists(FEAT) and "--use-cache" in sys.argv:
    rows = json.load(open(FEAT)); print(f"loaded cached features: {len(rows)}", flush=True)
else:
    torch.cuda.set_device(GPU)
    tok = AutoTokenizer.from_pretrained(NLI)
    nli = AutoModelForSequenceClassification.from_pretrained(NLI).to(DEV).eval()
    id2 = {int(k): v.upper() for k, v in nli.config.id2label.items()}
    ENT = [i for i, l in id2.items() if "ENTAIL" in l][0]; CON = [i for i, l in id2.items() if "CONTRADICT" in l][0]
    print("NLI loaded", flush=True)
    @torch.no_grad()
    def nli_supp(q, steps):
        steps = [s[:2000] for s in steps]  # cap so the hypothesis can't exceed the NLI window
        prem = [(q + (("\n" + "\n".join(steps[:i])) if i > 0 else ""))[:4000] for i in range(len(steps))]
        enc = tok(prem, steps, truncation=True, max_length=512, padding=True, return_tensors="pt").to(DEV)
        p = torch.softmax(nli(**enc).logits, dim=-1)
        ent = p[:, ENT].tolist(); con = p[:, CON].tolist()
        return {"nli_min_ent": min(ent), "nli_mean_ent": statistics.mean(ent),
                "nli_n_unsup": sum(1 for e in ent if e < 0.5), "nli_frac_con": statistics.mean(con)}
    rows = []
    for dom in DOMAINS:
        for m in MODELS:
            for f in glob.glob(os.path.join(BASE, dom, m, "response_*.json")):
                d = json.load(open(f)); uf = d.get("unfaithfulness")
                if uf not in (0, 1): continue
                s = d.get("sample_0", {})
                steps = [s[k] for k in sorted([k for k in s if k.startswith("step_")], key=lambda x: int(x.split("_")[1]))]
                if len(steps) < 2: continue
                ft = d.get("faithful_type")
                r = dict(dom=dom, model=m, y=uf, ft=ft,
                         correct=(1 if ft in (1, 2) else 0 if ft in (3, 4) else None),
                         soft=s.get("soft_faithfulness"), hard=s.get("hard_faithfulness"),
                         avg_impact=avg_impact(s), n_steps=len(steps),
                         **dag_feats(len(steps), extract_premises(steps)),
                         **nli_supp(d.get("question", ""), steps))
                rows.append(r)
            print(f"  {dom}/{m}: total rows now {len(rows)}", flush=True)
    json.dump(rows, open(FEAT, "w"))
    print(f"cached {len(rows)} -> {FEAT}", flush=True)

# ---- stats: AUROC + bootstrap CI ----
def auc(scores, labels):
    labels = np.asarray(labels); npos = labels.sum(); nneg = len(labels) - npos
    if npos == 0 or nneg == 0: return np.nan
    rk = rankdata(scores)
    return (rk[labels == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg)

def auc_ci(scores, labels, B=1000):
    scores = np.asarray(scores, float); labels = np.asarray(labels, int); n = len(scores)
    rng = np.random.default_rng(0); vals = []
    for _ in range(B):
        idx = rng.integers(0, n, n); a = auc(scores[idx], labels[idx])
        if not np.isnan(a): vals.append(a)
    return auc(scores, labels), np.percentile(vals, 2.5), np.percentile(vals, 97.5)

SIGNALS = ["soft", "hard", "avg_impact", "correct", "dag_lin", "dag_maxlb", "nli_n_unsup", "nli_min_ent"]
def subset(rows, pred): return [r for r in rows if pred(r)]
def show(R, name):
    R = [r for r in R if r.get("soft") is not None and r.get("avg_impact") is not None]
    y = [r["y"] for r in R]
    if len(R) < 12 or sum(y) == 0 or sum(y) == len(y): print(f"\n[{name}] n={len(R)} (skip)"); return
    print(f"\n[{name}] n={len(R)} unfaithful={sum(y)} ({sum(y)/len(y):.0%})")
    for sig in SIGNALS:
        sc = [r[sig] if r[sig] is not None else 0 for r in R]
        a, lo, hi = auc_ci(sc, y)
        star = "  *" if (lo > 0.5 or hi < 0.5) else "   "  # CI excludes chance
        print(f"   {sig:12s} AUROC {a:.3f}  [{lo:.3f}, {hi:.3f}]{star}")

print("\n" + "=" * 64 + "\nAUROC vs human `unfaithfulness`  (95% bootstrap CI; * = CI excludes 0.5)\n" + "=" * 64)
show(rows, "ALL domains+models")
show(subset(rows, lambda r: r["correct"] == 1), "ft1v2  CORRECT regime (post-hoc-on-correct = F1 frontier)")
show(subset(rows, lambda r: r["correct"] == 0), "ft3v4  INCORRECT regime")
for dom in DOMAINS:
    show(subset(rows, lambda r, d=dom: r["dom"] == d), f"domain={dom}")

# ---- F2: soft polarity (mean soft unfaithful - faithful) with bootstrap CI ----
R = [r for r in rows if r.get("soft") is not None]
sf = np.array([r["soft"] for r in R]); yy = np.array([r["y"] for r in R])
rng = np.random.default_rng(1); diffs = []
for _ in range(2000):
    idx = rng.integers(0, len(R), len(R))
    d_ = sf[idx][yy[idx] == 1].mean() - sf[idx][yy[idx] == 0].mean(); diffs.append(d_)
obs = sf[yy == 1].mean() - sf[yy == 0].mean()
print(f"\n[F2 polarity] mean(soft|unfaithful) - mean(soft|faithful) = {obs:+.3f} "
      f"[{np.percentile(diffs,2.5):+.3f}, {np.percentile(diffs,97.5):+.3f}]  (>0 => metric inverts)")
