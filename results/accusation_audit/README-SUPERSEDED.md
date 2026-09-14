# SUPERSEDED — do not use this packet for adjudication

Generated 2026-09-14 by the original `scripts/accusation_audit.py`, which had two evidence bugs
(see `notes/2026-09-14-accusation-audit-independent-repair.md`): every full-evidence record here
carries an EMPTY prompt although the judge received one, and context quotes were checked against
the trace instead of question/original_prompt. `reviewer_packet.jsonl` therefore withholds
evidence the judge actually saw and must not be given to a reviewer.

Use instead: `results/accusation_audit_repair/2026-09-14-final/reviewer/packet.jsonl`
(392 complete assessments over all 420 component outputs, with a manifest).

Files here are preserved unchanged for provenance only.
