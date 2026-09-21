"""Paired rubric-effect analysis for definition-informed-judge-spec.md. Frozen before any arm ran.

For each judge, compares a variant-rubric arm (D1, D2, R) against that judge's existing generic
prompt-A arm on the SAME traces, per regime, with a question-clustered paired bootstrap. Every
number that may be quoted is printed by this script; nothing is to be computed by hand.
"""
N_EXPECTED_ROWS = 1303
import json, hashlib, collections, sys
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]; RES = ROOT / 'results'
B, SEED = 2000, 0
JUDGES = {'qwen3_8b': 'Qwen3-8B (local, greedy)', 'llama31_8b': 'Llama-3.1-8B (local, greedy)',
          'qwen25_7b': 'Qwen2.5-7B (local, greedy)', 'mini': 'gpt-4o-mini (API, temp 0)'}
VARIANTS = ['D1', 'D2', 'R']
REGIMES = {'blind_ft1v2': ((1, 2), 2), 'correct_ft3v4': ((3, 4), 4)}

rf = json.load(open(RES / 'rigorous_features.json')); fr = json.load(open(RES / 'feat_rids.json'))
assert len(rf) == len(fr) == 1304
POP = {}
for f, r in zip(rf, fr):
    if f['ft'] in (1, 2, 3, 4):
        d, g, fn = r['rid'].split('/'); POP[r['rid']] = {'ft': f['ft'], 'q': f'{d}/{fn}', 'gen': g, 'dom': d}

def load(tag):
    p = RES / f'judge_raw_{tag}.jsonl'
    if not p.exists(): return None, 'missing'
    sc, n = {}, 0
    for line in p.open():
        o = json.loads(line); n += 1
        if o.get('score') is not None: sc[o['rid']] = float(o['score'])
    if n < N_EXPECTED_ROWS: return None, f'incomplete ({n} rows)'
    if len(sc) / n < 0.95: return None, f'parse rate {len(sc)/n:.3f}'
    return sc, 'ok'

def auroc(y, s):
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0: return None
    r = rankdata(s); return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

def pair_weighted_within(y, s, groups):
    num = den = 0.0
    for g in set(groups):
        idx = [i for i, x in enumerate(groups) if x == g]
        a = auroc(y[idx], s[idx]); n1 = int(y[idx].sum()); n0 = len(idx) - n1
        if a is not None: num += a * n1 * n0; den += n1 * n0
    return num / den if den else None

def paired(ref, var, fts, pos, ci_levels):
    rids = [r for r in POP if POP[r]['ft'] in fts and r in ref and r in var]
    y = np.array([1.0 if POP[r]['ft'] == pos else 0.0 for r in rids])
    a = np.array([ref[r] for r in rids]); b = np.array([var[r] for r in rids])
    byq = collections.defaultdict(list)
    for i, r in enumerate(rids): byq[POP[r]['q']].append(i)
    qs = list(byq); rng = np.random.default_rng(SEED); deltas = []
    for _ in range(B):
        idx = [i for k in rng.integers(0, len(qs), len(qs)) for i in byq[qs[k]]]
        x, z = auroc(y[idx], a[idx]), auroc(y[idx], b[idx])
        if x is not None and z is not None: deltas.append(z - x)
    gens = [POP[r]['gen'] for r in rids]; doms = [POP[r]['dom'] for r in rids]
    out = {'n': len(rids), 'ref': auroc(y, a), 'var': auroc(y, b)}
    out['delta'] = out['var'] - out['ref']
    for name, lv in ci_levels.items():
        lo, hi = (1 - lv) / 2 * 100, (1 + lv) / 2 * 100
        out[name] = [round(float(np.percentile(deltas, lo)), 4), round(float(np.percentile(deltas, hi)), 4)]
    out['within_generator'] = {'ref': pair_weighted_within(y, a, gens), 'var': pair_weighted_within(y, b, gens)}
    out['by_domain'] = {}
    for d in sorted(set(doms)):
        idx = [i for i, x in enumerate(doms) if x == d]
        out['by_domain'][d] = {'n': len(idx), 'ref': auroc(y[idx], a[idx]), 'var': auroc(y[idx], b[idx])}
    return out

