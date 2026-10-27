"""Saved zenith-sweep evidence and hashes only; no evaluator imports."""
import ast
import csv
from datetime import datetime,timezone
import difflib
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
REPO=ROOT.parent
LABELS=['Optimized Uniform 256-QAM','Fixed MB-shaped 256-QAM','Optimized MB-shaped 256-QAM']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))
def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def check():
    start=read('startup_manifest.json')
    assert all((REPO/p).is_file() and sha(REPO/p)==h for p,h in start['protected'].items()),'Protected historical file changed'
    assert sha(ROOT/'docs/FINAL_MODEL_SPEC.md')==start['frozen_sha256']
    assert sha(Path(start['request_path']))==sha(OUT/'task.txt')==start['request_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==start['HEAD']
    assert subprocess.check_output(['git','branch','--show-current'],cwd=REPO,text=True).strip()==start['branch']
    allowed={'paper_uav_hap_cvqkd/'+n for n in start['allowed_ledger_changes']}
    assert set(subprocess.check_output(['git','diff','--name-only'],cwd=REPO,text=True).splitlines())<=allowed
    subprocess.run(['git','diff','--check'],cwd=REPO,capture_output=True,check=True)
    protocol=read('protocol.json');sweep=read('sweep_receipt.json');figure=read('figure_receipt.json')
    for name,h in protocol['implementation_sha256'].items():assert sha(OUT/name)==h
    assert sweep['producer_sha256']==sha(OUT/'run_sweep.py') and sweep['protocol_sha256']==sha(OUT/'protocol.json')
    assert sweep['CSV_sha256']==figure['CSV_sha256']==sha(OUT/'skr_vs_zenith.csv')
    assert figure['renderer_sha256']==sha(OUT/'render_and_report.py')
    assert figure['PNG_sha256']==sha(OUT/'skr_vs_zenith.png') and figure['PDF_sha256']==sha(OUT/'skr_vs_zenith.pdf')
    assert protocol['mass_tolerance']==1e-10 and protocol['xi_det']==.005
    assert protocol['measurement']=='homodyne_1D_Gaussian_effective' and not protocol['source_interpolation']
    catalog=rows('source_catalog.csv');byhash={x['ensemble_hash']:x for x in catalog}
    assert len(byhash)==233 and sum(x['family']=='Uniform' for x in catalog)==36 and sum(x['family']=='MB' for x in catalog)==197
    assert all(sha(ROOT/x['source_path'])==x['source_sha256'] for x in catalog)
    data=rows('skr_vs_zenith.csv');assert len(data)==183 and {x['scheme'] for x in data}==set(LABELS)
    assert sorted({int(x['zenith_deg']) for x in data})==list(range(61))
    evaluations=0;failure_count=0;plot_points=0;failed_angles=[]
    for angle in range(61):
        block=read(f'angles/angle_{angle:03d}.json')
        assert block['producer_sha256']==sweep['producer_sha256'] and block['protocol_sha256']==sweep['protocol_sha256']
        raw=block['raw_PDF'];selection=[x for x in data if int(x['zenith_deg'])==angle]
        assert len(selection)==3
        assert abs(block['channel']['L_km']-19/math.cos(math.radians(angle)))<1e-11
        assert not raw['renormalized'] and not raw['clipped'] and 0<=raw['mh']**2<=raw['m1']<=1
        assert max(abs(x['residual']) for x in raw['direct'].values())<2e-10
        direct_noise=.0186*raw['direct']['1.0']['value']+.005*(raw['P0']+raw['direct']['0.0']['value'])
        assert abs(direct_noise-(.0186*raw['m1']+.005*raw['M0']))<2e-10
        assert abs(raw['upper_tail_quadrature']-raw['raw_upper_tail_mass'])<2e-10
        evaluations+=len(block['candidates'])+len(block['candidate_failures']);failure_count+=len(block['candidate_failures'])
        if not raw['normalized_within_tolerance']:
            failed_angles.append(angle)
            assert not block['candidates'] and not block['candidate_failures']
            assert all(not x['I_AB'] and not x['SKR'] and x['exclusion_reason']=='FAILED_CHANNEL_PDF_NORMALIZATION' for x in selection)
        for candidate in block['candidates']:
            identity=candidate['ensemble_hash'];source=byhash[identity]
            assert all(candidate[k]==float(source[k]) for k in ['C','w','VA','nu_raw'])
            assert candidate['source_sha256']==source['source_sha256']
            assert 'eta_det' not in candidate and candidate['xi_det']==.005
            assert candidate['T_Holevo']==raw['mh']**2
            assert candidate['matrix_spectrum_residual']<=1e-10 and candidate['uncertainty_min_eigenvalue']>=-1e-11
            assert min(candidate[k] for k in ['nu_1','nu_2','nu_3'])>=1
            assert abs(candidate['K_raw']-(.95*candidate['I_AB']-candidate['chi_BE']))<1e-13
        for value in selection:
            assert value['Dr_m']=='0.3' and value['divergence_urad']=='35.0' and value['jitter_urad']=='1.561'
            assert float(value['xi_det'])==.005 and float(value['xi_ch'])==.0186
            if value['scheme']==LABELS[1]:
                assert float(value['nu_raw'])==.25 and float(value['V_mod_or_VA'])==1.6249995399703647
                assert value['source_hash']==protocol['fixed_MB']['ensemble_hash']
            if value['SKR']:
                assert math.isfinite(float(value['SKR'])) and abs(float(value['SKR'])-(.95*float(value['I_AB'])-float(value['chi_BE'])))<1e-13
                assert abs(float(value['E_eta_xi'])-(.0186*raw['m1']+.005*raw['M0']))<1e-14
                if value['scheme']!=LABELS[1]:
                    family='Uniform' if value['scheme']==LABELS[0] else 'MB'
                    domain=[x for x in block['candidates'] if x['family']==family]
                    assert float(value['SKR'])>=max(x['K_raw'] for x in domain)-2e-12
                    if family=='Uniform':assert float(value['nu_raw'])==0
            positive=value['valid_point']=='True'
            assert positive==(value['numerically_valid']=='True' and value['SKR']!='' and float(value['SKR'])>0)
            if value['numerically_valid']=='True':
                proof=block['selected_checks'][value['source_hash']]
                assert proof['status']=='CURRENTLY_VERIFIED_PASS' and all(x['status']=='CURRENTLY_VERIFIED_PASS' for x in proof['checks'])
            if positive:
                plot_points+=1;proof=block['selected_checks'][value['source_hash']]
                assert proof['status']=='CURRENTLY_VERIFIED_PASS' and all(x['status']=='CURRENTLY_VERIFIED_PASS' for x in proof['checks'])
                assert all(abs(x['mass']-1)<2e-10 for x in proof['conditional_masses'])
                assert value['exclusion_reason']==''
            else:assert value['exclusion_reason']
    summary=read('summary.json')
    assert summary['candidate_evaluations']==evaluations and summary['candidate_failures']==failure_count
    assert summary['positive_plotted_points']==plot_points==figure['positive_values_rendered']
    assert summary['PDF_failed_angles']==failed_angles and summary['selected_rows']==183
    assert figure['labels']==LABELS and figure['negative_or_invalid_values_rendered']==0
    assert sum(x['positive_points'] for x in figure['curves'])==plot_points
    png=(OUT/'skr_vs_zenith.png').read_bytes();width,height=struct.unpack('>II',png[16:24])
    assert width>=2000 and height>=1400 and png[:8]==b'\x89PNG\r\n\x1a\n'
    assert (OUT/'skr_vs_zenith.pdf').read_bytes().startswith(b'%PDF')
    assert read('visual_review.json')['status']=='CURRENTLY_VERIFIED_PASS'
    for p in OUT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'))
    text=(OUT/'report_vi.md').read_text(encoding='utf-8')
    assert '\ufffd' not in text and 'Không dùng eta_det' in text and 'Không nội suy' in text
    return dict(status='CURRENTLY_VERIFIED_PASS',protected_files=len(start['protected']),angles=61,
        selected_rows=183,candidate_evaluations=evaluations,candidate_failures=failure_count,
        positive_plotted_points=plot_points,PDF_failed_angles=failed_angles,security_valid=False,
        optimization='Finite authenticated exact-source catalog only',numerical_rerun_by_verifier=False)


def main():
    args=sys.argv[1:]
    if args not in [[],['--seal']]:raise ValueError('Use no argument for read-only verification, or --seal once')
    receipt=OUT/'final_receipt.json'
    if args:
        if receipt.exists():raise FileExistsError('Preserve sealed result')
        result=check();start=read('startup_manifest.json');diff=[]
        for name in start['allowed_ledger_changes']:
            before=(OUT/'startup_ledgers'/Path(name).name).read_text(encoding='utf-8')
            after=(ROOT/name).read_text(encoding='utf-8')
            diff.extend(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),
                fromfile='startup/'+name,tofile='current/'+name))
        (OUT/'scoped_ledger_changes.diff').write_text(''.join(diff),encoding='utf-8')
        result.update(UTC=datetime.now(timezone.utc).isoformat(),
            artifact_sha256={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()},
            current_task_ledger_sha256={n:sha(ROOT/n) for n in start['allowed_ledger_changes']})
        receipt.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    else:
        saved=read('final_receipt.json')
        assert all((OUT/n).is_file() and sha(OUT/n)==h for n,h in saved['artifact_sha256'].items())
        assert all(sha(ROOT/n)==h for n,h in saved['current_task_ledger_sha256'].items())
        result=check()
    print('CURRENTLY_VERIFIED_PASS',result['angles'],'angles;',result['candidate_evaluations'],
        'candidate evaluations;',result['positive_plotted_points'],'positive points; no numerical rerun',flush=True)


if __name__=='__main__':main()
