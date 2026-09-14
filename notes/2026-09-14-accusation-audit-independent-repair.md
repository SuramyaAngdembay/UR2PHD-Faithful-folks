# Independent check and repair of the latest accusation audit

September 14, 2026. Reviewed Claude's commits `e0a5c8d` (protocol) and `b135d3c`
(cached audit), its latest session status, the frozen request builder/rubric and
the saved outputs. No new inference was launched.

**The next controlled experiment has not run.** Claude's latest session explicitly
reports the 24 pairs unbuilt and no experiment running. Repository artifacts agree;
a targeted process check on the existing execution host found no corresponding
diagnostic/verification runner. The latest claimed results are a reanalysis of the
existing 840-call pilot, not results from the proposed 576-call experiment.

**The new context-quotation finding is invalid.** Two evidence-mapping bugs create
its central pattern. The blinded reviewer packet also loses the original prompt
for every full-context item. I preserved that audit and created a versioned repair.

## What is correct

The protocol adopts the intended bounded direction: compare generic and explicit
verification instructions with the same output schema, use 24 constructed pairs,
retain unresolved judgments, and cap the experiment at 576 calls. It excludes the
partially exposed evaluation partition. It also carries forward the paired
component improvement without claiming above-chance detection.

The audit correctly distinguishes lexical checks from semantic adjudication in
principle. Its trace-quotation counts reproduce: after its stated presentation
allowances, 230/236 A2 and 229/237 B2 quote-linked records are locatable. This
establishes text location, not that the cited text supports the accusation.

## The two evidence bugs

1. `scripts/accusation_audit.py:visible` reads `item.get('prompt', '')` or
   `item.get('full_prompt', '')`. Prepared items instead store **`original_prompt`**.
   Consequently all 237 legacy B2 reviewer records contain `full_prompt: ""`, even
   though the judge received a nonempty original prompt. This makes the proposed
   human review invalid for those records: it withholds relevant evidence the
   judge actually saw.
2. The same `fields` object is passed to `locate` for both quotation types, with
   `_primary` always set to the CoT. Context quotations are therefore checked
   against the trace, and quotations of the question are called wrong-field
   quotations. The actual rubric explicitly permits `context_quote` from the
   **question/original_prompt**, and allows an empty string when unavailable.
   The frozen parser implements exactly this rule. A separately named input field
   called `context` was never required.

Thus the claim that restricted judges were forced to populate a context field
with no legitimate referent is false. Quoting the question was permitted, and
empty quotations were permitted. The full-context 63% figure results primarily
from omitting the original prompt during the audit, not evidence of increased
paraphrasing by the judge.

## Corrected counts on the identical legacy records

To isolate the correction, these counts retain Claude's same 473 records and
their IDs: A2 236 and B2 237. They do not use the differently deduplicated repaired
reviewer packet as the denominator.

| Context-quotation location | Restricted A2 | Full B2 |
|---|---:|---:|
| Exact span in permitted question/original prompt | 189 | 229 |
| Whitespace-only difference in permitted evidence | 1 | 6 |
| Exact text in another supplied field | 24 | 0 |
| Judge instructions quoted as record evidence | 11 | 0 |
| Empty quotation | 9 | 0 |
| Not located by these checks | 2 | 2 |
| Total legacy records | 236 | 237 |

In B2, **150/237 (63.3%) reported unlocated becomes 2/237 (0.8%)**. Of the 237,
229 are literal matches and another six only differ in whitespace. A2 still has
real wrong-field and instruction-as-evidence problems; these are distinct from
fabrication or semantic validity. The two residual unlocated quotations in each
arm still require inspection and are not a hallucination count.

This repair does not change the original pilot's strict per-output quotation
failure rates, AUROCs or paired effects. Different record definitions explain why
these counts do not have the earlier 210-outputs-per-arm denominator.

## The units and repeat interpretation also need correction

The legacy script emits records for evidence pairs whenever evidence is present,
including assessments with **no supported violation**. Of its 473 records, 192
(91 A2, 101 B2) contain no supported-violation component. Calling all 473 distinct
accusations is inaccurate. Moreover, one rationale can discuss multiple claims
and be repeated over two evidence pairs. These are quote-linked assessment
records, not independently identified atomic accusations.

The deduplication key includes rationale wording and quotation wording. Its
"five records appear in all three repeats" statistic therefore measures exact
normalized wording/bundle recurrence, not semantic accusation stability. It
cannot support the conclusion that the judge almost never repeats its accusation.

For comparison, directly across the 70 response triplets in each arm:

| Agreement across all three repeats | A2 | B2 |
|---|---:|---:|
| False-process decision code | 60/70 (85.7%) | 63/70 (90.0%) |
| Entire five-component decision vector | 39/70 (55.7%) | 51/70 (72.9%) |
| Exactly identical rationale text | 0/70 | 4/70 |

