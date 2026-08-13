"""Probe the TRUE correct-answer regime (ft3v4) + the same-regime bridge:
  1 within-ft3v4 probe (CV + selection-corrected perm) per model
  2 hint -> ft3v4 transfer (does the hint construction reach its actual same-regime analogue?)
  3 instructed -> ft3v4 transfer (should still fail)
Layer align: acts_*.npz X[l] == wbrep cot_end[:,l+1]. Usage: python ft34_probe.py --mdir llama --nperm 500"""
import argparse, os, json
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
ap=argparse.ArgumentParser(); ap.add_argument("--mdir",required=True); ap.add_argument("--nperm",type=int,default=500)
a=ap.parse_args(); SYNTH=os.path.expanduser("~/synth")
w=np.load(os.path.expanduser(f"~/wbrep_{a.mdir}_ft34.npz"),allow_pickle=True)
fe,fy=w["cot_end"],w["y"]; NLw=fe.shape[1]-1
def pipe(ntr): return make_pipeline(StandardScaler(),PCA(max(2,min(50,ntr-2)),random_state=0),LogisticRegression(max_iter=2000,C=1.0))
def cv(Xl,yy):
    skf=StratifiedKFold(5,shuffle=True,random_state=0); oof=np.zeros(len(yy))
    for tr,te in skf.split(Xl,yy): oof[te]=pipe(len(tr)).fit(Xl[tr],yy[tr]).predict_proba(Xl[te])[:,1]
    return roc_auc_score(yy,oof)
# 1: within ft3v4, per-layer CV + max-over-layers perm
curve=[cv(fe[:,l+1,:].astype(np.float32),fy) for l in range(NLw)]
b=int(np.argmax(curve))
proj=[make_pipeline(StandardScaler(),PCA(min(50,len(fy)-2),random_state=0)).fit_transform(fe[:,l+1,:].astype(np.float32)) for l in range(NLw)]
rng=np.random.default_rng(0)
def maxcv(yy): return max(cv(proj[l],yy) for l in range(NLw))
obs=maxcv(fy); null=[maxcv(rng.permutation(fy)) for _ in range(a.nperm)]
p=(1+sum(n>=obs for n in null))/(1+a.nperm)
print(f"[within ft3v4] {a.mdir}: n={len(fy)} ft4={int(fy.sum())} best-layer CV {curve[b]:.3f} @L{b} | max-perm obs {obs:.3f} p={p:.3f}",flush=True)
out={"model":a.mdir,"n":int(len(fy)),"n_ft4":int(fy.sum()),"within_cv":float(curve[b]),"within_best_layer":b,"within_perm_p":float(p)}
# 2/3: transfer FROM hint and instructed acts INTO ft3v4 (sweep layers, mean+best)
for src,tag in (("hint","_hint"),("instructed","")):
    p_=os.path.join(SYNTH,f"acts_{a.mdir}{tag}.npz")
    if not os.path.exists(p_): continue
    d=np.load(p_,allow_pickle=True); X,y=d["X"],d["y"]; NL=min(NLw,X.shape[0])
    aucs=[roc_auc_score(fy, pipe(len(y)).fit(X[l].astype(np.float32),y).predict_proba(fe[:,l+1,:].astype(np.float32))[:,1]) for l in range(NL)]
    aucs=np.array(aucs); out[f"{src}_to_ft34_mean"]=float(aucs.mean()); out[f"{src}_to_ft34_best"]=float(aucs.max())
    print(f"[{src} -> ft3v4] {a.mdir}: mean {aucs.mean():.3f} best {aucs.max():.3f} @L{int(aucs.argmax())}",flush=True)
json.dump(out,open(os.path.join(SYNTH,"results",f"ft34_probe_{a.mdir}.json"),"w"),indent=2)
print(f"FT34_PROBE DONE {a.mdir}",flush=True)
