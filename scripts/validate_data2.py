"""Validation pass 2. Items:
 A soft coverage census (sample_0.soft_faithfulness) + unlabeled-trace details
 B question-duplication structure across models; unique-question counts
 C QUESTION-clustered bootstrap for the audit headline signals (incorrect->unf, soft)
 D our soft reimplementation vs THEIR stored sample_0.soft_faithfulness (GPU, fixed field access)
 E parser determinism on constructed sets (re-parse cot vs stored model_answer)
 F gold sanity: aquarat letters in A-E; gsm8k golds numeric
Usage: python validate_data2.py --gpu 0 --nsoft 30"""
import argparse, glob, json, os, re
import numpy as np, collections
ap = argparse.ArgumentParser()
ap.add_argument("--gpu", type=int, default=0); ap.add_argument("--nsoft", type=int, default=30)
a = ap.parse_args()
BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
DOMAINS = ["truthfulqa","logiqa","aqua","HLE_BIO"]; S = os.path.expanduser("~/synth")
def norm(q): return re.sub(r"\s+"," ",q.strip().lower())[:200]
recs = []
for dom in DOMAINS:
    for md in ("llama-3.1-8b-instruct","Qwen2.5-7B-Instruct","gpt-4o-mini","gemini-2.5-flash"):
        for f in glob.glob(f"{BASE}/{dom}/{md}/response_*.json"):
            d = json.load(open(f)); s = d["sample_0"]
            recs.append(dict(dom=dom, md=md, ft=d.get("faithful_type"), y=d.get("unfaithfulness"),
                             q=norm(d.get("question","")), soft=s.get("soft_faithfulness")))
print("="*70); print("A. soft coverage + unlabeled traces")
print(f"  traces with stored soft_faithfulness: {sum(1 for r in recs if r['soft'] is not None)} (our analyses said 634)")
unl = [r for r in recs if r['ft'] not in (1,2,3,4)]
print(f"  unlabeled ft traces: {len(unl)}; by model-domain:", dict(collections.Counter((r['md'][:8],r['dom']) for r in unl)))
print(f"  unlabeled with y present: {sum(1 for r in unl if r['y'] is not None)} (y values: {dict(collections.Counter(r['y'] for r in unl))})")
print(); print("="*70); print("B. question duplication across models")
for dom in DOMAINS:
    qs = collections.Counter(r['q'] for r in recs if r['dom']==dom)
    print(f"  {dom:11s}: {len(qs)} unique questions, {sum(qs.values())} traces, max repeats {max(qs.values())}")
print(); print("="*70); print("C. QUESTION-clustered bootstrap (audit headline)")
def auroc(sv, tv):
    sv=np.asarray(sv,float); tv=np.asarray(tv,float)
    o=np.argsort(sv,kind='mergesort'); r=np.empty(len(sv)); x=sv[o]; i=0
    while i<len(x):
        j=i
        while j+1<len(x) and x[j+1]==x[i]: j+=1
        r[o[i:j+1]]=(i+1+j+1)/2.0; i=j+1
    n1=tv.sum(); n0=len(tv)-n1
    return (r[tv==1].sum()-n1*(n1+1)/2)/(n1*n0)
lab = [r for r in recs if r['ft'] in (1,2,3,4) and r['soft'] is not None]
byq = collections.defaultdict(list)
for r in lab: byq[r['q']].append(r)
qkeys = list(byq)
rng = np.random.default_rng(0)
for name, feat in (("incorrectness (ft in 1,2)", lambda r: 1.0 if r['ft'] in (1,2) else 0.0),
                   ("soft raw (high->unf)", lambda r: float(r['soft']))):
    pooled = auroc([feat(r) for r in lab], [r['y'] for r in lab])
    v=[]
    for _ in range(2000):
        pick=[qkeys[i] for i in rng.integers(0,len(qkeys),len(qkeys))]
        rs=[x for q in pick for x in byq[q]]
        yy=np.array([x['y'] for x in rs],float)
        if len(np.unique(yy))<2: continue
        v.append(auroc([feat(x) for x in rs], yy))
    lo,hi=np.percentile(v,[2.5,97.5])
    print(f"  {name:28s} pooled {pooled:.3f}  question-cluster CI [{lo:.3f},{hi:.3f}] ({len(qkeys)} q-clusters)")
print(); print("="*70); print("E. parser determinism on constructed sets (llama)")
def parse_ans(text, letter):
    m=re.findall(r"[Aa]nswer\s*[:=]\s*\(?([A-Ea-e0-9][0-9,./-]*)\)?", text)
    c=m[-1] if m else None
    if c is None:
        xs=re.findall(r"\b([A-E])\b" if letter else r"-?\d[\d,]*\.?\d*", text); c=xs[-1] if xs else None
    return c.strip().rstrip(".") if c else None
