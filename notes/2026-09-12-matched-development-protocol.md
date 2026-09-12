# Follow-up: fresh matched development pairs

Recorded before the new predictions. Batch 1 completed 88/88 unique calls with
no errors. Its four source-flip templates separate perfectly under full evidence,
but native B1 balanced accuracy is 8/24 and definition-aware D1 is 11/24.
Their paired balanced-accuracy difference is .125, 95% bootstrap interval
[-.0778, .3007]. The continuous B1 AUROC is .09375; word-count AUROC is .9931.
Crucially, no generator appears in both classes in that deliberately small
coverage sample. It cannot isolate a within-generator reader failure.

Rather than tune the prompt, use the remaining untouched development questions
to test the existing procedures with a tighter comparison. Exclude every question
in the original eight-item smoke and 24-item batch 1 native sample. Require
opposite native labels, identical generator and task, at most 800 trace words,
word-count ratio at most 1.25, and distinct question clusters throughout. Sort
candidate edges by absolute log length ratio and stable response IDs, selecting
greedily without question reuse. This audited rule yields six pairs (12 cases),
all SimpleQA, spanning three Instruct generators. It is a deterministic matching
rule, not a claim of maximum possible matching or population representativeness.

Run frozen A1/B1/A2/B2 and definition-aware full-context D1 on every response:
60 slots, at most 72 attempts, 1,500-second whole-run deadline. Reuse the successful
token-aware transport and original v2.1 prompts without modification. Keys remain
outside inference. Record the complete request plan before scoring.

Primary native statistic: within each matched pair, does U score above F (1),
below F (0), or tie (.5)? Average the six pair outcomes. Primary context contrast:
mean win(B1)-win(A1), with 2,000 pair bootstrap draws. Other arms and their pair
tables are descriptive. Report the word-count pair baseline. Do not pool all
cross-generator pairs and call that a matched estimate; do not replace this
endpoint after observing results. Six pairs cannot establish a general remedy.

If full context still fails, the literal-source control success does not explain
the natural-data problem. Inspect what the native labels call violations and
which evidence would support those particular claims. If performance improves,
test the same fixed procedure on additional support before claiming recovery.
Neither outcome licenses treating native labels as independently observed
internal computation or opening the 807-response evaluation automatically.
