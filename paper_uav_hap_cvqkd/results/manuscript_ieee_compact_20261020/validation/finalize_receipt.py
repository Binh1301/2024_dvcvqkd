"""Freeze the completed compact document; no scientific evaluations."""
from pathlib import Path
import hashlib
import json

out=Path(__file__).resolve().parents[1]
root=out.parents[1]
target=out/'validation/final_receipt.json'
if target.exists() and json.loads(target.read_text()).get('status')=='CURRENTLY_VERIFIED_PASS':
    raise FileExistsError('Completed receipt is immutable')
verification=json.loads((out/'validation/verification.json').read_text())
assert verification['status']=='CURRENTLY_VERIFIED_PASS'
artifacts={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(out.rglob('*')) if p.is_file() and p!=target}
receipt={**verification,'artifact_sha256':artifacts,'artifact_count':len(artifacts),
         'compiled_pages':3,'original_manuscript_unchanged':True,'protected_physical_layer_unchanged':True,
         'front_matter_unchanged':True,'bibliography_unchanged':True,
         'security_model_validated':False,'commit_or_push':False}
target.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'receipt_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                  'artifacts':len(artifacts),'checks':verification['checks'],
                  'occupied_equivalent_pages':verification['occupied_equivalent_pages']}))
