"""Prepare and run the amended, manifest-bound BonaFide judge diagnostic.

Preparation and inspection are offline. Run makes only explicitly bounded API
requests and never reads native labels. Evaluation requires a matching lock.
"""
import argparse
from collections import Counter, defaultdict
import csv
import datetime
import hashlib
import json
import math
from pathlib import Path
import random
import re
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def write_json(path, value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))

def response_id(row):
    key=(row['question_id'],row['target_model'],hashlib.sha1(row['cot'].encode()).hexdigest())
    return hashlib.sha1('|'.join(key).encode()).hexdigest()[:16]

def validate_population(population, prompts, split, released):
    rows=population['rows'];by_rid={r['rid']:r for r in rows}
    if len(by_rid)!=len(rows):raise ValueError('Duplicate response ID')
    source=defaultdict(list)
    for r in released:source[response_id(r)].append(r)
    for rid,r in by_rid.items():
        records=source.get(rid,[])
        labels={x['label_type'] for x in records if x['label_type'].endswith('_COT')}
        if labels not in ({'FAITHFUL_COT'},{'UNFAITHFUL_COT'}):raise ValueError(f'Invalid explicit whole labels: {rid}')
        if r['y']!=int('UNFAITHFUL_COT' in labels):raise ValueError(f'Wrong attached label: {rid}')
        for x in records:
            if any(r[k]!=x[s] for k,s in [('question','question'),('cot','cot'),('model','target_model'),('model_answer','model_answer')]):
                raise ValueError(f'Response text mismatch: {rid}')
            if prompts.get(rid)!=x['prompt']:raise ValueError(f'Original prompt mismatch: {rid}')
            normalize=lambda s: re.sub(r'\s+',' ',s).strip().lower().rstrip('.')
            if r['correct']!=int(normalize(x['model_answer'])==normalize(x['correct_answer'])):
                raise ValueError(f'Answer-correctness mismatch: {rid}')
        if r['cluster']!=re.sub(r'\s+',' ',r['question']).strip().lower():
            raise ValueError(f'Question-group mismatch: {rid}')
    inc=[r for r in rows if r['correct']==0]
    dev=set(split['dev_clusters']); clusters={r['cluster'] for r in inc}
    if not dev<=clusters:raise ValueError('Unknown development cluster')
    ndev=sum(r['cluster'] in dev for r in inc)
    if (len(inc),len(clusters),ndev,len(inc)-ndev)!=(1113,567,306,807):
        raise ValueError('Frozen population or split changed')
    return source

def pick_smoke(rows):
    selected=[]; used=set()
    for label in (0,1):
        pool=sorted([r for r in rows if r['y']==label],key=lambda r:(len(r['cot']),r['rid']))
        for fraction in (0,.33,.67,1):
            pivot=round(fraction*(len(pool)-1))
            candidates=sorted(range(len(pool)),key=lambda i:abs(i-pivot))
            chosen=next(pool[i] for i in candidates if pool[i]['cluster'] not in used)
            selected.append(chosen['rid']);used.add(chosen['cluster'])
    return selected

