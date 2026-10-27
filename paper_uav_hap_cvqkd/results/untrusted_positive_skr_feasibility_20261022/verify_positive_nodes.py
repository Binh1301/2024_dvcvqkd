"""GH128 check of every distinct reported positive exact node; no optimization."""
from pathlib import Path
import math
import numpy as np
import model as m
import run as r
from extend_bright import read_csv

OUT=Path(__file__).resolve().parent


def main():
    if (OUT/'positive_MI_verification.json').exists():raise FileExistsError('Preserve completed verification')
    sources=m.load_catalog(r.read(m.ROOT/'configs/manuscript_mobility.json'))
    factors={c['ensemble_hash']:m.source_factors(c) for c in sources}
    fields=['ensemble_hash','t_after_detector','N_post','K_raw']
    unique={}
    for p in sorted(OUT.glob('*.csv')):
        for row in read_csv(p.name):
            if not all(k in row for k in fields) or row['K_raw']<=0:continue
            key=(row['ensemble_hash'],row['t_after_detector'],row['N_post'])
            unique.setdefault(key,row)
    checked=[]
    for i,(key,row) in enumerate(unique.items()):
        x,px=factors[row['ensemble_hash']]
        i128=m.mi_gh(px,x.astype(complex),row['t_after_detector'],row['N_post'],128,dimension=1)
        difference=i128-row['I_AB']
        checked.append(dict(ensemble_hash=row['ensemble_hash'],t_after_detector=row['t_after_detector'],N_post=row['N_post'],
            I_AB_GH64=row['I_AB'],I_AB_GH128=i128,difference=difference,K_GH128=.95*i128-row['chi_BE'],
            status='CURRENTLY_VERIFIED_PASS' if abs(difference)<2e-13 else 'FAILED'))
        if (i+1)%1000==0:print('POSITIVE MI CHECK',i+1,'/',len(unique),flush=True)
    r.write('positive_MI_node_checks.csv',checked)
    failed=[x for x in checked if x['status']=='FAILED']
    r.save('positive_MI_verification.json',dict(status='CURRENTLY_VERIFIED_PASS' if not failed else 'FAILED',
         positive_nodes=len(checked),failed_nodes=len(failed),tolerance=2e-13,
         maximum_difference=max(abs(x['difference']) for x in checked),security_valid=False))
    if failed:raise AssertionError('Positive nodes have unresolved MI convergence; inspect saved checks')
    print('ALL POSITIVE MI NODES PASS',len(checked),flush=True)


if __name__=='__main__':main()
