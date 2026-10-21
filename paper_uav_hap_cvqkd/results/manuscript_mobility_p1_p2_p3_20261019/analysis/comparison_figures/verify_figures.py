"""Independently verify saved-data figures; never invoke scientific/optimization code."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import math
import re
import subprocess

import numpy as np
from PIL import Image
from scipy.stats import t

OUT=Path(__file__).resolve().parent
ANALYSIS=OUT.parent
SIM=ANALYSIS.parent
ROOT=SIM.parents[1]
METHODS=('Stationary','Greedy','DP')
LABELS={'Stationary':'Stationary (P2)','Greedy':'Greedy','DP':'Dynamic Programming (P3)'}
NAMES=('fig1_average_skr_vs_lambda','fig2_objective_vs_lambda','fig3_travel_distance_vs_lambda',
       'fig4_dp_objective_gain_vs_lambda','fig5_skr_vs_travel_distance','fig6_per_slot_skr_comparison',
       'fig7_cumulative_skr_vs_time','fig8_uniform_vs_mb_positions')
CHECKS=[]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def js(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def csvrows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
def check(name,condition):
    if not bool(np.all(condition)):raise AssertionError(name)
    CHECKS.append(name)
def close(name,a,b):check(name,np.allclose(a,b,atol=1e-12,rtol=1e-12))


def verify():
    startup=js(OUT/'startup_manifest.json')
    for name,digest in startup['protected_files'].items():
        if name not in startup['allowed_changed']:
            if not (ROOT/name).is_file() or sha(ROOT/name)!=digest:raise AssertionError('Protected file changed: '+name)
    check('all protected files except five authorized ledgers retain startup bytes',True)
    for command,key in ((['git','branch','--show-current'],'branch'),(['git','rev-parse','HEAD'],'commit')):
        check('Git '+key+' unchanged',subprocess.check_output(command,cwd=ROOT,text=True).strip()==startup[key])
    listed=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','--','.'],cwd=ROOT,text=True).splitlines()
    new=set(listed)-set(startup['protected_files'])
    prefix=OUT.relative_to(ROOT).as_posix()+'/'
    check('new project files occur only in comparison_figures',all(name.startswith(prefix) for name in new))
    prior_count=0
    for receipt,base,field in ((SIM/'validation/final_verification.json',SIM,'artifacts_sha256'),
            (ANALYSIS/'analysis_receipt.json',ANALYSIS,'artifact_sha256')):
        record=js(receipt);check('prior receipt status '+receipt.name,record['status']=='CURRENTLY_VERIFIED_PASS')
        for name,digest in record[field].items():
            check('prior artifact hash '+str((base/name).relative_to(ROOT)),sha(base/name)==digest);prior_count+=1
    schedule=js(SIM/'mobility/lambda_schedule.json');protocol=js(SIM/'protocol.json')
    with np.load(SIM/'mobility/paths.npz',allow_pickle=False) as a:paths=a['paths'];lam=a['lambda_values']
    with np.load(SIM/'clouds/states.npz',allow_pickle=False) as a:S=a['usable_skr'];C=a['blocked']
    check('complete path and cloud shapes',paths.shape==(100,10,3,30) and S.shape==C.shape==(100,100,30))
    check('lambda exact values sorted with zero',np.array_equal(lam,schedule['values']) and lam[0]==0 and np.all(np.diff(lam)>0))
    xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in csvrows(SIM/'positions.csv')])
    Kstar=np.array([float(r['K_star']) for r in csvrows(SIM/'p1/winners.csv')])
    check('boolean blocked interpretation and exact S',C.dtype==np.bool_ and np.array_equal(S,(~C)*Kstar[None,:,None]))
    metrics=csvrows(SIM/'mobility/mission_metrics.csv')
    keys=[(int(r['realization_id']),int(r['lambda_index']),r['strategy']) for r in metrics]
    check('all 3000 distinct paired method mission lambda records',len(keys)==len(set(keys))==3000 and set(keys)=={(r,l,m) for r in range(100) for l in range(10) for m in METHODS})
    rates=S[np.arange(100)[:,None,None,None],paths,np.arange(30)]
    distances=np.linalg.norm(np.diff(xy[paths],axis=3),axis=-1)
    check('all saved legs feasible under 300m bound',np.all(distances<=300+1e-12))
    values={'K':rates.mean(axis=-1),'D':distances.sum(axis=-1),'availability':(rates>0).mean(axis=-1)}
    values['U']=values['K']-lam[None,:,None]*values['D']/protocol['optimization']['reference_distance_m']
    fields={'K':'average_skr_bits_per_use','D':'total_distance_m','U':'objective_bits_per_use','availability':'availability'}
    for k,field in fields.items():
        saved=np.empty((100,10,3))
        for row in metrics:saved[int(row['realization_id']),int(row['lambda_index']),METHODS.index(row['strategy'])]=float(row[field])
        close('3000 original and independently reconstructed '+k,values[k],saved)
    close('all 3000 exact lambda entries',[float(r['lambda_bits_per_use']) for r in metrics],[lam[int(r['lambda_index'])] for r in metrics])
    check('2000 mission-wise DP objective dominance comparisons',values['U'][:,:,2,None]>=values['U'][:,:,:2]-1e-12)
    check('P2 zero distance and lambda-invariant SKR',np.all(values['D'][:,:,0]==0) and np.all(values['K'][:,:,0]==values['K'][:,[0],0]))
    check('DP distance non-increasing for each mission',np.diff(values['D'][:,:,2],axis=1)<=1e-9)
    time=csvrows(SIM/'mobility/time_series.csv');check('90000 original selected-slot rows',len(time)==90000)
    slotkeys=[(int(r['realization_id']),int(r['lambda_index']),METHODS.index(r['strategy']),int(r['slot'])-1) for r in time]
    check('90000 unique selected-slot keys',len(set(slotkeys))==90000)
    close('90000 saved per-slot SKR values',[float(r['usable_skr']) for r in time],[rates[key] for key in slotkeys])
    check('90000 saved selected positions',[int(r['position_index']) for r in time]==[int(paths[key]) for key in slotkeys])
    summaries=csvrows(OUT/'figure_data_summary.csv');summary={(int(r['lambda_index']),r['strategy']):r for r in summaries}
    check('30 summary records with complete coverage',len(summaries)==len(summary)==30 and set(summary)=={(l,m) for l in range(10) for m in METHODS})
    for (li,method),row in summary.items():
        check('100 paired missions '+str((li,method)),int(row['missions'])==100 and float(row['lambda_bits_per_use'])==lam[li])
        for key,arr in values.items():
            x=arr[:,li,METHODS.index(method)];mean=x.mean();sd=x.std(ddof=1);half=t.ppf(.975,99)*sd/10
            close('summary mean sd median tCI '+str((li,method,key)),[float(row[key+'_'+s]) for s in ('mean','sd','median','ci95_t_low','ci95_t_high')],[mean,sd,np.median(x),mean-half,mean+half])
    pairs=csvrows(OUT/'paired_improvements.csv');paired={(int(r['lambda_index']),r['baseline'],r['metric']):r for r in pairs}
    oldpaired={(int(r['lambda_index']),r['baseline'],r['metric']):r for r in csvrows(ANALYSIS/'tables/paired_comparisons.csv')}
    check('40 paired comparisons with complete coverage',len(pairs)==len(paired)==40 and set(paired)==set(oldpaired))
    for (li,base,key),row in paired.items():
        delta=values[key][:,li,2]-values[key][:,li,METHODS.index(base)];den=values[key][:,li,METHODS.index(base)].mean()
        check('positive paired ratio denominator '+str((li,base,key)),den>0)
        close('paired mean sd median percentage '+str((li,base,key)),[float(row[s]) for s in ('mean','sd','median','ratio_of_means_percent')],[delta.mean(),delta.std(ddof=1),np.median(delta),100*delta.mean()/den])
        check('paired strict tie inferior counts '+str((li,base,key)),[int(row[s]) for s in ('strict_improvement_missions','equal_missions','inferior_missions')]==[int(np.sum(delta>1e-12)),int(np.sum(abs(delta)<=1e-12)),int(np.sum(delta<-1e-12))])
        check('unchanged saved paired bootstrap CI '+str((li,base,key)),all(float(row[s])==float(oldpaired[li,base,key][s]) for s in ('ci95_bootstrap_low','ci95_bootstrap_high')) and int(row['bootstrap_resamples'])==20000 and int(row['bootstrap_seed'])==20261019)
    findings=js(OUT/'findings.json');meta=js(OUT/'render_metadata.json')
    li=int(np.flatnonzero(lam==schedule['representative'])[0]);rid=findings['mission_id']
    gains=values['U'][:,li,2]-values['U'][:,li,0];eligible=np.flatnonzero((gains>1e-12)&(values['U'][:,li,2]-values['U'][:,li,1]>1e-12))
    check('representative mission matches disclosed post-hoc rule',rid==min(eligible,key=lambda r:(-gains[r],r)) and meta['representative_mission_id']==rid and meta['representative_lambda']==lam[li])
    check('rounded requested lambda disclosed rather than invented',findings['requested_rounded_value_exists_exactly'] is False and findings['requested_rounded_lambda']==9.46803e-6 and findings['representative_lambda_exact']==lam[li])
    close('rounding difference',findings['rounding_difference'],9.46803e-6-lam[li])
    for base in ('Stationary','Greedy'):
        for key in ('K','U'):close('reported exact percentage '+base+key,findings['percentages'][base][key],float(paired[li,base,key]['ratio_of_means_percent']))
        check('reported strict win counts '+base,findings['strict_U_wins'][base]==int(paired[li,base,'U']['strict_improvement_missions']))
    representative=csvrows(OUT/'representative_slot_data.csv');cumulative=csvrows(OUT/'cumulative_skr_data.csv')
    check('90 representative slots and 93 cumulative points',len(representative)==90 and len(cumulative)==93)
    for si,method in enumerate(METHODS):
        rows=[r for r in representative if r['strategy']==method];cum=[r for r in cumulative if r['strategy']==method]
        check('selected mission slot indices '+method,[int(r['slot']) for r in rows]==list(range(1,31)) and all(int(r['realization_id'])==rid and float(r['lambda_bits_per_use'])==lam[li] for r in rows))
        close('representative slot rates '+method,[float(r['usable_skr']) for r in rows],rates[rid,li,si])
        check('representative blockage '+method,[r['blocked']=='True' for r in rows]==C[rid,paths[rid,li,si],np.arange(30)].tolist())
        close('exact cumulative sum including empty prefix '+method,[float(r['cumulative_skr_sum']) for r in cum],np.r_[0,np.cumsum(rates[rid,li,si])])
        check('cumulative monotonic '+method,np.diff([float(r['cumulative_skr_sum']) for r in cum])>=0)
    p1=csvrows(OUT/'p1_position_data.csv');family={(int(r['position_index']),r['family']):r for r in csvrows(SIM/'p1/family_winners.csv')}
    check('P1 full indices and negative Uniform retained',[int(r['j']) for r in p1]==list(range(1,101)) and all(float(r['Uniform_K_raw'])<0 for r in p1))
    for fam in ('Uniform','MB'):
        close('raw P1 source '+fam,[float(r[fam+'_K_raw']) for r in p1],[float(family[j,fam]['K_raw']) for j in range(100)])
    traces=csvrows(OUT/'plotted_points.csv');check('all 514 plotted primary curve points',len(traces)==514)
    expected={}
    for num,key in ((1,'K'),(2,'U'),(3,'D')):
        for si,method in enumerate(METHODS):expected[num,LABELS[method]]=(lam,values[key][:,:,si].mean(axis=0))
    for base in ('Stationary','Greedy'):
        expected[4,'DP minus '+base]=(lam,(values['U'][:,:,2]-values['U'][:,:,METHODS.index(base)]).mean(axis=0))
    for si,method in enumerate(METHODS):
        expected[5,LABELS[method]]=([0],[values['K'][:,0,si].mean()]) if si==0 else (values['D'][:,:,si].mean(axis=0),values['K'][:,:,si].mean(axis=0))
        expected[6,LABELS[method]]=(np.arange(1,31),rates[rid,li,si])
        expected[7,LABELS[method]]=(np.arange(31),np.r_[0,np.cumsum(rates[rid,li,si])])
    expected[8,'Optimized Uniform 256-QAM']=(np.arange(1,101),[float(family[j,'Uniform']['K_raw']) for j in range(100)])
    expected[8,'Optimized MB-shaped 256-QAM']=(np.arange(1,101),[float(family[j,'MB']['K_raw']) for j in range(100)])
    check('primary curve set exact',set((int(r['figure']),r['curve']) for r in traces)==set(expected))
    for (num,label),(x,y) in expected.items():
        rows=[r for r in traces if int(r['figure'])==num and r['curve']==label]
        check('plotted point order '+str((num,label)),[int(r['point_index']) for r in rows]==list(range(len(x))))
        close('plotted x '+str((num,label)),[float(r['x']) for r in rows],x)
        close('plotted y '+str((num,label)),[float(r['y']) for r in rows],y)
    styles={'Stationary':('tab:blue','-','o'),'Greedy':('tab:orange','--','s'),'DP':('tab:red','-','^')}
    for num in (1,2,3,5,6,7):
        for method,(color,line,marker) in styles.items():
            style=meta['styles'][NAMES[num-1]+':'+LABELS[method]]
            check('actual line color marker '+str((num,method)),(style['color'],style['linestyle'],style['marker'])==(color,line,marker) and 2<=style['linewidth']<=2.5 and 5<=style['markersize']<=7)
    check('symlog zero and exact linear threshold',meta['zero_lambda_retained'] is True and meta['symlog_linear_threshold']==lam[1])
    check('producer source identity',meta['producer_sha256']==sha(OUT/'render_comparisons.py'))
    imports=[]
    for node in ast.walk(ast.parse((OUT/'render_comparisons.py').read_text(encoding='utf-8'))):
        if isinstance(node,ast.Import):imports += [alias.name for alias in node.names]
        elif isinstance(node,ast.ImportFrom):imports.append(node.module)
    check('producer has no project evaluator optimizer or cloud imports',not any(name.startswith(('src','scripts')) for name in imports))
    visual=js(OUT/'visual_review.json');check('eight actual images visually reviewed',visual['status']=='CURRENTLY_VERIFIED_PASS' and len(visual['figures'])==8)
    for name in NAMES:
        with Image.open(OUT/(name+'.png')) as im:
            check('PNG 350dpi white background '+name,min(im.info['dpi'])>=349 and im.size==(2520,1277) and im.getpixel((0,0))[:3]==(255,255,255))
        pdf=(OUT/(name+'.pdf')).read_bytes();check('vector PDF '+name,pdf.startswith(b'%PDF') and b'/Subtype /Image' not in pdf)
        check('reviewed PNG matches actual file '+name,visual['figures'][name]['png_sha256']==sha(OUT/(name+'.png')))
    mapping=csvrows(OUT/'figure_source_mapping.csv');check('eight source-map rows',len(mapping)==8)
    for row in mapping:
        num=int(row['figure']);check('source-map file targets '+str(num),row['pdf']==NAMES[num-1]+'.pdf' and row['png']==NAMES[num-1]+'.png' and bool(row['original_source']))
    for name in ('comparison_report_vi.md','figure_interpretation_vi.md','figure_captions_en.md'):
        text=(OUT/name).read_text(encoding='utf-8')
        check('scientific scope warnings '+name,'UNVALIDATED_SECURITY_MODEL' in text and 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS' in text)
        check('all local document links exist '+name,all((OUT/link).exists() or link in ('figure_validation.md','validation_receipt.json') for link in re.findall(r'\]\(([^)]+)\)',text)))
    source={row['path']:row for row in js(OUT/'data_inventory.json')}
    for path,row in source.items():
        check('inventory input identity '+path,sha(ROOT/path)==row['sha256'])
        if 'rows' in row:
            actual=csvrows(ROOT/path);check('actual CSV schema and rows '+path,len(actual)==row['rows'] and list(actual[0])==row['columns'])
        else:
            with np.load(ROOT/path,allow_pickle=False) as a:
                check('actual NPZ schema '+path,set(a.files)==set(row['members']) and all(list(a[key].shape)==row['members'][key]['shape'] and str(a[key].dtype)==row['members'][key]['dtype'] for key in a.files))
    for path in OUT.rglob('*'):
        if path.is_file() and path.suffix in ('.py','.md','.json','.csv') and path.name not in ('figure_validation.md','validation_receipt.json'):
            check('no trailing whitespace '+path.name,all(line==line.rstrip() for line in path.read_text(encoding='utf-8-sig').splitlines()))
    report=f'''# Figure validation

CURRENTLY_VERIFIED_PASS — {len(CHECKS)} independent, named assertions.

- Complete saved input: 100 paired missions, ten exact λ values, three methods; 3,000 metric records and 90,000 selected-slot records. No omission, imputation or new optimization.
- All K, D, U and availability reconstructed directly from saved paths and S; U=mean(S)−λD/1000. Every leg ≤300m. DP objective dominates both baselines in all 2,000 comparisons within 1e−12; DP distance is non-increasing at the tested λ for each mission. P2 distance is zero and its SKR is λ-invariant.
- Means, sample SDs, medians and Student-t95% mean intervals independently checked. Forty paired comparisons use the same 100 mission IDs; bootstrap intervals are reused byte-equivalent numbers from the authenticated existing 20,000 whole-mission bootstrap analysis. Pointwise intervals are not simultaneous or security bounds.
- All 514 Matplotlib primary-curve points match independently reconstructed saved-data values; Fig.5 order is increasing λ. Actual line styles follow the requested blue-circle, orange-square and red-triangle assignments. λ=0 is retained; symlog threshold is {lam[1]!r} bits/use.
- Fig.6/7 use disclosed post-hoc mission {rid}, exact stored λ={lam[li]!r}. Requested rounded 9.46803e−6 is absent exactly; no new λ was created. Slot blockage is authenticated, cumulative values are exact prefix sums and are not physical secret-bit counts.
- Fig.8 retains all 100 negative Uniform raw rates and both families' exact raw values. No percentage gain relative to negative/zero Uniform.
- Eight vector PDFs (no embedded raster images), eight white-background 350dpi PNGs, eight source-map rows and linked English/Vietnamese documents checked. Final PNGs were visually inspected for clipping, readable labels, legends and preserved negative/zero values; image hashes are in visual_review.json.
- All {prior_count} hash-bound members of the two prior receipts match. All {len(startup['protected_files'])} pre-existing project files are protected; only the five authorized ledger paths may change. New files are restricted to this figure directory. Git branch and HEAD match startup.
- Original 24 tests/346 checks and prior 883 analysis checks remain historical evidence; they were not rerun or counted as this verification.

UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Frozen-specification hash discrepancy and Objective C USER_STOPPED remain. No physical SKR/source/cloud/P1/P2/P3/Greedy rerun; no final-test/held-out access, lifecycle promotion, external manuscript edit, commit or push. P2/DP are offline benchmarks; the synthetic finite-grid MI2D/homodyne-Holevo model is not a validated quantum-security rate.

Run `python -X utf8 -B verify_figures.py` using the project environment. A completed receipt is checked, not silently replaced.
'''
    target=OUT/'figure_validation.md'
    if (OUT/'validation_receipt.json').exists():
        if target.read_text(encoding='utf-8')!=report:raise AssertionError('Validation prose changed')
    else:target.write_text(report,encoding='utf-8')
    result=dict(status='CURRENTLY_VERIFIED_PASS',named_assertions=len(CHECKS),checks=CHECKS,
        protected_files=len(startup['protected_files']),allowed_changed_files=startup['allowed_changed'],prior_artifact_hashes=prior_count,
        original_metric_records=3000,original_selected_slot_records=90000,plotted_points=514,figure_pairs=8,
        new_physical_SKR=0,new_source_moments=0,new_cloud_missions=0,new_optimizer_calls=0,
        security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
        artifact_sha256={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='validation_receipt.json' and p.suffix!='.log'})
    receipt=OUT/'validation_receipt.json'
    if receipt.exists():
        old=js(receipt)
        if old!=result:raise AssertionError('Completed receipt or figure artifacts changed')
    else:receipt.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print('CURRENTLY_VERIFIED_PASS',len(CHECKS),'named assertions;',len(result['artifact_sha256']),'figure-package hashes;',prior_count,'prior-artifact hashes; no scientific rerun.',flush=True)


if __name__=='__main__':verify()
