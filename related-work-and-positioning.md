# Related Work, Novelty Positioning & Extensions

*Compiled from a multi-agent literature sweep (OpenReview / arXiv / ACL Anthology /
PMLR), June 2026. Every paper flagged "verified" was confirmed to exist via a real
search result or fetched page. The seven highest-overlap "novelty-threat" papers were
additionally fetched and read directly (abstracts confirmed) — see the ✅ marks.*

---

## 0. TL;DR verdict

- **The exact union the proposal claims — (PARC-style premise DAG) → (premise-constrained
  multi-signal step verification) → (graph-*targeted* counterfactual interventions) →
  (instance + step-level *faithfulness* detection on FaithCoT-Bench) — does not exist as a
  single published paper.** The integrated pipeline is still novel.
- **But every individual component now has strong, recent (2025–2026), often concurrent
  prior art, much of it at top venues.** Several papers independently do 2–3 of the stages.
  So the generic framing ("build a premise DAG and verify steps for faithfulness") is
  **largely anticipated** and will not survive review on its own.
- **The defensible, narrow-but-real white space is the *intervention-selection mechanism* and
  the *evidence-grounded knowledge-intensive extension*:** nobody uses a premise-dependency
  DAG to *choose which premises to counterfactually perturb*, and nobody integrates retrieved
  evidence + NLI into premise-DAG verification specifically to fix the knowledge-intensive
  weakness FaithCoT-Bench documents. The contribution must be sharpened to those, plus a
  head-to-head empirical **win over FaithCoT-Bench's existing detectors**.
- **CRAG:** feasible and conceptually aligned, but **not core**. Adopt Corrective-RAG's
  *retrieval-quality gate idea* cheaply (cite Self-RAG as the peer-reviewed anchor); use the
  *CRAG benchmark* only as an optional knowledge-intensive substrate (it has no faithfulness
  labels). Do **not** build the full Corrective-RAG pipeline for v1.

---

## 1. "Has someone done this?" — component-by-component novelty map

