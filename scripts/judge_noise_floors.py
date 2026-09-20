"""Within-model judge noise: greedy determinism and sampled-seed spread.

Two questions the local arms answer that the API arms could not:

  1. GREEDY DETERMINISM. Local greedy decoding should be bit-reproducible. qwen3_8b vs
     qwen3_8b_greedy2 are the same model, same prompt, same traces, run twice. Any disagreement is
     a bug or nondeterministic kernels, not sampling. Contrast with the API judges, where two
     identical temperature-0 configurations disagreed on 16-26% of items.
  2. SAMPLED-SEED SPREAD. Three seeds per model at temperature 0.7 give a within-model noise floor
     for AUROC, which is what the cross-judge capability table most lacks.

Run: python scripts/judge_noise_floors.py   Out: results/judge_noise_floors.json
"""
import json, hashlib, collections
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]; RES = ROOT / 'results'
rf = json.load(open(RES / 'rigorous_features.json')); fr = json.load(open(RES / 'feat_rids.json'))
assert len(rf) == len(fr) == 1304
rows = [{'rid': r['rid'], 'ft': f['ft']} for f, r in zip(rf, fr) if f['ft'] in (1, 2, 3, 4)]

def load(tag):
    f = RES / f'judge_raw_{tag}.jsonl'
    if not f.exists(): return None
    return {json.loads(l)['rid']: json.loads(l).get('score') for l in f.open()}

def auroc(y, s):
    y, s = np.asarray(y), np.asarray(s, float)
    ok = ~np.isnan(s); y, s = y[ok], s[ok]
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0: return None
    r = rankdata(s)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

def regime_auroc(sc, fts):
    sub = [r for r in rows if r['ft'] in fts]
    y = np.array([1.0 if r['ft'] in (2, 4) else 0.0 for r in sub])
    s = np.array([sc.get(r['rid']) if sc.get(r['rid']) is not None else np.nan for r in sub], float)
    return auroc(y, s)

out = {'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'greedy_determinism': {}, 'seed_spread': {}}

# ---- 1. greedy determinism ----
print('=== GREEDY DETERMINISM: same model, same prompt, run twice ===')
a, b = load('qwen3_8b'), load('qwen3_8b_greedy2')
if a and b:
    common = [r for r in a if r in b and a[r] is not None and b[r] is not None]
    same = sum(1 for r in common if a[r] == b[r])
    d = np.array([abs(a[r] - b[r]) for r in common])
    print(f'  Qwen3-8B greedy x2: {len(common)} comparable items')
    print(f'    identical scores : {same}/{len(common)} = {same/len(common)*100:.2f}%')
    print(f'    mean |delta|     : {d.mean():.3f}   max {d.max():.0f}')
    for rn, fts in (('blind', (1, 2)), ('correct', (3, 4))):
        print(f'    AUROC {rn:8s}: run1 {regime_auroc(a,fts):.4f}  run2 {regime_auroc(b,fts):.4f}  '
              f'delta {abs(regime_auroc(a,fts)-regime_auroc(b,fts)):.4f}')
    out['greedy_determinism'] = {'model': 'Qwen3-8B', 'n': len(common),
        'identical_frac': round(same/len(common), 5), 'mean_abs_delta': round(float(d.mean()), 4),
        'max_abs_delta': int(d.max()),
        'auroc_blind': [round(regime_auroc(a,(1,2)),4), round(regime_auroc(b,(1,2)),4)],
        'auroc_correct': [round(regime_auroc(a,(3,4)),4), round(regime_auroc(b,(3,4)),4)]}

# ---- 2. sampled-seed spread ----
print('\n=== SAMPLED-SEED SPREAD (temp 0.7, seeds 0/1/2) vs the greedy arm ===')
MODELS = {'qwen3_8b': 'Qwen3-8B', 'qwen25_7b': 'Qwen2.5-7B-Instruct',
          'llama31_8b': 'Llama-3.1-8B-Instruct', 'llama3_8b': 'Meta-Llama-3-8B-Instruct',
          'llama32_3b': 'Llama-3.2-3B-Instruct', 'olmo3_7b': 'Olmo-3-7B-Instruct',
          'qwen25_3b_instruct': 'Qwen2.5-3B-Instruct'}
print(f"{'model':28s} {'regime':8s} {'greedy':>7} {'seed AUROCs':>26} {'spread':>7} {'sd':>6}")
for tag, label in MODELS.items():
    g = load(tag)
    seeds = [load(f'{tag}_s{i}') for i in range(3)]
    if g is None or any(s is None for s in seeds): 
        print(f'{label:28s}  (incomplete, skipped)'); continue
    rec = {}
    for rn, fts in (('blind', (1, 2)), ('correct', (3, 4))):
        ga = regime_auroc(g, fts); sa = [regime_auroc(s, fts) for s in seeds]
        spread = max(sa) - min(sa); sd = float(np.std(sa, ddof=1))
        print(f'{label:28s} {rn:8s} {ga:7.3f} {str([round(x,3) for x in sa]):>26} {spread:7.3f} {sd:6.3f}')
        rec[rn] = {'greedy': round(ga, 4), 'seeds': [round(x, 4) for x in sa],
                   'spread': round(spread, 4), 'sd': round(sd, 4)}
    out['seed_spread'][label] = rec

allsp = [v[r]['spread'] for v in out['seed_spread'].values() for r in ('blind', 'correct')]
if allsp:
    print(f'\nseed spread across all model x regime cells: median {np.median(allsp):.3f}, max {max(allsp):.3f}')
    print(f'API judge run-to-run noise (gpt-5.2 identical config): 0.023')
    out['summary'] = {'median_seed_spread': round(float(np.median(allsp)), 4),
                      'max_seed_spread': round(float(max(allsp)), 4),
                      'api_noise_reference': 0.023}
(RES / 'judge_noise_floors.json').write_text(json.dumps(out, indent=2) + '\n')
print(f"\nwrote {RES}/judge_noise_floors.json")
