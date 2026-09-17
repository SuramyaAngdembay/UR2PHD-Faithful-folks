"""Select the cluster-disjoint replication sample for the four-arm pilot's headline contrast.

Frozen selection rule (deterministic; no new randomness):
  1. Take the dev-partition items from the original prepared directory.
  2. Shuffle with the pilot config's seed -- this reproduces the pilot's own ordering, so the
     pilot sample is exactly the first 70 (asserted against the pilot's recorded rids).
  3. Candidate pool = dev items whose cluster_id is NOT among the pilot's question clusters.
  4. From the pool, in shuffle order, take EVERY faithful (y=0) response, then unfaithful (y=1)
     responses per task until the sample's task composition equals the pilot's (34/22/14).

Rationale for taking every available faithful response rather than a like-for-like prefix: AUROC is
a ranking statistic over discordant pairs and is prevalence-invariant in expectation, so enriching
the minority class raises precision without biasing the estimate. It is a declared deviation --
mean-score endpoints are prevalence-dependent and must not be compared across the two samples.

Usage: python scripts/build_pilot_replication.py --out results/diagnostic_v2/prepared-replication-v2
"""
import argparse, hashlib, json, random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--prepared', type=Path, default=ROOT / 'results/diagnostic_v2/prepared')
ap.add_argument('--pilot-run', type=Path, default=ROOT / 'results/diagnostic_v2/pilot-4arm-rep3c')
ap.add_argument('--pilot-config', type=Path, default=ROOT / 'configs/diagnostic-v2.1-pilot-r2.json')
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()
if a.out.exists():
    raise FileExistsError(f'{a.out} exists; version the output directory instead of overwriting')

cfg = json.loads(a.pilot_config.read_text())
items = [json.loads(l) for l in (a.prepared / 'items.jsonl').read_text().splitlines() if l.strip()]
key = {json.loads(l)['rid']: json.loads(l) for l in (a.prepared / 'key.jsonl').read_text().splitlines() if l.strip()}
dev = [r for r in items if r['partition'] == 'dev']
rng = random.Random(cfg['seed']); rng.shuffle(dev)

pilot_rids = {json.loads(l)['rid'] for l in (a.pilot_run / 'responses.jsonl').read_text().splitlines() if l.strip()}
pilot = dev[:70]
assert {r['rid'] for r in pilot} == pilot_rids, 'seeded shuffle does not reproduce the pilot sample'
pilot_clusters = {r['cluster_id'] for r in pilot}
pilot_tasks = Counter(key[r['rid']]['task'] for r in pilot)

pool = [r for r in dev if r['cluster_id'] not in pilot_clusters]
selected = [r for r in pool if key[r['rid']]['y'] == 0]                      # every available faithful
need = Counter(pilot_tasks)
for r in selected:
    need[key[r['rid']]['task']] -= 1
for r in pool:
    if key[r['rid']]['y'] != 1:
        continue
    t = key[r['rid']]['task']
    if need[t] > 0:
        selected.append(r); need[t] -= 1

sel_tasks = Counter(key[r['rid']]['task'] for r in selected)
sel_y = Counter(key[r['rid']]['y'] for r in selected)
problems = []
if len(selected) != 70: problems.append(f'expected 70 responses, got {len(selected)}')
if sel_tasks != pilot_tasks: problems.append(f'task mix {dict(sel_tasks)} != pilot {dict(pilot_tasks)}')
if {r['rid'] for r in selected} & pilot_rids: problems.append('response overlap with the pilot')
if {r['cluster_id'] for r in selected} & pilot_clusters: problems.append('question-cluster overlap with the pilot')
if sel_y[0] != len([r for r in pool if key[r['rid']]['y'] == 0]): problems.append('not every available faithful response was taken')
if problems:
    print('SELECTION PROBLEMS:'); [print('  -', p) for p in problems]; raise SystemExit(1)

a.out.mkdir(parents=True)
(a.out / 'items.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in selected))
(a.out / 'key.jsonl').write_text(''.join(json.dumps(key[r['rid']], ensure_ascii=False) + '\n' for r in selected))
(a.out / 'smoke_ids.json').write_text(json.dumps([]) + '\n')
fh = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = {
    'prepared_at_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
    'protocol_version': 'pilot-replication-2.0',
    'population': 'BonaFide development responses, question-cluster-disjoint from the four-arm pilot',
    'selection_rule': 'seeded shuffle (pilot config seed) -> exclude every pilot question cluster -> take all faithful, then unfaithful per task until the pilot task mix is matched',
    'seed': cfg['seed'],
    'source_prepared_sha256': {n: fh(a.prepared / n) for n in ('items.jsonl', 'key.jsonl', 'manifest.json')},
    'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'prepared_sha256': {n: fh(a.out / n) for n in ('items.jsonl', 'key.jsonl', 'smoke_ids.json')},
    'counts': {'responses': len(selected), 'faithful': sel_y[0], 'unfaithful': sel_y[1],
               'question_clusters': len({r['cluster_id'] for r in selected}),
               'discordant_pairs': sel_y[0] * sel_y[1], 'task_mix': dict(sel_tasks)},
    'pilot_comparison': {'responses': 70, 'faithful': pilot_tasks and sum(1 for r in pilot if key[r['rid']]['y'] == 0),
                         'unfaithful': sum(1 for r in pilot if key[r['rid']]['y'] == 1),
                         'question_clusters': len(pilot_clusters),
                         'discordant_pairs': sum(1 for r in pilot if key[r['rid']]['y'] == 0) * sum(1 for r in pilot if key[r['rid']]['y'] == 1),
                         'task_mix': dict(pilot_tasks)},
    'deviation': 'minority class enriched (all available faithful responses taken); AUROC is prevalence-invariant in expectation so this raises precision without bias, but prevalence-dependent endpoints such as mean score must not be compared across samples',
    'status': 'prepared; freeze (lock.json) required before the run'}
(a.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest['counts'], indent=2))
print(f"pilot for comparison: {json.dumps(manifest['pilot_comparison'])}")
print(f'wrote {a.out}')