Code agreement also does not prove identical semantic claims or correct judgments.
It simply shows why textual recurrence, decision stability and semantic agreement
must be reported separately. Previously inspected stable false accusations remain
valid examples of reasoning errors despite accurate quotations.

The legacy script truncates normalized rationales to 400 characters; four source
outputs exceed this limit. Human reviewers should receive complete rationales.
It also has no input/artifact manifest and silently permits output overwrites.
The new repair closes those provenance gaps without changing the historical files.

## Repair performed

New script: `scripts/repair_accusation_audit.py`.
Outputs: `results/accusation_audit_repair/2026-09-14-final/`.

- Revalidates all 840 frozen requests, unique API responses, raw parsing, model
  identity, completion hash and input/code identity.
- Reconstructs evidence from the actual request schema and checks equality with
  the judge's complete user-message JSON for all 420 component calls. Missing
  full-context prompts fail rather than silently becoming empty strings.
- Saves corrected location classifications for every legacy record, preserving
  its ID and contributing request IDs.
- Creates **392 complete qualitative assessments** covering all 420 component
  outputs exactly once through recorded multiplicity. Deduplication uses the
  full rationale, component decisions, evidence status and complete quote bundle
  within each response/arm. Numeric score is excluded from the deduplication
  identity, but remains in the unchanged raw output.
- Keeps assessments without accusations as review controls and labels the unit
  accurately. These records are not claimed to be atomic allegations.
- Restores the original prompt in all **191 full-context assessments** in the
  new packet. Restricted records do not gain that prompt. Complete qualitative
  outputs are preserved without truncation.
- Hides native labels, scalar scores, procedure names and repeat counts in the
  reviewer package. It retains the judge's component assertions because they
  are the objects being reviewed. Evidence condition can still be inferred from
  available fields; this is not perfect condition blinding.
- Includes review instructions and the original common rubric. Semantic response
  fields remain blank: no independent human adjudication is claimed.
- Refuses existing output directories and hashes source, code and artifacts.

**Deliver only** the new `reviewer/` directory for independent review. The parent
contains the internal linkage key. The original
`results/accusation_audit/reviewer_packet.jsonl` is superseded and should not be
used to adjudicate full-context accusations.

```sh
python3 scripts/repair_accusation_audit.py \
  --run-dir results/diagnostic_v2/pilot-4arm-rep3c \
  --prepared results/diagnostic_v2/prepared \
  --legacy-dir results/accusation_audit \
  --output-dir results/accusation_audit_repair/NEW-UNUSED-DIRECTORY
python3 -m unittest discover -s tests -v
```

All **45 tests pass**, including six regressions for the actual prompt key,
restricted evidence boundaries, permitted question citations, wrong-field and
instruction citations, and full-rationale identities. Independent checks confirm
all reviewer evidence equals source input, all 420 qualitative outputs are
preserved, and literal A2/B2 context matches are exactly 189/229 on legacy units.
All manifest hashes match. Supplemental
`independent-validation.json` records these checks; it is separate from the
script-generated artifact manifest.

## Consequences and the next experiment

The broad research direction survives. This new audit provides **no new evidence
that full context increases paraphrasing**, that restricted judges have no valid
context to cite, or that accusations are almost always semantically different on
repeat. Do not design a correction around those false interpretations.

The previously established issues remain: generic native-label inversion, a
paired relative component improvement without established absolute detection,
and inspectable accusations contradicted by correctly quoted evidence. Those
are sufficient reasons to build the controlled experiment already authorized.
Manual inspection of constructed pairs is work to perform, not a new approval
requirement or a reason to leave the experiment unstarted.

Before inference, complete the operational freeze: exact 48 inputs, gold labels
for observable claim/support questions with reasons, both instruction texts,
shared schema, token cap, analysis definitions and manifests. The current protocol
is a high-level design, not yet a complete frozen request plan.

Clarify two points during construction:

1. The indistinguishability control applies only where actual judge payloads are
   identical. Source-attribution pairs can meet it when the changed prompt is
   withheld. Verification-language pairs that change the visible trace do not.
   Identical inputs imply the same input-conditioned distribution, not identical
   finite-sample scores from a stochastic service; a chance difference among
   three calls alone is not proof of leakage.
2. A claimed source attribution in the visible prompt and a claim about an
   unobserved execution event have different evidential requirements. Missing
   execution records must remain unresolved. Also define unsupported-accusation
   denominators and require useful claim/status accuracy so blanket abstention
   cannot count as a successful correction.

Proceed with construction and the bounded experiment after these integrity checks.
There is no need to reinterpret the manuscript again based on this broken audit.
