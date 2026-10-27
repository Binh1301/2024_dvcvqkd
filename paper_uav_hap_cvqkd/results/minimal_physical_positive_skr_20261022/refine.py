"""Refine the near-zero 40 cm branch and select a pointing-tolerant design."""
import json
import math
import numpy as np
from scipy.optimize import brentq
import search as s


def main():
    if (s.OUT/'final_selection.json').exists():
        raise FileExistsError('Completed refinement is immutable')
    s.SOURCES=s.n.previous.load_catalog(s.read(s.ROOT/'configs/manuscript_mobility.json'))
    for line in (s.OUT/'evaluations.jsonl').read_text().splitlines():
        row=json.loads(line)
        key=(row['ensemble_hash'],*s.parameters(row),int(row['radial_order']),int(row['width_order']))
        s.CACHE[key]=row;s.ROWS.append(row)
    seed=s.read(s.OUT/'selection.json')
    probe=s.read(s.OUT/'boundary_divergence_refinement.json')
    divergence=probe['result']['divergence']
    c=s.source(probe['evaluations'][0]);roots=[]
    def rate(diameter):
        return s.evaluate(c,(diameter,divergence,1.561,.1),'near_40cm_root',256,32)['K_raw']
    for target in (0.,1e-4):
        root=brentq(lambda d:rate(d)-target,.4,.55,xtol=1e-9)
        roots.append(dict(branch='near_40cm',variable='D_r',root=root,target_K=target,
            residual=rate(root)-target,divergence_urad=divergence,jitter_urad=1.561,sigma_h_m=.1,
            exact_source_hash=c['ensemble_hash'],scope='FIXED_SOURCE_FIXED_DIVERGENCE_LOCAL_NOT_GLOBAL'))
    # One millimetre reporting grid avoids presenting a numerical root as hardware tolerance.
    diameter=math.ceil(roots[-1]['root']*1000)/1000
    minimal,_=s.catalog((diameter,divergence,1.561,.1),'refined_minimal')
    nominal,_=s.catalog((.55,35.,3.,.1),'balanced_nominal')
    _,_=s.catalog((.55,35.,3.6,.12),'balanced_degraded')
    nom=[r for r in s.ROWS if s.parameters(r)==(.55,35.,3.,.1) and r['radial_order']==128]
    worst={r['ensemble_hash']:r for r in s.ROWS if s.parameters(r)==(.55,35.,3.6,.12) and r['radial_order']==128}
    balanced=max((r for r in nom if worst[r['ensemble_hash']]['K_raw']>=1.2e-4),key=lambda r:r['K_raw'])
    high=next(r for r in seed['receiver_contexts'] if r['D_r']==.55)
    original,_=s.catalog((.08,233.,15.61,1.),'original_actual')
    final=[];robustness=[];convergence=[];curves=[];comparisons=[]
    for label,row in [('minimal',minimal),('balanced',balanced),('higher_performance',high)]:
        c=s.source(row);par=s.parameters(row);values=[]
        for radial,width in [(256,32),(512,48),(1024,64)]:
            current=s.evaluate(c,par,'refined_final_'+label,radial,width);values.append(current)
            if len(values)>1 and abs(values[-1]['I_AB']-values[-2]['I_AB'])<2e-6:break
        error=abs(values[-1]['I_AB']-values[-2]['I_AB'])
        assert error<2e-6 and current['K_raw']>max(1e-4,2*.95*error)
        final.append({**current,'recommendation':label,'numerical_MI_error_observed':error})
        convergence.append(dict(recommendation=label,orders=[(r['radial_order'],r['width_order']) for r in values],
            observed_MI_change=error,positive_margin_after_2changes=current['K_raw']-2*.95*error))
        for angular in (.8,.9,1.,1.1,1.2):
            for horizontal in (.8,.9,1.,1.1,1.2):
                tested=s.evaluate(c,(par[0],par[1],par[2]*angular,par[3]*horizontal),'refined_robustness_'+label,256,32)
                robustness.append({**tested,'recommendation':label,'angular_perturbation':angular,'horizontal_perturbation':horizontal})
        for axis,name,baseline in [(0,'D_r',.08),(1,'divergence_urad',233.),(2,'jitter_urad',15.61),(3,'sigma_h_m',1.)]:
            for target in (0.,1e-4):
                def objective(value):
                    test=list(par);test[axis]=value
                    return s.evaluate(c,tuple(test),'refined_boundary_'+label,256,32)['K_raw']-target
                lo,hi=sorted((par[axis],baseline))
                if lo!=hi and objective(lo)*objective(hi)<0:
                    root=brentq(objective,lo,hi,xtol=1e-8)
                    roots.append(dict(branch=label,variable=name,root=root,target_K=target,residual=objective(root),
                        exact_source_hash=c['ensemble_hash'],scope='FIXED_SOURCE_OTHERS_FIXED_NOT_GLOBAL'))
        # Same-channel source comparisons distinguish energy selection from shaping.
        best,winners=s.catalog(par,'final_'+label)
        comparisons.extend({**r,'recommendation':label,'comparison':'family_energy_optimized_or_historical_fixed'} for r in winners)
        for family in ('Uniform','MB'):
            same=[r for r in s.ROWS if s.parameters(r)==par and r['family']==family and r['VA']==c['VA']]
            if same:comparisons.append({**max(same,key=lambda r:r['K_raw']),'recommendation':label,'comparison':'same_VA'})
            else:comparisons.append(dict(recommendation=label,family=family,VA=c['VA'],comparison='same_VA',status='MISSING_EXACT_SOURCE_NO_INTERPOLATION'))
        for axis,name,values_axis in [(2,'angular_jitter',s.JT),(3,'position',s.SIG)]:
            for value in values_axis:
                test=list(par);test[axis]=value
                curves.append({**s.evaluate(c,tuple(test),'figure_'+name,256,32),'recommendation':label,'figure':name})
    assert min(r['K_raw'] for r in robustness if r['recommendation']=='balanced')>=1e-4
    # Refine the complete worst pointing case for every recommendation.
    worst_fine=[]
    for row in final:
        stress=min((r for r in robustness if r['recommendation']==row['recommendation']),key=lambda r:r['K_raw'])
        a=s.evaluate(s.source(row),s.parameters(stress),'worst_refinement',512,48)
        assert abs(a['I_AB']-stress['I_AB'])<2e-6
        worst_fine.append({**a,'recommendation':row['recommendation']})
    s.write('refined_boundary_roots.csv',roots)
    s.write('final_robustness.csv',robustness);s.write('worst_robustness_fine.csv',worst_fine)
    s.write('table_B_positive_candidates.csv',final)
    s.write('final_source_comparisons.csv',comparisons);s.write('figure_sensitivity_data.csv',curves)
    s.save('final_convergence.json',convergence)
    # Rate is a separate Pareto dimension. All rows are exact evaluated nodes.
    by_physical={}
    for r in s.ROWS:
        if r['K_raw']<1e-4:continue
        key=s.parameters(r)
        if key not in by_physical or r['K_raw']>by_physical[key]['K_raw']:by_physical[key]=r
    candidates=list(by_physical.values())
    def dim(r):return np.array([-r['D_r'],r['divergence_urad'],r['jitter_urad'],r['sigma_h_m'],r['K_raw']])
    pareto=[r for r in candidates if not any(np.all(dim(o)>=dim(r)) and np.any(dim(o)>dim(r)) for o in candidates)]
    pareto.sort(key=lambda r:(r['D_r'],-r['divergence_urad'],-r['jitter_urad'],-r['sigma_h_m']))
    s.write('final_pareto.csv',pareto)
    s.save('final_selection.json',dict(status='CURRENTLY_VERIFIED_PASS_NUMERICAL_DIAGNOSTIC_ONLY',recommendations=final,
        baseline=seed['baseline'],original_catalog_best=original,nominal_balanced_catalog_best=nominal,
        receiver_contexts=seed['receiver_contexts'],prior_A_B_comparison_only=True,
        minimal_scope='Smallest millimetre reporting point on the refined 40cm fixed-source branch, not a global lower bound',
        balanced_scope='Largest nominal K among tested exact sources also surviving joint 20percent pointing degradation',
        security_valid=False,hardware_validated=False))
    s.write('all_evaluations.csv',s.ROWS)
    print('REFINEMENT COMPLETE',[(r['recommendation'],s.parameters(r),r['K_raw']) for r in final],len(s.ROWS),flush=True)


if __name__=='__main__':main()
