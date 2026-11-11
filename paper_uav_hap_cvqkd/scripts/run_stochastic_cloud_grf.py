"""Reproducible cloud-only exponential-GRF ensemble; preserves prior experiments."""
from pathlib import Path
from dataclasses import asdict,replace
import argparse,csv,hashlib,json,subprocess,sys,time
import numpy as np
from scipy.stats import t,norm

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.stochastic_cloud_grf import (MODEL_NAME,GRFConfig,CirculantGRF,CloudGRFSimulator,
                                    relative_intensity,components,DiagnosticTracker)

METRICS=['mean','variance','second_moment','cloud_fraction','third_moment','fourth_moment',
         'component_count','mean_area_m2','max_area_m2','new_track_segments','ended_track_segments',
         'material_RMS_change','material_presence_IoU']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path,obj):path.write_bytes((json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8'))


def write_csv(path,rows,columns=None):
    with path.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns or list(rows[0]));writer.writeheader();writer.writerows(rows)


def uncertainty(values):
    values=np.asarray(values);mean=values.mean(0);se=values.std(0,ddof=1)/np.sqrt(len(values))
    return mean,se,t.ppf(.975,len(values)-1)*se


def frozen_stage(sim,out):
    e=sim.embedding;c=sim.c;initial=sim.field
    frozen=np.stack([e.sample(initial,offset_x=-c.vx_m_s*k*c.dt_s,offset_y=-c.vy_m_s*k*c.dt_s) for k in range(c.slots)])
    final=e.advect(initial,c.slots)
    from scipy.fft import rfft2,irfft2
    cov0=irfft2(abs(rfft2(initial))**2,s=e.shape)/initial.size
    cov1=irfft2(abs(rfft2(final))**2,s=e.shape)/initial.size
    marker=np.zeros(e.shape);marker[e.iy[len(e.iy)//2],0]=1
    probes={str(k):float(e.sample(e.advect(marker,k)).max()) for k in (0,min(400,c.slots-1),c.slots-1)}
    positive=np.zeros(e.shape);positive[e.iy[0],e.ix[0]]=1
    eight=e.sample(e.advect(initial,8))
    interior=float(np.max(abs(eight[:,:-1]-sim.initial[:,1:]))) if c.vx_m_s*c.dt_s*8==-c.dx_m and c.vy_m_s==0 else None
    numerical={'status':'CURRENTLY_VERIFIED_PASS','frozen_rho':1.,'frozen_innovation_scale':0.,
               'internal_step_xy':[e.step_x,e.step_y],'displacement_xy_m_per_slot':[e.step_x*e.dx,e.step_y*e.dy],
               'output_step_x_cells':e.step_x*e.dx/c.dx_m,'eight_slot_displacement_x_m':8*e.step_x*e.dx,
               'eight_slot_common_interior_max_error':interior,
               'full_variance_relative_change':float(final.var()/initial.var()-1),
               'full_covariance_max_abs_change':float(abs(cov1-cov0).max()),
               'sorted_frozen_values_bitwise_identical':bool(np.array_equal(np.sort(initial.ravel()),np.sort(final.ravel()))),
               'tagged_seam_marker_ROI_max':probes,'positive_control_ROI_peak':float(e.sample(positive).max()),
               'method':'Exact internal-grid permutation; frozen ROI queried by unwrapped source indices before evolving simulation.'}
    if not numerical['sorted_frozen_values_bitwise_identical'] or max(probes.values())!=0 or numerical['positive_control_ROI_peak']!=1:
        numerical['status']='FAILED'
    write_json(out/'frozen_validation.json',numerical)
    np.savez_compressed(out/'frozen_fields.npz',latent_field=frozen,relative_intensity=relative_intensity(frozen,sim.theta,c),
                        time_s=np.arange(c.slots)*c.dt_s,theta_c=sim.theta)
    print('Frozen-field stage completed before evolving ensemble: '+numerical['status'],flush=True)
    return frozen,numerical


def run(config_path,out):
    started=time.perf_counter();settings=json.loads(config_path.read_text(encoding='utf-8'))
    c=GRFConfig(**settings['simulation']);seeds=settings['ensemble_seeds'];snaps=settings['snapshot_slots'];lags=settings['temporal_lags']
    if len(seeds)<10 or len(set(seeds))!=len(seeds) or seeds[0]!=c.seed:raise ValueError('at least ten distinct seeds, main seed first')
    if any(type(k)is not int or not 0<=k<c.slots for k in snaps+lags):raise ValueError('snapshot/lag outside horizon')
    out.mkdir(parents=True,exist_ok=False)
    prior=subprocess.check_output(['git','ls-files','src','configs','scripts','tests','docs/FINAL_MODEL_SPEC.md','docs/SECURITY_SCOPE_FREEZE.md'],cwd=ROOT,text=True).splitlines()
    for folder in ('ibrahim_cloud_demo_20261111','ibrahim_stationary_cloud_20261111'):
        prior.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'results'/folder).rglob('*') if p.is_file())
    prior.extend(['src/ibrahim_stationary_cloud.py','configs/ibrahim_stationary_cloud.json',
                  'scripts/run_ibrahim_stationary_cloud.py','scripts/plot_ibrahim_stationary_cloud.py',
                  'tests/test_ibrahim_stationary_cloud.py','docs/IBRAHIM_STATIONARY_CLOUD_README.md','docs/IBRAHIM_CLOUD_README.md'])
    protected={p:sha(ROOT/p) for p in sorted(set(prior))}
    write_json(out/'protected_inputs.json',protected)
    (out/'preexisting_git_diff.patch').write_bytes(subprocess.check_output(['git','diff'],cwd=ROOT))
    (out/'previous_session_handoff.md').write_bytes((ROOT/'.agent/SESSION_HANDOFF.md').read_bytes())
    producers=['src/stochastic_cloud_grf.py','scripts/run_stochastic_cloud_grf.py','tests/test_stochastic_cloud_grf.py']
    write_json(out/'design_receipt.json',{'settings':settings,'config_sha256':sha(config_path),
        'producer_hashes':{p:sha(ROOT/p) for p in producers},
        'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'git_branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        'startup_state':'Pre-existing EVID-0234/DEC-0217 documentation edits and untracked stationary-Ibrahim code/results preserved; see preexisting_git_diff.patch and protected_inputs.json.',
        'environment':{'python':sys.version,'numpy':np.__version__,'scipy':__import__('scipy').__version__},
        'scope':'CLOUD_GENERATION_ONLY; no optical blockage, attenuation, QKD, SKR, finite-size or UAV optimization'})
    e=CirculantGRF(c);write_json(out/'spectrum_validation.json',e.spectrum_receipt)
    boundary=e.boundary_receipt();write_json(out/'boundary_validation.json',boundary)
    base=CloudGRFSimulator(c,e);frozen,numerical=frozen_stage(base,out)
    metrics=np.empty((len(seeds),c.slots,len(METRICS)))
    h=settings['space_time_h_xy_m'];sp=settings['spatial_lags_cells'];edges=np.array(settings['histogram_edges'])
    st=np.empty((len(seeds),len(lags),len(h)));material=np.empty((len(seeds),len(lags)))
    spatial=np.empty((len(seeds),2,len(sp)));hist=np.empty((len(seeds),len(snaps),len(edges)-1))
    main=np.empty((c.slots,c.ny,c.nx));thetas=[];all_tracks=[]
    for si,seed in enumerate(seeds):
        sim=base if si==0 else CloudGRFSimulator(replace(c,seed=seed),e)
        thetas.append(sim.theta);initial_material=e.sample(sim.field,material_slot=0);energy=np.mean(initial_material**2)
        tracker=DiagnosticTracker(sim.c)
        for k in range(c.slots):
            x=sim.initial if k==0 else sim.step();mask=x>sim.theta
            lab,count=components(mask);areas=np.bincount(lab.ravel())[1:]*c.dx_m*c.dy_m
            births,ends=tracker.update(lab,k)
            mat=e.sample(sim.field,material_slot=k)
            initial_presence=initial_material>sim.theta;now_presence=mat>sim.theta
            union=np.count_nonzero(initial_presence|now_presence)
            metrics[si,k]=[x.mean(),x.var(),np.mean(x*x),mask.mean(),np.mean(x**3),np.mean(x**4),count,
                           float(areas.mean()) if count else 0.,float(areas.max()) if count else 0.,births,ends,
                           np.sqrt(np.mean((mat-initial_material)**2)),np.count_nonzero(initial_presence&now_presence)/union if union else 1.]
            if k in (0,c.slots-1):
                for j,(dx,dy) in enumerate(sp):
                    a=x[:c.ny-dy or None,:c.nx-dx or None];b=x[dy:,dx:]
                    spatial[si,0 if k==0 else 1,j]=np.mean(a*b)
            if k in snaps:
                hist[si,snaps.index(k)]=np.histogram(x,bins=edges)[0]/x.size
            if k in lags:
                li=lags.index(k)
                material[si,li]=np.mean(initial_material*mat)/energy
                for j,(hx,hy) in enumerate(h):
                    target=e.sample(sim.field,offset_x=hx,offset_y=hy,material_slot=0)
                    st[si,li,j]=np.mean(initial_material*target)
            if si==0:main[k]=x
        records=tracker.finish()
        all_tracks.extend(dict(seed=seed,**record) for record in records)
        print(f'seed {seed}: {si+1}/{len(seeds)}; final fraction={metrics[si,-1,3]:.4f}; track segments={len(records)}',flush=True)
    metadata={'model_name':MODEL_NAME,'parameters':asdict(c),'theta_c_actual':thetas[0],'rho':c.rho,'innovation_scale':c.alpha,
              'threshold_origin':'Analytic N(0,1) ensemble quantile' if c.threshold_mode=='ensemble' else c.threshold_mode,
              'latent_units':'dimensionless Gaussian','intensity_units':'relative uncalibrated proxy; NOT CLWC',
              'diagnostic_mask_semantics':'cloud presence only; NOT optical blockage',
              'coordinates':'array[k,y,x]; centres in metres, y increases upward; point samples, no area averaging',
              'boundary':boundary,'advection':'Exact integer internal shift; -5m is -1 internal x cell and -0.125 output x cell per slot'}
    np.savez_compressed(out/'cloud_fields.npz',latent_field=main,relative_intensity=relative_intensity(main,thetas[0],c),
                        diagnostic_mask=(main>thetas[0]).astype(np.uint8),x_m=(np.arange(c.nx)+.5)*c.dx_m,
                        y_m=(np.arange(c.ny)+.5)*c.dy_m,time_s=np.arange(c.slots)*c.dt_s,parameters_json=np.array(json.dumps(metadata)))
    np.savez_compressed(out/'ensemble_validation.npz',seeds=seeds,metrics=metrics,metric_names=METRICS,
                        material_correlation=material,space_time_covariance=st,spatial_covariance=spatial,
                        histogram=hist,histogram_edges=edges,snapshot_slots=snaps,temporal_lags=lags,
                        h_xy_m=h,spatial_lags_cells=sp,theta_c=thetas)
    write_json(out/'metadata.json',metadata)
    write_csv(out/'track_segments.csv',all_tracks)
    mm,se,ci=uncertainty(metrics);time_rows=[]
    for k in range(c.slots):
        row={'slot':k,'time_s':k*c.dt_s}
        for j,name in enumerate(METRICS):
            row.update({name+'_main':float(metrics[0,k,j]),name+'_mean':float(mm[k,j]),name+'_SE':float(se[k,j]),name+'_CI95_half':float(ci[k,j])})
        time_rows.append(row)
    write_csv(out/'time_statistics.csv',time_rows)
    sp_rows=[];sp_mean,sp_se,sp_ci=uncertainty(spatial)
    for ti in (0,1):
        for j,(dx,dy) in enumerate(sp):
            sp_rows.append({'time':'initial' if ti==0 else 'final','hx_m':dx*c.dx_m,'hy_m':dy*c.dy_m,
                            'distance_m':np.hypot(dx*c.dx_m,dy*c.dy_m),'theory':e.covariance(dx*c.dx_m,dy*c.dy_m),
                            'empirical':sp_mean[ti,j],'SE':sp_se[ti,j],'CI95_half':sp_ci[ti,j]})
    write_csv(out/'spatial_covariance.csv',sp_rows)
    st_mean,st_se,st_ci=uncertainty(st);mt_mean,mt_se,mt_ci=uncertainty(material)
    st_rows=[];temp_rows=[]
    for li,lag in enumerate(lags):
        temp_rows.append({'lag':lag,'time_s':lag*c.dt_s,'theory':c.rho**lag,'empirical':mt_mean[li],'SE':mt_se[li],'CI95_half':mt_ci[li]})
        for j,(hx,hy) in enumerate(h):
            st_rows.append({'lag':lag,'hx_m':hx,'hy_m':hy,'theory':e.covariance(hx,hy,lag),
                            'embedding_theory':e.embedded_covariance(hx,hy,lag),'empirical':st_mean[li,j],
                            'SE':st_se[li,j],'CI95_half':st_ci[li,j]})
    write_csv(out/'space_time_covariance.csv',st_rows);write_csv(out/'material_correlation.csv',temp_rows)
    checks=[];sigma=settings['validation']['seed_SE_multiplier'];tol=settings['validation']['numerical_tolerance']
    def check(name,values,target):
        avg,error,half=uncertainty(values)
        checks.append({'name':name,'estimate':float(avg),'target':float(target),'SE':float(error),'CI95_half':float(half),
                       'passed':bool(abs(avg-target)<=sigma*error+tol)})
    expected_roi_var=e.expected_roi_variance()
    for k in snaps:
        for j,target in ((0,0),(1,expected_roi_var),(2,1),(4,0),(5,3)):
            check(f'{METRICS[j]}_k{k}',metrics[:,k,j],target)
    for j,(dx,dy) in enumerate(sp):
        for ti in (0,1):check(f'spatial_{ti}_{dx}_{dy}',spatial[:,ti,j],e.covariance(dx*c.dx_m,dy*c.dy_m))
    for li,lag in enumerate(lags):
        check(f'material_lag_{lag}',material[:,li],c.rho**lag)
        for j,(hx,hy) in enumerate(h):check(f'space_time_{lag}_{hx}_{hy}',st[:,li,j],e.covariance(hx,hy,lag))
    for j in (0,1,2):check(f'paired_final_initial_{METRICS[j]}',metrics[:,-1,j]-metrics[:,0,j],0)
    changed=[p for p,digest in protected.items() if sha(ROOT/p)!=digest]
    embedding_error=max(abs(row['theory']-row['embedding_theory']) for row in st_rows)
    integration_pass=not changed and boundary['status']==numerical['status']=='CURRENTLY_VERIFIED_PASS' and embedding_error<tol
    failed=[ch for ch in checks if not ch['passed']]
    summary={}
    for name,values in [('final_fraction',metrics[:,-1,3]),('initial_fraction',metrics[:,0,3]),
                        ('time_mean_fraction',metrics[:,:,3].mean(1)),('initial_variance',metrics[:,0,1]),('final_variance',metrics[:,-1,1])]:
        avg,error,half=uncertainty(values);summary[name]={'mean':float(avg),'SE':float(error),'CI95_half':float(half)}
    track_summary=[]
    for seed in seeds:
        rows=[r for r in all_tracks if r['seed']==seed];spans=np.array([r['observed_span_s'] for r in rows])
        track_summary.append({'seed':seed,'segments':len(rows),'mean_observed_span_s':float(spans.mean()),
                              'median_observed_span_s':float(np.median(spans)),'max_observed_span_s':float(spans.max()),
                              'ROI_or_time_censored_fraction':float(np.mean([r['roi_censored'] or r['left_time_censored'] or r['right_time_censored'] for r in rows]))})
    write_csv(out/'track_summary.csv',track_summary)
    report={'status':'CURRENTLY_VERIFIED_PASS' if integration_pass and not failed else 'FAILED',
            'numerical_integrity_status':'CURRENTLY_VERIFIED_PASS' if integration_pass else 'FAILED',
            'scope':'SYNTHETIC_CLOUD_GENERATION_ONLY','parameters':asdict(c),'rho':c.rho,'alpha':c.alpha,'main_theta':thetas[0],
            'main':{'initial_fraction':float(metrics[0,0,3]),'final_fraction':float(metrics[0,-1,3]),
                    'time_mean_fraction':float(metrics[0,:,3].mean()),'initial_variance':float(metrics[0,0,1]),'final_variance':float(metrics[0,-1,1])},
            'ensemble':summary,'independent_seeds':seeds,'checks':checks,'failed_checks':failed,
            'expected_ROI_population_variance':expected_roi_var,'max_space_time_embedding_target_error':embedding_error,
            'histogram_target_bin_probabilities':np.diff(norm.cdf(edges)).tolist(),
            'spectrum':e.spectrum_receipt,'frozen':numerical,'boundary':boundary,
            'protected_inputs':{'count':len(protected),'changed':changed},'elapsed_runner_s':time.perf_counter()-started,
            'uncertainty':'Approximate pointwise Student-t 95% intervals across independent seeds. Four-SE checks were declared before simulation; cells/slots are not independent replicates. Histograms are descriptive, not iid-pixel normality tests.',
            'tracking_limit':'Observed 8-connected-component segment spans. Split/merge ambiguity terminates identities; ROI/time censoring recorded. Wind-weighted indicator interpolation is association-only, not latent-field advection.',
            'not_run':['full repository test suite','meteorological/CLWC calibration','optical blockage/attenuation','QKD/SKR/finite-size/UAV integration','training/final-test/heldout/publication evaluation'],
            'security':'UNVALIDATED_SECURITY_MODEL','lifecycle':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
            'frozen_spec_sha256':sha(ROOT/'docs/FINAL_MODEL_SPEC.md'),'historical_frozen_hash_discrepancy_preserved':True}
    write_json(out/'validation.json',report)
    print(json.dumps({'status':report['status'],'main':report['main'],'ensemble':summary,'checks':len(checks),'failed_checks':failed,'elapsed_s':report['elapsed_runner_s']},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/stochastic_cloud_grf.json')
    parser.add_argument('--output',type=Path,default=ROOT/'results/stochastic_cloud_grf_20261111')
    args=parser.parse_args();run(args.config,args.output)
