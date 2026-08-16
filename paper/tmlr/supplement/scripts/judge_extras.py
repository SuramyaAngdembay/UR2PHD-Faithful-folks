"""
Judge extras for the same-sample comparisons (GPT round-6 review items 1,2,4 + Fig3 bars).

 (a) FULL labeled set (n=1303): correctness-oracle AUROC vs judge AUROC, paired bootstrap dAUROC CI.
 (b) Judge regime degradation: 0.830 vs 0.679, two-sample bootstrap dAUROC CI + bootstrap p.
 (c) Judge excluding GPT-4o-mini's own traces: full + per-regime.
 (d) Judge on the EXACT complete-feature subset (open models w/ stored soft scores; expect n=633):
     full + incorrect regime (expect n=270) + correct regime (expect n=363) -> Table-1/Fig-3-matched.
CPU-only; reads the release + judge_raw.jsonl. Output: ~/synth/results/judge_extras.json
"""
import json, glob, os
import numpy as np

BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
RAW = os.path.expanduser("~/synth/results/judge_raw.jsonl")
OUT = os.path.expanduser("~/synth/results/judge_extras.json")
OPEN = {"llama-3.1-8b-instruct", "Qwen2.5-7B-Instruct"}

js = {}
for line in open(RAW):
    d = json.loads(line); js[d["rid"]] = d["score"]

recs = []
for f in sorted(glob.glob(BASE + "/*/*/response_*.json")):
    d = json.load(open(f)); ft = int(d.get("faithful_type", 0) or 0)
    if ft not in (1, 2, 3, 4): continue
    dom, mdl = f.split("/")[-3], f.split("/")[-2]
    rid = f"{dom}/{mdl}/{os.path.basename(f)}"
    if rid not in js: continue
    s = d["sample_0"]
    parsed = str(s.get("parsed_final_answer", "")).strip()
    recs.append(dict(ft=ft, unf=int(d["unfaithfulness"]), mdl=mdl,
                     correct=int(parsed == str(d["label"]).strip()) if parsed else None,
                     has_soft=s.get("soft_faithfulness") is not None,
                     score=js[rid]))
print(f"records: {len(recs)}")

def auroc(y, s):
    y, s = np.asarray(y, float), np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    return float((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())

rng = np.random.default_rng(0)
def boot_ci(y, s, B=5000):
    v = []
    y, s = np.asarray(y, float), np.asarray(s, float)
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i])) == 2: v.append(auroc(y[i], s[i]))
    return [round(float(q), 3) for q in np.percentile(v, [2.5, 97.5])]

# ---- (a) full-set oracle vs judge, PAIRED ----
rc = [r for r in recs if r["correct"] is not None]
y = np.array([r["unf"] for r in rc]); sj = np.array([r["score"] for r in rc], float)
so = np.array([1 - r["correct"] for r in rc], float)   # oracle score = incorrectness
a_or, a_ju = auroc(y, so), auroc(y, sj)
dd = []
for _ in range(5000):
    i = rng.integers(0, len(y), len(y))
    if len(set(y[i])) == 2: dd.append(auroc(y[i], sj[i]) - auroc(y[i], so[i]))
res = {"full_paired": {"n": len(y), "oracle_auroc": round(a_or, 3), "judge_auroc": round(a_ju, 3),
       "delta_judge_minus_oracle": round(a_ju - a_or, 3),
       "delta_ci95": [round(float(q), 3) for q in np.percentile(dd, [2.5, 97.5])]}}

# ---- (b) regime degradation, two-sample bootstrap ----
inc = [r for r in recs if r["ft"] in (1, 2)]; cor = [r for r in recs if r["ft"] in (3, 4)]
yi = np.array([int(r["ft"] == 2) for r in inc]); si = np.array([r["score"] for r in inc], float)
yc = np.array([int(r["ft"] == 4) for r in cor]); sc = np.array([r["score"] for r in cor], float)
ai, ac = auroc(yi, si), auroc(yc, sc)
dd = []
for _ in range(5000):
    i1 = rng.integers(0, len(yi), len(yi)); i2 = rng.integers(0, len(yc), len(yc))
    if len(set(yi[i1])) == 2 and len(set(yc[i2])) == 2:
        dd.append(auroc(yc[i2], sc[i2]) - auroc(yi[i1], si[i1]))
dd = np.array(dd)
res["regime_degradation"] = {"correct_auroc": round(ac, 3), "incorrect_auroc": round(ai, 3),
    "delta": round(ac - ai, 3), "delta_ci95": [round(float(q), 3) for q in np.percentile(dd, [2.5, 97.5])],
    "boot_p_delta_le_0": round(float((dd <= 0).mean()), 4)}

# ---- (c) excluding the judge's own (gpt-4o-mini-generated) traces ----
ex = [r for r in recs if r["mdl"] != "gpt-4o-mini"]
exi = [r for r in ex if r["ft"] in (1, 2)]; exc = [r for r in ex if r["ft"] in (3, 4)]
res["excl_own_traces"] = {
    "full": {"n": len(ex), "auroc": round(auroc([r["unf"] for r in ex], [r["score"] for r in ex]), 3),
             "ci95": boot_ci([r["unf"] for r in ex], [r["score"] for r in ex])},
    "incorrect": {"n": len(exi), "auroc": round(auroc([int(r["ft"]==2) for r in exi], [r["score"] for r in exi]), 3)},
    "correct": {"n": len(exc), "auroc": round(auroc([int(r["ft"]==4) for r in exc], [r["score"] for r in exc]), 3)}}

# ---- (d) complete-feature subset (open models with stored soft scores) ----
sub = [r for r in recs if r["mdl"] in OPEN and r["has_soft"]]
si_ = [r for r in sub if r["ft"] in (1, 2)]; sc_ = [r for r in sub if r["ft"] in (3, 4)]
def cell(rr, ykey):
    yy = [ykey(r) for r in rr]; ss = [r["score"] for r in rr]
    return {"n": len(rr), "auroc": round(auroc(yy, ss), 3), "ci95": boot_ci(yy, ss)}
res["subset633"] = {
    "full": cell(sub, lambda r: r["unf"]),
    "incorrect": cell(si_, lambda r: int(r["ft"] == 2)),
    "correct": cell(sc_, lambda r: int(r["ft"] == 4)),
    "oracle_on_subset": round(auroc([r["unf"] for r in sub if r["correct"] is not None],
                                    [1 - r["correct"] for r in sub if r["correct"] is not None]), 3)}
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(res, indent=1))
print("JUDGE_EXTRAS DONE")
