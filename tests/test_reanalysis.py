"""Regression tests for answer-label and paired-population failures."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from grace_answer_check import assess, evaluate, load_reviews, load_rows, record_hash, VERSION
from grace_regime_analysis import features, paired_regimes
from bonafide_reconcile_analysis import compare, exposure
from reanalysis_common import aucs, cluster_draws, interval, read_json, rhos, save_json


def row(gold='October 28, 2012', answer='October 29, 2012'):
    return {'id': 'trace', 'dataset': 'musique', 'question': 'When?', 'options': None,
            'gold_answer': gold, 'final_answer': answer,
            'steps': [{'text': 'A step.', 'faithfulness': 'faithful'}]}


class CorrectnessTests(unittest.TestCase):
    def test_similar_dates_and_numeric_values_are_not_matches(self):
        self.assertIs(assess(row())['correct'], False)
        self.assertIs(assess(row('2015', '2010'))['correct'], False)
        self.assertIs(assess(row('22.3', '22.30'))['correct'], True)
        self.assertIs(assess(row('October 01, 2012', 'October 1, 2012'))['correct'], True)

    def test_first_character_and_substring_are_not_equivalence(self):
        for gold, ans in [('Mark Antony', 'Maria Christina'),
                          ('Union Army', 'I cannot determine whether it was the Union Army.'),
                          ('Ottokar', 'Ottokar is the father, not the grandfather.'),
                          ('yes', 'Yes, wait, no; I cannot decide.')]:
            self.assertIsNone(assess(row(gold, ans))['correct'])

    def test_multi_choice_requires_explicit_choice(self):
        r = row('B) second', 'B')
        r['options'] = ['first', 'second', 'third', 'fourth']
        self.assertIs(assess(r)['correct'], True)
        r['final_answer'] = 'A) first'
        self.assertIs(assess(r)['correct'], False)
        for answer in ['B) first', 'B and D', 'Both could be correct', 'B, or perhaps C']:
            r['final_answer'] = answer
            self.assertIsNone(assess(r)['correct'])
        r['gold_answer'] = 'B) first'
        with self.assertRaisesRegex(ValueError, 'letter/text'):
            assess(r)

    def test_presentation_only_and_wrong_boolean(self):
        self.assertIs(assess(row('Piri Reis', '**Piri Reis** [ref_2].'))['correct'], True)
        self.assertIs(assess(row('yes', 'No.'))['correct'], False)
        self.assertIsNone(assess(row('London', 'England'))['correct'])

    def test_review_hash_prevents_stale_adjudication(self):
        r = row()
        review = {'id': r['id'], 'record_sha256': record_hash(r), 'correct': False, 'reason': 'Different day.'}
        self.assertIs(evaluate([r], {r['id']: review})[r['id']]['correct'], False)
        r['final_answer'] = 'October 28, 2012'
        with self.assertRaisesRegex(ValueError, 'Stale review'):
            evaluate([r], {r['id']: review})

    def test_unknown_native_label_and_duplicate_id_fail(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'test.jsonl'
            r = row()
            p.write_text(json.dumps(r) + '\n' + json.dumps(r) + '\n')
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                load_rows(d)
            r['steps'][0]['faithfulness'] = None
            p.write_text(json.dumps(r) + '\n')
            with self.assertRaisesRegex(ValueError, 'step labels'):
                load_rows(d)

    def test_duplicate_review_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'reviews.json'
            v = {'id': 'trace', 'correct': True, 'reason': 'same', 'record_sha256': 'hash'}
            p.write_text(json.dumps({'schema': VERSION, 'reviewer_type': 'assistant', 'decisions': [v, v]}))
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                load_reviews(p)

    def test_cache_coverage_and_invalid_counts_fail(self):
        with self.assertRaisesRegex(ValueError, 'exactly match'):
            features([row()], {})
        with self.assertRaisesRegex(ValueError, 'Invalid NLI count'):
            features([row()], {'trace': {'nli_unsup_ctx': 2}})


class StatisticalTests(unittest.TestCase):
    def test_undefined_resamples_cannot_be_silently_dropped_from_ci(self):
        result = interval(.2, [.1, .2, .3, np.nan], 'rho')
        self.assertIsNone(result['ci95'])
        self.assertEqual(result['bootstrap_valid'], 3)
        self.assertIsNotNone(result['conditional_valid_resample_percentiles'])

    def test_auc_ties_direction_and_one_class(self):
        self.assertEqual(aucs([0, 1], [1, 1])[0], .5)
        self.assertEqual(aucs([0, 1], [1, 0])[0], 0)
        self.assertEqual(aucs([0, 1], [0, 1])[0], 1)
        self.assertTrue(np.isnan(aucs([1, 1], [0, 1])[0]))

    def test_vectorized_rho_matches_scipy(self):
        x = np.array([[1, 5], [2, 2], [2, 3], [4, 8], [5, 6]])
        y = np.array([.1, .3, .3, .2, .9])
        for j, value in enumerate(rhos(y, x)):
            self.assertAlmostEqual(value, spearmanr(y, x[:, j]).statistic)
        self.assertTrue(np.isnan(rhos([1, 1, 1], [[1], [2], [3]])[0]))

    def test_clusters_not_individual_rows_are_resampled(self):
        for ix in cluster_draws(['a', 'a', 'b'], 20, 0):
            self.assertEqual(sum(ix == 0), sum(ix == 1))

    def test_paired_identical_arms_have_exactly_zero_difference(self):
        pop = {str(i): {'y': i % 2, 'correct': 0, 'cluster': str(i // 2)} for i in range(8)}
        arms = {a: {rid: float(rid) for rid in pop} for a in 'ABCD'}
        result = compare(pop, arms, set(pop), 40, 0)
        for v in result['paired_contrasts'].values():
            self.assertEqual(v['delta_auroc'], 0)
            self.assertEqual(v['ci95'], [0, 0])
        # An unmatched, highly discriminative extra A score must not alter the comparison.
        arms['A']['unmatched'] = 100
        self.assertEqual(result, compare(pop, arms, set(pop), 40, 0))

    def test_correct_responses_are_outside_original_split(self):
        pop = {'d': {'correct': 0, 'cluster': 'dev'}, 'e': {'correct': 0, 'cluster': 'eval'},
               'c': {'correct': 1, 'cluster': 'new'}}
        arms = {a: {'e': 1, 'c': 1} for a in 'ABCD'}
        result = exposure(pop, arms, {'dev_clusters': ['dev'], 'n_dev_responses': 1, 'n_eval_responses': 1})
        self.assertEqual(result['union_counts'], {'dev': 0, 'evaluation': 1, 'outside_split': 1})
        self.assertEqual(result['evaluation_scored_questions'], 1)

    def test_strict_json_and_frozen_output_protection(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'result.json'
            p.write_text('{"trace":1,"trace":2}')
            with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
                read_json(p)
            with self.assertRaises(FileExistsError):
                save_json(p, {})


if __name__ == '__main__':
    unittest.main()
