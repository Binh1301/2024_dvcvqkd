"""Read-only integrity verification; does not import or execute scientific evaluators."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import subprocess

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipt=json.loads((OUT/'final_receipt.json').read_text(encoding='utf-8'))
    for name,expected in receipt['artifact_sha256'].items():
        assert sha(OUT/name)==expected,('Artifact changed',name)
    for name,expected in receipt['preserved_prior_files'].items():
        assert sha(ROOT.parent/name)==expected,('Prior input changed',name)
    for p in OUT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
    selection=json.loads((OUT/'selection.json').read_text())
    assert not selection['security_valid']
    assert selection['recommended']['detector_security']=='untrusted'
    assert selection['recommended_reference_geometry']['K_raw']>0
    positive=json.loads((OUT/'positive_MI_verification.json').read_text())
    assert positive['status']=='CURRENTLY_VERIFIED_PASS' and positive['failed_nodes']==0
    with (OUT/'table_B_optical_feasibility_final.csv').open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    values=[float(row['K_raw']) for row in rows]
    assert values==sorted(values,reverse=True)
    assert all(row['security_status']=='DIAGNOSTIC_ONLY_NOT_VALIDATED' for row in rows)
    with (OUT/'table_C_detector_sensitivity_final.csv').open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==50 and all(row['detector_security']=='untrusted' for row in rows)
    diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    assert diff.returncode==0,diff.stdout+diff.stderr
    print('CURRENTLY_VERIFIED_PASS: artifact hashes, protected prior inputs, AST, tables, raw signs, all positive MI nodes and git diff --check')
    print('Scope: numerical diagnostic only; security/hardware validation is not established.')


if __name__=='__main__':main()
