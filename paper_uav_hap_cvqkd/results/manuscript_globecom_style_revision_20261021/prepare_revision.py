"""Authenticate historical manuscript/figures and prepare this isolated revision.

Only standard-library data reads and file copies; no scientific modules imported.
"""
import csv
import hashlib
import json
from pathlib import Path
import shutil

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
BASE=ROOT/'results/manuscript_ieee_overleaf_20261021'
STYLE=ROOT/'results/ieee_classic_restyled_figures_20261021'
FINAL=ROOT/'results/mobility_parameter_sensitivity_final_20261020'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def main():
    if (OUT/'main.tex').exists():raise FileExistsError('Do not prepare over an existing revision')
    checks=[];inputs={}
    names=['manuscript_ieee_overleaf_20261021','manuscript_ieee_compact_20261020',
           'manuscript_ieee_revision_20261020','ieee_classic_restyled_figures_20261021',
           'mobility_parameter_sensitivity_final_20261020','mobility_parameter_sensitivity_stage_b_20261020',
           'mobility_parameter_sensitivity_20261020']
    for name in names:
        folder=ROOT/'results'/name;receipt=folder/'validation/final_receipt.json'
        r=js(receipt)
        for member,digest in r['artifact_sha256'].items():
            p=ROOT/member if member.split('/')[0] in ('src','scripts','configs','docs','tests','results','.agent') else folder/member
            assert sha(p)==digest,('receipt',name,member)
            checks.append('receipt:'+name+':'+member)
        inputs[receipt.relative_to(ROOT).as_posix()]=sha(receipt)
    render=js(STYLE/'validation/render_receipt.json')
    entries=[]
    for name in ['fig2_cloud_blockage','fig3_temporal_correlation']:
        record=next(r for r in render['figures'] if r['group']=='00_final' and r['name']==name)
        assert record['fingerprint_before']==record['fingerprint_after']
        assert all(panel['xscale']==panel['yscale']=='linear' for panel in record['panels'])
        source=STYLE/record['pdf'];destination=OUT/'figures'/f'{name}.pdf'
        shutil.copyfile(source,destination)
        assert sha(source)==sha(destination)
        data=FINAL/'figures'/f'{name}_data.csv'
        inputs[source.relative_to(ROOT).as_posix()]=sha(source)
        inputs[data.relative_to(ROOT).as_posix()]=sha(data)
        entries.append(dict(scientific_result='Cloud blockage: mean usable SKR and zero-rate unavailability' if name=='fig2_cloud_blockage' else 'Latent temporal correlation: objective and total travel distance',
            old_figure='results/manuscript_ieee_overleaf_20261021/figures/compact_sensitivity.pdf',
            newest_verified_figure=source.relative_to(ROOT).as_posix(),
            manuscript_copy=destination.relative_to(OUT).as_posix(),source_csv=data.relative_to(ROOT).as_posix(),
            data_sha256=sha(data),figure_sha256=sha(source),
            original_figure_producer=record['producer'],restyle_producer='results/ieee_classic_restyled_figures_20261021/restyle_saved_figures.py',
            receipt='results/ieee_classic_restyled_figures_20261021/validation/final_receipt.json',
            numeric_fingerprint=record['fingerprint_after'],configuration='manuscript 2D-MI/homodyne; 233 sources; 233urad full divergence; Dr=0.08m',
            action='COPY_BYTE_FOR_BYTE; REPLACE_COMPACT_PANEL_WITH_LEGIBLE_TWO_PANEL_FIGURE'))
    entries.append(dict.fromkeys(entries[0],''))
    entries[-1].update(scientific_result='Candidate count J',old_figure=entries[0]['old_figure'],
        newest_verified_figure='results/ieee_classic_restyled_figures_20261021/figures/00_final/fig1_candidate_positions.pdf',
        source_csv='results/mobility_parameter_sensitivity_final_20261020/figures/fig1_candidate_positions_data.csv',
        action='KEEP_VERIFIED_11.409_PERCENT_IN_TEXT; OMIT_OPTIONAL_FIGURE_FOR_SPACE')
    for result,path,reason in [
        ('Mobility tradeoff','results/ieee_classic_restyled_figures_20261021/figures/00_final/fig4_skr_mobility_tradeoff.pdf','VALIDATE_AND_REPORT_88.370_PERCENT_DISTANCE_0.515_PERCENT_RATE_IN_TEXT'),
        ('Stage B probability','results/ieee_classic_restyled_figures_20261021/figures/04_stage_b/fig_B1_cloud_probability.pdf','PREFER_FINAL_CURATED_FIGURE_FOR_IDENTICAL_METRICS'),
        ('Zenith MI/Holevo diagnostic','results/zenith_angle_root_cause_diagnostic_20261021/figures/fig_F_MI_Holevo_SKR.pdf','EXCLUDE_PHYSICAL_DIAGNOSTIC_FROM_MOBILITY_EVIDENCE')]:
        row=dict.fromkeys(entries[0],'');row.update(scientific_result=result,newest_verified_figure=path,action=reason);entries.append(row)
    # Inventory the actual Stage B path, without assuming the directory label.
    index=rows(STYLE/'figure_index.csv')
    stage=next(r for r in index if r['figure']=='fig_B1_cloud_probability')
    entries[-2]['newest_verified_figure']=(STYLE/stage['pdf']).relative_to(ROOT).as_posix()
    with (OUT/'figure_replacement_manifest.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(entries[0]));w.writeheader();w.writerows(entries)
    for name in ['main.tex','main.pdf']:
        p=BASE/name;inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    for p in [ROOT/'configs/manuscript_mobility.json',FINAL/'tables/statistical_comparison.csv',
              FINAL/'tables/paired_improvements.csv',FINAL/'verified_findings.json',
              FINAL/'figure_captions_en.md',STYLE/'validation/render_receipt.json',
              ROOT/'docs/FINAL_MODEL_SPEC.md']:
        inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    for name in ['fig1_candidate_positions_data.csv','fig4_skr_mobility_tradeoff_data.csv']:
        p=FINAL/'figures'/name;inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    raw=(BASE/'main.tex').read_bytes()
    prefix=raw.split(b'\\section{Optimization Problem}',1)[0]
    bibliography=raw[raw.index(b'% Generated by IEEEtran.bst'):]
    (OUT/'validation/protected_prefix.tex.txt').write_bytes(prefix)
    (OUT/'validation/protected_bibliography.tex.txt').write_bytes(bibliography)
    (OUT/'input_manifest.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf-8',newline='\n')
    (OUT/'validation/preparation_checks.json').write_text(json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',
        historical_receipts=len(names),checks=len(checks),check_names=checks,
        selected_base=BASE.relative_to(ROOT).as_posix(),authenticated_source_of_attached_pdf=False,
        protected_prefix_sha256=hashlib.sha256(prefix).hexdigest(),protected_bibliography_sha256=hashlib.sha256(bibliography).hexdigest(),
        scientific_evaluations=0),indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Authenticated',len(names),'receipts /',len(checks),'members; copied two verified vector PDFs')


if __name__=='__main__':main()
