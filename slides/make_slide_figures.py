"""
Generate theme-matched figures for the proposal deck from real results/ data.
Theme: dark navy bg, family-colored horizontal bars, dashed chance line, white labels
(matches the deck's "Probe Performance by Model" panel style).
Outputs PNGs (2x scale) into slides/.
Usage: python3 slides/make_slide_figures.py   (run from repo root)
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG      = "#0e1420"   # panel background (matches card interiors)
FG      = "#e8ecf3"   # near-white text
MUT     = "#8b95a5"   # muted gray
GRID    = "#26303f"
GREEN   = "#2ecc71"
BLUE    = "#3b9dd9"
ORANGE  = "#f0a02f"
PINK    = "#e84393"
RED     = "#e3344a"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": FG, "axes.edgecolor": GRID, "axes.labelcolor": MUT,
    "xtick.color": MUT, "ytick.color": FG, "font.size": 11,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica Neue", "DejaVu Sans"],
})

OUT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(OUT), "results")

# ---------------------------------------------------------------- fig 1: 7-model probe AUROC
models = [   # (display, results-file key, family color, era note)
    ("Qwen-2.5-7B",                "qwen",     BLUE,   "2024"),
    ("Gemma-4-12B",                "gemma4",   GREEN,  "2026"),
    ("Llama-3.1-8B",               "llama",    ORANGE, "2024"),
    ("Qwen3-8B",                   "qwen3",    BLUE,   "2025"),
    ("DeepSeek-R1-Distill-7B",     "deepseek", PINK,   "2025"),
    ("Gemma-2-9B",                 "gemma",    GREEN,  "2024"),
    ("DeepSeek-R1-0528-8B",        "dsr0528",  PINK,   "2026"),
]
held, surf, perms = [], [], []
for _, k, _, _ in models:
    d = json.load(open(os.path.join(RES, f"synth_{k}.json")))
    held.append(d["wb_heldout_auroc"]); surf.append(d["black_box"]["surface_auroc"])
    perms.append(d["wb_perm_p"])

fig, ax = plt.subplots(figsize=(7.6, 4.4), dpi=200)
ys = range(len(models))[::-1]
for y, (name, _, c, era), h, s, p in zip(ys, models, held, surf, perms):
    ax.barh(y, h, height=0.62, color=c, alpha=0.92, zorder=3)
    ax.plot([s], [y], marker="D", color=FG, ms=5, zorder=4)           # surface baseline marker
    ax.text(h + 0.012, y, f"{h:.2f}", va="center", color=FG, fontweight="bold", fontsize=11)
    ax.text(-0.015, y, f"{name}  ({era})", va="center", ha="right", color=FG, fontsize=10.5)
ax.axvline(0.5, color=MUT, ls="--", lw=1.2, zorder=2)
ax.text(0.502, len(models) - 0.25, "chance", color=MUT, fontsize=9)
ax.set_xlim(0.0, 0.95); ax.set_ylim(-0.7, len(models) - 0.3)
ax.set_yticks([]); ax.set_xticks([0.5, 0.6, 0.7, 0.8, 0.9])
ax.spines[["top", "right", "left"]].set_visible(False)
ax.set_xlabel("Held-out AUROC (post-hoc vs genuine)")
ax.set_title("Internal probe, 7 models / 3 families (2024–2026) — all permutation-significant",
             color=FG, fontsize=12, fontweight="bold", loc="left", pad=14)
ax.text(0.0, -0.16, "White diamonds = surface-feature (black-box) baseline — the gap to the bar is the internal signal.  "
        "Perm p = 0.005 (5 models), 0.020, 0.025.",
        transform=ax.transAxes, color=MUT, fontsize=8.6)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_probe_by_model.png"), bbox_inches="tight")
print("fig_probe_by_model.png")

# ------------------------------------------------- fig 2: depth mismatch (real vs synthetic), Llama
synth = json.load(open(os.path.join(RES, "synth_llama.json")))["per_layer_cv_auroc"]
fcp   = json.load(open(os.path.join(RES, "faithcot_perlayer.json")))["llama"]
fig, ax = plt.subplots(figsize=(7.6, 4.2), dpi=200)
ax.plot(range(len(synth)), synth, color=BLUE, lw=2.4, label="Synthetic (prompted answer-first)")
ax.plot(range(len(fcp)), fcp, color=RED, lw=2.4, label="Real (human-annotated post-hoc)")
sb, fb = max(range(len(synth)), key=lambda i: synth[i]), max(range(len(fcp)), key=lambda i: fcp[i])
ax.scatter([sb], [synth[sb]], color=BLUE, s=46, zorder=5)
ax.scatter([fb], [fcp[fb]], color=RED, s=46, zorder=5)
ax.annotate(f"peaks EARLY (L{sb})", (sb, synth[sb]), xytext=(sb + 1.5, synth[sb] + 0.045),
            color=BLUE, fontsize=10.5, fontweight="bold")
ax.annotate(f"peaks LATE (L{fb})", (fb, fcp[fb]), xytext=(fb - 11.5, fcp[fb] + 0.05),
            color=RED, fontsize=10.5, fontweight="bold")
ax.axhline(0.5, color=MUT, ls="--", lw=1.2)
ax.text(0.4, 0.505, "chance", color=MUT, fontsize=9)
ax.set_xlabel("Layer (Llama-3.1-8B)"); ax.set_ylabel("Probe CV AUROC")
ax.set_ylim(0.35, 0.88); ax.grid(color=GRID, lw=0.6, alpha=0.6)
ax.spines[["top", "right"]].set_visible(False)
leg = ax.legend(loc="lower right", frameon=False, fontsize=10)
for t in leg.get_texts(): t.set_color(FG)
ax.set_title("Same behavior, different circuits: synthetic vs organic post-hoc live at different depths",
             color=FG, fontsize=12, fontweight="bold", loc="left", pad=12)
ax.text(0.0, -0.185, "Cross-distribution transfer ≈ chance even at the best of all 32 layers "
        "(Llama 0.55 / Qwen 0.60; layer-mean at chance).",
        transform=ax.transAxes, color=MUT, fontsize=8.6)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_layer_depth_mismatch.png"), bbox_inches="tight")
print("fig_layer_depth_mismatch.png")

# ---------------------------------------------------------- fig 3: the frontier (all signals chance)
sig = [("Answer-tracing", 0.545, 0.611), ("NLI step-support", 0.514, None),
       ("Premise-DAG structure", 0.490, None), ("Counterfactual interventions", 0.485, None)]
fig, ax = plt.subplots(figsize=(7.6, 3.6), dpi=200)
ys = range(len(sig))[::-1]
for y, (name, v, ci_hi) in zip(ys, sig):
    ax.barh(y, v, height=0.58, color=MUT, alpha=0.75, zorder=3)
    ax.text(max(v, ci_hi or 0) + 0.022, y, f"{v:.2f}", va="center", color=FG, fontweight="bold")
    ax.text(-0.015, y, name, va="center", ha="right", color=FG, fontsize=10.5)
# CI whiskers only where we have exact bounds (answer-tracing)
ax.plot([0.468, 0.611], [ys[0], ys[0]], color=FG, lw=1.4, zorder=4)
for x in (0.468, 0.611): ax.plot([x, x], [ys[0]-0.14, ys[0]+0.14], color=FG, lw=1.4, zorder=4)
ax.axvline(0.5, color=RED, ls="--", lw=1.6, zorder=2)
ax.text(0.507, -0.52, "chance", color=RED, fontsize=9.5, va="top")
ax.set_ylim(-0.75, len(sig) - 0.35)
ax.set_xlim(0.0, 0.75); ax.set_yticks([]); ax.set_xticks([0.25, 0.5, 0.75])
ax.spines[["top", "right", "left"]].set_visible(False)
ax.set_xlabel("AUROC, faithful vs post-hoc — correct answers only (ft1 vs ft2, n=270)")
ax.set_title("The frontier: control for correctness and every black-box signal goes blind",
             color=FG, fontsize=12, fontweight="bold", loc="left", pad=12)
ax.text(0.0, -0.26, "Every bootstrap 95% CI includes 0.5 (whiskers shown for answer-tracing). "
        "On the full benchmark, answer correctness ALONE scores 0.697 — the strongest signal.",
        transform=ax.transAxes, color=MUT, fontsize=8.6)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_frontier_chance.png"), bbox_inches="tight")
print("fig_frontier_chance.png")
