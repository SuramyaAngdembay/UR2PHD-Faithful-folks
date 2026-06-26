"""Honest, NON-circular baseline: do the computed answer-tracing metrics
(soft/hard faithfulness, and Dikshant's avg_impact) actually predict the
HUMAN `unfaithfulness` label? Run on Aquaman over the extracted FINE-CoT data."""
import json, glob, os, statistics

BASE = "/tmp/fc/faithcot"
GROUPS = [("truthfulqa", "llama-3.1-8b-instruct"), ("truthfulqa", "Qwen2.5-7B-Instruct"),
          ("logiqa", "llama-3.1-8b-instruct"), ("logiqa", "Qwen2.5-7B-Instruct")]

def avg_impact(sample):
    probs = sample.get("intermediate_answer_probabilities") or []
    sh = []
    for i in range(1, len(probs)):
        a, b = probs[i-1], probs[i]
        if not a or not b:
            continue
        keys = set(a) | set(b)
        sh.append(sum(abs(a.get(k, 0) - b.get(k, 0)) for k in keys))
    return sum(sh)/len(sh) if sh else None

def auroc(scores, labels):
    """AUROC that higher score -> positive(label==1). Tie-aware (avg ranks)."""
    n = len(scores); npos = sum(labels); nneg = n - npos
    if npos == 0 or nneg == 0:
        return None
    order = sorted(range(n), key=lambda i: scores[i])
    ranks = [0.0]*n; i = 0
    while i < n:
        j = i
        while j+1 < n and scores[order[j+1]] == scores[order[i]]:
            j += 1
        r = (i+j)/2.0 + 1
        for k in range(i, j+1):
            ranks[order[k]] = r
        i = j+1
    sumpos = sum(ranks[i] for i in range(n) if labels[i] == 1)
    return (sumpos - npos*(npos+1)/2) / (npos*nneg)

rows = []
for dom, m in GROUPS:
    for f in glob.glob(os.path.join(BASE, dom, m, "response_*.json")):
        d = json.load(open(f)); uf = d.get("unfaithfulness")
        if uf not in (0, 1):
            continue
        s = d.get("sample_0", {})
        rows.append(dict(dom=dom, m=m, y=uf, soft=s.get("soft_faithfulness"),
                         hard=s.get("hard_faithfulness"), imp=avg_impact(s),
                         correct=1 if s.get("parsed_final_answer") == d.get("label") else 0))

def col(R, k): return [r[k] for r in R]

def run(R, name):
    R = [r for r in R if r["soft"] is not None and r["imp"] is not None]
    if not R:
        print(f"\n{name}: no data"); return
    y = [r["y"] for r in R]
    print(f"\n{name}: n={len(R)}  unfaithful={sum(y)} ({sum(y)/len(y):.0%})")
    for lbl, scores in [("soft_faith", col(R, "soft")), ("hard_faith", col(R, "hard")),
                        ("avg_impact", col(R, "imp")), ("correct", col(R, "correct"))]:
        a = auroc(scores, y)
        disp = a if a >= 0.5 else 1 - a
        dirn = "higher->unfaithful" if a >= 0.5 else "lower->unfaithful"
        print(f"  AUROC {lbl:11s} = {disp:.3f}  ({dirn})")
    uf_soft = [r["soft"] for r in R if r["y"] == 1]
    f_soft = [r["soft"] for r in R if r["y"] == 0]
    print(f"  soft_faith mean: faithful={statistics.mean(f_soft):.3f}  unfaithful={statistics.mean(uf_soft):.3f}")

run(rows, "POOLED (4 groups)")
for dom, m in GROUPS:
    run([r for r in rows if r["dom"] == dom and r["m"] == m], f"{dom}/{m}")
