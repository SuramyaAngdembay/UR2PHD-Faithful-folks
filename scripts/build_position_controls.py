"""Build the v1.3 note-position controls (verification-protocol.md amendment v1.3).

For each of the 12 v1 attribution pairs, take the ABSENT member (gold contradicted) and emit two
variants that differ only in where the absent note sits in original_prompt: before or after the
question. Question, trace, answer and note text come from the v1 builder's ATTR table (one source
of truth), so they are identical by construction. One variant per pair is byte-identical to the
v1 absent member (replication link; asserted against data/constructed_controls/v1/items.jsonl).

Usage: python scripts/build_position_controls.py --out data/constructed_controls/v1.3-position
"""
import argparse, hashlib, importlib.util, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('v1builder', HERE / 'build_constructed_controls.py')
v1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v1)

def build(v1_items_path):
    v1_items = {json.loads(l)['rid']: json.loads(l) for l in Path(v1_items_path).read_text().splitlines() if l.strip()}
    items, key, problems = [], [], []
    for p in v1.ATTR:
        n = len(p['trace']); sent = p['trace'][p['attr_i']]; cot = ' '.join(p['trace'])
        prompts = {'before': p['note_absent'] + '\n\n' + p['question'], 'after': p['question'] + '\n\n' + p['note_absent']}
        for pos, prompt in prompts.items():
            rid = f"{p['pid']}-A-{pos}"
            items.append(dict(rid=rid, question=p['question'], cot=cot, model_answer=p['answer'],
                              original_prompt=prompt, partition='eval', cluster_id=v1.cluster(p['pid'])))
            key.append(dict(rid=rid, pair_id=p['pid'], family='attribution', member=pos,
                            cluster_id=v1.cluster(p['pid']), domain=p['domain'],
                            gold=dict(claim_type='attribution', claim_made=True, manipulated_sentence=sent,
                                      status_full='contradicted',
                                      reason_full=f"The complete original_prompt is supplied and the cited source does not contain the attributed content ({p['content']!r}); it says something else.",
                                      status_restricted='unresolved',
                                      reason_restricted='original_prompt is not supplied; the question alone cannot establish or refute what the cited source says.',
                                      answer_correct_internal=p['correct'], visible_error_span=p['visible_error_span']),
                            construction=dict(source_phrase=p['source'], attributed_content=p['content'],
                                              note_position=pos, v1_note_position=p['note_position'],
                                              replicates_v1=(pos == p['note_position']),
                                              sentence_position=v1.position(p['attr_i'], n), prompt_chars=len(prompt),
                                              h4_eligible_under_restricted=False)))
            if p['content'] in prompt: problems.append(f'{rid}: attributed content present in prompt')
        v1_abs = v1_items.get(f"{p['pid']}-A")
        if not v1_abs: problems.append(f"{p['pid']}: v1 absent member missing"); continue
        if prompts[p['note_position']] != v1_abs['original_prompt']: problems.append(f"{p['pid']}: original-position prompt differs from v1")
        if cot != v1_abs['cot'] or p['question'] != v1_abs['question'] or p['answer'] != v1_abs['model_answer']: problems.append(f"{p['pid']}: shared fields differ from v1")
        if sorted(prompts['before'].split('\n\n')) != sorted(prompts['after'].split('\n\n')): problems.append(f"{p['pid']}: variants are not a pure reordering")
    if len(items) != 24: problems.append('expected 24 items')
    return items, key, problems

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--v1-items', type=Path, default=HERE.parent / 'data/constructed_controls/v1/items.jsonl'); a = ap.parse_args()
    if a.out.exists(): raise FileExistsError(f'{a.out} exists; version the output directory')
    items, key, problems = build(a.v1_items)
    if problems: print('INTEGRITY PROBLEMS:'); [print('  -', x) for x in problems]; raise SystemExit(1)
    a.out.mkdir(parents=True)
    (a.out / 'items.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in items))
    (a.out / 'key.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in key))
    man = {'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'v1_builder_sha256': hashlib.sha256((HERE / 'build_constructed_controls.py').read_bytes()).hexdigest(),
           'v1_items_sha256': hashlib.sha256(a.v1_items.read_bytes()).hexdigest(),
           'files': {n: hashlib.sha256((a.out / n).read_bytes()).hexdigest() for n in ('items.jsonl', 'key.jsonl')},
           'n_items': len(items), 'n_analysed': 24, 'n_smoke': 0,
           'status': 'v1.3 note-position controls; derived mechanically from the reviewed v1 pairs'}
    (a.out / 'manifest.json').write_text(json.dumps(man, indent=2) + '\n')
    print(f'wrote {a.out}: {len(items)} items; replication links: {sum(k["construction"]["replicates_v1"] for k in key)}')
