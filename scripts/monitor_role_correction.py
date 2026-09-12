"""Correct the definition-aware baseline message roles without changing its rubric."""
import argparse
import json
from pathlib import Path
import random
import diagnostic_v2 as d

ROOT=Path(__file__).resolve().parents[1]

def payload(item,cfg,reference):
    # Keep baseline instructions in the instruction role. The common wrapper
    # promises JSON evidence, so provide the same JSON evidence as generic B1.
    instructions=reference['template'].split('## Inputs',1)[0].format().strip()
    result=d.build_payload(item,'B1',cfg)
    result['messages'][0]['content']=cfg['common_instruction']+'\n\n'+instructions
    schema={'type':'object','properties':{'faithful':{'type':'boolean'}},'required':['faithful'],'additionalProperties':False}
    result['response_format']={'type':'json_schema','json_schema':{'name':'bonafide_faithful','strict':True,'schema':schema}}
    return result

def prepare(out):
    if out.exists():raise ValueError('Preserve existing correction run')
    cfg=json.loads((ROOT/'configs/diagnostic-v2.1.json').read_text())
    reference=json.loads((ROOT/'configs/bonafide-monitor-reference.json').read_text())
    items={r['rid']:r for r in d.read_jsonl(ROOT/'results/diagnostic_v2/prepared/items.jsonl')}
    requests=[];key=[];sources={}
    for batch in ['autonomous_batch1','autonomous_batch2']:
        path=ROOT/'results'/batch/'prepared/analysis-key.jsonl';sources[batch]=d.file_hash(path)
        for r in d.read_jsonl(path):
            if r['arm']!='D1':continue
            body=payload(items[r['rid']],cfg,reference);request_id=d.digest(body)
            requests.append({'request_id':request_id,'payload':body,'parser':'boolean'})
            key.append(r|{'arm':'D2','source_batch':batch,'request_id':request_id})
    assert len(requests)==36 and len({r['request_id'] for r in requests})==36
    random.Random(20260914).shuffle(requests);out.mkdir(parents=True)
    d.write_jsonl(out/'requests.jsonl',requests);d.write_jsonl(out/'analysis-key.jsonl',key)
    d.write_json(out/'manifest.json',{'created_utc':d.utc(),'version':'definition-aware-role-correction',
      'requests_sha256':d.file_hash(out/'requests.jsonl'),'analysis_key_sha256':d.file_hash(out/'analysis-key.jsonl'),
      'original_selection_keys':sources,'config_sha256':d.digest(cfg),'monitor_reference_sha256':d.digest(reference),
      'slots':36,'unique_api_requests':36,'payload_bytes':sum(len(json.dumps(r['payload'],ensure_ascii=False).encode()) for r in requests),
      'max_http_requests':44,'max_seconds':900,'max_payload_bytes':400000,'max_tokens_per_request':1024,
      'max_total_attempt_payload_bytes':500000,'pacing_bytes_per_minute':40000,'minimum_request_gap_seconds':1,
      'status':'Documented message-role bug correction on the identical selected cases; supersedes D1 baseline interpretation'})
    print((out/'manifest.json').read_text())

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();prepare(args.output)
