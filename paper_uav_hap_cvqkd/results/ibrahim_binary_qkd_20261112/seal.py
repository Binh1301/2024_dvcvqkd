"""Bind current producers and exports, then run this package's read-only verifier."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


names = ['src/ibrahim_binary_qkd.py', 'configs/ibrahim_binary_qkd.json',
         'tests/test_ibrahim_binary_qkd.py', 'scripts/run_ibrahim_binary_qkd.py',
         'scripts/plot_ibrahim_binary_qkd.py', 'scripts/report_ibrahim_binary_qkd.py',
         'docs/IBRAHIM_BINARY_QKD_README.md']
save(OUT / 'producer_hashes.json', {name: sha(ROOT / name) for name in names})
save(OUT / 'artifact_hashes.json', {
    p.relative_to(OUT).as_posix(): sha(p) for p in sorted(OUT.rglob('*'))
    if p.is_file() and '__pycache__' not in p.parts
    and p.name not in {'artifact_hashes.json', 'verification.json'}
})
result = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(OUT / 'verify.py')],
                        capture_output=True, encoding='utf-8')
if result.returncode:
    raise RuntimeError(result.stdout + result.stderr)
record = json.loads(result.stdout)
save(OUT / 'verification.json', record)
print(json.dumps(record, indent=2))
