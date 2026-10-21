"""Bind the completed document artifacts; never runs scientific calculations."""
from pathlib import Path
import hashlib
import json

out = Path(__file__).resolve().parents[1]
root = out.parents[1]
target = out / 'validation/final_receipt.json'
if target.exists() and json.loads(target.read_text()).get('status') == 'CURRENTLY_VERIFIED_PASS':
    raise FileExistsError('Completed receipt is immutable')
verification = json.loads((out / 'validation/verification.json').read_text())
assert verification['status'] == 'CURRENTLY_VERIFIED_PASS'
paths = [p for p in out.rglob('*') if p.is_file() and p != target]
paths += [root / 'docs/security_model_consistency_audit.md', root / 'docs/manuscript_final_validation.md']
artifacts = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
receipt = {**verification, 'artifact_sha256': artifacts,
           'artifact_count': len(artifacts), 'compiled_pages': 6,
           'visual_review_pages': 6, 'figures_unchanged': 4,
           'security_model_validated': False, 'latest_exact_tex_available': False,
           'new_source_moment_calculations': 0, 'new_channel_calculations': 0,
           'scientific_source_changed': False, 'frozen_model_changed': False,
           'training_or_held_out_access': False, 'commit_or_push': False}
target.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'receipt_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                  'artifacts': len(artifacts), 'named_checks': verification['named_checks']}))
