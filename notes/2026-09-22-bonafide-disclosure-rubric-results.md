# Disclosure-aware rubric on BonaFide: results (2026-09-22)

Spec `bonafide-disclosure-rubric-spec.md` frozen at `b4f1254`; analysis `scripts/bonafide_rubric_H_analysis.py`
(sha `1976f0d37b800d13…`) frozen while the arms ran, unchanged. Both arms complete: gpt-4o-mini on
all 1,120 rows, gpt-4o on reconciliation arm C's 150 rows. Cost about $0.85.

## Pre-registered verdict: NOT-EXPLAINED (primary judge). My 65% expectation was wrong.

| arm | judge | evidence | rubric | AUROC (incorrect pop.) |
|---|---|---|---|---|
| frozen | gpt-4o-mini | clean question | A | 0.419 |
| **H, primary** | gpt-4o-mini | hint visible | **disclosure** | **0.251 [0.211, 0.291]**, Δ −0.167 [−0.218, −0.118] |
| frozen | gpt-4o | clean question | A | 0.332 (on the 143 shared rows) |
| C | gpt-4o | hint visible | A | 0.370 |
| **H, secondary** | gpt-4o | hint visible | **disclosure** | **0.671 [0.582, 0.754]**, Δ vs C +0.301 [+0.217, +0.391] |

## What each judge did with the instruction

Mean unfaithfulness score by BonaFide label, incorrect population:

| judge, rubric | faithful (discloses hint) | unfaithful (hides it) |
|---|---|---|
| gpt-4o, A, hint visible | 77 | 62 |
| **gpt-4o, disclosure** | **46** | **81** |
| gpt-4o-mini, A, clean | 36 | 32 |
| **gpt-4o-mini, disclosure** | **56** | **25** (45% of all scores exactly 0) |

gpt-4o read the rule as written: a trace that acknowledges the cue is faithful, one that hides it
is unfaithful. The two class means swap sides, which is exactly the label's direction. gpt-4o-mini
read the same paragraph as "mentions the cue → unfaithful": disclosing traces went *up* and silent
derivations were scored zero. It applied the conditional backwards.

By hint type for gpt-4o (shared rows): sycophancy 0.72→0.94, unauthorized-access 0.18→0.80,
security-audit 0.35→0.66, metadata 0.05→0.28. Metadata hints — the answer hidden in an XML-style
tag — stay inverted; the judge does not recognise that as a "cue" even when told to look.

## Reading

**The mechanism claim in the reframed BonaFide section survives, with a qualification it did not
have.** With evidence held fixed and only rubric text changed, gpt-4o moves from inverted to well
above chance, which is the direct demonstration that the reversal is a rubric–construct mismatch.
But the same rubric makes a weaker judge worse, because applying "faithful iff it acknowledges the
cue" requires holding a conditional, and gpt-4o-mini collapses it to a keyword rule. So: the
mismatch is in what the rubric asks, *and* resolving it requires a judge able to execute a
conditional definition. BonaFide's 0.82–0.87 came from a Gemini judge with the authors' own prompt;
our gpt-4o reaches 0.67 with a one-paragraph rubric on a 143-row pilot, short of that but on the
right side of chance by a wide margin.

This also sharpens the judge-capability story from the FaithCoT campaign: capability did not buy
blind-regime detection under a generic rubric, but it does buy the ability to follow the construct
you name. The rubric decides which construct is measured; the judge decides whether the rubric is
executed.

**Reported as pre-registered:** the primary decision rule fails. The secondary result is labelled
secondary and rests on 143 rows.

## Manuscript consequence

The BonaFide paragraph's sentence "the mismatch is in what the rubric asks, not in what the judge
can see" is now supported directly for gpt-4o and contradicted for gpt-4o-mini; amended in the
same commit to state both.
