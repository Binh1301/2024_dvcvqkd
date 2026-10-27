"""Read-only fixed-receiver30 artifact/provenance checks; --seal packages once."""
import ast
import csv
from datetime import datetime,timezone
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
REPO=ROOT.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8-sig'))


def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def checks():
    start=read('startup_manifest.json')
    assert all((REPO/n).is_file() and sha(REPO/n)==h for n,h in start['protected'].items()),'Historical file changed'
    assert sha(ROOT/'docs/FINAL_MODEL_SPEC.md')==start['frozen_sha256']
    assert sha(Path(start['request_path']))==sha(OUT/'task.txt')==start['request_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==start['HEAD']
    assert subprocess.check_output(['git','branch','--show-current'],cwd=REPO,text=True).strip()==start['branch']
    allowed={'paper_uav_hap_cvqkd/'+n for n in start['allowed_ledger_changes']}
    assert set(subprocess.check_output(['git','diff','--name-only'],cwd=REPO,text=True).splitlines())<=allowed
    subprocess.run(['git','diff','--check'],cwd=REPO,capture_output=True,check=True)
    protocol=read('protocol.json')
    for n,h in protocol['implementation_sha256'].items():assert sha(OUT/n)==h
    execution=read('execution_history.json')
    assert execution['producer_sha256']==sha(OUT/'inspect_receiver30.py')
    assert execution['protocol_sha256']==sha(OUT/'protocol.json')
    numerical=read('numerical_checks.json')
    assert numerical['status']=='CURRENTLY_VERIFIED_PASS'
    assert all(x['status']=='CURRENTLY_VERIFIED_PASS' for x in numerical['checks'])
    result=read('results.json');A=result['model_A'];B=result['model_B']
    assert abs(A['I_AB']-.21074687539663958)<5e-12
    assert abs(A['chi_BE']-.19481699897277194)<5e-12
    assert abs(A['K_raw']-.005392532654035664)<5e-12
    assert A['eta_det']==.95 and A['epsilon_det']==.005
    assert 'eta_det' not in B and B['xi_det']==.005
    assert all(B[k] is None for k in ['I_AB','beta_I_AB','chi_BE','K_raw'])
    assert B['status']=='BLOCKED_BY_SCIENTIFIC_MODEL' and B['MI_Holevo_evaluation']=='NOT_RUN'
    assert B['M0']<1-1e-10 and protocol['mass_tolerance']==1e-10
    assert abs(result['model_B_PDF']['raw_upper_tail_mass']-1.056995513649377e-10)<1e-20
    assert not result['security_valid'] and result['no_optimization'] and result['no_new_source_moments']
    assert result['source_identity']['ensemble_hash']==protocol['source_hash']
    params=rows('parameters.csv')
    assert len(params)==execution['parameter_rows'] and len(params)>90
    assert all(x['unit'] and x['configuration_source'] and x['specified_or_derived'] for x in params)
    assert len(rows('conditional_normalization.csv'))==16 and len(rows('moments.csv'))==6
    assert all(abs(float(x['mass'])-1)<2e-10 for x in rows('conditional_normalization.csv'))
    assert all(abs(float(x['residual']))<2e-10 for x in rows('moments.csv'))
    for p in OUT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'))
    report=(OUT/'report_vi.md').read_text(encoding='utf-8')
    assert '\ufffd' not in report and 'Không có ηdet' in report and 'BLOCKED' in report
    assert len(numerical['checks'])==execution['tests']
    return dict(status='CURRENTLY_VERIFIED_PASS',protected_files=len(start['protected']),
        numerical_component_checks=len(numerical['checks']),parameter_rows=len(params),
        scientific_model_B_normalization='FAILED',model_B_rate='BLOCKED',
        security_valid=False,new_optimization=False,source_cache_changed=False)


def main():
    args=sys.argv[1:]
    if args not in [[],['--seal']]:raise ValueError('No arguments for read-only; --seal once')
    receipt=OUT/'final_receipt.json'
    if args==['--seal']:
        if receipt.exists():raise FileExistsError('Preserve existing seal')
        verified=checks();start=read('startup_manifest.json');diff=[]
        for name in start['allowed_ledger_changes']:
            before=(OUT/'startup_ledgers'/Path(name).name).read_text(encoding='utf-8')
            after=(ROOT/name).read_text(encoding='utf-8')
            diff.extend(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),
                fromfile='startup/'+name,tofile='current/'+name))
        (OUT/'scoped_ledger_changes.diff').write_text(''.join(diff),encoding='utf-8')
        verified.update(UTC=datetime.now(timezone.utc).isoformat(),
            artifact_sha256={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()},
            current_task_ledger_sha256={n:sha(ROOT/n) for n in start['allowed_ledger_changes']},
            verifier_executes_scientific_evaluator=False)
        receipt.write_text(json.dumps(verified,indent=2)+'\n',encoding='utf-8')
    else:
        saved=read('final_receipt.json')
        assert all((OUT/n).is_file() and sha(OUT/n)==h for n,h in saved['artifact_sha256'].items())
        assert all(sha(ROOT/n)==h for n,h in saved['current_task_ledger_sha256'].items())
        verified=checks()
    print('CURRENTLY_VERIFIED_PASS:',verified['parameter_rows'],'parameter rows;',
        verified['numerical_component_checks'],'scoped checks; Model B BLOCKED; no evaluator rerun',flush=True)


if __name__=='__main__':main()
