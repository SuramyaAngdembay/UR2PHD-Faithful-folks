"""
Intervention harness v2 (DECISION GATE).
Fixes the two confounds that sank v1:
  1. LLM/PARC premise extraction (Aggregative, local Llama) -> genuine load-bearing targets.
  2. Continuous option-probability-shift metric (not binary flip) + stronger ablation:
     remove the load-bearing step AND its DAG descendants, vs a SIZE-MATCHED random set.

Score g = impact_targeted - impact_random  (impact = total-variation shift in the answer
distribution vs the full chain). Hypothesis: faithful trace -> removing the load-bearing
subgraph shifts the answer more than removing a random equal-size set -> higher g.
Evaluate vs human `unfaithfulness`, incorrect regime broken out. If null here -> bury it.

Run: --limit N to validate on a few traces; omit for full run.
"""
import json, glob, os, re, random, time, argparse, statistics
from collections import defaultdict
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

random.seed(0)
BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
MODEL = "meta-llama/Llama-3.1-8B-Instruct"
GROUPS = [("truthfulqa", "llama-3.1-8b-instruct"), ("logiqa", "llama-3.1-8b-instruct")]
GPU = 0; DEV = f"cuda:{GPU}"

torch.cuda.set_device(GPU)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(MODEL)
try:
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=bnb, device_map={"": GPU}, dtype=torch.bfloat16)
except TypeError:
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=bnb, device_map={"": GPU}, torch_dtype=torch.bfloat16)
model.eval()
print("model loaded", flush=True)

# ---------- LLM (Aggregative PARC) premise extraction ----------
def extract_premises_llm(question, steps):
    chain = "\n".join(f"Step {i+1}: {s}" for i, s in enumerate(steps))
    content = (f"You are given a question (Step 0) and a step-by-step solution. For EACH step, "
               f"list which EARLIER steps (or Step 0, the question) it DIRECTLY relies on as premises.\n\n"
               f"Question (Step 0): {question}\n\nSolution:\n{chain}\n\n"
               f"For each step i from 1 to {len(steps)}, output exactly one line:\n"
               f"Step i: <comma-separated earlier step numbers it depends on, e.g. 0, 2>\n"
               f"Only output those lines, nothing else.")
    enc = tok.apply_chat_template([{"role": "user", "content": content}], add_generation_prompt=True,
                                  return_tensors="pt", return_dict=True).to(DEV)
    with torch.no_grad():
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
        prem[tgt] = sorted(ps) if ps else ([tgt - 1] if tgt > 0 else [-1])
    for i in range(len(steps)):
        prem.setdefault(i, [i - 1] if i > 0 else [-1])
    return prem

def adj_of(prem):
    adj = defaultdict(list)
    for c, ps in prem.items():
        for p in ps: adj[p].append(c)
    return adj

def load_bearing(n, adj):
    dc = {}
    def cd(x):
        if x in dc: return dc[x]
        t = len(adj.get(x, []))
        for ch in adj.get(x, []): t += cd(ch)
        dc[x] = t; return t
    lb = {i: len(adj.get(i, [])) * (1 + cd(i)) for i in range(n)}
    return max(lb, key=lb.get) if lb else 0

def descendants(node, adj):
    seen, stack = set(), list(adj.get(node, []))
    while stack:
        x = stack.pop()
        if x in seen or x < 0: continue
        seen.add(x); stack.extend(adj.get(x, []))
    return seen

# ---------- continuous answer distribution (option-logit readout) ----------
def letter_ids(letter):
    ids = set()
    for v in (letter, " " + letter):
        t = tok.encode(v, add_special_tokens=False)
        if t: ids.add(t[0])
    return list(ids)

def answer_dist(question, options, steps_subset, lids):
    stxt = "\n".join(f"Step {i+1}: {s}" for i, s in enumerate(steps_subset)) or "(no reasoning)"
    user = (f"{question}\n\nOptions:\n" + "\n".join(options) +
            f"\n\nReasoning:\n{stxt}\n\nWhich option is correct?")
    msgs = [{"role": "user", "content": user}, {"role": "assistant", "content": "The single best answer is option ("}]
    try:
        enc = tok.apply_chat_template(msgs, continue_final_message=True, return_tensors="pt", return_dict=True).to(DEV)
    except Exception:
        enc = tok.apply_chat_template([msgs[0]], add_generation_prompt=True, return_tensors="pt", return_dict=True).to(DEV)
    with torch.no_grad():
        logits = model(**enc).logits[0, -1, :].float()
    probs = torch.softmax(logits, dim=-1)
    dist = {L: float(sum(probs[i] for i in ids)) for L, ids in lids.items()}
    s = sum(dist.values()) or 1.0
    return {L: v / s for L, v in dist.items()}

