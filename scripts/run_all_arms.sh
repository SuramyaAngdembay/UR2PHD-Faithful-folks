#!/bin/bash
# Sequential runner for every remaining local judge arm.
#
# WHY THIS REPLACES THE FOUR QUEUE SCRIPTS: they chained on
#   while pgrep -f "judge_local[.]py" >/dev/null; do sleep 60; done
# which ALSO matches the `bash -c` wrappers that created them, because those wrappers'
# command lines contain that very text as unexpanded heredoc. The condition could therefore
# never go false and the whole pipeline deadlocked after the greedy arms finished, with a
# zero-byte seed log. There is no process-polling here at all: one process, in order.
#
# Idempotent: an arm whose output already has the full row count is skipped, so this script
# can be killed and relaunched without losing or redoing work.
set -u
cd ~/synth || exit 9
export HF_HOME=~/hf_cache
[ -f ~/.hf_token ] && export HF_TOKEN=$(cat ~/.hf_token)   # token removed 2026-09-20; models are cached, none is needed
PY=~/ur2phd-venv/bin/python
N_EXPECTED=1304

run() {   # run <model> <tag> [seed]
  local m="$1" t="$2" s="${3:-}"
  local f="results/judge_raw_${t}.jsonl"
  if [ -f "$f" ] && [ "$(wc -l < "$f")" -ge "$N_EXPECTED" ]; then
    echo "SKIP $t (already complete)"; return 0
  fi
  echo "=== ARM $m -> $t ${s:+seed $s}  $(date -Is) ==="
  if [ -n "$s" ]; then
    $PY scripts/judge_local.py --model "$m" --tag "$t" --seed "$s" 2>&1 | grep -vE "Loading weights|Warning:"
  else
    $PY scripts/judge_local.py --model "$m" --tag "$t" 2>&1 | grep -vE "Loading weights|Warning:"
  fi
}

Q3=Qwen/Qwen3-8B
Q7=Qwen/Qwen2.5-7B-Instruct
Q25_3=Qwen/Qwen2.5-3B-Instruct
L31=meta-llama/Llama-3.1-8B-Instruct
L3=meta-llama/Meta-Llama-3-8B-Instruct
L32=meta-llama/Llama-3.2-3B-Instruct
OLMO=$($PY -c "import json;print(json.loads(open('results/judge_raw_olmo3_7b.jsonl').readline())['model'])" 2>/dev/null)

# PHASE 1 -- the load-bearing greedy arms. Self-judges FIRST: Qwen2.5-7B-Instruct and
# Llama-3.1-8B-Instruct are themselves FaithCoT generator models, so these two arms are the
# ones that re-test the self-preference reading that failed on cached data.
run "$Q7"  qwen25_7b
run "$L31" llama31_8b
run "$L3"  llama3_8b
run "$L32" llama32_3b
run "$Q3"  qwen3_8b_greedy2          # greedy is deterministic locally: repeat = a true null
echo "PHASE1_DONE $(date -Is)"

# PHASE 2 -- seeds for the two self-judges: the within-model noise floor for the primary contrast
for s in 0 1 2; do run "$Q7"  "qwen25_7b_s${s}"  "$s"; done
for s in 0 1 2; do run "$L31" "llama31_8b_s${s}" "$s"; done
echo "PHASE2_DONE $(date -Is)"

# PHASE 3 -- remaining seeds
for s in 0 1 2; do run "$Q3"    "qwen3_8b_s${s}"   "$s"; done
for s in 0 1 2; do run "$L3"    "llama3_8b_s${s}"  "$s"; done
for s in 0 1 2; do run "$L32"   "llama32_3b_s${s}" "$s"; done
run "$Q25_3" qwen25_3b_instruct
 for s in 0 1 2; do run "$Q25_3" "qwen25_3b_instruct_s${s}" "$s"; done
[ -n "$OLMO" ] && for s in 0 1 2; do run "$OLMO" "olmo3_7b_s${s}" "$s"; done
echo "ALL_ARMS_DONE $(date -Is)"
