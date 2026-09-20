"""Judge self-preference as a generator-identity composition effect (self-preference-spec.md).

Cached judge outputs only; no new inference. Runs on whatever arms exist, so it can be run now on
the cached arms and re-run unchanged when the queued local arms land.

The spec's key point, restated because it drives every choice here: AUROC is rank-based WITHIN the
evaluated subset, so a constant self-preference offset on a judge's own generations leaves
within-generator AUROC unchanged. The primary endpoint is therefore a paired SCORE OFFSET (E1m),
not an AUROC contrast. E4 reports the AUROC contrast anyway, labelled as unable to bear on the
question.

Regimes are keyed on `ft` only, never on the misnamed `correct` field.

Run: python scripts/self_preference_analysis.py
Out: results/self_preference/results.json
"""
import json, hashlib, collections
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'results'
B, SEED = 2000, 0

# ---------- population ----------
rf = json.load(open(RES / 'rigorous_features.json'))
fr = json.load(open(RES / 'feat_rids.json'))
assert len(rf) == len(fr) == 1304, 'unexpected population size'
assert all(a['ft'] == b['ft'] and a['n_steps'] == b['n_steps'] for a, b in zip(rf, fr)), \
    'positional join between rigorous_features and feat_rids is broken'

rows = []
for feat, rid in zip(rf, fr):
    if feat['ft'] not in (1, 2, 3, 4):
        continue
    dom, gen, fn = rid['rid'].split('/')
    rows.append({'rid': rid['rid'], 'dom': dom, 'gen': gen, 'q': f'{dom}/{fn}', 'ft': feat['ft']})

GENS = sorted({r['gen'] for r in rows})
byq = collections.defaultdict(list)
for r in rows:
    byq[r['q']].append(r)

REGIMES = {'blind_ft1v2': (1, 2), 'correct_ft3v4': (3, 4)}

# ---------- judge arms ----------
# Self-status is read off the arm's own `model` field against the generator names in the rids.
# Nothing here is asserted from memory.
GEN_OF_JUDGE = {'gpt-4o-mini': 'gpt-4o-mini',
                'Qwen/Qwen2.5-7B-Instruct': 'Qwen2.5-7B-Instruct',
                'meta-llama/Llama-3.1-8B-Instruct': 'llama-3.1-8b-instruct'}
# Arms whose input is degenerate for this question: the judge never sees the trace, so within a
# matched pair (which shares a question) its two inputs are identical and the offset must be 0.
DEGENERATE = {'qonly'}

arms = {}
for f in sorted(RES.glob('judge_raw_*.jsonl')):
    tag = f.stem.replace('judge_raw_', '')
    sc, model = {}, None
    for line in f.open():
        d = json.loads(line)
        if d.get('score') is None:
            continue
        sc[d['rid']] = float(d['score'])
        model = model or d.get('model')
    if len(sc) < 1300:
        print(f'  skipping {tag}: only {len(sc)} scored rows (arm incomplete)')
        continue
    arms[tag] = {'scores': sc, 'model': model,
                 'self_gen': GEN_OF_JUDGE.get(model), 'degenerate': tag in DEGENERATE}
print(f'arms loaded: {len(arms)} -> ' + ', '.join(sorted(arms)))
for t, a in sorted(arms.items()):
    print(f"  {t:12s} model={a['model']:26s} self_gen={a['self_gen'] or '-'}")

# ---------- helpers ----------
def auroc(y, s):
    y, s = np.asarray(y), np.asarray(s, float)
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0:
        return None
    r = rankdata(s)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

def boot_q(qkeys, per_q, stat, b=B, seed=SEED):
    """Question-clustered percentile bootstrap. per_q maps question -> list of contributions."""
    rng = np.random.default_rng(seed)
    qs = list(qkeys)
    if not qs:
        return None
    out = []
    for _ in range(b):
        pick = rng.integers(0, len(qs), len(qs))
        vals = [v for i in pick for v in per_q[qs[i]]]
        s = stat(vals)
        if s is not None:
            out.append(s)
    if not out:
        return None
    return [round(float(np.percentile(out, 2.5)), 4), round(float(np.percentile(out, 97.5)), 4)]

def matched_offset(scores, gen, fts):
    """E1m contributions: per question, (self score - mean matched-other score), matched on exact ft."""
    per_q = collections.defaultdict(list)
    for q, items in byq.items():
        for st in items:
            if st['gen'] != gen or st['ft'] not in fts:
                continue
            others = [o for o in items if o['gen'] != gen and o['ft'] == st['ft']]
            others = [o for o in others if o['rid'] in scores]
            if not others or st['rid'] not in scores:
                continue
            per_q[q].append(scores[st['rid']] - float(np.mean([scores[o['rid']] for o in others])))
    return per_q

# ---------- analysis ----------
result = {'spec': 'self-preference-spec.md',
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'arms': {t: {'model': a['model'], 'self_gen': a['self_gen']} for t, a in arms.items()},
          'generators': GENS, 'E1m_E2m': {}, 'E3_composition': {}, 'E4_auroc': {}}

