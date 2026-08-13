"""REPRODUCTION of FaithCoT-Bench's central validity claim: their step-removal AUC metric
(sample_0.soft_faithfulness / hard_faithfulness, precomputed by THEM) should separate faithful
from unfaithful. We reproduce against (a) their human unfaithfulness label and (b) the ft3-vs-ft4
correct regime, per model, with bootstrap CIs. No model needed -- reads their stored scores.
Also: does soft add value beyond correctness (their conflation caveat)? partial check."""
import json, glob, os
import numpy as np, collections
BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
def auroc(s, t):
    s=np.asarray(s,float); t=np.asarray(t,float)
    o=np.argsort(s,kind='mergesort'); r=np.empty(len(s)); x=s[o]; i=0
    while i<len(x):
        j=i
        while j+1<len(x) and x[j+1]==x[i]: j+=1
        r[o[i:j+1]]=(i+1+j+1)/2.0; i=j+1
    n1=t.sum(); n0=len(t)-n1
    return (r[t==1].sum()-n1*(n1+1)/2)/(n1*n0) if n1>0 and n0>0 else float('nan')
def ci(s,t,B=2000):
    rng=np.random.default_rng(0); v=[]
    for _ in range(B):
        i=rng.integers(0,len(s),len(s))
        if len(np.unique(t[i]))<2: continue
        v.append(auroc(s[i],t[i]))
    return np.percentile(v,[2.5,97.5]) if v else (float('nan'),float('nan'))
recs=[]
for dom in ("truthfulqa","logiqa","aqua","HLE_BIO"):
    for md in ("llama-3.1-8b-instruct","Qwen2.5-7B-Instruct","gpt-4o-mini","gemini-2.5-flash"):
        for f in glob.glob(f"{BASE}/{dom}/{md}/response_*.json"):
            d=json.load(open(f)); s=d["sample_0"]
            recs.append(dict(dom=dom, md=md, ft=d.get("faithful_type"), y=d.get("unfaithfulness"),
                             soft=s.get("soft_faithfulness"), hard=s.get("hard_faithfulness")))
out={}
print("="*70); print("REPRO 1: THEIR step-removal metric vs THEIR human label (soft high=?)")
R=[r for r in recs if r['soft'] is not None and r['y'] in (0,1)]
for md in ("all","llama-3.1-8b-instruct","Qwen2.5-7B-Instruct","gpt-4o-mini","gemini-2.5-flash"):
    RR=R if md=="all" else [r for r in R if r['md']==md]
    s=np.array([r['soft'] for r in RR]); y=np.array([r['y'] for r in RR])
    a=auroc(s,y); lo,hi=ci(s,y)
    # their intended: faithful has HIGHER soft (answer depends on steps) => soft LOW = unfaithful => AUROC(-soft)
    print(f"  {md:24s} n={len(RR):4d}  soft->unf(raw) {a:.3f} [{lo:.3f},{hi:.3f}]  | intended(-soft) {1-a:.3f}")
    out[f"soft_vs_human_{md}"]={"n":len(RR),"auroc_raw":float(a),"ci":[float(lo),float(hi)]}
print(); print("="*70); print("REPRO 2: THEIR metric on ft3(faithful)-vs-ft4(unfaithful), CORRECT regime")
R=[r for r in recs if r['soft'] is not None and r['ft'] in (3,4)]
for md in ("all","llama-3.1-8b-instruct","Qwen2.5-7B-Instruct"):
    RR=R if md=="all" else [r for r in R if r['md']==md]
    if len(RR)<20: print(f"  {md}: n={len(RR)} (skip)"); continue
    s=np.array([r['soft'] for r in RR]); y=np.array([1.0 if r['ft']==4 else 0.0 for r in RR])
    a=auroc(s,y); lo,hi=ci(s,y)
    print(f"  {md:24s} n={len(RR):4d} ft4={int(y.sum())}  soft->ft4(raw) {a:.3f} [{lo:.3f},{hi:.3f}] | intended {1-a:.3f}")
    out[f"soft_vs_ft34_{md}"]={"n":len(RR),"auroc_raw":float(a),"ci":[float(lo),float(hi)]}
json.dump(out, open(os.path.expanduser("~/synth/results/faithcot_reproduce.json"),"w"), indent=2)
print("\nFAITHCOT_REPRO DONE")
