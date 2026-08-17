"""
Temper-patch computations (post red-team). All from cached judge scores + release.
 (1) Judge AUROC per domain x regime; pooled vs prevalence-weighted within-model mean.
 (2) Parseable-only pooled incorrect-regime judge AUROC + is-parseable baseline.
 (3) Degradation delta excluding HLE-Bio, and domain-matched (common-mix reweight).
 (4) Question-clustered bootstrap CIs for pooled judge numbers + benchmark-wide NLI.
 (5) Judge score histogram.
Output: ~/synth/results/temper_patch.json
"""
import json, glob, os, hashlib
from collections import Counter
import numpy as np

BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
RAW = os.path.expanduser("~/synth/results/judge_raw.jsonl")
OUT = os.path.expanduser("~/synth/results/temper_patch.json")

js = {}
for line in open(RAW):
    d = json.loads(line); js[d["rid"]] = d["score"]

rows = []
for f in sorted(glob.glob(BASE + "/*/*/response_*.json")):
    d = json.load(open(f)); ft = int(d.get("faithful_type", 0) or 0)
    if ft not in (1, 2, 3, 4): continue
    dom, mdl = f.split("/")[-3], f.split("/")[-2]
    rid = f"{dom}/{mdl}/{os.path.basename(f)}"
    if rid not in js: continue
    s = d["sample_0"]
    parsed = str(s.get("parsed_final_answer", "")).strip()
    steps = [k for k in s if k.startswith("step_")]
    rows.append(dict(ft=ft, unf=int(d["unfaithfulness"]), dom=dom, mdl=mdl,
                     q=hashlib.md5(d["question"].encode()).hexdigest(),
                     parseable=int(bool(parsed)), n_steps=len(steps),
                     nli=None, score=js[rid]))
print(f"rows: {len(rows)}")

def auroc(y, s):
    y, s = np.asarray(y, float), np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    if not len(pos) or not len(neg): return None
    return float((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())

rng = np.random.default_rng(0)
def ci_trace(y, s, B=3000):
    y, s = np.asarray(y, float), np.asarray(s, float); v = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i])) == 2: v.append(auroc(y[i], s[i]))
    return [round(float(q), 3) for q in np.percentile(v, [2.5, 97.5])]

def ci_cluster(rr, ykey, B=3000):
    """bootstrap over question clusters"""
    qs = {}
    for r in rr: qs.setdefault(r["q"], []).append(r)
    keys = list(qs.keys()); v = []
    for _ in range(B):
        idx = rng.integers(0, len(keys), len(keys))
        samp = [r for i in idx for r in qs[keys[i]]]
        y = [ykey(r) for r in samp]; s = [r["score"] for r in samp]
        if len(set(y)) == 2: v.append(auroc(y, s))
    return [round(float(q), 3) for q in np.percentile(v, [2.5, 97.5])]

res = {}
inc = [r for r in rows if r["ft"] in (1, 2)]; cor = [r for r in rows if r["ft"] in (3, 4)]
yi = lambda r: int(r["ft"] == 2); yc = lambda r: int(r["ft"] == 4)

# (1) per domain x regime
res["per_domain"] = {}
for dom in sorted(set(r["dom"] for r in rows)):
    di = [r for r in inc if r["dom"] == dom]; dc = [r for r in cor if r["dom"] == dom]
    res["per_domain"][dom] = {
        "incorrect": {"n": len(di), "auroc": round(auroc([yi(r) for r in di], [r["score"] for r in di]), 3) if len(di) > 5 else None},
        "correct": {"n": len(dc), "auroc": round(auroc([yc(r) for r in dc], [r["score"] for r in dc]), 3) if len(dc) > 5 else None}}
# pooled vs within-model prevalence-weighted mean (incorrect regime)
per_m = {}
for m in sorted(set(r["mdl"] for r in inc)):
    mi = [r for r in inc if r["mdl"] == m]
    per_m[m] = {"n": len(mi), "auroc": round(auroc([yi(r) for r in mi], [r["score"] for r in mi]), 3)}
