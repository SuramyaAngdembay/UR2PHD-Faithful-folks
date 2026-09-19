"""Audit the release census and numerical claims in the September 19 sweep.

No inference or answer adjudication. Native correctness and exact-string
correctness are separate estimands; binary and four-way labels stay separate.
Run with --archive <faithcot.zip> --output-dir <new directory>.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import zipfile


ARCHIVE_SHA256 = "9ef674e33cae2654b2fe00ee2a00610f595eedb4ae649c4ed6a277b4a7eb6eba"
ARCHIVE_COMMIT = "5112797173f3ff7573f030bca28411a596fd52e8"


def f1(tp, fp, fn):
    denominator = 2 * tp + fp + fn
    return 2 * tp / denominator if denominator else None


def stats(cells):
    ui, uc, fi, fc = (cells.get(k, 0) for k in ("UI", "UC", "FI", "FC"))
    return {
        "n": ui + uc + fi + fc,
        "cells": dict(zip(("UI", "UC", "FI", "FC"), (ui, uc, fi, fc))),
        "incorrectness_auroc": 0.5 + 0.5 * (ui / (ui + uc) - fi / (fi + fc)),
        "phi": (ui * fc - uc * fi)
        / math.sqrt((ui + uc) * (fi + fc) * (ui + fi) * (uc + fc)),
        "incorrectness_positive_class_f1": f1(ui, fi, uc),
        "unfaithfulness_prevalence_correct": uc / (uc + fc),
        "unfaithfulness_prevalence_incorrect": ui / (ui + fi),
    }


def summarize(rows, correctness, four_way_target=False):
    counts = Counter()
    for _, record in rows:
        unfaithful = (record["faithful_type"] in (2, 4)
                      if four_way_target else record["unfaithfulness"] == 1)
        counts[("U" if unfaithful else "F") + ("C" if correctness(record) else "I")] += 1
    return stats(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    raw = args.archive.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ARCHIVE_SHA256:
        raise ValueError("Archive revision differs from the audited release")
    if args.output_dir.exists():
        raise FileExistsError("Refusing to overwrite an existing audit")
    with zipfile.ZipFile(args.archive) as archive:
        rows = [(name, json.loads(archive.read(name))) for name in archive.namelist()
                if name.endswith(".json") and "response_" in name
                and not name.startswith("__MACOSX")]
    labeled = [(n, d) for n, d in rows if d.get("unfaithfulness") in (0, 1)]
    valid = [(n, d) for n, d in labeled if d.get("faithful_type") in (1, 2, 3, 4)]
    parseable = [(n, d) for n, d in labeled if d.get("label") is not None
                 and d.get("sample_0", {}).get("parsed_final_answer") is not None]
    parseable_valid = [(n, d) for n, d in parseable if d.get("faithful_type") in (1, 2, 3, 4)]
    missing = [(n, d) for n, d in labeled
               if d.get("sample_0", {}).get("parsed_final_answer") is None]
    native = lambda d: d["faithful_type"] in (3, 4)
    exact = lambda d: str(d["sample_0"]["parsed_final_answer"]).strip().upper() == str(d["label"]).strip().upper()
    disagreements = [n for n, d in parseable_valid if native(d) != exact(d)]
    result = {
        "release_records": len(rows),
        "binary_labeled_records": len(labeled),
        "valid_four_way_records": len(valid),
        "top_level_field_counts": dict(Counter(k for _, d in rows for k in d)),
        "sample_0_field_counts": dict(Counter(k for _, d in rows for k in d.get("sample_0", {}))),
        "four_way_counts": dict(Counter(str(d["faithful_type"]) for _, d in valid)),
        "binary_vs_four_way_disagreements": sum(d["unfaithfulness"] != int(d["faithful_type"] in (2, 4)) for _, d in valid),
        "claude_subset_binary_target_exact_correctness": summarize(parseable, exact),
        "same_subset_valid_types_native_correctness": summarize(parseable_valid, native),
        "full_valid_binary_target_native_correctness": summarize(valid, native),
        "full_valid_four_way_target_native_correctness": summarize(valid, native, True),
        "excluded_missing_predictions": {
            "n": len(missing),
            "four_way_counts": dict(Counter(str(d["faithful_type"]) for _, d in missing)),
            "domains": dict(Counter(n.split("/")[1] for n, _ in missing)),
        },
        "parseable_correctness_disagreement_members": disagreements,
        "paper_figure_counts_diagnostic_only": stats({"UI": 204, "UC": 185, "FI": 189, "FC": 605}),
    }
    # Same true class counts for both detectors; positive-class F1 can reverse
    # under pooling even though each detector's pooled F1 is collapsible.
    detector_counts = {"A": [(6, 59, 4), (35, 6, 55)],
                       "B": [(1, 14, 9), (31, 9, 59)]}
    collapse = {}
    for name, groups in detector_counts.items():
        group_f1 = [f1(*g) for g in groups]
        denominators = [2 * tp + fp + fn for tp, fp, fn in groups]
        weights = [d / sum(denominators) for d in denominators]
        pooled = f1(*(sum(g[j] for g in groups) for j in range(3)))
        assert math.isclose(pooled, sum(w * f for w, f in zip(weights, group_f1)))
        collapse[name] = {"groups_tp_fp_fn": groups, "group_f1": group_f1,
                          "weights": weights, "pooled_f1": pooled}
    assert all(a > b for a, b in zip(collapse["A"]["group_f1"], collapse["B"]["group_f1"]))
    assert collapse["A"]["pooled_f1"] < collapse["B"]["pooled_f1"]
    result["f1_collapsibility_ranking_counterexample"] = collapse
    result["fixed_operating_point_prevalence_example"] = {
        str(p): 2 * p * 0.7 / (p * 1.7 + (1 - p) * 0.3) for p in (0.154, 0.574)
    }
    # With 70 TP, 30 FN, 30 FP, 70 TN at threshold .5, continuous rankings
    # within either side of the threshold are unspecified: AUC need not be .7.
    result["same_sensitivity_specificity_different_continuous_auc"] = {
        "sensitivity": 0.7, "specificity": 0.7,
        "low_auc": 70 * 70 / (100 * 100),
        "low_scores_tp_fn_fp_tn": [0.6, 0.1, 0.9, 0.4],
        "high_auc": (70 * 100 + 30 * 70) / (100 * 100),
        "high_scores_tp_fn_fp_tn": [0.9, 0.4, 0.6, 0.1],
        "hard_prediction_auc": (0.7 + 0.7) / 2,
    }
    args.output_dir.mkdir(parents=True)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (args.output_dir / "results.json").write_text(output)
    manifest = {
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "archive_sha256": digest, "archive_commit": ARCHIVE_COMMIT,
        "archive_url": f"https://raw.githubusercontent.com/se7esx/FaithCoT-BENCH/{ARCHIVE_COMMIT}/faithcot.zip",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "results_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "python_version": platform.python_version(), "new_inference": False,
        "interpretation": "Census and mathematical checks, not a detector leaderboard reproduction or independent correctness adjudication.",
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "claude_subset_binary_target_exact_correctness",
        "full_valid_binary_target_native_correctness",
        "full_valid_four_way_target_native_correctness",
        "excluded_missing_predictions")}, indent=2))


if __name__ == "__main__":
    main()
