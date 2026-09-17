"""Tests for the pilot replication: selection rule, procedure identity, lock enforcement."""
import importlib.util, json, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def load(n, r):
    s = importlib.util.spec_from_file_location(n, ROOT / r); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
d = load('diagnostic', 'scripts/diagnostic_v2.py'); ra = load('repanalysis', 'scripts/replication_analysis.py')
PREP = ROOT / 'results/diagnostic_v2/prepared-replication-v2'
CFG = json.loads((ROOT / 'configs/pilot-replication-v2.json').read_text())
PILOT_CFG = json.loads((ROOT / 'configs/diagnostic-v2.1-pilot-r2.json').read_text())

class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.key = {json.loads(l)['rid']: json.loads(l) for l in (PREP / 'key.jsonl').read_text().splitlines() if l.strip()}
        self.pilot_key = {json.loads(l)['rid']: json.loads(l) for l in (ROOT / 'results/diagnostic_v2/prepared/key.jsonl').read_text().splitlines() if l.strip()}
        self.pilot_rids = {json.loads(l)['rid'] for l in (ROOT / 'results/diagnostic_v2/pilot-4arm-rep3c/responses.jsonl').read_text().splitlines() if l.strip()}
    def test_composition_and_disjointness(self):
        from collections import Counter
        self.assertEqual(len(self.key), 70)
        self.assertEqual(Counter(k['y'] for k in self.key.values()), Counter({1: 52, 0: 18}))
        self.assertEqual(Counter(k['task'] for k in self.key.values()),
                         Counter(self.pilot_key[r]['task'] for r in self.pilot_rids))
        self.assertFalse(set(self.key) & self.pilot_rids, 'response overlap with the pilot')
        pilot_clusters = {self.pilot_key[r]['cluster_id'] for r in self.pilot_rids}
        self.assertFalse({k['cluster_id'] for k in self.key.values()} & pilot_clusters, 'question-cluster overlap')
    def test_every_available_faithful_was_taken(self):
        import random
        items = [json.loads(l) for l in (ROOT / 'results/diagnostic_v2/prepared/items.jsonl').read_text().splitlines() if l.strip()]
        dev = [r for r in items if r['partition'] == 'dev']
        random.Random(PILOT_CFG['seed']).shuffle(dev)
        pc = {r['cluster_id'] for r in dev[:70]}
        avail = [r for r in dev if r['cluster_id'] not in pc and self.pilot_key[r['rid']]['y'] == 0]
        self.assertEqual(len(avail), sum(1 for k in self.key.values() if k['y'] == 0))

class ProcedureIdentityTests(unittest.TestCase):
    def test_payload_affecting_fields_match_the_pilot(self):
        for f in ('model', 'temperature', 'max_tokens', 'response_format', 'response_formats',
                  'common_instruction', 'generic_rubric', 'component_rubric', 'evidence_policy', 'seed'):
            self.assertEqual(CFG[f], PILOT_CFG[f], f)
        self.assertEqual(CFG['arms'], ['A1', 'A2'])
    def test_plan_payloads_are_byte_identical_to_the_pilot_procedures(self):
        plan = d.request_plan(PREP, CFG, 'dev', 3)
        self.assertEqual(len(plan), 420)
        key = {k['rid']: k for k in d.read_jsonl(PREP / 'key.jsonl')}
        pilot_key = {k['rid']: k for k in d.read_jsonl(ROOT / 'results/diagnostic_v2/prepared/key.jsonl')}
        pilot_rids = {json.loads(l)['rid'] for l in (ROOT / 'results/diagnostic_v2/pilot-4arm-rep3c/responses.jsonl').read_text().splitlines() if l.strip()}
        excluded = {pilot_key[r]['cluster_id'] for r in pilot_rids}
        checks = d.replication_payload_checks(plan, key, CFG, PILOT_CFG, excluded)
        self.assertEqual(checks['payload_identical_to_reference_procedure'], 140)
        self.assertEqual(checks['question_clusters'], 55)
    def test_changed_procedure_is_rejected(self):
        import copy
        bad = copy.deepcopy(CFG); bad['component_rubric'] += ' extra sentence.'
        plan = d.request_plan(PREP, bad, 'dev', 1)
        key = {k['rid']: k for k in d.read_jsonl(PREP / 'key.jsonl')}
        with self.assertRaises(ValueError):
            d.replication_payload_checks(plan, key, bad, PILOT_CFG, set())
    def test_excluded_cluster_is_rejected(self):
        plan = d.request_plan(PREP, CFG, 'dev', 1)
        key = {k['rid']: k for k in d.read_jsonl(PREP / 'key.jsonl')}
        with self.assertRaises(ValueError):
            d.replication_payload_checks(plan, key, CFG, PILOT_CFG, {key[plan[0]['rid']]['cluster_id']})

class LockEnforcementTests(unittest.TestCase):
    def test_a_present_lock_is_enforced_on_a_non_eval_partition(self):
        """The new guard: a frozen plan cannot be sidestepped by running under another partition."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for n in ('items.jsonl', 'key.jsonl', 'smoke_ids.json', 'manifest.json'):
                (tmp / n).write_bytes((PREP / n).read_bytes())
            (tmp / 'lock.json').write_text(json.dumps({'identity': {'config_sha256': 'wrong'}}))
            class A:
                prepared = tmp; config = ROOT / 'configs/pilot-replication-v2.json'; partition = 'dev'
                output = tmp / 'out'; repeats = 3; max_items = None; dry_run = True
                endpoint = 'x'; max_http_requests = 500; max_seconds = 60
            with self.assertRaises(ValueError): d.run(A)

class EstimatorTests(unittest.TestCase):
    def test_auroc_edges(self):
        self.assertEqual(ra.auroc([0, 0, 1, 1], [1, 2, 3, 4]), 1.0)
        self.assertEqual(ra.auroc([0, 0, 1, 1], [4, 3, 2, 1]), 0.0)
        self.assertIsNone(ra.auroc([1, 1], [1, 2]))
    def test_reproduces_the_published_pilot_figures(self):
        r = ra.analyse(ROOT / 'results/diagnostic_v2/pilot-4arm-rep3c', ROOT / 'results/diagnostic_v2/prepared', 'pilot', 500, 0)
        self.assertAlmostEqual(r['auroc']['A1'], 0.2175, places=3)
        self.assertAlmostEqual(r['auroc']['A2'], 0.5108, places=3)
        self.assertAlmostEqual(r['contrast_A2_minus_A1'], 0.2933, places=3)

if __name__ == '__main__': unittest.main()
