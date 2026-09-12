# Autonomous diagnostic batch 1

Recorded before inference, following authorization to choose and run needed
experiments autonomously. This batch tests frozen procedures, not another prompt
rewrite optimized against the previous eight examples. No human gold is invented.

## Experiments and bounds

1. **Source-evidence controls:** four authored source-attribution templates. Each
   has two contexts making the same explicit attribution true or false. Cross
   full/restricted evidence with generic/component v2.1 procedures: 32 slots.
   Eight additional full-context cases test disclosed verification intentions
   and explicitly uncertain wrong arithmetic: 16 slots. These latter cases are
   negative controls for fabricated process/source claims, not certified faithful
   internal computations. Truth keys follow literal source values and arithmetic.
2. **Native-label baseline:** 24 distinct development questions, 12 per native
   class, excluding all eight previous smoke question clusters, and restricted
   to traces at most 800 words. Sample with a fixed seed and task/generator/length
   coverage. Run full-context generic B1 and the exact public BonaFide whole-trace
   definition-aware template: 48 slots. Keep the same model, temperature and
   1,024-token output cap. The published template returns a boolean; report its
   balanced accuracy and confusion table alongside generic threshold-50 balanced
   accuracy, with continuous generic AUROC separately. Boolean AUROC is also
   balanced accuracy, not a comparable rich ranking. This is a small exploratory
   pilot on a selected population, not a faithful replication of upstream's
   Gemini model or published AUROC.

Total 96 planned slots, at most 110 HTTP attempts, a 1,800-second whole-run
deadline and 1,024 output tokens per request. Input payload bytes are capped at
800,000 in aggregate before retry. Strict schemas and raw outputs are retained.
Use conservative byte-based pacing, safe rate-limit response headers and bounded
backoff; stop on billing/authentication errors or three consecutive failed
attempts. No Anvil GPU allocation is needed for this batch.

## Interpretation specified before results

For the source-flip controls, primary checks are the direction of the paired
full-context score change and whether the component procedure identifies the
explicit false source attribution. Restricted evidence is byte-identical for
opposite truth values. Cache one actual response per identical payload and reuse
it for both cases; never pay for duplicated requests and then mistake sampling
noise for recovered information. Report both request slots and unique API calls.

For a balanced pair with identical observable evidence and opposite truth,
every deterministic function of that evidence gives the same score. On a balanced
collection where each observable record appears once in each class, the score
distributions are identical and AUROC is exactly 0.5. Expected classification
accuracy cannot exceed 0.5, including randomized rules independent of the hidden
context. This is a construction-specific identifiability result, not a theorem
about the real FaithCoT/BonaFide populations or all possible evidence policies.

Do not treat four templates or near-duplicate controls as independent benchmark
replication. The controls are hand-authored stress tests and permit artifact
shortcuts. Report every template and score instead of a narrow population CI.
For negative controls, report component false-process allegations and generic
scores separately; logical mistakes can legitimately affect other targets.

For native examples, compare paired judgments with 2,000 question bootstrap draws,
report class/source coverage and a count baseline, and retain native-label versus
process-truth distinctions. Frozen previous predictions may be shown only on
these same cases as descriptive context, never substituted for a matched arm.
No procedure gains a new-method claim from this batch. The 807 evaluation cases
remain unopened. Results determine the next bounded experiment; human annotation
and natural independently verifiable examples remain necessary for stronger claims.

## Provenance

Generic/component prompts: `configs/diagnostic-v2.1.json`, unchanged.
Definition-aware template: `configs/bonafide-monitor-reference.json`, pinned
source and SHA256 included. The source's tool-unavailability statement applies
to the native BonaFide setting; that template is not used on synthetic tool logs.
The actual generated request plan and separate truth/sampling key are hash-bound.
Only the payload and opaque request identifier are staged for inference.

Rate handling follows the [official API rate-limit documentation](https://developers.openai.com/api/docs/guides/rate-limits).
Published baseline source: [BonaFide monitor](https://github.com/yoavgur/BonaFide/blob/e5f2a87ecfe590d8aa4c73ba06cd92c39051bf87/metrics/monitor/prompts.py).
