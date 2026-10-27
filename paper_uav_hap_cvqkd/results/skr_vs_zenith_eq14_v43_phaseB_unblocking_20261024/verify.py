"""Read-only forensic package and historical-file verification; no evaluators."""
import csv
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))


def verify():
    startup=read(OUT/'startup_manifest.json')
    for name,digest in startup['protected'].items():
        assert sha(ROOT.parent/name)==digest,'Historical file changed: '+name
    manifest=read(OUT/'artifact_manifest.json')
    for name,digest in manifest['files'].items():
        assert sha(OUT/name)==digest,'Forensic artifact changed: '+name
    summary=read(OUT/'readiness_summary.json')
    assert summary['PHASE_B_STRICT_READY'] is False
    assert summary['expensive_source_recomputations']==0
    assert not summary['pilot_executed'] and not summary['full_sweep_executed']
    with (OUT/'pilot_source_evidence.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    assert len(rows)==81
    assert sum(bool(row['source_path']) for row in rows)==80
    for row in rows:
        if row['source_path']:assert sha(ROOT/row['source_path'])==row['source_sha256']
    for name in ['pilot','exact_source_cache','new_exact_source']:
        assert not (OUT/name).exists(),'No new source/pilot outputs allowed'
    return dict(status='CURRENTLY_VERIFIED_PASS',protected_files=len(startup['protected']),
        artifacts=len(manifest['files']),source_rows=len(rows),source_jobs=0,
        PHASE_B_STRICT_READY=False,pilot_executed=False,full_sweep_executed=False)


if __name__=='__main__':print(json.dumps(verify(),indent=2))
