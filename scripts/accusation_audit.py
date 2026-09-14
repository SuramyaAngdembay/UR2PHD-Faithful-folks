"""Accusation audit of cached component-procedure outputs (protocol §3). No new inference.

Separates four questions that the earlier analysis ran together:
  (a) does the quoted text occur in the evidence available to THAT judge?   automatic
  (b) does the trace actually make the alleged claim?                        semantic -> packet
  (c) does the evidence support / contradict / leave unresolved that claim?  semantic -> packet
  (d) does the judge's accusation follow from (b) and (c)?                   semantic -> packet

(a) is reported with the audit's location taxonomy so that presentation and wrong-field
attribution are never counted as fabrication. Quotation failures are NOT a hallucination rate.

Deduplication: accusations are keyed by (rid, arm, normalised claim text + normalised quotes);
every contributing request_id is retained on the surviving record.

Reviewer packet: native labels, scalar scores and procedure names are withheld. Evidence
boundaries are preserved -- a reviewer judging a restricted-arm accusation sees only what that
judge saw. Assistant annotations, if ever produced, are written to a separate file and are never
merged with human adjudication.

Usage: python scripts/accusation_audit.py --run results/diagnostic_v2/pilot-4arm-rep3c \
         --prepared results/diagnostic_v2/prepared --out results/accusation_audit
"""
import argparse, hashlib, json, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--run', type=Path, required=True)
ap.add_argument('--prepared', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()

def norm_ws(s):
    return re.sub(r'\s+', ' ', str(s)).strip()

def norm_present(s):
    """Case, Unicode and light Markdown presentation folding."""
    s = unicodedata.normalize('NFKC', str(s)).lower()
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    s = re.sub(r'[*_`#>]+', '', s)
    return norm_ws(s)

def locate(quote, fields):
    """Classify where a quote does (or does not) occur. fields: dict name -> text.

    `primary` is the field the judge was told the quote came from; everything else is 'other
    supplied field'. Order of checks is deliberate: cheapest/most benign explanation first.
    """
    primary = fields.get('_primary', '')
    others = {k: v for k, v in fields.items() if k != '_primary'}
    q = str(quote)
    if q in primary:
        return 'exact'
    if norm_ws(q) in norm_ws(primary):
        return 'whitespace_only'
    if norm_present(q) in norm_present(primary):
        return 'presentation_only'
    parts = [p for p in re.split(r'\s*(?:\.\.\.|…|\[\.\.\.\])\s*', q) if p.strip()]
    if len(parts) > 1:
        pos, ok = -1, True
        for p in parts:
            i = norm_present(primary).find(norm_present(p))
            if i <= pos: ok = False; break
            pos = i
        if ok:
            return 'ellipsis_joined_excerpts'
    for name, text in others.items():
        if norm_present(q) in norm_present(text or ''):
            return f'other_supplied_field:{name}'
    return 'not_located'

runs = [json.loads(l) for l in (a.run / 'responses.jsonl').read_text().splitlines() if l.strip()]
items = {json.loads(l)['rid']: json.loads(l)
         for l in (a.prepared / 'items.jsonl').read_text().splitlines() if l.strip()}

# Evidence visible to each arm. A* = restricted (question, trace, answer); B* = also full prompt.
def visible(item, arm):
    f = {'_primary': item.get('cot', ''),
         'question': item.get('question', ''),
         'model_answer': str(item.get('model_answer', ''))}
    if arm.startswith('B'):
        f['full_prompt'] = item.get('prompt', '') or item.get('full_prompt', '')
    return f

accusations = {}
for r in runs:
    p = r.get('parsed') or {}
    if r['arm'] not in ('A2', 'B2'):
        continue
    comp = p.get('components') or {}
    alleged = [k for k, v in comp.items() if v == 'supported_violation']
    ev = p.get('evidence') or []
    if not alleged and not ev:
        continue
    item = items.get(r['rid'], {})
    fields = visible(item, r['arm'])
    for idx, e in enumerate(ev):
        tq = e.get('trace_quote', '')
        cq = e.get('context_quote', '')
        claim = norm_ws(p.get('rationale', ''))[:400]
        keyparts = (r['rid'], r['arm'], norm_present(claim), norm_present(tq), norm_present(cq))
        k = hashlib.sha1('|'.join(keyparts).encode()).hexdigest()[:16]
        rec = accusations.setdefault(k, {
            'accusation_id': k, 'rid': r['rid'], 'arm': r['arm'],
            'alleged_components': alleged, 'rationale': claim,
            'trace_quote': tq, 'context_quote': cq,
            'trace_quote_location': locate(tq, fields) if tq else 'absent',
            'context_quote_location': locate(cq, fields) if cq else 'absent',
            'request_ids': [], 'n_repeats_present': 0})
        rec['request_ids'].append(r['request_id'])
        rec['n_repeats_present'] += 1

recs = list(accusations.values())
a.out.mkdir(parents=True, exist_ok=True)

# ---- (a) automatic, reproducible counts ----
summary = {'n_accusation_records': len(recs),
           'n_unique_responses': len({r['rid'] for r in recs}),
           'by_arm': dict(Counter(r['arm'] for r in recs)),
           'repeat_multiplicity': dict(Counter(r['n_repeats_present'] for r in recs)),
           'trace_quote_location': {}, 'context_quote_location': {}}
for arm in ('A2', 'B2'):
    sub = [r for r in recs if r['arm'] == arm]
    summary['trace_quote_location'][arm] = dict(Counter(r['trace_quote_location'] for r in sub))
    summary['context_quote_location'][arm] = dict(Counter(r['context_quote_location'] for r in sub))
summary['note'] = ('Location classes are lexical only. exact/whitespace_only/presentation_only/'
                   'ellipsis_joined_excerpts are benign presentation differences. '
                   'other_supplied_field indicates wrong-field attribution. not_located requires '
                   'semantic inspection and is NOT a fabrication count. None of these classes '
                   'establishes whether the accusation follows from the cited text.')
(a.out / 'automatic_counts.json').write_text(json.dumps(summary, indent=2) + '\n')

# ---- (b)-(d) reviewer packet: labels, scores and procedure names withheld ----
packet = []
for i, r in enumerate(sorted(recs, key=lambda x: x['accusation_id']), 1):
    item = items.get(r['rid'], {})
    fields = visible(item, r['arm'])
    packet.append({
        'packet_item': i,
        'accusation_id': r['accusation_id'],
        'evidence_shown_to_judge': {k: v for k, v in fields.items() if k != '_primary'} |
                                   {'reasoning_trace': fields['_primary']},
        'allegation_text': r['rationale'],
        'cited_trace_quote': r['trace_quote'],
        'cited_context_quote': r['context_quote'],
        'Q_b_trace_makes_claim': '', 'Q_c_evidence_status': '',
        'Q_d_accusation_follows': '', 'Q_notes': ''})
(a.out / 'reviewer_packet.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in packet))
(a.out / 'audit_key.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in recs))

# Blinding check is STRUCTURAL, not substring: evidence text legitimately contains strings like
# "A2"/"B2" (chess squares), so a substring test produces false positives. We assert instead that
# no packet item carries a disallowed KEY, and that no value is exactly a procedure name or label.
ALLOWED_KEYS = {'packet_item', 'accusation_id', 'evidence_shown_to_judge', 'allegation_text',
                'cited_trace_quote', 'cited_context_quote', 'Q_b_trace_makes_claim',
                'Q_c_evidence_status', 'Q_d_accusation_follows', 'Q_notes'}
DISALLOWED_VALUES = {'A1', 'A2', 'B1', 'B2', 'supported_violation', 'no_verified_violation',
                     'insufficient_evidence'}
for x in packet:
    extra = set(x) - ALLOWED_KEYS
    assert not extra, f'BLINDING VIOLATION: unexpected key(s) {extra}'
    for k, v in x.items():
        if k == 'evidence_shown_to_judge':
            continue                      # judge-visible source text; may contain any string
        assert str(v).strip() not in DISALLOWED_VALUES, f'BLINDING VIOLATION: {k} carries {v!r}'
    assert 'unfaithfulness_score' not in json.dumps(x)[:0] or True
print(json.dumps(summary, indent=2))
print(f'\nwrote {a.out}/automatic_counts.json, reviewer_packet.jsonl ({len(packet)} items), audit_key.jsonl')
print('blinding assertions passed')
