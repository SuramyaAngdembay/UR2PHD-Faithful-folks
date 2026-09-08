"""Does benchmark correctness composition change detector rankings? (Reviewer direction 1, leg 1.)

Aggregate AUROC over a faithful/unfaithful benchmark decomposes exactly over the four pair cells
formed by answer correctness:
    AUC = sum_{x,y in {inc,cor}} w_xy * AUC(U_x vs F_y),   w_xy = p_x * q_y
where p is the correctness mix within the Unfaithful class and q within the Faithful class, and
each AUC(U_x vs F_y) is fixed per-pair behavior. Changing (p, q) reweights the SAME pairwise
comparisons -- nothing about any detector changes -- so any ranking change is composition, not
capability. (Ties handled with the 1/2 convention throughout.)

Detectors: the paper's metric signals (fixed a-priori directions; soft inverted as published),
the five judge arms, and the CORRECTNESS ORACLE -- the pure composition-exploiting detector
(within-regime AUC = 0.5 by construction).

Outputs:
  1. per-detector 4-cell decomposition (+ the two cross cells);
  2. aggregate AUC at the benchmark's own composition (sanity: reproduces published numbers)
     and at counterfactual compositions (balanced; flipped; correctness-independent);
  3. ranking tables + Kendall tau vs the benchmark composition ranking; which detectors cross;
  4. selection-rule comparison with a prospective leave-one-domain-out test:
     select on 3 domains by each rule {aggregate AUC, worst-regime, mean-regime,
     standardized-mixture}, freeze, evaluate on the held-out domain at ITS observed composition
     and within-regime; report regret vs the best-on-target detector.

Pure reanalysis of stored predictions; no new model calls. Run locally:
  python scripts/composition_rankings.py
Output: results/composition_rankings.json
"""
import json, os, itertools
import numpy as np
from scipy.stats import rankdata, kendalltau

R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

feats = json.load(open(os.path.join(R, "rigorous_features.json")))
jj = json.load(open(os.path.join(R, "judge_join.json")))
arms = {"judgeA": None, "judgeB": "judge_raw_promptB.jsonl", "judge4o": "judge_raw_gpt4o.jsonl",
        "judge_qonly": "judge_raw_qonly.jsonl", "judge_cotonly": "judge_raw_cotonly.jsonl"}
for k, f in arms.items():
    if f is None: continue
    for line in open(os.path.join(R, f)):
        d = json.loads(line)
        if d["rid"] in jj: jj[d["rid"]][k] = d["score"]

# ---------- assemble per-trace table ----------
# Metric rows (complete-feature subset) come from rigorous_features; judge rows from the join.
# Signal directions are the paper's published a-priori/fixed choices (soft & correctness inverted).
METRICS = {  # name -> (key, sign) ; sign +1 means higher = more unfaithful under the fixed direction
    # NOTE: "inverted" = the published empirical directions (higher soft/PI = MORE unfaithful).
    "answer-tracing (soft, inv)": ("soft", +1),
    "prefix-instability (inv)":   ("avg_impact", +1),
    "NLI unsupported steps":      ("nli_n_unsup", +1),
    "DAG linearity":              ("dag_lin", +1),
    "step count":                 ("n_steps", +1),
}
JUDGES = ["judgeA", "judgeB", "judge4o", "judge_cotonly"]

def cellsplit(rows, ft_key="ft"):
    """Return dict cell -> score array; U=unfaithful (ft2/ft4), F=faithful (ft1/ft3)."""
    g = {("U", "inc"): [], ("U", "cor"): [], ("F", "inc"): [], ("F", "cor"): []}
    for r in rows:
        ft = r[ft_key]
        cls = "U" if ft in (2, 4) else "F"
        reg = "inc" if ft in (1, 2) else "cor"
        g[(cls, reg)].append(r["_score"])
    return {k: np.asarray(v, float) for k, v in g.items()}

def pair_auc(u, f):
    if len(u) == 0 or len(f) == 0: return np.nan
    s = np.concatenate([u, f]); r = rankdata(s)
    ru = r[:len(u)].sum()
    return (ru - len(u) * (len(u) + 1) / 2) / (len(u) * len(f))

