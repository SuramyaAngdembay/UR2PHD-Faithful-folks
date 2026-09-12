"""Two-regime test on GRACE (third reference standard).

GRACE (Pham et al., github.com/pvhoang14/GRACE-benchmark, pinned 63b6b2d) supplies human
step-level faithfulness labels on 437 test traces from 10 models over 4 context-grounded datasets.
Unlike BonaFide it has BOTH classes in BOTH correctness strata, so the correctness stratification
of our FaithCoT result is at least testable here.

Design decisions, fixed before running (learned from the BonaFide freeze):
  * Unit = trace. Trace label = 1 if ANY step is labelled non-faithful. This is OUR aggregation of
    a natively step-level label and is reported as such; `frac_unfaithful` is carried as a
    sensitivity alternative.
  * Correctness = letter-normalised gold_answer == final_answer.
  * Cluster = original_question_id for all bootstraps (questions recur across models).
  * Power is asymmetric and known in advance: correct regime 180U/66F (testable), incorrect regime
    182U/9F (badly underpowered -- any incorrect-regime interval will be wide, and we will not read
    a point estimate there as a finding).
  * Composition audit already run: length is NOT confounded (unfaithful 4.68 vs faithful 4.65 mean
    steps), unlike BonaFide. Mild composition differences remain by dataset, track and model, so
    every headline is also reported conditioned on those.

Signals (all higher = more unfaithful unless noted):
  nli_unsup_ctx    # steps not entailed by the supplied passages   (grounding-apt)
  nli_unsup_prior  # steps not entailed by question + prior steps  (matches our FaithCoT definition)
  nli_mean_ent_ctx # mean entailment prob from passages (inverted: higher = more faithful)
  n_steps, words   # surface/length family
  frac_cited       # fraction of steps carrying citations (inverted expected)

Usage: python grace_regime_test.py --stage nli --gpu 0      # GPU pass, writes cache
       python grace_regime_test.py --stage stats            # CPU, reads cache
Output: ~/synth/results/grace_nli.json, ~/synth/results/grace_regime_results.json
"""
import argparse, glob, json, os, re
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--stage", required=True, choices=["nli", "stats"])
ap.add_argument("--gpu", type=int, default=0)
ap.add_argument("--gdir", default="~/grace/dataset/test")
a = ap.parse_args()
RES = os.path.expanduser("~/synth/results")
GDIR = os.path.expanduser(a.gdir)

def steptext(s):
    for k in ("text", "step", "content", "step_text"):
        if s.get(k): return str(s[k])
    return ""

def letter(s):
    m = re.match(r"\s*([A-E])\s*\)", str(s))
    return m.group(1) if m else str(s).strip()[:1].upper()

def load():
    rows = []
    for f in sorted(glob.glob(os.path.join(GDIR, "*.jsonl"))):
        for l in open(f):
            r = json.loads(l)
            r["correct"] = int(letter(r["gold_answer"]) == letter(r["final_answer"]))
            r["y"] = int(any(s.get("faithfulness") != "faithful" for s in r["steps"]))
            r["frac_unfaithful"] = float(np.mean([s.get("faithfulness") != "faithful" for s in r["steps"]]))
            r["n_steps"] = len(r["steps"])
            txt = " ".join(steptext(s) for s in r["steps"])
            r["words"] = len(txt.split())
            r["frac_cited"] = sum(1 for s in r["steps"] if s.get("citations")) / max(1, len(r["steps"]))
            r["cluster"] = r["original_question_id"]
            rows.append(r)
    return rows

