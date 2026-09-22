"""Analysis for bonafide-disclosure-rubric-spec.md. Written and hashed before any arm completed.

Primary: gpt-4o-mini rubric H (reconcile_H_full.jsonl) vs the frozen judge (judgeA in
bonafide_predictions.json) on the incorrect-answer population, paired, question-clustered bootstrap.
Secondary: gpt-4o rubric H (reconcile_H.jsonl) vs reconciliation arm C (reconcile_C.jsonl) on
their shared rows. Every quotable number is printed here.
"""
import json, hashlib, collections
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
ROOT = Path(__file__).resolve().parents[1]; RES = ROOT / 'results'; B, SEED = 2000, 0

pred = {p['rid']: p for p in json.load(open(RES / 'bonafide_predictions.json'))}
def load(fn, model=None):
    d = {}
    p = RES / fn
    if not p.exists(): return d
    for l in p.open():
        o = json.loads(l)
        if model and o.get('model') != model: continue
        if isinstance(o.get('score'), int): d[o['rid']] = float(o['score'])
    return d
def auroc(y, s):
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0: return None
    r = rankdata(s); return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
def paired(rids, ref, var):
    y = np.array([float(pred[r]['y']) for r in rids]); a = np.array([ref[r] for r in rids]); b = np.array([var[r] for r in rids])
    byq = collections.defaultdict(list)
    for i, r in enumerate(rids): byq[pred[r]['cluster']].append(i)
    qs = list(byq); rng = np.random.default_rng(SEED); dl, vb = [], []
    for _ in range(B):
        idx = [i for k in rng.integers(0, len(qs), len(qs)) for i in byq[qs[k]]]
        x, z = auroc(y[idx], a[idx]), auroc(y[idx], b[idx])
        if x is not None and z is not None: dl.append(z - x); vb.append(z)
    ci = lambda v: [round(float(np.percentile(v, 2.5)), 3), round(float(np.percentile(v, 97.5)), 3)]
    return {'n': len(rids), 'n_unf': int(y.sum()), 'ref': round(auroc(y, a), 4), 'var': round(auroc(y, b), 4),
            'var_ci95': ci(vb), 'delta': round(auroc(y, b) - auroc(y, a), 4), 'delta_ci95': ci(dl)}

out = {'spec': 'bonafide-disclosure-rubric-spec.md', 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
Hm = load('reconcile_H_full.jsonl', 'gpt-4o-mini'); H4 = load('reconcile_H.jsonl', 'gpt-4o'); C4 = load('reconcile_C.jsonl')
frozenA = {r: float(p['judgeA']) for r, p in pred.items() if isinstance(p.get('judgeA'), (int, float))}
frozen4 = {r: float(p['judge4o']) for r, p in pred.items() if isinstance(p.get('judge4o'), (int, float))}
inc = [r for r in pred if pred[r]['correct'] == 0]

if Hm:
    rids = [r for r in inc if r in Hm and r in frozenA]
    out['primary_mini_H_vs_frozenA_incorrect'] = paired(rids, frozenA, Hm)
    print('PRIMARY gpt-4o-mini rubric H vs frozen prompt-A judge, incorrect population:'); print('  ', out['primary_mini_H_vs_frozenA_incorrect'])
    by = {}
    for ht in sorted({pred[r]['hint_type'] for r in rids}):
        rr = [r for r in rids if pred[r]['hint_type'] == ht]; y = np.array([float(pred[r]['y']) for r in rr])
        a = auroc(y, np.array([Hm[r] for r in rr]))
        by[ht] = {'n': len(rr), 'n_unf': int(y.sum()), 'H': None if a is None else round(a, 3), 'frozenA': round(auroc(y, np.array([frozenA[r] for r in rr])), 3) if auroc(y, np.array([frozenA[r] for r in rr])) is not None else None}
    out['by_hint_type'] = by; print('  by hint type:'); [print('    ', k, v) for k, v in by.items()]
    v = out['primary_mini_H_vs_frozenA_incorrect']
    verdict = ('RUBRIC-EXPLAINS' if v['var'] >= 0.75 and v['delta_ci95'][0] > 0 else 'NOT-EXPLAINED' if v['var'] < 0.60 else 'MIXED')
    out['verdict'] = verdict; print('PRE-REGISTERED VERDICT:', verdict)
else: print('primary arm not yet available')
if H4 and C4:
    rids = [r for r in inc if r in H4 and r in C4]
    out['secondary_gpt4o_H_vs_armC'] = paired(rids, C4, H4); print('SECONDARY gpt-4o rubric H vs arm C (same evidence, rubric only):'); print('  ', out['secondary_gpt4o_H_vs_armC'])
    rids2 = [r for r in inc if r in H4 and r in frozen4]
    out['secondary_gpt4o_H_vs_frozen4o'] = paired(rids2, frozen4, H4); print('  vs frozen gpt-4o (clean question):', out['secondary_gpt4o_H_vs_frozen4o'])
(RES / 'bonafide_rubric_H_results.json').write_text(json.dumps(out, indent=1) + '\n'); print('wrote results/bonafide_rubric_H_results.json')
