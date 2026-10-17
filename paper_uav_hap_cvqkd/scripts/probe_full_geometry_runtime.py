"""Read-only runtime reconstruction for four declared geometry diagnostics."""
import copy
from dataclasses import asdict,is_dataclass
import hashlib,inspect,json,math,sys
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts._common import load_yaml
from src.binary_cloud_skr import clear_state,load_sources
from src.uav_mobility import candidate_grid
from src.trusted_heterodyne_skr import evaluate_candidate

OUT=ROOT/'results/full_geometry_fading_skr_audit_20261017'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def clean(value):
    if is_dataclass(value):return clean(asdict(value))
    if isinstance(value,Path):return value.as_posix()
    if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [clean(x) for x in value]
    if isinstance(value,float) and not math.isfinite(value):return {'float_hex':value.hex()}
    if hasattr(value,'tolist'):return clean(value.tolist())
    if hasattr(value,'item'):return clean(value.item())
    return value


def main():
    assert not (OUT/'runtime_probe.json').exists(),'Completed probe is immutable'
    start=read(OUT/'startup_manifest.json');settings=read(ROOT/'configs/binary_cloud_skr_demo.json')
    defaults=load_yaml(ROOT/'configs/default.yaml');old=ROOT/'results/trusted_heterodyne_skr_20261016'
    prior=read(old/'completion_integrity_receipt.json')
    for p,h in prior['receipts_and_report_sha256'].items():
        if sha(old/p)!=h:raise ValueError('Prior artifact changed: '+p)
    for p,h in read(old/'inputs.json')['producers'].items():
        if sha(ROOT/p)!=h:raise ValueError('Prior producer changed: '+p)
    groups,config,aliases=load_sources(settings,start['protected_hashes']);pair=read(ROOT/'configs/fading_effective_binary_cloud.json')['reference_pair']
    source=next(x for x in groups['MB'] if all(x[k]==v for k,v in pair.items()))
    ensemble=source['ensemble'];a=ensemble.amplitudes[0].tolist()
    selected={k:source[k] for k in ('nu_raw','V_A','C','w','ensemble_hash','source_cache_key','source_path')}
    selected.update(source_payload_sha256=sha(ROOT/source['source_path']),probabilities=ensemble.probabilities[0].tolist(),amplitudes=[[x.real,x.imag] for x in a])
    trusted=read(ROOT/'configs/manuscript_corrected_3moments.json')
    detectors={'ideal_primary':dict(eta_B=settings['channel']['R'],nu_B=settings['channel']['xi_det']),
               'trusted_diagnostic':dict(eta_B=trusted['R'],nu_B=trusted['xi_det'])}
    index=settings['geometry']['reference_position_index'];position=candidate_grid()[index]
    traces=[];active_case=None
    functions={'derive_physical_inputs','gaussian_beam_radius','manuscript_pointing_parameters',
               'hufnagel_valley_scintillation','from_physical','moments','link_geometry','load_yaml'}
    def profile(frame,event,arg):
        name=frame.f_code.co_name;filename=frame.f_code.co_filename.replace('\\','/')
        if name not in functions or not filename.startswith(ROOT.as_posix()+'/'):return
        code=frame.f_code;count=code.co_argcount+code.co_kwonlyargcount
        args={n:frame.f_locals.get(n) for n in code.co_varnames[:count] if n not in ('self','cls','config')}
        if name=='from_physical':args={'physical':frame.f_locals['physical']}
        if name=='moments':args={k:v for k,v in args.items() if k!='moments'}
        if event=='call':traces.append(dict(case=active_case,event=event,file=filename[len(ROOT.as_posix())+1:],function=name,line=code.co_firstlineno,arguments=clean(args)))
        elif event=='return' and name in ('derive_physical_inputs','from_physical','moments','manuscript_pointing_parameters'):
            if name=='moments' and not isinstance(arg,dict):return
            traces.append(dict(case=active_case,event=event,file=filename[len(ROOT.as_posix())+1:],function=name,line=code.co_firstlineno,result=clean(arg)))
    cases=[];torch.set_num_threads(1)
    combinations=[('A',2*settings['channel']['receiver_radius_m'],None),('B',.08,233e-6),('C',.55,233e-6),('D',.08,10e-6)]
    for case,diameter,divergence in combinations:
        cfg=copy.deepcopy(settings);cfg['channel']['receiver_radius_m']=diameter/2
        if divergence is not None:cfg['channel']['beam_waist_m']=2*defaults['channel']['wavelength_m']/(math.pi*divergence)
        active_case=case;sys.setprofile(profile)
        try:state=clear_state(cfg,position,index)
        finally:sys.setprofile(None)
        rows={name:evaluate_candidate(source,state['moments'],config,start['protected_hashes'],**d) for name,d in detectors.items()}
        fingerprint=hashlib.sha256(json.dumps(dict(channel=cfg['channel'],geometry=cfg['geometry'],raw=state['clear_raw_channel'],physical=state['physical']),sort_keys=True,separators=(',',':')).encode()).hexdigest()
        cases.append(dict(case=case,settings=cfg,state=state,geometry_fingerprint=fingerprint,production_results=rows))
        print('RUNTIME_CASE',case,'Dr',state['physical']['receiver_diameter_m'],'theta',state['physical']['theta_div_rad'],'m1',state['moments']['mean_eta'],flush=True)
    cached_state=read(ROOT/'results/binary_cloud_skr_20261015/clear_channel_states.json')[index]
    old_reference=read(old/'reference_decomposition.json')
    comparisons={name:{k:cases[0]['production_results'][name][k]-old_reference[key][k] for k in ('I_AB','chi_BE','K_raw','W_pre','Z_star')} for name,key in (('ideal_primary','corrected_primary'),('trusted_diagnostic','trusted_detector_diagnostic'))}
    files=('configs/default.yaml','configs/binary_cloud_skr_demo.json','configs/trusted_heterodyne_skr.json',
           'configs/fading_effective_binary_cloud.json','configs/manuscript_corrected_3moments.json',
           'scripts/_common.py','scripts/calculate_channel_pdf_and_moments.py','src/channel/pointing_error.py',
           'src/channel/scintillation.py','src/mobility_skr.py','src/manuscript_literal_3moments.py',
           'src/manuscript_corrected_3moments.py','src/trusted_heterodyne_skr.py','src/uav_mobility.py',
           'scripts/run_trusted_heterodyne_skr.py')
    env_matches={p:[(i+1,l.strip()) for i,l in enumerate((ROOT/p).read_text(encoding='utf-8').splitlines()) if any(x in l for x in ('os.environ','os.getenv','environ[','environ.get('))] for p in files if p.endswith('.py')}
    entry=(ROOT/'scripts/run_trusted_heterodyne_skr.py').read_text(encoding='utf-8')
    result=dict(status='RUNTIME_RECONSTRUCTED_PENDING_INDEPENDENT_AUDIT',defaults=clean(defaults),binary_settings=settings,
                cases=cases,source=selected,detectors=detectors,source_aliases=aliases,beta_rec=config['cvqkd']['beta_reconciliation'],
                raw_runtime_source_fingerprints={p:sha(ROOT/p) for p in files},runtime_trace=traces,
                fresh_A_matches_saved_state=cases[0]['state']==cached_state,reference_old_new_residual=comparisons,
                objective_cache_reused=False,source_moments_built=0,new_SKR_calls=8,full_catalog_or_missions_run=False,
                cli=dict(probe_argv=sys.argv,historical_runner_supported_arguments=['--stage','--output'],historical_physics_cli_overrides=False,historical_argv_not_saved=True),
                environment_config_reads=env_matches,no_environment_physics_override_path=not any(env_matches.values()),
                detector_0p8_in_active_configs=False,probe_script_sha256=sha(Path(__file__)))
    (OUT/'runtime_probe.json').write_text(json.dumps(clean(result),indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('RUNTIME_PROBE_SAVED',result['fresh_A_matches_saved_state'],comparisons,flush=True)


if __name__=='__main__':main()
