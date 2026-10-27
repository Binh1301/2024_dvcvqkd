"""Fixed-source boundaries, shortlist refinement and requested robustness."""
import math
import run_study as s


def robust_node(c,p,stage):
    coarse=s.evaluate(c,p,stage,256,32);fine=s.evaluate(c,p,stage,512,48)
    observed=abs(fine['I_AB']-coarse['I_AB'])
    if observed>=2e-6:
        finer=s.evaluate(c,p,stage,1024,64);observed=abs(finer['I_AB']-fine['I_AB']);fine=finer
    assert observed<2e-6
    return {**fine,'robustness_observed_MI_change':observed}


def main():
    if (s.OUT/'selection.json').exists():raise FileExistsError('Preserve completed selection')
    s.initialize();opt=s.read(s.OUT/'optimization.json')
    assert s.read(s.OUT/'source_coverage.json')['status']=='CURRENTLY_VERIFIED_PASS'
    diameters=s.DR+opt['fallback_diameters'];contexts=opt['contexts']
    reference=s.read(s.ROOT/'results/minimal_physical_positive_skr_20261022/final_selection.json')['recommendations'][0]
    common=s.source(reference);roots=[];status=[];curves=[];onset=[]
    for jitter in [3.,1.561]:
        for eta,noise in s.CORNERS:
            p=(20.,1.,0.,35.,jitter,.1,eta,noise,.92,.30)
            samples=[]
            for diameter in s.DR+s.FALLBACK:
                q=list(p);q[9]=diameter;r=s.evaluate(common,q,'fixed_source_aperture_curve',256,32)
                curves.append({**r,'pointing_scenario':'moderate3' if jitter==3 else 'demanding1p561'})
                samples.append(r)
            for target in [0.,1e-4]:
                pairs=[(a,b) for a,b in zip(samples,samples[1:]) if (a['K_raw']-target)*(b['K_raw']-target)<0]
                if not pairs:
                    status.append(dict(eta_det=eta,epsilon_det=noise,jitter_urad=jitter,target_K=target,status='NO_SIGN_CHANGE',K_at_8cm=samples[0]['K_raw'],K_at_45cm=samples[-1]['K_raw']))
                    continue
                lo,hi=pairs[0]
                def objective(diameter):
                    q=list(p);q[9]=diameter
                    return s.evaluate(common,q,'fixed_source_D_root',256,32)['K_raw']-target
                root=s.brentq(objective,lo['D_r'],hi['D_r'],xtol=1e-8,rtol=1e-11)
                rounded=math.ceil((root+1e-9)*1000)/1000
                q=list(p);q[9]=rounded;r=s.evaluate(common,q,'rounded_root_candidate',512,48)
                while r['K_raw']<=target+2e-6 and rounded+.001<=.45:
                    rounded=round(rounded+.001,3);q[9]=rounded
                    r=s.evaluate(common,q,'rounded_root_candidate',512,48)
                onset.append(r)
                roots.append(dict(eta_det=eta,epsilon_det=noise,jitter_urad=jitter,sigma_h_m=.1,zenith_deg=0.,divergence_urad=35.,
                    VA=common['VA'],nu_raw=common['nu_raw'],ensemble_hash=common['ensemble_hash'],target_K=target,D_crit_m=root,
                    bracket_lower_m=lo['D_r'],bracket_upper_m=hi['D_r'],residual=objective(root),rounded_D_m=rounded,rounded_K=r['K_raw'],
                    scope='FIXED_COMMON_SOURCE_OPTICS_PAT_GEOMETRY; FIRST_SAMPLED_BRACKET_NOT_GLOBAL_MINIMUM'))
    s.write('critical_receiver_roots.csv',roots);s.write('critical_receiver_status.csv',status)
    s.write('fixed_source_aperture_curves.csv',curves)
    s.save('threshold_reference.json',dict(source={k:common[k] for k in ['ensemble_hash','VA','nu_raw','C','w']},
        all_other_parameters_fixed=True,root_maximum_m=.45,source_optimization_along_curve=False))
    # Per-diameter positive shortlist, including the moderate-PAT alternative.
    shortlist=[];relaxations=[]
    for diameter in diameters:
        for eta,noise in s.CORNERS:
            local=[r for r in s.ROWS if r['D_r']==diameter and (r['eta_det'],r['epsilon_det'])==(eta,noise)
                and r['family']=='MB' and r['stage'].startswith(('catalog_','source_physical_coordinate','complete_physical_source_coordinate'))]
            if not local:continue
            for branch,condition in [('moderate',lambda r:r['jitter_urad']>=3),('demanding',lambda r:True)]:
                candidate=max((r for r in local if condition(r)),key=lambda r:r['K_raw'])
                if candidate['K_raw']<=0:continue
                shortlist.append({**candidate,'branch':branch})
    # Root-adjacent seeds at improved-noise conditions do not expand source moments.
    for r in onset:
        if r['epsilon_det']==.005 and r['K_raw']>0 and r['D_r']<=max(diameters):
            result=s.catalog(s.par(r),'onset_'+str(r['eta_det'])+'_'+str(r['jitter_urad'])+'_'+str(r['D_r']))
            shortlist.append({**result['best_MB'],'branch':'root_adjacent'})
    by_point={}
    for r in shortlist:
        key=(r['ensemble_hash'],*s.par(r))
        if key not in by_point:by_point[key]=r
    for r in list(by_point.values()):
        c=s.source(r);p=s.par(r)
        for jitter in s.JT:
            for sigma in s.SIG:
                q=list(p);q[4:6]=jitter,sigma
                relaxations.append(s.evaluate(c,q,'PAT_relaxation'))
    s.write('PAT_relaxation.csv',relaxations)
    # Keep nondominated pointing requirements for each aperture/detector at fixed source.
    pareto=[]
    for r in relaxations:
        if r['K_raw']<1.2e-4:continue
        peers=[x for x in relaxations if x['D_r']==r['D_r'] and x['eta_det']==r['eta_det'] and x['epsilon_det']==r['epsilon_det'] and x['ensemble_hash']==r['ensemble_hash']]
        if not any(x['K_raw']>=1.2e-4 and x['jitter_urad']>=r['jitter_urad'] and x['sigma_h_m']>=r['sigma_h_m']
            and (x['jitter_urad']>r['jitter_urad'] or x['sigma_h_m']>r['sigma_h_m']) for x in peers):pareto.append(r)
    s.write('least_demanding_PAT.csv',pareto)
    for r in pareto:by_point.setdefault((r['ensemble_hash'],*s.par(r)),{**r,'branch':'PAT_pareto'})
    refined=[];robust=[];convergence=[]
    for index,r in enumerate(by_point.values()):
        p=s.par(r);c=s.source(r);coarse=s.evaluate(c,p,'candidate_convergence',256,32)
        fine=s.evaluate(c,p,'candidate_final',512,48);observed=abs(fine['I_AB']-coarse['I_AB'])
        if observed>=2e-6:
            finer=s.evaluate(c,p,'candidate_final',1024,64);observed=abs(finer['I_AB']-fine['I_AB']);fine=finer
        assert observed<2e-6
        if fine['K_raw']<=2*.95*observed:continue
        label=f'candidate_{index:03d}';fine={**fine,'candidate':label,'branch':r['branch'],'observed_MI_change':observed}
        convergence.append(dict(candidate=label,observed_MI_change=observed,K_raw=fine['K_raw'],conservative_observed_margin=fine['K_raw']-2*.95*observed))
        cases=[]
        for jf,sf,case in [(1.,1.,'nominal'),(1.1,1.,'jitter_plus10'),(1.,1.1,'centering_plus10'),(1.1,1.1,'joint_plus10'),(1.2,1.2,'joint_plus20')]:
            q=list(p);q[4]*=jf;q[5]*=sf
            tested=robust_node(c,q,'robustness');cases.append({**tested,'candidate':label,'case':case})
        for noise in [.0135,.005]:
            q=list(p);q[7]=noise;cases.append({**robust_node(c,q,'robustness_noise'),'candidate':label,'case':'noise_'+str(noise)})
        bycase={x['case']:x for x in cases};fine['joint10_K']=bycase['joint_plus10']['K_raw'];fine['joint20_K']=bycase['joint_plus20']['K_raw']
        fine['robustness_class']='POSITIVE_AT_JOINT20' if fine['joint20_K']>1e-4 else ('POSITIVE_AT_JOINT10' if fine['joint10_K']>1e-4 else 'NOMINAL_ONLY_OR_BELOW_ENGINEERING_MARGIN')
        refined.append(fine);robust.extend(cases)
    assert refined,'No numerically validated positive candidate in allowed study'
    A=min(refined,key=lambda r:(r['D_r'],-r['K_raw']))
    moderate=[r for r in refined if r['jitter_urad']>=3]
    resilient=[r for r in moderate if r['joint20_K']>=1e-4]
    if not resilient:resilient=[r for r in moderate if r['joint10_K']>=1e-4]
    if not resilient:resilient=[r for r in refined if r['joint20_K']>=1e-4]
    if not resilient:resilient=[r for r in refined if r['joint10_K']>=1e-4]
    B=min(resilient or moderate or refined,key=lambda r:(r['D_r'],r['eta_det'],-r['epsilon_det'],-r['K_raw']))
    C=max(refined,key=lambda r:r['K_raw'])
    selected=[{**r,'design':label} for label,r in zip(['A_lightweight_priority','B_balanced_priority','C_performance_reference'],[A,B,C])]
    comparisons=[];sensitivity=[]
    final=[]
    for r in selected:
        p=s.par(r);c=s.source(r);ctx=s.catalog(p,'selected_'+r['design'][0])
        best=s.evaluate(s.source(ctx['best_MB']),p,'final_selected_source',512,48)
        coarse=s.evaluate(s.source(best),p,'final_selected_source',256,32)
        observed=abs(best['I_AB']-coarse['I_AB']);assert observed<2e-6 and best['K_raw']>2*.95*observed
        label='final_'+r['design'];cases=[]
        for jf,sf,case in [(1.,1.,'nominal'),(1.1,1.,'jitter_plus10'),(1.,1.1,'centering_plus10'),(1.1,1.1,'joint_plus10'),(1.2,1.2,'joint_plus20')]:
            q=list(p);q[4]*=jf;q[5]*=sf
            cases.append({**robust_node(s.source(best),q,'final_selected_robustness'),'candidate':label,'case':case})
        for noise in [.0135,.005]:
            q=list(p);q[7]=noise
            cases.append({**robust_node(s.source(best),q,'final_selected_robustness'),'candidate':label,'case':'noise_'+str(noise)})
        bycase={x['case']:x for x in cases};j10=bycase['joint_plus10']['K_raw'];j20=bycase['joint_plus20']['K_raw']
        # Preserve B's sampled robustness if the nominal-source optimum loses it.
        retain_B=r['design'].startswith('B') and ((r['joint20_K']>=1e-4 and j20<1e-4) or (r['joint10_K']>=1e-4 and j10<1e-4))
        if not retain_B:
            r={**r,**best,'candidate':label,'observed_MI_change':observed,'joint10_K':j10,'joint20_K':j20,
                'robustness_class':'POSITIVE_AT_JOINT20' if j20>1e-4 else ('POSITIVE_AT_JOINT10' if j10>1e-4 else 'NOMINAL_ONLY_OR_BELOW_ENGINEERING_MARGIN')}
            robust.extend(cases);refined.append(r)
            convergence.append(dict(candidate=label,observed_MI_change=observed,K_raw=best['K_raw'],conservative_observed_margin=best['K_raw']-2*.95*observed))
        r['source_selection']='RETAINED_FOR_ROBUSTNESS' if retain_B else 'BEST_EXACT_TESTED_NOMINAL_AT_SELECTED_PHYSICAL_POINT'
        final.append(r);c=s.source(r)
        for scheme,old in [('Uniform',ctx['best_Uniform']),('Fixed_MB',ctx['fixed_MB']),('Optimized_MB',ctx['best_MB'])]:
            comparisons.append({**s.evaluate(s.source(old),p,'selected_source_comparison',512,48),'design':r['design'],'scheme':scheme})
        for eta,noise in s.DETECTORS:
            q=list(p);q[6:8]=eta,noise
            sensitivity.append({**s.evaluate(c,q,'selected_detector_sensitivity',256,32),'design':r['design']})
    selected=final
    s.write('table_B_positive_candidates.csv',refined);s.write('robustness.csv',robust);s.save('convergence.json',convergence)
    s.write('source_comparison.csv',comparisons);s.write('detector_sensitivity.csv',sensitivity);s.write('selected_designs.csv',selected)
    s.write('all_evaluations.csv',s.ROWS)
    s.save('selection.json',dict(status='POSITIVE_MODEL_BASED_DIAGNOSTIC_CANDIDATES',recommendations=selected,
        positive_shortlist_count=len(refined),primary_minimum_sampled_positive_m=min((r['D_r'] for r in refined if r['D_r'] in s.DR),default=None),
        minimum_evaluated_positive_m=min(r['D_r'] for r in refined),common_threshold_source_hash=common['ensemble_hash'],
        fallback_used=opt['fallback_used'],moderate_PAT_positive_found=bool(moderate),
        balanced_objective_met=B['jitter_urad']>=3 and B['joint10_K']>=1e-4,
        distinct_recommended_physical_points=len({s.par(r) for r in selected}),global_minimum_certified=False,hardware_validated=False,security_valid=False))
    print('REFINEMENT COMPLETE',[(r['design'],r['D_r'],r['K_raw'],r['joint20_K']) for r in selected],len(s.ROWS),flush=True)


if __name__=='__main__':main()
