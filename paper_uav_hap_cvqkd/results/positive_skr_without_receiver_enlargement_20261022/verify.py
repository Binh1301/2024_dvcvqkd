"""Verify sealed saved artifacts without calling any scientific evaluator."""
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
def artifacts():return {p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='final_receipt.json' and '__pycache__' not in p.parts}


def main():
    start=read(OUT/'startup_manifest.json');allowed={f'paper_uav_hap_cvqkd/{p}' for p in LEDGERS}
    changed=[p for p,h in start['protected'].items() if p not in allowed and sha(ROOT.parent/p)!=h]
    assert not changed,changed
    assert sha(OUT/'numeric.py')==start['numeric_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==start['HEAD']
    validation=read(OUT/'validation.json');assert validation['status']=='CURRENTLY_VERIFIED_PASS'
    assert all(c['status']=='CURRENTLY_VERIFIED_PASS' for c in validation['checks'])
    selected=read(OUT/'selection.json')['recommendations'];assert len(selected)==3
    assert all(r['D_r']==.08 and r['detector_security']=='untrusted' and not r['security_valid'] for r in selected)
    assert all(r['h_hap_km']==20 and r['h_uav_km']==1 for r in selected)
    assert all(0<r['eta_det']<1 and r['epsilon_det']>0 for r in selected)
    with (OUT/'table_2_positive_8cm.csv').open() as f:B=list(csv.DictReader(f))
    extra=read(OUT/'necessity.json')['additional_positive_original_geometry']
    for r in selected+extra:
        if r['K_raw']>0:
            b=next(x for x in B if x['configuration']==r['configuration'])
            assert float(b['K_raw'])==r['K_raw'] and b['ensemble_hash']==r['ensemble_hash']
    assert abs(float(read(OUT/'regression.json')['K_raw'])-(-.0587243146799775588))<1e-15
    assert read(OUT/'figure_validation.json')['status']=='CURRENTLY_VERIFIED_PASS'
    pdfs=list((OUT/'figures').glob('*.pdf'));assert len(pdfs)==len(list((OUT/'figures').glob('*.png')))==8
    for p in pdfs:
        data=p.read_bytes();assert data.startswith(b'%PDF-') and len(re.findall(rb'/Type /Page\b',data))==1 and b'/Subtype /Image' not in data
    files=artifacts();path=OUT/'final_receipt.json'
    if '--seal' in sys.argv:
        if path.exists():raise FileExistsError('Preserve sealed receipt')
        payload=dict(status='CURRENTLY_VERIFIED_PASS_NUMERICAL_DIAGNOSTIC_ONLY',HEAD=start['HEAD'],request_sha256=start['request_sha256'],
            artifact_sha256=files,ledger_sha256={p:sha(ROOT/p) for p in LEDGERS},protected_file_count=len(start['protected']),
            scoped_checks=len(validation['checks']),logged_evaluations=validation['rows'],new_evaluations=validation['new_evaluations'],reused_evaluations=validation['reused'],
            receiver_fixed_m=.08,original_detector_positive=selected[0]['K_raw']>0,positive_recommendations=sum(r['K_raw']>0 for r in selected),
            additional_positive_original_geometry=read(OUT/'necessity.json')['additional_positive_original_geometry'],
            recommendations=[{k:r[k] for k in ['configuration','h_hap_km','h_uav_km','zenith_deg','divergence_urad','jitter_urad','sigma_h_m','eta_det','epsilon_det','VA','nu_raw','K_raw','ensemble_hash']} for r in selected],
            user_weather_pairs=read(OUT/'weather_input.json')['pairs'],vertical_extinction_profile='NOT_PROVIDED; changed heights sensitivity only',
            vector_figures=8,png_dpi=350,security_valid=False,hardware_validated=False,lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
            production_source_security_config_cache_frozen_changes=False,new_AP_training_final_test_heldout='NOT_RUN')
        path.write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    saved=read(path);assert files==saved['artifact_sha256']
    assert all(sha(ROOT/p)==h for p,h in saved['ledger_sha256'].items())
    print(json.dumps(dict(status=saved['status'],artifacts=len(files),protected_files=len(start['protected']),checks=saved['scoped_checks'],
        logged_evaluations=saved['logged_evaluations'],reused=saved['reused_evaluations'],receipt_sha256=sha(path),numerical_rerun=False)))


if __name__=='__main__':main()
