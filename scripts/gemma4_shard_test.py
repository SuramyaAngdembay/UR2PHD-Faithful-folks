"""
Can Gemma-4-12B (4-bit) run SHARDED across the 2x RTX 3070 (8GB each) for our inference/extraction
pipeline? Uses HF Accelerate device_map='auto' (naive pipeline parallelism across both GPUs), then
stresses it like real extraction: a long (~800-token) chat forward with output_hidden_states, plus a
short generate. Reports where layers landed (any 'cpu'/'disk' = slow offload) and peak VRAM per GPU.
Usage: python gemma4_shard_test.py   (leave BOTH GPUs visible)
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

MODEL = "google/gemma-4-12b-it"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(MODEL)
# cap per-GPU below 8GB to force a real 2-way split; allow cpu only as last resort (flagged if used)
max_mem = {0: "7GiB", 1: "7GiB", "cpu": "60GiB"}
try:
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=bnb, device_map="auto",
                                                 max_memory=max_mem, dtype=torch.bfloat16)
except TypeError:
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=bnb, device_map="auto",
                                                 max_memory=max_mem, torch_dtype=torch.bfloat16)
model.eval()

dm = getattr(model, "hf_device_map", {})
devs = sorted({str(v) for v in dm.values()})
offloaded = [k for k, v in dm.items() if str(v) in ("cpu", "disk")]
print(f"device_map spans: {devs}", flush=True)
print(f"modules offloaded to cpu/disk: {len(offloaded)}" + (f" e.g. {offloaded[:3]}" if offloaded else " (none -> pure GPU shard)"), flush=True)

for g in (0, 1): torch.cuda.reset_peak_memory_stats(g)

# short generate sanity
enc = tok.apply_chat_template([{"role": "user", "content": "What is 17*3? Answer with the number only."}],
                              add_generation_prompt=True, return_tensors="pt", return_dict=True)
enc = {k: v.to("cuda:0") for k, v in enc.items()}
with torch.no_grad():
    out = model.generate(**enc, max_new_tokens=40, do_sample=False)
print(f"GEN OK: {tok.decode(out[0, enc['input_ids'].shape[1]:], skip_special_tokens=True)!r}", flush=True)

# extraction stress: ~800-token assistant CoT forward with output_hidden_states (the real memory peak)
long_cot = ("Step {i}: we carefully work through the reasoning in detail with numbers 1234 and 5678. " * 60)
msgs = [{"role": "user", "content": "Solve: " + "blah "*40}, {"role": "assistant", "content": long_cot}]
enc2 = tok.apply_chat_template(msgs, return_tensors="pt", return_dict=True)
enc2 = {k: v.to("cuda:0") for k, v in enc2.items()}
print(f"extraction-style forward seq_len={enc2['input_ids'].shape[1]}", flush=True)
with torch.no_grad():
    hs = model(**enc2, output_hidden_states=True).hidden_states
last = hs[-1][0, -1, :].float().cpu().numpy()
print(f"hidden_states layers={len(hs)} dim={last.shape[0]} (extractable)", flush=True)

peaks = {g: torch.cuda.max_memory_allocated(g)/1e9 for g in (0, 1)}
print(f"PEAK VRAM  GPU0 {peaks[0]:.2f} GB | GPU1 {peaks[1]:.2f} GB  (each card=8GB)", flush=True)
ok = (not offloaded) and max(peaks.values()) < 7.6
print("SHARD_TEST: OK (fits sharded, GPU-only)" if ok else
      ("SHARD_TEST: USES CPU OFFLOAD (works but slow)" if offloaded else "SHARD_TEST: TIGHT/RISKY"), flush=True)
