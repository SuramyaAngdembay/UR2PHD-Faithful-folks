#!/bin/bash
# Per-GPU chain for the hint-testbed extension (run detached on Aquaman, one instance per GPU).
# Waits for the in-flight template-B generation on this GPU, then:
#   extract+analyze hintB -> generate logiqa (sycophancy, tag hintL) -> extract+analyze hintL
# Usage: bash queue_hint_ext.sh <gpu> <mdir> <hfmodel>
set -u
GPU=$1; MDIR=$2; MODEL=$3
source ~/ur2phd-venv/bin/activate

# wait for this GPU's hintB generation to finish (bracket pattern avoids self-match)
while pgrep -f "hint_generate[.]py.*--gpu ${GPU} .*hintB" > /dev/null; do sleep 300; done
echo "QUEUE[${MDIR}]: hintB generation done, extracting"

python ~/synth_extract.py --mdir ${MDIR} --gpu ${GPU} --tag hintB \
  && python ~/synth_analyze.py --mdir ${MDIR} --tag hintB --nperm 1000
echo "QUEUE[${MDIR}]: hintB analyzed"

python ~/hint_generate.py --model ${MODEL} --mdir ${MDIR} --dataset logiqa --n 651 \
  --gpu ${GPU} --outtag hintL
echo "QUEUE[${MDIR}]: logiqa generation done, extracting"

python ~/synth_extract.py --mdir ${MDIR} --gpu ${GPU} --tag hintL \
  && python ~/synth_analyze.py --mdir ${MDIR} --tag hintL --nperm 1000
echo "QUEUE_DONE ${MDIR}"