def prepare(args):
    res=args.results; out=args.output
    if out.exists():raise ValueError('Output already exists; preserve the prepared version')
    pop=json.loads((res/'bonafide_pop.json').read_text())
    prompts=json.loads((res/'bonafide_prompts.json').read_text())
    split=json.loads((res/'dev_clusters.json').read_text())
    csv.field_size_limit(10_000_000)
    with args.upstream_csv.open() as f:released=list(csv.DictReader(f))
    if file_hash(args.upstream_csv)!='5833b500c378bbdcc7103340987749efda10b5944897168e10aed2be4538e13e':
        raise ValueError('Expected the audited pinned curated source; record an amendment for another revision')
    source=validate_population(pop,prompts,split,released)
    dev=set(split['dev_clusters']); items=[];key=[];devrows=[]
    for r in pop['rows']:
        if r['correct']!=0:continue
        part='dev' if r['cluster'] in dev else 'eval'
        if part=='dev':devrows.append(r)
        items.append({k:r[k] for k in ['rid','question','cot','model_answer']} |
                     {'original_prompt':prompts[r['rid']], 'partition':part,
                      'cluster_id':hashlib.sha256(r['cluster'].encode()).hexdigest()})
        raw=source[r['rid']][0]
        key.append({'rid':r['rid'],'y':r['y'],'generator':r['model'],
                    'task':raw['hint_dataset'] or raw['src_type'],'word_count':len(r['cot'].split()),
                    'n_steps':r['n_steps'],'cluster_id':items[-1]['cluster_id'],'partition':part})
    smoke=pick_smoke(devrows)
    out.mkdir(parents=True)
    write_jsonl(out/'items.jsonl',items);write_jsonl(out/'key.jsonl',key)
    write_json(out/'smoke_ids.json',smoke)
    manifest={'prepared_at_utc':utc(),'protocol_version':'2.0',
              'source_revision':'685b904042d014950e29903c29ae4bd9086fa327',
              'input_sha256':{p.name:file_hash(p) for p in [res/'bonafide_pop.json',res/'bonafide_prompts.json',res/'dev_clusters.json',args.upstream_csv]},
              'prepared_sha256':{n:file_hash(out/n) for n in ['items.jsonl','key.jsonl','smoke_ids.json']},
              'counts':dict(Counter((r['partition']+'_unfaithful'+str(r['y'])) for r in key)),
              'responses':len(items),'question_clusters':len({r['cluster_id'] for r in items}),
              'verified_frozen_labels_and_original_prompts':len(pop['rows']),
              'smoke_responses':len(smoke),'status':'exploratory; smoke selection for instrument coverage only'}
    write_json(out/'manifest.json',manifest)
    print(json.dumps(manifest,indent=2))

def build_payload(item, arm, config):
    if arm not in config['arms']:raise ValueError('Unknown arm')
    record={'question':item['question'],'chain_of_thought':item['cot'],'final_answer':item['model_answer']}
    if arm.startswith('B'):record['original_prompt']=item['original_prompt']
    rubric=config['generic_rubric'] if arm.endswith('1') else config['component_rubric']
    return {'model':config['model'],'temperature':config['temperature'],
            'max_tokens':config['max_tokens'],
            'response_format':config.get('response_formats',{}).get(arm[-1],config['response_format']),
            'messages':[{'role':'system','content':config['common_instruction']+'\n\n'+rubric},
                        {'role':'user','content':json.dumps(record,ensure_ascii=False)}]}

COMPONENT_VALUES={
    'acknowledgment':{'yes','no','unclear','not_applicable'},
    'reliance':{'supported','not_established'},
    'false_process_claim':{'supported_violation','no_verified_violation','insufficient_evidence'},
    'required_omission':{'supported_violation','no_verified_violation','insufficient_evidence'},
    'logical_support':{'supported','partial','unsupported','insufficient_evidence'},
}

CLAIM_TYPES={'attribution','execution','other'}
SUPPORT_STATUSES={'supported','contradicted','unresolved'}

def parse_claims_output(raw, item, arm, evidence_policy='reject'):
    """Shared-schema claims family (controlled verification experiment). BOTH procedures use it,
    so output structure is constant across the procedure contrast. Evidence boundaries reuse the
    same allowed_context rule as the component family; never re-derive them elsewhere."""
    choice=raw['choices'][0]
    if choice.get('finish_reason')!='stop':raise ValueError('Non-stop finish reason')
    result=json.loads(choice['message']['content'])
    score=result.get('unfaithfulness_score')
    if type(score) is not int or not 0<=score<=100:raise ValueError('Score must be an integer in [0,100]')
    claims=result.get('claims')
    if not isinstance(claims,list):raise ValueError('Missing claims list')
    if not isinstance(result.get('rationale'),str):raise ValueError('Missing rationale')
    allowed_context=item['question']+('\n'+item['original_prompt'] if arm.startswith('B') else '')
    issues=[]
    for index,c in enumerate(claims):
        if not isinstance(c,dict):raise ValueError('Claim must be an object')
        if c.get('claim_type') not in CLAIM_TYPES:raise ValueError('Invalid claim_type')
        if c.get('support_status') not in SUPPORT_STATUSES:raise ValueError('Invalid support_status')
        if not isinstance(c.get('claim'),str):raise ValueError('Claim text must be a string')
        for name,allowed in [('trace_quote',item['cot']),('evidence_quote',allowed_context)]:
            quote=c.get(name)
            if not isinstance(quote,str) or len(quote)>240:raise ValueError('Unsupported or oversized evidence quote: '+name)
            if quote and quote not in allowed:
                if evidence_policy=='reject':raise ValueError('Unsupported or oversized evidence quote: '+name)
                issues.append({'index':index,'field':name,'issue':'not_an_exact_span_in_allowed_evidence'})
        if not c.get('trace_quote'):
            if evidence_policy=='reject':raise ValueError('Claim without a trace quote')
            issues.append({'index':index,'field':'trace_quote','issue':'empty'})
    result['_quote_validation']={'all_quotes_match':not issues,'issues':issues,
        'note':'Lexical span check only, not independent verification of the claim'}
    return result

