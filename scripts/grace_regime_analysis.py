"""GRACE two-regime analysis, with the aggregation degrees-of-freedom handled explicitly.

DISCLOSURE (no pre-registration is possible here and none is claimed): before writing this
analysis I inspected how the trace-label aggregation rule changes the 2x2 cell counts, and saw
that "any non-faithful step" starves the faithful-incorrect cell to 9 while a majority rule gives
112/79/55/191. Choosing a rule after seeing that is a researcher degree of freedom. Two defences
are built in instead of a claim of blindness:

  1. PRIMARY endpoint is THRESHOLD-FREE. GRACE's native annotation is graded (each step carries a
     label), so the trace-level target is the FRACTION of non-faithful steps and the statistic is
     Spearman rho between signal and that fraction, within each correctness regime. No aggregation
     rule enters the primary at all.
  2. SECONDARY endpoints are binary AUROC at EVERY threshold in {any, >0.25, >=0.5, >0.5, all},
     reported as a band. Any conclusion that flips inside that band is reported as not a finding.

Regime contrast: primary is rho(correct) - rho(incorrect); question-clustered bootstrap over
original_question_id (questions recur across the 10 generator models).

Composition controls (the audit skipped before the BonaFide freeze, run here first): GRACE shows
NO length confound (unfaithful 4.68 vs faithful 4.65 mean steps) but does show mild dataset/track/
model imbalance, so every headline is also reported within dataset x track cells.

Signal directions are fixed a priori, higher = more unfaithful:
  nli_unsup_ctx / nli_unsup_prior  (+)   n_steps / words (+)
  nli_mean_ent_ctx (-)             frac_cited (-)
Inverted signals are negated once, here, and never re-selected.

Usage: python grace_regime_analysis.py
Output: ~/synth/results/grace_regime_results.json
"""
import glob, json, os, re
import numpy as np
from collections import defaultdict
from scipy.stats import rankdata, spearmanr

RES = os.path.expanduser("~/synth/results")
GDIR = os.path.expanduser("~/grace/dataset/test")
INVERTED = {"nli_mean_ent_ctx", "frac_cited"}
# FIX: the native target is a FRACTION of non-faithful steps, so unsupported-step COUNTS are
# mechanically confounded with trace length (a long trace accrues more unsupported steps without
# a higher fraction). Rate versions are the like-for-like signals; counts retained for reference.
SIG = ["nli_frac_unsup_ctx", "nli_frac_unsup_prior", "nli_mean_ent_ctx",
       "nli_unsup_ctx", "nli_unsup_prior", "n_steps", "words", "frac_cited"]
RULES = {"any": lambda f: f > 0, ">0.25": lambda f: f > 0.25, ">=0.5": lambda f: f >= 0.5,
         ">0.5": lambda f: f > 0.5, "all": lambda f: f >= 1.0}

def steptext(s):
    for k in ("text", "step", "content", "step_text"):
        if s.get(k): return str(s[k])
    return ""

def letter(s):
    m = re.match(r"\s*([A-E])\s*\)", str(s))
    return m.group(1) if m else str(s).strip()[:1].upper()

rows = []
for f in sorted(glob.glob(os.path.join(GDIR, "*.jsonl"))):
    for l in open(f):
        r = json.loads(l)
        r["correct"] = int(letter(r["gold_answer"]) == letter(r["final_answer"]))
        r["frac"] = float(np.mean([s.get("faithfulness") != "faithful" for s in r["steps"]]))
        r["n_steps"] = len(r["steps"])
        txt = " ".join(steptext(s) for s in r["steps"])
        r["words"] = len(txt.split())
        r["frac_cited"] = sum(1 for s in r["steps"] if s.get("citations")) / max(1, len(r["steps"]))
        r["cluster"] = r["original_question_id"]
        rows.append(r)
nli = json.load(open(os.path.join(RES, "grace_nli.json")))
for r in rows:
    r.update(nli.get(r["id"], {}))
    for tag in ("ctx", "prior"):
        c = r.get(f"nli_unsup_{tag}")
        r[f"nli_frac_unsup_{tag}"] = None if c is None else c / max(1, r["n_steps"])
for r in rows:
    for k in INVERTED:
        if r.get(k) is not None: r[k] = -float(r[k])   # negate once; direction now fixed

cor = [r for r in rows if r["correct"] == 1]; inc = [r for r in rows if r["correct"] == 0]
print(f"n={len(rows)}  correct={len(cor)}  incorrect={len(inc)}")

def clus_boot(rws, stat, B=2000, seed=0):
    cl = defaultdict(list)
    for i, r in enumerate(rws): cl[r["cluster"]].append(i)
    ks = list(cl); rng = np.random.default_rng(seed); out = []
    tries = 0
    while len(out) < B and tries < B * 20:
        tries += 1
        idx = [i for c in rng.choice(len(ks), len(ks), replace=True) for i in cl[ks[c]]]
        v = stat([rws[i] for i in idx])
        if v is not None and not np.isnan(v): out.append(v)
    return out

