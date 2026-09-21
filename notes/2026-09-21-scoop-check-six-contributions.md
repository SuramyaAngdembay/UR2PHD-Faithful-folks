# Scoop check on six candidate contributions (2026-09-21)

Independent literature agent, ~160 tool calls. Evidence grades are the agent's own and are kept:
**[FT]** full text downloaded and the quoted span seen; **[ABS]** abstract/metadata page read;
**[SR]** search summary only. Per `subagent-claim-intake`, nothing below graded [ABS] or [SR] may be
cited in the manuscript without a direct read, and the [FT] quotes should be spot-checked before
they carry an argument. "Not found" means the searches did not surface it, not that it is absent.
Our own preprint is arXiv:2607.23458 and dominated several result sets.

## Verdicts

| | candidate contribution | verdict |
|---|---|---|
| A | correctness-stratified detector evaluation; metrics at chance on wrong answers | **partially anticipated — the specific result was not found elsewhere** |
| B | step-removal metrics anti-correlate with human labels | **partially anticipated, strongly** |
| C | capability-invariant judge ceiling on wrong answers | **not found; published results point the other way** |
| D | temperature-0 judge nondeterminism as a metric noise floor | **scooped in substance** |
| E | judge scores depend on who authored the trace; self-preference null | **partially anticipated** |
| F | constructed unfaithfulness does not transfer to human-annotated | **partially anticipated — the CoT human-annotated test was not found** |

## A — the strongest positioning we are not currently using

The CoT-monitorability literature recognises the correctness confound and resolves it by **deleting
the wrong answers**:

- Guan et al., "Monitoring Monitorability" (OpenAI; arXiv:2512.18311; ICML 2026 Oral) [FT]: "there is
  no way to soundly define negatives: if the model gets an incorrect answer…", "we drop incorrect
  answers for process evals".
- Emmons et al. (GDM; arXiv:2510.23966) [FT]: "we analyze CoTs only from tasks where the model
  produced a correct final answer… Including these instances would contaminate our metric".
- Arnav et al., CoT Red-Handed (NeurIPS 2025) [FT]; METR Aug 2025 [FT]; METR Jan 2026 [FT]: same move.

None reports detector performance on the wrong-answer stratum. **That stratum is exactly what our
paper evaluates**, and it holds most annotated unfaithfulness. This is a better framing than the
manuscript's current one and it is unclaimed.

Two objections a reviewer will bring, both must be met head-on:

- **Krumdick et al., "No Free Labels" (arXiv:2503.05061) [ABS]:** judges agree with experts "only on
  questions the judges were able to correctly answer themselves". The mundane reading of
  0.830 -> 0.679 is that wrong-answer items are hard questions, and hard for the judge too.
- **BonaFide [FT]:** "FaithCoT-Bench labels CoTs as unfaithful when annotators judge the reasoning
  path as implausible or wrong." Under that reading our result is about the label, not the detectors.

Adjacent precedents: Zhang et al. PRM lessons (arXiv:2501.07301) [FT] — a final-answer-conditioned
detector evaluation for process *correctness*, where the correct-answer stratum is the hard one;
Li et al. (arXiv:2605.11746) [FT] stratify an alignment measure by correctness. FaithCoT-Bench v2
[FT] reports the four-quadrant counts and phi = 0.286 but no stratified detector results.
CIE-Scorer [FT] and GeoFaith [FT]: no stratification.

## B — mostly taken

BonaFide [FT] already reports below-chance AUROCs for perturbation metrics (SCM 0.38, Early
Answering 0.32-0.44 on non-reasoning models, CC-SHAP 0.41). **FaithCoT-Bench's own appendix [FT]
already shows negative kappa against its human labels** for Removing Steps (-7.6, -16.0), Early
Answering (-10.7, -14.6) and Answer Tracing (-15.6, -20.3); the authors do not read it as inversion.
Tutek et al. FUR (EMNLP 2025) [FT]: Pearson 0.15 with human ratings. What is left for us: the
explicit inversion AUROC, reproduction on released scores, the causal-label replication, and the
regime localisation. **To verify before citing:** the agent could not find "fails to beat random" in
the Zaman & Srivastava abstract — check the body or soften our wording.

