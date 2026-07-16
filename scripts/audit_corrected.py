"""Corrected audit + two-regime frontier from rigorous_features.json (regime = ACTUAL ft, not the
README-inverted flag). Writes results/audit_corrected.json for the reframed Tables 1/2 + new ft3v4 table."""
import json, numpy as np, collections
rows=json.load(open('results/rigorous_features.json'))
def auroc(s,t):
    s=np.asarray(s,float); t=np.asarray(t,float)
    o=np.argsort(s,kind='mergesort'); r=np.empty(len(s)); x=s[o]; i=0
    while i<len(x):
        j=i
        while j+1<len(x) and x[j+1]==x[i]: j+=1
        r[o[i:j+1]]=(i+1+j+1)/2.0; i=j+1
    n1=t.sum(); n0=len(t)-n1
    return (r[t==1].sum()-n1*(n1+1)/2)/(n1*n0) if n1>0 and n0>0 else float('nan')
def ci(s,t,B=2000):
    rng=np.random.default_rng(0); v=[]
    for _ in range(B):
        i=rng.integers(0,len(s),len(s))
        if len(np.unique(t[i]))<2: continue
        v.append(auroc(s[i],t[i]))
    return np.percentile(v,[2.5,97.5])
keys=['correct','soft','nli_mean_ent','nli_min_ent','nli_n_unsup','nli_frac_con','dag_lin','dag_maxlb']
comp=[r for r in rows if all(r.get(k) is not None for k in keys)]
out={}
def block(name, R, y):
    print(f"\n== {name} (n={len(R)}, pos={int(sum(y))}) ==")
    res={}
    sigs=[("incorrectness","ft_incorrect",1),("soft_raw","soft",1),("soft_intended","soft",-1),
          ("nli_n_unsup","nli_n_unsup",1),("nli_mean_ent","nli_mean_ent",-1),
          ("dag_lin","dag_lin",-1),("dag_maxlb","dag_maxlb",1),("interventions","avg_impact",1)]
    for lbl,k,sgn in sigs:
        if k=="ft_incorrect": s=np.array([1.0 if r['ft'] in (1,2) else 0.0 for r in R])
        elif R and R[0].get(k) is None: continue
        else: s=np.array([sgn*float(r[k]) if r.get(k) is not None else 0.0 for r in R])
        a=auroc(s,y); lo,hi=ci(s,y); res[lbl]={"auroc":float(a),"ci":[float(lo),float(hi)]}
        print(f"   {lbl:16s} {a:.3f} [{lo:.3f},{hi:.3f}] {'SIG' if lo>0.5 or hi<0.5 else 'ns'}")
    return res
yy=np.array([r['y'] for r in comp],float)
out['full_audit']=block("FULL AUDIT vs human label", comp, yy)
inc=[r for r in comp if r['ft'] in (1,2)]
out['incorrect_regime']=block("INCORRECT regime ft1v2 (was mislabeled 'correct')", inc, np.array([1.0 if r['ft']==2 else 0 for r in inc]))
cor=[r for r in comp if r['ft'] in (3,4)]
out['correct_regime']=block("CORRECT regime ft3v4 (the TRUE post-hoc-on-correct)", cor, np.array([1.0 if r['ft']==4 else 0 for r in cor]))
# inversion within correct regime
sf=np.array([r['soft'] for r in cor]); yf=np.array([1.0 if r['ft']==4 else 0 for r in cor])
d=sf[yf==1].mean()-sf[yf==0].mean()
out['inversion_correct_regime']={"mean_diff":float(d)}
print(f"\ninversion within ft3v4: mean soft(unf)-soft(faith) = {d:+.3f}")
json.dump(out, open('results/audit_corrected.json','w'), indent=2)
print("\nAUDIT_CORRECTED DONE")
