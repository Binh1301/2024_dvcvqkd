"""Read-only artifact checks. Does not import any scientific producer or solver."""
from pathlib import Path
import csv
import hashlib
import json
import math
import sys
sys.path.insert(0,'C:/Users/HP/.codex/tools/manuscript-pdf-20261020')
from PIL import Image
from pypdf import PdfReader

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def js(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    render=js(OUT/'validation/render_receipt.json')
    assert render['renderer_sha256']==sha(OUT/'restyle_saved_figures.py')
    checks=[];issues=[];formats=[]
    def check(name,condition):
        checks.append(name)
        if not condition:issues.append(name)
    check('render scope',render['simulations']==render['solver_calls']==render['source_moment_calls']==0)
    for row in render['figures']:
        name=row['group']+'/'+row['name']
        check(name+':artist/scales identity',row['fingerprint_before']==row['fingerprint_after'])
        check(name+':legends inside',not row['layout_issues'])
        with Image.open(OUT/row['png']) as im:
            dpi=im.info.get('dpi',())
            check(name+':350 dpi',len(dpi)==2 and all(abs(v-350)<.02 for v in dpi))
            check(name+':white background',im.convert('RGB').getpixel((0,0))==(255,255,255))
        pdf=PdfReader(OUT/row['pdf']);check(name+':single vector page',len(pdf.pages)==1)
        page=pdf.pages[0];res=page['/Resources'].get_object();fonts=[];images=[]
        for font in res.get('/Font',{}).get_object().values():
            fonts.append(str(font.get_object().get('/BaseFont','')))
        for key,obj in res.get('/XObject',{}).get_object().items():
            if obj.get_object().get('/Subtype')=='/Image':images.append(str(key))
        check(name+':Times font',any('TimesNewRoman' in font or 'Times-Roman' in font for font in fonts))
        check(name+':no rasterized PDF plots',not images)
        formats.append(dict(figure=name,pdf=row['pdf'],png=row['png'],fonts=fonts,raster_images=images,
                            pdf_sha256=sha(OUT/row['pdf']),png_sha256=sha(OUT/row['png'])))
    startup=js(OUT/'validation/startup_manifest.json')
    allowed={'docs/EVIDENCE.md','docs/DECISION_LOG.md','docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md'}
    for name,digest in startup['protected_sha256'].items():
        if name not in allowed:check('historical unchanged:'+name,(ROOT/name).is_file() and sha(ROOT/name)==digest)
    for name,digest in js(OUT/'validation/input_manifest.json').items():
        check('render input unchanged:'+name,(ROOT/name).is_file() and sha(ROOT/name)==digest)
    # Authenticate receipt members directly; old verifier entry points can run
    # optimizers and are deliberately never imported or called.
    receipts=[
      'manuscript_mobility_p1_p2_p3_20261019/validation/final_verification.json',
      'manuscript_mobility_p1_p2_p3_20261019/analysis/analysis_receipt.json',
      'manuscript_mobility_p1_p2_p3_20261019/analysis/comparison_figures/validation_receipt.json',
      'mobility_parameter_sensitivity_20261020/validation/final_receipt.json',
      'mobility_parameter_sensitivity_stage_b_20261020/validation/final_receipt.json',
      'mobility_parameter_sensitivity_final_20261020/validation/final_receipt.json',
      'manuscript_ieee_revision_20261020/validation/final_receipt.json',
      'manuscript_ieee_compact_20261020/validation/final_receipt.json',
      'manuscript_ieee_overleaf_20261021/validation/final_receipt.json']
    authenticated=[]
    for name in receipts:
        path=ROOT/'results'/name;old=js(path)
        key=next(k for k in ('artifacts_sha256','artifact_sha256') if k in old)
        # Receipts in validation bind their parent result directory.
        base=path.parent.parent if path.parent.name=='validation' else path.parent
        for member,digest in old[key].items():
            target=ROOT/member if member.split('/')[0] in ('results','docs','scripts','src','configs','tests','.agent') else base/member
            check('old receipt:'+name+':'+member,target.is_file() and sha(target)==digest)
        authenticated.append(dict(path=name,sha256=sha(path),members=len(old[key])))
    result=dict(status='CURRENTLY_VERIFIED_PASS' if not issues else 'FAILED',checks=len(checks),
                failures=issues,figures=len(formats),formats=formats,authenticated_receipts=authenticated,
                historical_files_checked=len(startup['protected_sha256'])-len(allowed),
                scope='Presentation, preserved numeric artists and unchanged saved-input bytes only',
                quantum_security_validated=False,security_status='UNVALIDATED_SECURITY_MODEL',
                lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',SKR_evaluator_calls=0,solver_calls=0,
                source_moment_calls=0,cloud_generator_calls=0,commit_or_push=False)
    serialized=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if (OUT/'validation/final_receipt.json').exists():
        assert (OUT/'validation/verification.json').read_text(encoding='utf-8')==serialized,'Completed verification changed'
    else:
        (OUT/'validation/verification.json').write_text(serialized,encoding='utf-8')
    print(json.dumps(dict(status=result['status'],checks=len(checks),figures=len(formats),failures=issues[:25]),ensure_ascii=False))
    return not issues


if __name__=='__main__':
    sys.exit(0 if main() else 1)
