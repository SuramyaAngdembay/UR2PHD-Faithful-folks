import importlib.util, json, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
d = load('diagnostic', 'scripts/diagnostic_v2.py'); b = load('posbuilder', 'scripts/build_position_controls.py')
pa = load('posanalysis', 'scripts/position_analysis.py')
C13 = json.loads((ROOT / 'configs/controlled-verification-v1.3.json').read_text()); C1 = json.loads((ROOT / 'configs/controlled-verification-v1.json').read_text())

class PositionBuilderTests(unittest.TestCase):
    def test_builder_integrity_and_replication_links(self):
        items, key, problems = b.build(ROOT / 'data/constructed_controls/v1/items.jsonl')
        self.assertEqual(problems, []); self.assertEqual(len(items), 24)
        self.assertEqual(sum(k['construction']['replicates_v1'] for k in key), 12)
        self.assertEqual(sum(k['member'] == 'before' for k in key), 12)
    def test_config_identical_to_v1_except_arms(self):
        for k in ('model', 'temperature', 'max_tokens', 'response_formats', 'common_instruction', 'generic_rubric', 'component_rubric', 'schema_family'):
            self.assertEqual(C13[k], C1[k], k)
        self.assertEqual(C13['arms'], ['B1', 'B2'])
    def test_prepare_and_payload_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); items, key, _ = b.build(ROOT / 'data/constructed_controls/v1/items.jsonl')
            src = tmp / 'src'; src.mkdir()
            (src / 'items.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in items))
            (src / 'key.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in key))
            (src / 'manifest.json').write_text(json.dumps({'builder_sha256': 't', 'files': {n: d.file_hash(src / n) for n in ('items.jsonl', 'key.jsonl')}}))
            class A: source = src; output = tmp / 'prep'; expected_analysed = 24; no_smoke = True
            d.prepare_constructed(A)
            plan = d.request_plan(tmp / 'prep', C13, 'eval', 3); self.assertEqual(len(plan), 144)
            checks = d.payload_checks(plan, {k['rid']: k for k in key}, C13)
            self.assertEqual(checks, {'attribution_full_different': 24})
    def test_sign_test(self):
        self.assertAlmostEqual(pa.sign_test([1, 1, 1, 1, 1, 0])['p_two_sided'], 2 / 32)
        self.assertIsNone(pa.sign_test([0, 0])['p_two_sided'])

if __name__ == '__main__': unittest.main()
