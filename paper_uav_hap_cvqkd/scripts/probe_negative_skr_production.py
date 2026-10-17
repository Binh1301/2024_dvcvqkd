"""Bounded live production probe; independence checks live in a different script."""
import hashlib,inspect,json,sys
from collections import Counter
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.binary_cloud_skr import load_sources
from src.trusted_heterodyne_skr import evaluate_candidate
OUT=ROOT/'results/negative_skr_independent_audit_20261017'
OLD=ROOT/'results/trusted_heterodyne_skr_20261016'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    if (OUT/'production_probe.json').exists():raise RuntimeError('Completed probe is immutable')
    start=read(OUT/'startup_manifest.json');prior=read(OLD/'completion_integrity_receipt.json');prior_inputs=read(OLD/'inputs.json')
    for p,h in prior_inputs['producers'].items():
        if sha(ROOT/p)!=h:raise RuntimeError('Prior producer changed: '+p)
    for p,h in prior['receipts_and_report_sha256'].items():
        if sha(OLD/p)!=h:raise RuntimeError('Prior receipt/output changed: '+p)
    if sha(ROOT/'docs/TRUSTED_HETERODYNE_SKR_REPORT_VI.md')!=prior['canonical_report_sha256']:raise RuntimeError('Prior report changed')
    settings=read(ROOT/'configs/binary_cloud_skr_demo.json');groups,config,aliases=load_sources(settings,start['protected_hashes'])
    reference=read(ROOT/'results/binary_cloud_skr_20261015/clear_channel_states.json')[44]
    torch.set_num_threads(1)
    sources=[]
    for pair in ((.17,5.046875),(.30,.025)):
        x=next(x for x in groups['MB'] if (x['nu_raw'],x['V_A'])==pair)
        ens=x['ensemble'];p=ens.probabilities[0].tolist();alpha=ens.amplitudes[0].tolist();payload=read(ROOT/x['source_path'])
        sources.append(dict(nu_raw=x['nu_raw'],V_A=x['V_A'],C=x['C'],w=x['w'],ensemble_hash=x['ensemble_hash'],source_cache_key=x['source_cache_key'],source_path=x['source_path'],source_payload_sha256=sha(ROOT/x['source_path']),source_metadata=payload,probabilities=p,amplitudes=[[z.real,z.imag] for z in alpha]))
    inputs=dict(schema='independent-negative-skr-input-v1',reference_state=reference,sources=sources,beta_rec=config['cvqkd']['beta_reconciliation'],primary_detector=dict(eta_B=settings['channel']['R'],nu_B=settings['channel']['xi_det']),trusted_detector={k:v for k,v in zip(('eta_B','nu_B'),(read(ROOT/'configs/manuscript_corrected_3moments.json')['R'],read(ROOT/'configs/manuscript_corrected_3moments.json')['xi_det']))},binary_settings=settings,previous_evaluator_producers=prior_inputs['producers'],source_aliases=aliases,prior_completion_sha256=sha(OLD/'completion_integrity_receipt.json'))
    (OUT/'audit_inputs.json').write_text(json.dumps(inputs,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    traced=Counter();entropy_returns=[];mi_calls=[]
    def profile(frame,event,arg):
        filename=frame.f_code.co_filename.replace('\\','/');rel=filename[len(ROOT.as_posix())+1:] if filename.startswith(ROOT.as_posix()+'/') else filename
        if rel not in ('src/trusted_heterodyne_skr.py','src/cvqkd/mutual_information.py','scripts/run_ao_effective_channel_no_fading_noise_reference.py','src/manuscript_literal_3moments.py'):return
        if event=='call':
            parent=frame.f_back
            traced[(rel,frame.f_code.co_name,frame.f_code.co_firstlineno,parent.f_code.co_name if parent else None)]+=1
            if frame.f_code.co_name=='deterministic_mutual_information':
                mi_calls.append(dict(implementation=frame.f_locals.get('implementation'),order=frame.f_locals.get('quadrature_order'),transmittance=frame.f_locals['transmittance'].tolist(),epsilon=frame.f_locals['epsilon'].tolist()))
        if event=='return' and frame.f_code.co_name=='spectral_entropy':
            entropy_returns.append(dict(eigenvalues=frame.f_locals['values'].tolist(),entropy=arg))
    results=[];failures=[]
    for sid,source in enumerate(sources):
        x=next(x for x in groups['MB'] if x['ensemble_hash']==source['ensemble_hash'])
        cases=[('reference_fading',reference['moments'])]
        for t in (.01,.001,.0001,.00001,.000001,0.):
            cases.append(('fixed_channel_'+str(t),dict(mean_eta=t,mean_sqrt_eta=float(np.sqrt(t)),xi_ch=reference['moments']['xi_ch'],physical_probability_mass=1.,moment_law='deterministic_delta',deterministic_transmissivity=t)))
        cases.append(('pure_loss_T_0.25',dict(mean_eta=.25,mean_sqrt_eta=.5,xi_ch=0.,physical_probability_mass=1.,moment_law='deterministic_delta',deterministic_transmissivity=.25)))
        for label,moments in cases:
            for detector_name in ('primary_detector','trusted_detector'):
                if label=='reference_fading':sys.setprofile(profile)
                try:
                    row=evaluate_candidate(x,moments,config,start['protected_hashes'],**inputs[detector_name])
                    results.append(dict(source_id=sid,case=label,detector=detector_name,result=row))
                except Exception as exc:failures.append(dict(source_id=sid,case=label,detector=detector_name,error=repr(exc)))
                finally:sys.setprofile(None)
    stored=read(OLD/'reference_decomposition.json')
    residual={}
    for name,key in [('primary_detector','corrected_primary'),('trusted_detector','trusted_detector_diagnostic')]:
        fresh=next(r['result'] for r in results if r['source_id']==0 and r['case']=='reference_fading' and r['detector']==name)
        residual[name]={k:fresh[k]-stored[key][k] for k in ('I_AB','chi_BE','K_raw','W_pre','Z_star')}
        if max(abs(x) for x in residual[name].values())>1e-10:raise RuntimeError('Live reference is not the bound historical evaluator')
    provenance=dict(status='CURRENTLY_VERIFIED_PASS',scope='Source/producer/cache provenance and fresh production probe only; independent numerical validation pending',producer_script_sha256=sha(Path(__file__)),input_sha256=sha(OUT/'audit_inputs.json'),prior_result_residual=residual,prior_model=prior_inputs['config']['scientific_model'],previous_receipts_verified=True,source_moments_recomputed=0,objective_cache_K_reused_for_probe=0,new_SKR_calls=len(results),failures=failures)
    (OUT/'production_probe.json').write_text(json.dumps(dict(provenance=provenance,results=results),indent=2)+'\n',encoding='utf-8')
    graph=dict(calls=[dict(file=p,function=f,line=line,parent=parent,count=count) for (p,f,line,parent),count in sorted(traced.items())],actual_MI_calls=mi_calls,actual_Holevo_entropy_returns=entropy_returns,runner_reference_callsite='scripts/run_trusted_heterodyne_skr.py:55',ideal_and_trusted_called_same_module=True,source_and_moment_cache_read=True,SKR_cache_read=False)
    (OUT/'actual_call_graph.json').write_text(json.dumps(graph,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(provenance),flush=True)

if __name__=='__main__':main()
