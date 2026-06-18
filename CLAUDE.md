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
- [overleaf-proposal/](overleaf-proposal/) — LaTeX proposal (`main.tex`, `ur2phd.bib`).
- [notes/](notes/) — dated session logs. Newest: `notes/2026-06-18-litreview-and-positioning-session.md`.

## Current state (as of 2026-06-18)
- Proposal **re-scoped**: the generic "premise DAG + faithfulness" framing is largely anticipated by
  recent work (GoV 2506.12509, VeriCoT 2511.04662, Breaking-the-Chain 2603.16475, StepGap 2605.24733;
  FaithCoT-Bench already benchmarks counterfactual + judge detectors). The **defensible novelty** is
  (i) premise-DAG-*guided* intervention *selection*, (ii) evidence+NLI grounding in the DAG for
  knowledge-intensive faithfulness, (iii) DFS "accumulation faithfulness" localization.
- **CRAG**: not core — adopt only Corrective-RAG's retrieval-*gate* idea (cite Self-RAG); CRAG benchmark
  is an optional substrate (no faithfulness labels).

## Conventions
- Citations must be verified before going into a submission; see the provenance caveat in the latest
  notes file. Prefer peer-reviewed venues; mark unrefereed preprints as such (e.g. Corrective-RAG).
- Add new findings as dated files in `notes/`; keep `related-work-and-positioning.md` as the living
  canonical reference; keep this CLAUDE.md's "Current state" section current.

## Open next steps
(a) draft sharpened novelty/related-work into `overleaf-proposal/main.tex` + BibTeX;
(b) refresh `literature-map.md` with verified tiers;
(c) spec the MVP experiment (graph-targeted vs random interventions on a FaithCoT-Bench
knowledge-intensive subset, reusing PARC code + PERL + the FaithCoT-Bench harness).
