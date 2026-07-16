"""Pre-submission DATA validation battery. Checks that could invalidate experiments:
 1 census vs FaithCoT paper anchors (>1000 traces, >300 unfaithful, 4x4)
 2 ft vs ACTUAL correctness (does ft1/2 => parsed==gold hold? our 'correct regime' depends on it)
 3 y (binary unfaithfulness) vs ft mapping consistency
 4 step-field integrity; options format per domain
 5 QUESTION OVERLAP: FaithCoT-aqua vs our hint-aquarat / synthetic-aqua / gsm8k (bridge validity!)
 6 our construction recounts vs paper numbers
 7 (GPU) our step-removal soft reimplementation vs FaithCoT's stored soft_faithfulness
Usage: python validate_data.py --gpu 0 [--nsoft 40]"""
import argparse, glob, json, os, re
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--gpu", type=int, default=0); ap.add_argument("--nsoft", type=int, default=40)
a = ap.parse_args()
BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
DOMAINS = ["truthfulqa", "logiqa", "aqua", "HLE_BIO"]
MDIRS = ["llama-3.1-8b-instruct", "Qwen2.5-7B-Instruct", "gpt-4o-mini", "gemini-2.5-flash"]
def norm(q): return re.sub(r"\s+", " ", q.strip().lower())[:200]
rows = []
for dom in DOMAINS:
    for md in MDIRS:
        for f in glob.glob(os.path.join(BASE, dom, md, "response_*.json")):
            d = json.load(open(f)); s = d.get("sample_0", {})
            steps = sorted([k for k in s if k.startswith("step_")], key=lambda x: int(x.split("_")[1]))
            rows.append(dict(dom=dom, md=md, ft=d.get("faithful_type"), y=d.get("unfaithfulness"),
                             q=d.get("question",""), label=str(d.get("label")), 
                             parsed=str(s.get("parsed_final_answer")), nsteps=len(steps),
                             step_ok=all(s.get(k) for k in steps) and [int(k.split("_")[1]) for k in steps]==list(range(1,len(steps)+1)),
                             opts=d.get("options", [])))
print("="*70); print("1. CENSUS")
print(f"total traces: {len(rows)} (paper: 'over 1,000'; our analyses used 1,304)")
print(f"unfaithful (y=1): {sum(1 for r in rows if r['y']==1)} (paper: 'more than 300')")
import collections
print("per model x domain:")
for md in MDIRS:
    cnts = [sum(1 for r in rows if r['md']==md and r['dom']==d) for d in DOMAINS]
    print(f"  {md:24s} " + " ".join(f"{d}:{c}" for d,c in zip(DOMAINS,cnts)))
print("ft distribution:", dict(collections.Counter(r['ft'] for r in rows)))
print(); print("="*70); print("2. ft vs ACTUAL correctness (parsed==label)")
ct = collections.Counter((r['ft'], r['parsed'].upper()[:1]==r['label'].upper()[:1]) for r in rows if r['ft'] in (1,2,3,4))
for ft in (1,2,3,4):
    c, w = ct.get((ft,True),0), ct.get((ft,False),0)
    print(f"  ft{ft}: actually-correct {c:4d}  actually-wrong {w:4d}  ({c/(c+w):.0%} correct)" if c+w else f"  ft{ft}: none")
print(); print("="*70); print("3. y vs ft mapping")
ct2 = collections.Counter((r['ft'], r['y']) for r in rows if r['ft'] in (1,2,3,4))
print("  crosstab (ft,y):", dict(ct2))
print(); print("="*70); print("4. step integrity + options format")
bad = sum(1 for r in rows if not r['step_ok'])
print(f"  traces with broken/empty/non-contiguous steps: {bad}")
for dom in DOMAINS:
    ex = next(r for r in rows if r['dom']==dom and r['opts'])
    letter = sum(1 for r in rows if r['dom']==dom and r['opts'] and r['opts'][0] and str(r['opts'][0])[0].isalpha())
    tot = sum(1 for r in rows if r['dom']==dom and r['opts'])
    print(f"  {dom:11s} letter-prefixed options: {letter}/{tot}   e.g. {ex['opts'][:2]}")
print(); print("="*70); print("5. QUESTION OVERLAP (bridge validity)")
fc_aqua = {norm(r['q']) for r in rows if r['dom']=='aqua'}
S = os.path.expanduser("~/synth")
def qs(path): return {norm(t['question']) for t in json.load(open(path))} if os.path.exists(path) else set()
for name, p in [("hint aquarat (llama)", f"{S}/traces_llama_hint_aquarat.json"),
                ("hint gsm8k (llama)", f"{S}/traces_llama_hint_gsm8k.json"),
                ("synthetic aqua (llama)", f"{S}/traces_llama_aqua.json"),
                ("synthetic gsm8k (llama)", f"{S}/traces_llama_gsm8k.json")]:
    q = qs(p)
    ov = len(q & fc_aqua)
    print(f"  {name:24s} n_q={len(q):4d}  overlap with FaithCoT-aqua: {ov}")
