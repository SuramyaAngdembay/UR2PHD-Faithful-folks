# 2026-08-17 — Presentation "spine" blueprint (filed for TMLR revision round, NOT applied)

Post-freeze GPT review: technical limitations all known/disclosed ("limitations on
generalization, not defects in the central experiment"); main critique = presentation.
Adjudication: directionally valid (3rd reviewer to flag density) but full restructure
rejected at freeze — apply DURING TMLR revision if actual reviewers echo it.

## The six-step spine (use to restructure if revision demands)
1. Aggregate faithfulness detection is misleading (incorrectness ~ predictive).
2. Why: correctness partitions the task (metrics modest on correct, fail on incorrect).
3. Why metrics behave this way: step-removal = answer-reasoning coupling; inverts.
4. Is the hard regime information-free? No: internals carry signal (+ judge partial).
5. Can we manufacture training data? Not automatically: instructed decodable but
   no transfer; some hint-flip data transfers.
6. Prescriptions: stratify by correctness; transfer-validate synthetic data.

## Concrete moves (ranked by value/risk if unfrozen)
- S5: move NLI-length decomposition detail to App H, keep conclusion + 1 stat.
- Intro: compress 4 roadmap paragraphs -> 1 (story currently told 3x pre-related-work).
- S7 opening: add construct-validity thesis sentence ("synthetic detectability is not
  construct validity") or rename section accordingly.
- Fig 2 -> S7.2 (where hint construction is introduced).
- S8: trust Results; cut re-proofs, keep interpretation.
- Target: -1 to -2 main-text pages without removing evidence.

## Status notes
- GRACE (2606.16151): STILL unreleased (anonymous.4open.science 401, 2026-08-17).
  If it drops: stratified replication there = top-value technical addition.
- Freeze holds (bbdcf1c). Review's own advice: "would not add many more experiments."
