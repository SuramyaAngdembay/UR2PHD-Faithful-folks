"""Freeze a fresh, matched development diagnostic; reuse the bounded transport."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import random
import autonomous_batch1 as b
import diagnostic_v2 as d

ROOT=Path(__file__).resolve().parents[1]
def prepare(out):
    if out.exists():raise ValueError('Preserve existing prepared batch')
    prep=ROOT/'results/diagnostic_v2/prepared';d.check_prepared(prep)
    keys=d.read_jsonl(prep/'key.jsonl');items={r['rid']:r for r in d.read_jsonl(prep/'items.jsonl')}
    smoke=set(json.loads((prep/'smoke_ids.json').read_text()))
    previous=d.read_jsonl(ROOT/'results/autonomous_batch1/prepared/analysis-key.jsonl')
    excluded={r['cluster_id'] for r in keys if r['rid'] in smoke}|{r['cluster_id'] for r in previous if r['cohort']=='native'}
    eligible=[r for r in keys if r['partition']=='dev' and r['cluster_id'] not in excluded and r['word_count']<=800]
    edges=[(abs(math.log(f['word_count']/u['word_count'])),f,u)
       for f in eligible if f['y']==0 for u in eligible if u['y']==1
       and f['generator']==u['generator'] and f['task']==u['task'] and f['cluster_id']!=u['cluster_id']
       and max(f['word_count'],u['word_count'])/min(f['word_count'],u['word_count'])<=1.25]
    pairs=[];seen=set()
    for dist,f,u in sorted(edges,key=lambda e:(e[0],e[1]['rid'],e[2]['rid'])):
        if {f['cluster_id'],u['cluster_id']} & seen:continue
        pairs.append((f,u));seen|={f['cluster_id'],u['cluster_id']}
    if len(pairs)!=6:raise ValueError('Expected audited six-pair support; review changes')
    cfg=json.loads((ROOT/'configs/diagnostic-v2.1.json').read_text())
    reference=json.loads((ROOT/'configs/bonafide-monitor-reference.json').read_text())
    slots=[];requests={}
    for i,pair in enumerate(pairs):
        for k in pair:
            item=items[k['rid']]
            for arm in ['A1','B1','A2','B2','D1']:
                payload=b.baseline_payload(item,cfg,reference) if arm=='D1' else d.build_payload(item,arm,cfg)
                request_id=d.digest(payload)
                requests.setdefault(request_id,{'request_id':request_id,'payload':payload,'parser':'boolean' if arm=='D1' else 'component' if arm.endswith('2') else 'score'})
                slots.append({'pair':i,'arm':arm,'request_id':request_id,**k})
    plan=list(requests.values());random.Random(20260913).shuffle(plan)
    out.mkdir(parents=True);d.write_jsonl(out/'requests.jsonl',plan);d.write_jsonl(out/'analysis-key.jsonl',slots)
    manifest={'created_utc':d.utc(),'version':'autonomous-2-matched','requests_sha256':d.file_hash(out/'requests.jsonl'),
      'analysis_key_sha256':d.file_hash(out/'analysis-key.jsonl'),'config_sha256':d.digest(cfg),
      'monitor_reference_sha256':d.digest(reference),'prepared_manifest_sha256':d.file_hash(prep/'manifest.json'),
      'prior_selection_key_sha256':d.file_hash(ROOT/'results/autonomous_batch1/prepared/analysis-key.jsonl'),
      'slots':len(slots),'unique_api_requests':len(plan),'payload_bytes':sum(len(json.dumps(r['payload'],ensure_ascii=False).encode()) for r in plan),
      'native_distinct_questions':len(seen),'pairs':len(pairs),'candidate_edges':len(edges),
      'matching':'greedy ascending absolute log word ratio <=1.25; exact task and generator; no repeated or previously scored question',
      'pair_strata':[{'pair':i,'generator':f['generator'],'task':f['task'],'faithful_words':f['word_count'],'unfaithful_words':u['word_count']} for i,(f,u) in enumerate(pairs)],
      'max_http_requests':72,'max_seconds':1500,'max_payload_bytes':500000,'max_tokens_per_request':1024,
      'max_total_attempt_payload_bytes':650000,'pacing_bytes_per_minute':40000,'minimum_request_gap_seconds':1,
      'status':'exploratory six matched development pairs; no generalization estimate'}
    assert len(plan)==60 and manifest['payload_bytes']<=manifest['max_payload_bytes']
    d.write_json(out/'manifest.json',manifest);print(json.dumps(manifest,indent=2))

def analyze(bundle,out):
    meta=json.loads((bundle/'manifest.json').read_text())
    if d.file_hash(bundle/'analysis-key.jsonl')!=meta['analysis_key_sha256']:raise ValueError('Changed key')
    key=d.read_jsonl(bundle/'analysis-key.jsonl');raw=d.read_jsonl(out/'responses.jsonl');byid={r['request_id']:r for r in raw}
    if len(raw)!=len(byid):raise ValueError('Duplicate results')
    rows=[r|{'parsed':byid[r['request_id']]['parsed']} for r in key if r['request_id'] in byid]
    d.write_jsonl(out/'joined-analysis.jsonl',rows)
    tables={};wins={};complete=set()
    for pair in range(meta['pairs']):
        rs=[r for r in rows if r['pair']==pair]
        if len(rs)==10:complete.add(pair)
    for arm in ['A1','B1','A2','B2','D1']:
        table=[];armwins=[]
        for pair in sorted(complete):
            rs=[r for r in rows if r['arm']==arm and r['pair']==pair]
            f=next(r for r in rs if r['y']==0);u=next(r for r in rs if r['y']==1)
            sf=f['parsed']['unfaithfulness_score'];su=u['parsed']['unfaithfulness_score']
            win=float(su>sf)+.5*(su==sf);armwins.append(win)
            table.append({'pair':pair,'faithful_score':sf,'unfaithful_score':su,'win':win,
              'faithful_process_component':f['parsed'].get('components',{}).get('false_process_claim'),
              'unfaithful_process_component':u['parsed'].get('components',{}).get('false_process_claim')})
        wins[arm]=armwins;tables[arm]={'within_pair_win_rate':sum(armwins)/len(armwins) if armwins else None,'pairs':table}
    rng=random.Random(20260913);diffs=[]
    for _ in range(2000):
        ix=[rng.randrange(len(complete)) for _ in complete]
        if ix:diffs.append(sum(wins['B1'][i]-wins['A1'][i] for i in ix)/len(ix))
    summary={'complete_slots':len(rows),'expected_slots':len(key),'complete_pairs':len(complete),'arms':tables,
      'primary_B1_minus_A1_win_rate':sum(wins['B1'][i]-wins['A1'][i] for i in range(len(complete)))/len(complete) if complete else None,
      'primary_pair_bootstrap_95pct':[b.quantile(diffs,.025),b.quantile(diffs,.975)] if diffs else None,
      'word_count_within_pair_win_rate':sum((s['unfaithful_words']>s['faithful_words'])+.5*(s['unfaithful_words']==s['faithful_words']) for s in meta['pair_strata'])/meta['pairs'],
      'limitations':'Six selected same-generator/task, similar-length pairs. Authored controls and native whole labels have different targets. Wide uncertainty; not an independent benchmark.'}
    d.write_json(out/'analysis-summary.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('analyze');p.add_argument('--bundle',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    prepare(args.output) if args.command=='prepare' else analyze(args.bundle,args.output)

