"""Saved-data arithmetic/provenance checks only; no optimization or RNG draws."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import re
import subprocess

import numpy as np
from PIL import Image

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]
BASE=ROOT/'results/manuscript_mobility_p1_p2_p3_20261019'
A=ROOT/'results/mobility_parameter_sensitivity_20261020'
B=ROOT/'results/mobility_parameter_sensitivity_stage_b_20261020'
CHECKS=[]
METHODS=('Stationary','Greedy','DP')
METRICS=('K','U','D','availability','unavailability_percent','repositionings','blocked_slots','positive_slots')


def js(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
def check(name,condition):
    if not bool(np.all(condition)):raise AssertionError(name)
    CHECKS.append(name)
def same(a,b):return np.allclose(a,b,atol=1e-12,rtol=1e-12)
def describe(v,w):
    return np.array([v.mean(),v.std(ddof=1),np.median(v),*np.percentile(w@v,[2.5,97.5])])
def stat_values(r):return [float(r[k]) for k in ('mean','sd','median','ci95_low','ci95_high')]


def verify():
    startup=js(OUT/'startup_manifest.json');manifest=js(OUT/'input_manifest.json');protocol=js(OUT/'protocol.json')
    changed=[n for n,h in startup['protected_files'].items() if n not in startup['allowed_changed'] and (not (ROOT/n).is_file() or sha(ROOT/n)!=h)]
    check('all5283 prior files preserved except authorized ledgers',not changed)
    for cmd,key in ((['git','branch','--show-current'],'branch'),(['git','rev-parse','HEAD'],'commit')):
        check('Git identity '+key,subprocess.check_output(cmd,cwd=ROOT,text=True).strip()==startup[key])
    files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','--','.'],cwd=ROOT,text=True).splitlines()
    check('new files only in final output namespace',all(n in startup['protected_files'] or n.startswith(startup['allowed_output_prefix']) for n in files))
    check('git diff whitespace',subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode==0)
    for n,h in manifest['bindings'].items():check('authenticated input '+n,sha(ROOT/n)==h)
    for name,r in manifest['external_inputs'].items():check('external reference '+name,sha(Path(r['path']))==r['sha256'])
    check('six historical receipts',len(manifest['receipts'])==6)
    for file in (OUT/'build_final_package.py',Path(__file__)):
        tree=ast.parse(file.read_text(encoding='utf-8'))
        imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
        check('no production imports '+file.name,all(n.split('.')[0] in {'pathlib','csv','hashlib','json','matplotlib','numpy','ast','re','subprocess','PIL'} for n in imports))
        check('no solver/evaluator/RNG references '+file.name,not any(isinstance(n,ast.Attribute) and n.attr in {'random','generate_cloud','optimize_trajectory','greedy_trajectory','security','mi_gh','evaluate_candidate'} for n in ast.walk(tree)))
    cfg=rows(OUT/'tables/configurations.csv');check('29 selected figure configurations',len(cfg)==29)
    for f,expected in ((1,[10,20,40,60,80,100]),(2,[.1,.2,.3,.4,.5,.6,.7,.8]),(3,[0,.3,.6,.9,.98])):
        selected=[r for r in cfg if int(r['figure'])==f]
        check('exact figure selection '+str(f),[float(r['value']) for r in selected]==expected and all(float(r['lambda_bits_per_use'])==9.468026677248516e-6 for r in selected))
    schedule=js(BASE/'mobility/lambda_schedule.json')['values']
    check('all10 penalty values in saved order',[float(r['value']) for r in cfg if int(r['figure'])==4]==schedule)
    check('preserved status flags',protocol['security_status']=='UNVALIDATED_SECURITY_MODEL' and protocol['lifecycle']=='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')

    # Duplicate baseline rows are identified by physical case and exact penalty, not their local lambda index.
    originals={};source_tables={}
    for source,path in ((A,A/'existing_data/mission_metrics.csv'),(B,B/'mobility/mission_metrics.csv'),(BASE,BASE/'mobility/mission_metrics.csv')):
        data=[]
        for r in rows(path):
            if source==BASE:
                r=dict(case_id='base',realization_id=r['realization_id'],lambda_index=r['lambda_index'],lambda_bits_per_use=r['lambda_bits_per_use'],method=r['strategy'],
                       K=r['average_skr_bits_per_use'],U=r['objective_bits_per_use'],D=r['total_distance_m'],availability=r['availability'],
                       unavailability_percent=100*(1-float(r['availability'])),repositionings=r['repositionings'],blocked_slots=r['blocked_slots'],positive_slots=r['positive_slots'])
            data.append(r);key=(r['case_id'],float(r['lambda_bits_per_use']).hex(),int(r['realization_id']),r['method'])
            if key in originals:check('shared raw values '+str(key),same([float(r[m]) for m in METRICS],[float(originals[key][m]) for m in METRICS]))
            else:originals[key]=r
        source_tables[source]={(r['case_id'],int(r['realization_id']),int(r['lambda_index']),r['method']):r for r in data}
    check('22200 unique original mission-method records',len(originals)==22200)
    dominance=0
    for key,r in originals.items():
        if key[-1]!='DP':continue
        for baseline in METHODS[:2]:
            base=originals[(*key[:-1],baseline)]
            check('saved objective dominance '+str((*key[:-1],baseline)),float(r['U'])+1e-12>=float(base['U']));dominance+=1
    check('14800 unique mission-wise comparisons',dominance==14800)

    selected=rows(OUT/'tables/selected_missions.csv');lookup={(int(r['figure']),r['case_id'],int(r['lambda_index']),int(r['realization_id']),r['method']):r for r in selected}
    check('8700 selected records',len(lookup)==len(selected)==8700)
    xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in rows(BASE/'positions.csv')]);winners=rows(BASE/'p1/winners.csv');K=np.array([float(r['K_star']) for r in winners])
    check('all100 P1 sources identical and positive',len(winners)==100 and np.all(K>0) and {(float(r['nu_raw']),float(r['VA'])) for r in winners}=={(.125,8.)} and len({r['ensemble_hash'] for r in winners})==1)
    roster=rows(BASE/'source_roster.csv');check('233 sources andMB boundary',len(roster)==233 and sum(r['family']=='MB' for r in roster)==197 and max(float(r['VA']) for r in roster if r['family']=='MB')==8)
    with np.load(BASE/'clouds/states.npz',allow_pickle=False) as z:base_cloud=z['blocked']
    with np.load(BASE/'mobility/paths.npz',allow_pickle=False) as z:base_paths=z['paths']
    with np.load(A/'existing_data/paths.npz',allow_pickle=False) as z:apaths={k:z[k] for k in z.files}
    with np.load(B/'mobility/paths.npz',allow_pickle=False) as z:bpaths=z['paths']
    with np.load(B/'clouds/states.npz',allow_pickle=False) as z:bcloud=z['blocked']
    bcase={r['case_id']:i for i,r in enumerate(js(B/'protocol.json')['cases'])}
    subset={J:{int(r['position_index']) for r in rows(A/'subsets.csv') if int(r['J'])==J} for J in (10,20,40,60,80,100)}
    slots=0
    for r in selected:
        f,cid,li,rid,method=int(r['figure']),r['case_id'],int(r['lambda_index']),int(r['realization_id']),r['method'];si=METHODS.index(method)
        source=ROOT/r['source'];original=source_tables[source][cid,rid,li,method]
        check('selected raw identity '+str((f,cid,li,rid,method)),same([float(r[k]) for k in METRICS],[float(original[k]) for k in METRICS]))
        if f==1:path=apaths['paths_'+cid][rid,li,si];cloud=base_cloud[rid];allowed=subset[int(float(r['parameter_value']))]
        elif f in (2,3):path=bpaths[bcase[cid],rid,li,si];cloud=bcloud[bcase[cid],rid];allowed=set(range(100))
        else:path=base_paths[rid,li,si];cloud=base_cloud[rid];allowed=set(range(100))
        check('saved feasible path '+str((f,cid,li,rid,method)),len(path)==30 and set(path.tolist())<=allowed and np.all(np.linalg.norm(np.diff(xy[path],axis=0),axis=1)<=300+1e-12))
        rates=(~cloud[path,np.arange(30)])*K[path];D=float(np.linalg.norm(np.diff(xy[path],axis=0),axis=1).sum());mu=float(rates.mean());pos=int(np.count_nonzero(rates>0));lam=float(r['lambda_bits_per_use'])
        expected=[mu,mu-lam*D/1000,D,pos/30,100*(1-pos/30),np.count_nonzero(np.diff(path)),cloud[path,np.arange(30)].sum(),pos]
        check('saved path arithmetic '+str((f,cid,li,rid,method)),same(expected,[float(r[k]) for k in METRICS]))
        if method=='Stationary':check('stationary path '+str((f,cid,li,rid)),np.all(path==path[0]) and D==0)
        slots+=len(path)
    check('261000 selected-slot values reconstructed',slots==261000)

    with np.load(A/'existing_data/bootstrap_counts.npz',allow_pickle=False) as z:counts=z['counts']
    check('existing bootstrap counts',counts.shape==(20000,100) and np.all(counts.sum(axis=1)==100))
    w=counts.astype(float)/100
    statistics={(int(r['figure']),r['case_id'],int(r['lambda_index']),r['method'],r['metric']):r for r in rows(OUT/'tables/statistical_comparison.csv')}
    pairs={(int(r['figure']),r['case_id'],int(r['lambda_index']),r['baseline'],r['metric']):r for r in rows(OUT/'tables/paired_improvements.csv')}
    oldpairs={(int(r['lambda_index']),r['baseline'],r['metric']):r for r in rows(BASE/'analysis/comparison_figures/paired_improvements.csv')}
    check('statistics and paired coverage',len(statistics)==696 and len(pairs)==232)
    for selection in cfg:
        f,cid,li=int(selection['figure']),selection['case_id'],int(selection['lambda_index'])
        v=np.array([[[float(lookup[f,cid,li,rid,m][k]) for k in METRICS] for m in METHODS] for rid in range(100)])
        bs=(w@v.reshape(100,-1)).reshape(20000,3,8)
        for si,method in enumerate(METHODS):
            for ki,metric in enumerate(METRICS):
                r=statistics[f,cid,li,method,metric];expected=[v[:,si,ki].mean(),v[:,si,ki].std(ddof=1),np.median(v[:,si,ki]),*np.percentile(bs[:,si,ki],[2.5,97.5])]
                check('mean SD median CI '+str((f,cid,li,method,metric)),same(expected,stat_values(r)) and int(r['valid_missions'])==100)
        for bi,baseline in enumerate(METHODS[:2]):
            for metric in ('K','U','D','availability'):
                ki=METRICS.index(metric);r=pairs[f,cid,li,baseline,metric];delta=v[:,2,ki]-v[:,bi,ki];bb=bs[:,2,ki]-bs[:,bi,ki]
                check('paired mean SD median '+str((f,cid,li,baseline,metric)),same([delta.mean(),delta.std(ddof=1),np.median(delta)],[float(r[k]) for k in ('mean','sd','median')]))
                if f==4 and (li,baseline,metric) in oldpairs:
                    saved=oldpairs[li,baseline,metric];expected=[float(saved['ci95_bootstrap_low']),float(saved['ci95_bootstrap_high'])];seed=20261019
                else:expected=np.percentile(bb,[2.5,97.5]);seed=20261020
                check('paired CI identity '+str((f,cid,li,baseline,metric)),same(expected,[float(r['ci95_low']),float(r['ci95_high'])]) and int(r['bootstrap_seed'])==seed)
                tol=1e-9 if metric=='D' else 1e-12
                check('paired signs '+str((f,cid,li,baseline,metric)),[int(r[k]) for k in ('strict_positive','ties','negative')]==[np.sum(delta>tol),np.sum(abs(delta)<=tol),np.sum(delta<-tol)])
                if r['ratio_of_means_percent']:
                    den=v[:,bi,ki].mean();check('ratio positive denominator '+str((f,cid,li,baseline,metric)),den>1e-12 and same(100*delta.mean()/den,float(r['ratio_of_means_percent'])))
                if r['ratio_ci95_low']:
                    check('ratio CI '+str((f,cid,li,baseline,metric)),same(np.percentile(100*bb/bs[:,bi,ki],[2.5,97.5]),[float(r['ratio_ci95_low']),float(r['ratio_ci95_high'])]))

    for label in ('temporal','spatial'):
        data=rows(OUT/'tables'/f'{label}_evidence_missions.csv');check('500 evidence rows '+label,len(data)==500)
        for r in data:
            cid=r['case_id'];rid=int(r['realization_id']);ci=bcase[cid];cloud=bcloud[ci,rid];fixed=bpaths[ci,rid,1,0,0];path=bpaths[ci,rid,1,2]
            clear=~cloud[fixed];edges=np.diff(np.r_[False,clear,False].astype(int));runs=np.flatnonzero(edges==-1)-np.flatnonzero(edges==1)
            expected=dict(global_blockage_fraction=cloud.mean(),stationary_clear_fraction=clear.mean(),all_horizon_clear_positions=np.all(~cloud,axis=1).sum(),
                global_temporal_switch_fraction=np.not_equal(cloud[:,1:],cloud[:,:-1]).mean(),stationary_longest_clear_run_slots=runs.max() if len(runs) else 0,
                stationary_cell_switches=np.count_nonzero(np.diff(cloud[fixed])),DP_repositionings=np.count_nonzero(np.diff(path)),DP_moving_mission=int(np.any(np.diff(path))),
                DP_distance=float(source_tables[B][cid,rid,1,'DP']['D']),DP_minus_P2_U=float(source_tables[B][cid,rid,1,'DP']['U'])-float(source_tables[B][cid,rid,1,'Stationary']['U']),
                unavoidable_all_sites_blocked_fraction=np.all(cloud,axis=0).mean(),stationary_availability=clear.mean(),DP_availability=float(source_tables[B][cid,rid,1,'DP']['availability']))
            check('evidence from stored states '+str((label,cid,rid)),all(same(value,float(r[k])) for k,value in expected.items()))
            check('availability upper bound '+str((label,cid,rid)),float(r['DP_availability'])<=1-float(r['unavoidable_all_sites_blocked_fraction'])+1e-12)
        for r in rows(OUT/'tables'/f'{label}_evidence_summary.csv'):
            values=np.array([float(s[r['metric']]) for s in data if float(s['parameter_value'])==float(r['parameter_value'])])
            check('evidence summary '+str((label,r['parameter_value'],r['metric'])),same(describe(values,w),stat_values(r)) and len(values)==100)
    for r in rows(OUT/'tables/cloud_probability_discussion.csv'):
        p=float(r['probability']);selection=next(s for s in cfg if int(s['figure'])==2 and float(s['value'])==p);cid=selection['case_id']
        d=np.array([float(lookup[2,cid,1,rid,'Greedy']['U'])-float(lookup[2,cid,1,rid,'Stationary']['U']) for rid in range(100)])
        check('Greedy minus P2 cloud contrast '+str(p),same(describe(d,w),[float(r['Greedy_minus_P2_U_'+k]) for k in ('mean','sd','median','ci95_low','ci95_high')]))
    findings=js(OUT/'verified_findings.json')
    check('P1 source-map range',same([findings['P1']['K_min'],findings['P1']['K_max']],[K.min(),K.max()]))
    for method,target in (('Stationary',(4.16,3.07)),('Greedy',(2.70,4.42))):
        for metric,reference in zip(('K','U'),target):
            ratio=100*(findings['default']['DP'][metric]-findings['default'][method][metric])/findings['default'][method][metric]
            check('verified reference '+method+'/'+metric,same(ratio,findings['default_gain_percent'][method][metric]) and round(ratio,2)==reference)

    plotted=rows(OUT/'figures/plotted_points.csv');render=js(OUT/'figures/render_metadata.json')
    check('117 actual points',len(plotted)==render['point_count']==117)
    style={'Stationary':('tab:blue','-','o'),'Greedy':('tab:orange','--','D'),'DP':('tab:red','-','^')}
    for i,r in enumerate(plotted):
        f,cid,li,method,metric=int(r['figure']),r['case_id'],int(r['lambda_index']),r['method'],r['metric'];s=statistics[f,cid,li,method,metric]
        expected=[float(s[k]) for k in ('mean','ci95_low','ci95_high')]
        check('actual artist source '+str(i),np.array_equal(expected,[float(r[k]) for k in ('y','ci95_low','ci95_high')]))
        check('required grayscale-distinct style '+str(i),tuple(r[k] for k in ('color','linestyle','marker'))==style[method])
        selection=next(s for s in cfg if int(s['figure'])==f and s['case_id']==cid and int(s['lambda_index'])==li)
        check('point parameter identity '+str(i),float(r['parameter_value'])==float(selection['value']) and float(r['lambda_bits_per_use'])==float(selection['lambda_bits_per_use']))
        if f==4:
            s=statistics[f,cid,li,method,'D'];check('tradeoff x mean and CI '+str(i),np.array_equal([float(s[k]) for k in ('mean','ci95_low','ci95_high')],[float(r[k]) for k in ('x','x_ci95_low','x_ci95_high')]))
        else:check('actual parameter x '+str(i),float(r['x'])==float(selection['value']))
        meta=render['figures'][protocol['selected_figures'][f-1]]['panels'][int(r['panel'])-1]
        check('visible mean CI and zero '+str(i),meta['ylim'][0]<=min(0,*expected) and meta['ylim'][1]>=max(0,*expected))
    for method in ('Greedy','DP'):
        sequence=[r for r in plotted if int(r['figure'])==4 and r['method']==method]
        check('true penalty order '+method,[int(r['lambda_index']) for r in sequence]==list(range(10)))
    inventory=rows(OUT/'figure_inventory.csv');check('23 original figure reviews',len(inventory)==23)
    for r in inventory:check('inventory hash '+r['original_pdf'],sha(ROOT/r['original_pdf'])==r['pdf_sha256'] and sha((ROOT/r['original_pdf']).with_suffix('.png'))==r['png_sha256'])
    visual=js(OUT/'validation/visual_review.json');check('four final images reviewed',len(visual['images'])==4 and visual['status']=='CURRENTLY_VERIFIED_PASS')
    for r in rows(OUT/'figure_source_mapping.csv'):
        for ext in ('pdf','png'):check('final figure hash '+r[ext],sha(OUT/r[ext])==r[ext+'_sha256'])
        check('vector PDF '+r['pdf'],b'/Subtype /Image' not in (OUT/r['pdf']).read_bytes())
        with Image.open(OUT/r['png']) as im:check('350dpi common canvas '+r['png'],im.size==(2520,1190) and all(abs(v-350)<.1 for v in im.info['dpi']))
        check('reviewed image hash '+r['png'],sha(OUT/r['png'])==visual['images'][r['png']])
    for name in ('report_vi.md','numerical_results_discussion_en.md','figure_captions_en.md'):
        text=(OUT/name).read_text(encoding='utf-8');check('status warnings '+name,'UNVALIDATED_SECURITY_MODEL' in text and 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS' in text)
        check('document links '+name,all(link.startswith('https://') or (OUT/link).exists() or link in ('validation_report.md','validation/final_receipt.json') for link in re.findall(r'\]\(([^)]+)\)',text)))
    english=(OUT/'numerical_results_discussion_en.md').read_text(encoding='utf-8')
    check('English sectionIII andA-F',all(title in english for title in ('# III. Numerical Results and Discussion','## A.','## B.','## C.','## D.','## E.','## F.')))
    for p in sorted(OUT.rglob('*')):
        if p.suffix in ('.py','.md','.csv','.json') and p.name not in ('final_receipt.json','checks.json','validation_report.md'):
            check('whitespace '+p.relative_to(OUT).as_posix(),all(line==line.rstrip() for line in p.read_text(encoding='utf-8-sig').splitlines()))
    body=dict(status='CURRENTLY_VERIFIED_PASS',named_checks=len(CHECKS),checks=CHECKS,protected_files=len(startup['protected_files']),original_receipts=6,
              unique_original_records=22200,unique_DP_objective_comparisons=dominance,selected_mission_records=8700,selected_slot_values=slots,
              statistics_rows=696,paired_rows=232,actual_plotted_points=117,temporal_evidence_missions=500,spatial_evidence_missions=500,
              optimizer_calls=0,quantum_evaluator_calls=0,cloud_generator_calls=0,new_RNG_draws=0,new_parameter_points=0,
              scientific_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
    report=f'''# Final saved-data consolidation validation

CURRENTLY_VERIFIED_PASS: {len(CHECKS)} independent named arithmetic/provenance checks. No historical optimizer/cloud tests or Bellman calculations rerun or counted.

- All{len(startup['protected_files'])} prior files preserved except five authorized ledgers;Git identity unchanged. Six historical receipt packages and all referenced artifacts/producers/external inputs authenticated directly. Older recursive verifiers predate this new namespace and were not invoked.
- All22,200 unique original mission-method records agree across overlapping sources;14,800 unique matched-mission DP objective comparisons pass at1e-12. This is saved-output verification,not a rerun of P2/Greedy/DP.
- All8,700 selected records and261,000 selected-slot rewards reconstructed from saved global-index paths,masks and current P1 rates. Feasibility,stationarity,objective,distance,availability and subset membership pass.
- All696 mean/sample-SD/median/CI/N rows and232 paired summaries verified. Existing20,000 count vectors reused;no RNG draws. Existing tradeoff pairedK/U confidence intervals retain seed20261019;other intervals use saved counts seed20261020. Undefined/missing ratio intervals remain empty. Intervals are pointwise,not security bounds.
- Persistence/spatial evidence checked independently for1,000 saved missions,including stationary cloud-free fraction,always-clear candidate count,temporal switching,censored clear runs,DP movement frequency/distance and unavoidable full-grid blockage. No cloud generation or optimizer calls.
- Four vectorPDF/350dpiPNG figures have consistent7.2-inch width and required circle/diamond/triangle styles;117 actual artist points and CIs agree with CSV. True ten-penalty order and genuine zero values preserved;four actual images reviewed/hash-bound.23 historical figures inventoried without overwriting or redundant new supplementary rendering.
- English sectionIII A-F,VI numerical discussion,source/figure mappings and links checked;reference gains reproduced,not imposed. External manuscript placeholders unchanged.

UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Frozen hash discrepancy,Objective C USER_STOPPED,finite-catalog/grid,synthetic weather/geometry,offline future-state information and mixed2DMI/homodyne-Holevo limits remain. No scientific/security/frozen/cache/baseline/threshold/lifecycle change,training/test/final-test/held-out,external manuscript edit,commit/push.

Recheck using project Python: `python -X utf8 -B results/mobility_parameter_sensitivity_final_20261020/validation/verify_final_package.py`. Do not rerun historical experiment scripts. Completed receipts refuse replacement.
'''
    target=OUT/'validation/final_receipt.json'
    if target.exists():
        if js(OUT/'validation/checks.json')!=body or (OUT/'validation_report.md').read_text(encoding='utf-8')!=report:raise AssertionError('Completed checks/report changed')
    else:
        (OUT/'validation/checks.json').write_text(json.dumps(body,indent=2)+'\n',encoding='utf-8',newline='\n');(OUT/'validation_report.md').write_text(report,encoding='utf-8',newline='\n')
    result=dict(body,artifact_sha256={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='final_receipt.json' and p.suffix!='.log'})
    if target.exists():
        if js(target)!=result:raise AssertionError('Completed artifacts or receipt changed')
    else:target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('CURRENTLY_VERIFIED_PASS',len(CHECKS),'checks;',len(result['artifact_sha256']),'artifact hashes;zero scientific/optimizer/cloud calls',flush=True)


if __name__=='__main__':verify()
