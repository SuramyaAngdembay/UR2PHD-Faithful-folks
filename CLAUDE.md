# CLAUDE.md — UR2PHD-Faithful-folks

Orientation for any agent/session working in this repo. Read this first, then the linked docs.

## What this project is
Undergraduate research project (team **"ChainTrackers"** / "Faithful folks"; Suramya Raj Angdembay +
Dikshant Aryal; advisor Dr. Nick Rahimi; Summer 2026), prepping toward a publishable paper.

**Topic: Premise-Grounded Detection of Unfaithful Chain-of-Thought (CoT) Reasoning.** Combine
**PARC** (premise DAG over CoT + premise-constrained LLM judge, ICML 2025) with **FaithCoT-Bench**
(instance-level CoT *faithfulness* benchmark, ICLR 2026), adding graph-targeted counterfactual
interventions and evidence grounding. Goal = **detect & localize** unfaithful reasoning (not a new
reasoning model).

## File map
- [README.md](README.md) — topic summary, core idea, research question.
- [research-direction.md](research-direction.md) — motivation, method (stages A–E), hypotheses.
- [experimental-plan.md](experimental-plan.md) — datasets, conditions, metrics, MVP, work sequence.
- [literature-map.md](literature-map.md) — original (thin) lit map. **Superseded in depth by:**
- [related-work-and-positioning.md](related-work-and-positioning.md) — **the canonical reference**:
  verified related work (tiered), novelty verdict, ranked extensions, tightened datasets, per-stage
  approaches, CRAG verdict, reviewer objections, BibTeX to-add list.
- [paper-positioning-blackboxnlp.md](paper-positioning-blackboxnlp.md) — **target venue
  (BlackboxNLP @ EMNLP 2026) + paper framing**: contributions C1–C3, abstract sketch, positioning
  vs prior work, experiment status, reviewer objections.
- [overleaf-proposal/](overleaf-proposal/) — LaTeX proposal (`main.tex`, `ur2phd.bib`).
- [scripts/](scripts/) — Aquaman env setup + all experiment harnesses (run on the GPU box).
- [results/](results/) — raw experiment outputs (intervention v1/v2, rigorous feature table, white-box probe results).
- [notes/](notes/) — dated session logs + the findings log (see below).

## Current state (as of 2026-06-25)
**The premise-DAG / intervention thesis was empirically tested and BURIED.** On FaithCoT-Bench
(truthfulqa+logiqa, llama+qwen, human `unfaithfulness` label), four orthogonal method families all fail
to beat or augment answer-tracing (`soft_faithfulness`, AUROC ≈ 0.73):
- premise-DAG structure ≈ chance (AUROC 0.51–0.59);
- targeted counterfactual interventions: v1 null, v2 weak (g 0.56–0.61) and dominated by `soft`;
- per-step NLI support: weak (≤0.58), adds ~nothing to `soft` (local entailment ≠ faithfulness).

**The real open frontier** (annotated `faithful_type` split): detecting **post-hoc rationalization on
*correct* answers (ft1 vs ft2)** — every black-box signal is at chance (≈0.51) there. Methodological
finding: `soft_faithfulness` *anti-correlates* with human faithfulness (higher for unfaithful traces).

**Pivot:** instance-level detection is saturated by answer-tracing → stop method-hunting. Consolidate into
an **analysis / negative-results paper** (negative results + the post-hoc-on-correct frontier + the metric
polarity inversion), with **white-box/mechanistic** detection of the ft1v2 cases as the evidence-motivated
forward experiment. (The 2026-06-18 lit/novelty positioning remains valid as background — see related-work doc.)

