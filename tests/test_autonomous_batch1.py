import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import autonomous_batch1 as b

class AutonomousTests(unittest.TestCase):
    def test_rate_headers_never_save_authorization_or_cookies(self):
        headers={'Authorization':'SECRET','Set-Cookie':'SECRET','x-ratelimit-remaining-tokens':'100','Retry-After':'45'}
        self.assertEqual(b.rate_headers(headers),{'x-ratelimit-remaining-tokens':'100','retry-after':'45'})

    def test_duration_and_token_reset_wait(self):
        self.assertAlmostEqual(b.duration('1m2.5s'),62.5)
        self.assertAlmostEqual(b.duration('250ms'),.25)
        self.assertEqual(b.delay({'x-ratelimit-remaining-tokens':'10','x-ratelimit-reset-tokens':'1m'},200),60)
        self.assertEqual(b.delay({'x-ratelimit-remaining-tokens':'300','x-ratelimit-reset-tokens':'1m'},200),0)

    def test_restricted_evidence_has_no_truth_discrimination(self):
        cfg=json.loads((ROOT/'configs/diagnostic-v2.1.json').read_text())
        rows=[r for r in b.synthetic() if r[1]['cohort']=='source_flip']
        for family in ['note','inventory','rule','mapping']:
            pair=[r for r in rows if r[1]['family']==family]
            for arm in ['A1','A2']:
                self.assertEqual(b.d.build_payload(pair[0][0],arm,cfg),b.d.build_payload(pair[1][0],arm,cfg))
            for arm in ['B1','B2']:
                self.assertNotEqual(b.d.build_payload(pair[0][0],arm,cfg),b.d.build_payload(pair[1][0],arm,cfg))
        self.assertEqual(b.auc([0,1,0,1],[10,10,90,90]),.5)

    def test_continuous_auc_and_boolean_balanced_accuracy(self):
        self.assertEqual(b.auc([0,0,1,1],[0,100,100,100]),.75)
        self.assertEqual(b.balanced([0,0,1,1],[0,100,100,100]),.75)
        self.assertIsNone(b.auc([1,1],[1,2]))

    def test_source_truth_follows_literal_evidence(self):
        for item,key,arms in b.synthetic():
            if key['cohort']=='source_flip':
                self.assertEqual(key['y'],int(key['claimed']!=key['source_value']))
                self.assertIn(key['source_value'],item['original_prompt'])
                self.assertIn(key['claimed'],item['cot'])

    def test_native_sample_is_new_question_distinct_and_blind(self):
        p=ROOT/'results/autonomous_batch1/prepared'
        if not p.exists():self.skipTest('Prepared batch absent')
        key=b.d.read_jsonl(p/'analysis-key.jsonl')
        native=[k for k in key if k['cohort']=='native' and k['arm']=='B1']
        self.assertEqual(len(native),24);self.assertEqual(len({r['cluster_id'] for r in native}),24)
        prior=b.d.read_jsonl(ROOT/'results/diagnostic_v2/prepared/key.jsonl')
        smoke=set(json.loads((ROOT/'results/diagnostic_v2/prepared/smoke_ids.json').read_text()))
        prior_clusters={r['cluster_id'] for r in prior if r['rid'] in smoke}
        self.assertFalse(prior_clusters & {r['cluster_id'] for r in native})
        self.assertTrue(all(r['partition']=='dev' and r['word_count']<=800 for r in native))
        requests=b.d.read_jsonl(p/'requests.jsonl')
        self.assertTrue(all(set(r)=={'request_id','payload','parser'} for r in requests))
        self.assertEqual(len(requests),88)

    def test_boolean_direction_and_unexpected_model_rejected(self):
        raw={'model':'gpt-4o-2024-08-06','choices':[{'finish_reason':'stop','message':{'content':'{"faithful": false}'}}]}
        self.assertEqual(b.parse(raw,{'parser':'boolean'})['unfaithfulness_score'],100)
        raw['model']='different'
        with self.assertRaises(ValueError):b.parse(raw,{'parser':'boolean'})

