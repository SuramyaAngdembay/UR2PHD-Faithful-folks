"""Frozen analysis for amendment v1.3 (note-position check). Hashed before inference.

Detection := judged status 'contradicted' on the attribution claim, using the v1 analysis module's
matching rule unchanged (record_endpoints). Endpoints: detection rate by position per procedure;
per-pair contradicted counts (of 3 repeats); within-pair difference after - before with
pair-clustered bootstrap (2,000 draws, seed 0, percentile 95%) and an exact two-sided sign test on
pairs with a nonzero difference; status breakdown by position; replication agreement between each
pair's original-position variant and its v1 result. Constructed controls only.
"""
import argparse, hashlib, importlib.util, json, math
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('cva', HERE / 'controlled_verification_analysis.py')
cva = importlib.util.module_from_spec(spec); spec.loader.exec_module(cva)
VERSION = 'position-analysis-1.0'

def sign_test(diffs):
    nz = [d for d in diffs if d != 0]
    if not nz: return {'n_nonzero': 0, 'p_two_sided': None}
    k = sum(d > 0 for d in nz); n = len(nz)
    p = sum(math.comb(n, i) for i in range(0, n + 1) if abs(i - n / 2) >= abs(k - n / 2)) / 2 ** n
    return {'n_nonzero': n, 'positive': k, 'p_two_sided': min(1.0, p)}

def load(run, prepared):
    key = {json.loads(l)['rid']: json.loads(l) for l in (prepared / 'key.jsonl').read_text().splitlines() if l.strip()}
    rows = [json.loads(l) for l in (run / 'responses.jsonl').read_text().splitlines() if l.strip()]
    out = []
    for r in rows:
        k = key[r['rid']]; e = cva.record_endpoints(r['parsed'], k['gold'])
        out.append(dict(rid=r['rid'], pair_id=k['pair_id'], position=k['member'], replicates_v1=k['construction']['replicates_v1'],
                        procedure='generic' if r['arm'].endswith('1') else 'verification',
                        detected=e['judged_status'] == 'contradicted', status=e['judged_status'] or 'not_surfaced', score=e['score']))
    return key, out

def run(args):
    out = Path(args.out)
    if out.exists(): raise FileExistsError(f'{out} exists; choose a new versioned output directory')
    key, ev = load(Path(args.run), Path(args.prepared))
    pairs = sorted({k['pair_id'] for k in key.values()}); procs = ['generic', 'verification']
    def counts(proc, subset=None):
        c = defaultdict(lambda: {'before': 0, 'after': 0})
        for r in ev:
            if r['procedure'] == proc and (subset is None or r['pair_id'] in subset): c[r['pair_id']][r['position']] += r['detected']
        return c
    rng = np.random.default_rng(args.seed); result = {'analysis_version': VERSION, 'records': len(ev), 'per_procedure': {}}
    for proc in procs:
        c = counts(proc)
        diffs = [c[p]['after'] - c[p]['before'] for p in pairs]
        boots = []
        for _ in range(args.bootstrap):
            ps = [pairs[i] for i in rng.integers(0, len(pairs), len(pairs))]
            boots.append(float(np.mean([c[p]['after'] - c[p]['before'] for p in ps])) / 3)
        rate = {pos: float(np.mean([r['detected'] for r in ev if r['procedure'] == proc and r['position'] == pos])) for pos in ('before', 'after')}
        status = {pos: dict(Counter(r['status'] for r in ev if r['procedure'] == proc and r['position'] == pos)) for pos in ('before', 'after')}
        result['per_procedure'][proc] = {
            'detection_rate': rate, 'after_minus_before_rate': rate['after'] - rate['before'],
            'after_minus_before_ci95': [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            'sign_test': sign_test(diffs), 'per_pair_contradicted_of_3': {p: c[p] for p in pairs},
            'status_by_position': status}
    # replication: original-position variant vs v1 per pair
    rep = {}
    if args.v1_records:
        v1 = [json.loads(l) for l in Path(args.v1_records).read_text().splitlines() if l.strip()]
        v1c = defaultdict(int)
        for r in v1:
            if r['family'] == 'attribution' and r['member'] == 'absent' and r['evidence'] == 'full':
                v1c[(r['pair_id'], r['procedure'])] += r['judged_status'] == 'contradicted'
        for proc in procs:
            c = counts(proc); agree = 0; table = {}
            for p in pairs:
                orig = key[f'{p}-A-before']['construction']['v1_note_position']
                now = c[p][orig]; then = v1c[(p, proc)]; table[p] = {'v1': then, 'v1.3_same_position': now}; agree += (now == then)
            rep[proc] = {'pairs_with_identical_count': agree, 'of': len(pairs), 'table': table}
    result['replication_vs_v1'] = rep
    result['inputs_sha256'] = {'responses': hashlib.sha256((Path(args.run) / 'responses.jsonl').read_bytes()).hexdigest(),
                               'key': hashlib.sha256((Path(args.prepared) / 'key.jsonl').read_bytes()).hexdigest()}
    result['bootstrap'] = {'draws': args.bootstrap, 'seed': args.seed, 'cluster': 'pair_id'}
    out.mkdir(parents=True); (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    (out / 'records.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in ev))
    print(json.dumps({k: v for k, v in result.items() if k in ('per_procedure', 'replication_vs_v1')}, indent=1))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True); ap.add_argument('--prepared', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--v1-records', default=str(HERE.parent / 'results/controlled_verification/v1-analysis/records.jsonl'))
    ap.add_argument('--bootstrap', type=int, default=2000); ap.add_argument('--seed', type=int, default=0)
    run(ap.parse_args())
