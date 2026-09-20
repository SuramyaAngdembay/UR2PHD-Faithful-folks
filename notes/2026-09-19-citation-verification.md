# Citation verification: 17 entries added, 1 corrected, 4 claims narrowed (2026-09-19)

All entries in the block appended to `paper/ur2phd.bib`, `paper/arr/ur2phd.bib` and
`paper/tmlr/ur2phd.bib` were checked against a primary source before being added. "Primary" means
the publisher page, Crossref/PubMed deposited metadata, the ACL Anthology's own BibTeX, an official
conference dataset, or the arXiv record and full text itself. Secondary sources were used only to
locate URLs, never as the basis for a reported field.

Verdict: **every paper is real, every supplied arXiv ID resolves, no fabricated identifiers.**
Four findings change what we are allowed to write, and one existing entry was stale.

## Corrected: `arcuschin2025wild` was stale

Now **published at ICML 2026** (main conference, poster; `Accept (regular)`), not a 2025 preprint.
Confirmed from ICML's own conference dataset (record 64450) and corroborated by the arXiv comments
field, which reads "Published at the 43rd International Conference on Machine Learning (ICML 2026)".
Changed from `@article` to `@inproceedings` in all three bib files. The key is unchanged, so
`\citet` now renders "Arcuschin et al. (2026)"; no prose hard-codes the year beside it.

**Trap avoided:** search results repeatedly asserted "ICLR 2025" and pointed at
`iclr.cc/virtual/2025/32771`. That is a *workshop* paper (ICLR 2025 Workshop on Reasoning and
Planning for LLMs), superseded by the ICML main-conference version. Do not cite the workshop.
PMLR has not posted the ICML 2026 volume, so volume/pages are deliberately omitted rather than
guessed.

## Four corrections that narrow claims we had been making

