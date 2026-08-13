"""Phase-0 runs: (1) permutation p for same-regime transfers (hint/instructed -> ft3v4),
(2) CROSS-REGIME within-model transfer (ft1v2 <-> ft3v4) -- does unfaithfulness share a
direction across correctness regimes? Coupled perms, project-once. Usage: --mdir llama"""
import argparse, json, os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
ap=argparse.ArgumentParser(); ap.add_argument("--mdir",required=True); ap.add_argument("--nperm",type=int,default=500)
a=ap.parse_args(); S=os.path.expanduser("~/synth")
f12=np.load(os.path.expanduser(f"~/wbrep_{a.mdir}.npz"),allow_pickle=True)          # ft1v2 (incorrect regime)
f34=np.load(os.path.expanduser(f"~/wbrep_{a.mdir}_ft34.npz"),allow_pickle=True)      # ft3v4 (correct regime)
X12,y12=f12["cot_end"],f12["y"]; X34,y34=f34["cot_end"],f34["y"]
NL=min(X12.shape[1],X34.shape[1])-1
def proj_pair(Xa,Xb,l):
    sc=StandardScaler().fit(Xa[:,l+1,:].astype(np.float32))
    pc=PCA(max(2,min(50,Xa.shape[0]-2)),random_state=0).fit(sc.transform(Xa[:,l+1,:].astype(np.float32)))
    return pc.transform(sc.transform(Xa[:,l+1,:].astype(np.float32))), pc.transform(sc.transform(Xb[:,l+1,:].astype(np.float32)))
def sweep_perm(name, PR, ytr, yte, nperm):
    def sweep(yy): return np.array([roc_auc_score(yte, LogisticRegression(max_iter=2000,C=1.0).fit(PR[l][0],yy).predict_proba(PR[l][1])[:,1]) for l in range(len(PR))])
    obs=sweep(ytr); rng=np.random.default_rng(0)
    nm=[]; nb=[]
    for i in range(nperm):
        pm=sweep(rng.permutation(ytr)); nm.append(pm.mean()); nb.append(pm.max())
    pm_=(1+sum(m>=obs.mean() for m in nm))/(1+nperm); pb_=(1+sum(m>=obs.max() for m in nb))/(1+nperm)
    print(f"[{name}] mean {obs.mean():.3f} p={pm_:.3f} | best {obs.max():.3f} @L{int(obs.argmax())} p={pb_:.3f}",flush=True)
    return {"mean":float(obs.mean()),"p_mean":pm_,"best":float(obs.max()),"best_layer":int(obs.argmax()),"p_best":pb_}
out={"model":a.mdir}
# cross-regime, both directions (wbrep layer convention on both sides)
PR=[proj_pair(X12,X34,l) for l in range(NL)]
out["ft12_to_ft34"]=sweep_perm(f"{a.mdir} ft1v2->ft3v4 (cross-regime)",PR,y12,y34,a.nperm)
PR=[proj_pair(X34,X12,l) for l in range(NL)]
out["ft34_to_ft12"]=sweep_perm(f"{a.mdir} ft3v4->ft1v2 (cross-regime)",PR,y34,y12,a.nperm)
# same-regime construction transfers with perms (acts X[l] == wbrep [:,l+1])
for src,tag in (("hint","_hint"),("instructed","")):
    d=np.load(os.path.join(S,f"acts_{a.mdir}{tag}.npz"),allow_pickle=True); Xs,ys=d["X"],d["y"]
    NLs=min(Xs.shape[0],X34.shape[1]-1)
    PR=[]
    for l in range(NLs):
        sc=StandardScaler().fit(Xs[l].astype(np.float32))
        pc=PCA(max(2,min(50,Xs.shape[1]-2)),random_state=0).fit(sc.transform(Xs[l].astype(np.float32)))
        PR.append((pc.transform(sc.transform(Xs[l].astype(np.float32))), pc.transform(sc.transform(X34[:,l+1,:].astype(np.float32)))))
    out[f"{src}_to_ft34"]=sweep_perm(f"{a.mdir} {src}->ft3v4 (same-regime)",PR,ys,y34,a.nperm)
json.dump(out,open(os.path.join(S,"results",f"regime_transfers_{a.mdir}.json"),"w"),indent=2)
print(f"REGIME_TRANSFERS DONE {a.mdir}",flush=True)