def parse_output(raw, item, arm, evidence_policy='reject', schema_family='component'):
    if schema_family=='claims':return parse_claims_output(raw,item,arm,evidence_policy)
    if schema_family!='component':raise ValueError('Unknown schema family')
    choice=raw['choices'][0]
    if choice.get('finish_reason')!='stop':raise ValueError('Non-stop finish reason')
    result=json.loads(choice['message']['content'])
    score=result.get('unfaithfulness_score')
    if type(score) is not int or not 0<=score<=100:raise ValueError('Score must be an integer in [0,100]')
    if arm.endswith('2'):
        if result.get('evidence_status') not in {'sufficient','insufficient'}:raise ValueError('Missing evidence status')
        components=result.get('components',{})
        for k,values in COMPONENT_VALUES.items():
            if components.get(k) not in values:raise ValueError('Invalid component '+k)
        evidence=result.get('evidence')
        if not isinstance(evidence,list) or len(evidence)>2:raise ValueError('Invalid evidence list')
        allowed_context=item['question']+('\n'+item['original_prompt'] if arm.startswith('B') else '')
        quote_issues=[]
        for index,pair in enumerate(evidence):
            for name,allowed in [('trace_quote',item['cot']),('context_quote',allowed_context)]:
                quote=pair.get(name)
                if not isinstance(quote,str) or len(quote)>240:
                    raise ValueError('Unsupported or oversized evidence quote: '+name)
                if quote not in allowed:
                    if evidence_policy=='reject':raise ValueError('Unsupported or oversized evidence quote: '+name)
                    quote_issues.append({'index':index,'field':name,'issue':'not_an_exact_span_in_allowed_evidence'})
        if evidence_policy=='flag':
            result['_quote_validation']={'all_quotes_match':not quote_issues,'issues':quote_issues,
                'note':'Lexical span check only, not independent verification of the claim'}
        rationale=result.get('rationale')
        if not isinstance(rationale,str) or len(rationale.split())>100:raise ValueError('Invalid rationale')
    return result

def run_identity(config, prepared):
    return {'config_sha256':digest(config),'prepared_manifest_sha256':file_hash(prepared/'manifest.json'),
            'items_sha256':file_hash(prepared/'items.jsonl'),'runner_sha256':file_hash(__file__)}

def check_prepared(prepared):
    manifest=json.loads((prepared/'manifest.json').read_text())
    # Run does not need or open the native-label key.
    for name in ['items.jsonl','smoke_ids.json']:
        if file_hash(prepared/name)!=manifest['prepared_sha256'][name]:raise ValueError('Prepared data changed: '+name)

def request_plan(prepared,config,partition,repeats=1,max_items=None):
    """Build the request plan.

    `repeats` issues the SAME request `repeats` times so within-request
    instability can be measured (identical payload, temperature 0). Repeat 0
    keeps the historical request_id digest so existing runs still resume; later
    repeats add the index to the digest. Repeats are replicate measurements of
    one response, never additional independent examples.
    """
    if repeats<1:raise ValueError('repeats must be >=1')
    check_prepared(prepared)
    items=read_jsonl(prepared/'items.jsonl')
    smoke=set(json.loads((prepared/'smoke_ids.json').read_text()))
    items=[r for r in items if (r['rid'] in smoke if partition=='smoke' else r['partition']==partition)]
    rng=random.Random(config['seed']); rng.shuffle(items)
    if max_items is not None:
        if max_items<1:raise ValueError('max_items must be >=1')
        items=items[:max_items]          # deterministic subset of the seeded shuffle
    plan=[]
    for item in items:
        arms=list(config['arms']);rng.shuffle(arms)
        for arm in arms:
            payload=build_payload(item,arm,config)
            base={'rid':item['rid'],'arm':arm,'payload':payload}
            for rep in range(repeats):
                key=base if rep==0 else dict(base,repeat=rep)
                plan.append({'rid':item['rid'],'arm':arm,'repeat':rep,'request_id':digest(key),
                             'payload':payload,'item':item})
    return plan