**1. Matos et al. — F1 is collapsible, but only model-dependently, and the location was wrong.**
Our note said Table 1 and the Appendix. Table 1 is only a glossary; the results are in **Table 2**
and the derivation in **Appendix A.1.9**. The decomposition is real:
`F1 = sum_g w_g F1_g` with `w_g = (2TP_g + FP_g + FN_g) / sum_h (2TP_h + FP_h + FN_h)`.
But the paper explicitly distinguishes **strict** collapsibility (weights depend only on subgroup
properties such as size or prevalence) from **general** collapsibility (weights may be any
identifiable quantity, including the model's own counts). **F1 is labelled "Collapsible
(model-dependent)"**, not strictly collapsible.

  So: "F1 decomposes across strata" is supported. "F1 is the subgroup-size-weighted average of
  per-stratum F1" is **not** supported, because the weights move with the classifier. A referee
  would catch that, and our own earlier verification of `F1_pooled = sum_g w_g F1_g` to 1e-9 was
  verifying the model-dependent-weight form.

  **More useful to us than the F1 result:** the same paper proves **AUC is non-collapsible**,
  decomposing into within- and cross-group terms. That is direct support for the composition thesis
  and is the more citable result.

**2. Oakden-Rayner et al. — not a CheXpert paper, and the arXiv version is a different document.**
"CheXpert" appears exactly once in the CHIL 2020 paper, in the reference list; it is never used as
data. The datasets are CIFAR-100, a hip-fracture radiograph set, MURA, and **CXR14 (NIH
ChestX-ray14)** — the latter carries the pneumothorax/chest-drain spurious-correlate result. Any
text of ours saying CheXpert must say CXR14. Separately, arXiv:1909.12475 is a 6-page ML4H@NeurIPS
2019 extended abstract without the CIFAR-100 experiments; the 9-page CHIL 2020 paper is the
citable one. The term "hidden stratification" is genuinely coined there, verbatim.

**3. Mulherin & Miller — our quotation is truncated mid-sentence, and "stratified ROC curves" is
not verifiable.** The abstract is confirmed verbatim from two independent indexes. Our quoted
fragment ends "...relatively simple stratification procedures." but the source continues
"**, limited primarily by the sample size and the precision of the estimates.**" We dropped exactly
the clause stating the method's limitation, which is the worst clause to drop silently. Restore it
or end with a trailing ellipsis.

  The paper is fully paywalled (no open copy via Unpaywall, PMC, Europe PMC, or the Wayback
  Machine). The abstract confirms ROC curves are among the recommended strategies, but whether
  "stratified" distributes across all three list items is **grammatically ambiguous and could not
  be resolved**. Status: **Assumed, not Verified.** Do not write that they "prescribe stratified
  ROC curves" as a named procedure without pulling the PDF through institutional access. Safe
  phrasing: "outlines strategies using stratified sensitivity and specificity estimates,
  likelihood ratios, and ROC curves."

**4. Kallus & Zhou Proposition 1 — the double sum is stated, not separately proved.** Proposition 1
exists, is numbered 1 in both the arXiv and camera-ready versions, and our formula matches its
first line verbatim. But the proof opens "We show this for the decomposition
`Pr[R1>R0] = sum_a' Pr[A=a'|Y=0] Pr[R1>R0^{a'}]`; the others follow by applying the same argument."
So write "**as stated in** Proposition 1", not "as proved in". (There is also a cosmetic internal
mismatch: the proof announces the Y=0 form and displays the Y=1 form. Present in both versions,
harmless to us.)

## Smaller precision fixes folded into the entries

- **Deviyani & Diaz:** Crossref reports pages 4906–4925 for this DOI and that is **wrong**. The
  Anthology PDF's own printed page numbers are **4921–4940**. Any tooling that auto-pulls from
  Crossref will silently corrupt this entry.
- **Jadidinejad et al.:** not preprint-only. Peer-reviewed as *ACM TOIS* 40(1), Article 4,
  doi:10.1145/3458509. Cite the journal version.
- **Borkan et al.:** the **Companion** proceedings of WWW '19, not the main track.
- **Dehghani et al. (Benchmark Lottery):** no journal-ref, no comments field, DBLP key is CoRR-only.
  A search summary floated "NeurIPS 2021"; no primary evidence was found, so it is marked an
  unrefereed preprint per repo convention.
- **Prost et al.:** no peer-reviewed version found; marked preprint.
- **van Elteren (1960):** the 1960 ISI Bulletin is print-only and not online. Details confirmed
  from two mutually independent secondary sources with byte-identical fields. Status: **Measured,
  not Verified.** Do not confuse it with the 1958 Mathematisch Centrum technical-report precursor.
- **Tseng et al.:** our "0.91 to 0.86" description is accurate, but there are *three* AUCs and 0.87
  is easy to misuse. 0.91 = extreme-spectrum model on its own population; 0.86 = that model
  transferred to the whole-spectrum population (our number); 0.87 = a separately trained
  whole-spectrum model. The authors themselves hedge: "the effect of the bias may be modest in this
  example". Do not present it as dramatic degradation.
- **Janes & Pepe:** the published title spells out "receiver operating characteristic"; do not
  abbreviate to ROC. Distinct from Janes, Longton & Pepe, *Stata Journal* 2009.

## RFEval, the counter-evidence paper, now has an entry

`han2026rfeval` — Han, Lee & Do, ICLR 2026 poster, arXiv:2602.17053. Our description was correct on
every checked point: 7,186 instances (verbatim in the abstract), "output-level counterfactual
interventions" is their own wording, and RFEval is the authors' name. It was cited only in prose in
`related-work-and-positioning.md` and the notes, never in a bib file.

Its headline bites us verbatim: *"accuracy is neither a sufficient nor a reliable proxy for
faithfulness: once controlling for model and task, the accuracy-faithfulness link is weak and
statistically insignificant."* They report unfaithfulness in 49.7% of outputs across twelve
open-source models and seven tasks, driven mainly by stance inconsistency, and find failures track
post-training regime more than scale.

**Two scope distinctions for the response, both readable off their own abstract rather than
inferred:** their labels are intervention-constructed, not human annotations; and their
accuracy-faithfulness null is stated "once controlling for model and task", which is a
model/task-conditioned association rather than an instance-level claim about a fixed annotated
corpus. That does not dissolve the objection, and the "single strongest reviewer objection"
framing in `2026-09-19-stratified-eval-precedent.md` stands.

## Still open

- Mulherin & Miller full text (institutional access) if the stratified-ROC attribution stays
  load-bearing.
- The `jadidinejad2021simpson` article number rests on the Glasgow repository plus an ACM DL
  listing; ACM DL returns 403 to automated fetches. Consistent with Crossref's 1–22 article-level
  pagination.
- `kallus2019xauc` page range 3433–3443 comes from OpenAlex, not the official NeurIPS BibTeX (which
  has empty pages). Omitted from our entry, matching the publisher's own recommended citation.
