"""Build CIE-Scorer step circuits for LABELLED Llama-3.1-8B-Instruct FaithCoT traces.

Calls the authors' own functions with their own constants (cie_scorer.circuit); the loop body below
is theirs (score_jsonl.build_circuits) with three operational changes and no methodological one:
  1. a wall-clock budget, so short backfill jobs exit cleanly instead of being killed mid-write;
  2. atomic writes (tmp then rename), so a killed job can never leave a half-written graph that a
     resume would then trust;
  3. labelled traces only. Their loader gives an unlabelled trace label 0 (faithful) by default;
     building no circuits for those keeps them out of training by construction.
Token-selection lambda and beta are set per call because the paper's Table 3 varies them by dataset.
Per-graph timings go to a JSONL so SU projections are measured, not guessed.
"""
import argparse, json, os, sys, time
from pathlib import Path
import torch

ap = argparse.ArgumentParser()
ap.add_argument("--faithcot_root", required=True)
ap.add_argument("--dataset", required=True)
ap.add_argument("--out_root", required=True)
ap.add_argument("--lam", type=float, default=0.5)
ap.add_argument("--beta", type=float, default=0.5)
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--budget_min", type=float, default=0, help="stop cleanly after this many minutes (0 = no limit)")
ap.add_argument("--model_name", default="meta-llama/Llama-3.1-8B-Instruct")
ap.add_argument("--transcoder_name", default="facebook/crv-8b-instruct-transcoders")
a = ap.parse_args()
T0 = time.time()

from cie_scorer import circuit as C
from cie_scorer.score_faithcot import load_faithcot_rows
from cie_scorer.score_jsonl import load_response
from circuit_tracer import ReplacementModel

src = Path(a.faithcot_root) / a.dataset / "llama-3.1-8b-instruct"
rows = [r for r in load_faithcot_rows(src) if "unfaithfulness" in r]
if a.limit: rows = rows[:a.limit]
out = Path(a.out_root) / a.dataset; out.mkdir(parents=True, exist_ok=True)
tlog = out / "timing.jsonl"

todo = []
for row in rows:
    rp = src / f"response_{row['_cie_row_id']}.json"
    _, steps = load_response(rp)
    td = out / f"response_{row['_cie_row_id']}"
    need = [i for i in range(len(steps) + 1)
            if not ((td / f"step_{i}.pt").exists() and (td / "selection_meta" / f"step_{i}_selection.json").exists())]
    if need: todo.append((row, rp, steps, td, need))
print(f"[{a.dataset}] labelled traces {len(rows)}; traces with missing graphs {len(todo)}; lambda={a.lam} beta={a.beta}", flush=True)
if not todo:
    print("CIRCUITS_COMPLETE", a.dataset, flush=True); sys.exit(0)

t = time.time()
model = ReplacementModel.from_pretrained(a.model_name, a.transcoder_name, dtype=torch.bfloat16)
print(f"model+transcoders loaded in {time.time()-t:.0f}s; GPU mem {torch.cuda.max_memory_allocated()/1e9:.1f} GB", flush=True)

n_graphs = 0; stopped = False
for row, rp, steps, td, need in todo:
    if a.budget_min and (time.time() - T0) / 60 > a.budget_min:
        stopped = True; break
    (td / "selection_meta").mkdir(parents=True, exist_ok=True)
    items = [row["prompt"]] + steps
    for k in need:
        sentence = items[k]; g0 = time.time()
        selected, input_ids, entropies, causal_scores, final_scores = C.select_positions_entropy_causal(
            prompt=sentence, model=model, top_k=C.TOKEN_BUDGET, temperature=C.ENTROPY_TEMPERATURE,
            candidate_budget=C.CANDIDATE_BUDGET, sentence_lambda=a.lam, beta=a.beta,
            diversity_penalty=C.DIVERSITY_PENALTY, always_include_last=C.ALWAYS_INCLUDE_LAST, skip_first_token=True)
        target_pos = max(selected)
        graph = C.attribute_compressed(
            prompt=sentence, model=model, max_n_logits=C.MAX_N_LOGITS, desired_logit_prob=C.DESIRED_LOGIT_PROB,
            batch_size=C.BATCH_SIZE, max_feature_nodes=C.MAX_FEATURE_NODES,
            max_features_per_position=C.MAX_FEATURES_PER_POSITION, offload="cpu", verbose=False,
            update_interval=C.UPDATE_INTERVAL, selected_positions=selected, target_pos=target_pos)
        gp = td / f"step_{k}.pt"; tmp = td / f".step_{k}.pt.tmp"
        graph.to_pt(tmp); os.replace(tmp, gp)
        meta = {"source_trace_file": rp.name, "step_num": k, "step_text": sentence if k else "__base_prompt__",
                "prompt": sentence, "selected_positions": selected,
                "selected_tokens": C.decode_selected_tokens(input_ids, selected, model), "target_pos": target_pos,
                "entropies": [float(v) for v in entropies.tolist()],
                "causal_scores": {str(i): float(v) for i, v in causal_scores.items()},
                "final_scores": {str(i): float(v) for i, v in final_scores.items()}}
        mp = td / "selection_meta" / f"step_{k}_selection.json"; mt = td / "selection_meta" / f".step_{k}.tmp"
        mt.write_text(json.dumps(meta)); os.replace(mt, mp)
        n_graphs += 1
        with open(tlog, "a") as fh:
            fh.write(json.dumps({"trace": row["_cie_row_id"], "step": k, "n_tokens": int(input_ids.shape[-1]),
                                 "sec": round(time.time() - g0, 2),
                                 "peak_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2)}) + "\n")
el = time.time() - T0
print(f"[{a.dataset}] built {n_graphs} graphs in {el/60:.1f} min ({el/max(n_graphs,1):.1f} s/graph incl. load); "
      f"peak GPU {torch.cuda.max_memory_allocated()/1e9:.1f} GB", flush=True)
print(("BUDGET_STOP " if stopped else "CIRCUITS_COMPLETE ") + a.dataset, flush=True)
