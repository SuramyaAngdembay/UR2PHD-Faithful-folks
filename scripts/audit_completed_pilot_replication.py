"""Offline independent audit of the completed September 17 pilot replication.

Preserves frozen inputs/analysis. Recomputes AUROCs by direct pair comparison,
not the original rank implementation. Fixed-count bootstrap attempts expose
undefined samples; a CI is withheld if any attempt is undefined. Supplemental
analyses are exploratory. No model calls, exposure claims from file names, or
changes to the original run are made.
"""
import argparse
from collections import defaultdict
import datetime
import hashlib
import json
from pathlib import Path

import numpy as np

import diagnostic_v2 as runner

ROOT = Path(__file__).resolve().parents[1]
SQ = 'google_simpleqa-verified'
WEIGHTS = {SQ: 24 / 60, 'aai530-group6_ddxplus': 22 / 60, 'cais_hle': 14 / 60}
ARMS = ('A1', 'A2')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_run(run, prepared, frozen=False):
    meta = read(run / 'run.json')
    descriptor = meta['descriptor']
    config = meta['config']
    plan = runner.request_plan(prepared, config, descriptor['partition'],
                               descriptor['repeats'], descriptor['max_items'])
    expected = [p['request_id'] for p in plan]
    rows = runner.read_jsonl(run / 'responses.jsonl')
    ids = [r['request_id'] for r in rows]
    completion = read(run / 'completion.json')
    require(expected == descriptor['request_ids'], 'Reconstructed plan differs')
    require(set(ids) == set(expected), 'Missing or extra requests')
    require(len(ids) == len(set(ids)), 'Duplicate request IDs')
    # The historical pilot was resumed with carried records; match by identity,
    # not line number. The uninterrupted replication also preserves plan order.
    if frozen:
        require(ids == expected, 'Replication request order differs')
    planned_by_id = {p['request_id']: p for p in plan}
    require(completion['expected'] == completion['valid'] == len(plan), 'Incomplete marker')
    require(completion['failed_slots'] == 0, 'Failed slots')
    require(completion['responses_sha256'] == sha(run / 'responses.jsonl'), 'Response hash mismatch')
    require(descriptor['identity']['config_sha256'] == runner.digest(config), 'Config mismatch')
    require(descriptor['identity']['items_sha256'] == sha(prepared / 'items.jsonl'), 'Items mismatch')
    for row in rows:
        planned = planned_by_id[row['request_id']]
        require((row['rid'], row['arm']) == (planned['rid'], planned['arm']), 'Cell mismatch')
        require(row['returned_model'] == row['raw']['model'] == config['model'], 'Model mismatch')
        parsed = runner.parse_output(row['raw'], planned['item'], row['arm'],
                                     config.get('evidence_policy', 'reject'),
                                     config.get('schema_family', 'component'))
        require(parsed == row['parsed'], 'Raw/parsed mismatch')
    if frozen:
        lock = read(prepared / 'lock.json')
        require(runner.run_identity(config, prepared) == descriptor['identity'] == lock['identity'],
                'Frozen identity mismatch')
        require(runner.digest(expected) == lock['request_ids_sha256'], 'Frozen plan mismatch')
        require(sha(ROOT / 'scripts/replication_analysis.py') == lock['checklist']['_hashes']['analysis_script'],
                'Frozen analysis changed')
        require(lock['frozen_at_utc'] < min(r['timestamp_utc'] for r in rows), 'Late freeze')
        attempts = runner.read_jsonl(run / 'attempts.jsonl')
        errors = runner.read_jsonl(run / 'errors.jsonl')
        require(len(attempts) == len(rows) + len(errors) == completion['http_requests_recorded'],
                'Attempt counts mismatch')
        require(all(e['request_id'] in ids and e.get('http_status') == 429 for e in errors),
                'Unresolved or unexpected errors')
    key = {r['rid']: r for r in runner.read_jsonl(prepared / 'key.jsonl')}
    cells = defaultdict(dict)
    for row in rows:
        planned = planned_by_id[row['request_id']]
        if row['arm'] in ARMS:
            cells[row['rid']][(row['arm'], planned['repeat'])] = row['parsed']['unfaithfulness_score']
    result = []
    for rid in sorted(cells):
        require(set(cells[rid]) == {(a, b) for a in ARMS for b in range(3)}, 'Missing repeats')
        scores = {a: float(np.mean([cells[rid][(a, b)] for b in range(3)])) for a in ARMS}
        result.append(dict(key[rid], scores=scores | {'word_count': key[rid]['word_count'],
                                                    'n_steps': key[rid]['n_steps']}))
    require(len(result) == 70, 'Wrong response count')
    return result, {'requests': len(rows), 'raw_parse_matches': True, 'plan_matches': True,
                    'completion': completion}


