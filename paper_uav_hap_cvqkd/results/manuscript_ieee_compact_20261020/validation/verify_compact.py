"""Verify stored numbers, source preservation, and compiled layout; no solvers."""
from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]
ORIGINAL=ROOT/'results/manuscript_ieee_revision_20261020'
FINAL=ROOT/'results/mobility_parameter_sensitivity_final_20261020'
checks=[]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def js(path):return json.loads(path.read_text(encoding='utf-8'))
def rows(path):
    with path.open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))
def check(name,ok):
    checks.append(dict(check=name,passed=bool(ok)))
    if not ok:raise AssertionError(name)
def close(name,a,b):check(name,math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12))

receipt=OUT/'validation/final_receipt.json'
completed=receipt.exists() and js(receipt).get('status')=='CURRENTLY_VERIFIED_PASS'
if completed:
    for name,digest in js(receipt)['artifact_sha256'].items():
        assert sha(ROOT/name)==digest,'Completed artifact changed: '+name
startup=js(OUT/'startup_manifest.json')
for name,digest in js(OUT/'input_manifest.json')['inputs_sha256'].items():check('declared input:'+name,sha(ROOT/name)==digest)
tool=js(OUT/'tools/tex_toolchain.json')
check('Tectonic binary identity',sha(Path(tool['executable']))==tool['executable_sha256'])
allowed={'.agent/SESSION_HANDOFF.md','docs/EVIDENCE.md','docs/DECISION_LOG.md','docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md'}
for name,digest in startup['protected_sha256'].items():
    if name not in allowed:check('preserved:'+name,(ROOT/name).is_file() and sha(ROOT/name)==digest)
for p in ROOT.rglob('*'):
    if p.is_file() and not any(v in p.parts for v in ('.venv','.venv-binary-cloud','__pycache__','.git')):
        name=p.relative_to(ROOT).as_posix()
        check('new-file-scope:'+name,name in startup['protected_sha256'] or name.startswith('results/manuscript_ieee_compact_20261020/'))
check('Git branch',subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==startup['branch'])
check('Git HEAD',subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==startup['head'])
for directory,anchor in [(ORIGINAL,'9e181aa6ccaf14841d22884effb632df93318fb12461b63a68fd84d78a107bd7'),
                          (FINAL,'893ad90809c64c8d2ed742c374bf02dda2169842b71b6cef499fa3bb00960a09')]:
    old=directory/'validation/final_receipt.json'
    check('receipt anchor:'+directory.name,sha(old)==anchor)
    for name,digest in js(old)['artifact_sha256'].items():
        target=ROOT/name if directory==ORIGINAL else directory/name
        check('authenticated:'+name,sha(target)==digest)

