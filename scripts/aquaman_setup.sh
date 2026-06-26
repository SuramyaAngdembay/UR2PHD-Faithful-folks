#!/usr/bin/env bash
# UR2PHD faithfulness experiments — Aquaman env bootstrap.
# No secrets, no model downloads. Idempotent: safe to re-run.
# Stack: torch (cu121, works with driver 535 / CUDA 12.2), transformers, bitsandbytes (4-bit).
set -eo pipefail

VENV="$HOME/ur2phd-venv"
log(){ echo "[$(date +%H:%M:%S)] $*"; }

log "venv at $VENV (create if absent)"
[ -d "$VENV" ] || python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

log "upgrading pip/wheel/setuptools"
python -m pip install -q -U pip wheel setuptools

log "installing torch (cu121 wheels)"
pip install -q torch --index-url https://download.pytorch.org/whl/cu121

log "installing ML + analysis stack"
pip install -q "transformers>=4.44" accelerate "bitsandbytes>=0.43" \
    huggingface_hub sentencepiece numpy scipy

log "verifying stack + GPUs"
python - <<'PY'
import torch, transformers
print("  torch", torch.__version__, "| cuda_available", torch.cuda.is_available(),
      "| n_gpu", torch.cuda.device_count())
print("  transformers", transformers.__version__)
try:
    import bitsandbytes as bnb
    print("  bitsandbytes", bnb.__version__)
except Exception as e:
    print("  bitsandbytes import WARNING:", e)
for i in range(torch.cuda.device_count()):
    p = torch.cuda.get_device_properties(i)
    print(f"  cuda:{i} {p.name} cc{p.major}.{p.minor} {round(p.total_memory/1e9,1)}GB")
PY

log "ENV SETUP DONE"
