"""Portable GRACE reanalysis with tri-state correctness and paired uncertainty.

Exploratory: answer reviews are assistant judgments, not independent human gold.
Target = fraction of native unfaithful steps. Binary aggregations are sensitivity
endpoints, not new trace annotations. Historical NLI truncation remains a limit.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from grace_answer_check import VERSION, evaluate, load_reviews, load_rows
from reanalysis_common import (aucs, cluster_draws, interval, manifest, number,
                               read_json, rhos, save_json, sha256)

ROOT = Path(__file__).resolve().parents[1]
SIGNALS = ['nli_frac_unsup_ctx', 'nli_frac_unsup_prior', 'neg_nli_mean_ent_ctx',
           'nli_unsup_ctx', 'nli_unsup_prior', 'n_steps', 'words', 'neg_frac_cited']
RULES = {'any': lambda f: f > 0, '>0.25': lambda f: f > .25,
         '>=0.5': lambda f: f >= .5, '>0.5': lambda f: f > .5, 'all': lambda f: f == 1}


def steptext(step):
    for key in ('text', 'step', 'content', 'step_text'):
        if step.get(key):
            return str(step[key])
    raise ValueError('Step has no text')


def features(rows, cache):
    if set(cache) != {r['id'] for r in rows}:
        raise ValueError('NLI cache IDs must exactly match the GRACE population')
    x, target = [], []
    for row in rows:
        n, sc = len(row['steps']), cache[row['id']]
        for tag in ('ctx', 'prior'):
            count, mean = sc.get('nli_unsup_' + tag), sc.get('nli_mean_ent_' + tag)
            if type(count) is not int or not 0 <= count <= n:
                raise ValueError(f"Invalid NLI count: {row['id']} {tag}")
            if type(mean) not in (int, float) or not np.isfinite(mean) or not 0 <= mean <= 1:
                raise ValueError(f"Invalid NLI entailment: {row['id']} {tag}")
        target.append(sum(s['faithfulness'] == 'unfaithful' for s in row['steps']) / n)
        text = ' '.join(steptext(s) for s in row['steps'])
        x.append([sc['nli_unsup_ctx'] / n, sc['nli_unsup_prior'] / n,
                  -sc['nli_mean_ent_ctx'], sc['nli_unsup_ctx'], sc['nli_unsup_prior'],
                  n, len(text.split()), -sum(bool(s.get('citations')) for s in row['steps']) / n])
    return np.asarray(target), np.asarray(x, dtype=float)


def lift(y, correct):
    incorrect = correct == 0
    if not y.any() or not incorrect.any():
        return np.nan
    return incorrect[y].mean() / incorrect.mean()


def binary_summary(frac, x, correct=None):
    out = {}
    for rule, apply in RULES.items():
        y = apply(frac)
        rec = {'n': len(y), 'unfaithful': int(y.sum()), 'faithful': int((~y).sum()),
               'auroc': dict(zip(SIGNALS, map(number, aucs(y, x))))}
        if correct is not None:
            rec['cells'] = {c: {'faithful': int(((correct == v) & ~y).sum()),
                               'unfaithful': int(((correct == v) & y).sum())}
                            for c, v in [('correct', 1), ('incorrect', 0)]}
            rec['incorrect_base_rate'] = float((correct == 0).mean())
            rec['incorrect_given_unfaithful'] = float((correct[y] == 0).mean()) if y.any() else None
            rec['lift'] = number(lift(y, correct))
            rec['by_correctness_auroc'] = {
                c: dict(zip(SIGNALS, map(number, aucs(y[correct == v], x[correct == v]))))
                for c, v in [('correct', 1), ('incorrect', 0)]}
        out[rule] = rec
    return out


def paired_regimes(frac, x, correct, keys, repeats, seed):
    def estimates(ix):
        c = correct[ix]
        rc = rhos(frac[ix][c == 1], x[ix][c == 1])
        ri = rhos(frac[ix][c == 0], x[ix][c == 0])
        return np.stack([rhos(frac[ix], x[ix]), rc, ri, rc - ri])
    point = estimates(np.arange(len(frac)))
    draws, lifts = [], []
    for ix in cluster_draws(keys, repeats, seed):
        draws.append(estimates(ix))
        lifts.append([lift(apply(frac[ix]), correct[ix]) for apply in RULES.values()])
    draws, lifts = np.asarray(draws), np.asarray(lifts)
    binary = binary_summary(frac, x, correct)
    for j, rule in enumerate(RULES):
        v = binary[rule]['lift']
        binary[rule]['lift_interval'] = interval(v if v is not None else np.nan, lifts[:, j], 'lift')
    return {'n': len(frac), 'questions': len(set(keys)),
            'correct': int((correct == 1).sum()), 'incorrect': int((correct == 0).sum()),
            'signals': {signal: {label: interval(point[j, i], draws[:, j, i],
                                                'delta' if label == 'correct_minus_incorrect' else 'rho')
                                 for j, label in enumerate(['pooled', 'correct', 'incorrect', 'correct_minus_incorrect'])}
                        for i, signal in enumerate(SIGNALS)}, 'binary': binary}


def conditional_pairs(rows, frac, x):
    """Different estimand from rho: AUROC restricted to dataset x track pairs."""
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[(row['dataset'], row['track'])].append(i)
    result = {}
    for rule, apply in RULES.items():
        y, num, den, cells = apply(frac), np.zeros(len(SIGNALS)), 0, []
        for key, ix in sorted(groups.items()):
            yy = y[ix]
            w = int(yy.sum()) * int((~yy).sum())
            cells.append({'dataset': key[0], 'track': key[1], 'n': len(ix), 'unfaithful': int(yy.sum()), 'pairs': w})
            if w:
                num += w * aucs(yy, x[ix])
                den += w
        total = int(y.sum()) * int((~y).sum())
        result[rule] = {'endpoint': 'pair-weighted within-dataset-and-track binary AUROC',
                        'supported_pairs': den, 'pooled_pairs': total,
                        'pair_coverage': den / total if total else None, 'cells': cells,
                        'auroc': dict(zip(SIGNALS, map(number, num / den))) if den else None}
    return result


def run(args):
    out = Path(args.output_dir)
    if out.exists():
        raise FileExistsError(f'Choose a new versioned output directory: {out}')
    rows = load_rows(args.data_dir)
    decisions = evaluate(rows, load_reviews(None if args.no_reviews else args.reviews))
    frac, x = features(rows, read_json(args.nli_cache))
    keys = [(r['dataset'], str(r['original_question_id'])) for r in rows]
    c = np.array([-1 if decisions[r['id']]['correct'] is None else int(decisions[r['id']]['correct']) for r in rows])
    auto = np.array([-1 if decisions[r['id']]['automatic_correct'] is None else int(decisions[r['id']]['automatic_correct']) for r in rows])
    inputs = {'data/' + p.name: p for p in sorted(Path(args.data_dir).glob('*.jsonl'))}
    inputs['nli_cache'] = args.nli_cache
    if not args.no_reviews:
        inputs['answer_reviews'] = args.reviews
    scripts = [Path(__file__), Path(__file__).with_name('grace_answer_check.py'),
               Path(__file__).with_name('reanalysis_common.py')]
    protocol = {'analysis': 'grace-cached-reanalysis-v3', 'correctness_checker': VERSION,
                'review_provenance': 'none; deterministic decisions only' if args.no_reviews else 'assistant equivalence review; not independent human gold',
                'target': 'fraction of native unfaithful steps; five declared binary sensitivity rules',
                'score_direction': 'higher unfaithfulness; mean context entailment and citation fraction negated once',
                'cluster': 'dataset + original_question_id; same draws for direct regime differences',
                'nli_cache': {'model_as_documented': 'roberta-large-mnli', 'entailment_index': 2,
                              'unsupported_threshold': .5, 'premise_char_limit': 4000,
                              'pair_token_limit': 512, 'context_arm': 'supplied passages/context',
                              'prior_arm': 'question + preceding steps, omitting supplied context',
                              'provenance': 'legacy cache: no original requests, model revision, or token-level truncation logs'},
                'scope': 'selected verifier-disagreement GRACE test set; exploratory, prior sample exposure; no fresh judge inference',
                'uncertainty': 'percentile question bootstrap, fixed attempts, undefined replicates counted; no multiplicity adjustment'}
    man = manifest(inputs, scripts, protocol, args.seed, args.bootstrap)
    pooled_draws = np.asarray([rhos(frac[ix], x[ix]) for ix in cluster_draws(keys, args.bootstrap, args.seed)])
    pooled = {'n': len(rows), 'questions': len(set(keys)), 'steps': sum(len(r['steps']) for r in rows),
              'signals': {s: interval(v, pooled_draws[:, j], 'rho') for j, (s, v) in enumerate(zip(SIGNALS, rhos(frac, x)))},
              'binary': binary_summary(frac, x), 'conditional_pairs': conditional_pairs(rows, frac, x)}
    cohorts = {}
    for name, labels in [('reviewed', c), ('deterministic_only', auto)]:
        ix = np.flatnonzero(labels >= 0)
        if not len(ix):
            raise ValueError(f'No resolved answers in {name}')
        cohorts[name] = paired_regimes(frac[ix], x[ix], labels[ix], [keys[i] for i in ix], args.bootstrap, args.seed)
        cohorts[name]['rids'] = [rows[i]['id'] for i in ix]
        cohorts[name]['by_dataset'] = {d: dict(Counter('correct' if labels[i] else 'incorrect' for i in ix if rows[i]['dataset'] == d))
                                        for d in sorted({r['dataset'] for r in rows})}
        # Keep the fraction/rho endpoint for task-specific comparisons. This is
        # separate from the dataset x track binary conditional-pair diagnostic.
        cohorts[name]['within_dataset'] = {}
        for dataset in sorted({rows[i]['dataset'] for i in ix}):
            sub = np.array([i for i in ix if rows[i]['dataset'] == dataset])
            cohorts[name]['within_dataset'][dataset] = paired_regimes(
                frac[sub], x[sub], labels[sub], [keys[i] for i in sub], args.bootstrap, args.seed)
        print(f'{name}: {len(ix)} resolved answers', flush=True)
    # Exhaustive point-estimate sensitivity to unresolved answers only. This is
    # not a bound on errors in the resolved reviews or the benchmark reference.
    unresolved = np.flatnonzero(c < 0)
    sensitivity = {'unresolved_rids': [rows[i]['id'] for i in unresolved]}
    if len(unresolved) <= 12:
        deltas, ls = [], []
        for assignment in range(2 ** len(unresolved)):
            cc = c.copy()
            for bit, i in enumerate(unresolved):
                cc[i] = (assignment >> bit) & 1
            deltas.append(rhos(frac[cc == 1], x[cc == 1]) - rhos(frac[cc == 0], x[cc == 0]))
            ls.append([lift(apply(frac), cc) for apply in RULES.values()])
        sensitivity.update(assignments=len(deltas),
                           delta_ranges={s: [number(np.nanmin(np.asarray(deltas)[:, j])), number(np.nanmax(np.asarray(deltas)[:, j]))]
                                         for j, s in enumerate(SIGNALS)},
                           lift_ranges={s: [number(np.nanmin(np.asarray(ls)[:, j])), number(np.nanmax(np.asarray(ls)[:, j]))]
                                        for j, s in enumerate(RULES)})
    else:
        sensitivity['status'] = 'exhaustive assignment omitted above 12 unresolved answers'
    result = {'run_sha256': man['run_sha256'], 'pooled_all_traces': pooled, 'cohorts': cohorts,
              'correctness_coverage': dict(Counter('unresolved' if v < 0 else 'correct' if v else 'incorrect' for v in c)),
              'unresolved_sensitivity': sensitivity,
              'limitations': ['Answer reference equivalence, not revalidation of reference truth.',
                              'Assistant review and automatic-only selection can both introduce bias.',
                              'Non-detection is neither equivalence nor proof of FaithCoT-specific mechanisms.',
                              'Conditional pair AUROC is not an adjusted version of Spearman rho.']}
    out.mkdir(parents=True)
    save_json(out / 'correctness.json', {'schema': VERSION, 'decisions': decisions})
    save_json(out / 'results.json', result)
    man['artifacts'] = {name: sha256(out / name) for name in ('correctness.json', 'results.json')}
    save_json(out / 'manifest.json', man)
    print(f'Complete: {out}', flush=True)
    return result


def add_arguments(parser):
    parser.add_argument('--data-dir', '--gdir', required=True)
    parser.add_argument('--nli-cache', type=Path, default=ROOT / 'results/grace_nli.json')
    parser.add_argument('--reviews', type=Path, default=ROOT / 'configs/grace-answer-reviews-v3.json')
    parser.add_argument('--no-reviews', action='store_true')
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--bootstrap', type=int, default=2000)
    parser.add_argument('--seed', type=int, default=0)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    return run(parser.parse_args(argv))


if __name__ == '__main__':
    main()
