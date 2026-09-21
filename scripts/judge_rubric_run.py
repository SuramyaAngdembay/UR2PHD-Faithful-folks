"""Run one (judge model x rubric) arm for definition-informed-judge-spec.md.

Backends: `local` (4-bit NF4, greedy, identical loading to judge_local.py so that a rubric-A arm
from that script is an exact reference) and `openai` (temperature 0, JSON mode). Prompts come only
from judge_rubrics.py. Output: ~/synth/results/judge_raw_<tag>.jsonl with rid / score / model /
rubric / raw, resumable by rid.
"""
import argparse, json, os, glob, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_rubrics as RB

ap = argparse.ArgumentParser()
ap.add_argument("--backend", required=True, choices=["local", "openai"])
ap.add_argument("--model", required=True)
ap.add_argument("--rubric", required=True, choices=["A", "D1", "D2", "R"])
ap.add_argument("--tag", required=True)
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--rpm", type=int, default=90)
ap.add_argument("--workers", type=int, default=4)
a = ap.parse_args()

BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
OUT = os.path.expanduser(f"~/synth/results/judge_raw_{a.tag}.jsonl")
MAX_NEW = 96 if a.rubric == "D2" else 64          # D2's schema puts `classification` first

def extract(text):
    text = re.sub(r'<think>.*?</think>', ' ', text, flags=re.S)
    text = re.sub(r'<think>.*$', ' ', text, flags=re.S)
    if a.rubric == "D2":
        m = re.search(r'"classification"\s*:\s*"?([012])\b', text)
        return RB.D2_SCORE[int(m.group(1))] if m else None
    m = re.search(r'"unfaithfulness_score"\s*:\s*(-?\d+)', text) or re.search(r'(-?\d+)', text)
    if not m: return None
    v = int(m.group(1))
    return v if 0 <= v <= 100 else None

recs = []
for f in sorted(glob.glob(BASE + "/*/*/response_*.json")):
    d = json.load(open(f))
    if "unfaithfulness" not in d: continue
    d["_rid"] = "/".join(f.split("/")[-3:]); recs.append(d)
if a.limit: recs = recs[:: max(1, len(recs) // a.limit)][:a.limit]      # spread across domains/models
done = {json.loads(l)["rid"] for l in open(OUT)} if os.path.exists(OUT) else set()
todo = [r for r in recs if r["_rid"] not in done]
print(f"rubric {a.rubric} sha {RB.rubric_hashes()[a.rubric][:12]} | traces {len(recs)} | done {len(done)} | to run {len(todo)}", flush=True)

def save(rid, score, raw):
    with open(OUT, "a") as fh:
        fh.write(json.dumps({"rid": rid, "score": score, "model": a.model, "rubric": a.rubric,
                             "raw": raw[:160]}) + "\n")

t0 = time.time(); bad = 0
if a.backend == "local":
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForCausalLM.from_pretrained(
        a.model, dtype=torch.float16, device_map="auto",
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                                               bnb_4bit_quant_type="nf4"))
    model.eval()
    with torch.no_grad():
        for i, rec in enumerate(todo):
            msgs = RB.build_messages(a.rubric, rec)
            try:
                prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
            except TypeError:
                prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            enc = tok(prompt, return_tensors="pt", truncation=True, max_length=8192).to(model.device)
            out = model.generate(**enc, max_new_tokens=MAX_NEW, do_sample=False, pad_token_id=tok.eos_token_id)
            txt = tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
            s = extract(txt); bad += s is None
            save(rec["_rid"], s, txt)
            if (i + 1) % 25 == 0:
                el = time.time() - t0
                print(f"  {i+1}/{len(todo)}  {el:.0f}s  {el/(i+1):.2f}s/item  unparsed={bad}", flush=True)
else:
    import threading, urllib.request, urllib.error
    from concurrent.futures import ThreadPoolExecutor
    KEY = os.environ.get("OPENAI_API_KEY") or open(os.path.expanduser("~/.openai_key")).read().strip()
    lock = threading.Lock(); last = [0.0]; usage = [0, 0]
    def pace():
        with lock:
            w = last[0] + 60.0 / a.rpm - time.time()
            if w > 0: time.sleep(w)
            last[0] = time.time()
    def call(rec):
        body = json.dumps({"model": a.model, "temperature": 0, "max_tokens": 220 if a.rubric == "D2" else 30,
                           "response_format": {"type": "json_object"},
                           "messages": RB.build_messages(a.rubric, rec)}).encode()
        for att in range(12):
            try:
                pace()
                req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
                        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=120) as r: o = json.load(r)
                u = o.get("usage", {})
                with lock: usage[0] += u.get("prompt_tokens", 0); usage[1] += u.get("completion_tokens", 0)
                return o["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="ignore")[:200]
                if e.code in (400, 401, 403) or "insufficient_quota" in msg or "credit" in msg:
                    print(f"FATAL HTTP {e.code}: {msg}", flush=True); os._exit(3)
                time.sleep(min(float(e.headers.get("retry-after") or 2 ** att), 120))
            except Exception:
                time.sleep(2 ** min(att, 6))
        return ""
    def work(rec):
        global bad
        txt = call(rec); s = extract(txt)
        with lock:
            bad += s is None; save(rec["_rid"], s, txt)
    with ThreadPoolExecutor(a.workers) as ex:
        for i, _ in enumerate(ex.map(work, todo)):
            if (i + 1) % 100 == 0:
                print(f"  {i+1}/{len(todo)}  {time.time()-t0:.0f}s  unparsed={bad}  tok in={usage[0]} out={usage[1]}", flush=True)
    print(f"tokens in={usage[0]} out={usage[1]}", flush=True)
print(f"RUBRIC_ARM_DONE {a.tag} unparsed={bad}/{len(todo)}", flush=True)