w = np.array([per_m[m]["n"] for m in per_m], float)
res["incorrect_within_model"] = {"per_model": per_m,
    "n_weighted_mean": round(float(sum(per_m[m]["auroc"] * per_m[m]["n"] for m in per_m) / w.sum()), 3)}

# (2) parseable-only + is-parseable baseline (incorrect regime)
pi = [r for r in inc if r["parseable"]]
res["incorrect_parseable_only"] = {"n": len(pi),
    "auroc": round(auroc([yi(r) for r in pi], [r["score"] for r in pi]), 3),
    "ci95": ci_trace([yi(r) for r in pi], [r["score"] for r in pi])}
res["is_parseable_baseline_incorrect"] = round(auroc([yi(r) for r in inc], [1 - r["parseable"] for r in inc]), 3)
res["parseable_counts"] = {"ft1_unparsed": sum(1 for r in inc if r["ft"] == 1 and not r["parseable"]),
                            "ft2_unparsed": sum(1 for r in inc if r["ft"] == 2 and not r["parseable"])}

# (3) degradation excluding HLE + domain-matched
def degr(inc_s, cor_s, B=3000):
    yi_ = np.array([yi(r) for r in inc_s]); si = np.array([r["score"] for r in inc_s], float)
    yc_ = np.array([yc(r) for r in cor_s]); sc = np.array([r["score"] for r in cor_s], float)
    ai, ac = auroc(yi_, si), auroc(yc_, sc); dd = []
    for _ in range(B):
        i1 = rng.integers(0, len(yi_), len(yi_)); i2 = rng.integers(0, len(yc_), len(yc_))
        if len(set(yi_[i1])) == 2 and len(set(yc_[i2])) == 2:
            dd.append(auroc(yc_[i2], sc[i2]) - auroc(yi_[i1], si[i1]))
    dd = np.array(dd)
    return {"inc": round(ai, 3), "cor": round(ac, 3), "delta": round(ac - ai, 3),
            "ci95": [round(float(q), 3) for q in np.percentile(dd, [2.5, 97.5])],
            "p_le0": round(float((dd <= 0).mean()), 4)}
res["degradation_excl_hle"] = degr([r for r in inc if r["dom"] != "HLE_BIO"], [r for r in cor if r["dom"] != "HLE_BIO"])
# domain-matched: within-domain deltas, n-weighted (common domains, excl HLE tiny correct cell)
wd = []
for dom in ["truthfulqa", "logiqa", "aqua"]:
    di = [r for r in inc if r["dom"] == dom]; dc = [r for r in cor if r["dom"] == dom]
    ai = auroc([yi(r) for r in di], [r["score"] for r in di]); ac = auroc([yc(r) for r in dc], [r["score"] for r in dc])
    wd.append((dom, ac - ai, len(di) + len(dc)))
res["within_domain_deltas"] = {d: round(x, 3) for d, x, _ in wd}
res["within_domain_delta_weighted"] = round(float(sum(x * n for _, x, n in wd) / sum(n for _, _, n in wd)), 3)

# (4) question-clustered CIs
res["clustered_cis"] = {
    "judge_full": {"auroc": round(auroc([r["unf"] for r in rows], [r["score"] for r in rows]), 3),
                    "ci_cluster": ci_cluster(rows, lambda r: r["unf"])},
    "judge_incorrect": {"auroc": round(auroc([yi(r) for r in inc], [r["score"] for r in inc]), 3),
                         "ci_cluster": ci_cluster(inc, yi)},
    "judge_correct": {"auroc": round(auroc([yc(r) for r in cor], [r["score"] for r in cor]), 3),
                       "ci_cluster": ci_cluster(cor, yc)},
    "n_questions": len(set(r["q"] for r in rows)),
    "traces_per_question_mean": round(len(rows) / len(set(r["q"] for r in rows)), 2)}

# (5) score histogram
res["score_histogram"] = dict(sorted(Counter(r["score"] for r in rows).items()))
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(res, indent=1))
print("TEMPER_PATCH DONE")
