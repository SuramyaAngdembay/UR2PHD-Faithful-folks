# ARR / *ACL submission — construct-validity reframe

Reframed from the TMLR build (`paper/tmlr/main.tex`) after the TMLR desk rejection.
**All numbers, tables, figures and claims are unchanged**; what changed is the framing.

- **Title:** The Cleanest Construction Is the Least Valid: Construct Validity for
  Chain-of-Thought Faithfulness Detection
- **Thesis:** within-distribution detectability is not construct validity. The four
  findings (metric inversion, two regimes, construction transfer, label mismatch) are
  presented as instances of one measurement-validity claim, with the construction
  transfer result promoted from §7/§8.3 to contribution (1).
- **Structure:** Part I (what behavioral detection measures) -> Part II (where it fails)
  -> Part III (do constructions measure the real phenomenon) -> Discussion led by
  construct validity + three prescriptions.

## Build
`tectonic main.tex` (or pdflatex+bibtex). Style files from acl-org/acl-style-files.
Modes in `\usepackage[review]{acl}`: `review` (anonymous, default), `preprint`, `final`.

## Compliance
17 pages total; main content ends 71% down page 8 (ACL long-paper limit: 8 pages of
content; Limitations, Ethics, references and appendices are excluded). 0 unresolved
references, anonymous in review mode.
