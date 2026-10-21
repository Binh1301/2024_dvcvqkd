"""Verify saved-data editorial extension without rerunning any scientific solver."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import math
import re
import subprocess

from PIL import Image

OUT = Path(__file__).resolve().parent
BASE = OUT.parents[1]
ROOT = BASE.parents[1]
CHECKS = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    CHECKS.append(name)


def close(a, b):
    return math.isclose(float(a), float(b), abs_tol=1e-15, rel_tol=1e-12)


def verify():
    startup = read_json(OUT / 'startup_manifest.json')
    check('base receipt identity unchanged', sha(BASE / 'validation/final_receipt.json') == startup['base_receipt_sha256'])
    receipt = read_json(BASE / 'validation/final_receipt.json')
    check('base receipt original PASS', receipt['status'] == 'CURRENTLY_VERIFIED_PASS' and receipt['named_assertions'] == 7445)
    for name, digest in receipt['artifact_sha256'].items():
        check('original artifact ' + name, sha(BASE / name) == digest)
    for name, digest in receipt['producer_sha256'].items():
        check('original producer ' + name, sha(ROOT / name) == digest)
    changed = [name for name, digest in startup['protected_files'].items() if name not in startup['allowed_changed'] and (not (ROOT / name).is_file() or sha(ROOT / name) != digest)]
    check('all startup files preserved except five authorized ledgers', not changed)
    for command, key in ((['git', 'branch', '--show-current'], 'branch'), (['git', 'rev-parse', 'HEAD'], 'commit')):
        check('Git ' + key + ' unchanged', subprocess.check_output(command, cwd=ROOT, text=True).strip() == startup[key])
    files = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '--', '.'], cwd=ROOT, text=True).splitlines()
    check('new files only in editorial child namespace', all(n in startup['protected_files'] or n.startswith(startup['allowed_output_prefix']) for n in files))
    check('diff whitespace clean', subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True).returncode == 0)
    for name in ('build_report.py', 'verify_review.py'):
        modules = [n.module or '' for n in ast.walk(ast.parse((OUT / name).read_text(encoding='utf-8'))) if isinstance(n, ast.ImportFrom)]
        modules += [alias.name for n in ast.walk(ast.parse((OUT / name).read_text(encoding='utf-8'))) if isinstance(n, ast.Import) for alias in n.names]
        check('no solver or evaluator imports ' + name, all(m.split('.')[0] in {'pathlib', 'csv', 'hashlib', 'json', 'matplotlib', 'ast', 'math', 're', 'subprocess', 'PIL'} for m in modules))
    check('no cloud/source/path arrays generated', not any(p.suffix in ('.npz', '.npy') for p in OUT.iterdir()))
    protocol = read_json(BASE / 'protocol.json')['settings']
    check('Stage A settings unchanged and Stage B disabled', protocol['stage'] == 'A' and protocol['stage_b_allowed'] is False and protocol['new_cloud_generation_allowed'] is False)

    summary = {(r['case_id'], int(r['lambda_index']), r['method']): r for r in rows(BASE / 'existing_data/aggregate_statistics.csv')}
    paired = {(r['case_id'], int(r['lambda_index']), r['baseline'], r['metric']): r for r in rows(BASE / 'existing_data/paired_improvements.csv')}
    missions = rows(BASE / 'existing_data/mission_metrics.csv')
    by_mission = {(r['case_id'], r['lambda_index'], r['realization_id'], r['method']): r for r in missions}
    positive_dp = [r for r in missions if r['method'] == 'DP' and int(r['lambda_index']) == 1]
    lower_k = sum(float(r['K']) + 1e-12 < float(by_mission[r['case_id'], r['lambda_index'], r['realization_id'], 'Greedy']['K']) for r in positive_dp)
    for baseline in ('Stationary', 'Greedy'):
        check('saved mission-wise U dominance over ' + baseline, all(float(r['U']) + 1e-12 >= float(by_mission[r['case_id'], r['lambda_index'], r['realization_id'], baseline]['U']) for r in positive_dp))
    for li in (0, 1):
        for method in ('Stationary', 'Greedy', 'DP'):
            selected = [r for r in missions if r['case_id'] == 'base' and int(r['lambda_index']) == li and r['method'] == method]
            check(f'default 100 mission IDs lambda{li} {method}', sorted(int(r['realization_id']) for r in selected) == list(range(100)))
            for metric in ('K', 'U', 'D', 'availability'):
                check(f'default mean {metric} lambda{li} {method}', close(math.fsum(float(r[metric]) for r in selected) / 100, summary['base', li, method][metric + '_mean']))
    def val(case, method, metric, li=1):
        return float(summary[case, li, method][metric + '_mean'])
    def gap(case, baseline, key):
        return float(paired[case, 1, baseline, 'U'][key])
    expected = {
        'baseline_DP_U_gain_over_P2_percent': 100 * (val('base', 'DP', 'U') - val('base', 'Stationary', 'U')) / val('base', 'Stationary', 'U'),
        'baseline_DP_U_gain_over_Greedy_percent': 100 * (val('base', 'DP', 'U') - val('base', 'Greedy', 'U')) / val('base', 'Greedy', 'U'),
        'baseline_DP_distance_saving_over_Greedy_percent': 100 * (val('base', 'Greedy', 'D') - val('base', 'DP', 'D')) / val('base', 'Greedy', 'D'),
        'DP_distance_reduction_lambda0_to_ref_percent': 100 * (val('base', 'DP', 'D', 0) - val('base', 'DP', 'D')) / val('base', 'DP', 'D', 0),
        'DP_SKR_loss_lambda0_to_ref_percent': 100 * (val('base', 'DP', 'K', 0) - val('base', 'DP', 'K')) / val('base', 'DP', 'K', 0),
        'DP_SKR_lower_than_Greedy_missions_lambda_ref': lower_k,
        'distinct_case_missions_lambda_ref': len(positive_dp),
        'DP_J10_to_100_U_increase_percent': 100 * (val('base', 'DP', 'U') - val('J_10', 'DP', 'U')) / val('J_10', 'DP', 'U'),
        'DP_J10_to_100_K_increase_percent': 100 * (val('base', 'DP', 'K') - val('J_10', 'DP', 'K')) / val('J_10', 'DP', 'K'),
        'DP_J20_U_fraction_of_J100_percent': 100 * val('J_20', 'DP', 'U') / val('base', 'DP', 'U'),
        'DP_speed15_to_25_U_increase_percent': 100 * (val('speed_25', 'DP', 'U') - val('base', 'DP', 'U')) / val('base', 'DP', 'U'),
        'DP_speed20_to_25_distance_change_m': val('speed_25', 'DP', 'D') - val('speed_20', 'DP', 'D'),
        'p08_DP_U_gain_over_P2_percent': gap('probability_0p8', 'Stationary', 'ratio_of_means_percent'),
        'p08_DP_U_gain_over_Greedy_percent': gap('probability_0p8', 'Greedy', 'ratio_of_means_percent'),
        'p08_DP_delta_U_over_P2': gap('probability_0p8', 'Stationary', 'mean'),
        'p08_DP_delta_U_over_P2_ci95_low': gap('probability_0p8', 'Stationary', 'ci95_low'),
        'p08_DP_delta_U_over_P2_ci95_high': gap('probability_0p8', 'Stationary', 'ci95_high'),
    }
    metrics = read_json(OUT / 'review_metrics.json')
    check('derived metric coverage', metrics.keys() == expected.keys())
    for name, value in expected.items():
        check('derived arithmetic ' + name, close(metrics[name], value))
    check('derived CSV and JSON agree', {r['metric']: float(r['value']) for r in rows(OUT / 'review_metrics.csv')} == metrics)
    plotted = rows(OUT / 'fig_S1_paired_objective_gaps_data.csv')
    membership = rows(BASE / 'case_membership.csv')
    expected_keys = {(int(panel), m['case_id'], baseline) for panel, axis in enumerate(('J', 'speed', 'probability'), 1) for m in membership if m['axis'] == axis for baseline in ('Stationary', 'Greedy')}
    check('38 plotted point coverage', len(plotted) == len(expected_keys) == 38 and {(int(r['panel']), r['case_id'], r['baseline']) for r in plotted} == expected_keys)
    meta = read_json(OUT / 'render_metadata.json')
    check('render input identity', meta['input_sha256'] == sha(BASE / 'existing_data/paired_improvements.csv') and meta['points'] == 38)
    for r in plotted:
        source = paired[r['case_id'], 1, r['baseline'], 'U']
        check('actual plotted value and paired CI ' + r['case_id'] + '/' + r['baseline'], all(float(r[dest]) == float(source[key]) for dest, key in (('y', 'mean'), ('ci95_low', 'ci95_low'), ('ci95_high', 'ci95_high'))))
        check('actual x and penalty ' + r['case_id'] + '/' + r['baseline'], int(r['lambda_index']) == 1 and any(m['case_id'] == r['case_id'] and m['axis'] == r['axis'] and float(m['value']) == float(r['x']) for m in membership))
        panel = meta['panels'][int(r['panel']) - 1]
        check('visible zero and whole CI ' + r['case_id'] + '/' + r['baseline'], panel['ylim'][0] <= min(0, float(r['ci95_low'])) and panel['ylim'][1] >= max(0, float(r['ci95_high'])) and panel['xlim'][0] <= float(r['x']) <= panel['xlim'][1])
    visual = read_json(OUT / 'visual_review.json')
    mapping = rows(OUT / 'figure_review.csv')
    check('six original figures and one supplement reviewed', visual['status'] == 'CURRENTLY_VERIFIED_PASS' and len(mapping) == len(visual['images_viewed']) == 7)
    check('same four main figures retained', [r['figure'] for r in mapping if r['role'] == 'Main'] == ['A1', 'A2', 'B', 'C'])
    for r in mapping:
        for suffix in ('pdf', 'png'):
            check('figure file hash ' + r['figure'] + '/' + suffix, sha(OUT / r[suffix]) == r[suffix + '_sha256'])
        check('visual review image identity ' + r['figure'], sha(OUT / r['png']) == visual['images_viewed'][r['figure']]['png_sha256'])
        check('vector PDF ' + r['figure'], b'/Subtype /Image' not in (OUT / r['pdf']).read_bytes())
        with Image.open(OUT / r['png']) as im:
            check('350 dpi PNG ' + r['figure'], im.size == (2520, 1137) and all(abs(dpi - 350) < .1 for dpi in im.info['dpi']))
    for name in ('report_review_vi.md', 'discussion_en.md'):
        text = (OUT / name).read_text(encoding='utf-8')
        check('security and lifecycle warnings ' + name, all(word in text for word in ('UNVALIDATED_SECURITY_MODEL', 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS')))
        check('report links ' + name, all((OUT / link).exists() or link == 'validation_report.md' for link in re.findall(r'\]\(([^)]+)\)', text)))
        for number in ('3.075', '4.418', '25.04', str(lower_k), str(len(positive_dp))):
            check('numerical narrative token ' + name + '/' + number, number in text)
    for path in sorted(OUT.iterdir()):
        if path.suffix in ('.py', '.json', '.md', '.csv') and path.name not in ('validation_receipt.json', 'validation_report.md'):
            check('artifact whitespace ' + path.name, all(line == line.rstrip() for line in path.read_text(encoding='utf-8-sig').splitlines()))
    report = f'''# Stage A figure/report continuation validation

CURRENTLY_VERIFIED_PASS: {len(CHECKS)} named checks.

- {len(startup['protected_files'])} startup files preserved except the five authorized ledgers; original Stage A receipt and all {len(receipt['artifact_sha256'])} bound artifacts, including all six PDF/PNG pairs, remain unchanged. Git branch and HEAD are unchanged.
- Original full Stage A verifier passed 7,445 checks immediately before this child directory was created. The original verifier expects exact recursive file coverage and predates this append-only extension. This verifier authenticates original receipt members and producer hashes directly; it does not replace or rewrite the original receipt.
- All 38 actual S1 artist points, original paired confidence bounds, parameter identities and visible axes verified. Six original figures retained, seven PNGs visually reviewed and hash-bound; PDFs are vector and PNGs are 350 dpi.
- Seventeen derived quantities independently reconstructed, default means checked against all 100 saved mission IDs per method/penalty, and 5,200 positive-penalty objective comparisons rechecked from saved records. K_DP<K_Greedy in {lower_k}/{len(positive_dp)} positive-penalty case-mission pairs at tolerance 1e-12; objective dominance is not an SKR dominance claim.
- No solver, physical/source evaluator, cloud generation, new bootstrap draw or Stage B execution. Report links, scope warnings, numerical tokens and whitespace checked.

UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Frozen hash discrepancy and Objective C USER_STOPPED remain. No scientific/security/frozen/cache/baseline/threshold/lifecycle changes, training/test/held-out access, external manuscript edits, commit or push.

Recheck with project Python: `python -X utf8 -B results/mobility_parameter_sensitivity_20261020/analysis/figure_report_review_20261020/verify_review.py`.
'''
    report_path = OUT / 'validation_report.md'
    if report_path.exists():
        check_same = report_path.read_text(encoding='utf-8') == report
        if not check_same:
            raise AssertionError('Completed validation report changed')
    else:
        report_path.write_text(report, encoding='utf-8', newline='\n')
    body = dict(status='CURRENTLY_VERIFIED_PASS', named_checks=len(CHECKS), checks=CHECKS, protected_files=len(startup['protected_files']),
                original_receipt_sha256=sha(BASE / 'validation/final_receipt.json'), original_receipt_members=len(receipt['artifact_sha256']),
                actual_S1_points=38, original_figures_changed=0, new_mobility_runs=0, new_clouds=0, new_physical_SKR=0, new_bootstrap_draws=0, stage_b_executed=False,
                artifact_sha256={p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'validation_receipt.json'})
    target = OUT / 'validation_receipt.json'
    if target.exists():
        if read_json(target) != body:
            raise AssertionError('Completed review receipt changed')
    else:
        target.write_text(json.dumps(body, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('CURRENTLY_VERIFIED_PASS', len(CHECKS), 'checks;', len(body['artifact_sha256']), 'review artifacts; original Stage A unchanged')


if __name__ == '__main__':
    verify()