original_main=(ORIGINAL/'main.tex').read_text(encoding='utf-8')
main=(OUT/'main.tex').read_text(encoding='utf-8')
check('unchanged front matter and preamble',main.startswith(original_main.split(r'\input{system_and_method}')[0]))
old_system=(ORIGINAL/'system_and_method.tex').read_text(encoding='utf-8')
intro=old_system[:old_system.index(r'\subsubsection{Source and Stationary-Position Optimization}')]
raw=old_system[old_system.index('For an unblocked link,'):old_system.index(' For a finite\nexact-source catalog')]
physical=old_system[old_system.index(r'\subsection{Recorded Physical-Layer Model and Security Boundary}'):old_system.index(r'\section{Optimization Method}')]
check('unchanged geometry/raw-rate/security text',(OUT/'system_model.tex').read_text(encoding='utf-8')==intro+raw+'\n\n'+physical)
check('unchanged bibliography database',sha(OUT/'manuscript_refs.bib')==sha(ORIGINAL/'manuscript_refs.bib'))
check('unchanged rendered bibliography',sha(OUT/'main.bbl')==sha(ORIGINAL/'main.bbl'))
compact=(OUT/'compact_sections.tex').read_text(encoding='utf-8')
combined=main+(OUT/'system_model.tex').read_text(encoding='utf-8')+compact
labels=re.findall(r'\\label\{([^}]+)\}',combined)
refs=re.findall(r'\\(?:ref|eqref)\{([^}]+)\}',combined)
check('unique labels',len(labels)==len(set(labels)))
check('references resolve',set(refs)<=set(labels))
check('essential equation labels',{'eq:raw','eq:p1','eq:p2','eq:p3','eq:dp_init','eq:dp'}<=set(labels))
check('single included vector figure',re.findall(r'\\includegraphics\[[^]]*\]\{([^}]+)\}',compact)==['figures/compact_sensitivity.pdf'])
check('no pseudocode',r'\begin{algorithm}' not in compact)
check('no size/margin/spacing shortcuts',not re.search(r'\\(?:vspace|hspace|resizebox|scalebox|fontsize|scriptsize|tiny|small|footnotesize|geometry|enlargethispage)\b',compact))
check('same document class',r'\documentclass[conference,a4paper]{IEEEtran}' in main)
check('security flags retained',all(s in main for s in [r'UNVALIDATED\_SECURITY\_MODEL',r'NOT\_READY\_FOR\_PUBLICATION\_SCALE\_RUNS']))
conclusion=compact.split(r'\label{sec:conclusion}')[1]
word_count=len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*",conclusion))
check('60-90 word conclusion',60<=word_count<=90)
numerical=compact.split(r'\label{sec:numerical}')[1].split(r'\section{Conclusion}')[0].strip()
check('three numerical paragraphs',len(re.split(r'\n\s*\n',numerical))==3)

stats=rows(FINAL/'tables/statistical_comparison.csv')
missions=rows(FINAL/'tables/selected_missions.csv')
key_fields=('figure','case_id','lambda_index','method')
grouped=defaultdict(list)
for r in missions:grouped[tuple(r[k] for k in key_fields)].append(r)
for r in stats:
    group=grouped[tuple(r[k] for k in key_fields)]
    check('100 mission IDs:'+str(tuple(r[k] for k in key_fields))+r['metric'],sorted(int(v['realization_id']) for v in group)==list(range(100)))
    close('saved mean:'+str(tuple(r[k] for k in key_fields))+r['metric'],float(r['mean']),statistics.mean(float(v[r['metric']]) for v in group))

def value(figure,parameter,method,metric,penalty=None):
    selected=[r for r in stats if r['figure']==str(figure) and float(r['parameter_value'])==parameter
              and r['method']==method and r['metric']==metric
              and (penalty is None or float(r['lambda_bits_per_use'])==penalty)]
    assert len(selected)==1
    return float(selected[0]['mean'])

lambda_ref=9.468026677248516e-6
def trade(penalty,metric):
    return float(next(r['mean'] for r in stats if r['figure']=='4' and r['method']=='DP'
                      and r['metric']==metric and float(r['lambda_bits_per_use'])==penalty))
findings=dict(J_DP_U_gain_percent=100*(value(1,100,'DP','U')/value(1,10,'DP','U')-1),
              p08_unavailability_percent={m:value(2,.8,m,'unavailability_percent') for m in ['Stationary','Greedy','DP']},
              rho_DP_distance_m=[value(3,x,'DP','D') for x in [0,.98]],
              rho_DP_U_gain_over_P2_percent=[100*(value(3,x,'DP','U')/value(3,x,'Stationary','U')-1) for x in [0,.98]],
              DP_distance_reduction_percent=100*(1-trade(lambda_ref,'D')/trade(0,'D')),
              DP_SKR_reduction_percent=100*(1-trade(lambda_ref,'K')/trade(0,'K')))
