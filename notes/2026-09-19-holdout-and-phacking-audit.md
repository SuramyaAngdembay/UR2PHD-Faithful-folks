# Held-out integrity and p-hacking audit (2026-09-19)

Prompted by the user after the AI-scientist-pitfalls self-audit. Method follows the
research-claim-triage discipline: classify before fixing, trace every downstream copy, and label
every claim **Verified** (a check ran and fails on the broken version) / **Measured** (produced
under stated conditions, nothing independent confirms it) / **Assumed** (believed, unchecked).
Claims about our own process start at Assumed.

---

## 1. THE HEADLINE CORRECTION — the eval partition was never held out

**Verified.** `results/bonafide_predictions.json` is a 1,120-row list carrying `judge4o`, `judgeA`,
`judgeB`, `nli_n_unsup`, `pi` for **every** response — all 306 dev and all **807 eval**. The frozen
BonaFide evaluation then ran its hypothesis tests on **n=1113** (`bonafide_results.json`:
`population.incorrect.n = 1113`), i.e. the whole incorrect-answer population, dev and eval together.

**Verified, from commit timestamps:**

| time | commit | event |
|---|---|---|
| 2026-09-09 **20:38** | `2687226` | Frozen BonaFide eval unblinded; H1/H2/H3 computed on n=1113 |
| 2026-09-09 **23:45** | `9592772` | `dev_clusters.json` — the dev/eval split — first created |

**The split was created three hours after the population had been scored and hypothesis-tested in
full.** `frozen-eval-spec.md` contains no mention of a dev/eval partition, because none existed
when it was written. So the eval partition is not a holdout that was later contaminated; **it was
carved out of already-scored data.**

### Correcting my own figure from earlier today

The self-audit note (`f2af84d`, already pushed, and stated to the user in conversation) reported
**284/807 (35%) touched, 483 (60%) cluster-contaminated**. That is **wrong and far too low**. The
correct figure is **807/807 (100%) scored, 425/425 clusters, 100% cluster contamination.**

Cause — **Engineering** (a test can fail on the broken version): my sweep iterated
`results/**/*.jsonl` plus `dict['rows']` for `.json` files. `bonafide_predictions.json` is a
top-level JSON **list**, so it matched neither branch and was silently skipped. The corrected sweep
recurses into lists and dicts for any `rid` key. This is the skill's "vacuous check" failure mode:
a check that reported success because it never examined the relevant file.

### What "held out" can still honestly mean

**Verified** by artifact mapping: of 27 BonaFide-derived artifacts, exactly five touch eval —
`bonafide_pop.json`, `bonafide_predictions.json`, and `reconcile_A/B/C.jsonl` — plus the audit
packet key. **Every `diagnostic_v2` run (pilot, replication, v1, v1.3, accusation audits) is
dev-only.**

So the eval partition is a **procedure-specific holdout**: unexposed to the diagnostic-v2 component
and verification procedures, which did not exist on 2026-09-09. It is **not** a holdout for
`judge4o`, `judgeA`, `judgeB`, `nli_n_unsup` or `pi`, all of which were scored on it and used in a
completed hypothesis test.

Consequences:
- Any future eval-partition claim must name the procedure and state that the holdout is specific
  to it.
- The analyst-knowledge channel is **not** closed by that narrowness: we know the frozen eval's
  results on this exact data.
- **Engineering vs logic:** the un-tracked exposure was engineering (now fixed). The fact that the
  split postdates full scoring is **logic** — no code change undoes it. The claim must narrow.

---

## 2. P-HACKING SELF-ASSESSMENT

Checked against the standard researcher-degrees-of-freedom failure modes. Each verdict carries its
evidence.

### 2.1 Selective reporting / file drawer — **CLEAN (Verified)**

Test: for all 116 top-level result JSONs, extract headline numbers and check whether any appears
(2 or 3 dp) in any note, `CLAUDE.md`, `CURRENT_STATE.md` or the paper.
**Result: exactly one file's numbers never surfaced — `validate3.json`,** an external-accuracy
sanity check (model accuracies vs published ranges, all `within: true`), whose values appear in its
own commit message. No suppressed hypothesis test was found.

A first, cruder version of this check matched *filenames* and flagged 87 files. That was a false
alarm — results are routinely discussed without citing the filename. Recorded because the crude
version would have produced a serious and wrong accusation.

### 2.2 Optional stopping / growing the test family — **CLEAN, and conservative (Verified)**

The transfer grid's 11 artifacts decompose as 8 hypothesis cells + 2 raw-format controls + 1 cache
correction (`hintBc` replacing `hintB`). Commit dates:

- **2026-09-02**: `llama_hint`, `llama_hintL`, `qwen_hint`, `qwen_hintL` (4 cells) — the **positive
  cell is in this first wave** (`llama_hint` Δ +0.1848, p=0.0002).
- **2026-09-07**: the remaining 7 artifacts.

So the family **grew after the positive was known**. That direction matters: every added cell was
null, and Bonferroni was then applied over 8. Enlarging the denominator after a positive makes the
claim *harder*, not easier — the opposite of p-hacking. The positive survives at both m=4
(threshold .0125) and m=8 (.00625), and survives the serialization control
(`hint_rawfmt` Δ +0.1817, p=0.0004).

**Residual, Assumed:** artifacts cannot rule out experiments that were run and never written to
disk. No evidence of this was found; no evidence could rule it out either.

### 2.3 Multiple comparisons in the two-regime table — **CLEAN (Verified)**