result = {'spec': 'definition-informed-judge-spec.md',
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'arms': {}, 'skipped': {}}
avail = {}
for j in JUDGES:
    ref, st = load(j)
    if ref is None: result['skipped'][j] = st; continue
    for v in VARIANTS:
        var, st = load(f'{j}_{v}')
        if var is None: result['skipped'][f'{j}_{v}'] = st; continue
        avail[(j, v)] = (ref, var)
fam = max(1, len({j for (j, v) in avail if v == 'D1'}))
levels = {'ci95': 0.95, f'ci_bonf_{fam}': 1 - 0.05 / fam}
print(f'arms available: {sorted(f"{j}_{v}" for j, v in avail)}')
print(f'primary family (judges with a D1 arm): {fam}  -> Bonferroni interval level {levels[f"ci_bonf_{fam}"]:.4f}\n')

f3 = lambda x: 'n/a' if x is None else f'{x:.3f}'
for v in VARIANTS:
    for rn, (fts, pos) in REGIMES.items():
        rows = [(j, paired(*avail[(j, v)], fts, pos, levels)) for j in JUDGES if (j, v) in avail]
        if not rows: continue
        print(f'=== rubric {v} vs A | {rn} ===')
        print(f"{'judge':30s} {'A':>6} {v:>6} {'delta':>7} {'95% CI':>19} {'Bonferroni CI':>19} | {'within-gen A':>12} {v:>6}")
        for j, o in rows:
            bk = f'ci_bonf_{fam}'
            print(f"{JUDGES[j]:30s} {o['ref']:6.3f} {o['var']:6.3f} {o['delta']:+7.3f} {str(o['ci95']):>19} {str(o[bk]):>19} | "
                  f"{f3(o['within_generator']['ref']):>12} {f3(o['within_generator']['var']):>6}")
            result['arms'][f'{j}_{v}|{rn}'] = o
        if rn == 'blind_ft1v2':
            print('    blind regime by domain (A -> ' + v + '):')
            for j, o in rows:
                print(f"      {JUDGES[j][:24]:24s} " + '  '.join(f"{d}: {f3(x['ref'])}->{f3(x['var'])}" for d, x in o['by_domain'].items()))
        print()

# ---- pre-registered verdict on the primary question (D1, blind regime) ----
prim = [(j, result['arms'][f'{j}_D1|blind_ft1v2']) for j in JUDGES if f'{j}_D1|blind_ft1v2' in result['arms']]
if prim:
    bk = f'ci_bonf_{fam}'
    strong = [j for j, o in prim if o['delta'] >= 0.05 and o[bk][0] > 0]
    flat = [j for j, o in prim if o['delta'] < 0.03 or (o['ci95'][0] <= 0 <= o['ci95'][1])]
    best = max(o['var'] for _, o in prim)
    if len(strong) >= 2 and best >= 0.72: verdict = 'RUBRIC-BOUND: the generic-prompt ceiling was a rubric problem'
    elif len(flat) == len(prim): verdict = 'ROBUST: the blind-regime ceiling survives a definition-informed rubric'
    else: verdict = 'MIXED: report as is; neither pre-registered reading is met'
    print(f'PRE-REGISTERED VERDICT: {verdict}')
    print(f'   judges meeting the strong criterion: {strong or "none"}; judges flat: {flat or "none"}; best D1 blind AUROC {best:.3f}')
    result['verdict'] = {'text': verdict, 'strong': strong, 'flat': flat, 'best_D1_blind': best}
out = RES / 'rubric_effect'; out.mkdir(exist_ok=True)
(out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'\nwrote {out}/results.json')
