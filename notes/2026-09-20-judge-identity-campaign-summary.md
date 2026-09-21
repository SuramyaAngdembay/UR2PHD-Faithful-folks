# Judge-identity campaign: consolidated summary (2026-09-19/20)

> **CORRECTED 2026-09-21 — see `2026-09-21-independent-code-audit.md`, `2026-09-21-validity-stress-tests.md` and `2026-09-21-scoop-check-six-contributions.md`.** Of the five "findings that survive" below: #2 (judge nondeterminism) is already published by others and should be reported as practice, not contribution; #3's figures and its unanimity claim are wrong as stated; #4 (self-preference "absent, Verified") is downgraded to "not identifiable"; #1 (the ceiling) carries four caveats — pooled over generators (within-generator ceiling ~0.64), not uniform over domains (AQuA blind 0.75-0.88), possibly a label-reliability limit, possibly prompt-bound. The withdrawal in table row 3 rested on an invalid test. "2.2x" came from a partial in-flight arm; the final figure is 2.3x.


Written for the ChainTrackers team and Dr. Rahimi. Synthesises six notes from a single campaign.
Every number below traces to a committed artefact; per-finding detail is in the linked notes.

## What was run

Thirty local open-weight judge arms on Aquaman, plus reanalysis of eight cached API arms. Every arm
uses prompt A verbatim and the same 1,304 FaithCoT traces, so the judge model is the only variable.

- **Ten distinct judge models**: gpt-4o-mini, gpt-4o, gpt-5.2, Qwen2.5-7B-Instruct, Qwen3-8B,
  Qwen2.5-3B-Instruct, Llama-3.1-8B-Instruct, Meta-Llama-3-8B-Instruct, Llama-3.2-3B-Instruct,
  Olmo-3-7B-Instruct. Local models run 4-bit across 2x RTX 3070.
- **Three seeds per local model** at temperature 0.7, plus one greedy repeat, giving within-model
  noise floors.
- Cost: electricity. The API equivalent would have been roughly $200.

## Findings that survive

**1. No judge exceeds 0.679 in the blind regime. (Measured, 10 judges)**
The same ten reach 0.830 in the correct regime. Capability buys 2.2x more in the correct regime
than the blind one across all ten, 3.5x among the seven at 7B and above. Stated as a ceiling, it is
falsifiable by one counterexample and none of ten provides it, including a frontier reasoning
model. This is the single most useful result for the paper: it converts "hard for our judges" into
"hard for every judge we can obtain". → `2026-09-20-judge-capability-axis.md`

**2. Local greedy judges are exactly reproducible; API judges at temperature 0 are not. (Verified)**
Qwen3-8B run twice greedily: 1304/1304 identical scores, AUROC equal to 4 decimals. gpt-4o-mini at
temperature 0 agrees on 83.9% of items; gpt-5.2 under an identical configuration on 25.9%. Sampled
local decoding at 0.7 gives a median AUROC spread of 0.014 across twelve cells — **less noisy than
the API at temperature 0**. Consequence: single-run API judge differences below about 0.05 are not
interpretable, and the field reports such differences routinely.

**3. Judge scores encode which model wrote the trace. (Measured, 9 judges)**
Holding question and human faithfulness label fixed, traces are scored 19.5 to 31.7 points apart by
author model, against a question-only control floor of 1.1 and a faithfulness-label effect of 5.4
to 19.7. The two-group partition is unanimous across nine judges: Gemini and gpt-4o-mini traces are
always scored more faithful than Qwen2.5-7B and Llama-3.1-8B traces. Length explains 8 to 16%.
**Largest in the strongest judge tested**, so not a weak-judge artefact.
→ `2026-09-19-generator-identity-bias.md`

**4. Judge self-preference is absent. (Verified, 3 pre-registered tests)**
Spec frozen before any per-generator quantity was computed. gpt-4o-mini -8.63 [-14.57, -2.89],
Qwen2.5-7B -1.06 [-7.20, 5.44], Llama-3.1-8B **+25.22 [18.90, 31.41]** — significant in the
opposite direction. Differences-in-differences: -4.89, -9.26, +7.72. Signs disagree; there is no
effect. Self-status held fixed still spans 34 points, all of it explained by which generator
happens to be self.

**5. The headline regime gap survives stratification and pooling understates it. (Measured)**
Three of four generators show roughly +0.22 against the pooled +0.152. An independent
implementation reproduces the paper's headline at +0.152 [0.089, 0.215] against [0.089, 0.211].

## Claims withdrawn or narrowed today

Recorded because the withdrawals are as load-bearing as the findings.

| claim | status | why |
|---|---|---|
| "Blind-regime performance does not move with judge capability" | **withdrawn** | written on 8 judges (spread 0.054); the two 3B judges take it to 0.132 across ten |
| "All judges rank the generators identically" | **narrowed** | true as a two-group partition for 9 of 9; false as a total order (Olmo dissents) |
| "Pooled leaderboards partly rank generator style" | **withdrawn** | rank correlation 0.99 pooled vs within-generator, 4 inversions of 153 |
| Audit's "clean" verdict on judge self-preference | **corrected** | argued from BonaFide family non-overlap, never checked on FaithCoT where our judge wrote 26.1% of traces |
| Matos supports strict F1 collapsibility | **narrowed** | paper labels F1 model-dependent; separately proves AUC non-collapsible |
| `arcuschin2025wild` is a 2025 preprint | **corrected** | published ICML 2026; the widely-cited "ICLR 2025" is a workshop paper |

The third row matters most. The generator effect is large in score space and nearly inert in
ranking space, because AUROC is rank-based and an offset moves a generator's faithful and
unfaithful traces together. **That is the same invariance the spec used to reject the naive
self-preference design, and I failed to apply it to my own consequence claim until I tested it.**

## What this means for the paper

1. **Strengthen the blind-regime claim to a ceiling result.** Ten judges, no exceptions. This is
   the direct answer to "you used a weak judge" and it is currently unclaimed.
2. **Add the run-to-run noise result as a methodological contribution.** It bears on any paper
   using LLM judges, not only ours.
3. **Report the generator effect at scoping level**, beside the noise finding, as a caution about
   interpreting individual judge scores. Not in the composition argument, where correctness does
   the work and generator identity demonstrably does not.
4. **Report self-preference as a tested null.** Reviewers will raise Panickssery because our
   primary judge wrote a quarter of the traces. Three pre-registered tests beat a disclaimer.
5. **Name the correction family for each claim family.** 73 of 115 interval-bearing estimates
   currently carry no pre-registration statement. → `2026-09-19-multiplicity-ledger.md`

## Open

- Four Qwen2.5-3B-Instruct arms finishing; they replace base-model arms excluded for 20% non-random
  parse failure.
- Whether the generator effect survives on GRACE and BonaFide, which have different generators and
  annotation protocols. Needs a fresh spec.
- What drives the generator ordering. Length is ruled out; hedging, structure, formatting and
  refusal style are not tested.
- Llama-3.2-3B's greedy blind AUROC sits below all three of its sampled seeds by more than its own
  seed spread. Unexplained.
- **Rotate the Hugging Face token.** It was pasted into a transcript and all downloads are done.
