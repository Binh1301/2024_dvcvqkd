"""Saved-evidence verification only. --prepare and --seal package this audit once."""
import ast
import csv
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
REPO=ROOT.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8-sig'))


def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def save(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def git(*args):
    return subprocess.check_output(['git',*args],cwd=REPO,text=True,encoding='utf-8').strip()


def check():
    checks=[]
    def require(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    start=read('startup_manifest.json')
    allowed={'paper_uav_hap_cvqkd/'+p for p in start['allowed_ledger_changes']}
    protected={k:v for k,v in start['protected'].items() if k not in allowed}
    require(all((REPO/p).is_file() and sha(REPO/p)==h for p,h in protected.items()),
        'Protected historical/source/config/frozen files unchanged')
    require(git('rev-parse','HEAD')==start['HEAD'] and git('branch','--show-current')==start['branch'],
        'Repository branch and HEAD unchanged')
    require(set(git('diff','--name-only').splitlines())<=allowed,'Tracked changes limited to five ledgers')
    subprocess.run(['git','diff','--check'],cwd=REPO,check=True,capture_output=True)
    require(True,'Git whitespace check')
    require(sha(ROOT/'docs/FINAL_MODEL_SPEC.md')==start['frozen_current_sha256'],
        'Frozen current hash unchanged; historical discrepancy retained')
    for key,target in [('request','inputs/task.txt'),('manuscript','inputs/manuscript_v43.pdf')]:
        require(sha(Path(start[key+'_path']))==sha(OUT/target)==start[key+'_sha256'],key+' original and input copy unchanged')
    protocol=read('protocol.json');plan=read('comparison_plan.json')
    require(plan['protocol_sha256']==sha(OUT/'protocol.json') and plan['producer_sha256']==sha(OUT/'compare.py'),
        'Comparison producer and outcome-independent protocol hashes')
    require(all(sha(OUT/'attempt_1'/n)==h for n,h in protocol['initial_implementation_sha256'].items()),
        'Initial producer snapshots retained')
    require(protocol['mass_tolerance']==1e-10 and protocol['primary_secure_default'] is None,
        'Original mass tolerance and no secure default')
    for n in ['unit_tests.json','historical_regressions.json','validation.json','comparison_receipt.json','inventory_receipt.json']:
        require(read(n)['status']=='CURRENTLY_VERIFIED_PASS',n+' recorded scoped pass')
    unit=read('unit_tests.json');reg=read('historical_regressions.json')['records']
    require(unit['tests']==18 and not unit['failures'] and not unit['errors'],'18 unit tests without recorded failure')
    require(len(reg)==10 and all(x['status']=='CURRENTLY_VERIFIED_PASS' and max(abs(v) for v in x['differences'].values())<5e-12 for x in reg),
        '10 fresh matched historical regressions')
    expected={'source_normalization.csv':233,'channel_moment_checks.csv':27,
        'conditional_pdf_normalization.csv':32,'MI_independent_checks.csv':2,
        'old_vs_new.csv':10,'corrected_same_channel.csv':9,
        'detector_convention_comparison.csv':144,'classical_quantum_plane_checks.csv':16,
        'focused_independent_checks.csv':9,'repository_map.csv':37,
        'cache_impact.csv':287,'affected_results.csv':252,
        'scenario_parameters.csv':9,'noise_moment_checks.csv':288}
    for n,count in expected.items():require(len(rows(n))==count,n+' row count')
    source=rows('source_normalization.csv');byhash={x['ensemble_hash']:x for x in source}
    require(len(byhash)==233 and {'MB','Uniform'}=={x['family'] for x in source},'233 distinct MB/Uniform source identities')
    for x in source:
        payload=ROOT/x['source_path']
        require(sha(payload)==x['source_sha256'],'Source payload '+x['ensemble_hash'])
        d=json.loads(payload.read_text(encoding='utf-8'))
        require(all(float(x[k])==d[k] for k in ['C','w']) and float(x['VA']).hex()==d['V_A_hex']
            and x['ensemble_hash']==d['ensemble_hash'],'Exact C,w,VA identity '+x['ensemble_hash'])
        require(abs(float(x['PMF_sum'])-1)<1e-13 and abs(float(x['repo_VA_identity_residual']))<2e-12
            and abs(float(x['variance_X'])-float(x['VA']))<2e-12
            and abs(float(x['mean_X']))<1e-12,'Source normalization '+x['ensemble_hash'])
    pdf=read('channel_pdf_audit.json')['contexts']
    bad={x['context'] for x in pdf if x['normalization_status']=='FAILED'}
    require(len(pdf)==9 and bad=={'historical40cm','historical55cm','receiver30'},
        'Nine raw PDF contexts; three explicit mass failures')
    require(all(not x['renormalized'] and not x['clipped'] and x['moment_ordering'] for x in pdf),
        'PDF law, outage atom, no normalization or clipping repair')
    require(all(abs(float(x['residual']))<2e-10 for x in rows('channel_moment_checks.csv')),
        'Closed-form bounded moments match independent integration')
    require(all(abs(float(x['residual']))<2e-10 for x in rows('noise_moment_checks.csv')),
        '288 noise moments agree by independent quadrature linearity with explicit zero atom')
    require(all(abs(float(x['mass'])-1)<2e-10 for x in rows('conditional_pdf_normalization.csv')),
        'Real conditional Gaussian densities normalized')
    comparison=rows('detector_convention_comparison.csv')
    require({float(x['eta_det']) for x in comparison}=={.8,.85,.9,.95} and
        {float(x['epsilon_det']) for x in comparison}=={.0135,.005},'Separate hardware efficiency and electronic noise grids')
    for x in comparison:
        if x['model'] in ['B_literal_v43_as_printed','B_independent_xi_det_unresolved']:
            require(all(x[k]=='' for k in ['I_AB','chi_BE','K_raw']),'Invalid/undefined literal model has no numerical SKR')
        else:
            require(all(math.isfinite(float(x[k])) for k in ['I_AB','chi_BE','K_raw']), 'Finite explicitly projected/physical diagnostics')
    for x in rows('focused_independent_checks.csv'):
        require(abs(float(x['MI_GH64'])-float(x['MI_GH128']))<2e-10 and
            abs(float(x['MI_adaptive'])-float(x['MI_GH128']))<2e-10 and float(x['adaptive_error'])<2e-10
            and abs(float(x['chi_Z33'])-float(x['chi_Z129']))<2e-8
            and max(abs(float(x[k])-float(x['chi_Z129'])) for k in ['chi_entropy80','chi_entropy110'])<2e-11,
            'Independent MI/full-Z/entropy checks '+x['scenario'])
    require(all(abs(float(x['MI_difference']))<2e-10 for x in rows('classical_quantum_plane_checks.csv')),
        'Classical MI invariant; Holevo kept at physical quantum plane')
    old={x['scenario']:x for x in rows('old_vs_new.csv')}
    require(float(old['receiver28p1']['Legacy_SKR'])>0>float(old['receiver28p1']['Corrected_SKR'])
        and float(old['receiver30']['Corrected_SKR'])>0,'28.1cm Gaussian sign reversal; 30cm passive-law positive only')
    raw=read('raw_manuscript43_results.json')
    require({x['scenario'] for x in raw if x['K_raw'] is None}==bad
        and all(all(x[k] is None for k in ['I_AB','chi_BE','K_raw']) for x in raw if x['scenario'] in bad),
        'Raw PDF failed contexts return unavailable MI/Holevo/K')
    physical=rows('corrected_same_channel.csv')+read('covariance_unit_checks.json')
    require(all(float(x['chi_BE'])>=0 and min(float(x[k]) for k in ['nu_1','nu_2','nu_3'])>=1-1e-11 for x in physical),
        'Saved physical covariance spectra and finite nonnegative Holevo')
    for x in rows('corrected_same_channel.csv'):
        s=byhash[x['source_hash']]
        require(all(float(x[k])==float(s[k]) for k in ['C','w','VA']), 'Focused result uses unchanged source '+x['scenario'])
    for x in rows('repository_map.csv')+rows('cache_impact.csv'):
        require(sha(ROOT/x['path'])==x['sha256'],'Inventory path/hash '+x['path'])
    inv=read('inventory_receipt.json');entries=rows('affected_results.csv')
    require(inv['result_entries']==252 and inv['result_directories']==107 and inv['result_root_files']==145
        and sum(x['entry_kind']=='directory' for x in entries)==107,'Inventory distinguishes directories and root files')
    require(read('variants.json')['recommended_secure_default'] is None
        and not read('comparison_receipt.json')['security_valid']
        and not read('validation.json')['model_scientifically_validated'],'No whole-model or secure-default approval')
    for path in OUT.glob('*.py'):ast.parse(path.read_text(encoding='utf-8-sig'))
    require(True,'All new Python scripts parse')
    for name in ['report_vi.md','manuscript_corrections_vi.md','README.md']:
        text=(OUT/name).read_text(encoding='utf-8')
        require('\ufffd' not in text and 'không' in text.lower(),name+' UTF-8 text')
    report=(OUT/'report_vi.md').read_text(encoding='utf-8')
    require(all(old[k]['Corrected_SKR'] in report for k in old),'Report agrees with saved old-versus-new results')
    require('verify.py' in (OUT/'isolated_code_patch.diff').read_text(encoding='utf-8'),'Patch contains read-only verifier')
    return dict(status='CURRENTLY_VERIFIED_PASS',scope='SAVED_COMPONENT_AND_PROVENANCE_EVIDENCE_ONLY',
        protected_files=len(protected),checks=len(checks),check_names=checks,
        tests=18,historical_regressions=10,exact_sources=233,raw_PDF_contexts=9,
        scientific_PDF_failures=sorted(bad),model_security_valid=False,recommended_secure_default=None)


def main():
    mode=sys.argv[1:] or ['--verify']
    if mode not in [['--verify'],['--prepare'],['--seal']]:raise ValueError('Use --prepare, --seal, or no argument')
    receipt=OUT/'final_receipt.json'
    if mode==['--prepare']:
        if receipt.exists() or (OUT/'completion_checks.json').exists():raise FileExistsError('Preserve completed packaging')
        result=check()
        history=dict(UTC=datetime.now(timezone.utc).isoformat(),status='COMPLETED_WITH_MODEL_BLOCKERS',
            request='7944a7e7-5bcc-43d9-8f85-c514f9d2fb92',
            ordered_phases=['preserved historical regressions','initial 17-test validation then KeyError B',
                'correct original PDF factory and add 18th unit test','18-test component validation',
                'fixed-source focused comparisons','inventory/notation/Rician diagnostics','report and saved-evidence packaging'],
            attempts=dict(initial='attempt_1/failure.json',tolerances_changed=False,
                metadata_only_fix='252 entries were mislabeled as directories; now 107 directories plus 145 root files; originals in inventory_metadata_before_fix'),
            numerical_replay_in_packaging=False,new_AP=False,new_optimization=False,heldout_test_publication=False,
            producer_sha256={p.name:sha(p) for p in sorted(OUT.glob('*.py'))},
            protocol_sha256=sha(OUT/'protocol.json'),comparison_plan_sha256=sha(OUT/'comparison_plan.json'),
            environment=dict(python=platform.python_version(),platform=platform.platform(),
                packages={n:version(n) for n in ['numpy','scipy','mpmath']},PDF_tool='PyMuPDF1.26.5 outside project venv'),
            manuscript_pages_visually_checked=[2,3,4],PDF_modified=False,production_default_changed=False,
            scientific_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
        save('execution_history.json',history);save('completion_checks.json',result)
    elif mode==['--seal']:
        if receipt.exists():raise FileExistsError('Preserve existing seal')
        result=check()
        require_paths=['execution_history.json','completion_checks.json','scoped_ledger_changes.diff']
        if not all((OUT/n).exists() for n in require_paths):raise FileNotFoundError(require_paths)
        files={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()}
        start=read('startup_manifest.json')
        save('final_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',audit_outcome='COMPLETED_WITH_MODEL_BLOCKERS',
            UTC=datetime.now(timezone.utc).isoformat(),security_valid=False,recommended_secure_default=None,
            scientific_PDF_failures=result['scientific_PDF_failures'],protected_files=result['protected_files'],
            saved_evidence_checks=result['checks'],artifact_sha256=files,
            ledger_sha256={n:sha(ROOT/n) for n in start['allowed_ledger_changes']},
            branch=start['branch'],HEAD=start['HEAD'],numerical_evaluation_performed_by_verifier=False))
    else:
        saved=read('final_receipt.json')
        if not all((OUT/n).is_file() and sha(OUT/n)==h for n,h in saved['artifact_sha256'].items()):
            raise AssertionError('Sealed audit artifact changed')
        if not all(sha(ROOT/n)==h for n,h in saved['ledger_sha256'].items()):
            raise AssertionError('Sealed task ledger changed')
        result=check()
        if result['checks']!=saved['saved_evidence_checks']:raise AssertionError('Verification schema changed')
    print('CURRENTLY_VERIFIED_PASS',mode[0],'; saved evidence only; secure default = NONE',flush=True)


if __name__=='__main__':
    main()