def run(args):
    config=json.loads(args.config.read_text()); identity=run_identity(config,args.prepared)
    if args.partition=='eval':
        lock=args.prepared/'lock.json'
        if not lock.exists() or json.loads(lock.read_text()).get('identity')!=identity:
            raise ValueError('Evaluation requires a reviewed lock.json matching this exact config, inputs and runner')
    plan=request_plan(args.prepared,config,args.partition,getattr(args,'repeats',1),getattr(args,'max_items',None))
    if not plan:raise ValueError('Empty request plan')
    input_chars=sum(sum(len(m['content']) for m in p['payload']['messages']) for p in plan)
    if input_chars>config['max_total_input_characters']:raise ValueError('Input-character budget exceeded; document a bounded campaign config')
    descriptor={'identity':identity,'partition':args.partition,'request_ids':[p['request_id'] for p in plan],
                'endpoint':args.endpoint,'max_http_requests':args.max_http_requests,'max_seconds':args.max_seconds,
                'repeats':getattr(args,'repeats',1),'max_items':getattr(args,'max_items',None)}
    if args.dry_run:
        print(json.dumps({'requests':len(plan),'input_characters':input_chars,'maximum_output_tokens':len(plan)*config['max_tokens'],
                          'identity':identity,'partition':args.partition},indent=2));return
    if args.max_http_requests<len(plan):raise ValueError('HTTP request cap is smaller than the plan')
    args.output.mkdir(parents=True,exist_ok=True)
    manifest_path=args.output/'run.json'
    if manifest_path.exists():
        old=json.loads(manifest_path.read_text())
        if old['descriptor']!=descriptor:raise ValueError('Resume identity differs; create a new run directory')
    else:
        write_json(manifest_path,{'created_at_utc':utc(),'descriptor':descriptor,'config':config})
    rawpath=args.output/'responses.jsonl'; errors=args.output/'errors.jsonl'
    history=read_jsonl(rawpath) if rawpath.exists() else []
    expected={p['request_id'] for p in plan};done=set()
    for h in history:
        if h['request_id'] not in expected or h['request_id'] in done:raise ValueError('Unknown/duplicate response in resume file')
        done.add(h['request_id'])
    models={r['returned_model'] for r in history}
    if len(models)>1:raise ValueError('Mixed model identities in existing run')
    # Key read only at execution; never written into artifacts or diagnostics.
    key=args.api_key_file.expanduser().read_text().strip()
    if not key:raise ValueError('Empty credential file')
    attempts_path=args.output/'attempts.jsonl'
    prior_attempts=read_jsonl(attempts_path) if attempts_path.exists() else []
    if any(r['request_id'] not in expected for r in prior_attempts):raise ValueError('Unknown request in attempt ledger')
    started=time.monotonic();calls=len(prior_attempts)
    failures=0            # cumulative RETRYABLE failures (transient: 429 / 5xx / timeouts)
    consecutive_failures=0  # reset on any success; guards a genuinely stuck endpoint
    for p in plan:
        if p['request_id'] in done:continue
        succeeded=False
        for attempt in range(config['max_attempts_per_request']):
            if calls>=args.max_http_requests or time.monotonic()-started>=args.max_seconds:
                raise RuntimeError('Bound reached; partial results preserved')
            if args.rpm>0:time.sleep(60/args.rpm)
            begin=time.monotonic();calls+=1
            record={'request_id':p['request_id'],'rid':p['rid'],'arm':p['arm'],'timestamp_utc':utc(),'attempt':attempt+1}
            # Persist attempted calls before transport, so interrupted calls still
            # count toward the whole-run cap when resumed.
            with attempts_path.open('a') as f:
                f.write(json.dumps(record)+'\n');f.flush()
            raw=None;stop=False
            try:
                req=urllib.request.Request(args.endpoint,data=json.dumps(p['payload']).encode(),
                      headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=config['request_timeout_seconds']) as response:raw=json.load(response)
                record.update(raw=raw,returned_model=raw.get('model'),duration_seconds=time.monotonic()-begin)
                parsed=parse_output(raw,p['item'],p['arm'],config.get('evidence_policy','reject'),config.get('schema_family','component'))
                if not raw.get('model'):raise ValueError('Missing returned model identity')
                if models and raw['model'] not in models:stop=True;raise ValueError('Returned model identity changed')
                models.add(raw['model']);record['parsed']=parsed
                with rawpath.open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
                done.add(p['request_id']);succeeded=True;consecutive_failures=0
                print(json.dumps({'completed':len(done),'total':len(plan),'rid':p['rid'],'arm':p['arm'],
                                  'returned_model':raw['model'],'usage':raw.get('usage',{})}),flush=True)
                break
            except urllib.error.HTTPError as error:
                try:body=json.loads(error.read()).get('error',{})
                except Exception:body={}
                # Do not persist request headers or unfiltered remote error messages.
                code=body.get('code');record.update(error_type='HTTPError',http_status=error.code,error_code=code)
                stop=error.code in (400,401,403,404) or code in ('insufficient_quota','billing_hard_limit_reached')
                retry=error.code==429 or 500<=error.code<600
                try:retry_after=float(error.headers.get('retry-after') or 0)
                except Exception:retry_after=0.0
            except Exception as error:
                record.update(error_type=type(error).__name__,error_message=str(error)[:200])
                retry=isinstance(error,(TimeoutError,urllib.error.URLError))
            with errors.open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
            # A substantive failure (auth/quota/bad request/model change) halts immediately.
            # Transient failures are budgeted separately: a cumulative cap catches a degraded
            # endpoint, a consecutive cap catches a stuck one. A rate-limited endpoint can emit
            # many isolated 429s across a long run without that run being unhealthy.
            failures+=1 if retry else 0
            consecutive_failures+=1
            if stop:raise RuntimeError('Pilot stopped after a substantive failure; inspect saved errors')
            if consecutive_failures>=config.get('max_consecutive_failures',12):
                raise RuntimeError('Pilot stopped: endpoint failed repeatedly without success; inspect saved errors')
            if failures>=config.get('max_retryable_failures',200):
                raise RuntimeError('Pilot stopped: transient-failure budget exhausted; inspect saved errors')
            if not retry:break
            # 429 needs the token window to roll over; honour Retry-After when supplied.
            wait=retry_after if (locals().get('retry_after') or 0)>0 else (
                 min(15*(attempt+1),90) if record.get('http_status')==429 else min(2**attempt,8))
            time.sleep(wait)
        if not succeeded:
            print(json.dumps({'failed_request':p['request_id'],'rid':p['rid'],'arm':p['arm']}),flush=True)
    write_json(args.output/'completion.json',{'completed_at_utc':utc(),'expected':len(plan),'valid':len(done),
               'failed_slots':len(plan)-len(done),'http_requests_recorded':calls,'returned_models':sorted(models),
               'responses_sha256':file_hash(rawpath) if rawpath.exists() else None,
               'purpose':'instrument smoke only' if args.partition=='smoke' else 'exploratory diagnostic'})
    if len(done)!=len(plan):raise RuntimeError('Run has missing/invalid slots; no complete success')
    print('DIAGNOSTIC_COMPLETE',flush=True)

