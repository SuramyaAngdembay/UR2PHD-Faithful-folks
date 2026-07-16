"""White-box extraction for the TRUE correct-answer regime: ft3 (faithful-correct) vs ft4
(post-hoc-on-correct). Mirrors wb_extract.py but ft in (3,4), y=1 for ft4. Caches ~/wbrep_<m>_ft34.npz.
Usage: --model {llama|qwen} --gpu N"""
import json, glob, os, argparse
import numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True, choices=["llama", "qwen"]); ap.add_argument("--gpu", type=int, default=0)
a = ap.parse_args()
BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
DOMAINS = ["truthfulqa", "logiqa", "aqua", "HLE_BIO"]
MODELS = {"llama": "meta-llama/Llama-3.1-8B-Instruct", "qwen": "Qwen/Qwen2.5-7B-Instruct"}
MDIR = {"llama": "llama-3.1-8b-instruct", "qwen": "Qwen2.5-7B-Instruct"}
mname, mdir = MODELS[a.model], MDIR[a.model]; DEV = f"cuda:{a.gpu}"
def load():
    out = []
    for dom in DOMAINS:
        for f in glob.glob(os.path.join(BASE, dom, mdir, "response_*.json")):
            d = json.load(open(f)); ft = d.get("faithful_type")
            if ft not in (3, 4): continue          # TRUE correct-answer regime
            s = d["sample_0"]
            steps = [s[k] for k in sorted([k for k in s if k.startswith("step_")], key=lambda x: int(x.split("_")[1]))]
            if not steps: continue
            out.append(dict(dom=dom, q=d.get("question", ""), opts=d.get("options", []),
                            cot="\n".join(f"Step {i+1}: {st}" for i, st in enumerate(steps)),
                            y=1 if ft == 4 else 0, correct=1))
    return out
torch.cuda.set_device(a.gpu)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(mname)
try: model = AutoModelForCausalLM.from_pretrained(mname, quantization_config=bnb, device_map={"": a.gpu}, dtype=torch.bfloat16)
except TypeError: model = AutoModelForCausalLM.from_pretrained(mname, quantization_config=bnb, device_map={"": a.gpu}, torch_dtype=torch.bfloat16)
model.eval()
tr = load()
print(f"{a.model} ft34: n={len(tr)} ft4={sum(t['y'] for t in tr)} ft3={sum(1-t['y'] for t in tr)}", flush=True)
END = []
with torch.no_grad():
    for i, t in enumerate(tr):
        user = t["q"] + (("\n\nOptions:\n" + "\n".join(t["opts"])) if t["opts"] else "")
        enc = tok.apply_chat_template([{"role": "user", "content": user}, {"role": "assistant", "content": t["cot"]}],
                                      return_tensors="pt", return_dict=True).to(DEV)
        hs = model(**enc, output_hidden_states=True).hidden_states
        END.append(torch.stack([h[0, -1, :] for h in hs]).to(torch.float16).cpu().numpy())
        if (i+1) % 40 == 0: print(f"  {i+1}/{len(tr)}", flush=True)
np.savez_compressed(os.path.expanduser(f"~/wbrep_{a.model}_ft34.npz"),
                    cot_end=np.stack(END), y=np.array([t["y"] for t in tr]),
                    domain=np.array([t["dom"] for t in tr]))
print(f"WB_FT34 DONE {a.model} -> ~/wbrep_{a.model}_ft34.npz  shape {np.stack(END).shape}", flush=True)
