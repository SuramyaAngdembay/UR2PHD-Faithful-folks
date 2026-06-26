"""
Validate our premise extractor against PERL gold premise links (PARC datasets/).
Micro precision/recall/F1 of predicted premise links vs gold, on math reasoning chains
(the only gold-premise data available). Addresses the reviewer concern "was the extractor
good enough that the DAG null is meaningful?". This validates the HEURISTIC extractor
(used in the structural + v1 tests); the LLM Aggregative extractor (used in v2) is validated
separately on GPU.
"""
import json, glob, os, re
from collections import defaultdict

BASE = os.path.expanduser("~/ur2phd/upstream/PARC/datasets")

def extract_premises(steps):  # identical heuristic to dag_faithfulness / rigorous_analysis
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
            if len(pn & set(re.findall(r'\b[A-Z][a-z]+\b', steps[j]))) >= 2 or len(nm & set(re.findall(r'\b\d+\.?\d*\b', steps[j]))) >= 2:
                s.add(j)
        if not s and i > 0: s.add(i - 1)
        if i == 0: s.add(-1)
        prem[i] = sorted(s)
    return prem

def gold_premises(rec):
    out = {}
    for s in rec["premise_annotation"]["steps"]:
        sn = s["step_number"]
        if sn == 0: continue          # the question as a target -> skip
        g = set()
        for p in s.get("premises", []):
            pn = p[0] if isinstance(p, list) else p
            if pn == 0: g.add(-1)      # question
            elif isinstance(pn, int) and pn >= 1: g.add(pn - 1)
        out[sn - 1] = g                # our 0-based step index
    return out

files = []
for ds in ["gsm8k", "math", "metamathqa", "orca_math"]:
    files += sorted(glob.glob(os.path.join(BASE, ds, "*positives.json")))

tp = fp = fn = 0; nrec = 0; nsteps = 0; exact = 0
for f in files:
    try: data = json.load(open(f))
    except Exception: continue
    for rec in data:
        if "premise_annotation" not in rec or "steps" not in rec: continue
        pred = extract_premises(rec["steps"]); gold = gold_premises(rec)
        nrec += 1
        for tgt, g in gold.items():
            if tgt not in pred or not g: continue
            p = set(pred[tgt])
            tp += len(p & g); fp += len(p - g); fn += len(g - p)
            nsteps += 1
            if p == g: exact += 1

prec = tp / (tp + fp) if tp + fp else 0.0
rec_ = tp / (tp + fn) if tp + fn else 0.0
f1 = 2 * prec * rec_ / (prec + rec_) if prec + rec_ else 0.0
print("PERL gold premise-link validation — HEURISTIC extractor")
print(f"  files={len(files)}  records={nrec}  scored_steps={nsteps}")
print(f"  premise-link  precision={prec:.3f}  recall={rec_:.3f}  F1={f1:.3f}")
print(f"  exact-premise-set match per step = {exact/nsteps:.3f}" if nsteps else "  no steps")
print("  (PARC report ~>=0.90 recall for LLM extraction; heuristic expected lower ->")
print("   motivates LLM extraction for the 'fair' intervention test, which v2 used.)")
