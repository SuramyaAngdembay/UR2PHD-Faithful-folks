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

## ⚠️ CRITICAL CORRECTION (2026-07-16) — read before the history below
**FaithCoT-Bench's released `faithful_type` codes INVERT the README's correctness pairing.** Verified
(per-domain `parsed==label` crosstabs; reproduction of the paper's own Qwen-vs-Llama stats; independently
reported in FaithCoT-BENCH GitHub issue #3, where we commented with the systematic evidence):
**data coding = ft1 faithful-INCORRECT · ft2 unfaithful-INCORRECT · ft3 faithful-CORRECT · ft4
unfaithful-CORRECT (post-hoc-on-correct).** All entries below written before 2026-07-16 use the README's
(wrong) pairing: wherever they say "correct-answer regime / post-hoc-on-correct (ft1v2)", read
**"incorrect-answer regime"**. All *numbers* remain valid; only regime names flip. Corrected two-regime
results: `results/audit_corrected.json` (incorrect regime ft1v2: ALL black-box at chance = the true
frontier; correct regime ft3v4: soft 0.667/interv 0.659/NLI 0.626 sig, inversion strongest +0.176);
`results/faithcot_reproduce.json` (inversion reproduces on THEIR released scores, intended-dir 0.29–0.43);
`results/ft34_probe_*.json` (ft3v4 internally decodable in Qwen p=.014; Llama underpowered n_ft4=26);
`results/regime_transfers_*.json` (cross-regime transfer ~absent; same-regime construction transfers ns)
⇒ regimes are largely representationally distinct; hint construction aligns with the incorrect-regime
signal (0.616 p=.017). **The 2026-07-17 BlackboxNLP deadline was deliberately skipped** — see the phase
plan in "Open next steps". Full forensics: `notes/2026-07-16-data-validation.md`; origin commits
94335ba/2db16a4 (June-25 session overrode the correct `parsed==label` flag in favor of the README).

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
labels at scale; **scaled to 7 models / 3 families spanning 2024→2026** (+Qwen3-8B, +DeepSeek-R1-Distill-7B,
+Gemma-2-9b, +DeepSeek-R1-0528-Qwen3-8B [2026], +**Gemma-4-12B [2026, run via 2-GPU sharding]**).
**(i) White-box probe permutation-significant in ALL SEVEN** (held-out Qwen2.5 **0.81** / Gemma-4-12B **0.80**
/ Llama **0.74** / Qwen3 **0.72** / DeepSeek-R1-Distill **0.62** / Gemma-2 **0.60** / R1-0528 0.56 [n=81, perm
obs 0.688]), generalizing **across AQuA↔GSM8K** (0.52–0.73); effect **model-dependent** — strong in Qwen2.5/
Gemma-4/Llama, weak-but-sig in reasoning-distills + Gemma-2. Surface baseline ≈0.47–0.55 for 5/7 (Llama 0.64,
Gemma-4 0.665 partial surface tell; WB still clears by ~0.1). C1's "internally decodable" leg now holds
cross-family, cross-generation on clean labels. *(Gemma-4-12B runs via `--shard` device_map=auto across the
2×8 GB 3070s, 5.4 GB/card — single-card was the only blocker; ZeRO/FSDP N/A for inference. R1-0528 n=81 from
reasoning overflowing the 1024-tok budget.)* **(ii) The
FaithCoT(real)↔synthetic BRIDGE FAILS** (Llama/Qwen2.5 only — FaithCoT has no real traces for the newer
models) — synthetic post-hoc peaks
**early** (L9/L10), real ft1v2 peaks **late** (L29/L22); cross-distribution transfer is **~chance even
best-of-32-layers and domain-matched** (Llama FC→synth best 0.55 mean 0.48; Qwen 0.60/0.50). ⇒ **synthetic
answer-first is NOT a representational proxy for organic post-hoc** — a publishable methodological caution,
and the honest answer to "how do the two buckets connect" (they don't, internally). Caveat: Llama synthetic
**surface-feature baseline 0.639** (partial surface tell); soft_faithfulness uncomputable on numeric-option
AQuA; Gemma-2-9b blocked on HF gated access. **Disk constraint resolved (2026-07-05): HF cache moved to
`/data` (5.6 TB free) via symlink — no more download-run-delete.**

**Hint-induced ORGANIC post-hoc + 3-way bridge (2026-07-11):** built a Turpin-style biased-context testbed
(baseline-wrong → hint("I think the answer is {gold}") → flips-to-gold + never mentions hint = **organic
post-hoc with a causal label**; clean probed context; leakage-audited). Full AQuA-RAT test (254) + full
GSM8K test (1319). Yields: **Llama 428 genuine + 185 organic-ph; Qwen 464 + 70.** Results: **(i)** organic
post-hoc internally decodable in both (held-out Llama **0.75** / Qwen **0.84**, perm p=0.005; Qwen surface
0.703 caveat). **(ii) C2 inversion replicates with causal labels** — soft intended-direction **0.389 / 0.251**
(far below chance) on traces where reasoning provably didn't produce the answer. **(iii) 3-way bridge
(bridge3.py): depth gradient instructed L9 → hint-organic L17 → annotated L29 (Llama), and hint→FaithCoT
transfers (best 0.694, layer-MEAN 0.616, selection-free) where synthetic→FaithCoT fails (0.531/0.431)** ⇒
C4 sharpens: *instructed* rationalization is the artifact; *spontaneous* rationalization is
representationally continuous with the annotated organic phenomenon. Qwen bridge inconclusive (weak FC
anchor, n=70). **This is the GRACE-independent external validation** — inversion + decodability + the
organic bridge replicate on an independent, causally-labeled testbed. *(Scope note: the at-chance
FRONTIER claim stays FaithCoT-anchored — hint-testbed surface baselines partially separate, 0.63/0.70,
so do not claim black-box-at-chance there.)* The dataset/protocol is itself a contribution (RQ3 v1).
**Perm-tested (2026-07-12): Llama layer-mean p=0.010 (best 0.694 corrected p=0.050); Qwen p=0.741 (null).** Caveats: single hint template; math-only; class imbalance.

## Conventions
- **Data over docs:** when a dataset's documentation and its raw contents disagree, the DATA is the
  tiebreaker — resolve by inspecting ≥3 raw examples before trusting either. Never override an
  empirically-derived flag because documentation disagrees with it (that is how the 2026-07-16
  inversion happened).
- **Benchmark due diligence includes the upstream issue tracker** (FaithCoT issue #3 predated our
  discovery by a week).
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
13. `notes/2026-07-11-hint-organic-bridge.md` — hint-induced ORGANIC post-hoc (causal labels, leakage-audited): decodable both models (0.75/0.84, p=0.005); **inversion replicates with causal labels (soft intended 0.39/0.25)**; **3-way bridge: hint→FaithCoT transfers (mean 0.616) where synthetic fails (0.431)** ⇒ instructed rationalization is the artifact; depth gradient L9→L17→L29.

## Open next steps — POST-CORRECTION PHASE PLAN (2026-07-16; deadline skipped deliberately)
**Phase 0 (this week):** regime_transfers runs (llama done: cross-regime ~absent, same-regime ns; qwen running);
FaithCoT issue #3 commented with our evidence (done, by Suramya); brief Dr. Rahimi (his earlier approval
predates the correction — items 1/4 of his feedback folded into Phase 1); repo semantics corrected (done).
**Phase 1 (wk 1–2):** write the TWO-REGIME paper properly (unfaithfulness lives mostly in wrong answers;
black-box works on correct answers, collapses on incorrect; internals decode the blind regime in Llama and
the detectable regime in Qwen; inversion three-legged incl. reproduction on their own scores; benchmark
correction as community service) → **arXiv preprint ASAP to timestamp** vs concurrent work.
**Phase 2 (wk 2–4):** power the correct-regime evidence via the hint testbed (2nd template, more models,
non-math domain); explain regime-dependent model-dependence (cross-regime direction analysis → SAE
feature-decomposition study, Llama Scope/Gemma Scope); GRACE if ever released.
**Phase 3:** venue from strength — ARR / ICLR 2027 (~late Sept) / next workshop cycle as floor.
The old BlackboxNLP draft (paper/main.tex, pre-correction framing) is superseded — do NOT submit it.
