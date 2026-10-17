"""Integrity/acceptance bookkeeping; retains all strict numerical failures."""
import ast,base64,difflib,hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    start=read(OUT/'startup_manifest.json');summary=read(OUT/'audit_summary.json')
    raw=read(OUT/'independent_geometry_audit.json');runtime=read(OUT/'runtime_probe.json');diagnosis=read(OUT/'quadrature_precision_diagnosis.json')
    changed=[p for p,h in start['protected_hashes'].items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    assert not changed,changed
    assert raw['runtime_probe_sha256']==sha(OUT/'runtime_probe.json')
    assert runtime['probe_script_sha256']==sha(ROOT/'scripts/probe_full_geometry_runtime.py')
    assert raw['independent_quantum_helper_sha256']==sha(ROOT/'scripts/audit_negative_skr_independent.py')
    assert len(raw['checks'])==94 and len(raw['failures'])==5
    assert diagnosis['original_failures']==raw['failures'] and diagnosis['original_strict_checks_preserved']
    assert diagnosis['status']=='CURRENTLY_VERIFIED_PASS' and len(diagnosis['checks'])==18
    assert runtime['fresh_A_matches_saved_state'] and runtime['new_SKR_calls']==8
    assert all(v==0 for row in runtime['reference_old_new_residual'].values() for v in row.values())
    for p,h in runtime['raw_runtime_source_fingerprints'].items():assert sha(ROOT/p)==h,p
    report=ROOT/'docs/FULL_GEOMETRY_FADING_SKR_AUDIT_VI.md';text=report.read_text(encoding='utf-8')
    assert not [c for c in text if ord(c)<32 and c not in '\r\n\t']
    assert len(re.findall(r'^## [A-I]\. ',text,re.M))==9
    assert text.count('\\[')==text.count('\\]')
    for block in re.findall(r'\\\[(.*?)\\\]',text,re.S):assert block.count('{')==block.count('}')
    assert sha(report)==sha(OUT/'FULL_GEOMETRY_FADING_SKR_AUDIT_VI.md')
    for name in ('scripts/probe_full_geometry_runtime.py','scripts/audit_full_geometry_fading_skr.py'):
        ast.parse((ROOT/name).read_text(encoding='utf-8'))
    artifacts=('startup_manifest.json','runtime_probe.json','independent_geometry_audit.json','quadrature_precision_diagnosis.json',
               'audit_summary.json','high_precision_common_geometry.json','high_precision_SKR.json','moments_closed_vs_quadrature.csv',
               'runtime_parameters.csv','configuration_sensitivity.csv','SKR_entropy_decomposition.csv','FULL_GEOMETRY_FADING_SKR_AUDIT_VI.md',
               'write_full_report.py','diagnose_quadrature_precision.py')
    receipt=dict(status='CURRENTLY_VERIFIED_PASS',verification_scope='Provenance/report/coverage verified; not an all-numerical-checks PASS',
                 checked_utc=datetime.now(timezone.utc).isoformat(),verdicts=summary['verdicts'],strict_numerical_checks=summary['strict_checks'],
                 supplemental_diagnosis=summary['downstream_diagnosis'],production_SKRs_recomputed=8,independent_geometry_to_SKR_cases=8,
                 physical_entropy_bound_cases=8,physical_entropy_bound_failures=0,protected_files=len(start['protected_hashes']),protected_changes=changed,
                 production_files_edited=False,source_moment_builds=0,full_catalog_or_missions_run=False,training_or_test_access=False,
                 frozen_model_changed=False,frozen_historical_discrepancy=True,lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
                 Objective_C='USER_STOPPED',commit_or_push=False,publication_evaluation=False,external_edits=False,
                 producer_sha256={p:sha(ROOT/p) for p in ('scripts/probe_full_geometry_runtime.py','scripts/audit_full_geometry_fading_skr.py')},
                 artifact_sha256={p:sha(OUT/p) for p in artifacts},canonical_report_sha256=sha(report),report_QA=dict(sections=9,math_delimiters_balanced=True,control_characters=False))
    (OUT/'validation_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('artifact_sha256','producer_sha256')},indent=2))


if __name__=='__main__':main()