| Proposal stage | Strongest prior art (verified) | Status |
|---|---|---|
| **A. Decompose CoT into atomic steps** | PARC (ICML'25); ReasoningFlow (ArgMining'25, *same authors*); Natural Program / Deductive Verification (NeurIPS'23) | **Solved / standard** |
| **B. CoT → premise DAG** | PARC (ICML'25); ✅ **GoV / Graph-of-Verification** (arXiv 2506.12509); ✅ **VeriCoT** (arXiv 2511.04662) | **Published** — the DAG idea is *not* novel |
| **C. Premise-constrained step verification** | PARC; GoV; VeriCoT (FOL+solver); ✅ **StepGap** (NLI+LLM+evidence, multi-hop); REVEAL (ACL'24); ReCEval (EMNLP'23); Entailer (EMNLP'22) | **Heavily covered**, incl. NLI+evidence variants |
| **D. Counterfactual interventions for faithfulness** | Lanham'23; Turpin'23 (NeurIPS); CCT (ACL'24); ✅ **Breaking the Chain** (2603.16475); Thought Anchors (ICLR'26); Thinking Drafts (2505.13774); RFEval (ICLR'26); FRIT (2509.13334) | Targeted/importance interventions **exist** — but **none select via a premise DAG** |
| **E. Instance + step-level detection / localization** | **FaithCoT-Bench** (ICLR'26, your benchmark); REVEAL (ACL'24); ProcessBench (ACL'25); DeltaBench (ACL'25); ✅ **GRACE** (2606.16151); BIG-Bench Mistake (ACL-F'24) | Target task is **well-defined & contested** |

**The genuinely open niche (defensible novelty):**
1. **Premise-DAG-guided intervention selection** — use graph structure (centrality / out-degree
   / "load-bearingness") to pick *which* premises to perturb, and show this beats *random*
   (Lanham) and *importance-resampling* (Thought Anchors) and *output-level* (RFEval) selection.
   *Breaking the Chain* does targeted causal interventions but on **schema-guided deterministic
   structures** (rubrics/checklists with a known structure→decision function), **not** an
   LLM-built premise graph over free-form CoT — that gap is yours.
2. **Two-channel evidence grounding inside the DAG** — retrieved-evidence + NLI for *factual*
   premises vs symbolic/judge for *inferential* steps, targeted at the **knowledge-intensive**
   regime where FaithCoT-Bench shows all 11 detectors are weak. StepGap does NLI+evidence but
   **no DAG, no counterfactuals, tiny eval (82 Qs)**; REVEAL separates attribution-vs-logic but
   is **linear and a benchmark, not a method**.
3. **"Accumulation/propagation faithfulness"** — PARC's accumulation-error idea (a step locally
   valid but resting on a faulty upstream premise), reframed for *faithfulness* and localized via
   DFS over the DAG. PARC did this for *correctness*; nobody has for faithfulness.

**The biggest threat to the framing:** FaithCoT-Bench **already** benchmarks counterfactual,
logit-based, and LLM-judge detector families **and** ships step-level evidence annotations. So
"we do instance+step-level faithfulness detection" and "we use counterfactual detectors" are
**not** novel contributions — only the *method* (graph-targeted + evidence-grounded) and an
*empirical win* are.

---

## 2. Threat list — must-cite, must-differentiate (tiered)

### Tier 1 — structural twins (cite prominently; frame as "we extend")
- ✅ **PARC** — *Premise-Augmented Reasoning Chains* (Mukherjee et al., ICML 2025, arXiv 2502.02362).
  Your anchor. DAG + premise-constrained LLM judge, +6–16pt error-ID on math. Releases **PERL**
  dataset + code (github.com/SagnikMukherjee/PARC). *Gap you fill:* math-only, judge-only (no NLI/
  symbolic/evidence), **no counterfactuals**, labels step *correctness* not *faithfulness*.
- ✅ **GoV — Graph of Verification** (Fang et al., arXiv 2506.12509, training-free; venue not yet
  confirmed). DAG-structured step verification with adaptive "node-block" granularity; beats
  holistic + decomposition baselines. *Gap:* no counterfactuals, no evidence grounding, correctness
  not faithfulness. **This is the closest structural twin — cite it explicitly.**
- ✅ **VeriCoT** (Feng, Weir, Bostrom et al., AWS/JHU, arXiv 2511.04662). Neuro-symbolic: each CoT
  step → FOL, identify grounding premises (context/commonsense/prior steps), automated solver checks
  validity, flags ungrounded/fallacious steps. *Gap:* logical-validity not faithfulness, **no
  counterfactuals**, no retrieval/NLI for knowledge-intensive, not evaluated as an unfaithfulness
  detector. **Your stage C done with symbolic logic — must benchmark against it.**

### Tier 2 — intervention twins (the stage-D threat)
- ✅ **Breaking the Chain** (Somov et al., arXiv 2603.16475). Causal eval of faithfulness to
  *intermediate structures* in schema-guided pipelines; targeted edits; finds "apparent faithfulness
  is fragile," structures act as "influential context, not stable causal mediators." *Differentiator:*
  deterministic schema structures, **not a premise DAG over free-form CoT**.
- **Thought Anchors** (Bogdan et al., ICLR 2026 submission, arXiv 2506.19143) — which steps causally
  matter, via black-box resampling + attention suppression. *Random resampling, not graph-targeted.*
- **Thinking Drafts** (arXiv 2505.13774) — step-level + holistic faithfulness via importance-targeted
  truncation/replacement.
- **RFEval** (ICLR 2026 poster) — 7,186-instance counterfactual-faithfulness benchmark; **output-level**
  interventions (not premise-targeted) → exactly the gap you exploit.
- **FRIT** (arXiv 2509.13334) — causal-importance interventions to *train* faithfulness (DPO).
  Reusable pair-construction; different goal (training, not detection).
- Foundational: **Lanham et al.** *Measuring Faithfulness in CoT* (2307.13702, Anthropic) — the
  perturbation suite (add mistakes/truncate/paraphrase/filler) you must beat as the *untargeted*
  baseline. **Turpin et al.** *LMs Don't Always Say What They Think* (NeurIPS 2023) — biasing-feature
  test, canonical unfaithfulness definition.

### Tier 3 — evidence / step-verification twins
- ✅ **StepGap** (Ji et al., Pitt, arXiv 2605.24733). Hybrid NLI+LLM, 3 gap types (Contradicted /
  Irrelevant / Missing-Bridge), first-gap localization on multi-hop QA, sF1 72.0. **Small eval (82 Qs,
  181 steps).** Closest stage-C-with-evidence twin; no DAG, no counterfactuals.
- **REVEAL** — *A CoT Is as Strong as Its Weakest Link* (Jacovi et al., ACL 2024, 2402.00559). Per-step
  relevance / attribution-to-evidence / logical-correctness labels in open-domain QA; **finds verifiers
  good at attribution, weak at logic** → motivates your two-channel design. Benchmark, not method.
- ✅ **GRACE** (Pham, Le, Luu, arXiv 2606.16151). Step-level faithfulness-over-context benchmark;
  **GRACE-Inference (deductive) vs GRACE-Grounding (factual)** taxonomy — mirrors your two-channel split.
  Usable dataset + a positioning peer.

### Reframed (NOT core threats — fix in literature-map.md)
- ✅ **"From Chains to DAGs"** (Zhong, He, Mesgarani, Columbia, arXiv 2601.17593) — **white-box probing**
  of whether DAG structure is encoded in hidden states ("Reasoning DAG Probing"). Relevant to your
  *optional white-box extension*, **not** the core method. (Survey overstated this one.)
- ✅ **"When the Chain Breaks" = ReasonDiag** (Chen et al., **EuroVis 2026**, arXiv 2603.21286) —
  *interactive visualization* tool (arc + node-link diagrams) with a fact-check + symbolic error pipeline.
  Human-in-the-loop diagnosis, different contribution type. Cite as "we automate what ReasonDiag does
  interactively."

---

## 3. Highest-upside extensions (ranked by novelty × feasibility for a summer team)

1. **Premise-DAG-guided counterfactual intervention selection** *(the core hook).* Define
   "load-bearing premise" via graph centrality/out-degree; remove/negate/replace it; measure
   **distributional answer shift** (CCT-style, not binary flip). Show targeted ≫ random (Lanham) ≫
   resampling (Thought Anchors) ≫ output-level (RFEval). **This is your single most differentiating
   claim vs Breaking the Chain.** Feasible, clean baselines.
2. **Two-channel grounding for knowledge-intensive faithfulness.** Factual channel (NLI + retrieval +
   AttrScore) vs inferential channel (premise-judge + symbolic), per REVEAL's good-at-attribution /
   weak-at-logic finding. Target the **TruthfulQA / HLE-Bio** subsets where FaithCoT-Bench detectors
   fail. Highest payoff because it attacks the documented weak spot.
3. **Accumulation/propagation faithfulness via DAG traversal.** DFS to localize the *first unfaithful
   premise* and trace propagation downstream. Novel faithfulness framing of PARC's accumulation errors.
4. **Unify the two "faithfulness" definitions.** Conceptual + empirical bridge: use symbolic execution
   (VeriCoT / LINC / SatLM) as a *faithfulness oracle* on the formalizable subset to validate the
   black-box detector — while citing **"Do LLMs Game Formalization?"** (arXiv 2604.19459) as the caveat
   that autoformalization can itself be unfaithful.
5. **Reviewer-proofing controls the field is missing** *(cheap, high credibility).* Control for
   answer-choice bias (**Bentham et al., TMLR 2024**, "unfaithfulness as disguised accuracy"); cross-model
   judging to dodge self-preference (**Panickssery et al., NeurIPS 2024**); separate retrieval failure
   from reasoning failure (Self-RAG / CRAG gate + FEVER's NEI label).
6. **(Stretch) White-box validation.** Test whether black-box DAG load-bearingness correlates with
   internal causal importance — linear probes (From-Chains-to-DAGs; "Do Androids Know…", ACL-F'24),
   computational-graph verification (2510.09312), or step-unlearning (EMNLP 2025). High novelty, higher
   risk → keep optional.
7. **(Stretch) Cross-benchmark generalization** as its own result: train/tune on FaithCoT-Bench, transfer
   to GRACE / REVEAL / DeltaBench (long o1-style traces). Detector brittleness is real → generalization is
   a contribution.

---

## 4. Datasets — tightened plan (layered by annotation type)

> The current plan (FaithCoT-Bench primary; TruthfulQA/HLE-Bio/LogiQA/AQuA; GSM8K supplementary) is
> sound but must be **layered by what each dataset actually annotates** — faithfulness vs step-error
> vs answer-only. Only Tier 1 measures the real target.

### Tier 1 — FAITHFULNESS-labeled (primary eval)
- **FaithCoT-Bench / FINE-CoT** (ICLR 2026) — **KEEP as primary.** Its 4 domains are confirmed
  **LogiQA, TruthfulQA, AQuA, HLE-Bio** (HLE-Bio = biology subset of *Humanity's Last Exam*; your guess
  was right). Metrics: F1 (primary, class-imbalanced), Accuracy, Cohen's κ. *Caveats:* only ~300+
  unfaithful instances, 4 generators, binary instance-level; **localization is evaluated against the
  step-evidence annotations, not the headline F1** — design experiments accordingly.
- **GRACE** (arXiv 2606.16151) — **ADD.** Step-level faithfulness over context, inference-vs-grounding
  taxonomy = your two-channel design; tests generalization.
- **RFEval** (ICLR 2026) — **ADD** as the counterfactual-faithfulness comparison (7,186 instances) to
  benchmark *graph-targeted vs output-level* interventions head-to-head.

### Tier 2 — STEP-ERROR / first-error localization (localization claim + baseline source)
*(these score correctness, not faithfulness — but they're the canonical localization beds & strongest baselines)*
- **ProcessBench** (ACL 2025, 2412.06559) — **ADD.** Canonical first-error-step benchmark; PRM + critic baselines.
- **DeltaBench** (ACL 2025, 2502.19361) — **ADD.** Long o1-style traces → tests long-range premise
  dependencies (where the DAG should shine).
- **REVEAL** (ACL 2024, 2402.00559) — **ADD.** Per-step relevance/attribution/logic in open-domain QA →
  directly tests the retrieval-vs-reasoning two-channel split.
- **PRM800K** (ICLR 2024) / **PRMBench** (ACL 2025) — optional; PRMBench's *prerequisite sensitivity* +
  *deception resistance* dimensions are premise-adjacent and good ablation beds.
- **BIG-Bench Mistake** (Tyen et al., ACL-F 2024) — first-mistake-location; supports "find-error is hard."

### Tier 3 — GROUND-TRUTH premises (build gold DAGs + clean counterfactuals)
- **FOLIO** (EMNLP 2024) — **ADD.** FOL-verified premises = gold premise sets → gold DAGs, symbolic-check
  validation, **clean premise-removal counterfactuals**. Gold for the intervention experiments.
- **StrategyQA** (TACL 2021) — **ADD.** Multi-hop + gold decompositions + per-step Wikipedia evidence →
  seeds knowledge-intensive premise DAGs + evidence counterfactuals.
- **EntailmentBank** (EMNLP 2021) — optional; gold multi-premise entailment trees.

### Knowledge-intensive answer-only (source hard traces + retrieval substrate; NO faithfulness labels)
- **CRAG benchmark** (NeurIPS 2024 D&B) — optional substrate (see §6). HotpotQA / 2WikiMultiHopQA
  (supporting-fact annotations = cheap evidence proxy). TruthfulQA / MMLU-Pro (hard knowledge).

### Drop / de-prioritize
- **Plain GSM8K as a faithfulness dataset** — answer-correctness only (proposal already flags this). Use
  only for controlled math sanity checks — and prefer **PERL** (PARC's released data: premise + error
  annotations, PARC format, directly reusable) over raw GSM8K.
- **HLE-Bio caution:** extremely hard (HLE); models may fail so badly faithfulness is moot. Good as a
  stress test, not a primary signal.

### Label-construction & hygiene
- Where faithfulness labels are missing, synthetic corruption (PARC/FRIT-style inject-and-propagate) is
  cheap **but PARC and Bentham (TMLR'24) both show synthetic negatives are systematically *easier* to
  detect than real model errors** → always report synthetic vs real (human-labeled FaithCoT/GRACE)
  **separately**, never pooled.
- Contamination: GSM8K/MATH heavily contaminated; FaithCoT-Bench/GRACE/DeltaBench are newer (lower risk).

---

## 5. Approaches — what to borrow per pipeline stage

- **A. Decompose:** PARC atomic-step segmentation; ReasoningFlow typed nodes (Fact/Reasoning/Assumption/
  Conclusion — *same authors*) to type premises.
- **B. Premise DAG:** PARC **Aggregative** extraction (high recall, cheap) over **Dyadic** (O(n²)); GoV
  "node-block" adaptive granularity for long traces; FOLIO/PERL for gold-DAG ablation. PARC reports ~90%
  premise recall even from open models → feasibility is established.
- **C. Local verification — TWO CHANNELS** (architected separately, per REVEAL):
  - *Factual/grounding:* NLI via **SummaC** (sentence-pair aggregation), **AttrScore/ALCE** (attribution
    typing: attributable/extrapolatory/contradictory), **FActScore/SAFE** (atomic-fact retrieve-and-verify).
    Add a **retrieval-quality gate** (Self-RAG critique tokens / CRAG relevance / RARR agreement gate /
    FEVER NEI) to label *retrieval failure* vs *reasoning failure*.
  - *Logical/inferential:* premise-constrained LLM judge (PARC) + symbolic where formalizable
    (**VeriCoT/LINC** FOL prover; **PAL/PoT** interpreter for arithmetic; **SatLM** declarative). Measure
    the autoformalization-faithfulness gap ("Do LLMs Game Formalization?").
- **D. Intervention:** **CCT** distributional answer-shift (not binary flip); select premises by DAG
  load-bearingness; baselines = random (Lanham), resampling (Thought Anchors), output-level (RFEval);
  FRIT pair-construction reusable.
- **E. Aggregate:** transparent weighted score / light classifier (as proposed — fine for v1); DFS over DAG
  for accumulation-error / first-unfaithful-step (PARC); report **calibration**; penalize hallucination >
  abstention (CRAG scoring philosophy).
- **Judge hygiene:** cross-model judge (Panickssery NeurIPS'24 self-preference); decompose into per-step
  *binary* checks to dodge position bias (CALM, ICLR'25; position-bias study AACL'25); do not trust
  self-correction (Huang et al., ICLR'24).

---

## 6. CRAG verdict (two different CRAGs — do not conflate)

**(1) Corrective RAG — the METHOD** (Yan et al., arXiv 2401.15884). *Useful concept, mostly overkill for
v1 — adopt a stripped-down version.* It's a retrieval-quality evaluator (Correct/Incorrect/Ambiguous) →
corrective action (knowledge refinement / web-search fallback). The valuable piece is exactly the
**retrieval-quality gate** that lets you attribute a failed step to *bad retrieval* vs *bad reasoning* —
your hardest sub-problem. **But:** (a) it scores query/doc relevance, not premise-grounded step support;
(b) full CRAG (trained T5 evaluator + decompose-recompose + web fallback) is heavy infra; (c) it's an
**unrefereed preprint (ICLR'25 submission withdrawn)** — don't lean on it as a peer-reviewed anchor.
→ **Adopt the gating *idea* cheaply (NLI/LLM relevance check), cite *Self-RAG* (ICLR 2024) as the
peer-reviewed anchor, reserve web-search fallback for the knowledge-intensive ablation only.**

**(2) CRAG benchmark — the DATASET** (Yang et al., Meta, **NeurIPS 2024 D&B**, arXiv 2406.04744). *Good as
an optional knowledge-intensive testbed / retrieval substrate, NOT a primary dataset.* It is short-form
factual QA with **no faithfulness or step-level annotations** → it cannot supply your target labels. Value:
hard long-tail/time-sensitive questions to *generate CoT traces you then audit*; fixed **mock Web/KG APIs**
→ reproducible evidence + counterfactual experiments isolating retrieval quality; hallucination-penalizing
scoring to mirror. → **Phase-3 add-on paired with FaithCoT-Bench, not Phase-1.**

**Bottom line:** CRAG is feasible and well-aligned with the evidence-grounding stage, but **neither variant
is core**. Use Corrective-RAG's gate idea (cheap, cite Self-RAG); use the CRAG benchmark only as an optional
knowledge-intensive substrate.

---

## 7. Positioning, reviewer objections, MVP

### Top reviewer objections → preempt
1. **"Novelty — GoV/VeriCoT already do premise-DAG + constrained verification; Breaking-the-Chain/Thought-
   Anchors already do targeted interventions; FaithCoT-Bench already benchmarks counterfactual+judge
   detectors."** → Narrow the claim to **premise-DAG-driven intervention selection + evidence-grounded
   knowledge-intensive detection**, and **demonstrate wins over those exact methods as baselines.**
2. **"Terminology — 'faithful CoT' already means Lyu's by-construction thing."** → Disambiguate explicitly
   in the intro (detection of post-hoc unfaithfulness ≠ faithful-by-construction generation).
3. **"Your verifier shares the generator's errors / LLM judges are biased & unreliable."** → Cross-model
   judging; premise-restriction (PARC evidence); external NLI+symbolic signals; report judge-bias controls.
4. **"Premise-extraction errors propagate."** → Gold-DAG ablation on FOLIO/PERL; report premise P/R (PARC
   shows ~90% recall feasible).
5. **"Targeted ≠ better than random / unfaithfulness is just disguised accuracy."** → Control for
   answer-choice bias (Bentham TMLR'24); CCT distributional metric; show targeted > random head-to-head.
6. **"Cost."** → Report token/latency/call budgets; show a cheaper judge can match (one of the proposal's
   own stated success criteria).

### Minimum publishable result
Graph-targeted interventions + evidence grounding **beat FaithCoT-Bench's best existing detector by a
meaningful margin on the knowledge-intensive subsets (TruthfulQA, HLE-Bio)**, AND deliver better
first-unsupported-step **localization** than PARC/GoV/VeriCoT-style verification — with bias and cost
controls. A rigorous *negative* result ("targeted ≈ random once you control for X") is still a workshop
contribution.

### Scope cuts for a summer timeline
Defer white-box to future work; one math/logic + one knowledge-intensive subset; reuse **PARC code + PERL +
FaithCoT-Bench harness**; **Aggregative** premise extraction only; NLI + cheap relevance gate instead of full
Corrective-RAG; symbolic channel only on the logic subset (FOLIO).

---

## 8. New citations to add to `ur2phd.bib` / `literature-map.md`

Highest priority (verified, load-bearing): **GoV** (2506.12509), **VeriCoT** (2511.04662), **Breaking the
Chain** (2603.16475), **StepGap** (2605.24733), **GRACE** (2606.16151), **REVEAL** (2402.00559),
**ProcessBench** (2412.06559), **DeltaBench** (2502.19361), **RFEval** (ICLR 2026), **Thought Anchors**
(2506.19143), **Lanham et al.** (2307.13702), **Turpin et al.** (NeurIPS 2023), **Self-RAG** (2310.11511),
**Corrective RAG** (2401.15884), **CRAG benchmark** (2406.04744), **FOLIO** (EMNLP 2024), **StrategyQA**
(TACL 2021), **PRM800K / Let's Verify Step by Step** (2305.20050), **Bentham et al.** (TMLR 2024),
**Do LLMs Game Formalization?** (2604.19459).
