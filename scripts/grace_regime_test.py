"""GRACE entry point. Stats delegates to the shared repaired analysis.

The optional NLI stage preserves the legacy evidence/truncation protocol, writes
only to a new directory, and requires a pinned model revision. Stats needs no GPU.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
import numpy as np
from grace_answer_check import load_rows
from grace_regime_analysis import add_arguments, run, steptext
from reanalysis_common import manifest, save_json, sha256


def nli(args):
    if not args.model_revision or not re.fullmatch(r'[0-9a-f]{40}', args.model_revision):
        raise ValueError('--model-revision must be the exact 40-character Hugging Face commit for new inference')
    out = Path(args.output_dir)
    if out.exists():
        raise FileExistsError(out)
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    rows = load_rows(args.data_dir)
    model_name = 'FacebookAI/roberta-large-mnli'
    tok = AutoTokenizer.from_pretrained(model_name, revision=args.model_revision)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, revision=args.model_revision).to(f'cuda:{args.gpu}').eval()
    if model.config.id2label.get(2, '').lower() != 'entailment':
        raise ValueError('Unexpected entailment label index')
    protocol = {'stage': 'nli', 'model': model_name, 'revision': args.model_revision,
                'premise_char_limit': 4000, 'pair_token_limit': 512, 'batch_size': 8,
                'unsupported_threshold': .5, 'entailment_index': 2,
                'ctx': 'supplied passages or context', 'prior': 'question + previous steps, no supplied context',
                'correctness_or_native_labels_in_model_inputs': False}
    inputs = {'data/' + p.name: p for p in sorted(Path(args.data_dir).glob('*.jsonl'))}
    man = manifest(inputs, [Path(__file__), Path(__file__).with_name('grace_regime_analysis.py'),
                            Path(__file__).with_name('grace_answer_check.py'), Path(__file__).with_name('reanalysis_common.py')],
                   protocol, args.seed, 0)
    man['status'] = 'running inference; inspect final manifest for completion'
    man['versions']['torch'] = torch.__version__
    out.mkdir(parents=True)
    save_json(out / 'lock.json', man)
    scores = {}
    with torch.no_grad(), (out / 'trace_records.jsonl').open('x') as handle:
        for i, row in enumerate(rows):
            steps = [steptext(s) for s in row['steps']]
            ctx = ' '.join(p.get('text', '') for p in (row.get('passages') or []))[:4000] or row.get('context', '')[:4000]
            premises = {'ctx': [ctx] * len(steps),
                        'prior': [(row['question'] + ' ' + ' '.join(steps[:j]))[:4000] for j in range(len(steps))]}
            res, ents_by_arm = {}, {}
            for tag, prem in premises.items():
                ents = []
                for b in range(0, len(steps), 8):
                    enc = tok(prem[b:b+8], steps[b:b+8], truncation=True, max_length=512,
                              padding=True, return_tensors='pt').to(f'cuda:{args.gpu}')
                    ents.extend(torch.softmax(model(**enc).logits, -1)[:, 2].tolist())
                res['nli_unsup_' + tag] = sum(e < .5 for e in ents)
                res['nli_mean_ent_' + tag] = float(np.mean(ents))
                ents_by_arm[tag] = ents
            scores[row['id']] = res
            request_hash = hashlib.sha256(json.dumps({'steps': steps, 'premises': premises}, sort_keys=True).encode()).hexdigest()
            handle.write(json.dumps({'id': row['id'], 'request_sha256': request_hash, 'step_entailment': ents_by_arm, 'scores': res}) + '\n')
            handle.flush()
            if (i + 1) % 25 == 0:
                print(f'NLI {i+1}/{len(rows)}', flush=True)
    save_json(out / 'grace_nli.json', scores)
    man['status'] = 'complete NLI inference'
    man['artifacts'] = {name: sha256(out / name) for name in ('trace_records.jsonl', 'grace_nli.json')}
    save_json(out / 'manifest.json', man)
    print(f'Complete: {out}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', required=True, choices=['stats', 'nli'])
    parser.add_argument('--gpu', type=int, default=0)
    parser.add_argument('--model-revision')
    add_arguments(parser)
    args = parser.parse_args()
    return run(args) if args.stage == 'stats' else nli(args)


if __name__ == '__main__':
    main()
