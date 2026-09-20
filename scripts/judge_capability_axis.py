"""Blind vs correct regime AUROC across every distinct judge model.

Tests the reading proposed in notes/2026-09-19-generator-identity-bias.md: blind-regime
performance is flat in judge capability, and capability buys the CORRECT regime only. That was
based on three judges; this runs it across every judge arm available.

EXPLORATORY. Judge "capability" is not measured here -- model size and family are crude proxies and
these models differ in more than capability (instruct-tuning, quantization, vendor). The table
supports a qualitative reading, not a scaling law.

EXCLUSIONS are applied and reported, never silent:
  - qwen25_3b: `Qwen/Qwen2.5-3B` is a BASE model, not instruct-tuned, and 265/1304 (20.3%) of its
    outputs failed to parse. The missingness is strongly non-random -- 43.2% on LogiQA against 1.4%
    on AQuA, and differential by generator (25.8% gemini vs 16.5% gpt-4o-mini) -- so its AUROC is
    computed on a subset whose domain and generator composition differ from every other arm's.
    Since generator identity is exactly the covariate under study here, that is disqualifying.
  - prompt/ablation variants of a model already present (promptB, cotonly, qonly, gpt52B,
    gpt52rep) are excluded from the capability axis and reported separately, since they vary the
    PROMPT rather than the judge.

Run: python scripts/judge_capability_axis.py   Out: results/judge_capability_axis.json
"""
import json, hashlib, collections
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]; RES = ROOT / 'results'
MIN_PARSE_RATE = 0.95

rf = json.load(open(RES / 'rigorous_features.json')); fr = json.load(open(RES / 'feat_rids.json'))
assert len(rf) == len(fr) == 1304
assert all(a['ft'] == b['ft'] and a['n_steps'] == b['n_steps'] for a, b in zip(rf, fr)), 'join broken'
rows = []
for f, r in zip(rf, fr):
    if f['ft'] not in (1, 2, 3, 4): continue
    d, g, fn = r['rid'].split('/')
    rows.append({'rid': r['rid'], 'q': f'{d}/{fn}', 'gen': g, 'ft': f['ft']})

# One arm per distinct JUDGE MODEL, prompt held at the default rubric.
AXIS = {'mini': 'gpt-4o-mini', 'gpt4o': 'gpt-4o', 'gpt52': 'gpt-5.2',
        'qwen25_7b': 'Qwen2.5-7B-Instruct', 'qwen3_8b': 'Qwen3-8B',
        'llama31_8b': 'Llama-3.1-8B-Instruct', 'llama3_8b': 'Meta-Llama-3-8B-Instruct',
        'llama32_3b': 'Llama-3.2-3B-Instruct', 'olmo3_7b': 'Olmo-3-7B-Instruct',
        'qwen25_3b_instruct': 'Qwen2.5-3B-Instruct'}

def auroc(y, s):
    y, s = np.asarray(y), np.asarray(s, float)
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0: return None
    r = rankdata(s)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

def boot(sub, y, s, B=2000, seed=0):
    byq = collections.defaultdict(list)
    for i, r in enumerate(sub): byq[r['q']].append(i)
    qs = list(byq); rng = np.random.default_rng(seed); out = []
    for _ in range(B):
        idx = [i for k in rng.integers(0, len(qs), len(qs)) for i in byq[qs[k]]]
        a = auroc(y[idx], s[idx])
        if a is not None: out.append(a)
    return [round(float(np.percentile(out, 2.5)), 3), round(float(np.percentile(out, 97.5)), 3)]

out = {'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'status': 'EXPLORATORY; capability is proxied by size/family, not measured',
       'judges': {}, 'excluded': {}}
print(f"{'judge model':28s} {'blind':>7} {'95% CI':>16} {'correct':>8} {'95% CI':>16} {'gap':>7} {'parse':>7}")
for tag, label in AXIS.items():
    f = RES / f'judge_raw_{tag}.jsonl'
    if not f.exists():
        out['excluded'][label] = 'arm not yet available'; continue
    sc, n_tot = {}, 0
    for line in f.open():
        d = json.loads(line); n_tot += 1
        if d.get('score') is not None: sc[d['rid']] = float(d['score'])
    rate = len(sc) / max(n_tot, 1)
    if rate < MIN_PARSE_RATE:
        out['excluded'][label] = f'parse rate {rate:.3f} below {MIN_PARSE_RATE}; non-random missingness'
        print(f'{label:28s}  EXCLUDED (parse rate {rate:.1%})')
        continue
    res = {}
    for rname, fts in (('blind', (1, 2)), ('correct', (3, 4))):
        sub = [r for r in rows if r['ft'] in fts and r['rid'] in sc]
        y = np.array([1.0 if r['ft'] in (2, 4) else 0.0 for r in sub])
        s = np.array([sc[r['rid']] for r in sub])
        a = auroc(y, s)
        res[rname] = {'auroc': None if a is None else round(a, 4), 'ci95': boot(sub, y, s), 'n': len(sub)}
    gap = res['correct']['auroc'] - res['blind']['auroc']
    res['gap'] = round(gap, 4); res['parse_rate'] = round(rate, 4)
    out['judges'][label] = res
    print(f"{label:28s} {res['blind']['auroc']:7.3f} {str(res['blind']['ci95']):>16} "
          f"{res['correct']['auroc']:8.3f} {str(res['correct']['ci95']):>16} {gap:+7.3f} {rate:7.1%}")

(RES / 'judge_capability_axis.json').write_text(json.dumps(out, indent=2) + '\n')
if out['excluded']:
    print('\nEXCLUDED:')
    for k, v in out['excluded'].items(): print(f'  {k:28s} {v}')
print(f"\nwrote {RES}/judge_capability_axis.json")
