"""Render repaired appendix tables directly from versioned result JSONs."""
import argparse
from pathlib import Path
from reanalysis_common import read_json, sha256


ORDER = [('nli_frac_unsup_ctx', 'Context NLI, unsup. rate'),
         ('neg_nli_mean_ent_ctx', 'Context NLI, neg. entail.'),
         ('nli_frac_unsup_prior', 'Prior NLI, unsup. rate')]


def ci(rec):
    return '[' + ', '.join(f'{v:+.3f}' for v in rec['ci95']) + ']'


def render_grace(r):
    c = r['cohorts']['reviewed']
    a = r['cohorts']['deterministic_only']
    p = r['pooled_all_traces']
    lines = [r'\paragraph{Correctness and coverage.}',
             f"We use conservative exact-answer and explicit-option checks, followed by recorded assistant answer-equivalence review for unresolved responses. This is exploratory review, not independent human gold. Of {p['n']} traces, {a['n']} are resolved automatically; review yields {c['correct']} correct and {c['incorrect']} incorrect answers, leaving {p['n'] - c['n']} unresolved. The checker does not accept first-character matches, answer substrings, or token-overlap scores as correctness labels. Refusals and contradictory commitments are inspected explicitly. Reference answers themselves have not been independently revalidated.",
             r'\paragraph{Correctness-conditioned results.}',
             r'\begin{center}\footnotesize', r'\setlength{\tabcolsep}{3pt}',
             r'\begin{tabular}{@{}lccc@{}}', r'\toprule',
             r'Signal ($\rho$) & Correct & Incorrect & Difference \\', r'\midrule']
    for signal, label in ORDER:
        z = c['signals'][signal]
        lines.append(f"{label} & ${z['correct']['rho']:+.3f}$ & ${z['incorrect']['rho']:+.3f}$ & ${z['correct_minus_incorrect']['delta']:+.3f}$ " + r'\\')
    lines.extend([r'\bottomrule', r'\end{tabular}', r'\end{center}'])
    intervals = [c['signals'][s]['correct_minus_incorrect'] for s, _ in ORDER]
    lines.append('Paired question-bootstrap 95\% intervals for these differences, respectively, are ' +
                 ', '.join('$' + ci(v) + '$' for v in intervals) + '.')
    if all(v['ci95'][0] <= 0 <= v['ci95'][1] for v in intervals):
        lines.append('These comparisons do not resolve a correctness-stratum difference for the tested NLI procedures. The intervals also allow meaningful differences; they do not establish equivalence or a mechanism unique to FaithCoT.')
    lines.append(f"On all {p['n']} traces, independently of correctness checking, context unsupported-rate and negative mean-entailment correlations are " +
                 ', '.join(f"${p['signals'][s]['rho']:+.3f}$" for s, _ in ORDER[:2]) +
                 '. These are pooled grounding associations, not evidence that every detector family transfers.')
    lines.append(r'\paragraph{Sensitivity and limits.}')
    lines.append(f"The automatic-only subset has {a['correct']} correct and {a['incorrect']} incorrect answers; its three regime differences are " +
                 ', '.join(f"${a['signals'][s]['correct_minus_incorrect']['delta']:+.3f}$" for s, _ in ORDER) +
                 '. This subset changes task and answer-form composition substantially and is not an independent replication. We also release task-specific fraction/correlation analyses and every assignment of the unresolved answers; assignment sensitivity does not bound mistakes in resolved reviews.')
    lifts = [v['lift'] for v in c['binary'].values()]
    majority = c['binary']['>=0.5']['lift_interval']
    lines.append(r'The descriptive lift $P(\mathrm{incorrect}\mid\mathrm{unfaithful})/P(\mathrm{incorrect})$ ranges from ' +
                 f"${min(lifts):.2f}$ to ${max(lifts):.2f}$ over the five rules; at at-least-half unfaithful it is ${majority['lift']:.2f}$ " +
                 f"(95\% interval ${ci(majority)}$). The all-steps-unfaithful rule gives an interval ${ci(c['binary']['all']['lift_interval'])}$. " +
                 'Thus the association depends on the aggregation and selected population; evidence for it is not uniformly resolved across rules.')
    stepaucs = [v['auroc']['n_steps'] for v in p['binary'].values()]
    lines.append(f"Length remains associated with the fraction target (step-count $\\rho={p['signals']['n_steps']['rho']:+.3f}$); step-count AUROC ranges from ${min(stepaucs):.3f}$ to ${max(stepaucs):.3f}$ across aggregations. " +
                 'Dataset-by-track conditional pair AUROCs are provided as a separate binary endpoint with pair coverage; they are not adjusted Spearman correlations.')
    return '\n'.join(lines) + '\n'


