# Supplementary code and results — "Two Regimes of Chain-of-Thought Unfaithfulness"

Anonymized supplement: analysis code and per-experiment result JSONs backing every
quantitative claim. Raw trace data and activation caches (~GBs) are excluded for size;
they will be released publicly with the camera-ready.

## Claims -> scripts map (main paper)
- S3 label semantics (crosstabs, census; Table 6 / App. A): scripts/label_crosstabs.py -> results/label_crosstabs.json
- S4 black-box audit + regime split (Tables 1-2, Fig. 3): scripts/audit_corrected.py -> results/audit_corrected.json
- S4 inversion on the benchmark's own released scores: scripts/faithcot_reproduce.py -> results/faithcot_reproduce.json
- S4 four-model NLI/DAG replication: scripts/rigorous_analysis.py -> results/regime_fullset_nlidag.json
- S6 regime probes (Table 3): scripts/ft34_probe.py, scripts/regime_transfers.py -> results/ft34_probe_*.json, results/regime_transfers_*.json
- S7 instructed construction, 7 models (Table 4): scripts/synth_generate.py, synth_extract.py, synth_analyze.py -> results/synth_*.json
- S7 hint testbed (generation, filtering, decodability, inversion): scripts/hint_generate.py (+build_logiqa.py for LogiQA) -> results/synth_*_hint*.json
- S7 transfer matrix (Table 5, Fig. 5): scripts/bridge3.py, bridge3_perm.py, hintL_bridge.py -> results/bridge3_*.json, results/hintL_bridge_*.json
- S7 question-only control: scripts/qonly_extract.py, qonly_transfer.py
- App. E robustness (template B, strict subset): scripts/strict_subset.py, flip_stability2.py
- App. G SAE negative: scripts/sae_transfers.py; steering: intervention_harness*.py
- App. H AUPRC + forest: scripts/appendix_extras.py -> results/appendix_extras.json
- Data integrity / external accuracy anchors: scripts/validate_data3.py -> results/validate3.json
- S4/S5 LLM-judge baseline (fifth family; full labeled set): scripts/judge_baseline.py -> results/judge_baseline.json
- Every headline number, recomputed from JSONs: scripts/paper_numbers.py

## Environment
Python 3.10+; numpy, scikit-learn, torch (GPU steps), transformers, matplotlib.
GPU steps ran on 2x RTX 3070 (8 GB) with 4-bit NF4 quantization; exact checkpoints in
paper Appendix (Table: Model checkpoints). CPU-only scripts are marked in their headers.
