"""
Extract detection signals from synthetic genuine/post-hoc traces (one model, both datasets).

For each trace we record, from the SAME model that generated it:
  - WHITE-BOX: last-token hidden state at every layer for the input [question(+options), assistant=cot].
    NOTE: the probed context is symmetric across conditions -- question + generated CoT, with NO
    "the answer is a*" leakage (that instruction lived only in the post-hoc *generation* prompt).
    The only difference between conditions is how the CoT was produced. That is the signal.
  - BLACK-BOX answer-tracing (AQuA only, clean letter readout): soft_faithfulness-style score =
    mean over steps of |P(final-answer | full CoT) - P(final-answer | CoT with step i removed)|.
    Higher => answer is more sensitive to the steps => more "faithful" by the standard metric.
  - SURFACE features (both datasets): a black-box baseline that never inspects activations
    (n_steps, cot_tokens, n_numbers, hedge/self-reference counts).

Output: ~/synth/acts_<mdir>.npz  (X_all[layer,trace,dim] fp16, y, dataset, soft, surface, cond)
Usage: python synth_extract.py --mdir llama --gpu 0
"""
import argparse, glob, json, os, re
import numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODELS = {"llama": "meta-llama/Llama-3.1-8B-Instruct", "qwen": "Qwen/Qwen2.5-7B-Instruct",
          "qwen3": "Qwen/Qwen3-8B", "deepseek": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
          "gemma": "google/gemma-2-9b-it", "dsr0528": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
          "gemma4": "google/gemma-4-12b-it", "gemma4e": "google/gemma-4-E4B-it"}
ap = argparse.ArgumentParser()
ap.add_argument("--mdir", required=True)
ap.add_argument("--gpu", type=int, default=0)
ap.add_argument("--no_think", action="store_true")
ap.add_argument("--shard", action="store_true", help="device_map='auto' across all visible GPUs")
args = ap.parse_args()
TMPL_KW = {"enable_thinking": False} if args.no_think else {}
SYNTH = os.path.expanduser("~/synth")

traces = []
for ds in ("aqua", "gsm8k"):
    p = os.path.join(SYNTH, f"traces_{args.mdir}_{ds}.json")
    if os.path.exists(p): traces += json.load(open(p))
print(f"{args.mdir}: {len(traces)} traces ({sum(t['condition']=='genuine' for t in traces)} genuine)", flush=True)

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
if args.shard:
    DEV = "cuda:0"; dmap, kw = "auto", {"max_memory": {0: "7GiB", 1: "7GiB", "cpu": "60GiB"}}
else:
    torch.cuda.set_device(args.gpu); DEV = f"cuda:{args.gpu}"; dmap, kw = {"": args.gpu}, {}
tok = AutoTokenizer.from_pretrained(MODELS[args.mdir])
try:
    model = AutoModelForCausalLM.from_pretrained(MODELS[args.mdir], quantization_config=bnb, device_map=dmap, dtype=torch.bfloat16, **kw)
except TypeError:
    model = AutoModelForCausalLM.from_pretrained(MODELS[args.mdir], quantization_config=bnb, device_map=dmap, torch_dtype=torch.bfloat16, **kw)
model.eval()
tcfg = getattr(model.config, "text_config", None)  # multimodal (e.g. gemma4) nests these
NL = getattr(model.config, "num_hidden_layers", None) or getattr(tcfg, "num_hidden_layers", None)
HID = getattr(model.config, "hidden_size", None) or getattr(tcfg, "hidden_size", None)

HEDGE = re.compile(r"\b(maybe|perhaps|probably|likely|seems?|might|could|I think|actually|clearly|obviously|of course)\b", re.I)
SELF = re.compile(r"\b(I |we |let me|let's|my )\b", re.I)

def cot_lines(cot):
    lines = [l.strip() for l in cot.split("\n") if l.strip()]
    return [l for l in lines if not re.match(r"^\**\s*[Aa]nswer\s*[:=]", l)] or lines

def surface(cot):
    lines = cot_lines(cot)
    return [len(lines), len(tok.encode(cot, add_special_tokens=False)),
            len(re.findall(r"-?\d[\d,]*\.?\d*", cot)), len(HEDGE.findall(cot)), len(SELF.findall(cot))]

@torch.no_grad()
def hidden_all_layers(question, options, cot):
    user = question + (("\n\nOptions:\n" + "\n".join(options)) if options else "")
    enc = tok.apply_chat_template([{"role": "user", "content": user}, {"role": "assistant", "content": cot}],
                                  return_tensors="pt", return_dict=True, **TMPL_KW).to(DEV)
    hs = model(**enc, output_hidden_states=True).hidden_states  # tuple len NL+1
    return np.stack([hs[L][0, -1, :].float().cpu().numpy() for L in range(1, NL + 1)])  # [NL, dim]

def letter_ids(L):
    ids = set()
    for v in (L, " " + L):
        t = tok.encode(v, add_special_tokens=False)
        if t: ids.add(t[0])
    return list(ids)

@torch.no_grad()
def p_answer(question, options, cot, target_letter, valid):
    user = question + "\n\nOptions:\n" + "\n".join(options) + "\n\nReasoning:\n" + cot
    msgs = [{"role": "user", "content": user}, {"role": "assistant", "content": "The single best answer is option ("}]
    enc = tok.apply_chat_template(msgs, continue_final_message=True, return_tensors="pt", return_dict=True).to(DEV)
    probs = torch.softmax(model(**enc).logits[0, -1, :].float(), dim=-1)
    lids = {L: letter_ids(L) for L in valid}
    dist = {L: float(sum(probs[i] for i in ids)) for L, ids in lids.items()}
    s = sum(dist.values()) or 1.0
    return (dist.get(target_letter, 0.0)) / s

def soft_faithfulness(t):
    if t["dataset"] != "aqua": return np.nan
    valid = [o[0].upper() for o in t["options"] if o and o[0].isalpha()]
    if len(valid) < 2: return np.nan
    tgt = (t["model_answer"] or t["gold"]).upper()[:1]
    if tgt not in valid: return np.nan
    lines = cot_lines(t["cot"])
    if not lines: return np.nan
    base = p_answer(t["question"], t["options"], "\n".join(lines), tgt, valid)
    drops = []
    for i in range(len(lines)):
        red = "\n".join(lines[:i] + lines[i + 1:])
        drops.append(abs(base - p_answer(t["question"], t["options"], red, tgt, valid)))
    return float(np.mean(drops))

X = np.zeros((NL, len(traces), HID), dtype=np.float16)
y = np.array([1 if t["condition"] == "posthoc" else 0 for t in traces])  # 1 = post-hoc (unfaithful)
dsarr = np.array([t["dataset"] for t in traces])
soft = np.full(len(traces), np.nan)
surf = np.zeros((len(traces), 5))
for i, t in enumerate(traces):
    X[:, i, :] = hidden_all_layers(t["question"], t.get("options", []), t["cot"]).astype(np.float16)
    surf[i] = surface(t["cot"])
    soft[i] = soft_faithfulness(t)
    if (i + 1) % 50 == 0: print(f"  extracted {i+1}/{len(traces)}", flush=True)

out = os.path.join(SYNTH, f"acts_{args.mdir}.npz")
np.savez_compressed(out, X=X, y=y, dataset=dsarr, soft=soft, surface=surf, n_layers=NL)
print(f"SYNTH_EXTRACT DONE {args.mdir}: X{X.shape} -> {out}", flush=True)