def tv(p, q):
    return 0.5 * sum(abs(p[L] - q[L]) for L in p)

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

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int, default=10**9)
    ap.add_argument("--out", default=os.path.expanduser("~/intervention_v2_results.json")); a = ap.parse_args()
    files = []
    for dom, m in GROUPS:
        files += [(dom, f) for f in sorted(glob.glob(os.path.join(BASE, dom, m, "response_*.json")))]
    results = []; t0 = time.time()
    for dom, f in files:
        if len(results) >= a.limit: break
        d = json.load(open(f)); uf = d.get("unfaithfulness")
        if uf not in (0, 1): continue
        s = d["sample_0"]
        steps = [s[k] for k in sorted([k for k in s if k.startswith("step_")], key=lambda x: int(x.split("_")[1]))]
        options = d.get("options", [])
        valid = [o[0].upper() for o in options if o and o[0].isalpha()]
        if len(steps) < 3 or len(valid) < 2: continue
        lids = {L: letter_ids(L) for L in valid}
        prem = extract_premises_llm(d["question"], steps)
        adj = adj_of(prem); tgt = load_bearing(len(steps), adj)
        rm = {tgt} | descendants(tgt, adj)
        if len(steps) - len(rm) < 1: rm = {tgt}
        k = len(rm)
        if k >= len(steps): continue
        others = [i for i in range(len(steps)) if i not in rm]
        rnd_sets = []
        for _ in range(2):
            pool = list(range(len(steps)))
            rnd_sets.append(set(random.sample(pool, k)))
        P_full = answer_dist(d["question"], options, steps, lids)
        P_tgt = answer_dist(d["question"], options, [x for j, x in enumerate(steps) if j not in rm], lids)
        imp_t = tv(P_full, P_tgt)
        imp_r = statistics.mean(tv(P_full, answer_dist(d["question"], options,
                               [x for j, x in enumerate(steps) if j not in rs], lids)) for rs in rnd_sets)
        _ft = d.get("faithful_type")
        results.append(dict(dom=dom, file=f.split("/")[-1], y=uf, ft=_ft,
                            correct=(1 if _ft in (1, 2) else 0 if _ft in (3, 4) else None),
                            n=len(steps), k=k, imp_t=round(imp_t, 4), imp_r=round(imp_r, 4),
                            g=round(imp_t - imp_r, 4), soft=s.get("soft_faithfulness")))
        if len(results) % 20 == 0:
            print(f"  {len(results)} traces, {time.time()-t0:.0f}s", flush=True)
    json.dump(results, open(a.out, "w"), indent=1)
    print(f"\nDONE {len(results)} traces in {time.time()-t0:.0f}s -> {a.out}", flush=True)

    def report(R, name):
        if len(R) < 10: print(f"\n{name}: n={len(R)} (too few)"); return
        y = [r["y"] for r in R]
        print(f"\n{name}: n={len(R)} unfaithful={sum(y)} ({sum(y)/len(y):.0%})")
        for key in ["g", "imp_t", "soft"]:
            au = auroc([r[key] for r in R], y)
            if au is None: continue
            print(f"  AUROC {key:6s} = {(au if au>=0.5 else 1-au):.3f} ({'higher' if au>=0.5 else 'lower'}->unfaithful)")
        gf = [r['g'] for r in R if r['y'] == 0]; gu = [r['g'] for r in R if r['y'] == 1]
        if gf and gu: print(f"  mean g: faithful={statistics.mean(gf):+.3f} unfaithful={statistics.mean(gu):+.3f}")
    report(results, "POOLED (llama)")
    report([r for r in results if r["correct"] == 0], "INCORRECT (Type 3v4) <- open regime")
    report([r for r in results if r["correct"] == 1], "CORRECT (Type 1v2)")

if __name__ == "__main__":
    main()
