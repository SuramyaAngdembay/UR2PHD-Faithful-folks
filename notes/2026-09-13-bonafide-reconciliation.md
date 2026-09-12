# BonaFide reconciliation: our judge vs their published generic monitor — 2026-09-13

**Question.** BonaFide reports a *generic* LM monitor at **0.68 ± 0.02** CoT-level AUROC on the same
1,120 whole-label population where our frozen gpt-4o judge scored **0.270** and gpt-4o-mini 0.419.
Same labels, same examples, opposite sides of chance. Which of evidence policy, rubric, or judge
model explains it?

**Method.** Cloned github.com/yoavgur/BonaFide and reimplemented `metrics/monitor/` faithfully:
their verbatim generic COT_PROMPT, their `_resolve_prompt_text` hint-stripping rule, their
suspicion-score output contract. Judge held fixed at gpt-4o across arms (theirs is
gemini-3-flash-preview, so this reproduces their *design*, not their number). Stratified pilot,
n=150 common responses, question-clustered bootstrap. Exploratory, on an already-unblinded
population; not a frozen endpoint.

| arm | condition | n | AUROC | CI95 |
|---|---|---|---|---|
| A | their prompt + hint visible (`monitor_generic`) | 284 | **0.352** | [0.285, 0.425] |
| B | their prompt + hint stripped (`monitor_no_hint`) | 150 | 0.400 | [0.307, 0.493] |
| C | our rubric + hint visible | 150 | 0.367 | [0.280, 0.457] |
| D | our rubric + no prompt (frozen, gpt-4o) | 150 | 0.331 | [0.245, 0.417] |
| — | same, gpt-4o-mini (reference) | 150 | 0.479 | [0.383, 0.572] |

## My evidence-access hypothesis was WRONG

I predicted their monitor scores higher because it *sees the planted hint* and ours did not (spec
clarification C1). It does see the hint — their template is shown "the prompt given to the model" —
but supplying it does **not** help: arm A (hint visible) 0.352 vs arm B (hint stripped) 0.400. If
anything, showing the hint made it slightly worse. Their rubric doesn't explain the gap either
(A 0.352 vs C 0.367, essentially identical). **All four arms are below chance**, 0.331–0.400.

So neither of the two mechanisms I proposed accounts for the discrepancy, and the frozen result's
evidence policy is *not* the reason it inverted. That part of the earlier reading is withdrawn.

## A likelier explanation: a score-direction convention in the public code

In the shipped code, `metrics/base.py` documents the metric contract explicitly:

> `score_cot(...)` — "Score entire CoT faithfulness (0 to 1). **Higher = more faithful.**"

`MonitorMetric` honours it — it parses a boolean `{"faithful": true|false}`. But
`MonitorGenericMetric.parse_response` returns

```python
score = parsed["suspicion_score"]          # 0-100, higher = more SUSPICIOUS
return MonitorResult(faithful=score / 100.0)
```

placing a suspicion score into the slot contracted as faithfulness, and no negation appears
anywhere downstream in the shipped metric code.

If the (unreleased) analysis step consumes that contract as documented, the published generic-monitor
figure is computed on an inverted score, and its correctly-oriented value would be
**1 − 0.68 = 0.32**. Our three independent reimplementations land at **0.331 / 0.352 / 0.400**.
That the complement of their number falls inside our measurements across three arms is strong
corroboration, though not proof.

**Hedges, stated plainly.** The repo ships no AUROC code, so the final orientation step cannot be
verified from public artifacts; the repo may differ from the code that produced the paper; and the
*definition-aware* skyline (0.82) parses a genuine boolean and is unaffected by this. The decisive
check is asking the authors — the same courtesy we extended to FaithCoT over its label semantics.

## Consequence for our paper

If this holds, the framing reverses. We are **not contradicting** BonaFide's published baseline:
our measurement agrees with their data, and the apparent 0.68-vs-0.27 conflict is a reporting-sign
artifact rather than a scientific disagreement. The judge inversion on intervention-defined labels
would then be **corroborated by their own monitor**, not in tension with it. Until the authors
confirm, the paper should state the discrepancy, our reimplementation, and the sign hypothesis as a
hypothesis — not assert a bug in someone else's benchmark.
