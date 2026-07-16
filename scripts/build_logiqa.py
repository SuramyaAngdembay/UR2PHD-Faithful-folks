"""
Build ~/synth/logiqa_problems.json for the hint testbed's non-math domain extension.
LogiQA (en) test split -- logical-reasoning MC, domain-matched to FaithCoT's LogiQA traces.
Schema matches aquarat_problems.json: id, question, options ["A) ...",...], gold "A".
Run on Aquaman (CPU): python build_logiqa.py
"""
import json, os, re, urllib.request

URL = "https://raw.githubusercontent.com/lgw863/LogiQA-dataset/master/Test.txt"
raw = urllib.request.urlopen(URL, timeout=60).read().decode("utf-8")

# Format: blocks of 7 non-empty lines separated by blank lines:
# answer letter (a-d) / context / query / 4 option lines ("A.text" or "a. text")
blocks, cur = [], []
for line in raw.splitlines():
    if line.strip():
        cur.append(line.strip())
    elif cur:
        blocks.append(cur); cur = []
if cur:
    blocks.append(cur)

LET = "ABCD"
probs, skipped = [], 0
for i, b in enumerate(blocks):
    if len(b) != 7 or b[0].strip().lower() not in "abcd":
        skipped += 1; continue
    gold = b[0].strip().upper()
    ctx, q = b[1], b[2]
    opts = [re.sub(r"^[A-Da-d][.)]\s*", "", o).strip() for o in b[3:7]]
    probs.append(dict(
        id=f"logiqa_{i}",
        question=(ctx + "\n" + q).strip(),
        options=[f"{LET[j]}) {o}" for j, o in enumerate(opts)],
        gold=gold,
    ))
print(f"parsed {len(probs)} problems, skipped {skipped} malformed blocks")

out = os.path.expanduser("~/synth/logiqa_problems.json")
json.dump(probs, open(out, "w"))
print(f"BUILD_LOGIQA DONE: {len(probs)} problems -> {out}")
print("sample:", json.dumps(probs[0])[:400])
