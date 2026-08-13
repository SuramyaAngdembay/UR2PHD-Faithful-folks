"""
Our pipeline v1 (OBSERVATIONAL): does premise-DAG structure predict the HUMAN
`unfaithfulness` label, and does it add anything BEYOND answer correctness?
No counterfactual re-runs yet. Heuristic premise extraction (modular: the
extract_premises() function is the single thing we swap for LLM extraction later).
Controls for correctness via stratified AUROC + partial Spearman.
"""
import json, glob, os, re, math, argparse, statistics
from collections import defaultdict
from scipy.stats import spearmanr

# ---------- premise extraction (heuristic; replaceable with LLM) ----------
def extract_premises(steps):
    prem = {}
    for i, step in enumerate(steps):
        sl = step.lower(); s = set()
        for m in re.findall(r'step\s*(\d+)', sl):
            j = int(m) - 1
            if 0 <= j < i: s.add(j)
        if i > 0 and any(c in sl for c in ['therefore','thus','hence','so,','because',
                         'this means','it follows','the answer','consequently']):
            s.add(i - 1)
        pn = set(re.findall(r'\b[A-Z][a-z]+\b', step)); nm = set(re.findall(r'\b\d+\.?\d*\b', step))
        for j in range(i):
            ej = set(re.findall(r'\b[A-Z][a-z]+\b', steps[j])); nj = set(re.findall(r'\b\d+\.?\d*\b', steps[j]))
            if len(pn & ej) >= 2 or len(nm & nj) >= 2: s.add(j)
        if not s and i > 0: s.add(i - 1)
        if i == 0: s.add(-1)
        prem[i] = sorted(s)
    return prem

# ---------- DAG structural features ----------
def dag_features(n, prem):
    adj = defaultdict(list)
    for c, ps in prem.items():
        for p in ps: adj[p].append(c)
    desc = {}
    def cd(x):
        if x in desc: return desc[x]
        t = len(adj.get(x, []))
        for ch in adj.get(x, []): t += cd(ch)
        desc[x] = t; return t
    for i in range(-1, n): cd(i)
    indeg = {i: len(prem.get(i, [])) for i in range(n)}
    outdeg = {i: len(adj.get(i, [])) for i in range(-1, n)}
    lb = {i: outdeg.get(i, 0) * (1 + desc.get(i, 0)) for i in range(n)}
    lin = sum(1 for i in range(1, n) if prem.get(i, []) == [i - 1]) / max(n - 1, 1)
    dcache = {}
    def dep(x):
        if x in dcache: return dcache[x]
        ch = adj.get(x, [])
        d = 0 if not ch else 1 + max(dep(c) for c in ch)
        dcache[x] = d; return d
    depth = dep(-1) if -1 in adj else 0
    return dict(n_steps=n, linearity=round(lin, 3), depth=depth,
                avg_in=round(statistics.mean(indeg.values()), 3) if indeg else 0,
                avg_out=round(statistics.mean([outdeg[i] for i in range(n)]), 3) if n else 0,
                max_lb=max(lb.values()) if lb else 0)

def avg_impact(sample):
    probs = sample.get("intermediate_answer_probabilities") or []
    sh = []
    for i in range(1, len(probs)):
        a, b = probs[i - 1], probs[i]
        if a and b:
            ks = set(a) | set(b); sh.append(sum(abs(a.get(k, 0) - b.get(k, 0)) for k in ks))
    return sum(sh) / len(sh) if sh else None

# ---------- stats ----------
def auroc(scores, labels):
    n = len(scores); npos = sum(labels); nneg = n - npos
    if npos == 0 or nneg == 0: return None
    order = sorted(range(n), key=lambda i: scores[i]); ranks = [0.0] * n; i = 0
    while i < n:
        j = i
        while j + 1 < n and scores[order[j + 1]] == scores[order[i]]: j += 1
        r = (i + j) / 2.0 + 1
        for k in range(i, j + 1): ranks[order[k]] = r
        i = j + 1
    sp = sum(ranks[i] for i in range(n) if labels[i] == 1)
    return (sp - npos * (npos + 1) / 2) / (npos * nneg)

def sp(x, y):
    r = spearmanr(x, y).correlation
    return r if r == r else 0.0

def partial_spear(x, y, z):
    rxy, rxz, ryz = sp(x, y), sp(x, z), sp(y, z)
    d = math.sqrt(max((1 - rxz ** 2) * (1 - ryz ** 2), 1e-9))
    return (rxy - rxz * ryz) / d

GROUPS = [("truthfulqa", "llama-3.1-8b-instruct"), ("truthfulqa", "Qwen2.5-7B-Instruct"),
          ("logiqa", "llama-3.1-8b-instruct"), ("logiqa", "Qwen2.5-7B-Instruct")]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--base", required=True); a = ap.parse_args()
    rows = []
    for dom, m in GROUPS:
        for f in glob.glob(os.path.join(a.base, dom, m, "response_*.json")):
            d = json.load(open(f)); uf = d.get("unfaithfulness")
            if uf not in (0, 1): continue
            s = d.get("sample_0", {})
            steps = [s[k] for k in sorted([k for k in s if k.startswith("step_")],
                                          key=lambda x: int(x.split("_")[1]))]
            if len(steps) < 2: continue
            fe = dag_features(len(steps), extract_premises(steps))
            rows.append(dict(y=uf, correct=1 if s.get("parsed_final_answer") == d.get("label") else 0,
                             soft=s.get("soft_faithfulness"), imp=avg_impact(s), **fe))
    R = [r for r in rows if r["imp"] is not None and r["soft"] is not None]
    y = [r["y"] for r in R]; cor = [r["correct"] for r in R]
    print(f"n={len(R)}  unfaithful={sum(y)} ({sum(y)/len(y):.0%})  correct={sum(cor)} ({sum(cor)/len(R):.0%})")
    Rc = [r for r in R if r["correct"] == 1]; Ri = [r for r in R if r["correct"] == 0]
    print(f"  (correct subset n={len(Rc)}, incorrect subset n={len(Ri)})")
    feats = ["correct", "soft", "imp", "linearity", "depth", "avg_in", "avg_out", "max_lb", "n_steps"]
    def o(v): return None if v is None else (v if v >= 0.5 else 1 - v)
    def fmt(v): return "  -  " if v is None else f"{v:.3f}"
    print(f"\n{'feature':10s} {'AUROC':>7s} {'AUROC|cor':>10s} {'AUROC|inc':>10s} {'pSpear|cor':>11s}")
    for k in feats:
        sc = [r[k] for r in R]
        a_all = o(auroc(sc, y))
        a_c = o(auroc([r[k] for r in Rc], [r["y"] for r in Rc]))
        a_i = o(auroc([r[k] for r in Ri], [r["y"] for r in Ri]))
        ps = partial_spear(sc, y, cor)
        print(f"{k:10s} {fmt(a_all):>7s} {fmt(a_c):>10s} {fmt(a_i):>10s} {ps:>+11.3f}")
    print("\nAUROC oriented >=0.5. AUROC|cor / AUROC|inc control for correctness by stratifying.")
    print("pSpear|cor = partial Spearman(feature, unfaithful | correct). Heuristic DAG (crude):")
    print("DAG feature >0.5 within strata / nonzero partial => signal beyond correctness => pursue LLM extraction + interventions.")

if __name__ == "__main__":
    main()
