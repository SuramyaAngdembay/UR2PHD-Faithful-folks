# 2026-08-16 — Temper search (adversarial self-audit) + patch

Two red-team agents + 5 direct empirical checks against the frozen TMLR draft.
**No kill-shots. Core asymmetry survived everything.** Four Tier-1 weakeners found,
all verified, all patched with new computations (commit refs in git log).

## Verified findings -> patched into paper
1. NLI = length proxy (Spearman .86-.89 w/ steps; fraction-unsupported at chance both
   regimes .528/.507). Length alone reproduces the asymmetry (.620 correct / .505
   incorrect). DISCLOSED as thesis-strengthening ("metric detection is shallow");
   length baseline rows added to Tables 1-2.
2. Judge 0.679 pooled > every per-model cell (0.60-0.66; weighted mean .634 = composition)
   + AQuA-heavy (.880 vs .60-.64 elsewhere). Disclosed; abstract qualified.
   Parseability sub-attack REFUTED (0 unparseable in release).
3. Degradation .830->.679 survives domain matching: excl-HLE delta .140 [.070,.209];
   within-domain weighted +.109 (tqa +.119 / logiqa +.175 / aqua +.025). Disclosed.
4. Hint inversion leg: AQuA-only n=181/186 now stated; reframed as coupling-mechanism
   confirmation (labels coupling-aligned by construction).

## Tier-2 tests run
- Question-clustered bootstrap (340 clusters, 3.8 traces/q): judge CIs essentially
  unchanged (.679 [.633,.726]) -> disclosed in S3.
- Text-baseline transfer control (NEW RUN, roberta-mnli embeddings, hint->ft1v2):
  0.476 [.382,.573] = CHANCE -> mundane-text-carrier attack on the 0.616 activation
  transfer is dead; added to S7.3.
- Complementarity full disclosure: logistic .666, judge-mid-tercile probe .536 (n=48);
  "rank-mean" relabeled to z-mean (what the code does).
- Label churn per-cell (ft4 185->107, ft1 189->281) disclosed; superseded labels
  unrecoverable.
- Judge snapshot pinned: gpt-4o-mini-2024-07-18 (predates benchmark => contamination
  impossible); score histogram (7 effective levels) disclosed.

## Defused (do not concede in rebuttals)
Inversion is NOT length (0.32-0.38 inverted in every length tercile) and NOT domain
(holds 3/4 domains). No layer leakage in combination (nested OOF verified). No judge
contamination. Regime split not pure annotation artifact (binary-label + hint replication).

## Unexploited directions (scout report; NOT run - rebuttal arsenal / future work)
Top: (1) reasoning judge / R1-as-judge (judge currently forbidden to reason, max_tokens=30
- most attackable absence); (2) SelfCheckGPT-family self-consistency detectors (absent;
P(re-reach answer sans CoT) = our coupling mechanism operationalized); (3) cross-model
re-encoding probes (tests our own "closed models cannot be probed" sentence; could turn
"weight access required" into "any open reader suffices"). Also: logprob baselines,
routed judge->probe monitor, judge-probe disagreement as label-noise audit, difficulty
as third axis, PRM audit. Best next paper: export stratification protocol to
hallucination detection (<1 month, reuses everything).
