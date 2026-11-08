"""Bounded five-position real-producer pilot; never a full lookup/paper runner.

python -B -m uav_qkd.skr_pilot --output results/phase5c_skr_noise_pilot_20261107
"""
import argparse
import copy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np
from .config import load_config
from .phase5b_audit import audit_lookup_noise
from .skr_lookup import compare_lookup_setup

ROOT=Path(__file__).resolve().parents[2]
PARENT=ROOT.parent/'paper_uav_hap_cvqkd'
LOOKUP=PARENT/'results/skr_zenith_heatmap_20261106'
METRICS=('eta_f','xi_f','I_AB','chi_BE','K_raw')
ATOL=2e-10


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def read_rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def select_positions(rows):
    rows=[dict(r,x_m=float(r['x_m']),y_m=float(r['y_m'])) for r in rows]
    chosen=[];used=set()
    def add(row,role):
        r2=(row['x_m']-1000)**2+(row['y_m']-1000)**2
        if r2 in used:return False
        used.add(r2)
        chosen.append(dict(point_id=f'p{len(chosen)}',role=role,x_m=row['x_m'],y_m=row['y_m'],
                           radius2_m2=r2,zenith_deg=float(row['zenith_deg']),distance_m=float(row['distance_m'])))
        return True
    for xy,role in [((1000.,1000.),'projection'),((1480.,1000.),'intermediate'),((0.,0.),'farthest')]:
        add(next(r for r in rows if (r['x_m'],r['y_m'])==xy),role)
    for descending,role in [(True,'additional_high_lookup'),(False,'additional_low_lookup')]:
        for r in sorted(rows,key=lambda r:((-1 if descending else 1)*float(r['MB_K_raw']),r['y_m'],r['x_m'])):
            if add(r,role):break
    if len(chosen)!=5:raise ValueError('Pilot needs exactly five distinct map geometries')
    return chosen


def effective_protocol(original,noise):
    if noise not in (.0186,.0136):raise ValueError('Only the two author-authorized pilot noises are supported')
    return dict(xi_ch=noise,xi_det=original['xi_det'],beta=original['beta'],numerical=copy.deepcopy(original['numerical']))


def compare_candidate(actual,expected):
    delta={k:abs(float(actual[k])-float(expected[k])) for k in METRICS}
    identity=all(actual[k]==expected[k] for k in ('ensemble_hash','VA','nu_raw'))
    return dict(passed=bool(identity and all(np.isfinite(v) and v<=ATOL for v in delta.values())),
                identity_matches=identity,absolute_deviation=delta,atol=ATOL,rtol=0.)


def require_reproduction_pass(checks):
    if len(checks)!=5 or not all(c.get('passed') is True for c in checks):
        raise ValueError('Target-noise pilot requires all five reproduction checks to pass')


def repository_producers(modules):
    return {str(Path(m.__file__).resolve()):sha(m.__file__) for m in modules
            if getattr(m,'__file__',None) and str(m.__file__).endswith('.py')
            and Path(m.__file__).is_file() and Path(m.__file__).resolve().is_relative_to(ROOT.parent)}