def prepare_constructed(args):
    """Prepare the constructed-control population (verification-protocol.md §4). Verifies the
    builder manifest, the item schema, and the pair structure each family promises."""
    src=args.source;out=args.output
    if out.exists():raise ValueError('Output already exists; preserve the prepared version')
    man=json.loads((src/'manifest.json').read_text())
    for n,h in man['files'].items():
        if file_hash(src/n)!=h:raise ValueError('Constructed-control source changed since it was built: '+n)
    items=read_jsonl(src/'items.jsonl');key=read_jsonl(src/'key.jsonl')
    need={'rid','question','cot','model_answer','original_prompt','partition','cluster_id'}
    for it in items:
        if set(it)!=need:raise ValueError('Constructed item has unexpected fields: '+str(it.get('rid')))
    smoke=[it['rid'] for it in items if it['partition']=='smoke']
    analysed=[it for it in items if it['partition']=='eval']
    expected=getattr(args,'expected_analysed',48)
    if len(analysed)!=expected:raise ValueError(f'Expected {expected} analysed constructed items')
    if not smoke and not getattr(args,'no_smoke',False):raise ValueError('Expected smoke items (or pass --no-smoke)')
    if {k['rid'] for k in key}!={it['rid'] for it in analysed}:raise ValueError('Key/items mismatch')
    byc=defaultdict(list)
    for it in analysed:byc[it['cluster_id']].append(it)
    for k in key:
        pair=byc[k['cluster_id']]
        if len(pair)!=2:raise ValueError('Pair must have exactly two members: '+k['pair_id'])
        a,b=pair
        if k['family']=='attribution':
            if any(a[f]!=b[f] for f in ('question','cot','model_answer')) or a['original_prompt']==b['original_prompt']:
                raise ValueError('Attribution pair must be restricted-identical and full-different: '+k['pair_id'])
        elif k['family']=='verification':
            if a['original_prompt']!=b['original_prompt'] or a['question']!=b['question'] or a['model_answer']!=b['model_answer'] or a['cot']==b['cot']:
                raise ValueError('Verification pair must share prompt/question/answer and differ in trace: '+k['pair_id'])
        else:raise ValueError('Unknown family')
    out.mkdir(parents=True)
    write_jsonl(out/'items.jsonl',items);write_jsonl(out/'key.jsonl',key);write_json(out/'smoke_ids.json',smoke)
    manifest={'prepared_at_utc':utc(),'protocol_version':'controlled-verification-1.0',
              'population':'constructed controls; not benchmark data; never pooled with native AUROC',
              'source_manifest_sha256':file_hash(src/'manifest.json'),'source_builder_sha256':man['builder_sha256'],
              'prepared_sha256':{n:file_hash(out/n) for n in ['items.jsonl','key.jsonl','smoke_ids.json']},
              'counts':{'analysed':len(analysed),'smoke':len(smoke),'pairs':len({k['pair_id'] for k in key}),
                        'by_family':dict(Counter(k['family'] for k in key))},
              'status':'prepared; freeze (lock.json) required before an eval-partition run'}
    write_json(out/'manifest.json',manifest);print(json.dumps(manifest,indent=2))

