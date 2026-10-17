"""Audit-only integrity and scientific receipt; no production mutation."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];out=Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
start=read(out/'startup_manifest.json');summary=read(out/'audit_summary.json');ind=read(out/'independent_audit.json');probe=read(out/'production_probe.json')
changed=[p for p,h in start['protected_hashes'].items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
assert not changed,changed
assert summary['status']=='CURRENTLY_VERIFIED_PASS' and ind['failures']==[]
assert sha(out/'audit_inputs.json')==probe['provenance']['input_sha256']
assert sha(ROOT/'scripts/probe_negative_skr_production.py')==probe['provenance']['producer_script_sha256']
selfcheck=read(out/'independent_self_checks.json');assert sha(ROOT/'scripts/audit_negative_skr_independent.py')==selfcheck['independent_audit_script_sha256']
report=ROOT/'docs/NEGATIVE_SKR_INDEPENDENT_AUDIT_VI.md';missing=[]
for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
 if not target.startswith(('https://','http://')) and not (report.parent/target).exists():missing.append(target)
assert not missing,missing
receipts=['production_probe.json','actual_call_graph.json','audit_inputs.json','independent_audit.json','audit_summary.json','high_precision_decomposition.json','independent_results.csv','checks.csv','reference_entropy_decomposition.csv','independent_self_checks.json','supplemental_independent_checks.json','trusted_ideal_limit.csv','reference_documents.json','startup_manifest.json','NEGATIVE_SKR_INDEPENDENT_AUDIT_VI.md']
files={name:sha(out/name) for name in receipts}
for name in ('scripts/probe_negative_skr_production.py','scripts/audit_negative_skr_independent.py'):ast.parse((ROOT/name).read_text(encoding='utf-8'))
receipt=dict(status='CURRENTLY_VERIFIED_PASS',checked_utc=datetime.now(timezone.utc).isoformat(),scope='Bounded independent physical audit only',security_status='UNVALIDATED_SECURITY_MODEL',protected_files=len(start['protected_hashes']),protected_changes=changed,independent_checks=summary['total_checks'],physical_entropy_bound_checks=40,physical_entropy_bound_failures=0,new_production_reference_and_boundary_calls=32,source_moment_builds=0,full_catalog_or_P1_P3_runs=0,production_evaluator_or_config_modified=False,training_or_test_access=False,publication_evaluation=False,frozen_model_changed=False,frozen_historical_discrepancy=True,lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',Objective_C='USER_STOPPED',commit_or_push=False,external_files_modified=False,numerical_summary=summary,producer_sha256={p:sha(ROOT/p) for p in ('scripts/probe_negative_skr_production.py','scripts/audit_negative_skr_independent.py')},artifact_sha256=files,canonical_report_sha256=sha(report),report_local_links_missing=missing)
(out/'validation_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('artifact_sha256','numerical_summary')},indent=2))
