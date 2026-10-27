"""Targeted boundary catalogs; no new source moments or interpolation."""
from pathlib import Path
from scipy.optimize import brentq
import model as m
import run as r

OUT=Path(__file__).resolve().parent


def main():
    if (OUT/'boundary_selection.json').exists():raise FileExistsError('Preserve boundary results')
    r.SOURCES=m.load_catalog(r.read(m.ROOT/'configs/manuscript_mobility.json'))
    records=[];summary=[]
    def case(diameter,divergence):
        ch=m.optical(diameter,divergence,30,.1,.1)
        all_rows,best=r.catalog(ch,m.power_conserving(ch),'targeted_physical_boundary')
        records.extend(all_rows);summary.append(best)
        print('BOUNDARY',diameter,divergence,best['VA'],best['nu_raw'],best['K_raw'],flush=True)
        return best
    practical=case(.55,25)
    previous=None;roots=[]
    for diameter in [.55,.40,.30,.20,.10,.08]:
        best=case(diameter,10)
        if best['K_raw']<=0:
            if previous:
                c=r.candidate(previous)
                def objective(d):
                    ch=m.optical(d,10,30,.1,.1)
                    return r.evaluate(c,ch,m.power_conserving(ch),'aperture_root')['K_raw']
                root=brentq(objective,diameter,previous['D_r'],xtol=1e-9)
                roots.append(dict(variable='D_r',root=root,lower=diameter,upper=previous['D_r'],
                                  fixed_source_hash=c['ensemble_hash'],K_at_root=objective(root)))
            break
        previous=best
    small=previous
    wide=case(.75,100)
    if wide['K_raw']>0:
        failed=case(.75,233);upper=233;wide_positive=wide
    else:
        wide_positive=case(.75,50);failed=wide;upper=100
    if wide_positive['K_raw']>0 and failed['K_raw']<0:
        c=r.candidate(wide_positive)
        def objective(theta):
            ch=m.optical(.75,theta,30,.1,.1)
            return r.evaluate(c,ch,m.power_conserving(ch),'divergence_root')['K_raw']
        root=brentq(objective,wide_positive['theta_div_urad'],upper,xtol=1e-7)
        roots.append(dict(variable='theta_div_urad',root=root,lower=wide_positive['theta_div_urad'],upper=upper,
                          fixed_source_hash=c['ensemble_hash'],K_at_root=objective(root)))
    r.write('boundary_catalog_evaluations.csv',records)
    r.write('boundary_catalog_winners.csv',summary)
    r.write('boundary_root_evaluations.csv',[x for x in r.EVALUATIONS if x['stage'].endswith('root')])
    r.save('boundary_selection.json',dict(practical_candidate=practical,smallest_tested_aperture_candidate=small,
        widest_tested_divergence_candidate=wide_positive,roots=roots,
        status='FIXED_POINTING_ZENITH30_EXACT_CATALOG_ONLY_NOT_GLOBAL_PHYSICAL_OPTIMUM'))


if __name__=='__main__':main()
