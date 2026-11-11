"""Independent arithmetic/hash checks; never runs an optimizer or quantum producer."""
from pathlib import Path
import hashlib
import json
import csv
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/phase6a_baseline_20261109_rss_retry_20261110'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    manifest=read(OUT/'output_manifest.json')
    for name,digest in manifest.items():assert sha(OUT/name)==digest,name
    inputs=read(OUT/'input_manifest.json')
    for name,digest in inputs['inputs'].items():assert sha(name)==digest,name
    for name,digest in inputs['producers'].items():
        executed=(ROOT/'docs/phase6a_validation/executed_runner_rss_retry.py') if name.replace('\\','/').endswith('/phase6a_experiment.py') else ROOT/name
        assert sha(executed)==digest,name
    before=read(ROOT/'docs/phase6a_validation/protected_before.json')
    changed=[p for p,h in before.items() if not Path(p).is_file() or sha(p)!=h]
    assert not changed,changed
    report=read(OUT/'results.json');preflight=read(OUT/'preflight.json');config=read(OUT/'config.json')
    initial=ROOT/'results/phase6a_baseline_20261109'
    first_manifest=read(initial/'output_manifest.json')
    for name,digest in first_manifest.items():assert sha(initial/name)==digest,name
    first_inputs=read(initial/'input_manifest.json')
    for name,digest in first_inputs['inputs'].items():assert sha(name)==digest,name
    for name,digest in first_inputs['producers'].items():
        executed=(ROOT/'docs/phase6a_validation/executed_runner_with_tracemalloc.py') if name.replace('\\','/').endswith('/phase6a_experiment.py') else ROOT/name
        assert sha(executed)==digest,name
    first=read(initial/'results.json')
    assert first['runs'][-1]['status']=='FAILED_COMPUTATIONAL_LIMIT'
    assert first['runs'][-1]['solutions']=={}
    assert first['reduced_benchmark']['workload']=='REDUCED_BENCHMARK_ONLY'
    assert first['reduced_benchmark']['not_substituted_into_full_comparison'] is True
    assert report['config_sha256']==first['config_sha256']
    assert report['shared_scenario_sha256']==first['shared_scenario_sha256']
    for old,new in zip(first['runs'][:3],report['runs'][:3]):assert old['solutions']==new['solutions']
    with np.load(initial/'scenario.npz',allow_pickle=False) as old,np.load(OUT/'scenario.npz',allow_pickle=False) as new:
        for name in old.files:np.testing.assert_array_equal(old[name],new[name])
    assert preflight['status']=='CURRENTLY_VERIFIED_PASS'
    assert report['paper_mode']=='NOT_RUN' and report['paper_admissible'] is False
    assert report['source_evidence_promoted'] is False
    with np.load(OUT/'scenario.npz',allow_pickle=False) as saved:
        s={k:saved[k].copy() for k in saved.files}
    q,r,z,cost=s['positions'],s['rates'],s['z'],s['costs']
    assert q.shape==(121,2) and r.shape==(121,) and z.shape==(100,121)
    assert np.isin(z,[0,1]).all() and np.isfinite(r).all()
    for i in range(121):
        for j in range(121):
            distance=np.abs(q[i]-q[j])
            assert np.isfinite(cost[i,j])==(sum(distance) in (0,200))
    with np.load(OUT/'cloud_realization.npz',allow_pickle=False) as cloud:
        assert cloud['seed'].item()==20261108 and len(cloud['amplitude'])==400
        assert cloud['threshold_mg_m3'].item()==np.percentile(cloud['field'],90,method='linear')==15
    old=ROOT/'results/phase5d_full_target_radial_2proc_PHASE5E_20261108'
    with (old/'skr_map.csv').open(encoding='utf-8',newline='') as f:
        lookup={(float(row['x_m']),float(row['y_m'])):float(row['MB_K_raw']) for row in csv.DictReader(f)}
    np.testing.assert_array_equal(r,[lookup[tuple(pos)] for pos in q])
    selected=0;slot_rows=0;failed=[]
    for run in report['runs']:
        assert run['shared_scenario_sha256']==report['shared_scenario_sha256']
        folder=OUT/run['method'].lower().replace(' ','_')
        if run['status']!='FEASIBLE':
            assert not run['solutions'];failed.append(run['method']);continue
        assert run['runtime_s']>0 and run['sampled_peak_rss_bytes']>0
        if run['method']=='Pareto DP':
            assert run['classification']=='exact-on-graph'
            assert run['diagnostics']['label_cap'] is None
            assert run['diagnostics']['heuristic_discarded_labels']==0
        for objective,sol in run['solutions'].items():
            path=sol['path_indices'];assert path[0]==s['initial'].item()
            energy=0.;a=0.;u=0
            for k,(i,j) in enumerate(zip(path,path[1:]),1):
                assert np.isfinite(cost[i,j])
                assert np.linalg.norm(q[i]-q[j])/s['dt']<=30
                energy+=float(cost[i,j]);a+=int(z[k-1,j])*float(r[j]);u+=int(z[k-1,j])
                n=s['m0'].item()*u;raw=s['m0'].item()*a
                penalty=7*np.sqrt(n*np.log2(2/s['epsilon'].item())) if n else 0
                key=max(0,raw-penalty)
                row=sol['series'][k-1]
                for actual,expected in ((row['valid_signals'],n),(row['asymptotic_bits'],raw),
                                        (row['penalty_bits'],penalty),(row['key_bits'],key),(row['energy_j'],energy)):
                    assert np.isclose(actual,expected,rtol=1e-12,atol=1e-8),(run['method'],objective,k)
                slot_rows+=1
            assert energy<=s['budget'].item()
            assert sol['mission_time_s']==sol['K']*s['dt'].item()
            metric=key/sol['mission_time_s'] if objective=='P1' else key
            assert np.isclose(sol['objective_value'],metric,rtol=1e-12,atol=1e-8)
            assert run['method']!='Stationary' or len(set(path))==1
            with (folder/(objective+'_trajectory.csv')).open(encoding='utf-8',newline='') as f:
                rows=list(csv.DictReader(f));assert len(rows)==len(path)
                assert float(rows[0]['time_s'])==0
                for row,saved in zip(rows[1:],sol['series']):
                    j=saved['waypoint'];k=saved['k']
                    assert float(row['raw_clear_skr_bits_use'])==r[j]
                    assert float(row['effective_skr_bits_scheduled_use'])==z[k-1,j]*r[j]
                    assert float(row['raw_key_contribution_bits'])==s['m0']*z[k-1,j]*r[j]
                    assert float(row['emitted_uses'])==k*10*100000
                    assert float(row['allocated_signals_before_cloud'])==k*800000
            selected+=1
    assert selected==report['completed_algorithm_objective_pairs']
    for obj in ('P1','P2'):
        with (OUT/('comparison_'+obj+'.csv')).open(encoding='utf-8',newline='') as f:
            rows=list(csv.DictReader(f));assert len(rows)==4
            assert {row['method'] for row in rows}=={run['method'] for run in report['runs']}
    summary=dict(status='CURRENTLY_VERIFIED_PASS',core_output_hashes=len(manifest),input_hashes=len(inputs['inputs']),
        producer_hashes=len(inputs['producers']),protected_files=len(before),changed_existing_files=changed,
        selected_full_workload_solutions=selected,independently_checked_prefix_rows=slot_rows,failed_full_methods=failed,
        initial_failed_attempt_seals=len(first_manifest),initial_executed_source_archive_verified=True,
        retry_scientific_scenario_unchanged=True,three_baseline_solution_dicts_exactly_reproduced=True,
        paper_mode='NOT_RUN',paper_admissible=False,security_evidence_promoted=False,
        verification_scope='Hash seals, graph/cardinal/speed, source rates, signal accounting, independent prefix arithmetic and CSV consistency; no solver rerun')
    (ROOT/'docs/phase6a_validation/artifact_verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
