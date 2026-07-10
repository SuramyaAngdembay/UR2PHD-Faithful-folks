# Deck updates — slides 4+ (slides 1–3 untouched, already recorded)

Figures in this folder are theme-matched (dark navy bg `#0e1420`, family colors, dashed
chance lines) and generated from `results/*.json` by `make_slide_figures.py` — real numbers only.
Drop them into the green-bordered right-panel style used on the current slides.

---

## NEW SLIDE (insert after slide 3, before "Looking Inside the Black Box")
**Kicker (red):** The Diagnosis
**Title:** Why Black-Box Fails: The Accuracy Confound
**Subtitle (gray):** Most "unfaithfulness detection" is disguised accuracy prediction

**Left card — "The Confound" (blue heading):**
- **Correctness dominates:** On the full benchmark, answer correctness ALONE is the strongest
  "unfaithfulness" signal — **AUROC 0.697**, beating every purpose-built detector.
- **The controlled test:** So we control for it — only traces where the model is **correct**,
  and ask: faithful reasoning (ft1) vs post-hoc rationalization (ft2)? (n=270, human-annotated)
- **The frontier:** With correctness controlled, **every black-box signal collapses to chance**
  (all bootstrap 95% CIs include 0.5).

**Right panel (green border):** `fig_frontier_chance.png`
Panel title: THE FRONTIER: ALL SIGNALS AT CHANCE

*(Why add: this is contribution C4 of the paper and the logical hinge between recorded slide 3
and the white-box pivot — currently the deck never says WHY black-box fails.)*

---

## SLIDE 4 — "Looking Inside the Black Box" (replace left-card bullets)
Keep title/kicker/layout and the black-box→cube visual. Replace the three bullets:

- **Internal Activations:** Since black-box behavior is blind on this frontier, we probe the
  model's hidden states directly (white-box) — linear probes, PCA-50, with selection-corrected
  permutation tests. *(A sparse Lasso variant is planned for neuron-level localization.)*
- **The Finding:** On the human-annotated traces, the probe separates genuine from post-hoc
  reasoning in **Llama-3.1-8B: held-out AUROC 0.70**, generalizing across domains (0.60–0.71
  leave-one-domain-out). In **Qwen-2.5-7B it is weak** — the signal is **model-dependent**, not
  universal. *(honest asymmetry → motivates the scaling study, next slide)*
- **Causally active (early evidence):** Steering activations along the probe direction flips
  answers **2–3× more than a random direction** (0.22 vs 0.08 at +6σ) — the direction is
  functionally active, not a passive correlate. *(weak/suggestive; deeper causal tests planned)*

> Cut: "The model's internal state knows it is rationalizing! Activations cleanly separate…" —
> overclaims what 0.70/weak-Qwen supports, and "sparse Lasso on 4096-dim" isn't the headline method.

---

## SLIDE 5 — "A Universal Phenomenon" (retitle + REPLACE CHART — current one is wrong)
**Title:** A Consistent — but Model-Dependent — Signal
**Subtitle:** Internal decodability across 7 models, 3 families, 2024→2026

⚠️ **The current bar chart is fabricated** (LLAMA-3 70B / QWEN-1.5 72B / DEEPSEEK-V2 were never
run; Gemma-4's value is inverted — it's our 2nd BEST at 0.80, not 0.56).
**Replace with:** `fig_probe_by_model.png`

**Left card bullets:**
- ✓ Built a **ground-truth synthetic benchmark**: matched pairs where the same model either
  solves a problem (reason-first, kept only if correct) or justifies a **handed** gold answer
  (answer-first) — same correct answer, only the causal role of reasoning differs.
- ✓ **7 models, 3 families + reasoning distills, 2024→2026** (incl. Gemma-4-12B, run 4-bit
  sharded across two 8 GB GPUs).
- ✓ **All 7 permutation-significant** (held-out AUROC 0.56–0.81, p ≤ 0.025) — consistent, but
  **model-dependent**: strong in instruct models, weaker in reasoning-distills.
- ✓ **It's internal, not style:** a surface-feature (black-box) classifier reads ≈0.47–0.55 for
  5/7 models — the probe beats it everywhere (white diamonds in the chart).
- ✓ Within one family: **Gemma-2 0.60 → Gemma-4 0.80** — newer/larger = more decodable.

