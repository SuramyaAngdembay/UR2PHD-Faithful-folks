"""
VERIFICATION: recompute every paper number derivable from committed artifacts, in one run.
Run from repo root:  python3 scripts/paper_numbers.py
Each block prints [PAPER] the value as it appears in the manuscript and [RECOMPUTED] the value
derived fresh from results/*.json. Numbers that require the Aquaman-only .npz caches are listed
at the end with their server-side script + log locations instead.
"""
import json, re
import numpy as np

def auroc(s, t):
    s = np.asarray(s, float); t = np.asarray(t, float)
    order = np.argsort(s, kind='mergesort'); r = np.empty(len(s))
    sv = s[order]; i = 0
    while i < len(sv):
        j = i
        while j + 1 < len(sv) and sv[j+1] == sv[i]: j += 1
        r[order[i:j+1]] = (i+1 + j+1) / 2.0; i = j + 1
    n1 = t.sum(); n0 = len(t) - n1
    return (r[t == 1].sum() - n1*(n1+1)/2) / (n1*n0)

def boot_ci(s, t, B=2000, seed=0):
    rng = np.random.default_rng(seed); v = []
    s = np.asarray(s, float); t = np.asarray(t, float)
    for _ in range(B):
        i = rng.integers(0, len(s), len(s))
        if len(np.unique(t[i])) < 2: continue
        v.append(auroc(s[i], t[i]))
    return np.percentile(v, [2.5, 97.5])

rows = json.load(open('results/rigorous_features.json'))

print("=" * 72)
print("TABLE 1 (audit, n=633 complete-feature) + Figure 2 left panel")
print("=" * 72)
keys = ['correct','soft','nli_mean_ent','nli_min_ent','nli_n_unsup','nli_frac_con','dag_lin','dag_maxlb']
comp = [r for r in rows if all(r.get(k) is not None for k in keys)]
y = np.array([r['y'] for r in comp], float)
print(f"n={len(comp)} (paper says 633)")
audit = [("correctness (=>unf)", 'correct', 1, "0.696 [0.662,0.734]"),
         ("soft inverted",       'soft',    1, "0.651 [0.611,0.695]"),
         ("soft intended",       'soft',   -1, "0.349 [0.305,0.389]"),
         ("NLI # unsupported",   'nli_n_unsup', 1, "0.569 [0.523,0.615]"),
         ("NLI mean entailment", 'nli_mean_ent',-1, "0.493 [0.447,0.538]"),
         ("NLI contradiction",   'nli_frac_con', 1, "0.507 [0.461,0.554]"),
         ("DAG linearity",       'dag_lin',     -1, "0.530 [0.483,0.577]"),
         ("DAG max lookback",    'dag_maxlb',    1, "0.543 [0.496,0.588]")]
for name, k, sgn, paper in audit:
    s = np.array([sgn * float(r[k]) for r in comp])
    a = auroc(s, y); lo, hi = boot_ci(s, y)
    print(f"  {name:22s} [PAPER] {paper:22s} [RECOMPUTED] {a:.3f} [{lo:.3f},{hi:.3f}]")

print()
print("=" * 72)
print("METRIC INVERSION (+0.139 [+0.096,+0.182]) — Part I")
print("=" * 72)
yy = np.array([r['y'] for r in rows], float)
ss = np.array([np.nan if r.get('soft') is None else float(r['soft']) for r in rows])
m = ~np.isnan(ss)
d = ss[m][yy[m]==1].mean() - ss[m][yy[m]==0].mean()
rng = np.random.default_rng(0); v = []
for _ in range(2000):
    i = rng.integers(0, int(m.sum()), int(m.sum()))
    ti, si = yy[m][i], ss[m][i]
    if len(np.unique(ti)) < 2: continue
    v.append(si[ti==1].mean() - si[ti==0].mean())
lo, hi = np.percentile(v, [2.5, 97.5])
print(f"  [PAPER] +0.139 [+0.096,+0.182]   [RECOMPUTED] {d:+.3f} [{lo:+.3f},{hi:+.3f}]")

print()
print("=" * 72)
print("TABLE 2 (frontier, correct-answer traces) + Figure 2 right panel")
print("=" * 72)
fr = [r for r in rows if r.get('soft') is not None and r.get('avg_impact') is not None and r.get('ft') in (1, 2)]
y_h = np.array([r['y'] for r in fr], float)               # human label (paper target)
y_ft = np.array([1.0 if r['ft'] == 2 else 0.0 for r in fr])  # caption's alt target
print(f"n={len(fr)} (paper says 270); label agreement y vs ft2: {(y_h==y_ft).mean():.2f} (paper says 91%)")
front = [("answer-tracing (soft)", 'soft', "0.545 [0.468,0.611]"),
         ("interventions (avg_impact)", 'avg_impact', "0.485"),
         ("NLI (# unsupported)", 'nli_n_unsup', "0.514"),
         ("DAG (max lookback)", 'dag_maxlb', "0.490")]
for name, k, paper in front:
    missing = sum(1 for r in fr if r[k] is None)
    assert missing == 0, f"{k}: {missing} missing in subset -- extend the filter, do not impute"
    s = np.array([r[k] for r in fr], float)
    a = auroc(s, y_h); a2 = auroc(s, y_ft); lo, hi = boot_ci(s, y_h)
    print(f"  {name:26s} [PAPER] {paper:20s} [RECOMPUTED] {a:.3f} [{lo:.3f},{hi:.3f}]  (ft-target: {a2:.3f})")

