"""PhasesC/D: detector-assisted exact-source search, local thresholds and robustness."""
import json
import math
from scipy.optimize import brentq
import search as s


def main():
    if (s.OUT/'selection.json').exists():raise FileExistsError('Completed search is immutable')
    first=s.read(s.OUT/'phase1.json');s.initialize()
    if (s.OUT/'detector_probe.json').exists():
        for r in s.read(s.OUT/'detector_probe.json')['rows']:
            par=s.parameters(r);key=(r['ensemble_hash'],*par,int(r['radial_order']),int(r['width_order']))
            if key not in s.CACHE:
                r={**r,'stage':'C_probe','origin':'NEW_EXACT_EVALUATION_FROM_PROBE'}
                s.CACHE[key]=r;s.ROWS.append(r)
                with (s.OUT/'evaluations.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
    fixed=s.source(first['baseline']);C=[]
    # Few targeted beams and PAT tiers, not the full parameter Cartesian product.
    for angle in [30.,0.]:
        seed=s.source(next(r for r in first['B_catalog_best'] if r['h_hap_km']==20 and r['h_uav_km']==1 and r['zenith_deg']==angle))
        for div in [15.,25.,35.,50.]:
            for jitter,sigma in [(3.,.1),(3.,.05),(1.,.05)]:
                for eta,noise in [(.8,.005),(.8,.001),(.8,.0005),(.9,.001),(.95,.0005),(1.,0.)]:
                    for c in [fixed,seed]:
                        C.append(s.evaluate(c,(20.,1.,angle,div,jitter,sigma,eta,noise,.92),'C_fixed_source_screen'))
    s.write('stage_C_detector_screen.csv',C);print('STAGE C SCREEN COMPLETE',flush=True)
    catalog_best=[]
    for angle in [30.,0.]:
        for div in [15.,20.,25.,35.,50.]:
            for noise in [.001,.0005]:
                par=(20.,1.,angle,div,1.,.05,.8,noise,.92)
                best=s.catalog(par,f'C_z{angle:g}_d{div:g}_n{noise:g}');catalog_best.append(best)
                if best['K_raw']>=1e-4:break
    # Detector-only source reoptimization is a distinct counterfactual, not StageA.
    for noise in [.0005,0.]:
        par=list(s.BASE);par[7]=noise
        catalog_best.append(s.catalog(tuple(par),'detector_only_'+str(noise)))
    # Original-detector comparisons at the useful wider beams.
    for div in [25.,35.]:
        catalog_best.append(s.catalog((20.,1.,30.,div,1.,.05,.8,.0135,.92),'B_wider_'+str(div)))
    real=[r for r in catalog_best if r['epsilon_det']>0 and r['epsilon_det']<.0135 and r['K_raw']>=1e-4]
    if not real:
        # Exact zero-noise source identifies a continuous threshold; it is never
        # itself recommended as hardware. Test nonzero noise below that threshold.
        zeros=[]
        for div in [20.,25.,35.]:zeros.append(s.catalog((20.,1.,30.,div,1.,.05,.8,0.,.92),'zero_reference_'+str(div)))
        start=max(zeros,key=lambda r:r['K_raw'])
        if start['K_raw']>1e-4:
            c=s.source(start);par=list(s.parameters(start))
            def objective(noise):
                p=par.copy();p[7]=noise
                return s.evaluate(c,p,'derived_noise_threshold',256,32)['K_raw']
            root=brentq(objective,0.,.0135,xtol=1e-10);par[7]=root/2
            real.append(s.catalog(tuple(par),'derived_nonzero_detector'))
    s.write('catalog_shortlist.csv',catalog_best)
    if not real:
        s.save('selection.json',dict(status='NO_POSITIVE_NONIDEAL_POINT_FOUND',best=max(s.ROWS,key=lambda r:r['K_raw']),security_valid=False))
        s.write('all_evaluations.csv',s.ROWS);return
    # Explicitly prioritize original heights/angle and unchanged efficiency.
    def change_count(r):return sum(abs(x-y)>1e-12 for x,y in zip(s.parameters(r)[:8],s.BASE[:8]))
    def burden(r):
        return (change_count(r),233/r['divergence_urad'],15.61/r['jitter_urad'],1/r['sigma_h_m'],.0135/r['epsilon_det'])
    nominal=min(real,key=burden);relax=[];par=list(s.parameters(nominal));c=s.source(nominal)
    for axis,values in [(3,s.DIV),(4,s.JT),(5,s.SIG),(6,[.8,.85,.9,.95,.98]),(7,[.0135,.010,.005,.002,.001,.0005]),(2,[30.,25.,20.,15.,10.,5.,0.])]:
        for value in values:
            p=par.copy();p[axis]=value;r=s.evaluate(c,p,'minimal_change_relaxation');relax.append(r)
            if r['K_raw']>=1.2e-4:par=p;break
    detector_assisted=s.catalog(tuple(par),'relaxed_detector_assisted')
    # Stronger but nonideal detector; also test moderate PAT and wider beams.
    strong=[]
    for div,jitter in [(par[3],par[4]),(25.,3.),(35.,3.)]:
        strong.append(s.catalog((20.,1.,par[2],div,jitter,.05,.95,.0005,.92),f'nonideal_high_{div:g}_{jitter:g}'))
    high=max(strong+[detector_assisted],key=lambda r:r['K_raw'])
    original_hardware=[r for r in s.ROWS if r['eta_det']==.8 and r['epsilon_det']==.0135 and r['tau_zen']==.92 and r['h_hap_km']==20 and r['h_uav_km']==1]
    optical=max(original_hardware,key=lambda r:r['K_raw'])
    # Check which nominal positive sources have a reserve at joint+20percent.
    guard=[]
    for r in sorted(real+[detector_assisted]+strong,key=burden):
        p=list(s.parameters(r));p[4]*=1.2;p[5]*=1.2
        x=s.evaluate(s.source(r),p,'robustness_screen',256,32)
        guard.append({**x,'nominal_source_hash':r['ensemble_hash'],'nominal_parameters':json.dumps(s.parameters(r))})
    stable=[x for x in guard if x['K_raw']>=1e-4]
    if stable:
        chosen=min(stable,key=lambda r:burden({**r,'jitter_urad':r['jitter_urad']/1.2,'sigma_h_m':r['sigma_h_m']/1.2}))
        pp=tuple(json.loads(chosen['nominal_parameters']))
        detector_assisted=s.evaluate(s.source(chosen),pp,'robust_detector_assisted',512,48)
    selected=[('A_original_detector',optical),('B_detector_assisted',detector_assisted),('C_best_nonideal_tested',high)]
    final=[];convergence=[];robustness=[];roots=[];root_status=[];weather=[];curves=[];comparisons=[]
    for label,row in selected:
        c=s.source(row);par=s.parameters(row);values=[]
        for radial,width in [(256,32),(512,48),(1024,64)]:
            r=s.evaluate(c,par,'selected_'+label,radial,width);values.append(r)
            if len(values)>1 and abs(values[-1]['I_AB']-values[-2]['I_AB'])<2e-6:break
        error=abs(values[-1]['I_AB']-values[-2]['I_AB']);assert error<2e-6
        if row['K_raw']>0:assert r['K_raw']>max(1e-4,2*.95*error)
        final.append({**r,'configuration':label,'observed_MI_change':error})
        convergence.append(dict(configuration=label,orders=[(v['radial_order'],v['width_order']) for v in values],observed_MI_change=error,K_after_2changes=r['K_raw']-2*.95*error))
        for fa in [.8,.9,1.,1.1,1.2]:
            for fh in [.8,.9,1.,1.1,1.2]:
                p=list(par);p[4]*=fa;p[5]*=fh
                t=s.evaluate(c,p,'robustness_'+label,256,32)
                robustness.append({**t,'configuration':label,'angular_factor':fa,'horizontal_factor':fh})
        for vis,tau in [(23,.92),(15,.89),(5,.75)]:
            p=list(par);p[8]=tau
            weather.append({**s.evaluate(c,p,'weather_'+label,512,48),'configuration':label,'visibility_km':vis})
        if row['K_raw']>0:
            for axis,name,lo,hi in [(6,'eta_det',.05,1.),(7,'epsilon_det',0.,.0135),(4,'jitter_urad',par[4],15.61),(5,'sigma_h_m',par[5],1.),(2,'zenith_deg',0.,30.)]:
                for target in [0.,1e-4]:
                    def objective(value):
                        p=list(par);p[axis]=value
                        return s.evaluate(c,p,'threshold_'+label,256,32)['K_raw']-target
                    flo,fhi=objective(lo),objective(hi)
                    status=dict(configuration=label,variable=name,target_K=target,lower=lo,upper=hi,K_lower=flo+target,K_upper=fhi+target)
                    if flo*fhi<0:
                        root=brentq(objective,lo,hi,xtol=1e-9)
                        roots.append({**status,'root':root,'residual':objective(root),'L_crit_km':19/math.cos(math.radians(root)) if axis==2 else '',
                            'source_hash':c['ensemble_hash'],'scope':'FIXED_SOURCE_OTHERS_FIXED_ORIGINAL_HEIGHTS_NO_GLOBAL_CERTIFICATE'})
                        status['status']='BRACKETED_ROOT_FOUND'
                    else:status['status']='NO_SIGN_CHANGE_IN_REQUESTED_PHYSICAL_BRACKET'
                    root_status.append(status)
        # Identical channel/detector across family and historical fixed-source comparisons.
        s.catalog(par,'final_'+label)
        local=[x for x in s.ROWS if s.parameters(x)==par]
        for family in ['Uniform','MB']:
            best=max((x for x in local if x['family']==family),key=lambda x:x['K_raw'])
            comparisons.append({**best,'configuration':label,'comparison':family+'_best_tested'})
        comparisons.append({**s.evaluate(fixed,par,'comparison_fixed_MB'),'configuration':label,'comparison':'historical_fixed_MB'})
        for axis,name,values_axis in [(2,'zenith',[0.,5.,10.,15.,20.,25.,30.]),(6,'efficiency',[.8,.85,.9,.95,.98,1.]),
            (7,'noise',[.0135,.01,.005,.002,.001,.0005,0.]),(3,'divergence',s.DIV),(4,'pointing',s.JT)]:
            for value in values_axis:
                p=list(par);p[axis]=value
                curves.append({**s.evaluate(c,p,'figure_'+name,256,32),'configuration':label,'figure':name})
    s.write('table_2_positive_8cm.csv',[r for r in final if r['K_raw']>0]);s.write('table_4_SKR_decomposition.csv',[first['baseline']]+final)
    s.write('robustness.csv',robustness);s.write('weather_sensitivity.csv',weather);s.write('thresholds.csv',roots);s.write('threshold_status.csv',root_status)
    s.write('figure_data.csv',curves);s.write('source_comparisons.csv',comparisons);s.write('local_relaxation.csv',relax);s.write('robustness_screen.csv',guard)
    s.save('convergence.json',convergence)
    s.save('selection.json',dict(status='NUMERICAL_DIAGNOSTIC_COMPLETE',recommendations=final,baseline=first['baseline'],
        A_positive=final[0]['K_raw']>0,B_positive=final[1]['K_raw']>0,C_positive=final[2]['K_raw']>0,
        altitude_scenarios=first['B_catalog_best'],security_valid=False,hardware_validated=False,
        ranking='Original-height candidates only; few parameter changes plus engineering demands; ideal detector/height-uncalibrated cases excluded'))
    s.write('all_evaluations.csv',s.ROWS)
    print('SEARCH COMPLETE',[(r['configuration'],s.parameters(r),r['K_raw']) for r in final],len(s.ROWS),flush=True)


if __name__=='__main__':main()
