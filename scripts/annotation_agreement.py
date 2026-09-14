"""Inter-annotator agreement for reviewer annotation files exported by review-form.html.

Cohen's kappa and percent agreement per question on the items BOTH reviewers answered (blank
answers excluded), plus a disagreement list for adjudication. Human files only; never pass a
model-produced file as a reviewer.

Usage: python scripts/annotation_agreement.py --a annotations-suramya.jsonl --b annotations-dikshant.jsonl --out agreement
"""
import argparse, json
from collections import Counter
from pathlib import Path

QS = ['Q_b_trace_makes_claim', 'Q_c_evidence_status', 'Q_d_accusation_follows']

def load(p):
    rows = {}
    for l in Path(p).read_text().splitlines():
        if l.strip():
            r = json.loads(l); rows[r['assessment_id']] = r
    return rows

def kappa(pairs):
    n = len(pairs)
    if n == 0: return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)

ap = argparse.ArgumentParser(); ap.add_argument('--a', required=True); ap.add_argument('--b', required=True); ap.add_argument('--out', required=True)
args = ap.parse_args(); A, B = load(args.a), load(args.b)
out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
report, disagreements = {'reviewers': [next(iter(A.values()))['reviewer'], next(iter(B.values()))['reviewer']], 'questions': {}}, []
for q in QS:
    pairs = [(A[i][q], B[i][q]) for i in A.keys() & B.keys() if A[i].get(q) and B[i].get(q)]
    report['questions'][q] = {'n_both_answered': len(pairs),
                              'percent_agreement': (sum(a == b for a, b in pairs) / len(pairs)) if pairs else None,
                              'cohen_kappa': kappa(pairs),
                              'confusion': dict(Counter(f'{a}|{b}' for a, b in pairs))}
    disagreements += [{'assessment_id': i, 'question': q, 'a': A[i][q], 'b': B[i][q]}
                      for i in A.keys() & B.keys() if A[i].get(q) and B[i].get(q) and A[i][q] != B[i][q]]
(out / 'agreement.json').write_text(json.dumps(report, indent=2) + '\n')
(out / 'disagreements.jsonl').write_text(''.join(json.dumps(d) + '\n' for d in disagreements))
print(json.dumps(report, indent=2)); print(f'{len(disagreements)} disagreements -> {out}/disagreements.jsonl')
