"""Stage 1 only: audit saved numerical values; no SKR/source solver calls."""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
import subprocess
import sys

import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
OLD=ROOT/'results/skr_vs_zenith_angle_20261019'
DIAG=ROOT/'results/zenith_angle_root_cause_diagnostic_20261021'
sys.path.insert(0,str(ROOT))
from scripts.exact_cache_provenance import verify_source_payload

ANGLES=[24,30,40,48,52,60]
CHECKS=[]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def js(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def rows(path):
    with path.open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def csvout(name,data,fields=None):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(data[0]));w.writeheader();w.writerows(data)


def check(name,ok):
    CHECKS.append(dict(check=name,status='CURRENTLY_VERIFIED_PASS' if bool(ok) else 'FAILED'))
    if not ok:
        save('validation/failed_checks.json',CHECKS)
        raise AssertionError(name)


def jsonhash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def tensor(data,dtype,shape,complex_values=False):
    values=[[float(v.real).hex(),float(v.imag).hex()] for v in data] if complex_values else [float(v).hex() for v in data]
    return dict(dtype=dtype,shape=shape,data=values)


def main():
    if (OUT/'validation/final_receipt.json').exists():
        raise FileExistsError('Sealed stage-1 audit is immutable')
    for name in ['validation','figures','data']:
        (OUT/name).mkdir(exist_ok=True)
    if not (OUT/'startup_manifest.json').exists():
        protected={}
        for folder in ['src','scripts','configs','tests','docs','.agent','results']:
            for p in (ROOT/folder).rglob('*'):
                if p.is_file() and OUT not in p.parents and not any(s in ('__pycache__','.pytest_cache') for s in p.parts):
                    protected[p.relative_to(ROOT).as_posix()]=sha(p)
        git={}
        for key,args in [('head',['rev-parse','HEAD']),('branch',['branch','--show-current']),('status',['status','--short']),('diff',['diff'])]:
            git[key]=subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True).stdout
        save('startup_manifest.json',dict(git=git,protected_sha256=protected))
        (OUT/'validation/preexisting_handoff.md').write_bytes((ROOT/'.agent/SESSION_HANDOFF.md').read_bytes())
    receipt_audit=[]
    for folder,name in [(OLD,'validation_receipt.json'),(DIAG,'validation/final_receipt.json')]:
        for member,digest in js(folder/name)['artifact_sha256'].items():
            p=ROOT/member if member.split('/')[0] in ('src','scripts','configs','docs','tests','results','.agent') else folder/member
            data=p.read_bytes();raw=sha(p);lf=hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()
            status='RAW_SHA256_MATCH' if raw==digest else 'CRLF_ONLY_CONTENT_MATCH' if lf==digest else 'FAILED'
            check('historical receipt '+str(p.relative_to(ROOT)),status!='FAILED')
            receipt_audit.append(dict(path=p.relative_to(ROOT).as_posix(),comparison=status,historical_sha256=digest,current_sha256=raw))
    save('validation/receipt_authentication.json',receipt_audit)
    protocol=js(OLD/'protocol.json')
    check('218-source historical configuration',protocol['catalogs']=={'Uniform':36,'MB':182})
    check('historical optical settings',protocol['optical']['full_divergence_rad']==233e-6 and protocol['optical']['receiver_diameter_m']==.08)
    check('historical detector and noise',protocol['R']==1 and protocol['xi_det']==0 and protocol['xi_ch']==.0186 and protocol['beta']==.95)
    check('historical source normalization',protocol['normalization']=='VA=2*nbar')
    roster=rows(OLD/'source_roster.csv');evaluations=rows(OLD/'all_candidate_evaluations.csv');details=rows(OLD/'skr_vs_zenith_angle_detailed.csv')
    check('218 unique sources',len(roster)==218 and len({r['ensemble_hash'] for r in roster})==218)
    check('6758 saved values',len(evaluations)==31*218)
    check('31 angles',sorted({float(r['zenith_deg']) for r in evaluations})==list(range(0,61,2)))
    arrays=np.load(OLD/'verified_ensembles.npz',allow_pickle=False)
    source_map={};source_manifest=[];catalog=[]
    raw_grid=np.arange(16,dtype=float)-7.5
    expected_settings=dict(density_eigenvalue_tolerance=1e-12,physicality_tolerance=1e-10,precision_ladder=[1050,1250,1450])
    for index,r in enumerate(roster):
        eh=r['ensemble_hash'];p=arrays[eh+'_p'];a=arrays[eh+'_alpha'];nu=float(r['nu_raw']);va=float(r['VA'])
        payload=js(ROOT/r['source_path'])
        validation=verify_source_payload(payload,expected_settings)
        check('source exact provenance '+eh,validation['status']=='VERIFIED')
        source_bytes=(ROOT/r['source_path']).read_bytes()
        check('source file identity '+eh,sha(ROOT/r['source_path'])==r['source_sha256'] or hashlib.sha256(source_bytes.replace(b'\r\n',b'\n')).hexdigest()==r['source_sha256'])
        identity=dict(schema='exact-common-ensemble-v1',probabilities=tensor(p,'torch.float64',[1,256]),
            amplitudes=tensor(a,'torch.complex128',[1,256],True),declared_va=tensor([va],'torch.float64',[1]))
        check('ensemble hash '+eh,jsonhash(identity)==eh==payload['ensemble_hash'])
        check('256 positive distinct states '+eh,p.shape==a.shape==(256,) and np.all(p>0) and len(np.unique(a))==256)
        energy=2*float(np.dot(p,abs(a)**2));pmf_error=abs(float(p.sum())-1)
        check('PMF and VA '+eh,pmf_error<1e-14 and abs(energy-va)<2e-12)
        x,ix=np.unique(a.real,return_inverse=True);y,iy=np.unique(a.imag,return_inverse=True)
        target=np.exp(-nu*raw_grid**2);target/=target.sum();scale=math.sqrt(va/(4*float(np.dot(target,raw_grid**2))))
        check('raw MB PMF '+eh,np.max(abs(p-target[ix]*target[iy]))<2e-14 and np.max(abs(x-scale*raw_grid))<2e-13 and np.max(abs(y-scale*raw_grid))<2e-13)
        check('nu convention and moments '+eh,float.fromhex(payload['nu_mb_repo_hex'])==42.5*nu and float.fromhex(payload['nu_mb_raw_hex'])==nu and float.fromhex(payload['V_A_hex'])==va and float(r['C'])==payload['C'] and float(r['w'])==payload['w'] and payload['C']>0 and payload['w']>=0)
        source_map[eh]=r
        cat=dict(roster_index=index,**r,nu_repo=42.5*nu,mean_photons=va/2,peak_photons_observed=float(max(abs(a)**2)),pmf_sum_error=pmf_error,VA_reconstructed=energy)
        catalog.append(cat)
        source_manifest.append(dict(ensemble_hash=eh,family=r['family'],nu_raw=nu,VA=va,
            provenance='REUSED_ORIGINAL_218_SOURCE_CATALOG',source_path=r['source_path'],
            source_current_sha256=sha(ROOT/r['source_path']),C=r['C'],w=r['w'],moment_recomputation='NOT_RUN',
            solver_route=r['source_moment_route'],support_size=256))
    csvout('original_catalog_candidates.csv',catalog);csvout('source_manifest.csv',source_manifest)
    channels=js(OLD/'channel_by_angle.json');by_angle=defaultdict(list);residuals=[];identities=set()
    for r in evaluations:
        z=float(r['zenith_deg']);s=source_map[r['ensemble_hash']];va=float(r['VA']);ch=channels[str(int(z))]
        identity=(z,r['ensemble_hash']);check('unique candidate value '+str(identity),identity not in identities);identities.add(identity)
        check('source binding '+str(identity),all(r[k]==s[k] for k in ['family','nu_raw','VA','C','w','source_sha256']))
        m1=float(ch['mean_eta']);ms=float(ch['mean_sqrt_eta']);tf=ms*ms
        expected_N=(m1-tf)*va+.0186*m1
        rate_residual=float(r['K_raw'])-(.95*float(r['I_AB_2D'])-float(r['chi_BE']))
        noise_residual=float(r['N'])-expected_N
        check('saved decomposition '+str(identity),abs(rate_residual)<2e-18 and abs(noise_residual)<2e-17 and abs(float(r['eta_f'])-tf)<2e-18)
        gh=max(abs(float(r['MI_GH'+str(o)])-float(r['MI_GH64'])) for o in [16,32,64])
        check('saved numerical gates '+str(identity),gh<2e-13 and float(r['uncertainty_min_eigenvalue'])>0 and float(r['matrix_spectrum_max_difference'])<2e-11)
        check('saved covariance '+str(identity),abs(float(r['V'])-(1+va))<1e-13 and abs(float(r['W'])-(1+tf*va+expected_N))<1e-13)
        check('per-angle geometry '+str(identity),abs(float(r['distance_km'])-19/math.cos(math.radians(z)))<1e-11)
        by_angle[(z,r['family'])].append(r)
        residuals.append(dict(zenith_deg=z,ensemble_hash=r['ensemble_hash'],family=r['family'],K_raw=r['K_raw'],K_reconstruction_residual=rate_residual,N_reconstruction_residual=noise_residual,GH_max_difference=gh))
    csvout('candidate_value_validation.csv',residuals)
    audit=[];bounds=[];local=[];summary_table=[]
    for z in range(0,61,2):
        for family,scheme in [('Uniform','Optimized Uniform'),('MB','Optimized MB')]:
            allrows=by_angle[(z,family)]
            ordered=sorted(allrows,key=lambda r:-float(r['K_raw']))
            best=ordered[0];second=ordered[1];reported=next(r for r in details if float(r['zenith_deg'])==z and r['scheme']==scheme)
            check('catalog argmax '+str((z,family)),best['ensemble_hash']==reported['ensemble_hash'] and best['K_raw']==reported['K_raw'])
            va_values=[float(r['VA']) for r in allrows];nu_values=[float(r['nu_raw']) for r in allrows]
            va=float(best['VA']);nu=float(best['nu_raw']);gap=float(best['K_raw'])-float(second['K_raw'])
            check('strict numerical winner '+str((z,family)),gap>0)
            item=dict(zenith_deg=z,scheme=scheme,candidate_count=len(allrows),negative_candidates=sum(float(r['K_raw'])<0 for r in allrows),
                best_VA=va,best_nu_raw=nu,best_nu_repo=42.5*nu,K_raw=best['K_raw'],ensemble_hash=best['ensemble_hash'],
                reported_argmax_matches=True,runner_up_gap_bits_per_use=gap,VA_at_lower_bound=va==min(va_values),VA_at_upper_bound=va==max(va_values),
                nu_at_lower_bound=family=='MB' and nu==min(nu_values),nu_at_upper_bound=family=='MB' and nu==max(nu_values),
                optimality_status='GLOBAL OPTIMUM OVER THE FINITE TESTED CATALOG',continuous_global_optimum='NOT_CERTIFIED')
            audit.append(item)
            same=sorted((r for r in allrows if float(r['nu_raw'])==nu),key=lambda r:float(r['VA']))
            left,right=same[-2:];delta=float(right['K_raw'])-float(left['K_raw']);slope=delta/(float(right['VA'])-float(left['VA']))
            bounds.append(dict(zenith_deg=z,family=family,nu_raw=nu,VA_left=left['VA'],VA_right=right['VA'],K_left=left['K_raw'],K_right=right['K_raw'],
                delta_K_at_catalog_tail=delta,tail_secant_bits_per_use_per_SNU=slope,
                interpretation='FINITE_SECANT_NOT_A_BOUNDARY_DERIVATIVE_OR_EXTRAPOLATION',winner_at_upper_boundary=item['VA_at_upper_bound']))
            if family=='Uniform':
                for i in range(1,len(same)-1):
                    if float(same[i]['K_raw'])>max(float(same[i-1]['K_raw']),float(same[i+1]['K_raw'])):
                        local.append(dict(zenith_deg=z,VA= same[i]['VA'],K_raw=same[i]['K_raw'],left_VA=same[i-1]['VA'],right_VA=same[i+1]['VA'],classification='SAMPLED_NEIGHBORHOOD_MAXIMUM_NOT_CONTINUOUS_CERTIFICATE'))
            if z in ANGLES:
                summary_table.append(dict(zenith_deg=z,scheme=family,old_VA=va,old_nu=nu,new_VA='N/A',new_nu='N/A',old_SKR=best['K_raw'],new_SKR='N/A',absolute_improvement='N/A',gain_percent='N/A',
                    percentage_baseline_status='POSITIVE_BASELINE' if float(best['K_raw'])>0 else 'NONPOSITIVE_BASELINE_PERCENTAGE_UNDEFINED',
                    optimality_status='CATALOG_GLOBAL; NEW_SEARCH_PENDING_DOMAIN_APPROVAL',certified_global_gap='NOT_CERTIFIED'))
    csvout('original_catalog_audit.csv',audit);csvout('boundary_audit.csv',bounds)
    csvout('sampled_uniform_local_maxima.csv',local)
    csvout('refined_optima.csv',summary_table);csvout('optimality_improvement.csv',summary_table)
    csvout('new_exact_candidates.csv',[],['family','nu_raw','nu_repo','VA','C','w','ensemble_hash','source_path','status'])
    spacing=[]
    for family in ['Uniform','MB']:
        sub=[r for r in catalog if r['family']==family]
        for axis in ['nu_raw','VA']:
            values=sorted({float(r[axis]) for r in sub})
            for i,value in enumerate(values):
                spacing.append(dict(family=family,axis=axis,value=value,value_hex=value.hex(),previous_value=values[i-1] if i else 'N/A',step=value-values[i-1] if i else 'N/A'))
    csvout('parameter_spacing.csv',spacing)
    coverage={f:dict(candidates=len([r for r in roster if r['family']==f]),
        VA_min=min(float(r['VA']) for r in roster if r['family']==f),VA_max=max(float(r['VA']) for r in roster if r['family']==f),
        nu_min=min(float(r['nu_raw']) for r in roster if r['family']==f),nu_max=max(float(r['nu_raw']) for r in roster if r['family']==f),
        unique_VA=len({r['VA'] for r in roster if r['family']==f}),unique_nu=len({r['nu_raw'] for r in roster if r['family']==f})) for f in ['Uniform','MB']}
    save('summary.json',dict(stage='STAGE_1_COMPLETE_AWAITING_DOMAIN_APPROVAL',coverage=coverage,
        original_candidate_evaluations=len(evaluations),argmax_checks=len(audit),argmax_mismatches=0,
        smallest_runner_up_gap=min(r['runner_up_gap_bits_per_use'] for r in audit),
        MB_upper_VA_angles=[r['zenith_deg'] for r in audit if r['scheme']=='Optimized MB' and r['VA_at_upper_bound']],
        Uniform_upper_VA_angles=[r['zenith_deg'] for r in audit if r['scheme']=='Optimized Uniform' and r['VA_at_upper_bound']],
        new_source_evaluations=0,new_rate_evaluations=0,continuous_global_gap='NOT_CERTIFIED',
        historical_receipt_comparisons=dict(Counter(r['comparison'] for r in receipt_audit)),
        source_normalization='VA=2*nbar',nu_convention='nu_repo=42.5*nu_raw',
        domain_gate='No historical physical energy bound; numerical exploratory box requires approval',
        security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS'))
    save('proposed_pilot.json',dict(status='PROPOSED_NOT_APPROVED_NOT_EXECUTED',angles_deg=ANGLES,
        domain_kind='BOUNDED_NUMERICAL_EXPLORATION_NOT_PHYSICAL_CONSTRAINT',
        Uniform_VA_interval=[.02,48],MB_nu_raw_interval=[0,1.6],MB_VA_interval=[.025,32],
        first_batch_max_new_sources=6,first_batch_max_new_rate_evaluations=36,
        first_batch=[dict(family='Uniform',nu_raw=0,VA=v) for v in [16,24,48]]+
                    [dict(family='MB',nu_raw=n,VA=16) for n in [.08,.125,.2]],
        per_source_AP_timeout_seconds=3600,first_batch_max_source_worker_seconds=21600,
        source_call_policy='sequential; validated cache reuse first; stop on unsupported 256-state precision or provenance failure',
        stop_rules=['six-source budget; no automatic expansion or second batch',
            'any unresolved exact moments/PMF/geometry/covariance/ranking stops dependent claims',
            'upper-bound best remains boundary-limited',
            'no all-31-angle refinement without a new scoped decision'],
        certificate='GLOBAL OPTIMALITY GAP: NOT CERTIFIED'))
    inputs=[OLD/n for n in ['run_sweep.py','protocol.json','channel_by_angle.json','all_candidate_evaluations.csv',
        'skr_vs_zenith_angle_detailed.csv','source_roster.csv','verified_ensembles.npz','validation_receipt.json','manuscript_text.txt','request.txt']]
    inputs += [ROOT/n for n in ['docs/FINAL_MODEL_SPEC.md','docs/SECURITY_SCOPE_FREEZE.md','docs/NUMERICAL_CONVERGENCE_PREREGISTRATION.md',
        'scripts/run_exact_mb_test2.py','scripts/run_theta10_D55_unconstrained_three_scheme.py','scripts/exact_cache_provenance.py','scripts/full_support_c4_worker.py','src/cvqkd/gram_moments.py']]
    inputs.append(DIAG/'validation/final_receipt.json')
    save('input_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in inputs})
    save('validation/audit_checks.json',dict(status='CURRENTLY_VERIFIED_PASS',checks=len(CHECKS),check_names=CHECKS,
        max_K_reconstruction_residual=max(abs(float(r['K_reconstruction_residual'])) for r in residuals),
        max_N_reconstruction_residual=max(abs(float(r['N_reconstruction_residual'])) for r in residuals),
        max_saved_GH_difference=max(float(r['GH_max_difference']) for r in residuals),
        exact_moments_recomputation='NOT_RUN; authenticated historical source payloads only',new_scientific_calls=0))
    print(json.dumps(dict(checks=len(CHECKS),evaluations=len(evaluations),catalog_argmax=62,new_sources=0,new_rate_calls=0)))


if __name__=='__main__':
    main()
