"""Corrected composition/selection analysis (external review 2026-09-08 round 2).

Fixes relative to composition_rankings.py, whose selection headline did not survive review:
  1. The correctness ORACLE is excluded from every selection pool (it needs gold correctness, so
     it is not an available detector). It is kept ONLY as the composition illustration.
  2. Judges are IN the default pool. A metrics-only pool is reported as an explicit
     constrained setting (no API budget), not as the general result.
  3. All detectors in a comparison are evaluated on the SAME examples (rids attached to
     rigorous_features rows via a verified replay of the producer's glob order).
  4. Fixed-detector baselines (always-X for every candidate) are reported alongside the rules.
  5. Question-clustered bootstrap (cluster = domain/basename, ~341 clusters) that REPEATS the
     dev-selection step per draw; CIs on regret and on rule-vs-rule and rule-vs-fixed differences.

Selection rules: aggregate AUC, worst-regime, mean-regime, standardized(0.5,0.5).
Target criteria: within-regime mean, target's own composition, balanced deployment.
LODO is retrospective (domains were examined during development) and is labeled as such.

Run: python scripts/composition_rankings2.py    Output: results/composition_rankings2.json
"""
import json, os
import numpy as np
from scipy.stats import rankdata

R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
feats = json.load(open(os.path.join(R, "rigorous_features.json")))
rids = json.load(open(os.path.join(R, "feat_rids.json")))
assert len(feats) == len(rids)
for r, x in zip(feats, rids): r["rid"] = x["rid"]
jj = json.load(open(os.path.join(R, "judge_join.json")))
for k, f in {"judgeB": "judge_raw_promptB.jsonl", "judge4o": "judge_raw_gpt4o.jsonl",
             "judge_cotonly": "judge_raw_cotonly.jsonl"}.items():
    for line in open(os.path.join(R, f)):
        d = json.loads(line)
        if d["rid"] in jj: jj[d["rid"]][k] = d["score"]

METRICS = {"soft(inv)": ("soft", +1), "PI(inv)": ("avg_impact", +1), "NLI-unsup": ("nli_n_unsup", +1),
           "DAG-lin": ("dag_lin", +1), "steps": ("n_steps", +1)}
JUDGES = ["judgeA", "judgeB", "judge4o", "judge_cotonly"]

# ---- unified per-example table: rid -> {ft, dom, cluster, scores...} ----
tab = {}
for r in feats:
    if r["ft"] not in (1, 2, 3, 4): continue
    e = tab.setdefault(r["rid"], {"ft": r["ft"], "dom": r["dom"],
                                  "cluster": r["rid"].split("/")[0] + "/" + r["rid"].split("/")[-1]})
    for name, (k, s) in METRICS.items():
        v = r.get(k)
        if v is not None and not (isinstance(v, float) and np.isnan(v)): e[name] = s * v
for rid, v in jj.items():
    e = tab.setdefault(rid, {"ft": v["ft"], "dom": v["dom"],
                             "cluster": rid.split("/")[0] + "/" + rid.split("/")[-1]})
    for jn in JUDGES:
        if jn in v: e[jn] = v[jn]

ALL = list(tab.values())
COMMON = [e for e in ALL if all(d in e for d in list(METRICS) + JUDGES)]
print(f"examples: all={len(ALL)} common(all detectors)={len(COMMON)}", flush=True)

def pair_auc(u, f):
    if len(u) == 0 or len(f) == 0: return np.nan
    s = np.concatenate([u, f]); r = rankdata(s)
    return (r[:len(u)].sum() - len(u) * (len(u) + 1) / 2) / (len(u) * len(f))

def cells(ex, det):
    g = {("U", "inc"): [], ("U", "cor"): [], ("F", "inc"): [], ("F", "cor"): []}
    for e in ex:
        cls = "U" if e["ft"] in (2, 4) else "F"; reg = "inc" if e["ft"] in (1, 2) else "cor"
        g[(cls, reg)].append(e[det])
    return {f"{x}|{y}": pair_auc(np.asarray(g[("U", x)], float), np.asarray(g[("F", y)], float))
            for x in ("inc", "cor") for y in ("inc", "cor")}

def mix_auc(c, p, q):
    return (p * q * c["inc|inc"] + p * (1 - q) * c["inc|cor"]
            + (1 - p) * q * c["cor|inc"] + (1 - p) * (1 - q) * c["cor|cor"])

def own_mix(ex):
    U = [e for e in ex if e["ft"] in (2, 4)]; F = [e for e in ex if e["ft"] in (1, 3)]
    if not U or not F: return (0.5, 0.5)
    return (sum(e["ft"] == 2 for e in U) / len(U), sum(e["ft"] == 1 for e in F) / len(F))

