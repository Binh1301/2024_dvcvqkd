"""Seal only this new delivery, after tests and human visual review evidence."""
from pathlib import Path
import hashlib
import json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal():
    source_names=['src/ibrahim_continuous_attenuation.py',
        'configs/ibrahim_continuous_attenuation.json',
        'docs/IBRAHIM_CONTINUOUS_ATTENUATION_README.md',
        'scripts/run_ibrahim_continuous_attenuation.py',
        'scripts/plot_ibrahim_continuous_attenuation.py',
        'scripts/report_ibrahim_continuous_attenuation.py',
        'scripts/verify_ibrahim_continuous_attenuation.py',
        'tests/test_ibrahim_continuous_attenuation.py']
    visual=json.loads((OUT/'visual_qa.json').read_text())
    assert visual['status']=='CURRENTLY_VERIFIED_PASS'
    provenance={'source_hashes':{name:sha(ROOT/name) for name in source_names},
        'initial_producer_snapshots':{'scripts/plot_ibrahim_continuous_attenuation.py':
                'producer_snapshots/plot_ibrahim_continuous_attenuation_initial.py',
            'scripts/report_ibrahim_continuous_attenuation.py':
                'producer_snapshots/report_ibrahim_continuous_attenuation_initial.py'},
        'presentation_change':'Move Figure E note to avoid whisker; rerender saved data only. Explain L0*N parameter degeneracy in report. No numerical run, field, parameter or criterion changed.',
        'scope':'No old file, frozen model, QKD/security or lifecycle settings changed'}
    (OUT/'verification_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    excluded={'artifact_hashes.json','artifact_verification.json'}
    artifacts={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*'))
               if p.is_file() and p.name not in excluded}
    (OUT/'artifact_hashes.json').write_text(json.dumps(artifacts,indent=2)+'\n',encoding='utf-8')
    print('Sealed',len(artifacts),'files')


if __name__=='__main__':seal()
