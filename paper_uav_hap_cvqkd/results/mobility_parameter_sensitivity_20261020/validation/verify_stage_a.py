"""Independent saved-array verification; no production solver/evaluator imports."""
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
METHODS=('Stationary','Greedy','DP')
METRICS=('K','U','D','availability','unavailability_percent','repositionings','blocked_slots','positive_slots')
NAMES=('fig_A1_positions_objective_skr','fig_A2_positions_unavailability','fig_B_speed_sensitivity',
       'fig_C_cloud_probability_sensitivity','fig_D_duration_sensitivity','fig_E_spatial_correlation_sensitivity')
CHECKS=[]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
def save(p,value):Path(p).write_bytes((json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8'))
def check(name,condition):
    if not bool(np.all(condition)):raise AssertionError(name)
    CHECKS.append(name)
def close(name,a,b):check(name,np.allclose(a,b,atol=1e-12,rtol=1e-12))
def number(value):return None if value=='' else float(value)


def verify(c,out):
    startup=js(out/'startup_manifest.json');manifest=js(out/'input_manifest.json');proto=js(out/'protocol.json')
    check('protocol equals current approved configuration',proto['settings']==c and c['stage']=='A' and c['stage_b_allowed'] is False)
    for name,digest in startup['protected_files'].items():
        if name not in startup['allowed_changed']:
            if not (ROOT/name).is_file() or sha(ROOT/name)!=digest:raise AssertionError('Protected file changed: '+name)
    check('all5118 protected files except authorized ledgers preserved',True)
    for name,digest in manifest['bindings'].items():check('input identity '+name,sha(ROOT/name)==digest)
    for command,key in ((['git','branch','--show-current'],'branch'),(['git','rev-parse','HEAD'],'commit')):
        check('unchanged Git '+key,subprocess.check_output(command,cwd=ROOT,text=True).strip()==startup[key])
    listed=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','--','.'],cwd=ROOT,text=True).splitlines()
    check('new files only in authorized namespaces',all(n in startup['protected_files'] or n in startup['allowed_new_code'] or n.startswith(startup['allowed_output_prefix']) for n in listed))
    check('git diff whitespace',subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode==0)
    check('Stage B and cloud generation absent',not (out/'additional_clouds').exists() and not list(out.rglob('cloud_states.npz')) and c['new_cloud_generation_allowed'] is False)
    for name in ('audit','compute','aggregate'):
        receipt=js(out/'validation'/(name+'.json'));check('stage PASS '+name,receipt['status']=='CURRENTLY_VERIFIED_PASS')
        for path,digest in receipt['artifact_sha256'].items():check('stage artifact '+name+':'+path,sha(out/path)==digest)
    test=js(out/'validation/test_receipt.json');check('18 current tests',test['status']=='CURRENTLY_VERIFIED_PASS' and test['tests_run']==18 and test['failures']==test['errors']==0)
    for name,digest in test['producer_sha256'].items():check('tested producer '+name,sha(ROOT/name)==digest)
    base=ROOT/c['reference_directory'];archive=ROOT/c['archive_directory'];lam=np.array(c['lambda_values'])
    xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in rows(base/'positions.csv')])
    K=np.array([float(r['K_star']) for r in rows(base/'p1/winners.csv')])
    with np.load(archive/'cloud_states.npz',allow_pickle=False) as z:C=z['blocked']
    check('fixed absolute lambda values',np.array_equal(lam,[0,9.468026677248516e-6]))
    check('archive16x100x100x30 boolean masks',C.shape==(16,100,100,30) and C.dtype==np.bool_)
    check('all current P1 rates positive finite',len(K)==100 and np.isfinite(K).all() and np.all(K>0))
    cases=proto['cases'];bycase={r['case_id']:r for r in cases};members=proto['memberships'];order=proto['selection_order']
    check('26 distinct cases and30 axis memberships',len(cases)==len(bycase)==26 and len(members)==30)
    check('case scenario IDs only approved archived fields',sorted({r['scenario_id'] for r in cases})==[0,2,3,4,5,8,9,10,11])
    check('same baseline shared across5axes',sum(r['case_id']=='base' for r in members)==5)
    check('spatial-only original corners and permutation',order[:4]==[0,9,90,99] and sorted(order)==list(range(100)))
    quadrants=(xy[:,0]>=500).astype(int)+2*(xy[:,1]>=500).astype(int)
    for n in range(4,100):
        chosen=order[:n];count=np.bincount(quadrants[chosen],minlength=4)
        eligible=[j for j in range(100) if j not in chosen and count[quadrants[j]]==count.min()]
        distances={j:float(np.min(np.sum((xy[chosen]-xy[j])**2,axis=1))) for j in eligible}
        expected=sorted(eligible,key=lambda j:(-distances[j],j))[0]
        check('balanced maximin selection rank '+str(n+1),order[n]==expected)
    actualsubsets=rows(out/'subsets.csv');diags={int(r['J']):r for r in rows(out/'subset_diagnostics.csv')}
    previous=set()
    for J in c['candidate_counts']:
        ids=sorted(order[:J]);actual=[int(r['position_index']) for r in actualsubsets if int(r['J'])==J]
        check('nested subset IDs '+str(J),ids==actual and previous<=set(ids));previous=set(ids)
        count=np.bincount(quadrants[ids],minlength=4);check('quadrant balance '+str(J),count.max()-count.min()<=1)
        p=xy[ids];d=np.sqrt(np.sum((p[:,None]-p[None,:])**2,axis=-1));graph=d<=300
        pending=set(range(J));components=0
        while pending:
            stack=[pending.pop()];components+=1
            while stack:
                current=stack.pop();neighbors={j for j in pending if graph[current,j]};stack.extend(neighbors);pending-=neighbors
        close('subset graph diagnostics '+str(J),[components,np.sum(graph.sum(axis=1)==1),graph.sum()],[float(diags[J][k]) for k in ('components','isolated_positions','feasible_directed_edges_including_stay')])
    specifications={'J':'candidate_counts','speed':'speeds_m_per_s','horizon':'horizons','probability':'probabilities','spatial':'spatial_lengths_m'}
    scenarios=js(archive/'cloud_scenarios.json')
    for axis,field in specifications.items():
        mm=sorted([r for r in members if r['axis']==axis],key=lambda r:r['value'])
        check('exact approved sweep '+axis,[r['value'] for r in mm]==c[field])
        for member in mm:
            case=bycase[member['case_id']];key={'horizon':'Nt','J':'J','speed':'speed','probability':'probability','spatial':'spatial'}[axis]
            check('physical parameter matches plotted membership '+str((axis,member['value'])),case[key]==member['value'])
            for other,default in (('J',100),('Nt',30),('speed',15),('probability',.4),('spatial',250),('rho',.9)):
                if other!=key:check('unrelated parameter fixed '+str((axis,member['value'],other)),case[other]==default)
    for case in cases:
        cid=case['case_id'];sid=case['scenario_id'];ids=case['indices'];nt=case['Nt']
        check('original coordinate IDs '+cid,ids==sorted(order[:case['J']]) and len(ids)==case['J'] and 0<nt<=30)
        check('scenario parameters '+cid,(case['probability'],case['spatial'],case['rho'])==tuple(scenarios[sid][k] for k in ('probability','correlation_length_m','temporal_rho')))
    records=rows(out/'existing_data/mission_metrics.csv');lookup={(r['case_id'],int(r['realization_id']),int(r['lambda_index']),r['method']):r for r in records}
    check('15600 complete unique records',len(records)==len(lookup)==15600 and set(lookup)=={(case['case_id'],r,l,m) for case in cases for r in range(100) for l in range(2) for m in METHODS})
    pathfile=np.load(out/'existing_data/paths.npz',allow_pickle=False)
    check('path member set exact',set(pathfile.files)=={'lambda_values','realization_ids'}|{'paths_'+case['case_id'] for case in cases})
    check('path metadata',np.array_equal(pathfile['lambda_values'],lam) and np.array_equal(pathfile['realization_ids'],np.arange(100)))
    arrays={};slot_count=0
    for case in cases:
        cid=case['case_id'];nt=case['Nt'];speed=case['speed'];ids=np.array(case['indices']);sid=case['scenario_id'];paths=pathfile['paths_'+cid]
        check('path coverage '+cid,paths.shape==(100,2,3,nt) and np.issubdtype(paths.dtype,np.integer) and np.isin(paths,ids).all())
        checkpoint=out/'existing_data'/('checkpoint_'+cid+'.npz')
        with np.load(checkpoint,allow_pickle=False) as z:
            case_hash=hashlib.sha256(json.dumps(case,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            check('checkpoint identity '+cid,str(z['input_sha256'])==sha(out/'input_manifest.json') and str(z['case_sha256'])==case_hash and np.array_equal(z['paths'],paths))
        for field,target in (('J',case['J']),('Nt',nt),('max_speed_m_per_s',speed),('scenario_id',sid),('probability',case['probability']),('correlation_length_m',case['spatial']),('temporal_rho',case['rho'])):
            check('metric configuration column '+cid+field,all(float(r[field])==target for key,r in lookup.items() if key[0]==cid))
        S=(~C[sid,:,:,:nt])*K[None,:,None]
        rates=S[np.arange(100)[:,None,None,None],paths,np.arange(nt)]
        blocked=C[sid,np.arange(100)[:,None,None,None],paths,np.arange(nt)]
        legs=np.sqrt(np.sum(np.diff(xy[paths],axis=3)**2,axis=-1));D=legs.sum(axis=-1)
        check('all speed constraints '+cid,legs<=speed*20+1e-12)
        values={'K':rates.mean(axis=-1),'D':D,'U':rates.mean(axis=-1)-lam[None,:,None]*D/1000,
            'availability':np.count_nonzero(rates>0,axis=-1)/nt,'unavailability_percent':100*(1-np.count_nonzero(rates>0,axis=-1)/nt),
            'repositionings':np.count_nonzero(np.diff(paths,axis=-1),axis=-1),'blocked_slots':blocked.sum(axis=-1),'positive_slots':np.count_nonzero(rates>0,axis=-1)}
        for key,value in values.items():
            actual=np.array([[[float(lookup[cid,rid,li,m][key]) for m in METHODS] for li in range(2)] for rid in range(100)])
            close('600 reconstructed '+key+' '+cid,actual,value)
        check('DP dominates both baselines '+cid,values['U'][:,:,2,None]>=values['U'][:,:,:2]-1e-12-1e-12*abs(values['U'][:,:,:2]))
        check('P2 zero distance and lambda invariant '+cid,np.all(D[:,:,0]==0) and np.array_equal(values['K'][:,0,0],values['K'][:,1,0]))
        close('lambda0 objective equals usable SKR '+cid,values['U'][:,0],values['K'][:,0])
        check('blocked selected values exactly zero '+cid,np.all(rates[blocked]==0) and np.array_equal(values['positive_slots'],nt-values['blocked_slots']))
        inverse=np.full(100,-1,dtype=int);inverse[ids]=np.arange(len(ids));p=xy[ids]
        d=np.sqrt(np.sum((p[:,None]-p[None,:])**2,axis=-1));local=S[:,ids,:]
        for li,penalty in enumerate(lam):
            expected=ids[np.argmax(local[:,:,0],axis=1)]
            check('Greedy first slot '+str((cid,li)),expected==paths[:,li,1,0])
            for n in range(1,nt):
                prev=inverse[paths[:,li,1,n-1]]
                score=np.where(d[prev]<=speed*20,local[:,:,n]-nt*penalty*d[prev]/1000,-np.inf)
                expected=ids[np.argmax(score,axis=1)]
                check('causal Nt-lambda Greedy '+str((cid,li,n)),expected==paths[:,li,1,n])
            independent=[]
            for rid in range(100):
                F=local[rid,:,0].copy()
                for n in range(1,nt):F=local[rid,:,n]+np.max(np.where(d<=speed*20,F[:,None]-nt*penalty*d/1000,-np.inf),axis=0)
                independent.append(float(F.max()/nt))
            close('100 cumulative Bellman optima '+str((cid,li)),independent,values['U'][:,li,2])
        arrays[cid]=values;slot_count+=int(paths.size)
    check('423000 selected-slot values reconstructed',slot_count==423000)
    monotone_count=0
    for axis,methods,increasing in (('J',(0,2),True),('speed',(2,),True),('probability',(0,2),False)):
        mm=sorted([r for r in members if r['axis']==axis],key=lambda r:r['value'])
        for before,after in zip(mm,mm[1:]):
            for si in methods:
                delta=arrays[after['case_id']]['U'][:,:,si]-arrays[before['case_id']]['U'][:,:,si]
                check('guaranteed monotonic '+str((axis,before['value'],after['value'],METHODS[si])),delta>=-1e-12 if increasing else delta<=1e-12)
                monotone_count+=delta.size
    for member in [m for m in members if m['axis']=='speed']:
        cid=member['case_id'];close('P2 speed invariance '+cid,arrays[cid]['K'][:,:,0],arrays['base']['K'][:,:,0])
        if member['value']<5:close('no movement DP equals P2 '+cid,arrays[cid]['U'][:,:,2],arrays[cid]['U'][:,:,0])
    for member in [m for m in members if m['axis']=='horizon']:
        nt=bycase[member['case_id']]['Nt'];check('lambda0 Greedy causal horizon prefix '+str(nt),np.array_equal(pathfile['paths_'+member['case_id']][:,0,1],pathfile['paths_base'][:,0,1,:nt]))
    mm=sorted([r for r in members if r['axis']=='probability'],key=lambda r:r['value'])
    check('archived probability masks nested',all(not np.any(C[bycase[a['case_id']]['scenario_id']]&~C[bycase[b['case_id']]['scenario_id']]) for a,b in zip(mm,mm[1:])))
    summaryrows=rows(out/'existing_data/aggregate_statistics.csv');summary={(r['case_id'],int(r['lambda_index']),r['method']):r for r in summaryrows}
    pairedrows=rows(out/'existing_data/paired_improvements.csv');paired={(r['case_id'],int(r['lambda_index']),r['baseline'],r['metric']):r for r in pairedrows}
    check('156 method summaries and416 paired comparisons',len(summaryrows)==len(summary)==156 and len(pairedrows)==len(paired)==416)
    with np.load(out/'existing_data/bootstrap_counts.npz',allow_pickle=False) as z:counts=z['counts']
    check('20000 whole-mission bootstrap count rows',counts.shape==(20000,100) and np.all(counts>=0) and np.all(counts.sum(axis=1)==100))
    rng=np.random.default_rng(20261020);draws=rng.integers(0,100,size=(20000,100))
    independent_counts=np.array([np.bincount(draw,minlength=100) for draw in draws],dtype=np.int16)
    check('bootstrap seed and paired resampling identity',np.array_equal(counts,independent_counts))
    for ci,case in enumerate(cases):
        cid=case['case_id']
        for li in range(2):
            X=np.stack([arrays[cid][k][:,li,:] for k in METRICS],axis=-1)
            boot=(counts.astype(float)/100@X.reshape(100,-1)).reshape(20000,3,len(METRICS))
            if ci==0:
                close('direct draw means agree with weighted bootstrap '+str(li),X[draws[:100]].mean(axis=1),boot[:100])
            for si,method in enumerate(METHODS):
                row=summary[cid,li,method];check('100 summary mission IDs '+str((cid,li,method)),int(row['missions'])==100)
                for ki,key in enumerate(METRICS):
                    x=X[:,si,ki];q=np.quantile(boot[:,si,ki],[.025,.975])
                    close('mean SD median CI '+str((cid,li,method,key)),[float(row[key+'_'+k]) for k in ('mean','sd','median','ci95_low','ci95_high')],[x.mean(),x.std(ddof=1),np.median(x),*q])
            for bi,baseline in enumerate(METHODS[:2]):
                for key in ('K','U','D','availability'):
                    ki=METRICS.index(key);x=X[:,2,ki]-X[:,bi,ki];bs=boot[:,2,ki]-boot[:,bi,ki];q=np.quantile(bs,[.025,.975]);row=paired[cid,li,baseline,key]
                    close('paired mean SD median CI '+str((cid,li,baseline,key)),[float(row[k]) for k in ('mean','sd','median','ci95_low','ci95_high')],[x.mean(),x.std(ddof=1),np.median(x),*q])
                    tol=1e-9 if key=='D' else 1e-12
                    check('paired sign counts '+str((cid,li,baseline,key)),[int(row[k]) for k in ('strict_positive','ties','negative')]==[int(np.sum(x>tol)),int(np.sum(abs(x)<=tol)),int(np.sum(x<-tol))])
                    den=X[:,bi,ki].mean();valid=key in ('K','U') and den>1e-12
                    if valid:
                        close('ratio of paired means '+str((cid,li,baseline,key)),float(row['ratio_of_means_percent']),100*x.mean()/den)
                        if np.all(boot[:,bi,ki]>1e-12):close('paired ratio CI '+str((cid,li,baseline,key)),[float(row[k]) for k in ('ratio_ci95_low','ratio_ci95_high')],np.quantile(100*bs/boot[:,bi,ki],[.025,.975]))
                    else:check('undefined ratio not fabricated '+str((cid,li,baseline,key)),row['ratio_of_means_percent']==row['ratio_ci95_low']==row['ratio_ci95_high']=='')
    for row in rows(out/'existing_data/parameter_effects.csv'):
        axis=row['axis'];method=row['method'];metric=row['metric'];mm=sorted([r for r in members if r['axis']==axis],key=lambda r:r['value'])
        if method.startswith('DP-minus-'):
            bi=METHODS.index(method.removeprefix('DP-minus-'));y=np.array([(arrays[m['case_id']][metric][:,1,2]-arrays[m['case_id']][metric][:,1,bi]).mean() for m in mm])
        else:y=np.array([arrays[m['case_id']][metric][:,1,METHODS.index(method)].mean() for m in mm])
        close('finite-range effect '+str((axis,method,metric)),[float(row[k]) for k in ('minimum','maximum','span','endpoint_change')],[y.min(),y.max(),np.ptp(y),y[-1]-y[0]])
    jm=sorted([r for r in members if r['axis']=='J'],key=lambda r:r['value'])
    increments=rows(out/'existing_data/J_incremental_gains.csv')
    check('15 paired J increments',len(increments)==15)
    for row in increments:
        before=next(r['case_id'] for r in jm if r['value']==int(row['J_before']));after=next(r['case_id'] for r in jm if r['value']==int(row['J_after']));si=METHODS.index(row['method'])
        delta=arrays[after]['U'][:,1,si]-arrays[before]['U'][:,1,si];q=np.quantile((counts.astype(float)/100)@delta,[.025,.975])
        close('paired J incremental mean CI '+str((row['J_before'],row['J_after'],row['method'])),[float(row[k]) for k in ('mean','ci95_low','ci95_high','gain_per_added_position')],[delta.mean(),*q,delta.mean()/(int(row['J_after'])-int(row['J_before']))])
    check('all10 baseline lambda statistics preserved',rows(out/'existing_data/lambda_reference.csv')==rows(base/'analysis/tables/method_comparison.csv'))
    findings=js(out/'findings.json');effects=rows(out/'existing_data/parameter_effects.csv')
    for label,method,key in (('SKR','DP','K'),('availability','DP','availability'),('mobility_gain_vs_P2','DP-minus-Stationary','U'),('gain_vs_Greedy','DP-minus-Greedy','U')):
        expected=max((r for r in effects if r['method']==method and r['metric']==key),key=lambda r:float(r['span']))
        actual=findings['strongest_observed_spans'][label]
        check('reported strongest parameter '+label,actual['axis']==expected['axis'])
        close('reported strongest span '+label,actual['span'],float(expected['span']))
    for method in METHODS:
        for key in ('K','availability'):
            expected=max((r for r in effects if r['method']==method and r['metric']==key),key=lambda r:float(r['span']))
            actual=findings['method_specific_strongest_spans'][method][key]
            check('method-specific strongest parameter '+method+key,actual['axis']==expected['axis'])
            close('method-specific strongest span '+method+key,actual['span'],float(expected['span']))
    for axis,observation in findings['observations'].items():
        mm=sorted([r for r in members if r['axis']==axis],key=lambda r:r['value'])
        check('reported parameter values '+axis,observation['values']==[r['value'] for r in mm])
        for si,method in enumerate(METHODS):
            for key in ('K','U','D','availability'):
                y=np.array([arrays[r['case_id']][key][:,1,si].mean() for r in mm]);actual=observation['methods'][method][key]
                close('reported numeric trend '+str((axis,method,key)),[actual[k] for k in ('first','last','minimum','maximum')],[y[0],y[-1],y.min(),y.max()])
    render=js(out/'existing_data/figures/render_metadata.json')
    check('render PASS and no clipped layout',render['status']=='CURRENTLY_VERIFIED_PASS' and render['layout_issues']==[] and render['point_count']==344)
    check('current plotting producer',render['producer_sha256']==sha(ROOT/'scripts/plot_mobility_parameter_sensitivity.py'))
    points=rows(out/'existing_data/figures/plotted_points.csv');check('344 primary plotted points',len(points)==344)
    memberships={(m['axis'],m['case_id']):m['value'] for m in members}
    for i,row in enumerate(points):
        cid=row['case_id'];li=int(row['lambda_index']);metric=row['metric'];base_method=row['baseline'];method=row['method']
        check('evaluated point x '+str(i),float(row['x'])==memberships[row['axis'],cid] and float(row['lambda_bits_per_use'])==lam[li])
        if base_method:
            expected=paired[cid,li,base_method,'U'];keys=('ratio_of_means_percent','ratio_ci95_low','ratio_ci95_high') if metric=='gain_percent' else ('mean','ci95_low','ci95_high')
            target=[number(expected[k]) for k in keys]
        else:
            expected=summary[cid,li,method];scale=100 if metric=='availability' else 1
            target=[float(expected[metric+'_'+k])*scale for k in ('mean','ci95_low','ci95_high')]
            style={'Stationary':('tab:blue','-','o'),'Greedy':('tab:orange','--','s'),'DP':('tab:red','-','^')}[method]
            if row['figure']==NAMES[2] and li==0 and method!='Stationary':style=(style[0],':' if method=='Greedy' else '-.','v' if method=='Greedy' else 'D')
            check('actual method curve style '+str(i),(row['color'],row['linestyle'],row['marker'])==style)
        actual=[number(row[k]) for k in ('y','ci95_low','ci95_high')]
        if any(x is None for x in target):check('undefined figure point not fabricated '+str(i),actual==target)
        else:close('actual artist data and CI '+str(i),actual,target)
        panel=render['figures'][row['figure']]['panels'][int(row['panel'])-1]
        check('zero and all data bounds visible '+str(i),panel['ylim'][0]<=0<=panel['ylim'][1] and all(x is None or panel['ylim'][0]<=x<=panel['ylim'][1] for x in target))
    visual=js(out/'validation/visual_review.json');check('six actual final images visually reviewed',visual['status']=='CURRENTLY_VERIFIED_PASS' and set(visual['figures'])==set(NAMES))
    for name in NAMES:
        p=out/'existing_data/figures'/(name+'.png')
        with Image.open(p) as image:check('white350dpi PNG '+name,image.size==(2520,1137) and min(image.info['dpi'])>=349 and image.getpixel((0,0))[:3]==(255,255,255))
        pdf=(out/'existing_data/figures'/(name+'.pdf')).read_bytes();check('vector PDF '+name,pdf.startswith(b'%PDF') and b'/Subtype /Image' not in pdf)
        check('reviewed PNG hash '+name,sha(p)==visual['figures'][name]['png_sha256'])
    check('six source-map rows',len(rows(out/'figure_source_mapping.csv'))==6)
    for name in ('report_vi.md','figure_captions_en.md'):
        text=(out/name).read_text(encoding='utf-8');check('scope warnings '+name,'UNVALIDATED_SECURITY_MODEL' in text and 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS' in text)
        links=re.findall(r'\]\(([^)]+)\)',text)
        check('document link targets '+name,all(link.startswith('https://') or (out/link).exists() or link in ('validation_report.md','validation/final_receipt.json') for link in links))
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.suffix in ('.py','.md','.json','.csv') and p.name not in ('final_receipt.json','independent_checks.json','validation_report.md'):
            check('artifact whitespace '+p.relative_to(out).as_posix(),all(line==line.rstrip() for line in p.read_text(encoding='utf-8-sig').splitlines()))
    for name in startup['allowed_new_code']:check('new implementation whitespace '+name,all(line==line.rstrip() for line in (ROOT/name).read_text(encoding='utf-8').splitlines()))
    audit=js(out/'validation/audit.json');compute=js(out/'validation/compute.json')
    report=f'''# Stage A validation

CURRENTLY_VERIFIED_PASS: {len(CHECKS)} independent named assertions; 18 current deterministic tests. Historical tests are not rerun or counted.

- 26 unique approved configurations, 100 paired mission IDs, two fixed absolute penalties; complete 15,600 metrics and 423,000 selected-slot values reconstructed from original coordinates, current P1 and authenticated archived masks.
- 5,200 independent cumulative Bellman optima match saved DP objectives. All 10,400 mission-wise DP comparisons dominate P2/Greedy within absolute/relative1e−12. Every Greedy step independently reconstructs its current-slot Nt-lambda score and deterministic tie-break.
- {monotone_count} mathematically guaranteed monotonic inequalities checked for nested J, relaxed speed and nested blockage probability. No unsupported monotonic constraint imposed on Greedy, availability, distance versus speed, horizon or spatial length. No-movement DP equals P2; P2 is speed/lambda invariant; lambda0 Greedy prefixes are causal.
- Mean, sample SD, median and every percentile CI independently recomputed. Bootstrap20,000 whole-mission draws, seed20261020, paired weight identity replayed; no cell/slot independence assumption. Ratios use positive baseline mission means; undefined ratios are empty, never fabricated zeros. Intervals are pointwise, not simultaneous or quantum-security bounds.
- 344 actual primary artist points and their unmodified confidence bounds trace to saved CSVs; six reviewed white-background350dpi PNGs and six vector PDFs. Zero is visible; spatial x-axis is explicitly logarithmic; no smoothing or interpolated simulation points.
- All3,000 original baseline metric records and3,000 paths reproduced at all10 old penalties before the batch; maximum residual {audit['max_abs_metric_residual']!r}. Baseline audit used1,000 DP/Greedy pairs plus4 deterministic archived controls; Stage A batch used5,000 new pairs. No physical/channel/source/cloud evaluator calls.
- {manifest['prior_hash_members']} old receipt members authenticated; exact-source payloads and producer hashes bound. All{len(startup['protected_files'])} startup files protected except the five authorized ledger paths; new code/output namespace restricted, Git branch/HEAD unchanged and diff whitespace passes.

UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Stage B NOT_RUN; new cloud scenarios=0, new physical SKR=0, new C,w=0. Frozen historical-hash discrepancy and Objective C USER_STOPPED remain. No production quantum model/cache change, final-test/held-out access, publication/lifecycle/baseline/threshold promotion, external edit, commit or push. These are synthetic finite-catalog/grid, offline P2/DP numerical comparisons, not validated quantum-security or propulsion-energy claims.

Recheck using project Python: `scripts/run_mobility_parameter_sensitivity.py --stage verify`. Completed receipts are checked, never silently replaced.
'''
    body=dict(status='CURRENTLY_VERIFIED_PASS',named_assertions=len(CHECKS),checks=CHECKS,metric_records=15600,selected_slot_values=slot_count,
        literal_DP_optima=5200,DP_dominance_comparisons=10400,guaranteed_monotonic_inequalities=monotone_count,plotted_points=344,
        new_clouds=0,new_physical_SKR=0,new_source_moments=0,stage_b_executed=False,
        protected_files=len(startup['protected_files']),allowed_changed_files=startup['allowed_changed'],
        security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
    target=out/'validation/final_receipt.json'
    if target.exists():
        if (out/'validation_report.md').read_text(encoding='utf-8')!=report:raise AssertionError('Completed validation report changed')
        if js(out/'validation/independent_checks.json')!=body:raise AssertionError('Completed verification checks changed')
    else:
        (out/'validation_report.md').write_bytes(report.encode('utf-8'));save(out/'validation/independent_checks.json',body)
    result=dict(body,producer_sha256={n:sha(ROOT/n) for n in startup['allowed_new_code']},
        artifact_sha256={p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='final_receipt.json' and p.suffix!='.log'})
    if target.exists():
        if js(target)!=result:raise AssertionError('Completed receipt or package artifacts changed')
    else:save(target,result)
    print('CURRENTLY_VERIFIED_PASS',len(CHECKS),'named assertions;',len(result['artifact_sha256']),'artifact hashes; Stage B NOT_RUN',flush=True)
