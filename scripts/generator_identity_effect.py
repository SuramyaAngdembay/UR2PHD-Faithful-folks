"""E5: does a judge's score encode WHO WROTE the trace more than WHETHER IT IS UNFAITHFUL?

EXPLORATORY, and labelled so deliberately. This was NOT the pre-registered hypothesis in
self-preference-spec.md. It is what that spec's E2m falsification test revealed: the matched
own-vs-other offsets were large for non-self judges too, which kills the self-preference reading
and points at generator identity instead. Order of events recorded in
notes/2026-09-19-generator-identity-bias.md. No claim here may be promoted to a headline without a
fresh spec and, ideally, a held-out benchmark.

Both effects are measured the SAME way so the ratio means something: as a deviation from the
within-question mean, on the same questions, in the blind (incorrect-answer) regime.

  LABEL effect     within a question, mean judge score on ft2 traces minus mean on ft1 traces.
                   This is what the judge is supposed to detect.
  GENERATOR spread within a question AND a fixed true label, the max-minus-min across generators of
                   the mean deviation. This is what the judge is not supposed to be responding to.

Run: python scripts/generator_identity_effect.py   Out: results/self_preference/generator_identity.json
"""
import json, hashlib, collections
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]; RES = ROOT / 'results'
B, SEED = 2000, 0

rf = json.load(open(RES / 'rigorous_features.json')); fr = json.load(open(RES / 'feat_rids.json'))
tx = json.load(open(RES / 'faithcot_texts.json'))
assert len(rf) == len(fr) == 1304
assert all(a['ft'] == b['ft'] and a['n_steps'] == b['n_steps'] for a, b in zip(rf, fr)), 'join broken'

rows = []
for f, r in zip(rf, fr):
    d, g, fn = r['rid'].split('/')
    t = tx.get(r['rid']) or {}
    rows.append({'rid': r['rid'], 'gen': g, 'q': f'{d}/{fn}', 'ft': f['ft'],
                 'w': len((t.get('text') or '').split())})
byq = collections.defaultdict(list)
for r in rows: byq[r['q']].append(r)
GENS = sorted({r['gen'] for r in rows})
QS = sorted(byq)

def per_question(sc, qs):
    """Per question: (label contribution, {gen: deviation contributions}). Blind regime only."""
    lab, dev = {}, {}
    for q in qs:
        items = byq[q]
        a = [sc[r['rid']] for r in items if r['ft'] == 2 and r['rid'] in sc]
        b = [sc[r['rid']] for r in items if r['ft'] == 1 and r['rid'] in sc]
        if a and b: lab[q] = float(np.mean(a) - np.mean(b))
        d = collections.defaultdict(list)
        for ft in (1, 2):
            grp = [r for r in items if r['ft'] == ft and r['rid'] in sc]
            if len(grp) < 2: continue
            m = float(np.mean([sc[r['rid']] for r in grp]))
            for r in grp: d[r['gen']].append(sc[r['rid']] - m)
        if d: dev[q] = {g: v for g, v in d.items()}
    return lab, dev

def stats(qs, lab, dev):
    L = [lab[q] for q in qs if q in lab]
    if not L: return None
    agg = collections.defaultdict(list)
    for q in qs:
        for g, v in dev.get(q, {}).items(): agg[g].extend(v)
    means = {g: float(np.mean(v)) for g, v in agg.items() if v}
    if len(means) < 2: return None
    return float(np.mean(L)), max(means.values()) - min(means.values()), means

out = {'endpoint': 'E5 (EXPLORATORY -- not pre-registered; see spec amendment note)',
       'regime': 'blind_ft1v2', 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'judges': {}}
rng_master = np.random.default_rng(SEED)
BOOT = [rng_master.integers(0, len(QS), len(QS)) for _ in range(B)]   # shared draws across judges

print(f"{'judge':10s} {'label effect':>22s} {'generator spread':>22s} {'ratio':>18s}")
for f in sorted(RES.glob('judge_raw_*.jsonl')):
    tag = f.stem.replace('judge_raw_', '')
    sc = {}; n_rows = 0
    for line in f.open():
        d = json.loads(line); n_rows += 1
        if d.get('score') is not None: sc[d['rid']] = float(d['score'])
    # Parse RATE, not an absolute count: an absolute 1300 threshold silently dropped
    # Olmo-3-7B (1299 scored of 1304) for five unparsed rows, which is not a reason to exclude it.
    # The real exclusion criterion is heavy, non-random missingness -- see the Qwen2.5-3B base arms.
    if len(sc) / max(n_rows, 1) < 0.95: 
        print(f'  skipping {tag}: parse rate {len(sc)/max(n_rows,1):.3f}')
        continue
    lab, dev = per_question(sc, QS)
    base = stats(QS, lab, dev)
    if base is None: continue
    L0, S0, means = base
    bl, bs, br = [], [], []
    for pick in BOOT:
        qs = [QS[i] for i in pick]
        s = stats(qs, lab, dev)
        if s is None: continue
        bl.append(s[0]); bs.append(s[1])
        if abs(s[0]) > 1e-9: br.append(s[1] / s[0])
    ci = lambda v: [round(float(np.percentile(v, 2.5)), 2), round(float(np.percentile(v, 97.5)), 2)]
    print(f'{tag:10s} {f"{L0:6.1f} {ci(bl)}":>22s} {f"{S0:6.1f} {ci(bs)}":>22s} '
          f'{f"{S0/L0:5.2f} {ci(br)}" if abs(L0)>1e-9 else "n/a":>18s}')
    out['judges'][tag] = {'label_effect': round(L0, 3), 'label_effect_ci95': ci(bl),
                          'generator_spread': round(S0, 3), 'generator_spread_ci95': ci(bs),
                          'ratio': round(S0 / L0, 3) if abs(L0) > 1e-9 else None,
                          'ratio_ci95': ci(br) if br else None,
                          'per_generator_deviation': {g: round(v, 3) for g, v in sorted(means.items(), key=lambda x: x[1])},
                          'n_questions_label': len(lab)}

o = RES / 'self_preference'; o.mkdir(parents=True, exist_ok=True)
(o / 'generator_identity.json').write_text(json.dumps(out, indent=2) + '\n')
print(f'\nwrote {o}/generator_identity.json')