**Hardened (2026-06-26):** scaled to **4 domains × 4 models** (n=634 complete-feature / 1304 traces) with
**bootstrap 95% CIs** — F1 (post-hoc-on-correct frontier: every signal's CI includes 0.5, n=270) and F2
(metric inversion: +0.139 [+0.096, +0.182]) are now **statistically backed**; correctness strongest (0.697\*),
DAG structure ns (except weakly on math). **Target venue: BlackboxNLP @ EMNLP 2026** — framing in
`paper-positioning-blackboxnlp.md`.

**White-box pilot (2026-06-29):** an internal linear probe detects post-hoc-on-correct (ft1v2) in
**Llama-3.1-8B (AUROC 0.71, permutation p=0.01, layers 16–31)** but **not significantly in Qwen
(0.62, p=0.32)** — so C1 becomes a black-box-vs-internals contrast (behaviorally blind, internally
(partially) decodable in *some* models). Also: LLM extractor validated at **0.82 recall** vs PERL
gold (licenses the v2 null); GRACE NLI replicates the weak-NLI finding (preliminary, underpowered).

**White-box firm-up (2026-07-02):** items (a),(b),(d),(e) done — Llama **held-out AUROC 0.70 / F1 0.70**
(25×70/30), cross-domain 0.60–0.71 (leave-one-domain-out), signal ~**linear** (MLP no gain), perm p=0.03;
Qwen weak (held-out 0.58); mechanism **model-dependent** (a2 pre-CoT answer-commitment sig in Qwen p=0.044
uncorrected, null in Llama). **Item (c) causal steering (2026-07-02): weak/suggestive** — post-hoc
direction flips answers ~2–3× more than a random direction at +6σ (0.22 vs 0.08) and lowers confidence
more → functionally active, not a passive correlate, but modest (large-α only, n=51, indirect readout).
**All white-box firm-up items a–e now done.** Caveats: small n (144/126),
(a)-sweep PCA-once inflation (use strict numbers), a2 uncorrected.

**Synthetic-construction generalization (2026-07-04):** built matched **genuine (reason-first,
keep-if-correct) vs post-hoc (answer-first, rationalize gold)** CoT on **AQuA+GSM8K** for **Llama-3.1-8B
(229 pairs) + Qwen-2.5-7B (277 pairs)** — the post-hoc-on-correct frontier with ground-truth construction
labels at scale; **later scaled to 4 models / 3 families** (+Qwen3-8B no-think 175 pairs, +DeepSeek-R1-
Distill-7B 251 pairs, 2026-07-05). **(i) White-box probe permutation-significant (p=0.005) in ALL FOUR**
(held-out Qwen2.5 **0.81** / Llama **0.74** / Qwen3 **0.72** / DeepSeek **0.62**), generalizing
**across AQuA↔GSM8K** (0.52–0.73); effect **model-dependent** (weakest in reasoning-distilled DeepSeek).
Surface baseline ≈0.54 for 3 models (Llama 0.64 caveat) ⇒ signal is genuinely internal. The earlier Qwen
null was largely FaithCoT label-noise/small-n; C1's "internally decodable" leg now holds cross-family on
clean labels. **(ii) The FaithCoT(real)↔synthetic BRIDGE FAILS** (Llama/Qwen2.5 only — FaithCoT has no
real traces for the newer models) — synthetic post-hoc peaks
**early** (L9/L10), real ft1v2 peaks **late** (L29/L22); cross-distribution transfer is **~chance even
best-of-32-layers and domain-matched** (Llama FC→synth best 0.55 mean 0.48; Qwen 0.60/0.50). ⇒ **synthetic
answer-first is NOT a representational proxy for organic post-hoc** — a publishable methodological caution,
and the honest answer to "how do the two buckets connect" (they don't, internally). Caveat: Llama synthetic
**surface-feature baseline 0.639** (partial surface tell); soft_faithfulness uncomputable on numeric-option
AQuA; Gemma-2-9b blocked on HF gated access. **Disk constraint resolved (2026-07-05): HF cache moved to
`/data` (5.6 TB free) via symlink — no more download-run-delete.**

## Conventions
- Citations must be verified before going into a submission; see the provenance caveat in the latest
  notes file. Prefer peer-reviewed venues; mark unrefereed preprints as such (e.g. Corrective-RAG).
- Add new findings as dated files in `notes/`; keep `related-work-and-positioning.md` as the living
  canonical reference; keep this CLAUDE.md's "Current state" section current.

## Findings log (chronological)
1. `notes/2026-06-18-litreview-and-positioning-session.md` — lit review + novelty positioning.
2. `notes/2026-06-25-finding-human-label-baseline.md` — soft/hard = answer-tracing AUC; human
   `unfaithfulness` is the real target; honest baselines (soft ≈0.73, correctness ≈0.76).
3. `notes/2026-06-25-exp1-targeted-interventions-spec.md` — Exp-1 design.
4. `notes/2026-06-25-finding-intervention-v1-null.md` — v1 intervention null (heuristic targets).
5. `notes/2026-06-25-finding-intervention-v2-bury.md` — decision-gate: DAG/intervention buried.
6. `notes/2026-06-25-finding-nli-and-frontier.md` — NLI support null; post-hoc-on-correct frontier.
7. `notes/2026-06-26-rigorous-scaled-results.md` — scaled 4×4 + bootstrap CIs; F1 & F2 significant.
8. `notes/2026-06-29-validation-grace-and-extraction.md` — LLM extractor 0.82 recall vs PERL; GRACE NLI ~chance (preliminary).
9. `notes/2026-06-29-whitebox-pilot.md` — internal probe: Llama ft1v2 AUROC 0.71 (p=0.01), Qwen n.s. (p=0.32).
10. `notes/2026-07-02-whitebox-method-abde.md` — white-box firm-up (a,b,d,e): Llama held-out 0.70/F1 0.70, cross-domain, ~linear, model-dependent.
11. `notes/2026-07-02-whitebox-causal-c.md` — item (c) causal steering: weak/suggestive (post-hoc dir perturbs answers ~2–3× > random at +6σ; functionally active, modest).
12. `notes/2026-07-04-synthetic-construction-generalization.md` — synthetic genuine-vs-post-hoc on AQuA+GSM8K: WB probe strong in BOTH models (held-out Llama 0.74 / Qwen 0.81, p=0.005), generalizes across math datasets; but FaithCoT↔synthetic bridge FAILS (~chance, depth-mismatched) ⇒ synthetic post-hoc ≠ real proxy.

## Open next steps (BlackboxNLP-targeted — see paper-positioning-blackboxnlp.md)
DONE: 4×4 + CIs (F1/F2 sig); LLM-extractor validation (0.82 recall); GRACE NLI (preliminary); white-box pilot + firm-up a/b/d/e (Llama held-out 0.70, Qwen weak); **synthetic-construction generalization** (WB strong in both models on clean labels; **bridge to real post-hoc fails → new methodological caution**).
(a) **write the paper** (C1 frontier + black-box-vs-internals incl. Llama held-out 0.70 + synthetic 2-model WB 0.74/0.81 + C2 metric inversion + C3 rigorous negatives + **C4 synthetic-proxy caution**) into `overleaf-proposal/`;
(b) **full GRACE eval set** (437 traces) for a conclusive 2nd-benchmark claim (email authors / await release);
(c) *(optional)* extra models on the synthetic study (DeepSeek-R1-Distill / Qwen3-8B / Gemma) via download-run-delete — disk-gated (34 GB free).
