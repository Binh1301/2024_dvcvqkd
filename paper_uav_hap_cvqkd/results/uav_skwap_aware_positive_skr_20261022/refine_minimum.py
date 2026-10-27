"""Refine the smallest candidate along its exact, fixed-source aperture branch."""
import csv
import math
import shutil
import run_study as s
from refine import robust_node


def rows(name):
    with (s.OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def main():
    if (s.OUT/'source_refined_minimum.json').exists():raise FileExistsError('Preserve completed minimum refinement')
    s.initialize();sel=s.read(s.OUT/'selection.json');initial=sel['recommendations'][0]
    snapshot=s.OUT/'selection_phase1';snapshot.mkdir(exist_ok=True)
    for name in ['selection.json','selected_designs.csv','table_B_positive_candidates.csv','robustness.csv','convergence.json','source_comparison.csv','detector_sensitivity.csv']:
        if not (snapshot/name).exists():shutil.copy2(s.OUT/name,snapshot/name)
    original_hashes={p.name:s.sha(p) for p in snapshot.iterdir() if p.is_file()}
    candidates=rows('table_B_positive_candidates.csv');robust=rows('robustness.csv');conv=s.read(s.OUT/'convergence.json')
    current=initial;roots=[]
    # shortcut: at most three exact-source/local-aperture iterations; never a global minimum proof.
    for iteration in range(3):
        p=s.par(current);c=s.source(current)
        def objective(diameter):
            q=list(p);q[9]=diameter
            return s.evaluate(c,q,'source_refined_minimum_root',256,32)['K_raw']
        lo=max(d for d in s.DR if d<p[9] and objective(d)<0)
        assert objective(p[9])>0
        root=s.brentq(objective,lo,p[9],xtol=1e-8,rtol=1e-11)
        rounded=math.ceil((root+1e-9)*1000)/1000
        entry=dict(iteration=iteration,ensemble_hash=c['ensemble_hash'],VA=c['VA'],nu_raw=c['nu_raw'],parameters=list(p),
            lower_m=lo,upper_m=p[9],D_crit_m=root,residual=objective(root),rounded_m=rounded,
            scope='FIXED_SELECTED_EXACT_SOURCE_OPTICS_PAT_GEOMETRY; LOCAL_BRACKET_NOT_GLOBAL')
        roots.append(entry)
        if rounded>=p[9]:entry['status']='NO_SMALLER_MILLIMETER_POINT';break
        q=list(p);q[9]=rounded;ctx=s.catalog(q,'minimum_refinement_'+str(iteration))
        best=robust_node(s.source(ctx['best_MB']),q,'minimum_refinement_final');observed=best['robustness_observed_MI_change']
        assert best['K_raw']>2*.95*observed
        label='minimum_refinement_'+str(iteration);cases=[]
        for jf,sf,case in [(1.,1.,'nominal'),(1.1,1.,'jitter_plus10'),(1.,1.1,'centering_plus10'),(1.1,1.1,'joint_plus10'),(1.2,1.2,'joint_plus20')]:
            tested=list(q);tested[4]*=jf;tested[5]*=sf
            cases.append({**robust_node(s.source(best),tested,'minimum_refinement_robustness'),'candidate':label,'case':case})
        for noise in [.0135,.005]:
            tested=list(q);tested[7]=noise
            cases.append({**robust_node(s.source(best),tested,'minimum_refinement_noise'),'candidate':label,'case':'noise_'+str(noise)})
        bycase={x['case']:x for x in cases};j10=bycase['joint_plus10']['K_raw'];j20=bycase['joint_plus20']['K_raw']
        current={**best,'candidate':label,'branch':'source_refined_root_adjacent','observed_MI_change':observed,
            'joint10_K':j10,'joint20_K':j20,'design':initial['design'],'source_selection':'BEST_EXACT_TESTED_AT_SOURCE_REFINED_LOCAL_ROOT_POINT',
            'robustness_class':'POSITIVE_AT_JOINT20' if j20>1e-4 else ('POSITIVE_AT_JOINT10' if j10>1e-4 else 'NOMINAL_ONLY_OR_BELOW_ENGINEERING_MARGIN')}
        candidates.append(current);robust.extend(cases);conv.append(dict(candidate=label,observed_MI_change=observed,K_raw=best['K_raw'],conservative_observed_margin=best['K_raw']-2*.95*observed))
        entry.update(status='SMALLER_POSITIVE_REFINED',rounded_source_hash=best['ensemble_hash'],rounded_K=best['K_raw'])
    B=sel['recommendations'][1]
    if not sel['balanced_objective_met']:
        pool=[r for r in candidates if float(r['jitter_urad'])>=3] or candidates
        chosen=max(pool,key=lambda r:(float(r['joint10_K']),float(r['joint20_K']),float(r['K_raw'])))
        raw=s.CACHE[s.key(s.source(chosen),s.par(chosen),int(chosen['radial_order']),int(chosen['width_order']))]
        B={**raw,**{k:chosen[k] for k in ['candidate','branch','robustness_class']},
            **{k:float(chosen[k]) for k in ['observed_MI_change','joint10_K','joint20_K']},
            'design':B['design'],'source_selection':'BEST_OBSERVED_JOINT10_SHORTLIST_REFERENCE; BALANCED_OBJECTIVE_UNMET'}
    selected=[current,B,sel['recommendations'][2]]
    comparisons=[r for r in rows('source_comparison.csv') if r['design'].startswith('C')]
    sensitivity=[r for r in rows('detector_sensitivity.csv') if r['design'].startswith('C')]
    for design in selected[:2]:
        p=s.par(design);ctx=s.catalog(p,'minimum_final_'+design['design'][0])
        for scheme,r in [('Uniform',ctx['best_Uniform']),('Fixed_MB',ctx['fixed_MB']),('Optimized_MB',ctx['best_MB'])]:
            comparisons.append({**s.evaluate(s.source(r),p,'minimum_source_comparison',512,48),'design':design['design'],'scheme':scheme})
        for eta,noise in s.DETECTORS:
            q=list(p);q[6:8]=eta,noise
            sensitivity.append({**s.evaluate(s.source(design),q,'minimum_detector_sensitivity',256,32),'design':design['design']})
    sel.update(recommendations=selected,minimum_evaluated_positive_m=current['D_r'],positive_shortlist_count=len(candidates),
        distinct_recommended_physical_points=len({s.par(r) for r in selected}),
        balanced_objective_met=B['jitter_urad']>=3 and B['joint10_K']>=1e-4,source_refined_minimum='source_refined_minimum.json')
    s.write('table_B_positive_candidates.csv',candidates);s.write('robustness.csv',robust);s.save('convergence.json',conv)
    s.write('source_comparison.csv',comparisons);s.write('detector_sensitivity.csv',sensitivity);s.write('selected_designs.csv',selected)
    s.write('all_evaluations.csv',s.ROWS);s.save('selection.json',sel)
    s.save('source_refined_minimum.json',dict(status='CURRENTLY_VERIFIED_PASS',roots=roots,phase1_sha256=original_hashes,
        initial_D_m=initial['D_r'],final_D_m=current['D_r'],balanced_reference_rule='HIGHEST_OBSERVED_JOINT10_WHEN_BALANCED_OBJECTIVE_UNMET',maximum_coordinate_iterations=3,global_minimum_certified=False))
    print('MINIMUM REFINEMENT COMPLETE',current['D_r'],current['K_raw'],len(s.ROWS),flush=True)


if __name__=='__main__':main()