print(); print("="*70); print("6. CONSTRUCTION RECOUNTS")
for m in ("llama","qwen"):
    for tag, sets in (("", ("aqua","gsm8k")), ("_hint", ("aquarat","gsm8k"))):
        tot_g = tot_p = 0
        for ds in sets:
            p = f"{S}/traces_{m}{tag}_{ds}.json"
            if not os.path.exists(p): continue
            tr = json.load(open(p))
            tot_g += sum(1 for t in tr if t['condition']=='genuine'); tot_p += sum(1 for t in tr if t['condition']=='posthoc')
        print(f"  {m}{tag or '(instructed)'}: genuine {tot_g}, posthoc {tot_p}")
print(); print("="*70); print("7. SOFT REIMPLEMENTATION vs STORED soft_faithfulness (GPU)")
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
torch.cuda.set_device(a.gpu); DEV=f"cuda:{a.gpu}"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
try: model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct", quantization_config=bnb, device_map={"": a.gpu}, dtype=torch.bfloat16)
except TypeError: model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct", quantization_config=bnb, device_map={"": a.gpu}, torch_dtype=torch.bfloat16)
model.eval()
def letter_ids(L):
    ids=set()
    for v in (L," "+L):
        tks=tok.encode(v, add_special_tokens=False)
        if tks: ids.add(tks[0])
    return list(ids)
@torch.no_grad()
def p_ans(q, opts, cot, tgt, valid):
    user=q+"\n\nOptions:\n"+"\n".join(opts)+"\n\nReasoning:\n"+cot
    msgs=[{"role":"user","content":user},{"role":"assistant","content":"The single best answer is option ("}]
    enc=tok.apply_chat_template(msgs, continue_final_message=True, return_tensors="pt", return_dict=True).to(DEV)
    pr=torch.softmax(model(**enc).logits[0,-1,:].float(),dim=-1)
    dist={L:float(sum(pr[i] for i in letter_ids(L))) for L in valid}
    s=sum(dist.values()) or 1.0
    return dist.get(tgt,0.0)/s
pairs=[]
cands=[]
for dom in ("truthfulqa","logiqa"):
    for f in sorted(glob.glob(os.path.join(BASE,dom,"llama-3.1-8b-instruct","response_*.json"))):
        d=json.load(open(f)); s=d["sample_0"]
        if d.get("soft_faithfulness") is None: continue
        opts=d.get("options",[])
        if not opts or not str(opts[0])[0].isalpha(): continue
        steps=[s[k] for k in sorted([k for k in s if k.startswith("step_")], key=lambda x:int(x.split("_")[1]))]
        if not (2<=len(steps)<=10): continue
        tgt=str(s.get("parsed_final_answer","?")).upper()[:1]
        valid=[str(o)[0].upper() for o in opts]
        if tgt not in valid: continue
        cands.append((d,steps,tgt,valid))
print(f"  candidate traces with stored soft + letter options: {len(cands)}; using {min(a.nsoft,len(cands))}")
for d,steps,tgt,valid in cands[:a.nsoft]:
    q=d["question"]; opts=d["options"]
    cot="\n".join(f"Step {i+1}: {st}" for i,st in enumerate(steps))
    base=p_ans(q,opts,cot,tgt,valid)
    drops=[]
    for i in range(len(steps)):
        red="\n".join(f"Step {j+1}: {st}" for j,st in enumerate(steps[:i]+steps[i+1:]))
        drops.append(abs(base-p_ans(q,opts,red,tgt,valid)))
    pairs.append((float(np.mean(drops)), float(d["soft_faithfulness"])))
ours=np.array([p[0] for p in pairs]); theirs=np.array([p[1] for p in pairs])
pear=float(np.corrcoef(ours,theirs)[0,1])
def rank(x):
    o=np.argsort(x); r=np.empty(len(x)); r[o]=np.arange(len(x)); return r
spear=float(np.corrcoef(rank(ours),rank(theirs))[0,1])
print(f"  our-soft vs stored-soft: Pearson {pear:.3f}  Spearman {spear:.3f}  (n={len(pairs)})")
json.dump({"n":len(pairs),"pearson":pear,"spearman":spear,
           "pairs":[[float(a_),float(b_)] for a_,b_ in pairs]},
          open(os.path.expanduser("~/synth/results/soft_reimpl_validation.json"),"w"))
print("VALIDATE_DATA DONE")
