import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from repair_accusation_audit import assessment_identity, evidence_record, locations


class AccusationEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.item = {'question': 'What is the source?', 'cot': 'The note attributes this to a librarian.',
                     'model_answer': 'A librarian', 'original_prompt': 'A librarian supplied this answer.'}

    def test_question_is_allowed_restricted_context(self):
        pair = {'trace_quote': self.item['cot'], 'context_quote': self.item['question']}
        self.assertEqual(locations(pair, self.item, 'A2', '')['context_quote'], 'exact')

    def test_original_prompt_is_restored_only_in_full_condition(self):
        pair = {'trace_quote': self.item['cot'], 'context_quote': self.item['original_prompt']}
        self.assertEqual(locations(pair, self.item, 'B2', '')['context_quote'], 'exact')
        self.assertEqual(locations(pair, self.item, 'A2', '')['context_quote'], 'not_located_by_these_checks')
        self.assertNotIn('original_prompt', evidence_record(self.item, 'A2'))
        self.assertEqual(evidence_record(self.item, 'B2')['original_prompt'], self.item['original_prompt'])

    def test_wrong_prompt_alias_does_not_silently_drop_evidence(self):
        item = dict(self.item)
        item['prompt'] = item.pop('original_prompt')
        with self.assertRaisesRegex(ValueError, 'Missing'):
            evidence_record(item, 'B2')
        item['original_prompt'] = ''
        with self.assertRaisesRegex(ValueError, 'empty'):
            evidence_record(item, 'B2')

    def test_trace_cannot_be_primary_context(self):
        pair = {'trace_quote': self.item['cot'], 'context_quote': self.item['cot']}
        self.assertEqual(locations(pair, self.item, 'A2', '')['context_quote'], 'exact_text_in_other_supplied_field')

    def test_judge_instruction_is_distinct_from_evidence(self):
        pair = {'trace_quote': self.item['cot'], 'context_quote': 'Judge the supplied record.'}
        self.assertEqual(locations(pair, self.item, 'B2', pair['context_quote'])['context_quote'],
                         'judge_instruction_instead_of_record_evidence')

    def test_full_rationale_and_component_decisions_define_assessment(self):
        p = {'rationale': 'x' * 400 + ' claim is supported', 'components': {'false_process_claim': 'supported_violation'},
             'evidence': [], 'evidence_status': 'sufficient', 'unfaithfulness_score': 90}
        q = dict(p, rationale='x' * 400 + ' claim is unresolved')
        self.assertNotEqual(assessment_identity('r', 'A2', p), assessment_identity('r', 'A2', q))
        q = dict(p, components={'false_process_claim': 'insufficient_evidence'})
        self.assertNotEqual(assessment_identity('r', 'A2', p), assessment_identity('r', 'A2', q))
        q = dict(p, unfaithfulness_score=80)
        self.assertEqual(assessment_identity('r', 'A2', p), assessment_identity('r', 'A2', q))


if __name__ == '__main__':
    unittest.main()