def pair_auc(positive, negative):
    if not len(positive) or not len(negative):
        return float('nan')
    p = np.asarray(positive)[:, None]
    n = np.asarray(negative)[None, :]
    return float(np.mean((p > n) + 0.5 * (p == n)))


def estimates(rows):
    faithful = [r for r in rows if r['y'] == 0]
    unfaithful = [r for r in rows if r['y'] == 1]
    scores = {a: pair_auc([r['scores'][a] for r in unfaithful],
                          [r['scores'][a] for r in faithful])
              for a in (*ARMS, 'word_count', 'n_steps')}
    return scores | {'A2_minus_A1': scores['A2'] - scores['A1'],
                     'A2_minus_reversed_A1': scores['A2'] - (1 - scores['A1']),
                     'A2_minus_word_count': scores['A2'] - scores['word_count']}


def standardized(rows):
    require(all(r['task'] == SQ for r in rows if r['y'] == 0), 'Unexpected faithful task')
    f = [r for r in rows if r['y'] == 0]
    values = {}
    for a in ARMS:
        values[a] = sum(weight * pair_auc([r['scores'][a] for r in rows if r['y'] == 1 and r['task'] == task],
                                         [r['scores'][a] for r in f])
                        for task, weight in WEIGHTS.items())
    return values | {'A2_minus_A1': values['A2'] - values['A1']}


def bootstrap(rows, estimator, attempts=2000, seed=0):
    by_cluster = defaultdict(list)
    for r in rows:
        by_cluster[r['cluster_id']].append(r)
    clusters = sorted(by_cluster)
    rng = np.random.default_rng(seed)
    names = list(estimator(rows))
    draws = np.full((attempts, len(names)), np.nan)
    for b in range(attempts):
        sample = [r for i in rng.integers(0, len(clusters), len(clusters))
                  for r in by_cluster[clusters[i]]]
        v = estimator(sample)
        draws[b] = [v[k] for k in names]
    result = {'responses': len(rows), 'questions': len(clusters),
              'faithful': sum(r['y'] == 0 for r in rows),
              'attempts': attempts, 'seed': seed, 'metrics': {}}
    points = estimator(rows)
    for j, name in enumerate(names):
        undefined = int(np.sum(~np.isfinite(draws[:, j])))
        ci = None if undefined else np.quantile(draws[:, j], [0.025, 0.975]).tolist()
        result['metrics'][name] = {'point': points[name], 'ci': ci, 'undefined_draws': undefined}
    return result, dict(zip(names, draws.T))


