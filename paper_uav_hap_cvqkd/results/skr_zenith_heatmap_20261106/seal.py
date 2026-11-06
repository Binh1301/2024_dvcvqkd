"""Record final output identities after numerical and visual verification."""
import hashlib
import json
from pathlib import Path

from PIL import Image

OUT=Path(__file__).resolve().parent


def main():
    validation=json.loads((OUT/'verification.json').read_text())
    if validation['status']!='CURRENTLY_VERIFIED_PASS':raise ValueError('Numerical verification failed')
    figures={}
    for name in ('skr_vs_zenith.png','skr_heatmap.png'):
        with Image.open(OUT/name) as image:
            dpi=image.info.get('dpi',(0.,0.))
            if min(dpi)<299.9:raise ValueError('Figure DPI below 300: '+name)
            figures[name]=dict(size_px=list(image.size),dpi=list(dpi))
    manifest={str(p.relative_to(OUT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='final_manifest.json' and '__pycache__' not in p.parts}
    result=dict(status='COMPLETED_NUMERICAL_CATALOG_EVALUATION',files=manifest,figures=figures,
                scientific_scope='unchanged receiver30 asymptotic numerical objective; source evidence retained',
                Cw_or_security_evidence_promoted=False)
    (OUT/'final_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(files=len(manifest),figures=figures),indent=2))


if __name__=='__main__':main()