def payload_checks(plan, key, config):
    """Amendment v1.1 A4(vi): the request plan must realise the intended evidence conditions."""
    if config['response_formats']['1']!=config['response_formats']['2']:raise ValueError('Procedures must share one output schema')
    if config['generic_rubric']==config['component_rubric']:raise ValueError('Procedures must differ in instructions')
    byreq={(p['rid'],p['arm'],p['repeat']):p['payload'] for p in plan}
    pairs=defaultdict(list)
    for rid,k in key.items():pairs[k['pair_id']].append(rid)
    checked=Counter()
    for pid,rids in pairs.items():
        a,b=sorted(rids);fam=key[a]['family']
        for arm in config['arms']:
            pa,pb=byreq[(a,arm,0)],byreq[(b,arm,0)]
            ra,rb=(json.loads(p['messages'][1]['content']) for p in (pa,pb))
            if pa['messages'][0]!=pb['messages'][0] or pa['response_format']!=pb['response_format']:raise ValueError(pid+': arm system/schema differs within pair')
            if arm.startswith('A'):
                if 'original_prompt' in ra or 'original_prompt' in rb:raise ValueError(pid+': restricted payload carries original_prompt')
            else:
                for rid,rec in ((a,ra),(b,rb)):
                    if 'original_prompt' not in rec:raise ValueError(pid+': full payload lacks original_prompt')
                    if fam=='attribution':
                        c=key[rid]['construction']['attributed_content']
                        if (c in rec['original_prompt'])!=(key[rid]['member']=='present'):raise ValueError(rid+': attributed content presence wrong')
            if fam=='attribution':
                if arm.startswith('A') and pa!=pb:raise ValueError(pid+': restricted payloads must be byte-identical (H4)')
                if arm.startswith('B') and pa==pb:raise ValueError(pid+': full payloads must differ')
                checked['attribution_'+('restricted_identical' if arm.startswith('A') else 'full_different')]+=1
            else:
                diff={f for f in set(ra)|set(rb) if ra.get(f)!=rb.get(f)}
                if diff!={'chain_of_thought'}:raise ValueError(pid+'/'+arm+': verification pair differs in '+str(sorted(diff)))
                checked['verification_trace_only_difference']+=1
    return dict(checked)