check('J percentage',round(findings['J_DP_U_gain_percent'],3)==11.409)
check('p percentages',[round(x,2) for x in findings['p08_unavailability_percent'].values()]==[24.60,16.53,4.07])
check('rho distances',[round(x,2) for x in findings['rho_DP_distance_m']]==[1038.25,31.84])
check('rho objective gains',[round(x,3) for x in findings['rho_DP_U_gain_over_P2_percent']]==[23.712,.155])
check('tradeoff distance',round(findings['DP_distance_reduction_percent'],3)==88.370)
check('tradeoff SKR',round(findings['DP_SKR_reduction_percent'],3)==.515)
source_rows={}
for filename in ('fig1_candidate_positions_data.csv','fig2_cloud_blockage_data.csv','fig3_temporal_correlation_data.csv'):
    for r in rows(FINAL/'figures'/filename):source_rows[(filename,r['method'],r['point_index'],r['metric'])]=r
rendered=rows(OUT/'figures/compact_sensitivity_data.csv')
check('57 actual saved points',len(rendered)==57)
filenames={1:'fig1_candidate_positions_data.csv',2:'fig2_cloud_blockage_data.csv',3:'fig3_temporal_correlation_data.csv'}
for r in rendered:
    expected=source_rows[(filenames[int(r['compact_panel'])],r['method'],r['point_index'],r['metric'])]
    check('unchanged plotted row:'+str((r['compact_panel'],r['method'],r['point_index'])),{k:v for k,v in r.items() if k!='compact_panel'}==expected)
render=js(OUT/'figures/render_metadata.json')
check('vector figure identity',render['pdf_sha256']==sha(OUT/'figures/compact_sensitivity.pdf'))
for name,digest in render['inputs_sha256'].items():check('figure input:'+name,sha(FINAL/'figures'/name)==digest)
check('legible nominal figure fonts',render['minimum_font_points']>=8.5)

layout=js(OUT/'validation/layout_measurement.json')
check('layout for current PDF',layout['pdf_sha256']==sha(OUT/'main.pdf'))
check('approximately 1.5 pages including figure/caption',1.45<=layout['occupied_equivalent_pages']<=1.50)
check('correct optimization start',layout['start']['page']==2 and layout['start']['column']==1)
check('conclusion endpoint',layout['end']['page']==3 and layout['end']['column']==1)
check('nearby figure',layout['figure_page']==3)
check('actual figure font scale',layout['figure_minimum_rendered_font_pt']>=8)
inspection=js(OUT/'validation/pdf_inspection.json')
check('rendered current PDF',inspection['pdf_sha256']==sha(OUT/'main.pdf') and len(inspection['pages'])==3)
for page in inspection['pages']:check('rendered page:'+str(page['page']),sha(OUT/'validation'/page['png'])==page['sha256'])
visual=js(OUT/'validation/visual_review.json')
check('visual review current PDF',visual['pdf_sha256']==sha(OUT/'main.pdf') and
      visual['reviewed_pages']==[dict(page=p['page'],sha256=p['sha256'],status='VISUALLY_REVIEWED') for p in inspection['pages']])
log=(OUT/'main.log').read_text(encoding='utf-8')
for name,pattern in [('errors',r'^!'),('undefined references',r'(?:Reference|Citation).*undefined|There were undefined'),
                     ('overfull',r'Overfull \\[hv]box'),('underfull',r'Underfull \\[hv]box'),('font substitutions','LaTeX Font Warning')]:
    check('no '+name,not re.search(pattern,log,re.M))
check('frozen identity unchanged',sha(ROOT/'docs/FINAL_MODEL_SPEC.md')=='df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15')
check('git diff whitespace',subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode==0)
result=dict(status='CURRENTLY_VERIFIED_PASS',checks=len(checks),protected_files=len(startup['protected_sha256']),
            conclusion_words=word_count,figures=1,panels=3,saved_plot_points=len(rendered),
            occupied_equivalent_pages=layout['occupied_equivalent_pages'],occupied_equivalent_columns=layout['occupied_equivalent_columns'],
            findings=findings,optimizer_calls=0,SKR_evaluator_calls=0,source_moment_calls=0,cloud_generator_calls=0,
            security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
for name,payload in [('checks.json',checks),('verification.json',result)]:
    p=OUT/'validation'/name
    if completed:assert js(p)==payload,'Completed evidence changed: '+name
    else:p.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(result,indent=2))