The audit table reports 7 signals × 3 strata = 21 nominal 95% intervals with no correction applied.
I tested whether the headline claims survive correction (normal-approximation rescaling of the
bootstrap half-width — **Measured**, not a recomputed bootstrap):

| signal (correct regime) | point | 95% | Bonferroni m=7 | m=21 |
|---|---:|---|---|---|
| soft_raw | .6667 | [.592, .736] | [.568, .765] ✓ | [.555, .778] ✓ |
| interventions | .6591 | [.588, .730] | [.562, .756] ✓ | [.549, .769] ✓ |
| nli_n_unsup | .6259 | [.556, .696] | [.530, .722] ✓ | [.517, .734] ✓ |
| soft_intended (inversion) | .3333 | [.264, .408] | [.235, .432] ✓ | [.222, .445] ✓ |
| dag_maxlb | .5618 | [.491, .634] | includes .5 | includes .5 |

Every claimed result survives correction over 21 comparisons. `dag_maxlb` loses significance but
**was never claimed** — `CLAUDE.md` reports DAG structure as ns. No correction-dependent claim.

### 2.4 Layer selection in the white-box work — **CLEAN (Verified)**

`bridge3_perm_llama.json` stores **both** a selection-free primary (`obs_layer_mean` 0.6157,
`p_layer_mean` 0.01698) and a selection-corrected best (`obs_best` 0.6944, layer 25,
`p_best` 0.0490). Reporting a selection-free statistic as primary is the correct remedy for
best-of-32-layers multiplicity.

### 2.5 HARKing / post-hoc hypotheses — **MIXED, but disclosed (Verified)**

Instances exist and are labelled as post hoc in the text: the note-style hypothesis (v1.3), the
SimpleQA-only sensitivity, the composition-conditioning reading. Against that, **v1.3 recorded a
pre-registered prediction that FAILED** and the failure was published — behaviour a HARKing process
does not produce.

### 2.6 Garden of forking paths — **THE REAL RESIDUAL RISK (Assumed)**

116 top-level result JSONs, ~100 AUROC figures across the notes, and Bonferroni applied inside one
8-cell grid and nowhere else. Individual intervals are nominal. No global error rate is controlled,
and no artifact can reconstruct the analysis decisions that were considered and not taken. This is
the one finding I cannot close with evidence.

---

## 3. CONTAMINATION MAP — what is clean

**Verified by independent recomputation** (a separate AUROC implementation using explicit
discordant-pair counting rather than `rankdata`, run against raw `responses.jsonl`):

| result | recomputed | stored | status |
|---|---|---|---|
| Pilot A1 / A2 | .2175 / .5108 | .2175 / .5108 | **exact match** |
| Replication A1 / A2 | .2767 / .5994 | .2767 / .5994 | **exact match** |
| v1 absent/full judgments, generic | 18 / 4 / 9 / 5 | identical | **exact match** |
| v1 absent/full judgments, verification | 18 / 17 / 1 | identical | **exact match** |
| Two-regime table (all 21 cells) | — | matches `CLAUDE.md` | **verified** |
| bridge3 Llama layer-mean, p | .6157, .01698 | claimed .616, .017 | **verified** |
| GRACE: all 8 stratum differences | — | every CI includes 0 | **verified** |

### CLEAN — usable as-is

1. **Constructed-control experiments (v1, v1.3).** Synthetic data we authored; no partition issue
   can apply. Gold by construction, frozen before inference, analysis hashed. *Caveat, not
   contamination:* v1.3 showed an unbalanced construction variable.
2. **The pilot and the replication (A1/A2 contrast).** Dev-only, **Verified**. Procedures frozen;
   the component rubric text (2026-09-11) predates the reconciliation eval scores (2026-09-12).
3. **The transfer grid and the white-box/bridge line.** FaithCoT and hint-testbed data, no BonaFide
   partition involvement; selection-free primaries; multiplicity handled.
4. **The two-regime audit table.** Survives correction over 21 comparisons.
5. **GRACE reanalysis.** Independent dataset, threshold-free primary, all thresholds reported.

### CONTAMINATED — must carry a scope statement

1. **Everything computed on the BonaFide eval partition** — the frozen eval's H1/H2/H3, the
   reconciliation arms. 100% scored. Not a holdout for those signals.
2. **The pilot/replication samples as "fresh data".** 38/70 replication responses and **18/18 of
   its faithful class** were previously scored. The contrast is still a valid out-of-sample test
   *against the pilot*; it is not unseen data.
3. **Any future eval-partition result**, which must name the procedure it is a holdout for.

### POWER-LIMITED NULLS — correctly framed, but state it

- "Incorrect regime: all black-box at chance." CI half-widths ≈ .07, so an effect of .56 would
  often be missed. This is *not distinguishable from chance at this power*, not established
  absence. The repo's own phrasing ("every signal's CI includes 0.5") is already correct.
- GRACE stratum differences: all CIs include zero with half-widths ≈ .2 — very underpowered.

---

## 4. ACTIONS

1. **Done:** corrected the 35% figure here and in `CURRENT_STATE.md`; corrected in conversation.
2. **Do not describe the BonaFide eval partition as held out** without naming the procedure.
3. **Build the multiplicity ledger** (§2.6) before anything enters the manuscript.
4. **Fix the exposure sweep permanently** — it now recurses all containers; keep it as the check.
5. One trivial drift found: Qwen bridge p stored `0.7402597` (= 741/1001) but reported as
   **0.741** in `CLAUDE.md:130` and `notes/2026-07-11-hint-organic-bridge.md:66,89`. Null either
   way; corrected for hygiene given this project's prior p-value transcription incident.
