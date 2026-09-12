# UR2PhD working instructions

Read [CURRENT_STATE.md](CURRENT_STATE.md) before research or implementation.
It supersedes interpretations in historical `CLAUDE.md`, proposals, notes, and
old commit messages. Preserve those records rather than silently rewriting them.

Reusable local skills: `$ur2phd-research` and `$ur2phd-compute` under
`~/.codex/skills/`. They contain the dataset, session and server context. Host
details and credential locations stay local; do not publish complete sessions.

## Scientific invariants

- FaithCoT types 1/2 are incorrect; 3/4 correct. Binary and four-way-derived
  faithfulness fields disagree on some responses; name the field used.
- BonaFide unit: question ID + generator + exact trace. Require that response's
  explicit whole label; absent whole labels are not faithful labels.
- Current BonaFide whole-label data do not support a correct-answer AUROC.
- Native labels, logical validity, process-claim truth, and causal dependence
  are different endpoints. Reliance alone is not unfaithfulness.
- Preserve original frozen predictions and splits. New work uses versioned
  manifests and output directories, question-grouped evaluation, and paired
  uncertainty where comparisons use the same examples.
- No label, correct answer, annotation rationale, score or selection metadata
  enters a judge prompt. Legitimate original prompts are allowed only in the
  declared full-context condition.
- Later text re-encoding is not original generation-state access. Correlation,
  null significance, or failed transfer does not identify an internal mechanism.

## Execution and handoff

Check current branch, upstream divergence and changes before editing. Do not
overwrite unrelated work or frozen results. Preserve the existing untracked
`paper/figs/_arxiv_p1.png`. Omit assistant co-author/generated-by trailers;
do not rewrite shared history to remove old ones.

Keep experiment code and nonsecret configs in the repo. Save run hashes,
model identity, usage, errors, completion status and resumable records. Check
allocation balance and an actual small end-to-end run before a large submission.
Never treat a transient empty scheduler query as proof of successful completion.

Record findings and unfinished work in a dated `notes/` entry and update
`CURRENT_STATE.md`. New evidence may change the plan; change it explicitly.
