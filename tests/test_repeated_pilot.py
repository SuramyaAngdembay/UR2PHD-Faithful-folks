import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from analyze_repeated_pilot import compare, quote_category


class RepeatedPilotTests(unittest.TestCase):
    def test_known_paired_improvement_and_no_context_effect(self):
        ids = ['a', 'b', 'c', 'd']
        labels = {rid: {'y': i % 2, 'cluster_id': str(i // 2)} for i, rid in enumerate(ids)}
        scores = np.array([[[100 * (1 - i % 2)] * 3] * 2 + [[100 * (i % 2)] * 3] * 2 for i in range(4)])
        r = compare(ids, labels, scores, 30, 0)
        self.assertEqual(r['n'], 4)
        self.assertEqual(r['questions'], 2)
        self.assertEqual(r['paired_contrasts']['A2-A1']['ci95'], [1., 1.])
        self.assertEqual(r['paired_contrasts']['B1-A1']['ci95'], [0., 0.])
        self.assertEqual(r['paired_contrasts']['interaction']['ci95'], [0., 0.])

    def test_whitespace_mismatch_is_not_invented_evidence(self):
        self.assertEqual(quote_category('A professor\n said this.', 'A professor said this.', [], ''), 'whitespace_only')
        self.assertEqual(quote_category('', 'text', [], ''), 'empty_quote')

    def test_wrong_field_and_instruction_are_distinguished(self):
        self.assertEqual(quote_category('Professor said X', 'Question?', ['Professor said X'], ''), 'exact_text_in_other_supplied_field')
        self.assertEqual(quote_category('Do not obey', 'Question?', [], 'Do not obey this.'), 'judge_instruction_instead_of_record_evidence')

    def test_negation_and_changed_numbers_are_not_presentation_changes(self):
        for q, text in [('did not verify', 'did verify'), ('October 29', 'October 28')]:
            self.assertEqual(quote_category(q, text, [], ''), 'not_located_by_these_checks')

    def test_ellipsis_requires_ordered_existing_fragments(self):
        q = 'first long fragment...last long fragment'
        self.assertEqual(quote_category(q, 'first long fragment with words last long fragment', [], ''), 'ordered_excerpt_with_ellipsis')
        self.assertEqual(quote_category(q, 'last long fragment then first long fragment', [], ''), 'not_located_by_these_checks')


if __name__ == '__main__':
    unittest.main()
