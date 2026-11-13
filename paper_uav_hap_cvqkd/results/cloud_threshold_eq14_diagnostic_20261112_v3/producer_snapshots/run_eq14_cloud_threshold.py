"""User-authorized Eq14 cloud-loss diagnostic; immutable original kernels/caches."""
from pathlib import Path
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.eq14_cloud_diagnostic import Eq14Diagnostic,BatchedEq14,catalog_maximum,EXECUTED
from src.cloud_threshold_search import search_raw_threshold


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        fields=list(dict.fromkeys(k for row in rows for k in row))
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def initialize(out):
    global MODEL,BATCH,OUT
    OUT=Path(out);MODEL=Eq14Diagnostic();BATCH=BatchedEq14(MODEL.sources)


def geometry_job(job):
    started=time.perf_counter();name,angle,distance=job
    target=OUT/(name+'_summary.json')
    if target.exists():return json.loads(target.read_text())
    context=MODEL.context(angle);clear=catalog_maximum(MODEL,BATCH,context,0.)
    fixed=next(s for s in MODEL.sources if s['ensemble_hash']==clear['ensemble_hash'])
    cache={};records=[]
    def evaluate(A,mode):
        key=(float(A),mode)
        if key not in cache:
            row=(MODEL.evaluate(fixed,context,A) if mode=='fixed_clear_optimum' else catalog_maximum(MODEL,BATCH,context,A))
            cache[key]=dict(row,mode=mode,geometry=name,zenith_deg=angle,distance_km=distance)
        return cache[key]['K_raw']
    searches={}
    for mode in ['fixed_clear_optimum','catalog_reselected_212']:
        result=search_raw_threshold(lambda A:evaluate(A,mode),width_db=.001)
        crossings=result['positive_to_nonpositive_crossings']
        bracket=([crossings[0]['lower_db'],crossings[0]['upper_db']]
                 if result['clear_raw_skr']>0 and len(crossings)==1 else None)
        # Root interval is numerical only. Keep sampled nonmonotonicity explicit.
        searches[mode]={k:v for k,v in result.items() if k!='samples'}
        searches[mode]['diagnostic_crossing_interval_db']=bracket
        searches[mode]['diagnostic_crossing_midpoint_db']=sum(bracket)/2 if bracket else None
        searches[mode]['zero_additional_margin']=result['clear_raw_skr']<=0
        # Detect positive re-entry in evaluated samples independently of raw monotonicity.
        signs=[p['K_raw']>0 for p in result['samples']]
        searches[mode]['sampled_positive_reentry']=any(not a and b for a,b in zip(signs,signs[1:]))
    records=list(cache.values());write_csv(OUT/(name+'_evaluations.csv'),records)
    summary=dict(geometry=name,zenith_deg=angle,distance_km=distance,clear_selection=clear,
        searches=searches,seconds=time.perf_counter()-started,
        canonical_rate_evaluations=len(records),channel=context,
        classification='DIAGNOSTIC_ONLY_UNCERTIFIED_CW',
        optimization_scope='EXISTING_212_SOURCE_FINITE_CATALOG; NOT_CONTINUOUS_GLOBAL_OPTIMIZATION')
    save(target,summary)
    return summary


def guarded_job(job):
    try:return geometry_job(job)
    except Exception as error:
        import traceback
        result=dict(failed=True,geometry=job[0],error=str(error),traceback=traceback.format_exc())
        save(OUT/(job[0]+'_failure.json'),result)
        return result


