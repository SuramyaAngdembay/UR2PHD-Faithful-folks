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
- [results/](results/) — raw per-trace experiment outputs (intervention v1/v2).
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

## Open next steps (BlackboxNLP-targeted — see paper-positioning-blackboxnlp.md)
(a) validate the **LLM** extractor vs PERL gold (licenses the v2 intervention claim; heuristic was F1 0.57);
(b) **GRACE** step-level NLI replication (preliminary 2nd benchmark; 40 examples public);
(c) **white-box pilot** on ft1v2 — highest upside (flips C1 from a null to "the signal is inside");
(d) write the paper (C1 frontier + C2 metric inversion + C3 rigorous negatives) into `overleaf-proposal/`.
