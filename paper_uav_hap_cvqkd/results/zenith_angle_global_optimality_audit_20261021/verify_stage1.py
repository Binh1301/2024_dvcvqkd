"""Independent saved-artifact checks; never imports scientific evaluators."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import re
import numpy as np
import fitz
from PIL import Image

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
OLD=ROOT/'results/skr_vs_zenith_angle_20261019'


def js(p):
    return json.loads(p.read_text(encoding='utf-8'))


def rows(p):
    with p.open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    checks=[]
    def check(name,condition):
        assert condition,name
        checks.append(name)
    receipt=OUT/'validation/final_receipt.json'
    sealed=receipt.exists()
    if sealed:
        for name,digest in js(receipt)['artifact_sha256'].items():
            check('sealed artifact '+name,sha(OUT/name)==digest)
    original=rows(OLD/'source_roster.csv');values=rows(OLD/'all_candidate_evaluations.csv')
    audits=rows(OUT/'original_catalog_audit.csv');catalog=rows(OUT/'original_catalog_candidates.csv')
    check('catalog exactly218',len(catalog)==218 and Counter(r['family'] for r in catalog)=={'Uniform':36,'MB':182})
    check('same exact source identities',[(r['family'],r['nu_raw_hex'],r['VA_hex'],r['ensemble_hash']) for r in original]==[(r['family'],r['nu_raw_hex'],r['VA_hex'],r['ensemble_hash']) for r in catalog])
    order={r['ensemble_hash']:i for i,r in enumerate(original)}
    matrix=np.full((31,218),np.nan)
    lookup={}
    for r in values:
        z=int(float(r['zenith_deg']));column=order[r['ensemble_hash']]
        check('matrix unique cell '+str((z,column)),np.isnan(matrix[z//2,column]))
        matrix[z//2,column]=float(r['K_raw']);lookup[(z,r['ensemble_hash'])]=r
    check('all6758 cells finite',matrix.shape==(31,218) and np.isfinite(matrix).all())
    check('negative values retained',np.any(matrix<0) and sum(int(r['negative_candidates']) for r in audits)==int((matrix<0).sum()))
    for a in audits:
        z=int(a['zenith_deg']);indices=np.array([i for i,r in enumerate(original) if r['family']==('MB' if a['scheme']=='Optimized MB' else 'Uniform')])
        index=int(indices[np.argmax(matrix[z//2,indices])])
        check('independent array argmax '+a['scheme']+str(z),original[index]['ensemble_hash']==a['ensemble_hash'] and matrix[z//2,index]==float(a['K_raw']))
        sorted_values=np.sort(matrix[z//2,indices])
        check('runnerup '+a['scheme']+str(z),sorted_values[-1]-sorted_values[-2]==float(a['runner_up_gap_bits_per_use']))
    detail=rows(OLD/'skr_vs_zenith_angle_detailed.csv')
    for scheme,z,expected in [('Optimized Uniform',52,1.06625951727330e-4),('Fixed MB',48,2.41357175677000e-4),('Optimized MB',48,3.42145110300252e-4)]:
        data=[r for r in detail if r['scheme']==scheme];winner=data[int(np.argmax([float(r['K_raw']) for r in data]))]
        check('historical zenith peak '+scheme,int(winner['zenith_deg'])==z and abs(float(winner['K_raw'])-expected)<1e-18)
    check('no newly evaluated sources',rows(OUT/'new_exact_candidates.csv')==[])
    for a in rows(OUT/'optimality_improvement.csv'):
        check('no fabricated new optimum '+a['scheme']+a['zenith_deg'],all(a[k]=='N/A' for k in ['new_VA','new_nu','new_SKR','absolute_improvement','gain_percent']))
        check('unknown gap remains uncertified '+a['scheme']+a['zenith_deg'],a['certified_global_gap']=='NOT_CERTIFIED')
    summary=js(OUT/'summary.json')
    check('boundary anglesMB',summary['MB_upper_VA_angles']==list(range(24,61,2)))
    check('boundary anglesUniform',summary['Uniform_upper_VA_angles']==list(range(42,61,2)))
    proposal=js(OUT/'proposed_pilot.json')
    check('proposal explicitly unapproved',proposal['status']=='PROPOSED_NOT_APPROVED_NOT_EXECUTED')
    check('pilot limited sixsources',len(proposal['first_batch'])==6 and proposal['first_batch_max_new_rate_evaluations']==36)
    for p in rows(OUT/'data/plotted_rate_samples.csv'):
        source=lookup[(int(float(p['zenith_deg'])),p['ensemble_hash'])]
        check('plotted rate exact '+str((p['figure'],p['ensemble_hash'],p['zenith_deg'])),p['K_raw']==source['K_raw'])
    manifest=rows(OUT/'figure_manifest.csv');check('eight figures',len(manifest)==8)
    font_info=[]
    for r in manifest:
        p=OUT/r['pdf'];d=fitz.open(p);page=d[0]
        check('vector PDF '+r['figure'],len(d)==1 and not page.get_images() and bool(page.get_drawings()) and bool(page.get_text()))
        check('figure hash '+r['figure'],sha(p)==r['pdf_sha256'])
        text=page.get_text('dict');spans=[s for b in text['blocks'] if b['type']==0 for line in b['lines'] for s in line['spans']]
        check('embedded fonts '+r['figure'],all(len(d.extract_font(f[0])[3])>0 for f in page.get_fonts()))
        img=Image.open(OUT/r['png'])
        check('350dpi PNG '+r['figure'],abs(img.info['dpi'][0]-350)<.1 and abs(img.width-page.rect.width/72*350)<2)
        check('PDF text inpage '+r['figure'],all(s['bbox'][0]>=-1 and s['bbox'][1]>=-1 and s['bbox'][2]<=page.rect.width+1 and s['bbox'][3]<=page.rect.height+1 for s in spans))
        font_info.append(dict(figure=r['figure'],minimum_font_points=min(s['size'] for s in spans)))
    for p,digest in js(OUT/'input_manifest.json').items():
        check('input preserved '+p,sha(ROOT/p)==digest)
    snapshot=js(OUT/'startup_manifest.json');changed=[]
    allowed={'docs/EVIDENCE.md','docs/DECISION_LOG.md','docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md'}
    for p,digest in snapshot['protected_sha256'].items():
        if sha(ROOT/p)!=digest:
            changed.append(p);check('only permitted ledger '+p,p in allowed)
    for name in ['report_vi.md','parameter_domain_audit.md','figure_captions_en.md','validation_report.md']:
        text=(OUT/name).read_text(encoding='utf-8')
        for token in ['UNVALIDATED_SECURITY_MODEL','NOT_READY_FOR_PUBLICATION_SCALE_RUNS']:
            check('scope flag '+name+token,token in text)
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if '://' not in target:
                check('report link '+target,(OUT/target).exists())
    if not sealed:
        record=dict(status='CURRENTLY_VERIFIED_PASS',scope='STAGE_1_SAVED_CATALOG_ONLY',checks=len(checks),
            check_names=checks,source_count=218,saved_values=6758,catalog_argmax=62,argmax_mismatches=0,
            new_exact_sources=0,new_rate_evaluations=0,figure_count=8,figure_fonts=font_info,
            protected_files=len(snapshot['protected_sha256']),changed_ledgers=changed,
            pilot='NOT_RUN_AWAITING_DOMAIN_APPROVAL',continuous_optimality='NOT_CERTIFIED',
            security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
        (OUT/'validation/independent_checks.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',checks=len(checks),catalog_argmax=62,new_exact_sources=0,pilot='NOT_RUN_AWAITING_DOMAIN_APPROVAL')))


if __name__=='__main__':
    main()
