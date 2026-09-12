"""Exact observable-record collision audit; no model inference or generalization bound."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
from diagnostic_v2 import digest, file_hash, write_json
ROOT=Path(__file__).resolve().parents[1]

def normalized(s):return re.sub(r'\s+',' ',s).strip().lower()
def census(rows,fields,label='y'):
    groups=defaultdict(list)
    for r in rows:groups[digest([r[f] for f in fields])].append(r)
    conflicts=[rs for rs in groups.values() if len({r[label] for r in rs})>1]
    return {'n':len(rows),'distinct_observations':len(groups),'duplicate_groups':sum(len(v)>1 for v in groups.values()),
      'mixed_label_groups':len(conflicts),'responses_in_mixed_groups':sum(map(len,conflicts)),
      'maximum_in_sample_lookup_accuracy':sum(max(Counter(r[label] for r in rs).values()) for rs in groups.values())/len(rows),
      'mixed_group_ids':[[r['id'] for r in rs] for rs in conflicts]}

def run(source,out,bonafide_source=None):
    join=json.loads((ROOT/'results/judge_join.json').read_text());fc=[];hashes={}
    for name,j in sorted(join.items()):
        p=source/name;r=json.loads(p.read_text());hashes[name]=file_hash(p);s=r['sample_0']
        assert r['faithful_type']==j['ft'] and r['unfaithfulness']==j['unf']
        assert isinstance(s['full_response'],str) and s['full_response']
        fc.append({'id':name,'question':r['question'],'normalized_question':normalized(r['question']),
          'options':r['options'],'cot':s['full_response'],'answer':s.get('parsed_final_answer'),
          'y':j['unf'],'fourway_y':int(j['ft'] in (2,4))})
    frozen=json.loads((ROOT/'results/bonafide_pop.json').read_text())['rows']
    bf=[{'id':r['rid'],'question':r['question'],'normalized_question':normalized(r['question']),
         'options':[],'cot':r['cot'],'answer':r['model_answer'],'y':r['y']} for r in frozen if r['correct']==0]
    results={}
    for name,rows,label in [('faithcot_binary',fc,'y'),('faithcot_fourway',fc,'fourway_y'),('bonafide_incorrect',bf,'y')]:
        results[name]={'question_only':census(rows,['normalized_question'],label),
                      'question_trace_answer':census(rows,['question','options','cot','answer'],label),
                      'trace_only':census(rows,['cot'],label)}
    qf={r['normalized_question'] for r in fc};qb={r['normalized_question'] for r in bf}
    xf={digest([r['question'],r['cot'],r['answer']]) for r in fc};xb={digest([r['question'],r['cot'],r['answer']]) for r in bf}
    results['cross_dataset']={'shared_normalized_question_texts':len(qf&qb),'shared_exact_question_trace_answer_records':len(xf&xb),
      'note':'Exact textual overlap only; does not establish semantic equivalence or compare source-specific information policies.'}
    results['provenance']={'faithcot_join_sha256':file_hash(ROOT/'results/judge_join.json'),
      'faithcot_raw_file_hash_manifest_sha256':digest(hashes),'bonafide_population_sha256':file_hash(ROOT/'results/bonafide_pop.json'),
      'status':'finite observed-record consistency audit; lookup accuracy is an in-sample upper bound, not achievable held-out performance or a causal identification result'}
    out.mkdir(parents=True,exist_ok=True);write_json(out/'faithcot-source-hashes.json',hashes);write_json(out/'collision-audit.json',results)
    for name,rs in results.items():
        if name.startswith(('faithcot','bonafide')):
            print(name,{k:{f:v[f] for f in ['n','distinct_observations','mixed_label_groups','responses_in_mixed_groups','maximum_in_sample_lookup_accuracy']} for k,v in rs.items()})
    print(results['cross_dataset'])
    if bonafide_source:
        csv.field_size_limit(10000000);native=defaultdict(list)
        from diagnostic_v2 import response_id, read_jsonl
        with bonafide_source.open() as handle:
            for r in csv.DictReader(handle):native[response_id(r)].append(r)
        audited=[]
        for r in bf:
            labels=[v for v in native[r['id']] if v['label_type'].endswith('_COT')]
            assert len(labels)==1
            reason=labels[0]['labeling_reason']
            category=('all_certified' if reason.startswith('all sentences') else
              'no_ack_or_faithful_steps' if reason.startswith('no acknowledgements') else
              'unfaithful_step' if reason.startswith('contains ') else
              'missing_required_steps' if reason.startswith('missing ') else 'other')
            audited.append({'rid':r['id'],'native_y':r['y'],'category':category,'reason':reason,
              'n_released_unfaithful_steps':sum(v['label_type']=='UNFAITHFUL_STEP' for v in native[r['id']])})
        report={'frozen_incorrect_reason_counts':dict(Counter(r['category'] for r in audited)),
          'source_sha256':file_hash(bonafide_source),'status':'Post-selection descriptive audit of native automated annotation reasons; not independent process facts','batches':{}}
        report['category_policy']='Mutually exclusive first-listed reason categories; multiple underlying reasons can coexist.'
        report['overlapping_reason_flags']={name:sum(fragment in r['reason'] for r in audited) for name,fragment in
          [('unfaithful_step','unfaithful step(s)'),('no_ack_or_faithful_steps','no acknowledgements of hint and no faithful steps'),('missing_required_steps','ground truth step(s)')]}
        index={r['rid']:r for r in audited}
        for batch in ['autonomous_batch1','autonomous_batch2']:
            keys=read_jsonl(ROOT/'results'/batch/'prepared/analysis-key.jsonl')
            ids={r['rid'] for r in keys if r['arm']=='B1' and r.get('cohort','native')=='native'}
            picked=[index[rid] for rid in sorted(ids)]
            report['batches'][batch]={'counts':dict(Counter(r['category'] for r in picked)),'rows':picked}
            report['batches'][batch]['overlapping_reason_flags']={name:sum(fragment in r['reason'] for r in picked) for name,fragment in
              [('unfaithful_step','unfaithful step(s)'),('no_ack_or_faithful_steps','no acknowledgements of hint and no faithful steps')]}
        write_json(out/'native-label-reason-audit.json',report)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--faithcot-source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--bonafide-source',type=Path)
    args=ap.parse_args();run(args.faithcot_source,args.output,args.bonafide_source)
