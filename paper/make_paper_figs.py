"""
Paper figures (light theme, ACL-friendly). Fig 1: the three-way depth gradient for Llama —
per-layer probe CV AUROC for instructed-synthetic (peaks early), hint-organic (middle),
and human-annotated FaithCoT (late). Data from results/*.json (real numbers only).
Usage: python3 paper/make_paper_figs.py   (from repo root)
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")

BLUE, ORANGE, RED, GRAY = "#3b6fb6", "#d98032", "#c23b4b", "#777777"
plt.rcParams.update({"font.size": 10, "font.family": "serif", "axes.edgecolor": "#444",
                     "figure.facecolor": "white", "axes.facecolor": "white"})

synth = json.load(open(os.path.join(RES, "synth_llama.json")))["per_layer_cv_auroc"]
hint  = json.load(open(os.path.join(RES, "synth_llama_hint.json")))["per_layer_cv_auroc"]
fc    = json.load(open(os.path.join(RES, "faithcot_perlayer.json")))["llama"]

fig, ax = plt.subplots(figsize=(5.4, 3.0), dpi=300)
for vals, color, label in [(synth, BLUE, "Instructed synthetic (answer-first prompt)"),
                           (hint, ORANGE, "Hint-induced (unverbalized flip)"),
                           (fc, RED, "Human-annotated (FaithCoT-Bench)")]:
    ax.plot(range(len(vals)), vals, color=color, lw=1.8, label=label)
    b = max(range(len(vals)), key=lambda i: vals[i])
    ax.scatter([b], [vals[b]], color=color, s=26, zorder=5)
    ax.annotate(f"L{b}", (b, vals[b]), xytext=(b - 1.2, vals[b] + 0.022),
                color=color, fontsize=9, fontweight="bold")
ax.axhline(0.5, color=GRAY, ls="--", lw=1)
ax.text(0.3, 0.507, "chance", color=GRAY, fontsize=8)
ax.set_xlabel("Layer (Llama-3.1-8B)")
ax.set_ylabel("Probe CV AUROC")
ax.set_ylim(0.42, 0.85)
ax.grid(color="#e5e5e5", lw=0.5)
ax.spines[["top", "right"]].set_visible(False)
leg = ax.legend(loc="lower right", frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "figs", "depth_gradient.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(HERE, "figs", "depth_gradient.png"), bbox_inches="tight")
print("figs/depth_gradient.{pdf,png}")