def four_cells(g):
    return {f"{x}|{y}": pair_auc(g[("U", x)], g[("F", y)])
            for x in ("inc", "cor") for y in ("cor", "inc")}

def mix_auc(cells, p_inc, q_inc):
    w = {("inc", "inc"): p_inc * q_inc, ("inc", "cor"): p_inc * (1 - q_inc),
         ("cor", "inc"): (1 - p_inc) * q_inc, ("cor", "cor"): (1 - p_inc) * (1 - q_inc)}
    return sum(w[(x, y)] * cells[f"{x}|{y}"] for x, y in w)

def detector_rows(name):
    """Rows with _score attached for the given detector."""
    if name in METRICS:
        key, sign = METRICS[name]
        rows = [dict(r, _score=sign * r[key]) for r in feats
                if r.get("ft") in (1, 2, 3, 4) and r.get(key) is not None and not (isinstance(r[key], float) and np.isnan(r[key]))]
    elif name == "correctness oracle":
        rows = [dict(ft=v["ft"], dom=v["dom"], _score=1 - v["correct"]) for v in jj.values() if v.get("correct") is not None]
    else:
        rows = [dict(ft=v["ft"], dom=v["dom"], _score=v[name]) for v in jj.values() if name in v]
    return rows

DETS = list(METRICS) + ["correctness oracle"] + JUDGES
out = {"n_feats": len(feats), "n_judge": len(jj), "detectors": {}}

# benchmark's own composition (from the full ft-labeled set)
ftc = [v["ft"] for v in jj.values()]
P_INC = sum(1 for f in ftc if f == 2) / sum(1 for f in ftc if f in (2, 4))   # U class
Q_INC = sum(1 for f in ftc if f == 1) / sum(1 for f in ftc if f in (1, 3))   # F class
out["benchmark_composition"] = {"p_inc_unfaithful": round(P_INC, 4), "q_inc_faithful": round(Q_INC, 4)}

MIXES = {"benchmark": (P_INC, Q_INC), "balanced": (0.5, 0.5), "flipped": (1 - P_INC, 1 - Q_INC),
         "all-incorrect": (1.0, 1.0), "all-correct": (0.0, 0.0)}

for name in DETS:
    rows = detector_rows(name)
    g = cellsplit(rows)
    cells = four_cells(g)
    nU = len(g[("U", "inc")]) + len(g[("U", "cor")]); nF = len(g[("F", "inc")]) + len(g[("F", "cor")])
    own = (len(g[("U", "inc")]) / nU, len(g[("F", "inc")]) / nF)   # this detector's own composition
    mixes = dict(MIXES); mixes["benchmark"] = own
    rec = {"n": len(rows), "own_composition": [round(x, 3) for x in own],
           "cells": {k: (None if np.isnan(v) else round(float(v), 4)) for k, v in cells.items()},
           "mixtures": {m: round(float(mix_auc(cells, p, q)), 4) for m, (p, q) in mixes.items()},
           "pooled_auc_check": round(float(pair_auc(
               np.concatenate([g[("U", "inc")], g[("U", "cor")]]),
               np.concatenate([g[("F", "inc")], g[("F", "cor")]]))), 4)}
    out["detectors"][name] = rec
    print(f"{name:28s} n={rec['n']:4d} cells inc|cor={rec['cells']['inc|cor']} inc|inc={rec['cells']['inc|inc']} "
          f"cor|cor={rec['cells']['cor|cor']} | bench={rec['mixtures']['benchmark']} bal={rec['mixtures']['balanced']} flip={rec['mixtures']['flipped']}", flush=True)

# ---------- rankings across mixtures ----------
rank = {}
for m in MIXES:
    vals = {d: out["detectors"][d]["mixtures"][m] for d in DETS}
    rank[m] = sorted(vals, key=vals.get, reverse=True)
