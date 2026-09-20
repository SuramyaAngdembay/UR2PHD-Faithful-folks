"""Step 1: per-regime competitive gap on FaithCoT (step1-competitive-gap-spec.md).

Cached data only; no new inference. Regimes keyed on `ft`, NEVER on the misnamed `correct` field
(see the hazard note in the spec). Join integrity is asserted, not assumed.
"""
import json, hashlib, re, zipfile
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
TEXTS = Path(__file__).resolve().parents[1] / 'results/faithcot_texts.json'

def auroc(y, s):
    y = np.asarray(y); s = np.asarray(s, float)
    ok = ~np.isnan(s); y, s = y[ok], s[ok]
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0: return None, 0
    r = rankdata(s)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)), len(y)

# ---- load and JOIN, with assertions ----
rf = json.load(open(ROOT / 'results/rigorous_features.json'))
fr = json.load(open(ROOT / 'results/feat_rids.json'))
assert len(rf) == len(fr) == 1304
assert all(a['ft'] == b['ft'] and a['n_steps'] == b['n_steps'] for a, b in zip(rf, fr)), 'positional join broken'
jj = json.load(open(ROOT / 'results/judge_join.json'))
rows = []
for feat, rid in zip(rf, fr):
    if feat['ft'] not in (1, 2, 3, 4): continue
    r = dict(feat); r['rid'] = rid['rid']
    j = jj.get(r['rid'])
    if j is not None:
        assert j['ft'] == r['ft'], f"JOIN MISMATCH on ft for {r['rid']}"   # independent check of the positional join
        r['judgeA'] = j.get('judgeA')
    rows.append(r)
print(f'joined rows: {len(rows)}; judge scores attached: {sum(1 for r in rows if r.get("judgeA") is not None)}')

# ---- attach trace text from the public release for length + text baselines ----
texts = json.load(open(TEXTS))
miss = 0
for r in rows:
    t = texts.get(r['rid'])
    if t is None: miss += 1; r['text'] = None; r['question'] = None; continue
    r['text'] = t['text']; r['question'] = t['question']
    r['words'] = len(r['text'].split()); r['chars'] = len(r['text'])
print(f'traces without text: {miss}')

# ---- supervised text baseline: question-grouped CV, fixed hyperparameters ----
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline

def text_baseline(sub, target):
    X = [r['text'] or '' for r in sub]; y = np.array([target(r) for r in sub])
    g = [r['question'] or r['rid'] for r in sub]
    if len(set(y)) < 2: return None
    oof = np.full(len(y), np.nan)
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups=g):
        if len(set(y[tr])) < 2: continue
        m = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=50000),
                          LogisticRegression(C=1.0, solver='liblinear', class_weight='balanced', max_iter=1000))
        m.fit([X[i] for i in tr], y[tr])
        oof[te] = m.predict_proba([X[i] for i in te])[:, 1]
    return oof

SIGNALS = ['soft', 'hard', 'avg_impact', 'dag_lin', 'dag_maxlb',
           'nli_n_unsup', 'nli_min_ent', 'nli_mean_ent', 'nli_frac_con',
           'n_steps', 'words', 'chars', 'judgeA']
STRATA = {'INCORRECT regime (ft1v2)': (lambda r: r['ft'] in (1, 2), lambda r: 1.0 if r['ft'] == 2 else 0.0),
          'CORRECT regime (ft3v4)':   (lambda r: r['ft'] in (3, 4), lambda r: 1.0 if r['ft'] == 4 else 0.0),
          'POOLED':                   (lambda r: True,              lambda r: 1.0 if r['ft'] in (2, 4) else 0.0)}

def boot_ci(sub, y, s, B=2000, seed=0):
    byq = defaultdict(list)
    for i, r in enumerate(sub): byq[r['question'] or r['rid']].append(i)
    qs = list(byq); rng = np.random.default_rng(seed); out = []
    while len(out) < B:
        idx = [i for q in rng.integers(0, len(qs), len(qs)) for i in byq[qs[q]]]
        a, n = auroc(y[idx], s[idx])
        if a is not None: out.append(a)
    return [round(float(np.percentile(out, 2.5)), 3), round(float(np.percentile(out, 97.5)), 3)]

result = {'spec': 'step1-competitive-gap-spec.md',
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'strata': {}}
for sname, (filt, target) in STRATA.items():
    sub = [r for r in rows if filt(r)]
    y = np.array([target(r) for r in sub])
    print(f'\n===== {sname}  n={len(sub)}  unfaithful={int(y.sum())} =====')
    print(f"{'detector':22s} {'AUROC':>7} {'95% CI':>16} {'n':>6}")
    block = {'n': len(sub), 'unfaithful': int(y.sum()), 'detectors': {}}
    entries = []
    for sig in SIGNALS:
        s = np.array([r.get(sig) if r.get(sig) is not None else np.nan for r in sub], float)
        if np.isnan(s).all(): continue
        a, n = auroc(y, s)
        if a is None: continue
        ok = ~np.isnan(s)
        ci = boot_ci([r for r, k in zip(sub, ok) if k], y[ok], s[ok])
        entries.append((sig, a, ci, n))
    oof = text_baseline(sub, target)
    if oof is not None and not np.isnan(oof).all():
        a, n = auroc(y, oof); ok = ~np.isnan(oof)
        entries.append(('text_baseline_cv', a, boot_ci([r for r, k in zip(sub, ok) if k], y[ok], oof[ok]), n))
    for sig, a, ci, n in sorted(entries, key=lambda e: -abs(e[1] - 0.5)):
        flag = '' if (ci[0] > 0.5 or ci[1] < 0.5) else '   (CI covers 0.5)'
        print(f'{sig:22s} {a:>7.3f} {str(ci):>16} {n:>6}{flag}')
        block['detectors'][sig] = {'auroc': round(a, 4), 'ci95': ci, 'n': n,
                                   'excludes_chance': bool(ci[0] > 0.5 or ci[1] < 0.5)}
    result['strata'][sname] = block

out = ROOT / 'results/step1_competitive_gap'
out.mkdir(parents=True, exist_ok=True)
(out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'\nwrote {out}/results.json')