def validate(out):
    model=Eq14Diagnostic();batch=BatchedEq14(model.sources)
    checkpoints=[]
    for angle in [0.,4.,math.degrees(math.acos(19/22))]:
        context=model.context(angle)
        for A in [0.,.5,100.]:
            bounds=batch.upper_bounds(context,A)
            rows=[model.evaluate(s,context,A) for s in model.sources]
            raw=np.array([r['K_raw'] for r in rows]);maximum=max(rows,key=lambda r:r['K_raw'])
            fast=catalog_maximum(model,batch,context,A)
            bound_violation=float(np.max(raw-bounds))
            delta=abs(maximum['K_raw']-fast['K_raw'])
            assert delta<=1e-10 and bound_violation<=1e-11
            # Compare all vectorized Holevo values with preserved 110-digit components.
            chi=batch.covariance(context,A)[2]
            chi_error=max(abs(chi[i]-r['chi_BE']) for i,r in enumerate(rows))
            missing_batch=BatchedEq14(model.missing,bounds_only=True)
            tt,nn,cc=missing_batch.covariance(context,A)
            missing_chi_error=max(abs(cc[i]-model.model['components'](s['VA'],tt,nn[i]/tt,s['C'],s['w'],digits=110)['chi_BE']) for i,s in enumerate(model.missing))
            assert missing_chi_error<1e-11
            assert chi_error<1e-11
            checkpoints.append(dict(angle=angle,A_db=A,all_archived_sources=len(rows),
                maximum_difference=delta,upper_bound_violation=bound_violation,
                max_float_Holevo_error=chi_error,missing_source_float_Holevo_error=missing_chi_error,candidates_evaluated=fast['candidates_evaluated'],
                missing_sources_excluded=fast['unavailable_sources_excluded_by_upper_bound']))
    # Exact reference replay at A=0; compare all sources available in archive.
    with (ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024/angle_00_candidates.csv').open() as f:
        stored={r['ensemble_hash']:r for r in csv.DictReader(f)}
    c=model.context(0.)
    replay=max(abs(model.evaluate(s,c,0.)['K_raw']-float(stored[s['ensemble_hash']]['K_raw'])) for s in model.sources)
    assert replay<2e-10
    result=dict(status='CURRENTLY_VERIFIED_PASS',scope='software/numerical diagnostic; source Cw not certified',
        checkpoints=checkpoints,saved_A0_replay_max_error=replay,archive_sources=len(model.sources),
        unarchived_sources=len(model.missing),executed_preserved_functions=EXECUTED,
        physical_security_certification=False)
    save(out/'adapter_validation.json',result)
    return result


def main(out,workers):
    if out.exists():raise FileExistsError('Use a fresh output directory')
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    out.mkdir(parents=True)
    prior=ROOT/'results/cloud_threshold_readiness_20261112'
    protected=json.loads((prior/'protected_inputs.json').read_text())
    protected.update(json.loads((prior/'input_hashes.json').read_text()))
    for folder in [prior,ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024']:
        for f in folder.rglob('*'):
            if f.is_file() and '__pycache__' not in f.parts:protected[f.relative_to(ROOT).as_posix()]=sha(f)
    for f in [ROOT/'results/skr_vs_zenith_angle_20261019/verified_ensembles.npz']:
        protected[f.relative_to(ROOT).as_posix()]=sha(f)
    for n in ['src/cloud_threshold_search.py','scripts/audit_cloud_threshold_readiness.py','tests/test_cloud_threshold_search.py']:
        protected[n]=sha(ROOT/n)
    save(out/'protected_inputs.json',protected)
    (out/'startup_git_diff.patch').write_bytes(subprocess.check_output(['git','diff'],cwd=ROOT))
    ledger=out/'startup_ledgers';ledger.mkdir()
    for name in ['docs/PROJECT_STATE.md','docs/EVIDENCE.md','docs/DECISION_LOG.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md']:
        (ledger/Path(name).name).write_bytes((ROOT/name).read_bytes())
    save(out/'design_receipt.json',dict(user_selected_branch='manuscript_eq14_direct',
        user_accepted_uncertified_Cw=True,security_valid=False,geometry=dict(HAP_xyz_m=[1000,1000,20000],UAV_altitude_m=1000,side_m=2000,cells_per_side=50),
        coarse_A_db=[0,100,.5],root_bracket_width_db=.001,workers=workers,
        finite_catalog_sources=212,continuous_global_optimization=False,
        source_generation=False,model_settings='unchanged historical Eq14 Dr.30m homodyne xi_det.005',
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),git_status=status,
        producer_hashes={n:sha(ROOT/n) for n in ['src/eq14_cloud_diagnostic.py','scripts/run_eq14_cloud_threshold.py']},
        import_blocker='Historical CLI import fails WinError4551 torch_python.dll; isolated existing numerical definitions used, no policy changes',
        preliminary_probes='Original CLI failed before SKR; isolated-route probes recorded in session, not claimed as main-run counts'))
    print('Validating canonical adapter and capacity screening...',flush=True)
    validate(out)
    print('Adapter validation PASS',flush=True)
    indices=np.arange(50)*2-49;radii=sorted(set((indices[:,None]**2+indices[None,:]**2).ravel().tolist()))
    jobs=[];geometry_by_r={}
    for i,r2 in enumerate(radii):
        r=20*math.sqrt(r2);angle=math.degrees(math.atan2(r,19000));name=f'grid_{i:03}'
        geometry_by_r[r2]=name;jobs.append((name,angle,math.hypot(19000,r)/1000))
    jobs+=[('vertical',0.,19.),('domain_corner',math.degrees(math.atan2(math.sqrt(2)*1000,19000)),math.sqrt(19**2+2))]
    for distance in [19.5,20.,21.,22.]:jobs.append((f'extended_{distance:g}km',math.degrees(math.acos(19/distance)),distance))
    save(out/'geometry_jobs.json',[dict(id=n,zenith_deg=a,distance_km=d) for n,a,d in jobs])
    started=time.perf_counter();completed=[]
    with ProcessPoolExecutor(max_workers=workers,initializer=initialize,initargs=(str(out),)) as pool:
        future={pool.submit(guarded_job,job):job[0] for job in jobs}
        for done in as_completed(future):
            result=done.result();completed.append(result)
            if result.get('failed'):
                print(result['traceback'],flush=True)
                for pending in future:pending.cancel()
                for process in pool._processes.values():process.terminate()
                raise RuntimeError('Geometry failed; failure artifact saved, all remaining work cancelled')
            print(f"{len(completed)}/{len(jobs)} {result['geometry']} elapsed={time.perf_counter()-started:.1f}s",flush=True)
    by_name={r['geometry']:r for r in completed};map_rows=[];threshold_rows=[]
    for r in sorted(completed,key=lambda r:r['zenith_deg']):
        for mode,s in r['searches'].items():
            br=s['diagnostic_crossing_interval_db']
            threshold_rows.append(dict(geometry=r['geometry'],zenith_deg=r['zenith_deg'],distance_km=r['distance_km'],
                mode=mode,clear_raw_skr=s['clear_raw_skr'],A_crit_db=s['diagnostic_crossing_midpoint_db'],
                lower_db=br[0] if br else None,upper_db=br[1] if br else None,
                zero_additional_margin=s['zero_additional_margin'],sampled_nonincreasing=s['sampled_nonincreasing'],
                sampled_positive_reentry=s['sampled_positive_reentry'],status=s['status'],security_valid=False))
    for iy in range(50):
        for ix in range(50):
            r2=int(indices[ix]**2+indices[iy]**2);r=by_name[geometry_by_r[r2]]
            for mode,s in r['searches'].items():
                map_rows.append(dict(ix=ix,iy=iy,x_m=20+40*ix,y_m=20+40*iy,geometry=r['geometry'],
                    zenith_deg=r['zenith_deg'],mode=mode,A_crit_db=s['diagnostic_crossing_midpoint_db'],
                    clear_raw_skr=s['clear_raw_skr'],zero_additional_margin=s['zero_additional_margin']))
    write_csv(out/'critical_thresholds.csv',threshold_rows);write_csv(out/'critical_threshold_map.csv',map_rows)
    for name,h in protected.items():assert sha(ROOT/name)==h,name
    save(out/'execution_summary.json',dict(status='CURRENTLY_VERIFIED_PASS',scope='DIAGNOSTIC_ONLY_UNCERTIFIED_CW',
        geometry_groups=len(jobs),grid_unique_radii=len(radii),grid_positions=2500,
        main_canonical_selected_evaluations=sum(r['canonical_rate_evaluations'] for r in completed),
        seconds=time.perf_counter()-started,protected_files=len(protected),
        continuous_reoptimization='NOT_RUN_MISSING_CONTINUOUS_SOURCE_COVERAGE_AND_BLOCKED_TORCH',
        finite_catalog_reselection='COMPLETE_212_SOURCES_WITH_UPPER_BOUND_SCREENING',
        full_task_global_reoptimization_complete=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--workers',type=int,default=6)
    args=parser.parse_args();main(args.output.resolve(),args.workers)