def exposure(replication):
    # Explicit historical artifacts; packet selection is not asserted to be completed review.
    categories = {
        'scored': ['results/reconcile_A.jsonl', 'results/reconcile_B.jsonl', 'results/reconcile_C.jsonl',
                   'results/autonomous_batch1/run/joined-analysis.jsonl',
                   'results/autonomous_batch2/run/joined-analysis.jsonl',
                   'results/metadata_comment_ablation/run/joined-analysis.jsonl',
                   'results/diagnostic_v2/smoke-gpt4o-v2.1/responses.jsonl'],
        'packet_selected': ['results/diagnostic_v2/audit/withheld_key.jsonl',
                            'results/audit_packet/audit_key.jsonl'],
        'retrospective_context': ['results/autonomous_campaign_2026-09-12/matched-retrospective-context.jsonl']}
    key = {r['rid']: r for r in runner.read_jsonl(ROOT / 'results/diagnostic_v2/prepared/key.jsonl')}
    historical = {}
    ledger = []
    for kind, files in categories.items():
        historical[kind] = {name: {r.get('rid') for r in runner.read_jsonl(ROOT / name)} & key.keys()
                            for name in files}
    for r in replication:
        record = {'rid': r['rid'], 'y': r['y'], 'cluster_id': r['cluster_id']}
        for kind, sources in historical.items():
            record[kind] = [name for name, ids in sources.items() if r['rid'] in ids]
        ledger.append(record)
    all_ids = set().union(*(ids for sources in historical.values() for ids in sources.values()))
    all_clusters = {key[r]['cluster_id'] for r in all_ids}
    direct = [r for r in ledger if any(r[kind] for kind in categories)]
    scored = [r for r in ledger if r['scored']]
    summary = {'direct_scoring_exposure': len(scored),
               'faithful_directly_scored': sum(r['y'] == 0 for r in scored),
               'scored_or_selected_or_context': len(direct),
               'faithful_scored_or_selected_or_context': sum(r['y'] == 0 for r in direct),
               'responses_at_prior_questions': sum(r['cluster_id'] in all_clusters for r in replication),
               'scope': 'Explicit named development artifacts; broader benchmark analyses predate these.'}
    return summary, ledger, [ROOT / name for files in categories.values() for name in files]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    require(not args.out.exists(), 'Output already exists; choose a new audit version')
    pilot, pilot_integrity = verify_run(ROOT / 'results/diagnostic_v2/pilot-4arm-rep3c',
                                        ROOT / 'results/diagnostic_v2/prepared')
    rep, integrity = verify_run(ROOT / 'results/diagnostic_v2/rep-eval',
                                ROOT / 'results/diagnostic_v2/prepared-replication-v2', True)
    require(not {r['cluster_id'] for r in pilot} & {r['cluster_id'] for r in rep}, 'Pilot overlap')
    original = read(ROOT / 'results/controlled_verification/replication-analysis/results.json')
    results = {}
    for name, rows in [('pilot', pilot), ('replication', rep)]:
        primary, _ = bootstrap(rows, estimates)
        for arm in ARMS:
            require(np.isclose(primary['metrics'][arm]['point'], original[name]['auroc'][arm], atol=1e-12),
                    'Primary AUROC differs')
            require(np.allclose(primary['metrics'][arm]['ci'], original[name]['auroc_ci'][arm], atol=1e-12),
                    'Primary interval differs')
        require(np.allclose(primary['metrics']['A2_minus_A1']['ci'], original[name]['contrast_ci'], atol=1e-12),
                'Paired contrast interval differs')
        simpleqa, _ = bootstrap([r for r in rows if r['task'] == SQ], estimates)
        task_standardized, _ = bootstrap(rows, standardized)
        components = {t: estimates([r for r in rows if r['y'] == 0 or r['task'] == t])
                      for t in WEIGHTS}
        results[name] = {'primary_reproduced': primary, 'simpleqa_exploratory': simpleqa,
                         'fixed_task_weight_exploratory': task_standardized,
                         'task_components_against_faithful_SimpleQA': components}
    # Independent question draws across cohorts: exploratory difference, not a replication/equivalence test.
    old, old_draws = bootstrap([r for r in pilot if r['task'] == SQ], estimates, seed=20260917)
    new, new_draws = bootstrap([r for r in rep if r['task'] == SQ], estimates, seed=20260918)
    delta = new_draws['A2'] - old_draws['A2']
    difference = {'point': new['metrics']['A2']['point'] - old['metrics']['A2']['point'],
                  'ci': np.quantile(delta, [.025, .975]).tolist() if np.isfinite(delta).all() else None,
                  'undefined_draws': int(np.sum(~np.isfinite(delta))),
                  'seeds': [20260917, 20260918], 'attempts': len(delta),
                  'scope': 'Exploratory independent-cluster bootstrap; cohorts differ in composition/exposure.'}
    ex, ledger, inputs = exposure(rep)
    output = {'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'Offline completed-run audit; no new inference',
              'integrity': integrity, 'pilot_integrity': pilot_integrity,
              'original_primary_results_reproduced': True, 'results': results,
              'simpleqa_A2_new_minus_pilot_exploratory': difference,
              'prior_exposure': ex, 'fixed_unfaithful_task_weights': WEIGHTS,
              'ci_policy': '2000 fixed attempts, question-cluster paired; withhold CI if any draw undefined; nominal exploratory intervals, no multiplicity adjustment'}
    inputs += [ROOT / 'scripts/audit_completed_pilot_replication.py', ROOT / 'scripts/diagnostic_v2.py',
               ROOT / 'scripts/replication_analysis.py', ROOT / 'results/controlled_verification/replication-analysis/results.json']
    for run in ['rep-eval', 'pilot-4arm-rep3c']:
        inputs += [ROOT / 'results/diagnostic_v2' / run / f for f in ['run.json', 'responses.jsonl', 'completion.json']]
    for prep in ['prepared', 'prepared-replication-v2']:
        inputs += [ROOT / 'results/diagnostic_v2' / prep / f for f in ['key.jsonl', 'items.jsonl', 'manifest.json']]
    inputs += [ROOT / 'results/diagnostic_v2/prepared-replication-v2/lock.json']
    output['input_sha256'] = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    args.out.mkdir(parents=True)
    (args.out / 'results.json').write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
    (args.out / 'exposure-ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
    print(json.dumps({k: output[k] for k in ['original_primary_results_reproduced', 'prior_exposure',
                                            'simpleqa_A2_new_minus_pilot_exploratory']}, indent=2))
    for name in results:
        for endpoint in ['primary_reproduced', 'simpleqa_exploratory', 'fixed_task_weight_exploratory']:
            print(name, endpoint, json.dumps(results[name][endpoint]['metrics']))


if __name__ == '__main__':
    main()
