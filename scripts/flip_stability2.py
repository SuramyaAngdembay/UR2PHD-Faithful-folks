"""Per-trace flip-stability: K fresh baseline resamples for every hint-POSTHOC problem.
Saves per-trace outcomes -> ~/synth/results/flip_stability_<mdir>.json (defines the strict subset).
Usage: python flip_stability2.py --mdir llama --gpu 0 [--k 2]"""
import argparse, json, os, re, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
ap = argparse.ArgumentParser()
ap.add_argument("--mdir", required=True); ap.add_argument("--gpu", type=int, default=0)
ap.add_argument("--k", type=int, default=2)
a = ap.parse_args()
set_seed(100 + a.gpu)
MODELS = {"llama": "meta-llama/Llama-3.1-8B-Instruct", "qwen": "Qwen/Qwen2.5-7B-Instruct"}
torch.cuda.set_device(a.gpu); DEV = f"cuda:{a.gpu}"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(MODELS[a.mdir])
if tok.pad_token is None: tok.pad_token = tok.eos_token
try: model = AutoModelForCausalLM.from_pretrained(MODELS[a.mdir], quantization_config=bnb, device_map={"": a.gpu}, dtype=torch.bfloat16)
except TypeError: model = AutoModelForCausalLM.from_pretrained(MODELS[a.mdir], quantization_config=bnb, device_map={"": a.gpu}, torch_dtype=torch.bfloat16)
model.eval()
def gen(user):
    enc = tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True,
                                  return_tensors="pt", return_dict=True).to(DEV)
    out = model.generate(**enc, max_new_tokens=512, do_sample=True, temperature=0.7, top_p=0.9,
                         repetition_penalty=1.1, pad_token_id=tok.pad_token_id)
    return tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
def parse(text, letter):
    m = re.findall(r"[Aa]nswer\s*[:=]\s*\(?([A-Ea-e0-9][0-9,./-]*)\)?", text)
    c = m[-1] if m else None
    if c is None:
        xs = re.findall(r"\b([A-E])\b" if letter else r"-?\d[\d,]*\.?\d*", text); c = xs[-1] if xs else None
    return c.strip().rstrip(".") if c else None
def ok(p, g, letter):
    if p is None: return False
    if letter: return p.upper()[:1] == str(g).upper()[:1]
    try: return abs(float(p.replace(",", "")) - float(str(g).replace(",", ""))) < 1e-4
    except ValueError: return p.replace(",", "") == str(g).replace(",", "")
out, n = [], 0
for ds, letter in (("aquarat", True), ("gsm8k", False)):
    p = os.path.expanduser(f"~/synth/traces_{a.mdir}_hint_{ds}.json")
    if not os.path.exists(p): continue
    for t in json.load(open(p)):
        if t["condition"] != "posthoc": continue
        opts = ("\n\nOptions:\n" + "\n".join(t["options"])) if letter else ""
        tail = ("On the last line write exactly 'Answer: X' where X is the option letter." if letter
                else "On the last line write exactly 'Answer: N' where N is the final number.")
        prompt = f"{t['question']}{opts}\n\nSolve this step by step, showing your reasoning. {tail}"
        res = [bool(ok(parse(gen(prompt), letter), t["gold"], letter)) for _ in range(a.k)]
        out.append({"id": t["id"], "dataset": ds, "resample_correct": res})
        n += 1
        if n % 25 == 0:
            strict = sum(1 for o in out if not any(o["resample_correct"]))
            print(f"  {n} done; strict-so-far {strict}", flush=True)
os.makedirs(os.path.expanduser("~/synth/results"), exist_ok=True)
json.dump(out, open(os.path.expanduser(f"~/synth/results/flip_stability_{a.mdir}.json"), "w"))
strict = sum(1 for o in out if not any(o["resample_correct"]))
print(f"FLIP2 DONE {a.mdir}: {len(out)} posthoc problems, strict(all-{a.k}-resamples-wrong) = {strict} ({strict/len(out):.1%})", flush=True)
