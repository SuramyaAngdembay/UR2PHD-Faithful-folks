"""Build ~/synth/truthfulqa_problems.json in the schema hint_generate.py expects.

Third hint source for the source-dependence test. TruthfulQA is chosen because it is a FaithCoT
domain (so annotated counterparts exist for domain-matched transfer) and because it is a knowledge/
misconception task rather than multi-step reasoning like the existing AQuA and LogiQA sources. A
third reasoning source could not separate a real model-by-source interaction from noise.

Schema per record: {"id", "question", "options": ["A) ...", ...], "gold": "A"}
Uses the mc1 targets, which have exactly one correct answer. Released choice counts range from 3 to
13; they are capped at 5 (correct answer plus 4 seeded-random distractors) so that option count
matches AQuA's 5 and LogiQA's 4. Without the cap, option count would vary systematically between
sources and become a confound in an experiment whose variable is source DOMAIN.
"""
import json, os, random
from datasets import load_dataset

OUT = os.path.expanduser("~/synth/truthfulqa_problems.json")
LET = "ABCDEFGHIJKL"
rng = random.Random(0)

ds = load_dataset("truthfulqa/truthful_qa", "multiple_choice", split="validation")
recs = []
for i, r in enumerate(ds):
    mc1 = r["mc1_targets"]
    choices, labels = list(mc1["choices"]), list(mc1["labels"])
    if sum(labels) != 1 or len(choices) < 3:
        continue
    gold_i = labels.index(1)
    distract = [j for j in range(len(choices)) if j != gold_i]
    rng.shuffle(distract)
    keep = [gold_i] + distract[:4]        # cap at 5 options, matching AQuA
    rng.shuffle(keep)
    choices = [choices[j] for j in keep]
    labels  = [labels[j]  for j in keep]
    gold = LET[labels.index(1)]
    recs.append({"id": f"truthfulqa_{i}",
                 "question": r["question"],
                 "options": [f"{LET[k]}) {c}" for k, c in enumerate(choices)],
                 "gold": gold})

json.dump(recs, open(OUT, "w"), indent=1)
n_opt = sum(len(r["options"]) for r in recs) / len(recs)
from collections import Counter
print(f"wrote {OUT}: n={len(recs)}, mean options={n_opt:.1f}")
print("gold letter distribution:", dict(sorted(Counter(r['gold'] for r in recs).items())))
print("sample:", json.dumps(recs[0], indent=1)[:340])
