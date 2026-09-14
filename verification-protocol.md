# Evidence-verification protocol — frozen 2026-09-14, before any new inference

**Objective.** Test whether explicit claim-by-claim evidence verification reduces *false
accusations* by a faithfulness judge. We have a development lead, not an established corrective
method, and this protocol is written before any new request is issued.

## 0. Inherited conclusions (carried forward, not re-litigated)

1. Restricted component vs restricted generic: **ΔAUROC +0.293 [+0.093, +0.502]**, exploratory,
   from a 70-response development sample.
2. Above-chance component detection is **unproven** (A2 0.511 [0.320, 0.694]); benefit from
   additional evidence is **unproven** in both directions (B1−A1 +0.042 [−0.015, +0.107];
   B2−A2 −0.066 [−0.159, +0.015]).
3. Exact quotation matching does **not** establish that an accusation is supported. Observed
   quotation failures are largely presentation and wrong-field attribution; they are not a
   hallucination rate.
4. The current component comparison changes **both** rubric text and output structure, so it does
   not isolate the rubric's causal effect.
5. The 70 responses are **development** data. The 807-response partition is **partially exposed**
   (204 responses / 156 question clusters previously scored) and may not be called untouched.

## 1. Populations

- **P1 — cached development outputs.** The 840 completed responses in `pilot-4arm-rep3c`
  (70 responses x 4 arms x 3 repeats). Used for the accusation audit in §3. **No new inference.**
- **P2 — constructed controls.** 24 matched pairs = 48 inputs, built for §4. Labelled *constructed
  controls* everywhere; never pooled with native benchmark AUROC.
- Explicitly **not** used: the 807-response evaluation partition. No tuning on it, no sweep.

## 2. Hypotheses

- **H1 (primary).** Under an explicit claim-by-claim verification procedure, the rate of
  *unsupported accusations* on constructed controls is lower than under generic assessment
  instructions, at matched evidence conditions.
- **H2.** The verification procedure more often correctly identifies **whether a claim was made**
  (separately from whether its execution is established).
- **H3.** The verification procedure more often reaches the correct
  **supported / contradicted / unresolved** decision, including correct use of *unresolved*.
- **H4 (control).** Where the manipulated information is withheld (restricted evidence), the two
  members of a matched pair are byte-identical inputs and must therefore be **indistinguishable**;
  any systematic within-pair separation there indicates a leak or an artefact, not detection.

## 3. Accusation audit of cached outputs (no inference)

All 70 responses and their component outputs (A2, B2). Accusations deduplicated across repeats by
(response, arm, normalised claim + quote), **retaining every contributing request_id**.

Four separable questions per accusation, kept distinct:
  (a) does the quoted text occur in the evidence available to *that* judge (arm-specific)?
  (b) does the trace actually make the alleged claim?
  (c) does the available evidence support, contradict, or leave the claim unresolved?
  (d) does the judge's accusation follow from (b) and (c)?

(a) is automatically checkable and will be reported with reproducible counts and the audit's
location taxonomy (whitespace / presentation / ellipsis-joined / other-field / judge-instructions /
unlocated). (b)-(d) are **semantic** and go to a reviewer packet: native labels, scalar scores and
procedure names hidden where possible, restricted/full evidence boundaries preserved so a reviewer
never sees evidence the judge did not have. Assistant-produced annotations are stored in a
separate file from any human adjudication and are never merged into a single column.

Deliverable: error taxonomy + reproducible automatic counts + reviewer packet. **Quotation failures
are not reported as a hallucination rate.**

## 4. Bounded controlled experiment

**Design.** 24 matched pairs (48 inputs), two families:
- **Source attribution (12 pairs).** Question, answer and trace held fixed; the complete supplied
  prompt either does or does not contain the attribution the trace claims.
- **Verification language (12 pairs).** Distinguishes *proposing* verification ("I should check X")
  from *claiming it occurred* ("I verified X"). Whether a claim was made is scored separately from
  whether its execution is established.

**Construction rules.** Vary wording and sources; do not copy the discovered professor/audit-log
examples; balance superficial cues across members; manually inspect every manipulation.
**Absence of an execution record is not proof that verification never occurred** — the correct
label there is *unresolved*.

**Procedures.** Two instruction sets, **identical** output schema, evidence fields, token cap and
model (pinned `gpt-4o-2024-08-06`, temperature 0): generic assessment vs explicit claim-by-claim
evidence verification. Both emit claim, quotation, support-status and overall score. Instructions
frozen in a config before running. This equalises output structure, addressing inherited
conclusion 4.

**Call budget.** 48 inputs x 2 evidence conditions x 2 procedures x 3 repeats = **576 calls
maximum** on the pinned judge. No other inference.

## 5. Endpoints

Primary: unsupported-accusation rate (H1). Secondary: claim-made accuracy (H2), support-status
accuracy including unresolved coverage (H3), within-pair ordering, repeat stability.
Uncertainty is paired and grouped by **source question**. Unresolved coverage is reported
explicitly, never silently folded into an error. Constructed-control results are reported
separately from native benchmark AUROC.

## 6. Advancement rule (fixed now)

- Semantic decisions improve -> freeze the procedure, then test fresh native examples and a second
  judge family, then adapt only compatible components to GRACE.
- Scores move without accusation validity improving -> record the negative, inspect the specific
  failure, do not expand.
- No large benchmark sweep, no tuning on the evaluation partition, no manuscript restructuring on
  the strength of this experiment.
