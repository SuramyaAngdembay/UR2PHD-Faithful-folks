"""
Item (c): causal validation via activation steering (Version A, forward-pass).
Compute the post-hoc direction (diff-of-means of cot_end @ best layer) on a TRAIN split;
on HELD-OUT traces, add +/- alpha*sigma*direction to the residual stream at that layer and
read the model's answer-option distribution. Compare the post-hoc direction to a RANDOM
direction (same norms) -> if steering the post-hoc direction shifts answers MORE than random
(dose-response), the direction is a functionally active axis, not just a readable correlate.
Llama only (best-supported model). ~forward passes, no generation.
"""
import json, glob, os
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from sklearn.model_selection import train_test_split

BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
DOMAINS = ["truthfulqa", "logiqa", "aqua", "HLE_BIO"]
MODEL = "meta-llama/Llama-3.1-8B-Instruct"; MDIR = "llama-3.1-8b-instruct"
GPU = 0; DEV = f"cuda:{GPU}"
BESTL = 19; BLOCK = BESTL - 1          # hidden_states[BESTL] = output of decoder block BESTL-1
ALPHAS = [-6, -4, -2, 0, 2, 4, 6]      # in units of sigma along the direction

def load_traces():
    out = []
    for dom in DOMAINS:
        for f in sorted(glob.glob(os.path.join(BASE, dom, MDIR, "response_*.json"))):
            d = json.load(open(f)); ft = d.get("faithful_type")
            if ft not in (1, 2): continue
            s = d["sample_0"]
            steps = [s[k] for k in sorted([k for k in s if k.startswith("step_")], key=lambda x: int(x.split("_")[1]))]
            opts = d.get("options", [])
            if not steps or not opts: continue
            out.append(dict(q=d.get("question", ""), opts=opts,
                            cot="\n".join(f"Step {i+1}: {st}" for i, st in enumerate(steps)),
                            y=1 if ft == 2 else 0, ans=str(s.get("parsed_final_answer", "?"))))
    return out

torch.cuda.set_device(GPU)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(MODEL)
try:
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=bnb, device_map={"": GPU}, dtype=torch.bfloat16)
except TypeError:
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=bnb, device_map={"": GPU}, torch_dtype=torch.bfloat16)
model.eval()

STEER = {"v": None}
def hook(m, i, o):
    if STEER["v"] is None: return o
    v = torch.tensor(STEER["v"], dtype=(o[0].dtype if isinstance(o, tuple) else o.dtype), device=DEV)
    if isinstance(o, tuple):
        return (o[0] + v,) + tuple(o[1:])
    return o + v
handle = model.model.layers[BLOCK].register_forward_hook(hook)

@torch.no_grad()
def act_last(q, opts, cot):
    user = q + "\n\nOptions:\n" + "\n".join(opts)
    enc = tok.apply_chat_template([{"role": "user", "content": user}, {"role": "assistant", "content": cot}],
                                  return_tensors="pt", return_dict=True).to(DEV)
    STEER["v"] = None
    return model(**enc, output_hidden_states=True).hidden_states[BESTL][0, -1, :].float().cpu().numpy()

def letter_ids(L):
    ids = set()
    for v in (L, " " + L):
        t = tok.encode(v, add_special_tokens=False)
        if t: ids.add(t[0])
    return list(ids)

@torch.no_grad()
def answer(q, opts, cot, valid):
    user = q + "\n\nOptions:\n" + "\n".join(opts) + "\n\nReasoning:\n" + cot
    msgs = [{"role": "user", "content": user}, {"role": "assistant", "content": "The single best answer is option ("}]
    try:
        enc = tok.apply_chat_template(msgs, continue_final_message=True, return_tensors="pt", return_dict=True).to(DEV)
    except Exception:
        enc = tok.apply_chat_template([msgs[0]], add_generation_prompt=True, return_tensors="pt", return_dict=True).to(DEV)
    logits = model(**enc).logits[0, -1, :].float()
    probs = torch.softmax(logits, dim=-1)
    lids = {L: letter_ids(L) for L in valid}
    dist = {L: float(sum(probs[i] for i in ids)) for L, ids in lids.items()}
    s = sum(dist.values()) or 1.0
    return {L: v / s for L, v in dist.items()}

tr_all = load_traces()
tr_all = [t for t in tr_all if sum(1 for o in t["opts"] if o and o[0].isalpha()) >= 2]  # letter-MC only (answer readout needs option letters)
tr, te = train_test_split(tr_all, test_size=0.4, stratify=[t["y"] for t in tr_all], random_state=0)
print(f"llama: {len(tr_all)} letter-MC traces (train {len(tr)}, test {len(te)})", flush=True)

# direction from TRAIN
Atr = np.stack([act_last(t["q"], t["opts"], t["cot"]) for t in tr]); ytr = np.array([t["y"] for t in tr])
dvec = Atr[ytr == 1].mean(0) - Atr[ytr == 0].mean(0)
unit = dvec / (np.linalg.norm(dvec) + 1e-8)
sigma = float((Atr @ unit).std())
rng = np.random.default_rng(0); rnd = rng.normal(size=dvec.shape); rnd = rnd / (np.linalg.norm(rnd) + 1e-8)
print(f"direction ||dmean||={np.linalg.norm(dvec):.2f}, sigma(proj)={sigma:.2f}", flush=True)

def dose_response(direction, name):
    valids = [[o[0].upper() for o in t["opts"] if o and o[0].isalpha()] for t in te]
    base = []
    for t, vd in zip(te, valids):
        STEER["v"] = None
        d0 = answer(t["q"], t["opts"], t["cot"], vd); base.append(max(d0, key=d0.get))
    print(f"\n[{name}] dose-response on {len(te)} held-out traces:")
    for a in ALPHAS:
        vec = (a * sigma) * direction
        flips = 0; porig_drop = []
        for t, vd, b in zip(te, valids, base):
            STEER["v"] = vec
            d = answer(t["q"], t["opts"], t["cot"], vd)
            STEER["v"] = None
            if max(d, key=d.get) != b: flips += 1
            porig_drop.append(d.get(b, 0.0))
        print(f"  alpha={a:+d}sigma: answer-flip {flips/len(te):.2f} | mean P(orig-answer) {np.mean(porig_drop):.3f}", flush=True)

dose_response(unit, "POST-HOC direction")
dose_response(rnd, "RANDOM direction (control)")
handle.remove()
print("\nCAUSAL_C DONE", flush=True)
