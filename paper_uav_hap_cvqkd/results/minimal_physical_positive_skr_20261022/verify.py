"""Hash-bound, read-only saved-artifact verification; --seal creates the receipt once."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
LEDGERS=['docs/EVIDENCE.md','docs/DECISION_LOG.md','docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md']


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def artifacts():return {p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='final_receipt.json' and '__pycache__' not in p.parts}


def main():
    start=read(OUT/'startup_manifest.json');receipt=OUT/'final_receipt.json'
    allowed={f'paper_uav_hap_cvqkd/{p}' for p in LEDGERS}
    changed=[p for p,h in start['protected'].items() if p not in allowed and sha(ROOT.parent/p)!=h]
    assert not changed,changed
    assert sha(OUT/'numeric.py')==start['numeric_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==start['HEAD']
    assert read(OUT/'checks.json')['status']=='CURRENTLY_VERIFIED_PASS'
    assert all(c['status']=='CURRENTLY_VERIFIED_PASS' for c in read(OUT/'checks.json')['checks'])
    assert read(OUT/'figure_validation.json')['status']=='CURRENTLY_VERIFIED_PASS'
    selected=read(OUT/'final_selection.json')['recommendations']
    assert len(selected)==3 and all(r['K_raw']>1e-4 and not r['security_valid'] for r in selected)
    with (OUT/'table_B_positive_candidates.csv').open(encoding='utf-8') as f:
        B=list(csv.DictReader(f))
    for r in selected:
        b=next(b for b in B if b['recommendation']==r['recommendation'])
        assert b['ensemble_hash']==r['ensemble_hash'] and float(b['K_raw'])==r['K_raw']
    with (OUT/'worst_robustness_fine.csv').open() as f:
        worst=list(csv.DictReader(f))
    assert float(next(r for r in worst if r['recommendation']=='balanced')['K_raw'])>=1e-4
    pdfs=list((OUT/'figures').glob('*.pdf'));pngs=list((OUT/'figures').glob('*.png'))
    assert len(pdfs)==len(pngs)==7
    for p in pdfs:
        data=p.read_bytes()
        assert data.startswith(b'%PDF-') and len(re.findall(rb'/Type /Page\b',data))==1
        assert b'/Subtype /Image' not in data,'Raster object in vector figure: '+str(p)
    files=artifacts()
    if '--seal' in sys.argv:
        if receipt.exists():raise FileExistsError('Receipt already sealed')
        payload=dict(status='CURRENTLY_VERIFIED_PASS_NUMERICAL_DIAGNOSTIC_ONLY',schema_version=1,
            HEAD=start['HEAD'],request_sha256=start['request_sha256'],artifact_sha256=files,
            ledger_sha256={p:sha(ROOT/p) for p in LEDGERS},protected_file_count=len(start['protected']),
            protected_scope='All startup files unchanged except five authorized state ledgers; old model/source/cache/results preserved',
            preserved_input_manifest='startup_manifest.json',checks=len(read(OUT/'checks.json')['checks']),
            logged_evaluations=read(OUT/'checks.json')['rows'],vector_figures=7,png_dpi=350,
            baseline_K=read(OUT/'final_selection.json')['baseline']['K_raw'],
            recommendations=[{k:r[k] for k in ['recommendation','D_r','divergence_urad','jitter_urad','sigma_h_m','VA','nu_raw','ensemble_hash','K_raw']} for r in selected],
            lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',security_valid=False,hardware_validated=False,
            training_final_test_heldout_new_source_AP='NOT_RUN',production_baseline_or_threshold_approval='UNCHANGED')
        receipt.write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    saved=read(receipt)
    assert files==saved['artifact_sha256'],'Artifact inventory/hash mismatch'
    assert all(sha(ROOT/p)==h for p,h in saved['ledger_sha256'].items())
    print(json.dumps(dict(status=saved['status'],artifacts=len(files),protected_files=len(start['protected']),checks=saved['checks'],
        logged_evaluations=saved['logged_evaluations'],receipt_sha256=sha(receipt),numerical_evaluation_rerun=False)))


if __name__=='__main__':main()
