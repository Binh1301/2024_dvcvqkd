"""Read-only receipt checks; no evaluator imports and no numerical rerun."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
LEDGERS=['docs/EVIDENCE.md','docs/DECISION_LOG.md','docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory():return {p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='final_receipt.json' and '__pycache__' not in p.parts}


def main():
    start=read(OUT/'startup_manifest.json');allowed={f'paper_uav_hap_cvqkd/{p}' for p in LEDGERS}
    changed=[p for p,h in start['protected'].items() if p not in allowed and sha(ROOT.parent/p)!=h]
    assert not changed,changed
    assert all(sha(ROOT/p)==h for p,h in start['imported_model_sha256'].items())
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==start['HEAD']
    protocol=read(OUT/'protocol.json')
    assert sha(OUT/'parameter_adapter.py')==protocol['adapter_sha256'] and sha(OUT/'run_study.py')==protocol['producer_sha256']
    for p in OUT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'))
    validation=read(OUT/'validation.json');assert validation['status']=='CURRENTLY_VERIFIED_PASS'
    assert all(c['status']=='CURRENTLY_VERIFIED_PASS' for c in validation['checks'])
    selection=read(OUT/'selection.json');selected=selection['recommendations'];assert len(selected)==3
    assert all(r['D_r']<=.45 and r['epsilon_det'] in [.005,.0135] and r['eta_det'] in [.8,.85,.9,.95]
        and r['detector_security']=='untrusted' and r['receiver']=='homodyne_1D' and r['K_raw']>0 and not r['security_valid'] for r in selected)
    with (OUT/'selected_designs.csv').open() as f:table=list(csv.DictReader(f))
    for r,b in zip(selected,table):
        assert r['design']==b['design'] and r['ensemble_hash']==b['ensemble_hash'] and r['K_raw']==float(b['K_raw'])
    assert read(OUT/'regression.json')['status']=='CURRENTLY_VERIFIED_PASS'
    assert read(OUT/'source_coverage.json')['status']=='CURRENTLY_VERIFIED_PASS'
    assert read(OUT/'figure_validation.json')['status']=='CURRENTLY_VERIFIED_PASS'
    pdfs=list((OUT/'figures').glob('*.pdf'));assert len(pdfs)==len(list((OUT/'figures').glob('*.png')))==9
    for p in pdfs:
        data=p.read_bytes();assert data.startswith(b'%PDF-') and len(re.findall(rb'/Type /Page\b',data))==1 and b'/Subtype /Image' not in data
    hardware=read(OUT/'hardware_evidence.json')
    assert not hardware['aggregate_power_calculated'] and not hardware['throughput_energy_sortie_calculated']
    assert read(OUT/'completion_checks.json')['status']=='CURRENTLY_VERIFIED_PASS'
    files=inventory();path=OUT/'final_receipt.json'
    if '--seal' in sys.argv:
        if path.exists():raise FileExistsError('Preserve sealed receipt')
        payload=dict(status='CURRENTLY_VERIFIED_PASS',scope='PARAMETER_ONLY_SWAP_DIAGNOSTIC',HEAD=start['HEAD'],request_sha256=start['request_sha256'],
            artifact_sha256=files,ledger_sha256={p:sha(ROOT/p) for p in LEDGERS},imported_model_sha256=start['imported_model_sha256'],
            protected_file_count=len(start['protected']),scoped_checks=len(validation['checks']),logged_evaluations=validation['rows'],
            new_evaluations=validation['new_evaluations'],reused_evaluations=validation['reused_evaluations'],
            minimum_validated_candidate_m=selection['minimum_evaluated_positive_m'],primary_minimum_sampled_positive_m=selection['primary_minimum_sampled_positive_m'],
            balanced_objective_met=selection['balanced_objective_met'],moderate_PAT_positive_found=selection['moderate_PAT_positive_found'],
            distinct_recommended_physical_points=selection['distinct_recommended_physical_points'],
            designs=[{k:r[k] for k in ['design','D_r','zenith_deg','L_km','divergence_urad','jitter_urad','sigma_h_m','eta_det','epsilon_det','VA','nu_raw','I_AB','beta_I_AB','chi_BE','K_raw','joint10_K','joint20_K','robustness_class','ensemble_hash']} for r in selected],
            vector_figures=9,png_dpi=350,security_valid=False,hardware_validated=False,global_minimum_certified=False,
            total_payload_mass_power_f_rep_energy_sortie='UNKNOWN_NOT_FABRICATED',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
            historical_model_security_config_cache_frozen_changes=False,training_final_test_heldout_publication_new_AP='NOT_RUN')
        path.write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    saved=read(path);assert files==saved['artifact_sha256']
    assert all(sha(ROOT/p)==h for p,h in saved['ledger_sha256'].items())
    print(json.dumps(dict(status=saved['status'],artifacts=len(files),protected_files=len(start['protected']),checks=saved['scoped_checks'],
        rows=saved['logged_evaluations'],reused=saved['reused_evaluations'],minimum_validated_D_m=saved['minimum_validated_candidate_m'],
        receipt_sha256=sha(path),numerical_rerun=False)))


if __name__=='__main__':main()
