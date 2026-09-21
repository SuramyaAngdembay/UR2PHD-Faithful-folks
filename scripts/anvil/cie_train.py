"""Train and score the CIE-Scorer detector from released code, for cie-scorer-stratified-spec.md.

Uses the authors' classes and their train()/evaluate() unchanged. Three modes:
  plumb  one epoch on whatever circuits exist. Functionality only; nothing it prints is a result.
  repro  stage 3: per dataset, paper Table 3 hyperparameters, their split logic, seeds 0-4. Reports
         the HELD-OUT test metric and, separately, the all-records figure their script's final line
         prints (train + validation + test together).
  oof    stage 4: one pooled detector, 5-fold CV stratified on the four annotation cells, scores
         averaged over seeds. Writes one out-of-fold continuous score per trace.
"""
import argparse, json, os, random, sys, time
from pathlib import Path
import numpy as np, torch
from sklearn.model_selection import StratifiedKFold, train_test_split

ap = argparse.ArgumentParser()
ap.add_argument("--mode", required=True, choices=["plumb", "repro", "oof"])
ap.add_argument("--faithcot_root", required=True)
ap.add_argument("--circuits_root", required=True)
ap.add_argument("--pyg_root", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--datasets", nargs="+", default=["logiqa", "truthfulqa", "aqua", "HLE_BIO"])
ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3, 4])
ap.add_argument("--epochs", type=int, default=20)
ap.add_argument("--model_name", default="meta-llama/Llama-3.1-8B-Instruct")
a = ap.parse_args()
DEV = "cuda"

from cie_scorer import detector as D
from cie_scorer.graph_features import build_ondisk_dataset_from_step_circuits

# paper Table 3: alpha, GNN layers, GNN width, learning rate  (lambda/beta act at circuit time)
TABLE3 = {"logiqa": (0.4, 2, 256, 1e-4), "truthfulqa": (0.5, 2, 256, 1e-4),
          "aqua": (0.5, 2, 256, 1e-4), "HLE_BIO": (0.5, 1, 128, 5e-5)}
POOLED = (0.5, 2, 256, 1e-4)      # fixed in spec amendment v1.1 before any training result existed

def records_for(ds):
    src = Path(a.faithcot_root) / ds / "llama-3.1-8b-instruct"
    pyg = Path(a.pyg_root) / ds
    if not (pyg / "index.json").exists():
        build_ondisk_dataset_from_step_circuits(root=str(pyg), circuit_root=str(Path(a.circuits_root) / ds),
                                                make_undirected=False, overwrite=False)
    recs = D.build_aligned_records(json_source=str(src), internal_pyg_dir=str(pyg))
    for r in recs:
        js = json.loads((src / f"{r.trace_id}.json").read_text())
        assert "unfaithfulness" in js, f"unlabelled trace reached training: {ds}/{r.trace_id}"
        r.ft = int(js.get("faithful_type", 0) or 0); r.ds = ds
        r.rid = f"{ds}/llama-3.1-8b-instruct/{r.trace_id}.json"
    return recs

def make_model(recs, hp):
    alpha, layers, width, _ = hp
    return D.JointFGWUnfaithfulnessDetector(
        ext_in_dim=recs[0].ext_embs.shape[1], int_in_dim=recs[0].internal_graphs[0].x.shape[1],
        hidden_dim=width, proj_dim=width, gin_layers=layers, alpha=alpha, seq_weight=1.0, sim_weight=0.4).to(DEV)

def score(model, recs):
    model.eval(); out = []
    with torch.no_grad():
        for r in recs:
            s, _ = model(r, device=DEV); out.append(float(s.item()))
    return out

all_recs = {ds: records_for(ds) for ds in a.datasets}
print({ds: len(v) for ds, v in all_recs.items()}, flush=True)
enc = D.FrozenSentenceEncoder(model_name=a.model_name, layer_idx=15, device=DEV)
for ds in a.datasets: D.precompute_external_embeddings(all_recs[ds], enc, batch_size=8)
del enc; torch.cuda.empty_cache()
result = {"mode": a.mode, "datasets": a.datasets, "seeds": a.seeds, "epochs": a.epochs}

if a.mode == "plumb":
    recs = [r for ds in a.datasets for r in all_recs[ds]]
    m = make_model(recs, POOLED); t = time.time()
    D.train(m, list(recs), [], list(recs), device=DEV, epochs=1, lr=POOLED[3])
    result["plumb"] = {"n": len(recs), "sec_per_epoch": round(time.time() - t, 1), "note": "functionality only"}

elif a.mode == "repro":
    result["repro"] = {}
    for ds in a.datasets:
        hp = TABLE3[ds]; runs = []
        for seed in a.seeds:
            D.set_seed(seed)
            tr, va, te = D.stratified_trace_split(all_recs[ds], test_size=0.4, val_size=0.3, seed=seed)
            m = make_model(all_recs[ds], hp)
            m, thr = D.train(m, tr, va, te, device=DEV, epochs=a.epochs, lr=hp[3])
            held = D.evaluate(m, te, device=DEV, threshold=thr)
            allr = D.evaluate(m, tr + va + te, device=DEV, threshold=thr)
            runs.append({"seed": seed, "n_test": len(te), "heldout_acc": held["acc"], "heldout_f1": held["f1"],
                         "allrecords_acc": allr["acc"], "allrecords_f1": allr["f1"]})
            print(ds, runs[-1], flush=True)
        result["repro"][ds] = runs

else:  # oof
    recs = [r for ds in a.datasets for r in all_recs[ds] if r.ft in (1, 2, 3, 4)]
    cells = np.array([r.ft for r in recs]); acc = np.zeros((len(a.seeds), len(recs)))
    for si, seed in enumerate(a.seeds):
        D.set_seed(seed)
        for fold, (tr_i, te_i) in enumerate(StratifiedKFold(5, shuffle=True, random_state=seed).split(cells, cells)):
            tr_all = [recs[i] for i in tr_i]; te = [recs[i] for i in te_i]
            tr_idx, va_idx = train_test_split(np.arange(len(tr_all)), test_size=0.3, random_state=seed,
                                              stratify=[r.label for r in tr_all])
            tr = [tr_all[i] for i in tr_idx]; va = [tr_all[i] for i in va_idx]
            m = make_model(recs, POOLED)
            m, _ = D.train(m, tr, va, te, device=DEV, epochs=a.epochs, lr=POOLED[3])
            acc[si, te_i] = score(m, te)
            print(f"seed {seed} fold {fold} done", flush=True)
    mean = acc.mean(0)
    result["oof"] = [{"rid": r.rid, "ds": r.ds, "ft": r.ft, "label": r.label, "score": float(mean[i]),
                      "score_by_seed": [float(x) for x in acc[:, i]]} for i, r in enumerate(recs)]

Path(a.out).parent.mkdir(parents=True, exist_ok=True)
Path(a.out).write_text(json.dumps(result, indent=1) + "\n")
print("CIE_TRAIN_DONE", a.mode, "->", a.out, flush=True)