print()
print("=" * 72)
print("TABLE 4 + FIGURE 3 (instructed construction, 7 models)")
print("=" * 72)
order = [("Qwen-2.5-7B","qwen"),("Gemma-4-12B","gemma4"),("Llama-3.1-8B","llama"),("Qwen3-8B","qwen3"),
         ("DeepSeek-R1-Dist.-7B","deepseek"),("Gemma-2-9B","gemma"),("DeepSeek-R1-0528-8B","dsr0528")]
for disp, k in order:
    d = json.load(open(f'results/synth_{k}.json'))
    print(f"  {disp:22s} n={d['n_posthoc']:3d}  held-out {d['wb_heldout_auroc']:.3f}  "
          f"perm p={d['wb_perm_p']:.3f}  surface {d['black_box']['surface_auroc']:.3f}")

print()
print("=" * 72)
print("HINT TESTBED (7.2): decodability + inversion with counterfactual labels")
print("=" * 72)
for k in ("llama", "qwen"):
    d = json.load(open(f'results/synth_{k}_hint.json'))
    print(f"  {k:6s} held-out {d['wb_heldout_auroc']:.3f} (paper 0.752/0.835)  perm p={d['wb_perm_p']:.3f}  "
          f"surface {d['black_box']['surface_auroc']:.3f} (paper 0.626/0.703)")
    print(f"         soft intended {d['black_box']['soft_auroc_intended']:.3f} (paper 0.389/0.251)")
ci = json.load(open('results/hint_inversion_ci.json'))
for k, v in ci.items():
    print(f"  {k:6s} inversion CI [RECORDED] {v['soft_intended_auroc']:.3f} [{v['ci'][0]:.3f},{v['ci'][1]:.3f}]")

print()
print("=" * 72)
print("TABLE 5 + FIGURES 4-5 (three-way bridge)")
print("=" * 72)
for k in ("llama", "qwen"):
    b = json.load(open(f'results/bridge3_{k}.json'))
    print(f"  {k}: own-best layers " + ", ".join(f"{n}=L{v['layer']}(CV {v['cv']:.3f})" for n, v in b['own_best'].items()))
    for pair, tv in b['transfers'].items():
        print(f"     {pair:22s} best {tv['best']:.3f} @L{tv['best_layer']}  mean {tv['mean']:.3f}")
    p = json.load(open(f'results/bridge3_perm_{k}.json'))
    print(f"     perm: layer-mean {p['obs_layer_mean']:.3f} p={p['p_layer_mean']:.3f} | "
          f"best {p['obs_best']:.3f} p={p['p_best']:.3f}")
rb = json.load(open('results/transfer_robust_llama.json'))
print("  robustness (no-PCA / test-scaler):", {k: round(v, 3) for k, v in rb.items()})

print()
print("=" * 72)
print("AQUAMAN-ONLY NUMBERS (need ~/wbrep_*.npz / ~/synth on the server)")
print("=" * 72)
print("""  Table 3 (real-label probes): scripts/wb_probe_a.py (CV+perm), wb_probe_ed.py (held-out+LODO),
     whitebox_probe_v2.py (pilot p) -> run on Aquaman; caches ~/wbrep_llama.npz, ~/wbrep_qwen.npz
  Table 6 / steering (0.22 vs 0.08): scripts/wb_causal_c.py -> Aquaman log + notes/2026-07-02-whitebox-causal-c.md
  Extraction validation (0.82/0.79 vs 0.57): scripts/validate_extraction_llm.py, validate_extraction.py
  Interventions g=0.56-0.61: scripts/intervention_harness_v2.py -> results/intervention_v2_results.json
  Circularity rho=0.87: scripts/analyze_human_label.py + notes/2026-06-25-finding-human-label-baseline.md
  Fig 4 FaithCoT curve: results/faithcot_perlayer.json (recompute: snippet in notes / bridge3.py curves)""")
print("\nDONE — every [RECOMPUTED] value should match its [PAPER] value.")

print()
print("=" * 72)
print("REVIEW-RESPONSE RERUNS (2026-07-15)")
print("=" * 72)
import json as _j
gn = _j.load(open('results/grouped_nested.json'))
for k, v in gn.items():
    key = 'grouped_nested_auroc' if 'grouped_nested_auroc' in v else 'nested_auroc'
    print(f"  {k:22s} nested {v[key]:.3f} +/- {v['std']:.3f}")
eb = _j.load(open('results/embed_baseline.json'))
for k, v in eb.items(): print(f"  embed-LR {k:16s} n={v['n']:4d} AUROC {v['auroc']:.3f}")
for m in ('llama','qwen'):
    q = _j.load(open(f'results/qonly_{m}.json'))
    print(f"  qonly {m}: best CV {q['qonly_best_cv']:.3f} @L{q['qonly_best_layer']}")
    s = _j.load(open(f'results/strict_{m}.json'))
    print(f"  strict {m}: n_ph {s['n_posthoc_strict']}, within CV {s['within_cv_best']:.3f}, "
          f"transfer mean {s['transfer_mean']:.3f} p={s['p_mean']:.3f} | best {s['transfer_best']:.3f} p={s['p_best']:.3f}")
    fs = _j.load(open(f'results/flip_stability_{m}.json'))
    strict = sum(1 for r in fs if not any(r['resample_correct']))
    print(f"  flip-stability {m}: {strict}/{len(fs)} fail both resamples ({strict/len(fs):.1%})")
for m in ('llama','qwen'):
    qt = _j.load(open(f'results/qonly_transfer_{m}.json'))
    print(f"  qonly-TRANSFER {m}: mean {qt['qonly_transfer_mean']:.3f} p={qt['p_mean']:.3f} | "
          f"best {qt['qonly_transfer_best']:.3f} p={qt['p_best']:.3f}  (difficulty-carrier control)")
