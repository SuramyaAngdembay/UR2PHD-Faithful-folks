"""Isolate the metadata visibility comment; retain repeated-original noise controls."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
import diagnostic_v2 as d
from diagnostic_audit_packet import select

ROOT=Path(__file__).resolve().parents[1]
COMMENT='<!-- METADATA FOR DEBUGGING PURPOSES ONLY - SHOULD NOT BE ACCESSABLE BY THE MODEL -->'

def prepare(out):
    if out.exists():raise ValueError('Preserve existing batch')
    prep=ROOT/'results/diagnostic_v2/prepared';d.check_prepared(prep)
    items={r['rid']:r for r in d.read_jsonl(prep/'items.jsonl')};keys=d.read_jsonl(prep/'key.jsonl')
    smoke=set(json.loads((prep/'smoke_ids.json').read_text()));used={r['cluster_id'] for r in keys if r['rid'] in smoke}
    for batch in ['autonomous_batch1','autonomous_batch2']:
        used|={r['cluster_id'] for r in d.read_jsonl(ROOT/'results'/batch/'prepared/analysis-key.jsonl') if r.get('cohort','native')=='native'}
    eligible=[k for k in keys if k['partition']=='dev' and k['cluster_id'] not in used and k['word_count']<=800 and COMMENT in items[k['rid']]['original_prompt']]
    fresh=select(eligible,12,20260915)
    discovery=[r for r in keys if r['rid'] in ['54786893150aa784','6296e4b78b8d98e1']]
    cfg=json.loads((ROOT/'configs/diagnostic-v2.1.json').read_text());requests=[];key=[]
    for group,rows in [('fresh',fresh),('discovery',discovery)]:
        for r in rows:
            original=items[r['rid']]
            assert original['original_prompt'].count(COMMENT)==1
            for variant in ['original_1','original_2','comment_removed']:
                item=original.copy()
                if variant=='comment_removed':item['original_prompt']=original['original_prompt'].replace(COMMENT,'',1)
                payload=d.build_payload(item,'B2',cfg)
                request_id=d.digest({'payload':payload,'replicate':variant})
                requests.append({'request_id':request_id,'payload':payload,'parser':'component'})
                key.append({'group':group,'variant':variant,'request_id':request_id,**r})
    random.Random(20260915).shuffle(requests);out.mkdir(parents=True)
    d.write_jsonl(out/'requests.jsonl',requests);d.write_jsonl(out/'analysis-key.jsonl',key)
    assert len(requests)==42
    d.write_json(out/'manifest.json',{'created_utc':d.utc(),'version':'metadata-comment-ablation',
      'requests_sha256':d.file_hash(out/'requests.jsonl'),'analysis_key_sha256':d.file_hash(out/'analysis-key.jsonl'),
      'config_sha256':d.digest(cfg),'slots':len(requests),'unique_api_requests':len(requests),
      'payload_bytes':sum(len(json.dumps(r['payload'],ensure_ascii=False).encode()) for r in requests),
      'fresh_questions':len({r['cluster_id'] for r in fresh}),'fresh_classes':dict(Counter(r['y'] for r in fresh)),
      'discovery_questions':len(discovery),'removed_comment':COMMENT,
      'max_http_requests':50,'max_seconds':1100,'max_payload_bytes':500000,'max_tokens_per_request':1024,
      'max_total_attempt_payload_bytes':600000,'pacing_bytes_per_minute':40000,'minimum_request_gap_seconds':1,
      'status':'Exploratory presentation intervention; fresh and discovery reported separately; two actual unchanged calls per case'})
    print((out/'manifest.json').read_text())

def analyze(bundle,out):
    import autonomous_batch1 as b
    meta=json.loads((bundle/'manifest.json').read_text())
    assert d.file_hash(bundle/'analysis-key.jsonl')==meta['analysis_key_sha256']
    key=d.read_jsonl(bundle/'analysis-key.jsonl');raw=d.read_jsonl(out/'responses.jsonl');byid={r['request_id']:r for r in raw}
    assert len(raw)==42 and len(byid)==42
    rows=[r|{'parsed':byid[r['request_id']]['parsed']} for r in key]
    d.write_jsonl(out/'joined-analysis.jsonl',rows)
    tables={};rng=random.Random(20260915)
    for group in ['fresh','discovery']:
        cases=[]
        for rid in sorted({r['rid'] for r in rows if r['group']==group}):
            rs={r['variant']:r for r in rows if r['rid']==rid}
            scores={k:r['parsed']['unfaithfulness_score'] for k,r in rs.items()}
            original=(scores['original_1']+scores['original_2'])/2
            cases.append({'rid':rid,'native_y':rs['original_1']['y'],'scores':scores,
              'comment_removed_minus_original_mean':scores['comment_removed']-original,
              'original_repeat_absolute_difference':abs(scores['original_1']-scores['original_2']),
              'false_process_components':{k:r['parsed']['components']['false_process_claim'] for k,r in rs.items()},
              'rationales':{k:r['parsed']['rationale'] for k,r in rs.items()}})
        deltas=[r['comment_removed_minus_original_mean'] for r in cases]
        draws=[sum(rng.choice(deltas) for _ in deltas)/len(deltas) for _ in range(2000)]
        tables[group]={'n':len(cases),'mean_comment_removed_minus_original':sum(deltas)/len(deltas),
           'question_bootstrap_95pct':[b.quantile(draws,.025),b.quantile(draws,.975)],
           'mean_original_repeat_absolute_difference':sum(r['original_repeat_absolute_difference'] for r in cases)/len(cases),
           'cases':cases}
    usage=Counter()
    for r in raw:
        for k,v in r['raw'].get('usage',{}).items():
            if type(v)is int:usage[k]+=v
    summary={'complete':True,'api_calls':len(raw),'usage':dict(usage),'groups':tables,
      'limits':'Selected metadata-hint development cases; one ablated response versus two original repeats. Editing a visibility statement changes presented evidence, not actual historical model access. Not validated process truth or an established fix.'}
    d.write_json(out/'analysis-summary.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('analyze');p.add_argument('--bundle',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();prepare(a.output) if a.command=='prepare' else analyze(a.bundle,a.output)

