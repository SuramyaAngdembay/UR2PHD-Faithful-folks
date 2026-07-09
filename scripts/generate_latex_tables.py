import json
import glob
import os

# TABLE 1: White-Box Synthetic Scaling
synth_files = glob.glob('results/synth_*.json')
synth_data = []
for f in synth_files:
    d = json.load(open(f))
    synth_data.append(d)

# Sort models by held-out AUROC (descending), matching the paper table
synth_data.sort(key=lambda x: -x.get('wb_heldout_auroc', x.get('wb_cv_auroc', 0)))

latex_table_1 = """
\\begin{table}[h]
\\centering
\\begin{tabular}{lcccc}
\\toprule
\\textbf{Model} & \\textbf{n pairs} & \\textbf{Best Layer} & \\textbf{Held-out AUROC} & \\textbf{Perm $p$-value} \\\\
\\midrule
"""
model_names = {
    "qwen": "Qwen-2.5-7B",
    "llama": "Llama-3.1-8B",
    "gemma": "Gemma-2-9B-IT",
    "gemma4": "Gemma-4-12B",
    "gemma4e": "Gemma-4-E4B-IT",
    "qwen3": "Qwen3-8B",
    "deepseek": "DeepSeek-R1-Distill-Qwen-7B",
    "dsr0528": "DeepSeek-R1-0528-Qwen3-8B"
}
for d in synth_data:
    mname = model_names.get(d['model'], d['model'])
    n = d['n_posthoc']  # matched genuine/post-hoc pairs (n_posthoc == pair count)
    l = d['wb_best_layer']
    auc = d.get('wb_heldout_auroc', d.get('wb_cv_auroc', 0))
    p = d['wb_perm_p']
    latex_table_1 += f"{mname} & {n} & {l} & {auc:.3f} & {p:.3f} \\\\\n"

latex_table_1 += """\\bottomrule
\\end{tabular}
\\caption{White-box linear probe detection of the post-hoc-vs-genuine construction on the synthetic benchmark across %d models. $n$ = matched genuine/post-hoc pairs; significance via 200-permutation selection-corrected tests.}""" % len(synth_data) + """
\\label{tab:synth_scaling}
\\end{table}
"""

# TABLE 2: The Proxy Bridge Failure
bridge_files = glob.glob('results/bridge_*.json')
latex_table_2 = """
\\begin{table}[h]
\\centering
\\begin{tabular}{lcccc}
\\toprule
\\textbf{Model} & \\textbf{Synth Best L} & \\textbf{Real Best L} & \\textbf{Real $\\to$ Synth AUC} & \\textbf{Synth $\\to$ Real AUC} \\\\
\\midrule
"""
for f in bridge_files:
    d = json.load(open(f))
    mname = "Llama-3.1-8B" if d['model'] == 'llama' else "Qwen-2.5-7B"
    sl = d['synth_best_layer']
    rl = d['faithcot_best_layer']
    f2s = d['sweep_all']['fc2s_best']
    s2f = d['sweep_all']['s2fc_best']
    latex_table_2 += f"{mname} & L{sl} & L{rl} & {f2s:.3f} & {s2f:.3f} \\\\\n"

latex_table_2 += """\\bottomrule
\\end{tabular}
\\caption{The Proxy Bridge Failure: Synthetic post-hoc is encoded at early layers (L9/L10) while real organic post-hoc is encoded late (L22/L29). Cross-distribution transfer peaks at near chance ($< 0.60$), demonstrating that prompt-induced rationalization does not transfer to real unfaithfulness.}
\\label{tab:bridge_failure}
\\end{table}
"""

# Inject into main.tex ONLY at the placeholder marker; otherwise print for manual use so we
# never silently clobber the now hand-maintained tables (or no-op while claiming success).
tex_path = 'overleaf-proposal/main.tex'
target = """% TODO: Insert tables and numerical results for:
% 1. Black-box negative results (4x4 scaled)
% 2. White-box decodability (6-model synthetic scaling)
% 3. The Real-Synthetic Bridge failure
% 4. Metric Inversion (soft_faithfulness AUC)"""
replacement = latex_table_1 + "\n" + latex_table_2

with open(tex_path, 'r') as f:
    content = f.read()
if target in content:
    with open(tex_path, 'w') as f:
        f.write(content.replace(target, replacement))
    print("Tables injected into main.tex at the placeholder marker.")
else:
    print("Placeholder marker not found in main.tex (tables are maintained inline).")
    print("Regenerated LaTeX below -- copy in manually if you want to refresh:\n")
    print(replacement)
