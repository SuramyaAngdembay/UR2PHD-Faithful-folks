#!/bin/bash
# Status for the local open-weight judge arms.
# Tag extraction iterates /proc and requires argv[0] to be the venv python, reading args from the
# NUL-separated cmdline. argv[0] -- NOT /proc/pid/exe, which resolves through the venv symlink to
# /usr/bin/python3.10 -- is what distinguishes the judge from the queue-script bash wrappers,
# whose command lines embed unexpanded heredoc text and defeated two earlier pgrep -f patterns.
cd ~/synth || exit 9

BASES='qwen3_8b qwen25_3b qwen25_7b olmo3_7b llama31_8b llama3_8b llama32_3b'

n=0; donelist=""
for base in $BASES; do
  for suf in "" _greedy2 _s0 _s1 _s2; do
    f="results/judge_raw_${base}${suf}.jsonl"
    [ -f "$f" ] || continue
    c=$(wc -l < "$f"); c=${c:-0}
    if [ "$c" -ge 1300 ]; then n=$((n+1)); donelist="${donelist}${base}${suf} "; fi
  done
done

cur=none
for p in $(pgrep -f 'judge_local[.]py' 2>/dev/null); do
  a0=$(tr '\0' '\n' < "/proc/$p/cmdline" 2>/dev/null | head -1)
  case "$a0" in *ur2phd-venv/bin/python*) ;; *) continue ;; esac
  t=$(tr '\0' '\n' < "/proc/$p/cmdline" 2>/dev/null | awk '$0=="--tag"{getline; print; exit}')
  [ -n "$t" ] && { cur="$t"; break; }
done

rows=0; age=-1
if [ "$cur" != none ] && [ -f "results/judge_raw_${cur}.jsonl" ]; then
  rows=$(wc -l < "results/judge_raw_${cur}.jsonl"); rows=${rows:-0}
  age=$(( $(date +%s) - $(stat -c %Y "results/judge_raw_${cur}.jsonl") ))
fi

q=0; qlist=""
for s in run_all_arms run_local_arms queue_seeds queue_llama queue_llama3 queue_llama32; do
  if pgrep -f "${s}[.]sh" >/dev/null 2>&1; then q=$((q+1)); qlist="${qlist}${s} "; fi
done

e=$(cat results/*arms*.log results/*queue*.log 2>/dev/null | grep -cE 'CUDA out of memory|Traceback'); e=${e:-0}

printf 'STATUS %s %s %s %s %s %s\n' "$n" "$cur" "$rows" "$q" "$e" "$age"
[ -n "$1" ] && { echo "done: ${donelist:-none}"; echo "queues: ${qlist:-none}"; }
