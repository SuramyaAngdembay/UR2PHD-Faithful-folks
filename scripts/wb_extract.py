"""
Rich white-box representation extractor (run once per model; caches to disk).
For each ft1/ft2 (correct-answer) trace, extract hidden states at 3 positions x all layers:
  - pre_cot : last token of (question+options) BEFORE the CoT (add_generation_prompt) -> tests
              whether the answer/post-hoc signature is present BEFORE reasoning.
  - cot_end : last token of (question + full CoT) -> the v1 representation.
  - cot_mean: mean-pool over the assistant/CoT token span.
Stored fp16. Labels saved: y (ft2=post-hoc=1), answer letter, domain, correctness.
Usage: --model {llama|qwen} --gpu N
"""
import json, glob, os, argparse
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True, choices=["llama", "qwen", "deepseek"])
ap.add_argument("--gpu", type=int, default=0)
a = ap.parse_args()

BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
DOMAINS = ["truthfulqa", "logiqa", "aqua", "HLE_BIO"]
MODELS = {"llama": "meta-llama/Llama-3.1-8B-Instruct", "qwen": "Qwen/Qwen2.5-7B-Instruct", "deepseek": "deepseek-ai/deepseek-llm-7b-chat"}
MDIR = {"llama": "llama-3.1-8b-instruct", "qwen": "Qwen2.5-7B-Instruct", "deepseek": "deepseek-llm-7b-chat"}
mname, mdir = MODELS[a.model], MDIR[a.model]
DEV = f"cuda:{a.gpu}"
OUT = os.path.expanduser(f"~/wbrep_{a.model}.npz")

def load_traces():
    out = []
    for dom in DOMAINS:
        for f in glob.glob(os.path.join(BASE, dom, mdir, "response_*.json")):
            d = json.load(open(f)); ft = d.get("faithful_type")
            if ft not in (1, 2): continue
            s = d["sample_0"]
            steps = [s[k] for k in sorted([k for k in s if k.startswith("step_")], key=lambda x: int(x.split("_")[1]))]
            if not steps: continue
            out.append(dict(dom=dom, q=d.get("question", ""), opts=d.get("options", []),
                            cot="\n".join(f"Step {i+1}: {st}" for i, st in enumerate(steps)),
                            y=1 if ft == 2 else 0, ans=str(s.get("parsed_final_answer", "?")),
                            correct=1 if s.get("parsed_final_answer") == d.get("label") else 0))
    return out

torch.cuda.set_device(a.gpu)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(mname)
try:
    model = AutoModelForCausalLM.from_pretrained(mname, quantization_config=bnb, device_map={"": a.gpu}, dtype=torch.bfloat16)
except TypeError:
    model = AutoModelForCausalLM.from_pretrained(mname, quantization_config=bnb, device_map={"": a.gpu}, torch_dtype=torch.bfloat16)
model.eval()
tr = load_traces()
print(f"{a.model}: n={len(tr)} ft2={sum(t['y'] for t in tr)} ft1={sum(1-t['y'] for t in tr)}", flush=True)

PRE, END, MEAN = [], [], []
with torch.no_grad():
    for i, t in enumerate(tr):
        user = t["q"] + (("\n\nOptions:\n" + "\n".join(t["opts"])) if t["opts"] else "")
        # pre-CoT: question only, assistant turn opened (no content)
        enc_pre = tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True,
                                          return_tensors="pt", return_dict=True).to(DEV)
        pre_len = enc_pre["input_ids"].shape[1]
        hs_pre = model(**enc_pre, output_hidden_states=True).hidden_states
        PRE.append(torch.stack([h[0, -1, :] for h in hs_pre]).to(torch.float16).cpu().numpy())
        # full: question + CoT
        enc = tok.apply_chat_template([{"role": "user", "content": user}, {"role": "assistant", "content": t["cot"]}],
                                      return_tensors="pt", return_dict=True).to(DEV)
        hs = model(**enc, output_hidden_states=True).hidden_states
        T = enc["input_ids"].shape[1]; start = min(pre_len, T - 1)
        END.append(torch.stack([h[0, -1, :] for h in hs]).to(torch.float16).cpu().numpy())
        MEAN.append(torch.stack([h[0, start:, :].mean(0) for h in hs]).to(torch.float16).cpu().numpy())
        if (i + 1) % 40 == 0: print(f"  {i+1}/{len(tr)}", flush=True)

np.savez_compressed(OUT,
                    pre_cot=np.stack(PRE), cot_end=np.stack(END), cot_mean=np.stack(MEAN),
                    y=np.array([t["y"] for t in tr]), ans=np.array([t["ans"] for t in tr]),
                    domain=np.array([t["dom"] for t in tr]), correct=np.array([t["correct"] for t in tr]))
print(f"saved {OUT}  shapes pre/end/mean = {np.stack(PRE).shape}", flush=True)
print("EXTRACT DONE", flush=True)