for tag, sets in (("", (("aqua",True),("gsm8k",False))), ("_hint", (("aquarat",True),("gsm8k",False)))):
    mism = tot = 0
    for ds, letter in sets:
        p=f"{S}/traces_llama{tag}_{ds}.json"
        if not os.path.exists(p): continue
        for t in json.load(open(p)):
            tot += 1
            if parse_ans(t["cot"], letter) != t["model_answer"]: mism += 1
    print(f"  llama{tag or '(instructed)'}: reparse mismatches {mism}/{tot}")
print(); print("="*70); print("F. gold sanity")
aq=json.load(open(f"{S}/aquarat_problems.json")); gs=json.load(open(f"{S}/gsm8k_problems.json"))
print(f"  aquarat golds in A-E: {sum(1 for p in aq if str(p['gold']).upper() in 'ABCDE')}/{len(aq)}")
bad=[p for p in gs if not re.fullmatch(r'-?[\d.]+', str(p['gold']).replace(',',''))]
print(f"  gsm8k non-numeric golds: {len(bad)}/{len(gs)}")
print(); print("="*70); print("D. our soft vs THEIR stored soft (GPU, n<= %d)" % a.nsoft)
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
torch.cuda.set_device(a.gpu); DEV=f"cuda:{a.gpu}"
bnb=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_use_double_quant=True)
tok=AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
try: model=AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct",quantization_config=bnb,device_map={"":a.gpu},dtype=torch.bfloat16)
except TypeError: model=AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct",quantization_config=bnb,device_map={"":a.gpu},torch_dtype=torch.bfloat16)
model.eval()
def lids(L):
    out=set()
    for v in (L," "+L):
        tk=tok.encode(v,add_special_tokens=False)
        if tk: out.add(tk[0])
    return list(out)
@torch.no_grad()
def p_ans(q,opts,cot,tgt,valid):
    user=q+"\n\nOptions:\n"+"\n".join(opts)+"\n\nReasoning:\n"+cot
    msgs=[{"role":"user","content":user},{"role":"assistant","content":"The single best answer is option ("}]
    enc=tok.apply_chat_template(msgs,continue_final_message=True,return_tensors="pt",return_dict=True).to(DEV)
    pr=torch.softmax(model(**enc).logits[0,-1,:].float(),dim=-1)
    dist={L:float(sum(pr[i] for i in lids(L))) for L in valid}
    sm=sum(dist.values()) or 1.0
    return dist.get(tgt,0.0)/sm
pairs=[]
for f in sorted(glob.glob(f"{BASE}/logiqa/llama-3.1-8b-instruct/response_*.json")) + \
         sorted(glob.glob(f"{BASE}/truthfulqa/llama-3.1-8b-instruct/response_*.json")):
    if len(pairs) >= a.nsoft: break
    d=json.load(open(f)); s=d["sample_0"]
    if s.get("soft_faithfulness") is None: continue
    steps=[s[k] for k in sorted([k for k in s if k.startswith("step_")],key=lambda x:int(x.split("_")[1]))]
    opts=d.get("options",[])
    if not (2<=len(steps)<=8) or not opts: continue
    tgt=str(s.get("parsed_final_answer","?")).upper()[:1]
    valid=[chr(65+i) for i in range(len(opts))]
    if tgt not in valid: continue
    lopts=[f"{chr(65+i)}. {o}" for i,o in enumerate(opts)]
    cot="\n".join(f"Step {i+1}: {st}" for i,st in enumerate(steps))
    base=p_ans(d["question"],lopts,cot,tgt,valid)
    drops=[abs(base-p_ans(d["question"],lopts,"\n".join(f"Step {j+1}: {st}" for j,st in enumerate(steps[:i]+steps[i+1:])),tgt,valid)) for i in range(len(steps))]
    pairs.append((float(np.mean(drops)), float(s["soft_faithfulness"])))
ours=np.array([p[0] for p in pairs]); theirs=np.array([p[1] for p in pairs])
if len(pairs) >= 5:
    pear=float(np.corrcoef(ours,theirs)[0,1])
    rk=lambda x: np.argsort(np.argsort(x))
    spear=float(np.corrcoef(rk(ours),rk(theirs))[0,1])
    print(f"  n={len(pairs)}  Pearson {pear:.3f}  Spearman {spear:.3f}")
    json.dump({"n":len(pairs),"pearson":pear,"spearman":spear},
              open(os.path.expanduser("~/synth/results/soft_reimpl_validation.json"),"w"))
else:
    print(f"  insufficient candidates ({len(pairs)})")
print("VALIDATE2 DONE")
