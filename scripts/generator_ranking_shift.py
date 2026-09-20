"""Does pooling across generators change the DETECTOR RANKING?

The actionable form of the generator-identity finding. If a benchmark's leaderboard pools across
generator models, and judge scores carry a large generator-identity offset, then the pooled ranking
may partly reflect generator style rather than detection. This tests that directly on our own data,
which is the honest place to test it first.

Compares, for each detector, the POOLED AUROC against the size-weighted mean of WITHIN-GENERATOR
AUROCs, then compares the two induced rankings by Spearman correlation and by counting inversions.

EXPLORATORY. Population is the complete-feature subset so that metric signals and judges are
scored on identical rows; that is a smaller and differently-composed set than the full 1,304.

Run: python scripts/generator_ranking_shift.py   Out: results/generator_ranking_shift.json
"""
import json, hashlib, collections, itertools
from pathlib import Path
import numpy as np
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[1]; RES = ROOT / 'results'
rf = json.load(open(RES / 'rigorous_features.json')); fr = json.load(open(RES / 'feat_rids.json'))
assert len(rf) == len(fr) == 1304

JUDGES = {'mini': 'judge gpt-4o-mini', 'gpt4o': 'judge gpt-4o', 'gpt52': 'judge gpt-5.2',
          'qwen25_7b': 'judge Qwen2.5-7B', 'qwen3_8b': 'judge Qwen3-8B',
          'llama31_8b': 'judge Llama-3.1-8B', 'llama3_8b': 'judge Meta-Llama-3',
          'llama32_3b': 'judge Llama-3.2-3B', 'olmo3_7b': 'judge Olmo-3-7B'}
# sign +1 means higher = more unfaithful; -1 flips a metric whose natural direction is inverted.
METRICS = {'soft': -1, 'hard': -1, 'avg_impact': +1, 'dag_lin': +1, 'dag_maxlb': +1,
           'nli_n_unsup': +1, 'nli_min_ent': -1, 'nli_mean_ent': -1, 'n_steps': +1}

jsc = {}
for tag in JUDGES:
    f = RES / f'judge_raw_{tag}.jsonl'
    if not f.exists(): continue
    d = {}
    n = 0
    for line in f.open():
        o = json.loads(line); n += 1
        if o.get('score') is not None: d[o['rid']] = float(o['score'])
    if len(d) / max(n, 1) >= 0.95: jsc[tag] = d

rows = []
for feat, rid in zip(rf, fr):
    if feat['ft'] not in (1, 2, 3, 4): continue
    dom, gen, fn = rid['rid'].split('/')
    r = {'rid': rid['rid'], 'gen': gen, 'ft': feat['ft']}
    if any(feat.get(m) is None for m in METRICS): continue          # complete-feature only
    if any(rid['rid'] not in jsc[t] for t in jsc): continue          # scored by every judge
    for m in METRICS: r[m] = float(feat[m])
    for t in jsc: r[t] = jsc[t][rid['rid']]
    rows.append(r)
print(f'complete-feature rows scored by all {len(jsc)} judges: {len(rows)}')
GENS = sorted({r['gen'] for r in rows})

def auroc(y, s):
    y, s = np.asarray(y), np.asarray(s, float)
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0: return None
    rk = rankdata(s)
    return float((rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

DET = {**{k: (k, s) for k, s in METRICS.items()}, **{v: (k, +1) for k, v in JUDGES.items() if k in jsc}}
out = {'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'n_rows': len(rows), 'regimes': {}}

for rname, fts in (('blind_ft1v2', (1, 2)), ('correct_ft3v4', (3, 4))):
    sub = [r for r in rows if r['ft'] in fts]
    y = np.array([1.0 if r['ft'] in (2, 4) else 0.0 for r in sub])
    pooled, within = {}, {}
    for label, (key, sgn) in DET.items():
        s = np.array([r[key] * sgn for r in sub], float)
        a = auroc(y, s)
        if a is None: continue
        pooled[label] = a
        ws, aus = [], []
        for g in GENS:
            idx = [i for i, r in enumerate(sub) if r['gen'] == g]
            ag = auroc(y[idx], s[idx])
            if ag is not None: ws.append(len(idx)); aus.append(ag)
        within[label] = float(np.average(aus, weights=ws)) if aus else None
    labels = [l for l in pooled if within.get(l) is not None]
    pr = {l: r for l, r in zip(labels, rankdata([-pooled[l] for l in labels]))}
    wr = {l: r for l, r in zip(labels, rankdata([-within[l] for l in labels]))}
    rho = spearmanr([pr[l] for l in labels], [wr[l] for l in labels]).statistic
    inv = sum(1 for a, b in itertools.combinations(labels, 2)
              if (pooled[a] - pooled[b]) * (within[a] - within[b]) < 0)
    npairs = len(labels) * (len(labels) - 1) // 2
    print(f'\n===== {rname}  n={len(sub)}  detectors={len(labels)} =====')
    print(f"{'detector':22s} {'pooled':>7} {'within':>7} {'gap':>7} {'rank p':>7} {'rank w':>7} {'move':>5}")
    for l in sorted(labels, key=lambda x: -pooled[x]):
        mv = int(pr[l] - wr[l])
        print(f'{l:22s} {pooled[l]:7.3f} {within[l]:7.3f} {pooled[l]-within[l]:+7.3f} '
              f'{pr[l]:7.0f} {wr[l]:7.0f} {mv:+5d}')
    print(f'  Spearman(pooled rank, within rank) = {rho:.4f}')
    print(f'  pairwise inversions = {inv} of {npairs} ({inv/npairs*100:.1f}%)')
    out['regimes'][rname] = {'n': len(sub), 'spearman_rank_corr': round(float(rho), 4),
        'pairwise_inversions': inv, 'pairs': npairs,
        'detectors': {l: {'pooled': round(pooled[l], 4), 'within_generator_weighted': round(within[l], 4),
                          'composition_gap': round(pooled[l] - within[l], 4),
                          'rank_pooled': int(pr[l]), 'rank_within': int(wr[l])} for l in labels}}

(RES / 'generator_ranking_shift.json').write_text(json.dumps(out, indent=2) + '\n')
print(f"\nwrote {RES}/generator_ranking_shift.json")
