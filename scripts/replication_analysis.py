"""Frozen analysis for the pilot replication (pilot-replication-spec.md). Hashed before inference.

One code path computes the SAME estimator on both samples, so the two are comparable by
construction:
  score(response, arm) = mean unfaithfulness_score over that cell's three identical repeats
  AUROC(arm)           = rank-based AUROC over responses, native unfaithful = positive
  contrast             = AUROC(A2) - AUROC(A1)
  uncertainty          = question-cluster bootstrap, 2,000 draws, seed 0, percentile 95%,
                         the SAME resampled clusters used for both arms and the contrast
                         (draws in which either class is absent are redrawn)

Self-check: running this on the pilot must reproduce its published figures (A1 .2175, A2 .5108,
contrast +.2933) or the script aborts -- a reimplementation that disagrees on identical data is a
bug, not a result.

Pre-registered replication criteria (fixed in the spec before any request; all reported whichever
way they come out):
  R1  sign of the replication contrast, and whether its 95% interval excludes zero
  R2  whether the replication point estimate lies inside the pilot interval [+.093, +.502]
  R3  whether the pilot point estimate (+.2933) lies inside the replication interval
Prevalence-dependent quantities (mean score) are reported per sample and NEVER compared across
them: the replication deliberately enriches the minority class.
"""
import argparse, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

VERSION = 'pilot-replication-analysis-1.0'
PILOT_PUBLISHED = {'A1': 0.2175, 'A2': 0.5108, 'contrast': 0.2933}
PILOT_INTERVAL = (0.093, 0.502)
ARMS = ('A1', 'A2')

def auroc(y, s):
    y = np.asarray(y); s = np.asarray(s, float)
    n1 = int(y.sum()); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return None
    r = rankdata(s)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

def cell_scores(run, key):
    rows = [json.loads(l) for l in (run / 'responses.jsonl').read_text().splitlines() if l.strip()]
    cells = defaultdict(list)
    for r in rows:
        if r['arm'] in ARMS and r['rid'] in key:
            cells[(r['rid'], r['arm'])].append(r['parsed']['unfaithfulness_score'])
    rids = sorted({rid for rid, _ in cells})
    for rid in rids:
        for arm in ARMS:
            if len(cells[(rid, arm)]) != 3:
                raise ValueError(f'expected 3 repeats for {rid}/{arm}, got {len(cells[(rid, arm)])}')
    return rids, {arm: {rid: float(np.mean(cells[(rid, arm)])) for rid in rids} for arm in ARMS}, rows

def analyse(run, prepared, label, draws, seed):
    key = {json.loads(l)['rid']: json.loads(l) for l in (prepared / 'key.jsonl').read_text().splitlines() if l.strip()}
    rids, means, rows = cell_scores(run, key)
    y = np.array([key[r]['y'] for r in rids])
    point = {arm: auroc(y, [means[arm][r] for r in rids]) for arm in ARMS}
    contrast = point['A2'] - point['A1']
    by_cluster = defaultdict(list)
    for i, rid in enumerate(rids): by_cluster[key[rid]['cluster_id']].append(i)
    clusters = sorted(by_cluster)
    rng = np.random.default_rng(seed); draws_arm = {a: [] for a in ARMS}; draws_c = []
    while len(draws_c) < draws:
        idx = [i for c in rng.integers(0, len(clusters), len(clusters)) for i in by_cluster[clusters[c]]]
        yy = y[idx]
        if yy.sum() == 0 or yy.sum() == len(yy): continue
        a = {arm: auroc(yy, [means[arm][rids[i]] for i in idx]) for arm in ARMS}
        if any(v is None for v in a.values()): continue
        for arm in ARMS: draws_arm[arm].append(a[arm])
        draws_c.append(a['A2'] - a['A1'])
    ci = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
    return {'label': label, 'n_responses': len(rids), 'n_clusters': len(clusters),
            'faithful': int((y == 0).sum()), 'unfaithful': int((y == 1).sum()),
            'discordant_pairs': int((y == 0).sum() * (y == 1).sum()),
            'task_mix': dict(Counter(key[r]['task'] for r in rids)),
            'auroc': point, 'auroc_ci': {arm: ci(draws_arm[arm]) for arm in ARMS},
            'contrast_A2_minus_A1': contrast, 'contrast_ci': ci(draws_c),
            'mean_score_prevalence_dependent_do_not_compare_across_samples':
                {arm: float(np.mean([means[arm][r] for r in rids])) for arm in ARMS}}

def run(args):
    out = Path(args.out)
    if out.exists(): raise FileExistsError(f'{out} exists; choose a new versioned output directory')
    pilot = analyse(Path(args.pilot_run), Path(args.pilot_prepared), 'pilot', args.bootstrap, args.seed)
    for k, v in PILOT_PUBLISHED.items():
        got = pilot['auroc'][k] if k in ARMS else pilot['contrast_A2_minus_A1']
        if abs(got - v) > 0.002:
            raise ValueError(f'self-check failed: recomputed pilot {k}={got:.4f} != published {v}')
    rep = analyse(Path(args.replication_run), Path(args.replication_prepared), 'replication', args.bootstrap, args.seed)
    lo, hi = rep['contrast_ci']
    criteria = {
        'R1_sign': 'positive' if rep['contrast_A2_minus_A1'] > 0 else ('negative' if rep['contrast_A2_minus_A1'] < 0 else 'zero'),
        'R1_interval_excludes_zero': bool(lo > 0 or hi < 0),
        'R2_replication_point_inside_pilot_interval': bool(PILOT_INTERVAL[0] <= rep['contrast_A2_minus_A1'] <= PILOT_INTERVAL[1]),
        'R3_pilot_point_inside_replication_interval': bool(lo <= PILOT_PUBLISHED['contrast'] <= hi),
        'intervals_overlap': bool(lo <= PILOT_INTERVAL[1] and PILOT_INTERVAL[0] <= hi)}
    result = {'analysis_version': VERSION,
              'analysis_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'estimator': 'per-response mean of 3 identical repeats; rank AUROC; question-cluster bootstrap, same draws for both arms',
              'bootstrap': {'draws': args.bootstrap, 'seed': args.seed},
              'pilot_self_check': 'passed', 'pilot': pilot, 'replication': rep,
              'preregistered_criteria': criteria,
              'scope': 'native BonaFide development responses; the replication sample is question-cluster-disjoint from the pilot and enriches the minority class'}
    out.mkdir(parents=True); (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('pilot', 'replication', 'preregistered_criteria')}, indent=1))

if __name__ == '__main__':
    ROOT = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pilot-run', default=str(ROOT / 'results/diagnostic_v2/pilot-4arm-rep3c'))
    ap.add_argument('--pilot-prepared', default=str(ROOT / 'results/diagnostic_v2/prepared'))
    ap.add_argument('--replication-run', required=True)
    ap.add_argument('--replication-prepared', default=str(ROOT / 'results/diagnostic_v2/prepared-replication-v2'))
    ap.add_argument('--out', required=True); ap.add_argument('--bootstrap', type=int, default=2000); ap.add_argument('--seed', type=int, default=0)
    run(ap.parse_args())
