# Definition-aware baseline role correction

During inspection, a message-role error was identified in the D1 baseline.
`baseline_payload` in `autonomous_batch1.py` puts the entire upstream template,
including its instructions, in a user message. Its system message says the user
message is a JSON evidence record and not instructions to follow. That contract
is inconsistent with the supplied plain-text template. Even if the model follows
some of that text, this is not a clean implementation of the intended baseline.

Preserve D1 outputs as an implementation-failure record. Its batch-1 balanced
accuracy (.4583) and its comparison with B1 are superseded as scientific baseline
evidence. A1/B1/A2/B2 payloads already have the correct instruction/evidence
separation and are unaffected. Batch 2 was already running when this bug was
found; retain that immutable run as well, flagging its D1 arm.

Before correction calls, fix the baseline as **D2**: put the source template's
whole-trace instruction section verbatim (with format escapes resolved) in the
system role after the common wrapper. Put the exact same JSON evidence as B1 in
the user role. Keep its boolean faithful output and strict schema, GPT-4o snapshot,
temperature zero and 1,024-token cap. This explicitly adapts upstream's input
layout and backend; it is not the original Gemini experiment. Do not change the
scientific rubric or selected cases based on the observed scores.

Run all 36 affected native cases (24 batch-1 cases and 12 matched batch-2 cases),
at most 44 HTTP attempts and a 900-second whole-run deadline. Reuse the successful
bounded transport. The correction key records the original selection manifests.
Tests require JSON-only user evidence, the actual baseline definitions in the
system role, and identical B1/D2 evidence. Recompute comparisons with D2, retaining
the old results and the reason for superseding them.