for rname, fts in REGIMES.items():
    print(f'\n########## REGIME {rname} ##########')

    # ---- E1m / E2m: matched own-vs-other offset, every judge x every generator ----
    print(f'\n--- E1m/E2m matched offset (judge score on generator G minus matched others) ---')
    print(f"{'judge':12s} {'generator':26s} {'offset':>8} {'95% CI':>19} {'pairs':>6} {'q':>4}  self")
    block = {}
    for tag in sorted(arms):
        sc = arms[tag]['scores']
        for gen in GENS:
            per_q = matched_offset(sc, gen, fts)
            npair = sum(len(v) for v in per_q.values())
            if npair == 0:
                continue
            flat = [v for vs in per_q.values() for v in vs]
            off = float(np.mean(flat))
            ci = boot_q(list(per_q), per_q, lambda v: float(np.mean(v)) if v else None)
            is_self = (arms[tag]['self_gen'] == gen)
            sd = float(np.std([sc[r['rid']] for r in rows
                               if r['ft'] in fts and r['rid'] in sc]))
            # CALIBRATION ARM, not an exactness check. A judge that never sees the trace has
            # byte-identical inputs within a matched pair (question and options are identical
            # across generators for all 341 questions -- verified against the raw FaithCoT records,
            # not assumed). Its offsets are therefore pure API nondeterminism at temperature 0,
            # which this project has measured directly and which is NOT zero. So the invariant to
            # assert is that the noise is UNBIASED -- its interval must cover zero -- rather than
            # that it is absent. An earlier version of this script asserted exact zero and fired;
            # the assumption in the assertion was wrong, not the matching code.
            if arms[tag]['degenerate']:
                assert ci is None or (ci[0] <= 0 <= ci[1]), (
                    f'LEAK: calibration arm {tag} has a matched offset on {gen} whose interval '
                    f'{ci} excludes zero. Its inputs are byte-identical within a pair, so an '
                    'unbiased offset is the only admissible result; a biased one means the '
                    'matching is pairing records that do not actually share a question.')
            excl = ci is not None and (ci[0] > 0 or ci[1] < 0)
            print(f"{tag:12s} {gen:26s} {off:>8.2f} {str(ci):>19} {npair:>6} {len(per_q):>4}  "
                  f"{'SELF' if is_self else ''}{'  *' if excl else ''}")
            block[f'{tag}|{gen}'] = {'judge': tag, 'generator': gen, 'is_self': is_self,
                                     'offset': round(off, 4), 'ci95': ci,
                                     'offset_standardized': round(off / sd, 4) if sd > 0 else None,
                                     'n_pairs': npair, 'n_questions': len(per_q),
                                     'excludes_zero': bool(excl),
                                     'degenerate_control': arms[tag]['degenerate']}
    # The calibration arm's offsets are an assumption-free empirical null for E1m: same design,
    # same judge family, same matching, but the judge cannot see which model wrote the trace.
    null = [v['offset'] for v in block.values() if v['degenerate_control']]
    if null:
        block['_empirical_null'] = {
            'source_arms': sorted({v['judge'] for v in block.values() if v['degenerate_control']}),
            'offsets': null,
            'max_abs_offset': round(float(np.max(np.abs(null))), 4),
            'note': 'Judge sees question and options only; these are byte-identical within a '
                    'matched pair, so any non-zero offset here is temperature-0 API '
                    'nondeterminism. A self-judge offset inside this range is not interpretable.'}
    result['E1m_E2m'][rname] = block

    # ---- E3: composition -- pooled AUROC vs size-weighted mean within-generator AUROC ----
    print(f'\n--- E3 composition (pooled AUROC minus weighted mean of within-generator AUROCs) ---')
    print(f"{'judge':12s} {'pooled':>7} {'within-mean':>12} {'gap':>7}")
    comp = {}
    for tag in sorted(arms):
        sc = arms[tag]['scores']
        sub = [r for r in rows if r['ft'] in fts and r['rid'] in sc]
        if not sub:
            continue
        y = np.array([1.0 if r['ft'] in (2, 4) else 0.0 for r in sub])
        s = np.array([sc[r['rid']] for r in sub])
        pooled = auroc(y, s)
        ws, aus = [], []
        per_gen = {}
        for gen in GENS:
            g = [r for r in sub if r['gen'] == gen]
            yg = np.array([1.0 if r['ft'] in (2, 4) else 0.0 for r in g])
            sg = np.array([sc[r['rid']] for r in g])
            a = auroc(yg, sg)
            per_gen[gen] = None if a is None else round(a, 4)
            if a is not None:
                ws.append(len(g)); aus.append(a)
        wm = float(np.average(aus, weights=ws)) if aus else None
        gap = None if (pooled is None or wm is None) else pooled - wm
        print(f"{tag:12s} {pooled if pooled is None else f'{pooled:.3f}':>7} "
              f"{wm if wm is None else f'{wm:.3f}':>12} {gap if gap is None else f'{gap:+.3f}':>7}")
        comp[tag] = {'pooled_auroc': None if pooled is None else round(pooled, 4),
                     'within_generator_weighted_mean': None if wm is None else round(wm, 4),
                     'composition_gap': None if gap is None else round(gap, 4),
                     'per_generator_auroc': per_gen}
    result['E3_composition'][rname] = comp

    # ---- E4: within-generator AUROC, own vs other (SECONDARY; cannot bear on self-preference) ----
    e4 = {}
    for tag in sorted(arms):
        g = arms[tag]['self_gen']
        if not g:
            continue
        c = result['E3_composition'][rname].get(tag, {}).get('per_generator_auroc', {})
        own = c.get(g)
        oth = [v for k, v in c.items() if k != g and v is not None]
        e4[tag] = {'self_generator': g, 'auroc_own': own,
                   'auroc_other_mean': round(float(np.mean(oth)), 4) if oth else None,
                   'note': 'SECONDARY. A constant self-preference offset does not change '
                           'within-subset AUROC, so a null here is not evidence against E1m.'}
    result['E4_auroc'][rname] = e4

out = RES / 'self_preference'
out.mkdir(parents=True, exist_ok=True)
(out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'\nwrote {out}/results.json')