> Cut: "holds universally… proving it is not a structural fluke" → "consistently significant,
> model-dependent in strength". (Universality is falsified by our own DeepSeek/Gemma-2 numbers.)

---

## SLIDE 6 — "A Warning to the Community" (fix one bullet + optional real-data figure)
Keep title, kicker, left-card structure. Two changes:

- ❌→ Replace "**Zero Transferability**" bullet with:
  "**Near-Chance Transfer:** Probes trained on synthetic post-hoc do not transfer to real
  annotated post-hoc (or vice versa) — **best-of-all-32-layers ≤ 0.60, layer-average at
  chance** — and the two signals live at different depths (early L9/L10 vs late L22/L29)."
- The right-panel schematic (L9 vs L29 spikes) is directionally correct — keep it, or upgrade
  to the real measured curves: `fig_layer_depth_mismatch.png` (same story, actual data,
  Llama-3.1-8B).

---

## NEW SLIDE (insert before the summary slide)
**Kicker (red):** The Proposal
**Title:** Proposed Work & Timeline
**Subtitle (gray):** From validated findings to a BlackboxNLP @ EMNLP 2026 submission

**Left card — "Done → Doing → Next" (blue heading):**
- ✅ **Done:** black-box audit (4 domains × 4 models, bootstrap CIs) · frontier localization ·
  metric inversion (+0.139 [+0.096, +0.182]) · white-box probe + causal steering ·
  7-model synthetic scaling · bridge test · full paper draft (`main.tex`)
- 🔄 **Now:** paper polish → advisor review (Dr. Rahimi) → port to ACL/BlackboxNLP template
  (CFP expected ~Aug 2026)
- 🔭 **Proposed next:**
  1. **Second benchmark** — GRACE full eval set (437 traces) on release (authors contacted)
  2. **Stronger causal tests** — activation patching/ablation beyond steering
  3. **Organic unfaithfulness data** — the bridge failure shows synthetic proxies don't
     transfer; collecting naturally occurring post-hoc traces is the field's real bottleneck
  4. **Scale-up** — Gemma-4-31B / DeepSeek-V4 class models (needs ≥16 GB GPUs)

**Right panel:** simple 4-row timeline (Jul: polish → Aug: submit BlackboxNLP → Fall: GRACE +
causal follow-ups → beyond: organic data). Text rows in the card style are fine if a graphic is
too fiddly.

*(Why add: this is a PROPOSAL deck — reviewers expect a plan, risks, and venue, not only results.)*

---

## SLIDE 7 — "Summary & Next Steps" (fix two bullets)
- 🧠 Replace "White-Box Breakthrough: … via sparse linear probing across **all major LLM
  families**" with: "**White-Box Contrast:** post-hoc rationalization is behaviorally invisible
  yet **linearly decodable from activations** — in all 7 models tested, with model-dependent
  strength."
- 🚀 Replace the generic next-steps bullet with: "**Next:** BlackboxNLP @ EMNLP 2026 submission ·
  GRACE second benchmark on release · deeper causal validation."
- QR panel: repo is **private** — caption it "(public at submission)" or flip visibility before
  presenting.

---

## Numbers safe to quote (all in `results/` + paper)
| claim | number |
|---|---|
| Correctness confound (full benchmark) | AUROC **0.697** — strongest single signal |
| Frontier (ft1 vs ft2, n=270) | soft 0.545 [0.468, 0.611] · NLI 0.514 · DAG 0.490 · interventions 0.485 — all CIs ∋ 0.5 |
| Metric inversion | **+0.139** [+0.096, +0.182] (unfaithful traces score HIGHER) |
| White-box, real labels (Llama) | held-out **0.70** / F1 0.70 · LODO 0.60–0.71 · perm p=0.03 |
| White-box, real labels (Qwen) | held-out 0.58, n.s. → model-dependent |
| Causal steering | flips 0.22 vs random 0.08 at +6σ (n=51, weak/suggestive) |
| Synthetic 7-model | 0.81 / 0.80 / 0.74 / 0.72 / 0.62 / 0.60 / 0.56 — all perm p ≤ 0.025 |
| Surface baselines | ≈0.47–0.55 (5/7); Llama 0.64, Gemma-4 0.67 (partial tells) |
| Bridge | best-of-layers ≤0.60, means at chance; depths L9/L10 vs L22/L29 |
