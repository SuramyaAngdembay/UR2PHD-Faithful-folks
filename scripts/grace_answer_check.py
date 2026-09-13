"""Conservative, auditable GRACE answer equivalence. No substring/F1 gold labels."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

VERSION = 'grace-answer-equivalence-v3'
FIELDS = ('id', 'dataset', 'question', 'options', 'gold_answer', 'final_answer')


def canonical(text):
    """Normalize presentation only; preserve numbers, negation, and word identity."""
    text = unicodedata.normalize('NFKC', str(text)).casefold()
    text = re.sub(r'\[ref_\d+\]', '', text)
    text = text.replace('**', '').replace('`', '').replace('’', "'")
    return ' '.join(text.split()).strip(' \t\r\n.!?"“”')


def record_hash(row):
    payload = {k: row.get(k) for k in FIELDS}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def load_rows(data_dir):
    files = sorted(Path(data_dir).expanduser().glob('*.jsonl'))
    if not files:
        raise ValueError(f'No GRACE JSONLs in {data_dir}')
    rows, seen = [], set()
    for path in files:
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row['id'] in seen:
                raise ValueError(f"Duplicate trace ID: {row['id']}")
            seen.add(row['id'])
            for key in ('question', 'gold_answer', 'final_answer'):
                if not isinstance(row.get(key), str):
                    raise ValueError(f"Invalid {key}: {row['id']}")
            steps = row.get('steps')
            if not steps or any(s.get('faithfulness') not in ('faithful', 'unfaithful') for s in steps):
                raise ValueError(f"Missing/unknown step labels: {row['id']}")
            rows.append(row)
    return rows


def assess(row):
    """Return True/False only for explicit equivalence decisions, else None."""
    gold, answer = canonical(row['gold_answer']), canonical(row['final_answer'])
    def result(value, rule):
        return {'correct': value, 'rule': rule, 'source': 'deterministic',
                'record_sha256': record_hash(row)}
    if not gold:
        return result(None, 'missing_reference')
    if not answer:
        return result(False, 'empty_response')
    options = row.get('options')
    if options:
        match = re.match(r'^([a-e])\s*[).:]\s*(.*)$', gold)
        if not match or ord(match[1]) - ord('a') >= len(options):
            raise ValueError(f"Invalid reference option: {row['id']}")
        gi = ord(match[1]) - ord('a')
        if canonical(match[2]) != canonical(options[gi]):
            raise ValueError(f"Reference letter/text disagreement: {row['id']}")
        pm = re.fullmatch(r'([a-e])(?:\s*[).:](?:\s*(.*))?)?', answer)
        if pm:
            pi = ord(pm[1]) - ord('a')
            if pi >= len(options):
                return result(False, 'invalid_option')
            text = pm[2] or ''
            if not text or canonical(text) == canonical(options[pi]):
                return result(pi == gi, 'explicit_option')
            return result(None, 'option_with_unverified_explanation')
        for i, option in enumerate(options):
            if answer == canonical(option):
                return result(i == gi, 'exact_option_text')
        return result(None, 'unresolved_multiple_choice_response')
    if gold == answer:
        return result(True, 'exact_answer')
    if gold in ('yes', 'no') and answer in ('yes', 'no'):
        return result(False, 'opposite_boolean')
    number = r'[+-]?\d+(?:\.\d+)?%?'
    if re.fullmatch(number, gold) and re.fullmatch(number, answer):
        # Compare explicit values, retaining percentage-unit distinctions.
        from decimal import Decimal
        if gold.endswith('%') == answer.endswith('%'):
            same = Decimal(gold.rstrip('%')) == Decimal(answer.rstrip('%'))
            return result(same, 'explicit_numeric_value')
    date = r'(january|february|march|april|may|june|july|august|september|october|november|december) (\d{1,2}),? (\d{4})'
    gm, am = re.fullmatch(date, gold), re.fullmatch(date, answer)
    if gm and am:
        value = lambda m: (m[1], int(m[2]), int(m[3]))
        return result(value(gm) == value(am), 'explicit_date')
    return result(None, 'requires_answer_equivalence_review')


def load_reviews(path):
    if path is None:
        return {}
    raw = json.loads(Path(path).read_text())
    if raw.get('schema') != VERSION or raw.get('reviewer_type') != 'assistant':
        raise ValueError('Review schema/provenance must be explicit')
    out = {}
    for entry in raw['decisions']:
        if entry['id'] in out:
            raise ValueError('Duplicate review ID')
        if type(entry.get('correct')) not in (bool, type(None)):
            raise ValueError('Review correctness must be boolean or null')
        if not entry.get('reason') or not entry.get('record_sha256'):
            raise ValueError('Review requires reason and input hash')
        out[entry['id']] = entry
    return out


def evaluate(rows, reviews=None):
    reviews = reviews or {}
    unknown = set(reviews) - {r['id'] for r in rows}
    if unknown:
        raise ValueError(f'Reviews do not match this population: {sorted(unknown)}')
    decisions = {}
    for row in rows:
        base = assess({k: row.get(k) for k in FIELDS})
        decision = dict(base, automatic_correct=base['correct'], automatic_rule=base['rule'])
        if row['id'] in reviews:
            review = reviews[row['id']]
            if review['record_sha256'] != record_hash(row):
                raise ValueError(f"Stale review: {row['id']}")
            decision.update(correct=review['correct'], rule='recorded_equivalence_review',
                            source='assistant_review', reason=review['reason'])
        decisions[row['id']] = decision
    return decisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    rows = load_rows(args.data_dir)
    packet = []
    for row in rows:
        d = assess(row)
        packet.append({k: row.get(k) for k in FIELDS} | d)
    out = Path(args.output)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'schema':VERSION,'instructions':'Review answer equivalence using only question, options, reference and response. No faithfulness labels or detector scores are included. Keep ambiguity unresolved.', 'records':packet}, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(dict(Counter('unresolved' if r['correct'] is None else str(r['correct']) for r in packet))))


if __name__ == '__main__':
    main()