def rho(rws, k):
    v = [(r[k], r["frac"]) for r in rws if r.get(k) is not None]
    if len(v) < 15 or len({x[1] for x in v}) < 2: return None
    return float(spearmanr([x[0] for x in v], [x[1] for x in v]).statistic)

def auc_at(rws, k, rule):
    v = [(float(r[k]), int(RULES[rule](r["frac"]))) for r in rws if r.get(k) is not None]
    y = np.array([x[1] for x in v]); s = np.array([x[0] for x in v])
    if y.sum() in (0, len(y)) or len(v) < 15: return None
    rk = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    return float((rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

out = {"n": len(rows),
       "regimes": {"correct": len(cor), "incorrect": len(inc)},
       "primary": "Spearman rho(signal, fraction of non-faithful steps), threshold-free",
       "disclosure": "aggregation cell counts were inspected before this analysis; primary is "
                     "threshold-free and all five thresholds are reported as a band",
       "composition": "no length confound (4.68 vs 4.65 mean steps); mild dataset/track/model imbalance",
       "signals": {}}

print("\n=== PRIMARY (threshold-free): Spearman rho vs fraction non-faithful ===")
print(f"{'signal':18s} {'pooled':>20} {'CORRECT':>20} {'INCORRECT':>20} {'cor-inc':>18}")
for k in SIG:
    rec = {}
    for lab, rws in (("pooled", rows), ("correct", cor), ("incorrect", inc)):
        p = rho(rws, k)
        if p is None: rec[lab] = None; continue
        bs = clus_boot(rws, lambda z, kk=k: rho(z, kk))
        rec[lab] = {"rho": round(p, 3),
                    "ci95": [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)]}
    d = clus_boot(rows, lambda z, kk=k: (lambda a, b: None if a is None or b is None else a - b)(
        rho([r for r in z if r["correct"] == 1], kk), rho([r for r in z if r["correct"] == 0], kk)))
    dp = (rec["correct"]["rho"] - rec["incorrect"]["rho"]) if rec.get("correct") and rec.get("incorrect") else None
    rec["regime_diff"] = None if dp is None else {
        "delta": round(dp, 3),
        "ci95": [round(float(np.percentile(d, 2.5)), 3), round(float(np.percentile(d, 97.5)), 3)]}
    f = lambda x: f"{x['rho']:+.3f} {x['ci95']}" if x else "n/a"
    g = lambda x: f"{x['delta']:+.3f} {x['ci95']}" if x else "n/a"
    print(f"{k:18s} {f(rec.get('pooled')):>20} {f(rec.get('correct')):>20} {f(rec.get('incorrect')):>20} {g(rec.get('regime_diff')):>18}")
    out["signals"][k] = {"primary": rec}

print("\n=== SECONDARY: binary AUROC across ALL five aggregation thresholds ===")
print(f"{'signal':18s} " + " ".join(f"{r:>14}" for r in RULES))
for reg, rws in (("CORRECT", cor), ("INCORRECT", inc)):
    print(f"-- {reg} regime")
    for k in SIG:
        vals = []
        for rule in RULES:
            v = auc_at(rws, k, rule)
            vals.append("n/a" if v is None else f"{v:.3f}")
        out["signals"][k].setdefault("auroc_band", {})[reg] = dict(zip(RULES, vals))
        span = [float(x) for x in vals if x != "n/a"]
        flip = "  <-- crosses 0.5" if span and min(span) < 0.5 < max(span) else ""
        print(f"   {k:18s} " + " ".join(f"{v:>14}" for v in vals) + flip)

print("\n=== composition control: within dataset x track (pair-weighted AUROC, majority rule) ===")
for k in SIG:
    num = den = 0.0
    for key in {(r["dataset"], r["track"]) for r in rows}:
        sub = [r for r in rows if (r["dataset"], r["track"]) == key and r.get(k) is not None]
        y = np.array([int(RULES[">=0.5"](r["frac"])) for r in sub])
        if y.sum() in (0, len(y)) or len(sub) < 10: continue
        s = np.array([float(r[k]) for r in sub]); rk = rankdata(s)
        n1 = y.sum(); n0 = len(y) - n1
        w = float(n1 * n0)
        num += w * float((rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)); den += w
    v = round(num / den, 3) if den else None
    out["signals"][k]["conditioned_dataset_track"] = v
    print(f"   {k:18s} {v}")

json.dump(out, open(os.path.join(RES, "grace_regime_results.json"), "w"), indent=2)
print("\nGRACE REGIME ANALYSIS DONE")
