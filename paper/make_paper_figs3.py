"""
Figures for the TWO-REGIME paper (corrected ft semantics, 2026-07-16).
ft1=faithful-INCORRECT, ft2=unfaithful-INCORRECT, ft3=faithful-CORRECT, ft4=unfaithful-CORRECT
(verified against released data; see notes/2026-07-16-data-validation.md).

Outputs (paper/figs/):
  two_regimes.pdf     -- 3-panel bar chart: full / incorrect regime / correct regime (replaces confound_frontier)
  depth_gradient.pdf  -- per-layer curves, relabeled: annotated anchor = INCORRECT regime (ft1v2); + ft3v4 curve
  transfer_heatmap.pdf-- 3x3 llama heatmap, 'annotated' relabeled 'annot. (incorrect rgm.)'
  (seven_models.pdf unchanged -- reused as-is)
Run: python3 paper/make_paper_figs3.py   (from repo root)
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = lambda f: json.load(open(f"results/{f}.json"))
plt.rcParams.update({"font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5,
                     "figure.dpi": 200, "savefig.bbox": "tight"})
BLUE, RED, GREY, GREEN = "#3b6fb6", "#c23b3b", "#8a8a8a", "#3b8a5a"

# ---------------------------------------------------------------- two_regimes
a = R("audit_corrected")
SIGS = [("incorrectness", "incorrectness"), ("answer-tracing\n(inverted)", "soft_raw"),
        ("interventions", "interventions"), ("NLI support", "nli_n_unsup"), ("DAG structure", "dag_maxlb")]
PANELS = [("Full benchmark  (n=633)", "full_audit"),
          ("INCORRECT answers  (n=270)\nhonest error vs. unfaithful error", "incorrect_regime"),
          ("CORRECT answers  (n=363)\nfaithful vs. post-hoc", "correct_regime")]
fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.5), sharey=True)
for ax, (title, key) in zip(axes, PANELS):
    labels, vals, los, his, cols = [], [], [], [], []
    for name, sk in SIGS:
        if key != "full_audit" and sk == "incorrectness":
            continue  # degenerate within a regime
        v = a[key][sk]
        labels.append(name); vals.append(v["auroc"])
        los.append(v["auroc"] - v["ci"][0]); his.append(v["ci"][1] - v["auroc"])
        sig = v["ci"][0] > 0.5
        cols.append(RED if sk == "incorrectness" else (BLUE if sig else GREY))
    x = np.arange(len(vals))
    ax.bar(x, vals, 0.62, color=cols, yerr=[los, his], error_kw=dict(lw=0.9, capsize=2), zorder=3)
    ax.axhline(0.5, color="k", ls="--", lw=0.8, zorder=2)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=38, ha="right", fontsize=7)
    ax.set_ylim(0.38, 0.78); ax.set_title(title, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
axes[0].set_ylabel("AUROC vs. human label")
fig.savefig("paper/figs/two_regimes.pdf"); plt.close(fig)
print("two_regimes.pdf")

# ------------------------------------------------------------ depth_gradient
b3 = R("bridge3_llama")
pl_ft12 = R("faithcot_perlayer")["llama"]                      # annotated, INCORRECT regime
pl_syn = R("synth_llama")["per_layer_cv_auroc"]
pl_hint = R("synth_llama_hint")["per_layer_cv_auroc"]
fig, ax = plt.subplots(figsize=(3.35, 2.4))
for curve, lab, c in [(pl_syn, "instructed (peak L9)", GREEN),
                      (pl_hint, "hint-induced (peak L17)", BLUE),
                      (pl_ft12, "annotated, incorrect rgm. (peak L29)", RED)]:
    curve = curve[:33]
    ax.plot(range(len(curve)), curve, lw=1.4, color=c, label=lab)
    pk = int(np.argmax(curve)); ax.scatter([pk], [curve[pk]], s=16, color=c, zorder=5)
ax.axhline(0.5, color="k", ls="--", lw=0.8)
ax.set_xlabel("layer (Llama-3.1-8B)"); ax.set_ylabel("within-distribution CV AUROC")
ax.set_ylim(0.42, 0.82); ax.legend(fontsize=6.5, loc="lower right", framealpha=0.9)
ax.spines[["top", "right"]].set_visible(False)
fig.savefig("paper/figs/depth_gradient.pdf"); plt.close(fig)
print("depth_gradient.pdf")

# ----------------------------------------------------------- transfer_heatmap
names = ["synthetic", "hint", "faithcot"]
disp = ["instructed", "hint-induced", "annotated\n(incorrect rgm.)"]
M = np.zeros((3, 3))
for i, tr in enumerate(names):
    for j, te in enumerate(names):
        M[i, j] = b3["own_best"][tr]["cv"] if tr == te else b3["transfers"][f"{tr}->{te}"]["mean"]
fig, ax = plt.subplots(figsize=(3.1, 2.7))
im = ax.imshow(M, cmap="RdBu_r", vmin=0.3, vmax=0.8)
for i in range(3):
    for j in range(3):
        ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=8.5,
                fontweight="bold" if i == j else "normal",
                color="white" if abs(M[i, j] - 0.55) > 0.13 else "black")
        if i == j:
            ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False, ec="k", lw=1.6))
ax.set_xticks(range(3)); ax.set_xticklabels(disp, fontsize=7)
ax.set_yticks(range(3)); ax.set_yticklabels(disp, fontsize=7)
ax.set_xlabel("test on"); ax.set_ylabel("train on")
fig.colorbar(im, ax=ax, shrink=0.85, label="AUROC (diag: CV; off-diag: layer-mean)")
fig.savefig("paper/figs/transfer_heatmap.pdf"); plt.close(fig)
print("transfer_heatmap.pdf")
