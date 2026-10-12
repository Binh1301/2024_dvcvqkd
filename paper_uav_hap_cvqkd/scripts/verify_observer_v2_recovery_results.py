"""Read-only scientific/source-cache provenance plus saved recovery validation."""
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.exact_cache_provenance import verify_source_payload,json_hash,source_hashes
from scripts.diagnose_theta10_D55_source_bottlenecks import digest,read,rows
from scripts.overnight_source_observer import atomic_json

BASE=ROOT/'results/theta10_D55_ao_numerical_optimum_validation'
OUT=BASE/'observer_v2_recovery'
OLD=BASE/'overnight_ao_run'


def main():
    assert not (OUT/'final_saved_artifact_verification.json').exists(),'Preserve completed verification'
    expected=read(OUT/'protected_input_manifest.json')
    assert all(digest(ROOT/n)==h for n,h in expected.items())
    settings={'density_eigenvalue_tolerance':1e-12,'physicality_tolerance':1e-10,'precision_ladder':[1050,1250,1450]}
    paths={}
    for p in (ROOT/'results').glob('**/exact_source_cache/*.json'):
        paths.setdefault(p.stem,[]).append(p)
    verified=[]
    for r in rows(OLD/'expanded_source_catalog.csv'):
        path=paths[r['source_cache_key']][0];p=read(path);result=verify_source_payload(p,settings)
        assert p['ensemble_hash']==r['ensemble_hash']
        assert (p['nu_mb_raw_hex'],p['V_A_hex'])==(float(r['nu_raw']).hex(),float(r['V_A']).hex())
        assert all(float(p[k])==float(r[k]) for k in ('C','w'))
        verified.append({'source_cache_key':r['source_cache_key'],'path':path.relative_to(ROOT).as_posix(),
           'sha256':digest(path),'verification':result['status'],'identity':result})
    assert len(verified)==147
    atomic_json(OUT/'source_provenance_validation.json',verified)
    checkpoint=read(OLD/'objective_checkpoint.json');matrix=[]
    for distance,entry in checkpoint.items():
        identity=entry['identity'];body=identity['identity']
        assert json_hash(body)==identity['sha256']
        assert (body['security'],body['MI'],body['quadrature_order'],body['beta'],body['epsilon'])==('direct_Z_minus','deterministic_heterodyne_product',8,.95,.0186)
        for name,expected_hash in body['scientific_implementation'].items():
            assert source_hashes((ROOT/name).read_bytes())['canonical_lf_sha256']==expected_hash
        assert len(entry['rows'])==147
        for r in entry['rows']:
            assert float(r['beta_I_AB'])==.95*float(r['I_AB'])
            assert float(r['SKR'])==float(r['beta_I_AB'])-float(r['chi_BE'])
        matrix.append({'L_km':float(distance),'rows':147,'identity_sha256':identity['sha256'],'verified':True})
    assert len(matrix)==26
    required=['observer_v2_code_audit.md','mpmath_context_validation.md','profiling_lifecycle_tests.csv',
        'dummy_worker_integration_results.csv','supervisor_safety_tests.md','instrumentation_overhead.csv',
        'protected_hash_audit.csv','ap_readiness_checklist.md','probe_A_execution_plan.md',
        'conditional_P1_P2_continuation_plan.md','observer_v2_recovery_report.md','observer_v2_recovery_report.json']
    assert all((OUT/n).is_file() for n in required)
    done=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);assert done.returncode==0
    command="@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -match '--approved-ap|--probe|--profile-worker|full_support_c4_worker\\.py|observer_v2_recovery_entry\\.py.*--dummy-mode'} | Select-Object ProcessId) | ConvertTo-Json -Compress"
    p=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,check=True)
    assert p.stdout.strip() in ('','[]','null')
    report=read(OUT/'observer_v2_recovery_report.json')
    output={'status':'CURRENTLY_VERIFIED_PASS_FOR_SAVED_RECOVERY_AND_SOURCE_PROVENANCE',
        'utc':datetime.now(timezone.utc).isoformat(),'readiness':report['status'],
        'protected_hashes_unchanged':len(expected),'source_provenance_verified':147,
        'objective_identity_matrices_verified':26,'objective_rows_checked':3822,'objective_matrices':matrix,
        'requested_outputs_present':12,'dummy_native_cases_passed':sum(r['PASS'] for r in report['native_tests']),
        'regression_tests':report['test_count'],'no_source_or_dummy_orphan':True,'git_diff_check':'CURRENTLY_VERIFIED_PASS',
        'AP_workers_launched':0,'fresh_source_moments':0,'fresh_SKR_evaluations':0,'fresh_AO_invocations':0,
        'fresh_explicit_approval_required':True,'recovery_report_sha256':digest(OUT/'observer_v2_recovery_report.json')}
    atomic_json(OUT/'final_saved_artifact_verification.json',output)
    print(json.dumps({k:output[k] for k in ('status','readiness','protected_hashes_unchanged',
                'source_provenance_verified','objective_rows_checked','requested_outputs_present')},indent=2))


if __name__=='__main__':main()