def render_bonafide(r, exp):
    p, inc = r['paired_all'], r['paired_incorrect']
    lines = [r'\paragraph{Exploratory reconciliation on common responses.}',
             f"We compare cached A/B/C scores and historical GPT-4o scores D on exactly {p['n']} common responses ({p['questions']} questions; {p['unfaithful']} unfaithful, {p['faithful']} faithful). A uses a generic rubric with the full prompt; B uses that rubric with the local hint-stripping rule; C uses our rubric with the full prompt; D uses our rubric with the clean question. B is not an exact implementation of the upstream definition-aware no-hint monitor. All score directions are fixed towards unfaithfulness.",
             r'\begin{center}\small', r'\begin{tabular}{@{}lcc@{}}', r'\toprule',
             r'Arm & AUROC & 95\% interval \\', r'\midrule']
    for arm, v in p['arms'].items():
        lines.append(f"{arm} & {v['auroc']:.3f} & ${ci(v)}$ " + r'\\')
    lines.extend([r'\bottomrule', r'\end{tabular}', r'\end{center}'])
    lines.append('Direct paired differences are ' + '; '.join(
        f"{name}: ${p['paired_contrasts'][name]['delta_auroc']:+.3f}$, ${ci(p['paired_contrasts'][name])}$"
        for name in ['A-B', 'A-C', 'C-D']) +
        '. These intervals do not establish a context or rubric remedy, nor equivalence. A on its larger, unmatched sample is descriptive only.')
    v = inc['paired_contrasts']['B-D']
    lines.append(f"On the {inc['n']} common incorrect answers, A/B/C/D AUROCs are " +
                 '/'.join(f"{inc['arms'][a]['auroc']:.3f}" for a in 'ABCD') +
                 f". B minus D is ${v['delta_auroc']:+.3f}$ (${ci(v)}$), an exploratory nominal interval among multiple contrasts involving a historical comparator; this is not independent evidence of a general correction method.")
    lines.append(f"The reconciliation exposes {len(exp['evaluation_scored_rids'])} of the original {exp['evaluation_n']} evaluation responses across {exp['evaluation_scored_questions']} question clusters; {exp['evaluation_responses_sharing_scored_questions']} evaluation responses share those clusters. We retain that split and flag exposure. The seven correct answers lie outside the split's incorrect-answer population. Legacy scores lack raw judge outputs and exact request provenance, so these analyses cannot validate quoted rationales or attribute differences solely to evidence access.")
    return '\n'.join(lines) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--grace-result', required=True, type=Path)
    p.add_argument('--bonafide-result', required=True, type=Path)
    p.add_argument('--exposure', required=True, type=Path)
    p.add_argument('--output-dir', required=True, type=Path)
    a = p.parse_args()
    a.output_dir.mkdir(parents=True, exist_ok=True)
    for name, source, content in [
        ('grace_reanalysis.tex', a.grace_result, render_grace(read_json(a.grace_result))),
        ('bonafide_reconciliation.tex', a.bonafide_result, render_bonafide(read_json(a.bonafide_result), read_json(a.exposure)))]:
        (a.output_dir / name).write_text('% Rendered from versioned results; do not edit numbers by hand.\n% Source SHA256: ' + sha256(source) + '\n' + content)
        print(a.output_dir / name)


if __name__ == '__main__':
    main()
