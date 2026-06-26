#!/usr/bin/env bash
# Download the two FINE-CoT models to the HF cache on Aquaman.
# Qwen2.5-7B-Instruct (open) + Llama-3.1-8B-Instruct (gated; token in ~/.cache/huggingface/token).
# We fetch full safetensors and 4-bit-quantize at load time via bitsandbytes.
set -eo pipefail
source "$HOME/ur2phd-venv/bin/activate"
export HF_HUB_DISABLE_PROGRESS_BARS=1
python - <<'PY'
import time
from huggingface_hub import snapshot_download
# safetensors + configs + tokenizer only; skips the Llama original/ consolidated .pth duplicate
PATS = ["*.safetensors", "*.json", "*.txt", "tokenizer*", "*.model"]
for repo in ["Qwen/Qwen2.5-7B-Instruct", "meta-llama/Llama-3.1-8B-Instruct"]:
    t = time.time()
    print(f"[dl] start {repo}", flush=True)
    snapshot_download(repo, allow_patterns=PATS)
    print(f"[dl] DONE {repo} in {int(time.time()-t)}s", flush=True)
print("[dl] ALL MODELS DOWNLOADED", flush=True)
PY
du -sh ~/.cache/huggingface/hub 2>/dev/null || true
echo "[dl] SCRIPT COMPLETE"
