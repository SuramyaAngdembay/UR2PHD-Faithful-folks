"""
Fit-test google/gemma-4-12b-it (multimodal 'gemma4_unified') for our TEXT-ONLY causal pipeline on
an 8GB card in 4-bit. Tries AutoModelForCausalLM, then AutoModelForImageTextToText / AutoModel, runs
one short chat forward, and reports peak VRAM. If it loads + generates + fits, we can add a branch to
synth_generate/synth_extract; else fall back to Gemma-2-9b as the Gemma-family representative.
Usage: python gemma4_fit_test.py --gpu 0 [--model google/gemma-4-12b-it]
"""
import argparse, torch
ap = argparse.ArgumentParser()
ap.add_argument("--gpu", type=int, default=0)
ap.add_argument("--model", default="google/gemma-4-12b-it")
args = ap.parse_args()
torch.cuda.set_device(args.gpu); DEV = f"cuda:{args.gpu}"
from transformers import AutoTokenizer, BitsAndBytesConfig
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(args.model)

model = None
for name in ("AutoModelForCausalLM", "AutoModelForImageTextToText", "AutoModel"):
    try:
        import transformers as T
        cls = getattr(T, name)
        try:
            model = cls.from_pretrained(args.model, quantization_config=bnb, device_map={"": args.gpu}, dtype=torch.bfloat16)
        except TypeError:
            model = cls.from_pretrained(args.model, quantization_config=bnb, device_map={"": args.gpu}, torch_dtype=torch.bfloat16)
        print(f"LOADED via {name}", flush=True); break
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__} {str(e)[:120]}", flush=True)
if model is None:
    print("GEMMA4_FIT: cannot load -> fall back to Gemma-2-9b"); raise SystemExit
model.eval()

try:
    enc = tok.apply_chat_template([{"role": "user", "content": "What is 17*3? Answer with the number only."}],
                                  add_generation_prompt=True, return_tensors="pt", return_dict=True).to(DEV)
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=40, do_sample=False)
    txt = tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
    # a hidden-states forward like extraction does
    with torch.no_grad():
        hs = model(**enc, output_hidden_states=True).hidden_states
    peak = torch.cuda.max_memory_allocated(args.gpu) / 1e9
    print(f"GEN OK: {txt!r}", flush=True)
    print(f"hidden_states layers={len(hs)} dim={hs[-1].shape[-1]}", flush=True)
    print(f"PEAK VRAM {peak:.2f} GB (card=8GB)", flush=True)
    print("GEMMA4_FIT: OK" if peak < 7.6 else "GEMMA4_FIT: TIGHT/RISKY", flush=True)
except Exception as e:
    print(f"GEMMA4_FIT: forward/generate failed -> {type(e).__name__} {str(e)[:160]}", flush=True)