def rule_score(c, rule, mix):
    w = [c["inc|inc"], c["cor|cor"]]
    if any(np.isnan(x) for x in w): return -np.inf
    return {"aggregate": lambda: mix_auc(c, *mix), "worst-regime": lambda: min(w),
            "mean-regime": lambda: float(np.mean(w)), "standardized": lambda: mix_auc(c, .5, .5)}[rule]()

def crit_score(c, crit, mix):
    w = [c["inc|inc"], c["cor|cor"]]
    if any(np.isnan(x) for x in w): return np.nan
    return {"within-regime": lambda: float(np.mean(w)), "target-composition": lambda: mix_auc(c, *mix),
            "balanced": lambda: mix_auc(c, .5, .5)}[crit]()

RULES = ("aggregate", "worst-regime", "mean-regime", "standardized")
CRITS = ("within-regime", "target-composition", "balanced")
DOMS = sorted({e["dom"] for e in ALL})

def lodo(ex, pool, nboot=1000, seed=0):
    """Retrospective LODO with per-draw re-selection; returns point + clustered-bootstrap regrets."""
    rng = np.random.default_rng(seed)
    clusters = sorted({e["cluster"] for e in ex})
    bycl = {c: [e for e in ex if e["cluster"] == c] for c in clusters}
    def one(sample):
        res = {}
        for held in DOMS:
            dev = [e for e in sample if e["dom"] != held]; tst = [e for e in sample if e["dom"] == held]
            if not tst or not dev: continue
            cd = {d: cells(dev, d) for d in pool}; ct = {d: cells(tst, d) for d in pool}
            md, mt = own_mix(dev), own_mix(tst)
            for crit in CRITS:
                perf = {d: crit_score(ct[d], crit, mt) for d in pool}
                if any(np.isnan(v) for v in perf.values()): continue
                best = max(perf.values())
                for rule in RULES:
                    pick = max(pool, key=lambda d: rule_score(cd[d], rule, md))
                    res.setdefault((crit, rule), []).append(best - perf[pick])
                for d in pool:  # fixed baselines
                    res.setdefault((crit, f"fixed:{d}"), []).append(best - perf[d])
        return {k: float(np.mean(v)) for k, v in res.items()}
    point = one(ex)
    boots = {k: [] for k in point}
    for _ in range(nboot):
        draw = [e for c in rng.choice(clusters, len(clusters), replace=True) for e in bycl[c]]
        for k, v in one(draw).items():
            if k in boots: boots[k].append(v)
    out = {}
    for k, v in point.items():
        b = np.array(boots[k])
        out["|".join(k) if isinstance(k, tuple) else k] = {
            "mean_regret": round(v, 4),
            "ci95": [round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)] if len(b) else None}
    # paired rule differences (aggregate minus alternative), same draws
    for crit in CRITS:
        for alt in ("worst-regime", "mean-regime", "standardized"):
            a = np.array(boots[(crit, "aggregate")]); w = np.array(boots[(crit, alt)])
            if len(a) and len(w):
                d = a - w
                out[f"{crit}|aggregate-minus-{alt}"] = {
                    "mean": round(float(np.mean(d)), 4),
                    "ci95": [round(float(np.percentile(d, 2.5)), 4), round(float(np.percentile(d, 97.5)), 4)]}
    return out

out = {"n_all": len(ALL), "n_common": len(COMMON),
       "note": "LODO is retrospective (domains examined during development); oracle excluded from all pools; "
               "regret = best-available-on-target minus selected, under each criterion",
       "settings": {}}
POOLS = {"metrics-only(common)": (COMMON, list(METRICS)),
         "metrics+judges(common)": (COMMON, list(METRICS) + JUDGES),
         "judges-only(all)": ([e for e in ALL if all(j in e for j in JUDGES)], JUDGES)}
for name, (ex, pool) in POOLS.items():
    print(f"-- {name}: n={len(ex)} pool={pool}", flush=True)
    out["settings"][name] = lodo(ex, pool)
    for crit in CRITS:
        row = {r: out["settings"][name].get(f"{crit}|{r}", {}).get("mean_regret") for r in RULES}
        fixed_best = min((out["settings"][name][k]["mean_regret"], k) for k in out["settings"][name]
                         if k.startswith(f"{crit}|fixed:"))
        print(f"   {crit:18s} " + " ".join(f"{r}={row[r]}" for r in RULES) + f" | best-fixed {fixed_best[1].split(':',1)[1]}={fixed_best[0]}", flush=True)

json.dump(out, open(os.path.join(R, "composition_rankings2.json"), "w"), indent=2)
print("CORRECTED COMPOSITION ANALYSIS DONE", flush=True)
