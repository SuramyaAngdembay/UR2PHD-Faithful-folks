# Metadata visibility-comment intervention

Recorded after the matched results and before ablation calls. The component
judge with full evidence calls two native-faithful traces unfaithful because
they used allegedly inaccessible metadata. The original prompt actually contains
that metadata, preceded by a comment saying it should not be accessible. Both
traces openly acknowledge reliance. This suggests a concrete interpretation
error, not merely a globally weak reader.

Test one intervention: remove only the exact HTML visibility comment from the
original prompt, preserving the question, metadata fields and answer cue, full
trace and final answer. Freeze the v2.1 B2 rubric. For each case issue two actual
unchanged-original requests and one comment-removed request, in randomized order.
The duplicate originals estimate ordinary within-protocol variation and must not
be deduplicated. Request IDs distinguish repeats; no repeat identifier is sent
to the model. This is a presentation intervention, not alteration of the actual
historical execution or an instruction-following success target.

Use the two discovery cases plus 12 question-distinct fresh development cases
containing the exact comment, at most 800 words, excluding every previously
scored question from the smoke and native pilots. The fixed coverage selection
uses seed 20260915. Report discovery and fresh groups separately; do not pool
the examples that motivated the hypothesis into a validation headline.

Primary descriptive outcome on fresh cases: mean score(comment removed) minus
mean of the two original scores, with 2,000 question bootstrap draws. Compare
that change with the absolute difference between original repeats. Also report
the specific false-process component and every case, since score movement alone
does not establish improved validity. Native classes are descriptive selection
metadata and remain outside the judge. No native AUROC optimization is intended.

42 planned calls, maximum 50 HTTP attempts, 1,100-second total deadline and
1,024-token output cap. The role-corrected definition-aware baseline and the
matched run have finished; this batch uses the same rate-aware transport.
Neither a null nor a positive outcome identifies all causes of cross-dataset
failure. A positive outcome motivates a fresh evidence-presentation study; it
does not establish that removing relevant context is a general remedy.
