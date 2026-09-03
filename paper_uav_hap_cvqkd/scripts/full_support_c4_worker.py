"""Exact-binary64 arbitrary-precision full-support C4 source-moment worker."""
from __future__ import annotations
import json, sys
import mpmath as mp

def _sectors(p,z):
    blocks=[]
    for d in range(4):
        r=mp.j**d
        blocks.append(mp.matrix([[mp.sqrt(p[i]*p[j])*mp.exp(-(abs(z[i])**2+abs(r*z[j])**2)/2+mp.conj(z[i])*r*z[j]) for j in range(64)] for i in range(64)]))
    answer=[]
    for s in range(4):
        x=mp.zeros(64)
        for d in range(4): x += blocks[d]*mp.j**(s*d)
        answer.append((x+x.H)/2)
    return answer

def _row(p,z,digits):
    with mp.workdps(digits):
        values=[]; vectors=[]
        for g in _sectors(p,z):
            v,u=mp.eighe(g); values.append([mp.re(v[i]) for i in range(64)]); vectors.append(u)
        rank=sum(x>0 for v in values for x in v)
        if rank!=256: return {"digits":digits,"rank":rank,"resolved":False}
        a=[]; q=[]; c=mp.mpf(0)
        for s in range(4):
            previous=(s-1)%4; m=vectors[s].H*mp.diag(z)*vectors[previous]
            sr=mp.diag([mp.sqrt(x) for x in values[s]]); sp=mp.diag([mp.sqrt(x) for x in values[previous]])
            b=sr*(mp.lu_solve(sp,m.T)).T
            aa=sr*(mp.lu_solve(sp,(sr*b).T)).T
            a.append(aa); c+=mp.trace(sr*b*sp*b.H).real
            q.append(sr*vectors[s].H*mp.diag([1/(2*mp.sqrt(x)) for x in p]))
        t=[a[s]*q[(s-1)%4] for s in range(4)]
        d=[mp.fsum(mp.conj(q[s][i,k])*t[s][i,k] for s in range(4) for i in range(64)) for k in range(64)]
        w=mp.fsum(4*p[k]*mp.fsum(abs(t[s][i,k]-q[s][i,k]*d[k])**2 for s in range(4) for i in range(64)) for k in range(64))
        return {"digits":digits,"rank":256,"resolved":True,"C":mp.nstr(c,50),"w":mp.nstr(w,50)}

def main():
    request=json.load(sys.stdin)
    p=[mp.mpf(float.fromhex(x)) for x in request["probabilities_float64_hex"]]
    z=[mp.mpc(float.fromhex(x),float.fromhex(y)) for x,y in request["prototypes_float64_hex"]]
    rows=[_row(p,z,int(d)) for d in request["precision_ladder_decimal_digits"]]
    final=rows[-2:]; ok=all(x["resolved"] and x["rank"]==256 for x in final)
    if ok:
        ok=all(abs(mp.mpf(final[0][name])-mp.mpf(final[1][name]))<=mp.mpf("1e-7")+mp.mpf("1e-6")*max(abs(mp.mpf(final[0][name])),abs(mp.mpf(final[1][name]))) for name in ("C","w"))
    result={"status":"FULL_SUPPORT_CONVERGED" if ok else "FAIL_CLOSED","rows":rows}
    if ok: result.update({"C":final[-1]["C"],"w":final[-1]["w"]})
    json.dump(result,sys.stdout,sort_keys=True)

if __name__=="__main__": main()
