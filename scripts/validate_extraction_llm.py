"""
Validate the LLM (Aggregative, PARC-style) premise extractor -- the one used by intervention
v2 -- against PERL gold premise links. This licenses the v2 decision-gate claim ("targets were
genuinely load-bearing"). Same extraction prompt/parse as intervention_harness_v2.py.
Compares micro precision/recall/F1 vs gold (heuristic was P0.56/R0.58/F1 0.57).
"""
import json, glob, os, re, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

BASE = os.path.expanduser("~/ur2phd/upstream/PARC/datasets")
MODEL = "meta-llama/Llama-3.1-8B-Instruct"; GPU = 0; DEV = f"cuda:{GPU}"
CAP_PER_DS = 40  # sample per math dataset for tractability

torch.cuda.set_device(GPU)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(MODEL)
try:
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=bnb, device_map={"": GPU}, dtype=torch.bfloat16)
except TypeError:
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=bnb, device_map={"": GPU}, torch_dtype=torch.bfloat16)
model.eval(); print("model loaded", flush=True)

def strip_prefix(s): return re.sub(r'^\s*Step\s*\d+\s*:\s*', '', s)

@torch.no_grad()
def extract_llm(question, steps):
    steps = [strip_prefix(s) for s in steps]
    chain = "\n".join(f"Step {i+1}: {s}" for i, s in enumerate(steps))
    content = (f"You are given a question (Step 0) and a step-by-step solution. For EACH step, list "
               f"which EARLIER steps (or Step 0, the question) it DIRECTLY relies on as premises.\n\n"
               f"Question (Step 0): {question}\n\nSolution:\n{chain}\n\n"
               f"For each step i from 1 to {len(steps)}, output exactly one line:\n"
               f"Step i: <comma-separated earlier step numbers, e.g. 0, 2>\nOnly output those lines.")
    enc = tok.apply_chat_template([{"role": "user", "content": content}], add_generation_prompt=True,
                                  return_tensors="pt", return_dict=True).to(DEV)
    out = model.generate(**enc, max_new_tokens=220, do_sample=False)
    txt = tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
    prem = {}
    for line in txt.splitlines():
        mm = re.match(r'\s*Step\s+(\d+)\s*:\s*(.*)', line, re.I)
        if not mm: continue
        tgt = int(mm.group(1)) - 1
        if not (0 <= tgt < len(steps)): continue
        ps = set()
        for r in re.findall(r'\d+', mm.group(2)):
            r = int(r)
            if r == 0: ps.add(-1)
            elif 1 <= r and (r - 1) < tgt: ps.add(r - 1)
        prem[tgt] = ps
    return prem

def gold_premises(rec):
    out = {}
    for s in rec["premise_annotation"]["steps"]:
        sn = s["step_number"]
        if sn == 0: continue
        g = set()
        for p in s.get("premises", []):
            pn = p[0] if isinstance(p, list) else p
            if pn == 0: g.add(-1)
            elif isinstance(pn, int) and pn >= 1: g.add(pn - 1)
        out[sn - 1] = g
    return out

tp = fp = fn = 0; nrec = 0; nsteps = 0; t0 = time.time()
for ds in ["gsm8k", "math", "metamathqa", "orca_math"]:
    cnt = 0
    for f in sorted(glob.glob(os.path.join(BASE, ds, "*positives.json"))):
        if cnt >= CAP_PER_DS: break
        for rec in json.load(open(f)):
            if cnt >= CAP_PER_DS: break
            if "premise_annotation" not in rec or "steps" not in rec: continue
            try:
                pred = extract_llm(rec.get("question", ""), rec["steps"])
            except Exception as e:
                print("  extract error:", str(e)[:80], flush=True); continue
            gold = gold_premises(rec); cnt += 1; nrec += 1
            for tgt, g in gold.items():
                if tgt not in pred or not g: continue
                p = pred[tgt]; tp += len(p & g); fp += len(p - g); fn += len(g - p); nsteps += 1
            if nrec % 20 == 0: print(f"  {nrec} recs, {time.time()-t0:.0f}s", flush=True)
prec = tp / (tp + fp) if tp + fp else 0.0
rec_ = tp / (tp + fn) if tp + fn else 0.0
f1 = 2 * prec * rec_ / (prec + rec_) if prec + rec_ else 0.0
print(f"\nLLM-extractor PERL validation: recs={nrec} steps={nsteps} ({time.time()-t0:.0f}s)")
print(f"  premise-link  precision={prec:.3f}  recall={rec_:.3f}  F1={f1:.3f}")
print(f"  (heuristic: P0.56/R0.58/F1 0.57; PARC report ~>=0.90 recall for LLM extraction)")
