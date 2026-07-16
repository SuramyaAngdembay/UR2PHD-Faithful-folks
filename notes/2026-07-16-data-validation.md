# Pre-submission data validation (2026-07-16): one critical find, everything else clean

*Scripts: `validate_data.py` (pass 1), `validate_data2.py` (pass 2). Requested by Suramya as a
final benchmark-integrity gate before submission.*

## CRITICAL FIND (pass 1): FaithCoT-Bench ft-code correctness axis is INVERTED vs its README
The released JSONs code: **ft3=faithful-CORRECT, ft4=unfaithful-CORRECT (post-hoc-on-correct),
ft1=faithful-INCORRECT, ft2=unfaithful-INCORRECT** — verified uniformly across all 4 domains via
parsed_final_answer==label (ft3/4 ≈100% match gold; ft1/2 ≈0%), and externally confirmed: under
this reading the data reproduces the FaithCoT paper's own claim (Qwen aqua 81% acc/36% unf vs
Llama 58%/22%). The README states the opposite pairing (Type1/2=correct). Our code inherited the
README mapping since June (`correct = ft in (1,2)` in rigorous_analysis.py) ⇒ every "correct-answer
regime (ft1v2)" analysis actually measured the INCORRECT-answer regime.

**Corrected readings:**
- Audit headline 0.696 = INCORRECTNESS→unfaithful (not correctness).
- "Frontier" (all-black-box-at-chance) = the incorrect-answer regime (honest-error vs unfaithful-error).
- TRUE correct regime (ft3v4, complete n=363, ft4=74): black-box works moderately —
  soft 0.667 [0.592,0.736], interventions 0.659, NLI 0.626 (sig); DAG ns. Inversion holds there too
  (intended-direction 0.333).
- White-box probes/steering/bridge all targeted ft1v2 = incorrect regime (numbers real, meaning relabeled).
- Hint testbed (correct-by-construction) → bridge is a cross-regime transfer.
- ft3v4 per open model: llama ft3=137/ft4=26; qwen 152/48 (white-box on true correct regime possible but thin).
- ⇒ file GitHub issue with FaithCoT authors; paper must state the verified mapping explicitly.

## Pass-2 results (all clean)
- soft coverage: 682 traces carry sample_0.soft_faithfulness (634 = ∩ with intervention subset ✓).
- 61 unlabeled traces (60 ft=None, 1 ft=0; mostly aqua) consistently excluded (1364−60=1304 ✓).
- Question structure: 100 q × 4 models per domain (HLE: 40 q, some ×2/model) — a clustering level.
- **Question-clustered bootstrap (335 clusters): audit headline SURVIVES** —
  incorrectness 0.696 [0.660,0.734]; soft 0.651 [0.606,0.698].
- **Soft reimplementation vs their stored values: Spearman 0.822** (Pearson 0.711, n=30) — our
  AUROC-based (rank) results on synthetic/hint stand on a consistent implementation.
- Parser determinism: 0/458 + 0/613 reparse mismatches. Golds: 254/254 aquarat letters, 0/1319
  bad gsm8k numerics.
- Their stat.py fills missing labels with defaults (unfaithfulness=0, ft=3) — potential silent
  label-noise mechanism in the release pipeline; noted as caveat.

## Status
Everything except the ft-mapping is validated clean. Paper decision pending: full honest reframe
(Option A, go/no-go tonight) vs skip deadline (Option B).
