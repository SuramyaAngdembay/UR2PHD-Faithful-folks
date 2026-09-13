"""Paired reanalysis of cached BonaFide reconciliation; no new API requests.

A = generic/full prompt, B = generic/locally stripped prompt (NOT upstream's
no-hint rubric), C = our rubric/full prompt, D = historical GPT-4o/clean question.
All scores point towards unfaithfulness. These are exploratory protocol contrasts;
D is a historical comparison, and score-only caches cannot validate rationales.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from reanalysis_common import (aucs, cluster_draws, indexed, interval, manifest,
                               number, read_json, save_json, sha256)
ROOT = Path(__file__).resolve().parents[1]
ARMS = ['A', 'B', 'C', 'D']
CONTRASTS = [('A', 'B'), ('A', 'C'), ('C', 'D'), ('A', 'D'), ('B', 'D'), ('B', 'C')]


def score(value):
    if type(value) not in (int, float) or not np.isfinite(value) or not 0 <= value <= 100:
        raise ValueError(f'Invalid score: {value!r}')
    return float(value)


def load_inputs(directory):
    directory = Path(directory)
    paths = {name: directory / name for name in
             ['bonafide_pop.json', 'bonafide_predictions.json', 'dev_clusters.json']}
    pop = indexed(read_json(paths['bonafide_pop.json'])['rows'], 'rid')
    for row in pop.values():
        if type(row['y']) is not int or row['y'] not in (0, 1) or type(row['correct']) is not int or row['correct'] not in (0, 1):
            raise ValueError('Population labels must be explicit binary integers')
        if not isinstance(row['cluster'], str) or not row['cluster']:
            raise ValueError('Missing question cluster')
    frozen = indexed(read_json(paths['bonafide_predictions.json']), 'rid')
    arms, metadata = {}, {}
    for arm in 'ABC':
        # Explicit filenames: do not silently merge overlapping _full campaigns.
        path = directory / f'reconcile_{arm}.jsonl'
        paths[path.name] = path
        records = indexed([json.loads(line) for line in path.read_text().splitlines()], 'rid')
        for rid, rec in records.items():
            if rid not in pop or rec['arm'] != arm or rec['model'] != 'gpt-4o':
                raise ValueError(f'Unknown response / wrong arm / mixed model: {rid}')
        arms[arm] = {rid: score(rec['score']) for rid, rec in records.items()}
        metadata[arm] = {'model_alias': 'gpt-4o', 'n': len(records), 'original_request_provenance': 'legacy score-only cache'}
    arms['D'] = {}
    for rid, rec in frozen.items():
        if rid not in pop:
            raise ValueError(f'Unknown frozen ID: {rid}')
        if any(rec[k] != pop[rid][k] for k in ('y', 'correct', 'cluster')):
            raise ValueError(f'Frozen/population label or cluster drift: {rid}')
        if rec.get('judge4o') is not None:
            arms['D'][rid] = score(rec['judge4o'])
    metadata['D'] = {'model_alias_as_documented': 'gpt-4o', 'n': len(arms['D']),
                     'historical': True, 'field': 'judge4o'}
    return pop, arms, read_json(paths['dev_clusters.json']), paths, metadata


def compare(pop, arms, ids, repeats, seed):
    ids = sorted(ids)
    if not ids:
        raise ValueError('Empty paired intersection')
    y = np.array([pop[rid]['y'] for rid in ids])
    x = np.array([[arms[a][rid] for a in ARMS] for rid in ids])
    keys = [pop[rid]['cluster'] for rid in ids]
    point = aucs(y, x)
    draws = np.asarray([aucs(y[ix], x[ix]) for ix in cluster_draws(keys, repeats, seed)])
    contrasts = {}
    for a, b in CONTRASTS:
        i, j = ARMS.index(a), ARMS.index(b)
        contrasts[f'{a}-{b}'] = interval(point[i] - point[j], draws[:, i] - draws[:, j], 'delta_auroc')
    return {'rids': ids, 'n': len(ids), 'questions': len(set(keys)), 'unfaithful': int(y.sum()),
            'faithful': int((1 - y).sum()), 'correct': sum(pop[rid]['correct'] for rid in ids),
            'arms': {a: interval(point[i], draws[:, i], 'auroc') for i, a in enumerate(ARMS)},
            'paired_contrasts': contrasts}


def exposure(pop, arms, split):
    dev_clusters = set(split['dev_clusters'])
    eligible = {rid for rid, row in pop.items() if row['correct'] == 0}
    dev = {rid for rid in eligible if pop[rid]['cluster'] in dev_clusters}
    ev = eligible - dev
    if len(dev) != split['n_dev_responses'] or len(ev) != split['n_eval_responses']:
        raise ValueError('Frozen split counts do not match the eligible population')
    touched = set.union(*(set(arms[a]) for a in 'ABC'))
    touched_eval = touched & ev
    clusters = {pop[rid]['cluster'] for rid in touched_eval}
    common = set.intersection(*(set(arms[a]) for a in ARMS))
    def counts(ids):
        return {'dev': len(ids & dev), 'evaluation': len(ids & ev), 'outside_split': len(ids - eligible)}
    return {'split_preserved': True, 'eligible_incorrect': len(eligible), 'dev_n': len(dev), 'evaluation_n': len(ev),
            'union_counts': counts(touched), 'paired_counts': counts(common),
            'evaluation_scored_rids': sorted(touched_eval), 'evaluation_scored_questions': len(clusters),
            'evaluation_responses_sharing_scored_questions': sum(pop[rid]['cluster'] in clusters for rid in ev),
            'note': 'The original split covers incorrect answers only. Correct answers are outside it. Prior hypothesis exposure still makes this exploratory.'}


def run(args):
    out = Path(args.output_dir)
    if out.exists():
        raise FileExistsError(f'Choose a new versioned output directory: {out}')
    pop, arms, split, paths, metadata = load_inputs(args.results_dir)
    common = set.intersection(*(set(arms[a]) for a in ARMS))
    incorrect = {rid for rid in common if pop[rid]['correct'] == 0}
    protocol = {'analysis': 'bonafide-paired-reconciliation-v2', 'label': 'frozen explicit native whole-label y; 1=unfaithful',
                'direction': 'all scores higher unfaithfulness; no complement selected after outcomes',
                'arms': {'A': 'generic rubric / full prompt', 'B': 'generic rubric / local hint-strip rule, not upstream monitor_no_hint',
                         'C': 'our rubric / full prompt', 'D': 'historical GPT-4o / our rubric / clean question'},
                'population': 'exact four-arm response intersection; incorrect-only sensitivity',
                'bootstrap': 'same question resamples in every arm and direct contrast; fixed attempts; no multiplicity adjustment',
                'scope': 'exploratory; historical D; no fresh inference; legacy score-only records lack raw outputs and exact requests'}
    man = manifest(paths, [Path(__file__), Path(__file__).with_name('reanalysis_common.py')], protocol, args.seed, args.bootstrap)
    result = {'run_sha256': man['run_sha256'], 'arm_metadata': metadata,
              'paired_all': compare(pop, arms, common, args.bootstrap, args.seed),
              'paired_incorrect': compare(pop, arms, incorrect, args.bootstrap, args.seed),
              'unpaired_descriptive_only': {
                  a: {'n': len(sc), 'auroc': number(aucs([pop[rid]['y'] for rid in sorted(sc)], [sc[rid] for rid in sorted(sc)])[0])}
                  for a, sc in arms.items()},
              'limitations': ['No causal attribution to evidence alone when rubric/format/time also differ.',
                              'Nonsignificance does not establish equivalence or no context effect.',
                              'Public monitor score-interface inconsistency does not verify published AUROC orientation.',
                              'All arms use one provider; no independent rationale validation.']}
    exp = exposure(pop, arms, split)
    out.mkdir(parents=True)
    save_json(out / 'results.json', result)
    save_json(out / 'exposure.json', exp)
    man['artifacts'] = {name: sha256(out / name) for name in ('results.json', 'exposure.json')}
    save_json(out / 'manifest.json', man)
    print(json.dumps({'output': str(out), 'paired_n': len(common),
                      'auroc': {a: result['paired_all']['arms'][a]['auroc'] for a in ARMS},
                      'exposed_eval': len(exp['evaluation_scored_rids'])}), flush=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results-dir', type=Path, default=ROOT / 'results')
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--bootstrap', type=int, default=2000)
    parser.add_argument('--seed', type=int, default=0)
    return run(parser.parse_args(argv))


if __name__ == '__main__':
    main()
