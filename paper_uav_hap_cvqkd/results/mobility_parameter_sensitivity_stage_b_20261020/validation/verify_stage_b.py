"""Independent Stage B artifact verification; no production solver/evaluator calls."""
from pathlib import Path
import csv
import hashlib
import json
import math
import re
import subprocess

import numpy as np
from PIL import Image
from scipy.integrate import quad
from scipy.linalg import cholesky
from scipy.special import ndtri
from scipy.stats import t

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]
CHECKS=[]


def js(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
def check(name,condition):
    if not bool(np.all(condition)):raise AssertionError(name)
    CHECKS.append(name)
def same(a,b):return np.allclose(a,b,atol=1e-12,rtol=1e-12)


def verify():
    c=js(ROOT/'configs/mobility_parameter_sensitivity_stage_b.json');s=js(OUT/'startup_manifest.json');proto=js(OUT/'protocol.json')
    check('pre-run config identity',js(OUT/'pre_run_protocol.json')['settings']==c and js(OUT/'pre_run_protocol.json')['config_sha256']==sha(ROOT/'configs/mobility_parameter_sensitivity_stage_b.json'))
    check('current protocol identity',proto['settings']==c and c['stage']=='B' and c['new_physical_skr_allowed'] is False)
    changed=[n for n,h in s['protected_files'].items() if n not in s['allowed_changed'] and (not (ROOT/n).is_file() or sha(ROOT/n)!=h)]
    check('all protected historical files intact',not changed)
    for cmd,key in ((['git','branch','--show-current'],'branch'),(['git','rev-parse','HEAD'],'commit')):
        check('Git identity '+key,subprocess.check_output(cmd,cwd=ROOT,text=True).strip()==s[key])
    files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','--','.'],cwd=ROOT,text=True).splitlines()
    check('new file namespaces',all(n in s['protected_files'] or n in s['allowed_new_code'] or n.startswith(s['allowed_output_prefix']) for n in files))
    check('git diff whitespace',subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode==0)
    manifest=js(OUT/'input_manifest.json')
    for name,h in manifest['bindings'].items():check('input '+name,sha(ROOT/name)==h)
    test=js(OUT/'validation/tests.json');check('9 current boundary tests',test['status']=='CURRENTLY_VERIFIED_PASS' and test['tests_run']==9 and test['errors']==test['failures']==0)
    for name,h in test['producer_sha256'].items():check('tested producer '+name,sha(ROOT/name)==h)
    for stage in ('audit','cloud','compute','aggregate'):
        r=js(OUT/'validation'/(stage+'.json'));check('stage '+stage+' PASS',r['status']=='CURRENTLY_VERIFIED_PASS')
        for name,h in r['artifact_sha256'].items():check('stage artifact '+stage+'/'+name,sha(OUT/name)==h)
    cases=proto['cases'];members=proto['memberships'];indices={r['case_id']:i for i,r in enumerate(cases)}
    check('16 cases and18 memberships',len(cases)==len(indices)==16 and len(members)==18)
    for axis,values in (('probability',c['probabilities']),('spatial',c['spatial_lengths_m']),('temporal',c['temporal_rhos'])):
        check('axis exact values '+axis,sorted(r['value'] for r in members if r['axis']==axis)==values)
    check('only3 new cloud profiles',[r['parameters'] for r in cases if r['archive_id'] is None]==c['new_cloud_parameters'])
    base=ROOT/c['reference_directory'];A=ROOT/c['stage_a_directory'];archive=ROOT/c['archive_directory']
    xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in rows(base/'positions.csv')]);K=np.array([float(r['K_star']) for r in rows(base/'p1/winners.csv')])
    distance=np.sqrt(np.sum((xy[:,None]-xy[None,:])**2,axis=-1));feasible=distance<=300
    check('original coordinate order',np.array_equal(xy,np.array([(x,y) for y in range(50,1000,100) for x in range(50,1000,100)])))
    with np.load(OUT/'clouds/states.npz',allow_pickle=False) as z:C=z['blocked'];Z=z['latent'];cloud_ids=z['case_ids'];ids=z['realization_ids']
    check('mask shape dtype finite latent',C.shape==(16,100,100,30) and C.dtype==np.bool_ and Z.shape==C.shape and np.isfinite(Z).all())
    check('case and realization identity',cloud_ids.tolist()==[r['case_id'] for r in cases] and np.array_equal(ids,np.arange(100)))
    with np.load(archive/'cloud_states.npz',allow_pickle=False) as z:oldC=z['blocked']
    diagnostics=rows(OUT/'clouds/correlation_diagnostics.csv');diag={(r['case_id'],r['metric']):r for r in diagnostics}
    check('112 cloud diagnostics',len(diag)==len(diagnostics)==112)
    for ci,case in enumerate(cases):
        cid=case['case_id'];p,ell,rho=case['parameters'];threshold=ndtri(p)
        covariance=np.exp(-distance/ell);factor=cholesky(covariance,lower=True)
        check('Cholesky covariance '+cid,same(factor@factor.T,covariance))
        reconstructed=np.empty((100,100,30))
        for rid in range(100):
            rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([20261015,rid])))
            innovation=(factor@rng.standard_normal((30,100)).T).T
            latent=np.empty_like(innovation);latent[0]=innovation[0]
            for n in range(1,30):latent[n]=rho*latent[n-1]+math.sqrt(1-rho*rho)*innovation[n]
            reconstructed[rid]=latent.T
        check('independent latent innovation replay '+cid,same(reconstructed,Z[ci]))
        check('exact binary threshold '+cid,np.array_equal(C[ci],reconstructed<threshold))
        if case['archive_id'] is not None:check('archive boolean replay '+cid,np.array_equal(C[ci],oldC[case['archive_id']]))
        b=(C[ci].astype(float)-p)/math.sqrt(p*(1-p));z=Z[ci]
        values=dict(blockage_probability=C[ci].mean(axis=(1,2)),latent_spatial_near=(z[:,0]*z[:,1]).mean(axis=1),
                    latent_spatial_far=(z[:,0]*z[:,99]).mean(axis=1),latent_temporal=(z[:,:,:-1]*z[:,:,1:]).mean(axis=(1,2)),
                    binary_spatial_near=(b[:,0]*b[:,1]).mean(axis=1),binary_spatial_far=(b[:,0]*b[:,99]).mean(axis=1),
                    binary_temporal=(b[:,:,:-1]*b[:,:,1:]).mean(axis=(1,2)))
        targets=dict(blockage_probability=p,latent_spatial_near=math.exp(-100/ell),latent_spatial_far=math.exp(-math.hypot(900,900)/ell),latent_temporal=rho)
        for name in ('spatial_near','spatial_far','temporal'):
            rr=targets['latent_'+name]
            # Plackett identity is independent of the generator's conditional-normal integral.
            targets['binary_'+name]=quad(lambda t:math.exp(-threshold*threshold/(1+t))/(2*math.pi*math.sqrt(1-t*t)),0,rr,epsabs=1e-12,epsrel=1e-12)[0]/(p*(1-p))
        for metric,observed in values.items():
            d=diag[cid,metric];mu=float(observed.mean());sd=float(observed.std(ddof=1));se=sd/10;tol=5*se+1e-10
            half=float(t.ppf(.975,99))*se
            check('cluster calibration '+cid+'/'+metric,same([mu,sd,se,tol,targets[metric],mu-half,mu+half],[float(d[k]) for k in ('mean','sd','se','tolerance','target','ci95_low','ci95_high')]) and abs(mu-targets[metric])<=tol and d['passed']=='True')
    probability=sorted([r for r in members if r['axis']=='probability'],key=lambda r:r['value'])
    check('all p masks nested',all(np.all(C[indices[a['case_id']]]<=C[indices[b['case_id']]]) for a,b in zip(probability,probability[1:])))
    temporal=[indices[r['case_id']] for r in members if r['axis']=='temporal']
    check('same initial slot across rho',all(np.array_equal(C[temporal[0],:,:,0],C[i,:,:,0]) for i in temporal))

    with np.load(OUT/'mobility/paths.npz',allow_pickle=False) as z:paths=z['paths'];path_ids=z['case_ids'];lams=z['lambda_values'];rids=z['realization_ids']
    check('trajectory dimensions and identities',paths.shape==(16,100,2,3,30) and np.issubdtype(paths.dtype,np.integer) and path_ids.tolist()==cloud_ids.tolist() and lams.tolist()==c['lambda_values'] and np.array_equal(rids,ids))
    records=rows(OUT/'mobility/mission_metrics.csv');lookup={(r['case_id'],int(r['realization_id']),int(r['lambda_index']),r['method']):r for r in records}
    check('9600 complete metric records',len(lookup)==len(records)==9600)
    methods=('Stationary','Greedy','DP');metrics=('K','U','D','availability','unavailability_percent','repositionings','blocked_slots','positive_slots')
    expected_values={};dominance=0;slot_count=0
    for ci,case in enumerate(cases):
        cid=case['case_id'];values=np.empty((100,2,3,8))
        for rid in range(100):
            S=(~C[ci,rid])*K[:,None]
            for li,lam in enumerate(lams):
                objectives=[]
                for si,method in enumerate(methods):
                    path=paths[ci,rid,li,si];r=lookup[cid,rid,li,method]
                    check('path feasible '+str((cid,rid,li,method)),np.all((path>=0)&(path<100)) and np.all(feasible[path[:-1],path[1:]]))
                    rates=S[path,np.arange(30)];D=float(distance[path[:-1],path[1:]].sum());mu=float(rates.mean());U=mu-lam*D/1000
                    Apos=int(np.count_nonzero(rates>0));block=int(C[ci,rid,path,np.arange(30)].sum())
                    expected=[mu,U,D,Apos/30,100*(1-Apos/30),int(np.count_nonzero(np.diff(path))),block,Apos]
                    check('path metrics '+str((cid,rid,li,method)),same(expected,[float(r[k]) for k in metrics]))
                    check('initial/final/max step '+str((cid,rid,li,method)),int(r['initial_position_index'])==int(path[0]) and int(r['final_position_index'])==int(path[-1]) and same(float(r['max_transition_m']),distance[path[:-1],path[1:]].max()))
                    if si==0:check('P2 direct max/tie '+str((cid,rid,li)),np.all(path==int(np.argmax(S.mean(axis=1)))))
                    if si==1:
                        choices=[int(np.argmax(S[:,0]))]
                        for n in range(1,30):choices.append(int(np.argmax(np.where(feasible[choices[-1]],S[:,n]-30*lam*distance[choices[-1]]/1000,-np.inf))))
                        check('Greedy current-slot replay '+str((cid,rid,li)),np.array_equal(path,choices))
                    objectives.append(U);values[rid,li,si]=expected;slot_count+=30
                F=S[:,0].copy()
                for n in range(1,30):F=S[:,n]+np.max(np.where(feasible,F[:,None]-30*lam*distance/1000,-np.inf),axis=0)
                check('independent cumulative Bellman '+str((cid,rid,li)),same(float(F.max()/30),objectives[2]))
                check('objective dominance '+str((cid,rid,li)),objectives[2]+1e-12>=max(objectives[:2]));dominance+=2
            check('DP distance nonincreasing with lambda '+str((cid,rid)),values[rid,1,2,2]<=values[rid,0,2,2]+1e-9)
            check('P2 invariant to lambda '+str((cid,rid)),same(values[rid,0,0],values[rid,1,0]))
        expected_values[cid]=values
    for before,after in zip(probability,probability[1:]):
        a=expected_values[before['case_id']];b=expected_values[after['case_id']]
        check('optimal U nonincreasing with p '+before['case_id'],b[:,:,[0,2],1]<=a[:,:,[0,2],1]+1e-12)
    with np.load(A/'existing_data/paths.npz',allow_pickle=False) as z:
        for ci,case in enumerate(cases):
            if case['stage_a_case_id'] is not None:check('exact shared Stage A paths '+case['case_id'],np.array_equal(paths[ci],z['paths_'+case['stage_a_case_id']]))
    summary={(r['case_id'],int(r['lambda_index']),r['method']):r for r in rows(OUT/'mobility/aggregate_statistics.csv')}
    paired={(r['case_id'],int(r['lambda_index']),r['baseline'],r['metric']):r for r in rows(OUT/'mobility/paired_improvements.csv')}
    check('statistics coverage',len(summary)==96 and len(paired)==256)
    with np.load(A/'existing_data/bootstrap_counts.npz',allow_pickle=False) as z:counts=z['counts']
    weights=counts.astype(float)/100
    for cid,values in expected_values.items():
        for li in range(2):
            v=values[:,li];bs=(weights@v.reshape(100,-1)).reshape(20000,3,8)
            for si,method in enumerate(methods):
                r=summary[cid,li,method]
                for ki,metric in enumerate(metrics):
                    expected=[v[:,si,ki].mean(),v[:,si,ki].std(ddof=1),np.median(v[:,si,ki]),*np.percentile(bs[:,si,ki],[2.5,97.5])]
                    check('statistics '+str((cid,li,method,metric)),same(expected,[float(r[metric+'_'+key]) for key in ('mean','sd','median','ci95_low','ci95_high')]))
            for bi,baseline in enumerate(methods[:2]):
                for ki in (0,1,2,3):
                    metric=metrics[ki];r=paired[cid,li,baseline,metric];diff=v[:,2,ki]-v[:,bi,ki];bootdiff=bs[:,2,ki]-bs[:,bi,ki]
                    expected=[diff.mean(),diff.std(ddof=1),np.median(diff),*np.percentile(bootdiff,[2.5,97.5])]
                    check('paired CI '+str((cid,li,baseline,metric)),same(expected,[float(r[k]) for k in ('mean','sd','median','ci95_low','ci95_high')]))
                    den=float(v[:,bi,ki].mean());valid=metric in ('K','U') and den>1e-12
                    if valid:
                        check('paired ratio '+str((cid,li,baseline,metric)),same(100*diff.mean()/den,float(r['ratio_of_means_percent'])) and same(np.percentile(100*bootdiff/bs[:,bi,ki],[2.5,97.5]),[float(r['ratio_ci95_low']),float(r['ratio_ci95_high'])]))
                    else:check('undefined ratio '+str((cid,li,baseline,metric)),all(r[k]=='' for k in ('ratio_of_means_percent','ratio_ci95_low','ratio_ci95_high')))
                    tol=1e-9 if metric=='D' else 1e-12
                    check('paired mission signs '+str((cid,li,baseline,metric)),[int(r[k]) for k in ('strict_positive','ties','negative')]==[int(np.sum(diff>tol)),int(np.sum(abs(diff)<=tol)),int(np.sum(diff<-tol))])
    plotted=rows(OUT/'figures/plotted_points.csv');render=js(OUT/'figures/render_metadata.json')
    check('234 actual primary artist points',len(plotted)==render['points']==234)
    for i,r in enumerate(plotted):
        cid=r['case_id'];li=int(r['lambda_index']);metric=r['metric'];panel=int(r['panel'])
        if r['baseline']:
            source=paired[cid,li,r['baseline'],'U'];expected=[float(source[k]) for k in ('mean','ci95_low','ci95_high')]
        else:
            source=summary[cid,li,r['method']];scale=100 if metric=='availability' else 1
            expected=[float(source[metric+'_'+k])*scale for k in ('mean','ci95_low','ci95_high')]
        check('actual plotted value/CI '+str(i),np.array_equal(expected,[float(r[k]) for k in ('y','ci95_low','ci95_high')]))
        check('plotted membership/lambda '+str(i),any(m['case_id']==cid and m['axis']==r['axis'] and m['value']==float(r['x']) for m in members) and float(r['lambda_bits_per_use'])==c['lambda_values'][li])
        meta=render['figures'][r['figure']]['panels'][panel-1]
        check('whole CI/zero visible '+str(i),meta['ylim'][0]<=min(0,*expected) and meta['ylim'][1]>=max(0,*expected))
    visual=js(OUT/'validation/visual_review.json');check('four images actually reviewed',visual['status']=='CURRENTLY_VERIFIED_PASS' and len(visual['images'])==4)
    for name,meta in render['figures'].items():
        check('layout inside canvas '+name,not meta['layout_issues'])
        check('vector PDF '+name,b'/Subtype /Image' not in (OUT/'figures'/(name+'.pdf')).read_bytes())
        png=OUT/'figures'/(name+'.png');check('reviewed PNG hash '+name,sha(png)==visual['images'][name]['sha256'])
        with Image.open(png) as im:check('350dpi PNG '+name,im.size==(2520,1190) and all(abs(v-350)<.1 for v in im.info['dpi']))
    findings=js(OUT/'findings.json')
    for axis,data in findings.items():
        for r in data:
            cid=r['case_id'];dp=summary[cid,1,'DP']
            check('report finding '+axis+'/'+cid,all(same(r[k],float(dp[k+'_mean'])) for k in ('K','U','D','availability')) and same(r['gain_over_P2_percent'],float(paired[cid,1,'Stationary','U']['ratio_of_means_percent'])) and same(r['gain_over_Greedy_percent'],float(paired[cid,1,'Greedy','U']['ratio_of_means_percent'])))
    effects=rows(OUT/'mobility/parameter_effects.csv');check('42 cloud-only effect spans',len(effects)==42)
    for r in effects:
        mm=sorted([m for m in members if m['axis']==r['axis']],key=lambda m:m['value'])
        if r['method'].startswith('DP-minus-'):
            baseline=r['method'].removeprefix('DP-minus-');values=np.array([float(paired[m['case_id'],1,baseline,'U']['mean']) for m in mm])
        else:values=np.array([float(summary[m['case_id'],1,r['method']][r['metric']+'_mean']) for m in mm])
        check('cloud effect span '+str((r['axis'],r['method'],r['metric'])),same([np.ptp(values),values.min(),values.max(),mm[int(values.argmin())]['value'],mm[int(values.argmax())]['value']],[float(r[k]) for k in ('span','minimum','maximum','argmin','argmax')]))
    for name in ('report_vi.md','figure_captions_en.md'):
        text=(OUT/name).read_text(encoding='utf-8')
        check('scope warnings '+name,'UNVALIDATED_SECURITY_MODEL' in text and 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS' in text)
        check('links '+name,all((OUT/link).exists() or link in ('validation_report.md','validation/final_receipt.json') for link in re.findall(r'\]\(([^)]+)\)',text)))
    for p in sorted(OUT.rglob('*')):
        if p.suffix in ('.py','.md','.json','.csv') and p.name not in ('final_receipt.json','validation_report.md','checks.json'):
            check('whitespace '+p.relative_to(OUT).as_posix(),all(line==line.rstrip() for line in p.read_text(encoding='utf-8-sig').splitlines()))
    for n in s['allowed_new_code']:check('new code whitespace '+n,all(line==line.rstrip() for line in (ROOT/n).read_text(encoding='utf-8').splitlines()))
    body=dict(status='CURRENTLY_VERIFIED_PASS',named_checks=len(CHECKS),checks=CHECKS,protected_files=len(s['protected_files']),
              metric_records=9600,selected_slot_values=slot_count,literal_DP_optima=3200,DP_dominance_comparisons=dominance,
              new_cloud_masks=300,archived_mask_replays=1300,new_mobility_solver_pairs=1400,baseline_solver_pairs=200,
              actual_plotted_points=234,current_tests=9,new_physical_SKR=0,new_source_moments=0,new_bootstrap_draws=0,
              scientific_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
    report=f'''# Stage B validation

CURRENTLY_VERIFIED_PASS: {len(CHECKS)} named checks and9 current boundary tests.

- All{len(s['protected_files'])} startup files preserved except five authorized ledgers; every input and producer hash authenticated,Git branch/HEAD unchanged,whitespace clean. Stage A and its report continuation preserved.
- Only300 newly generated masks at p=.3/.5/.7;1300 archived masks replayed exactly. Independent SciPy Cholesky/PCG64 AR reconstruction matches every latent state and binary threshold;112 mission-cluster cloud calibration checks pass. Latent and Bernoulli targets independently agree via Plackett integration. Probability masks nested;initial slot shared across rho.
- Baseline600 records and paths reproduced at both fixed penalties. All9600 trajectory metrics and{slot_count} selected-slot values reconstructed;3200 cumulative Bellman optima and{dominance} objective-dominance comparisons pass. Every Greedy current-slot choice replayed. P2 lambda invariance,DP distance monotonicity in lambda and optimal U monotonicity under nested p masks checked. No imposed trend for availability,Greedy,ell orrho.
- All96 summary rows and256 paired contrasts independently verified,including means/SD/median,paired signs,ratios and20,000 whole-mission percentile CIs using original Stage A count vectors. No new bootstrap draws;undefined ratios stay empty. CIs are pointwise,not simultaneous or quantum-security bounds.
- Four vector-PDF/350dpi-PNG figures,234 actual artist points/CI and all reviewed image hashes match saved CSVs;report links and findings checked. No smoothing,extra simulation points or original figure changes.

UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Stage B cloud-only authorization does not change scientific/security/frozen/cache/baseline/threshold/lifecycle status. Frozen historical-hash discrepancy,Objective C USER_STOPPED,synthetic finite-grid/catalog,offline P2/DP and mixed MI/Holevo limitations remain. No new physical SKR or C,w,training/test/held-out,external manuscript edit,commit/push.

Recheck with project Python: `scripts/run_mobility_cloud_sensitivity.py --stage verify`. Completed receipts cannot be silently replaced.
'''
    target=OUT/'validation/final_receipt.json'
    if target.exists():
        if js(OUT/'validation/checks.json')!=body or (OUT/'validation_report.md').read_text(encoding='utf-8')!=report:raise AssertionError('Completed verification changed')
    else:
        (OUT/'validation/checks.json').write_text(json.dumps(body,indent=2)+'\n',encoding='utf-8',newline='\n')
        (OUT/'validation_report.md').write_text(report,encoding='utf-8',newline='\n')
    result=dict(body,producer_sha256={n:sha(ROOT/n) for n in s['allowed_new_code']},
                artifact_sha256={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='final_receipt.json' and p.suffix!='.log'})
    if target.exists():
        if js(target)!=result:raise AssertionError('Completed Stage B receipt or artifacts changed')
    else:target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('CURRENTLY_VERIFIED_PASS',len(CHECKS),'checks;',len(result['artifact_sha256']),'artifact hashes;Stage B cloud-only complete',flush=True)


if __name__=='__main__':verify()