## C — credited only with two further tests

Published results say stronger monitors help: Guan et al. [FT] (+40% g-mean² o3-mini to GPT-5
Thinking); METR x2 [FT]. Partial saturation exists: Wang et al. (arXiv:2510.01367) [FT], Yang et al.
(arXiv:2607.08535) [FT], an Anthropic blog (21 Aug 2026) [FT]. **GeoFaith Table 1 [FT] already runs
six judges on FaithCoT pooled** (GPT-5 56.3, DeepSeek-V3.2 59.1, ... Llama-70B 32.7 F1; trained 8B
detector 61.7) — non-monotone, unstratified, no ceiling claim.

**The sharpest threat:** BonaFide's *generic* judge scores 0.67-0.68 on a mostly incorrect-answer
population — a striking coincidence with our 0.679 — while their **definition-informed judge reaches
0.82-0.87**. So our ceiling may be prompt-bound. C must be scoped to generically prompted judges
until a definition-informed prompt and a reference-guided arm have been run on our blind regime, and
CIE-Scorer/GeoFaith are untested on that stratum and could be counterexamples.

## D — do not claim

Atil et al. (Eval4NLP 2025; arXiv:2408.04667) [ABS]; Tamba (arXiv:2606.26185) [FT]; Yagubyan
(arXiv:2606.13685) [FT]; Lau (arXiv:2603.04417) [ABS]; Messing (arXiv:2604.11581) [ABS]. New to us
is only the AUROC-level number and the API-versus-local-greedy contrast. Report as practice.
Caveat from Yuan et al. (arXiv:2506.09501) [ABS]: local inference also varies with batch size and
GPU count, so our "exactly 0" holds for a fixed configuration only.

## E — an extension, with an objection that lands

Quality-controlled designs exist (Chen et al. EMNLP 2025 [ABS]; Spiliopoulou et al. [ABS]; Yang et
al. [ABS]); a self-preference null exists (Roytburg et al., ICML 2026 [ABS]: only 51% of prior
self-preference findings survive an evaluator-quality baseline). Goel et al. (arXiv:2502.04313)
[ABS] find judges favour similar models — our null disagrees and must address it.

**The objection that lands:** a binary label does not hold *quality* fixed, and our unanimous
two-group partition (Gemini and gpt-4o-mini scored more faithful; Qwen2.5-7B and Llama-3.1-8B less)
**tracks generator capability**. The judges may simply be right that, within the same label, weaker
models' traces are worse. Our campaign note says "not a validity verdict" but does not name this.

## F — our most distinctive piece

Kirch et al. (arXiv:2511.17408) [FT] make the general off-policy point; arXiv comments now read
**"ACL 2026"**, so `offpolicy2025probes` is stale (**verify before editing the bib**). Goldowsky-Dill
et al. (ICML 2025) [SR] report instructed-deception probes *do* transfer (0.96-0.999) — we must
position against it. Deception-domain analogues: Luikham (arXiv:2609.00180) [FT]; Ying et al. [FT];
Natarajan et al. (ICML 2026) [ABS]; Smith, Chughtai, Nanda [ABS]. An Anthropic blog [FT] includes a
CoT-unfaithfulness fold: in-distribution 0.95, cross-fold 0.70-0.75. Mirtaheri & Belkin [FT] list
this transfer as future work. **In tension with our metadata-template failure:** Nguyen, Cox, Meek,
Arcuschin (arXiv:2607.29062) [FT] find faithfulness steering generalises across cue types.
**No one was found testing constructed CoT unfaithfulness against human annotations.**

## What a sceptical reviewer would credit

Credited: the empirical core of A, if Krumdick and the BonaFide label critique are answered; and F.
Credited with caveats: C. Read as extensions: B and E. Already known: D.

Incidental: FaithCoT v2's published counts give 204/(204+185) = 52% of unfaithfulness on wrong
answers against our 69% from the release. Our appendix already notes the figure is
release-sensitive; the **abstract leads with 69%** and should not do so without the qualifier.