def freeze(args):
    """Write lock.json only when the operational freeze checklist is complete and the payload
    checks pass. run --partition eval refuses without a matching lock."""
    config=json.loads(args.config.read_text());prepared=args.prepared;lock=prepared/'lock.json'
    if lock.exists():raise ValueError('lock.json exists; a frozen plan is never re-frozen in place')
    checklist=json.loads(args.checklist.read_text())
    missing=[k for k,v in checklist.items() if not k.startswith('_') and v is not True]   # '_'-prefixed keys carry notes
    if missing:raise ValueError('Freeze checklist incomplete: '+', '.join(missing))
    key={k['rid']:k for k in read_jsonl(prepared/'key.jsonl')}
    plan=request_plan(prepared,config,'eval',args.repeats)
    checks=payload_checks(plan,key,config)
    write_json(lock,{'frozen_at_utc':utc(),'identity':run_identity(config,prepared),'checklist':checklist,
                     'checklist_sha256':file_hash(args.checklist),'repeats':args.repeats,'requests':len(plan),
                     'request_ids_sha256':digest([p['request_id'] for p in plan]),'payload_checks':checks})
    print(json.dumps(json.loads(lock.read_text()),indent=2))

def inspect_run(args):
    runmeta=json.loads((args.output/'run.json').read_text())
    path=args.output/'responses.jsonl';rows=read_jsonl(path) if path.exists() else []
    ep=args.output/'errors.jsonl';errors=read_jsonl(ep) if ep.exists() else []
    usage=Counter()
    for r in rows+errors:
        for k,v in r.get('raw',{}).get('usage',{}).items():
            if isinstance(v,int):usage[k]+=v
    summary={'partition':runmeta['descriptor']['partition'],'valid_responses':len(rows),'errors':len(errors),
             'by_arm':dict(Counter(r['arm'] for r in rows)),
             'returned_models':sorted({r['returned_model'] for r in rows}), 'token_usage_in_recorded_responses':dict(usage),
             'component_evidence_status':dict(Counter(r['parsed'].get('evidence_status') for r in rows if r['arm'].endswith('2'))),
             'component_exact_quote_checks':dict(Counter(str(r['parsed'].get('_quote_validation',{}).get('all_quotes_match')) for r in rows if r['arm'].endswith('2'))),
             'score_ranges_by_arm':{a:[min(z),max(z)] for a in ['A1','B1','A2','B2'] if (z:=[r['parsed']['unfaithfulness_score'] for r in rows if r['arm']==a])},
             'interpretation':'Format/evidence instrumentation only; no performance estimate for the selected smoke population.'}
    write_json(args.output/'instrument-summary.json',summary);print(json.dumps(summary,indent=2))

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--results',type=Path,default=ROOT/'results')
    p.add_argument('--upstream-csv',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.set_defaults(fn=prepare)
    p=sub.add_parser('run');p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--repeats',type=int,default=1,help='identical repeats per (response,arm) for instability measurement')
    p.add_argument('--max-items',type=int,default=None,dest='max_items',help='cap responses (deterministic subset of the seeded shuffle)')
    p.add_argument('--config',type=Path,default=ROOT/'configs/diagnostic-v2.json')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--partition',choices=['smoke','dev','eval'],default='smoke')
    p.add_argument('--endpoint',default='https://api.openai.com/v1/chat/completions')
    p.add_argument('--api-key-file',type=Path,default=Path('~/.openai_key'))
    p.add_argument('--max-http-requests',type=int,default=36);p.add_argument('--max-seconds',type=int,default=900)
    p.add_argument('--rpm',type=float,default=12);p.add_argument('--dry-run',action='store_true');p.set_defaults(fn=run)
    p=sub.add_parser('prepare-constructed');p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-analysed',type=int,default=48,dest='expected_analysed')
    p.add_argument('--no-smoke',action='store_true',dest='no_smoke');p.set_defaults(fn=prepare_constructed)
    p=sub.add_parser('freeze');p.add_argument('--prepared',type=Path,required=True);p.add_argument('--config',type=Path,required=True)
    p.add_argument('--checklist',type=Path,required=True);p.add_argument('--repeats',type=int,default=3);p.set_defaults(fn=freeze)
    p=sub.add_parser('inspect');p.add_argument('--output',type=Path,required=True);p.set_defaults(fn=inspect_run)
    args=ap.parse_args();args.fn(args)

if __name__=='__main__':main()
