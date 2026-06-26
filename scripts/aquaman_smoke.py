"""Smoke test: load each model in 4-bit (nf4) on its own 3070 and generate.
Confirms 4-bit 8B fits in 8 GB and produces sane output. Run inside ur2phd-venv."""
import time, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

bnb = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
)
PROMPT = "In one sentence, what is the capital of France?"

def load(repo, gpu):
    kw = dict(quantization_config=bnb, device_map={"": gpu})
    try:
        return AutoModelForCausalLM.from_pretrained(repo, dtype=torch.bfloat16, **kw)
    except TypeError:  # older transformers arg name
        return AutoModelForCausalLM.from_pretrained(repo, torch_dtype=torch.bfloat16, **kw)

for repo, gpu in [("Qwen/Qwen2.5-7B-Instruct", 0), ("meta-llama/Llama-3.1-8B-Instruct", 1)]:
    dev = f"cuda:{gpu}"
    print(f"\n=== {repo} on {dev} ===", flush=True)
    try:
        torch.cuda.set_device(gpu)  # bnb dequant kernels use the current device context
        torch.cuda.reset_peak_memory_stats(gpu)
        t = time.time(); tok = AutoTokenizer.from_pretrained(repo); model = load(repo, gpu)
        load_s = time.time() - t
        enc = tok.apply_chat_template([{"role": "user", "content": PROMPT}],
                                      add_generation_prompt=True, return_tensors="pt",
                                      return_dict=True).to(dev)
        in_len = enc["input_ids"].shape[1]
        t = time.time(); out = model.generate(**enc, max_new_tokens=50, do_sample=False)
        gen_s = time.time() - t
        txt = tok.decode(out[0][in_len:], skip_special_tokens=True)
        n = out.shape[1] - in_len; mem = torch.cuda.max_memory_allocated(gpu) / 1e9
        print(f"load={load_s:.0f}s gen={gen_s:.1f}s ({n/gen_s:.1f} tok/s) vram_peak={mem:.1f}GB", flush=True)
        print("OUT:", " ".join(txt.split()), flush=True)
        del model; torch.cuda.empty_cache()
    except Exception as e:
        print("FAILED:", type(e).__name__, str(e)[:300], flush=True)

print("\nSMOKE DONE", flush=True)