if a.stage == "nli":
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    tok = AutoTokenizer.from_pretrained("roberta-large-mnli")
    m = AutoModelForSequenceClassification.from_pretrained("roberta-large-mnli").to(f"cuda:{a.gpu}").eval()
    ENT = 2
    rows = load(); out = {}
    with torch.no_grad():
        for i, r in enumerate(rows):
            steps = [steptext(s) for s in r["steps"]]
            ctx = " ".join(p.get("text", "") for p in (r.get("passages") or []))[:4000] or r.get("context", "")[:4000]
            prem_ctx = [ctx] * len(steps)
            prem_pri = [(r["question"] + " " + " ".join(steps[:j]))[:4000] for j in range(len(steps))]
            res = {}
            for tag, prem in (("ctx", prem_ctx), ("prior", prem_pri)):
                ents = []
                for b in range(0, len(steps), 8):
                    hs = steps[b:b + 8]; ps = prem[b:b + 8]
                    if not any(h.strip() for h in hs):
                        ents += [0.0] * len(hs); continue
                    enc = tok(ps, hs, truncation=True, max_length=512, padding=True,
                              return_tensors="pt").to(f"cuda:{a.gpu}")
                    ents += torch.softmax(m(**enc).logits, -1)[:, ENT].tolist()
                res[f"nli_unsup_{tag}"] = int(sum(1 for e in ents if e < 0.5))
                res[f"nli_mean_ent_{tag}"] = float(np.mean(ents)) if ents else 0.0
            out[r["id"]] = res
            if (i + 1) % 50 == 0: print(f"  nli {i+1}/{len(rows)}", flush=True)
    json.dump(out, open(os.path.join(RES, "grace_nli.json"), "w"))
    print("GRACE NLI DONE", flush=True)

else:
    from scipy.stats import rankdata
    from collections import defaultdict, Counter
    rows = load()
    nli = json.load(open(os.path.join(RES, "grace_nli.json")))
    for r in rows: r.update(nli.get(r["id"], {}))
    def auc(y, s):
        y = np.asarray(y); s = np.asarray(s, float); rk = rankdata(s)
        n1 = y.sum(); n0 = len(y) - n1
        return None if n1 == 0 or n0 == 0 else float((rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    def cell(rws, k, B=2000):
        rws = [r for r in rws if r.get(k) is not None]
        y = np.array([r["y"] for r in rws])
        if y.sum() in (0, len(y)) or len(rws) < 15: return None
        s = np.array([r[k] for r in rws], float)
        cl = defaultdict(list)
        for i, r in enumerate(rws): cl[r["cluster"]].append(i)
        ks = list(cl); rng = np.random.default_rng(0); bs = []
        while len(bs) < B:
            idx = [i for c in rng.choice(len(ks), len(ks), replace=True) for i in cl[ks[c]]]
            yy = y[idx]
            if yy.sum() in (0, len(yy)): continue
            bs.append(auc(yy, s[idx]))
        return dict(n=len(rws), pos=int(y.sum()), auroc=round(auc(y, s), 3),
                    ci95=[round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)])
    SIG = ["nli_unsup_ctx", "nli_unsup_prior", "nli_mean_ent_ctx", "n_steps", "words", "frac_cited"]
    cor = [r for r in rows if r["correct"] == 1]; inc = [r for r in rows if r["correct"] == 0]
    out = {"n": len(rows), "regimes": {"correct": {"n": len(cor), "pos": sum(r["y"] for r in cor)},
                                       "incorrect": {"n": len(inc), "pos": sum(r["y"] for r in inc)}},
           "trace_label": "any non-faithful step (our aggregation of a step-level native label)",
           "pooled": {}, "correct_regime": {}, "incorrect_regime": {}, "conditioned": {}}
    print(f"{'signal':18s} {'pooled':>22} {'CORRECT':>22} {'INCORRECT':>22}")
    for k in SIG:
        p, c, i = cell(rows, k), cell(cor, k), cell(inc, k)
        out["pooled"][k], out["correct_regime"][k], out["incorrect_regime"][k] = p, c, i
        f = lambda d: f"{d['auroc']:.3f} {d['ci95']}" if d else "n/a"
        print(f"{k:18s} {f(p):>22} {f(c):>22} {f(i):>22}")
    # conditioned within dataset x track (composition control)
    print("\nconditioned (within dataset x track, pair-weighted):")
    for k in SIG:
        num = den = 0.0
        for key in {(r["dataset"], r["track"]) for r in rows}:
            sub = [r for r in rows if (r["dataset"], r["track"]) == key and r.get(k) is not None]
            y = np.array([r["y"] for r in sub])
            if y.sum() in (0, len(y)) or len(sub) < 10: continue
            w = float(y.sum() * (len(y) - y.sum()))
            num += w * auc(y, np.array([r[k] for r in sub], float)); den += w
        v = round(num / den, 3) if den else None
        out["conditioned"][k] = v
        print(f"   {k:18s} {v}")
    json.dump(out, open(os.path.join(RES, "grace_regime_results.json"), "w"), indent=2)
    print("\nGRACE REGIME TEST DONE")