def run(output,*,resume=False):
    output=Path(output).resolve()
    if output.exists() and any(output.iterdir()) and not resume:
        raise FileExistsError('Choose a new empty pilot output or explicitly resume matching checkpoints')
    if (output/'summary.json').exists():raise FileExistsError('Completed pilot is immutable')
    output.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter()
    noise_audit=audit_lookup_noise(LOOKUP)
    original=read(LOOKUP/'execution_physical_protocol.json')
    setup=load_config(ROOT/'configs/channel/optimized_physical_setup.yaml')
    compatible=compare_lookup_setup(setup,original)
    if compatible['physical_mismatches'] or compatible['noise_mismatches']!=['channel_excess_noise_snu']:
        raise ValueError('Pilot must isolate channel noise only with the author-confirmed optics')
    points=select_positions(read_rows(LOOKUP/'skr_map.csv'))
    config=dict(scope='EXPLICIT_USER_AUTHORIZED_PHASE5C_FIVE_POSITION_DIAGNOSTIC_ONLY',
        author_target_noise=.0136,historical_noise=.0186,detector_noise=.005,physical=original['physical'],
        points=points,candidates=212,MB_candidates=179,Uniform_candidates=33,selection='per-family signed raw K argmax; first catalog tie retained',
        effective_protocols={n:effective_protocol(original,x) for n,x in [('reproduction',.0186),('target',.0136)]},
        atol=ATOL,rtol=0.,random_seed=None,randomness='None: deterministic source vectors, analytic moments, GH64/128 and native multiprecision',
        physical_context_lineage='Fresh original validated physical contexts; use only noise-independent m1,mh,M0 for active effective noise',
        target_authority='Current explicit Phase5C task, not the inherited historical experiment-spec authorization',
        paper_mode='NOT_RUN',full_regeneration_authorized=False,cloud='NOT_USED',finite_size='NOT_USED',
        source_evidence_promoted=False,security_valid=False)
    config_digest=hashlib.sha256(json.dumps(config,sort_keys=True,allow_nan=False).encode()).hexdigest()
    if (output/'config.json').exists():
        if read(output/'config.json')!=config:raise ValueError('Resume configuration mismatch')
    else:(output/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    wrapper_sha=sha(__file__)
    spec=importlib.util.spec_from_file_location('_phase5c_original_producer',LOOKUP/'run.py')
    native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    old=native.helpers()
    def write(path,value):
        path=Path(path)
        if path.exists():raise FileExistsError('Refuse to overwrite checkpoint: '+str(path))
        path.write_text(json.dumps(old.clean(value),indent=2,allow_nan=False),encoding='utf-8')
    pool=[];input_hashes=dict(noise_audit['verified_inputs_and_producers'])
    for row in read_rows(LOOKUP/'source_pool.csv'):
        path=PARENT/row['source_path']
        if sha(path)!=row['source_sha256']:raise ValueError('Historical source payload hash mismatch')
        input_hashes[str(path)]=sha(path)
        source=dict(row,VA=float.fromhex(row['VA_hex']),nu_raw=float.fromhex(row['nu_raw_hex']),
                    C=float.fromhex(row['C_hex']),w=float.fromhex(row['w_hex']),classification=row['source_evidence_class'])
        old.historical.verify_source_payload(read(path),json.loads(row['source_settings_json']))
        source=old.historical.with_ensemble(source)
        if old.historical.input_digests(source)!=json.loads(row['input_digests_json']):raise ValueError('Native source vector identity mismatch')
        pool.append(source)
    if len(pool)!=212 or sum(s['family']=='MB' for s in pool)!=179:raise ValueError('Pilot catalog changed')
    for path in (LOOKUP/'source_pool.csv',ROOT/'configs/channel/optimized_physical_setup.yaml',Path(__file__)):
        input_hashes[str(path)]=sha(path)
    # Bind all loaded repository modules, while preserving original native guards.
    producers=repository_producers(list(sys.modules.values()))
    manifest=dict(config_sha256=config_digest,wrapper_sha256=wrapper_sha,inputs=input_hashes,producers=producers,
                  python=platform.python_version(),python_executable=sys.executable,platform=platform.platform(),
                  roster=[{k:s[k] for k in ('family','ensemble_hash','VA','nu_raw','C_hex','w_hex','source_path','source_sha256','classification')} for s in pool])
    if (output/'input_manifest.json').exists():
        if read(output/'input_manifest.json')!=manifest:raise ValueError('Resume input/producer identity mismatch')
    else:write(output/'input_manifest.json',manifest)
    input_identity=sha(output/'input_manifest.json')
    preparation_s=time.perf_counter()-started
    checks=[];results={};actual_calls=0
    for stage in ('reproduction','target'):
        if stage=='target':require_reproduction_pass(checks)
        stage_dir=output/stage;stage_dir.mkdir(exist_ok=True)
        stage_results=[]
        for point in points:
            checkpoint=stage_dir/(point['point_id']+'.json')
            if checkpoint.exists():
                record=read(checkpoint)
                if record['input_manifest_sha256']!=input_identity or record['point']!=point:
                    raise ValueError('Checkpoint context identity mismatch')
                if read(checkpoint.with_suffix('.seal.json'))['sha256']!=sha(checkpoint):raise ValueError('Checkpoint seal mismatch')
            else:
                began=time.perf_counter()
                # Original validator is used unchanged with its original noise.
                context=old.canonical.channel_context(point['zenith_deg'],original)
                context_s=time.perf_counter()-began
                candidates=[];evaluation_began=time.perf_counter()
                for source in pool:
                    value=old.evaluator.evaluate(source,context,config['effective_protocols'][stage])
                    actual_calls+=1
                    candidates.append(dict(family=source['family'],ensemble_hash=source['ensemble_hash'],VA=source['VA'],nu_raw=source['nu_raw'],
                        source_path=source['source_path'],source_sha256=source['source_sha256'],source_evidence_class=source['classification'],
                        **{k:v for k,v in value.items() if k!='decimal'}))
                winners={family:max((c for c in candidates if c['family']==family),key=lambda c:c['K_raw']) for family in ('MB','Uniform')}
                record=dict(stage=stage,point=point,input_manifest_sha256=input_identity,trial_config_sha256=config_digest,
                    physical_context_original_protocol_sha256=sha(LOOKUP/'execution_physical_protocol.json'),active_effective_protocol=config['effective_protocols'][stage],
                    context=context,candidates=candidates,winners=winners,context_s=context_s,
                    evaluator_s=time.perf_counter()-evaluation_began,total_point_s=time.perf_counter()-began,
                    fresh_candidate_calls=len(candidates),seed=None,security_valid=False)
                write(checkpoint,record);write(checkpoint.with_suffix('.seal.json'),dict(sha256=sha(checkpoint)))
            stage_results.append(record)
            if stage=='reproduction':
                tag=hashlib.sha256(float(point['zenith_deg']).hex().encode()).hexdigest()[:18]
                historical=read_rows(LOOKUP/'contexts'/f'{tag}_candidates.csv')
                by_source={r['ensemble_hash']:r for r in historical}
                comparisons=[]
                for candidate in record['candidates']:
                    expected=dict(by_source[candidate['ensemble_hash']])
                    for k in ('VA','nu_raw'):expected[k]=float(expected[k])
                    comparisons.append(compare_candidate(candidate,expected))
                old_context=read(LOOKUP/'contexts'/f'{tag}.json')
                winner_match=all(record['winners'][f]['ensemble_hash']==old_context['winners'][f]['ensemble_hash'] for f in ('MB','Uniform'))
                checks.append(dict(point_id=point['point_id'],passed=bool(all(c['passed'] for c in comparisons) and winner_match),
                    winner_identity_matches=winner_match,max_deviation={k:max(c['absolute_deviation'][k] for c in comparisons) for k in METRICS}))
            print(stage,point['point_id'],point['x_m'],point['y_m'],'MB_K',record['winners']['MB']['K_raw'],flush=True)
        results[stage]=stage_results
        if stage=='reproduction':
            write(output/'reproduction_checks.json',checks) if not (output/'reproduction_checks.json').exists() else None
            require_reproduction_pass(checks)
    for name,h in {**input_hashes,**producers}.items():
        if sha(name)!=h:raise ValueError('Input/producer changed during execution: '+name)
    comparisons=[]
    for a,b in zip(results['reproduction'],results['target']):
        x,y=a['winners']['MB'],b['winners']['MB']
        comparisons.append(dict(point=a['point'],historical=x,target=y,
            delta={k:y[k]-x[k] for k in METRICS},selection_changed=x['ensemble_hash']!=y['ensemble_hash']))
    summary=dict(status='CURRENTLY_VERIFIED_PASS',scope=config['scope'],config_sha256=config_digest,input_manifest_sha256=input_identity,
        reproduction_checks=checks,comparisons=comparisons,preparation_s=preparation_s,elapsed_this_process_s=time.perf_counter()-started,
        fresh_calls_this_process=actual_calls,total_checkpoint_candidate_calls=2120,
        evaluator_s={k:sum(r['evaluator_s'] for r in v) for k,v in results.items()},
        context_s={k:sum(r['context_s'] for r in v) for k,v in results.items()},
        paper_mode='NOT_RUN',security_valid=False,paper_admissible=False,evidence_labels_promoted=False)
    write(output/'summary.json',summary)
    seals={str(f.relative_to(output)):sha(f) for f in sorted(output.rglob('*')) if f.is_file()}
    write(output/'output_manifest.json',seals)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    result=run(args.output,resume=args.resume)
    print(json.dumps({k:result[k] for k in ('status','fresh_calls_this_process','elapsed_this_process_s')},indent=2))


if __name__=='__main__':main()
