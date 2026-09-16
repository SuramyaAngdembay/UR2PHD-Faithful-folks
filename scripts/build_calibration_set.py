"""Select the 40-accusation calibration subset of the repaired reviewer packet.

Rule (seed 0): among assessments alleging >=1 supported violation, pick 40 from 40 distinct
responses, 20 from each evidence arm, one assessment per response chosen at random. The reviewer
directory receives only blinded packet items (verbatim from reviewer/packet.jsonl, renumbered);
the selection key (arm, rid) is written OUTSIDE the reviewer directory. Both annotators review
the same 40 items so agreement can be computed.

Usage: python scripts/build_calibration_set.py --final results/accusation_audit_repair/2026-09-14-final
"""
import argparse, hashlib, json, random
from collections import defaultdict
from pathlib import Path

ap = argparse.ArgumentParser(); ap.add_argument('--final', type=Path, required=True); ap.add_argument('--n', type=int, default=40); ap.add_argument('--seed', type=int, default=0)
a = ap.parse_args()
K = [json.loads(l) for l in (a.final / 'assessment-key.jsonl').read_text().splitlines() if l.strip()]
P = {json.loads(l)['assessment_id']: json.loads(l) for l in (a.final / 'reviewer/packet.jsonl').read_text().splitlines() if l.strip()}
acc = [k for k in K if any(v == 'supported_violation' for v in (k.get('components') or {}).values())]
rng = random.Random(a.seed)
by_arm = defaultdict(lambda: defaultdict(list))
for k in acc: by_arm[k['arm']][k['rid']].append(k)
chosen, used = [], set()
for arm in sorted(by_arm):
    rids = [r for r in sorted(by_arm[arm]) if r not in used]; rng.shuffle(rids)
    for rid in rids[: a.n // len(by_arm)]:
        used.add(rid); chosen.append(rng.choice(by_arm[arm][rid]))
assert len(chosen) == a.n and len({k['rid'] for k in chosen}) == a.n, 'selection rule violated'
out = a.final / 'reviewer/calibration-40'; out.mkdir(parents=True, exist_ok=True)
items = []
for i, k in enumerate(sorted(chosen, key=lambda k: k['assessment_id']), 1):
    it = dict(P[k['assessment_id']]); it['packet_item'] = i; items.append(it)
(out / 'packet.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in items))
readme = (a.final / 'reviewer/README.md').read_text()
(out / 'README.md').write_text('# Calibration subset (40 accusations)\n\nSame questions and rules as the full packet; these 40 items are the shared set for two annotators, chosen by a fixed rule (seed 0): 40 distinct responses, 20 per evidence arm, one accusation-bearing assessment each. Every item alleges at least one violation, so not_applicable should be rare here.\n\n---\n\n' + readme)
sel = [{'packet_item': it['packet_item'], 'assessment_id': it['assessment_id'], 'rid': k['rid'], 'arm': k['arm']} for it, k in zip(items, sorted(chosen, key=lambda k: k['assessment_id']))]
(a.final / 'calibration-40-selection-key.jsonl').write_text(''.join(json.dumps(s) + '\n' for s in sel))
man = {'rule': '40 accusation-bearing assessments, 40 distinct responses, 20 per arm, one per response at random', 'seed': a.seed,
       'source_packet_sha256': hashlib.sha256((a.final / 'reviewer/packet.jsonl').read_bytes()).hexdigest(),
       'packet_sha256': hashlib.sha256((out / 'packet.jsonl').read_bytes()).hexdigest(), 'n': len(items)}
(out / 'manifest.json').write_text(json.dumps(man, indent=2) + '\n')
print(f'calibration set: {len(items)} items from {len({s["rid"] for s in sel})} responses; arms {dict((arm, sum(s["arm"]==arm for s in sel)) for arm in sorted({s["arm"] for s in sel}))}')
