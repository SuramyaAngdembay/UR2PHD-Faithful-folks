# Session log — 2026-06-18: literature sweep, novelty positioning, dataset/approach/CRAG

*This is a distilled session record for future context agents. Deep detail lives in
[../related-work-and-positioning.md](../related-work-and-positioning.md). This file = what was
asked, what we concluded, what was decided, and what to do next.*

## What was asked
Take the current proposal (PARC × FaithCoT mix: "DAG + LLM-as-judge as a good indicator for math
reasoning" + introduce faithfulness à la FaithCoT) and: identify its potential / extensions; survey
peer-reviewed work (OpenReview, EMNLP, ICML, ICLR, AAAI, JMLR, TMLR) for prior/similar work; tighten
the datasets; recommend approaches; and judge whether **CRAG** is feasible/good here.

## How it was done (process note)
- Ran a multi-agent literature workflow: 4 agents grounded the foundational papers
  (PARC, FaithCoT-Bench, Lyu Faithful-CoT, both CRAGs) + 10 agents surveyed subtopics → **75 unique
  verified papers**. Then adversarial similarity-verification + synthesis phases were scheduled.
- **The workflow hit the rolling usage cap mid-run** (26 agents, ~669K tokens): the Verify + Synthesize
  phases failed. **No data lost** — the 14 ground/survey agents' structured outputs were recovered from
  the workflow `journal.jsonl`, and the synthesis was done directly. The 7 highest-overlap "novelty
  threat" papers were then **fetched and read individually** to confirm they are real (several had
  future-dated arXiv IDs that needed checking). All 7 confirmed real.

## Key conclusions
1. **Novelty verdict:** the *exact* union (premise DAG → premise-constrained multi-signal verification →
   **graph-targeted** counterfactual interventions → instance+step **faithfulness** detection on
   FaithCoT-Bench) is **not** published as one paper, but **every stage has strong recent prior art**.
   The generic framing won't survive review. Defensible white space:
   - **(i)** premise-DAG-*guided* intervention *selection* (nobody does this on free-form CoT);
   - **(ii)** evidence+NLI grounding inside the DAG for the **knowledge-intensive** regime (FaithCoT's
     documented weak spot);
   - **(iii)** "accumulation faithfulness" via DFS over the DAG (PARC's idea, reframed correctness→faithfulness).
2. **Biggest threats (verified real, must cite + differentiate):**
   - **GoV** (arXiv 2506.12509) and **VeriCoT** (arXiv 2511.04662) = structural twins (DAG + per-step
     constrained verification; VeriCoT adds FOL + premise grounding + localization). Neither does
     counterfactuals/evidence/faithfulness.
   - **StepGap** (2605.24733) = stage-C-with-evidence twin (NLI+LLM+evidence, multi-hop) but tiny eval, no DAG.
   - **Breaking the Chain** (2603.16475) = targeted causal interventions, but on **schema-guided
     deterministic structures**, not a premise DAG over free-form CoT.
   - **FaithCoT-Bench already benchmarks counterfactual + LLM-judge detectors and ships step-level evidence
     labels** → "instance+step faithfulness detection" is not itself novel; only the *method* + an
     *empirical win* are.
   - Corrected over-flags: **"From Chains to DAGs"** (2601.17593) is *white-box probing* (→ optional
     extension, not core); **"When the Chain Breaks" = ReasonDiag** is an *interactive viz tool at
     **EuroVis 2026*** (different contribution type).
3. **Datasets:** keep FaithCoT-Bench/FINE-CoT primary (4 domains = LogiQA, TruthfulQA, AQuA, HLE-Bio).
   Add GRACE + RFEval (faithfulness), ProcessBench + DeltaBench + REVEAL (localization baselines),
   FOLIO + StrategyQA (gold premises for clean counterfactuals). Drop plain GSM8K-as-faithfulness; use
   PARC's released **PERL** instead. Report synthetic vs real errors separately (synthetic are artificially easy).
4. **Approaches:** two-channel verification (factual: NLI/AttrScore/FActScore + retrieval gate; logical:
   premise-judge + symbolic VeriCoT/LINC/SatLM); CCT distributional answer-shift for interventions;
   cross-model judging for bias hygiene.
5. **CRAG verdict:** **not core.** Corrective-RAG (method, 2401.15884) — adopt only the retrieval-quality
   *gate* idea, cheaply, and cite **Self-RAG (ICLR 2024)** as the peer-reviewed anchor (Corrective-RAG is a
   withdrawn preprint). CRAG benchmark (NeurIPS 2024 D&B, 2406.04744) — has **no faithfulness labels**;
   optional knowledge-intensive substrate / mock retrieval only, Phase-3 add-on.

## Decisions
- Proposal contribution **re-scoped** from "premise DAG + faithfulness" (too generic) to the narrow white
  space (i)–(iii) above, positioned explicitly against GoV / VeriCoT / Breaking-the-Chain / FaithCoT-Bench.
- This Ur2Phd folder is being made a standalone git repo; GitHub repo name **UR2PHD-Faithful-folks** (private).

## Open next steps (offered, not yet done)
- (a) Draft sharpened novelty/related-work paragraphs into `overleaf-proposal/main.tex` + add BibTeX entries.
- (b) Refresh `literature-map.md` with the verified tiers from `related-work-and-positioning.md`.
- (c) Spec the MVP experiment: graph-targeted vs random interventions on one FaithCoT-Bench
  knowledge-intensive subset (TruthfulQA or HLE-Bio), reusing PARC code + PERL + FaithCoT-Bench harness.

## Provenance / caveats
- Foundational papers + the 7 top-threat papers were individually verified (titles/authors/abstracts).
- Remaining ~68 survey papers were marked verified by web-search-grounded agents instructed not to
  fabricate; the famous classics (PRM800K, Lanham, Turpin, Self-RAG, FEVER, FActScore, SummaC, REVEAL,
  ProcessBench, etc.) are well-known and real. Treat any *not* in the verified-7 list as "high-confidence
  but re-check the exact venue/ID before citing in a submission."