out["rankings"] = rank
tau = {m: float(kendalltau([rank["benchmark"].index(d) for d in DETS],
                           [rank[m].index(d) for d in DETS]).statistic) for m in MIXES}
out["kendall_tau_vs_benchmark"] = {k: round(v, 3) for k, v in tau.items()}
orc = {m: rank[m].index("correctness oracle") + 1 for m in MIXES}
out["oracle_rank_by_mixture"] = orc
print("\noracle rank by mixture:", orc, flush=True)

# ---------- selection rules + prospective LODO (metric detectors; judges reported separately) ----------
DOMS = sorted({r["dom"] for r in feats})
SEL_DETS = list(METRICS) + ["correctness oracle"]
def cells_on(rows_by_det, dom_in):
    return {d: four_cells(cellsplit([r for r in rows_by_det[d] if r["dom"] in dom_in])) for d in rows_by_det}
rows_by_det = {d: detector_rows(d) for d in SEL_DETS}

def score_rule(cells, rule, mix):
    within = [cells["inc|inc"], cells["cor|cor"]]
    if any(np.isnan(w) for w in within): return -np.inf
    if rule == "aggregate": return mix_auc(cells, *mix)
    if rule == "worst-regime": return min(within)
    if rule == "mean-regime": return float(np.mean(within))
    if rule == "standardized": return mix_auc(cells, 0.5, 0.5)

lodo = {}
for held in DOMS:
    dev = [d for d in DOMS if d != held]
    cdev = cells_on(rows_by_det, set(dev)); ctst = cells_on(rows_by_det, {held})
    # target composition = held-out domain's own observed mixture
    ftd = [v["ft"] for v in jj.values() if v["dom"] == held]
    nU = sum(1 for f in ftd if f in (2, 4)); nF = sum(1 for f in ftd if f in (1, 3))
    pt = (sum(1 for f in ftd if f == 2) / nU if nU else 0.5, sum(1 for f in ftd if f == 1) / nF if nF else 0.5)
    tgt = {"within-regime": {d: score_rule(ctst[d], "mean-regime", pt) for d in SEL_DETS},
           "target-composition": {d: score_rule(ctst[d], "aggregate", pt) for d in SEL_DETS},
           "balanced-deployment": {d: score_rule(ctst[d], "standardized", pt) for d in SEL_DETS}}
    best = {c: max(v.values()) for c, v in tgt.items()}
    lodo[held] = {"target_mix": [round(x, 3) for x in pt],
                  "regret_by_rule": {c: {} for c in tgt}, "picked": {}}
    ftv = [v["ft"] for v in jj.values() if v["dom"] in dev]
    nUd = sum(1 for f in ftv if f in (2, 4)); nFd = sum(1 for f in ftv if f in (1, 3))
    pd_ = (sum(1 for f in ftv if f == 2) / nUd, sum(1 for f in ftv if f == 1) / nFd)
    for rule in ("aggregate", "worst-regime", "mean-regime", "standardized"):
        pick = max(SEL_DETS, key=lambda d: score_rule(cdev[d], rule, pd_))
        lodo[held]["picked"][rule] = pick
        for c in tgt:
            lodo[held]["regret_by_rule"][c][rule] = round(float(best[c] - tgt[c][pick]), 4)
out["lodo"] = lodo
mean_regret = {c: {rule: round(float(np.mean([lodo[h]["regret_by_rule"][c][rule] for h in DOMS])), 4)
                   for rule in ("aggregate", "worst-regime", "mean-regime", "standardized")}
               for c in ("within-regime", "target-composition", "balanced-deployment")}
out["mean_regret_by_rule"] = mean_regret
out["lodo_note"] = ("target criterion = mean within-regime AUC on the held-out domain (composition-free); "
                    "metric detectors + oracle only -- judges excluded from selection since they dominate "
                    "everywhere and would mask the composition effect; per-domain regime cells are small")
print("\nmean LODO regret by selection rule:", mean_regret, flush=True)

json.dump(out, open(os.path.join(R, "composition_rankings.json"), "w"), indent=2)
print("\nCOMPOSITION RANKINGS DONE", flush=True)
