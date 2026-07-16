"""Figures 2-4 for the paper (light theme): transfer heatmap, confound/frontier panels, 7-model dots."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(os.path.dirname(HERE), "results")
plt.rcParams.update({"font.size": 9.5, "font.family": "serif", "figure.facecolor": "white"})
BLUE, ORANGE, RED, GRAY, GREEN = "#3b6fb6", "#d98032", "#c23b4b", "#777777", "#3a8f5f"

# ---- Fig: 3x3 transfer heatmap (Llama) ----
b = json.load(open(os.path.join(RES, "bridge3_llama.json")))
names = ["synthetic", "hint", "faithcot"]; disp = ["Instructed", "Hint-induced", "Annotated"]
M = np.zeros((3, 3))
for i, a in enumerate(names):
    for j, c in enumerate(names):
        M[i, j] = b["own_best"][a]["cv"] if i == j else b["transfers"][f"{a}->{c}"]["mean"]
fig, ax = plt.subplots(figsize=(3.4, 2.9), dpi=300)
im = ax.imshow(M, cmap="Blues", vmin=0.4, vmax=0.85)
from matplotlib.patches import Rectangle
for i in range(3):
    for j in range(3):
        ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=10.5,
                fontweight="bold" if i == j else "normal",
                color="white" if M[i,j] > 0.65 else "black")
    ax.add_patch(Rectangle((i-0.5, i-0.5), 1, 1, fill=False, edgecolor="black", lw=1.6))  # mark diagonal
ax.set_xticks(range(3), ["Instr.", "Hint", "Annot."], fontsize=8.5); ax.set_yticks(range(3), disp, fontsize=8.5)
ax.set_xlabel("test on"); ax.set_ylabel("train on")
ax.set_title("Probe transfer, layer-mean AUROC (Llama)", fontsize=9.5)
fig.colorbar(im, shrink=0.8)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "figs", "transfer_heatmap.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(HERE, "figs", "transfer_heatmap.png"), bbox_inches="tight", dpi=300)
print("transfer_heatmap.pdf/png")

# ---- Fig: confound + frontier two panels ----
fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.5), dpi=300, sharey=True)
full = [("Correctness", 0.696, (0.662, 0.734), RED), ("Answer-tracing (inv.)", 0.651, (0.611, 0.695), GRAY),
        ("NLI (# unsup.)", 0.569, (0.523, 0.615), GRAY), ("DAG (max lb.)", 0.543, (0.496, 0.588), GRAY)]
front = [("Answer-tracing", 0.545, (0.468, 0.611), GRAY), ("Interventions", 0.485, None, GRAY),
         ("NLI", 0.514, None, GRAY), ("DAG", 0.490, None, GRAY)]
for ax, data, title in [(axes[0], full, "Full benchmark (n=633)"), (axes[1], front, "Correct answers only (n=270)")]:
    ys = np.arange(len(data))[::-1]
    for y, (name, v, ci, c) in zip(ys, data):
        ax.barh(y, v, height=0.55, color=c, alpha=0.85)
        if ci: ax.plot(list(ci), [y, y], color="black", lw=1.1)
        ax.text(-0.02, y, name, ha="right", va="center", fontsize=8.5)
    ax.axvline(0.5, color=RED, ls="--", lw=1.1)
    ax.set_xlim(0, 0.8); ax.set_yticks([]); ax.set_title(title, fontsize=9.5)
    ax.spines[["top", "right", "left"]].set_visible(False)
axes[0].set_xlabel("AUROC vs. human label"); axes[1].set_xlabel("AUROC, faithful vs. post-hoc")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "figs", "confound_frontier.pdf"), bbox_inches="tight")
print("confound_frontier.pdf")

# ---- Fig: 7-model dot plot with surface baselines ----
models = [("Qwen-2.5-7B", "qwen"), ("Gemma-4-12B", "gemma4"), ("Llama-3.1-8B", "llama"),
          ("Qwen3-8B", "qwen3"), ("DeepSeek-R1-Dist.-7B", "deepseek"), ("Gemma-2-9B", "gemma"),
          ("DeepSeek-R1-0528-8B", "dsr0528")]
held, surf = [], []
for _, k in models:
    d = json.load(open(os.path.join(RES, f"synth_{k}.json")))
    held.append(d["wb_heldout_auroc"]); surf.append(d["black_box"]["surface_auroc"])
fig, ax = plt.subplots(figsize=(4.6, 2.9), dpi=300)
ys = np.arange(len(models))[::-1]
for y, (name, _), h, s in zip(ys, models, held, surf):
    ax.plot([s, h], [y, y], color="#cccccc", lw=2, zorder=1)
    ax.scatter([h], [y], color=BLUE, s=42, zorder=3, label="probe (held-out)" if y == ys[0] else None)
    ax.scatter([s], [y], color=GRAY, s=30, marker="D", zorder=3, label="surface baseline" if y == ys[0] else None)
    ax.text(0.392, y, name, ha="right", va="center", fontsize=8.5)
ax.axvline(0.5, color=RED, ls="--", lw=1.1)
ax.set_xlim(0.4, 0.9); ax.set_yticks([])
ax.set_xlabel("AUROC, post-hoc vs. genuine")
ax.spines[["top", "right", "left"]].set_visible(False)
leg = ax.legend(loc="lower right", frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "figs", "seven_models.pdf"), bbox_inches="tight")
print("seven_models.pdf")
