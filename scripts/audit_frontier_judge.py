#!/usr/bin/env python3
"""Paired, question-clustered audit of frozen FaithCoT judge scores; no inference.

Uses both released faithfulness fields separately, native four-way correctness,
and an exact four-pair-type AUC decomposition. Requires numpy only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np

# Full pinned SHA; kept explicit to reject a changed upstream archive.
ARCHIVE_SHA = "9ef674e33cae2654b2fe00ee2a00610f595eedb4ae649c4ed6a277b4a7eb6eba"
MODELS = ["gpt-4o-mini", "gpt-5.2-2025-12-11"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def raw_scores(path, expected_model):
    rows = [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
    assert len({r["rid"] for r in rows}) == len(rows), "Duplicate response ID"
    assert all(r["model"] == expected_model for r in rows), "Unexpected requested model"
    assert all(type(r["score"]) is int and 0 <= r["score"] <= 100 for r in rows)
    return {r["rid"]: r["score"] for r in rows}


def auc(pos, neg):
    """Histogram AUC, ties receive half credit, NaN on undefined draws."""
    denom = pos.sum(-1) * neg.sum(-1)
    num = (pos * (np.cumsum(neg, axis=-1) - neg / 2)).sum(-1)
    return np.divide(num, denom, out=np.full_like(num, np.nan), where=denom > 0)


def endpoints(h):
    # h: draw x model x cell x score; cell = 2 * unfaithful + incorrect.
    out = {
        "pooled": auc(h[:, :, 2] + h[:, :, 3], h[:, :, 0] + h[:, :, 1]),
        "incorrect_regime": auc(h[:, :, 3], h[:, :, 1]),
        "correct_regime": auc(h[:, :, 2], h[:, :, 0]),
        "score_vs_incorrectness": auc(h[:, :, 1] + h[:, :, 3], h[:, :, 0] + h[:, :, 2]),
    }
    total_pairs = (h[:, :, 2:].sum((-1, -2)) * h[:, :, :2].sum((-1, -2)))
    pieces = []
    for name, p, n in [("wrong_U_wrong_F", 3, 1), ("wrong_U_right_F", 3, 0),
                       ("right_U_wrong_F", 2, 1), ("right_U_right_F", 2, 0)]:
        pos, neg = h[:, :, p], h[:, :, n]
        pair_count = pos.sum(-1) * neg.sum(-1)
        pair_auc = auc(pos, neg)
        weight = np.divide(pair_count, total_pairs, out=np.zeros_like(pair_count), where=total_pairs > 0)
        # A zero-weight component contributes zero even when its AUC is undefined.
        piece = np.where(pair_count > 0, pair_auc * weight, 0)
        out["pair_auc_" + name] = pair_auc
        out["weighted_auc_" + name] = piece
        pieces.append(piece)
    out["weighted_within"] = pieces[0] + pieces[3]
    out["weighted_cross"] = pieces[1] + pieces[2]
    np.testing.assert_allclose(sum(pieces), out["pooled"], atol=1e-12)
    return out


def interval(values):
    valid = values[np.isfinite(values)]
    return {"defined_draws": len(valid), "total_draws": len(values),
            "ci95": np.quantile(valid, [.025, .975]).tolist() if len(valid) == len(values) else None}


def direct_auc(y, scores):
    diffs = scores[y == 1, None] - scores[y == 0][None, :]
    return float(((diffs > 0) + .5 * (diffs == 0)).mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--mini", type=Path, default=Path("results/judge_raw_mini.jsonl"))
    ap.add_argument("--gpt52", type=Path, default=Path("results/judge_raw_gpt52.jsonl"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--draws", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20260919)
    args = ap.parse_args()
    assert args.draws >= 1000
    if args.out.exists():
        raise FileExistsError(f"Refusing to overwrite {args.out}")
    assert sha(args.archive) == ARCHIVE_SHA, "Archive is not the pinned release"
    sources = {}
    with zipfile.ZipFile(args.archive) as z:
        for name in z.namelist():
            if name.startswith("faithcot/") and name.endswith(".json") and "/response_" in name:
                d = json.loads(z.read(name))
                if d.get("faithful_type") in [1, 2, 3, 4]:
                    sources[name.removeprefix("faithcot/")] = d
    raws = [raw_scores(args.mini, MODELS[0]), raw_scores(args.gpt52, MODELS[1])]
    assert set(raws[0]) == set(raws[1]) == set(sources)
    ids = sorted(sources)
    assert len(ids) == 1303
    records = [sources[rid] for rid in ids]
    scores = np.array([[raw[rid] for raw in raws] for rid in ids])
    ft = np.array([r["faithful_type"] for r in records])
    wrong = np.isin(ft, [1, 2]).astype(int)
    targets = {"four_way_derived": np.isin(ft, [2, 4]).astype(int),
               "binary_unfaithfulness": np.array([r["unfaithfulness"] for r in records])}
    assert set(targets["binary_unfaithfulness"]) == {0, 1}
    # Exact released question text; no strip/lowercase normalization or generator partitioning.
    questions, group = np.unique([r["question"] for r in records], return_inverse=True)
    rng = np.random.default_rng(args.seed)
    multiplicities = rng.multinomial(len(questions), np.ones(len(questions)) / len(questions),
                                    size=args.draws).astype(np.int64)
    result = {"n": len(ids), "question_clusters": len(questions),
              "native_type_counts": {str(k): int((ft == k).sum()) for k in [1, 2, 3, 4]},
              "faithfulness_field_disagreements": int((targets["four_way_derived"] != targets["binary_unfaithfulness"]).sum()),
              "bootstrap": {"unit": "exact question text", "draws": args.draws, "seed": args.seed,
                            "interval": "percentile 95%, paired models and endpoints, not multiplicity adjusted",
                            "scope": "Sampling uncertainty conditional on these frozen scores; no model/run uncertainty"},
              "models": MODELS, "targets": {}}
    for target_name, y in targets.items():
        hist = np.zeros((len(questions), 2, 4, 101), dtype=np.int64)
        cell = 2 * y + wrong
        for model in range(2):
            np.add.at(hist, (group, model, cell, scores[:, model]), 1)
        point = endpoints(hist.sum(0, keepdims=True).astype(float))
        # Independent direct-comparison checks of every primary AUC.
        for model in range(2):
            for key, label, use in [
                ("pooled", y, np.ones(len(y), bool)),
                ("incorrect_regime", y, wrong == 1), ("correct_regime", y, wrong == 0),
                ("score_vs_incorrectness", wrong, np.ones(len(y), bool)),
            ]:
                np.testing.assert_allclose(point[key][0, model], direct_auc(label[use], scores[use, model]), atol=1e-12)
        chunks = {key: [] for key in point}
        for start in range(0, args.draws, 250):
            # Exact integer counts avoid spurious Accelerate/NumPy float-matmul
            # warnings on some macOS builds. Floating arithmetic starts at AUC.
            h = (multiplicities[start:start + 250] @ hist.reshape(len(questions), -1)).reshape(-1, 2, 4, 101).astype(float)
            assert np.isfinite(h).all() and (h >= 0).all()
            for key, values in endpoints(h).items():
                chunks[key].append(values)
        summary = {}
        for key, estimate in point.items():
            draws = np.concatenate(chunks[key])
            summary[key] = {"mini": float(estimate[0, 0]), "gpt52": float(estimate[0, 1]),
                            "difference": float(estimate[0, 1] - estimate[0, 0]),
                            "difference_uncertainty": interval(draws[:, 1] - draws[:, 0]),
                            "mini_uncertainty": interval(draws[:, 0]), "gpt52_uncertainty": interval(draws[:, 1])}
        result["targets"][target_name] = summary
    args.out.mkdir(parents=True, exist_ok=False)
    result_path = args.out / "results.json"
    result_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    manifest = {"script": {"path": str(Path(__file__).resolve()), "sha256": sha(__file__)},
                "inputs": [{"path": str(p.resolve()), "sha256": sha(p)} for p in [args.archive, args.mini, args.gpt52]],
                "output": {"path": result_path.name, "sha256": sha(result_path)},
                "numpy_version": np.__version__, "arguments": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for target, summary in result["targets"].items():
        print(target)
        for key in ["pooled", "incorrect_regime", "correct_regime", "score_vs_incorrectness", "weighted_within", "weighted_cross"]:
            s = summary[key]
            print(f"  {key}: {s['mini']:.6f} -> {s['gpt52']:.6f}, diff {s['difference']:+.6f}, CI {s['difference_uncertainty']['ci95']}")


if __name__ == "__main__":
    main()
