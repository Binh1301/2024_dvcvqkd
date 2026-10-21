"""Read saved artifacts and build outputs only; no scientific imports or solvers."""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
FINAL = ROOT / 'results/mobility_parameter_sensitivity_final_20261020'
BASE = ROOT / 'results/manuscript_mobility_p1_p2_p3_20261019'
CHECKS = []


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, condition):
    CHECKS.append(dict(name=name, passed=bool(condition)))
    if not condition:
        raise AssertionError(name)


def close(name, value, expected, tol=1e-12):
    check(name, math.isclose(value, expected, abs_tol=tol, rel_tol=tol))


receipt_path = OUT / 'validation/final_receipt.json'
completed = receipt_path.is_file() and read_json(receipt_path).get('status') == 'CURRENTLY_VERIFIED_PASS'
if completed:
    for name, digest in read_json(receipt_path)['artifact_sha256'].items():
        assert sha(ROOT / name) == digest, 'Completed receipt member changed: ' + name

startup = read_json(OUT / 'startup_manifest.json')
manifest = read_json(OUT / 'input_manifest.json')
for name, digest in manifest['inputs_sha256'].items():
    check('declared input:' + name, sha(ROOT / name) == digest)
for name, digest in manifest['external_sha256'].items():
    check('external original:' + name, sha(Path(name)) == digest)
for name, record in manifest['primary_references'].items():
    check('primary reference:' + name, sha(OUT / 'references' / name) == record['sha256'])
allowed = {'.agent/SESSION_HANDOFF.md', 'docs/EVIDENCE.md', 'docs/DECISION_LOG.md',
           'docs/PROJECT_STATE.md', 'docs/NEXT_ACTIONS.md'}
for name, digest in startup['protected_sha256'].items():
    if name not in allowed:
        check('protected:' + name, (ROOT / name).is_file() and sha(ROOT / name) == digest)
for field, command in [('branch', ['git', 'branch', '--show-current']),
                       ('head', ['git', 'rev-parse', 'HEAD'])]:
    check('git:' + field, subprocess.check_output(command, cwd=ROOT, text=True).strip() == startup[field])
new_allowed = {'docs/security_model_consistency_audit.md', 'docs/manuscript_final_validation.md'}
for path in ROOT.rglob('*'):
    if not path.is_file() or any(x in path.parts for x in ('.venv', '.venv-binary-cloud', '__pycache__', '.git')):
        continue
    name = path.relative_to(ROOT).as_posix()
    check('new-file-scope:' + name, name in startup['protected_sha256'] or
          name in new_allowed or name.startswith('results/manuscript_ieee_revision_20261020/'))

# Directly authenticate historical members. Never execute historical verifiers.
receipts = [(BASE / 'validation/final_verification.json', 'artifacts_sha256'),
            (ROOT / 'results/mobility_parameter_sensitivity_20261020/validation/final_receipt.json', 'artifact_sha256'),
            (ROOT / 'results/mobility_parameter_sensitivity_stage_b_20261020/validation/final_receipt.json', 'artifact_sha256'),
            (FINAL / 'validation/final_receipt.json', 'artifact_sha256')]
receipt_manifest = {}
for path, key in receipts:
    payload = read_json(path)
    directory = path.parents[1]
    members = payload[key]
    for name, digest in members.items():
        check('receipt-member:' + directory.name + '/' + name,
              (directory / name).is_file() and sha(directory / name) == digest)
    receipt_manifest[path.relative_to(ROOT).as_posix()] = dict(sha256=sha(path), members=len(members))
check('final receipt anchor', sha(FINAL / 'validation/final_receipt.json') ==
      '893ad90809c64c8d2ed742c374bf02dda2169842b71b6cef499fa3bb00960a09')

roster = rows(BASE / 'source_roster.csv')
check('233 sources / 197 MB / 36 Uniform', Counter(r['family'] for r in roster) == {'MB': 197, 'Uniform': 36})
check('unique ensembles', len({r['ensemble_hash'] for r in roster}) == 233)
for row in roster:
    path = ROOT / row['source_path']
    check('source SHA:' + row['ensemble_hash'], sha(path) == row['source_sha256'])
    payload = read_json(path)
    for field in ('C', 'w', 'ensemble_hash'):
        check('payload ' + field + ':' + row['ensemble_hash'], str(payload[field]) == row[field])
    check('source VA/nu/support:' + row['ensemble_hash'],
          float.fromhex(payload['V_A_hex']) == float(row['VA']) and
          float.fromhex(payload['nu_mb_raw_hex']) == float(row['nu_raw']) and payload['support_size'] == 256)
    identity_fields = ('schema', 'ensemble_hash', 'nu_mb_raw_hex', 'nu_mb_repo_hex', 'V_A_hex',
                       'mb_convention', 'source_implementation', 'source_settings')
    identity = {k: payload[k] for k in identity_fields}
    check('payload identity:' + row['ensemble_hash'], hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest() == payload['cache_key'])
    for filename, digest in payload['source_implementation'].items():
        raw = (ROOT / filename).read_bytes()
        canonical = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        check('source producer:' + row['ensemble_hash'] + ':' + filename,
              digest in {hashlib.sha256(raw).hexdigest(), hashlib.sha256(canonical).hexdigest(),
                         hashlib.sha256(canonical.replace(b'\n', b'\r\n')).hexdigest()})
winners = rows(BASE / 'p1/winners.csv')
check('100 identical-source P1 winners', len(winners) == 100 and
      all(float(r['VA']) == 8 and float(r['nu_raw']) == .125 for r in winners) and
      len({r['ensemble_hash'] for r in winners}) == 1)
for i, r in enumerate(winners):
    close('saved P1 rate arithmetic:' + str(i), float(r['K_raw']), float(r['beta_I_AB']) - float(r['chi_BE']))
    close('saved P1 clipping:' + str(i), float(r['K_star']), max(0, float(r['K_raw'])))

missions = rows(FINAL / 'tables/selected_missions.csv')
stats = rows(FINAL / 'tables/statistical_comparison.csv')
grouped = defaultdict(list)
key_fields = ('figure', 'case_id', 'lambda_index', 'method')
for row in missions:
    grouped[tuple(row[k] for k in key_fields)].append(row)
    label = ':'.join(row[k] for k in (*key_fields, 'realization_id'))
    close('saved U:' + label, float(row['U']),
          float(row['K']) - float(row['lambda_bits_per_use']) * float(row['D']) / 1000)
    close('saved unavailability:' + label, float(row['unavailability_percent']),
          100 * (1 - float(row['availability'])))
    if row['method'] == 'Stationary':
        close('stationary D:' + label, float(row['D']), 0)
for key, values in grouped.items():
    check('100 paired IDs:' + str(key), sorted(int(r['realization_id']) for r in values) == list(range(100)))
for row in stats:
    key = tuple(row[k] for k in key_fields)
    vals = [float(r[row['metric']]) for r in grouped[key]]
    for metric, actual in [('mean', statistics.mean(vals)), ('sd', statistics.stdev(vals)), ('median', statistics.median(vals))]:
        close('summary ' + metric + ':' + str(key) + ':' + row['metric'], float(row[metric]), actual)
    check('saved CI finite:' + str(key) + ':' + row['metric'],
          math.isfinite(float(row['ci95_low'])) and float(row['ci95_low']) <= float(row['ci95_high']))
stat_index = {tuple(r[k] for k in key_fields) + (r['metric'],): r for r in stats}
figures = ['fig1_candidate_positions', 'fig2_cloud_blockage', 'fig3_temporal_correlation', 'fig4_skr_mobility_tradeoff']
for name in figures:
    check('unchanged figure:' + name, sha(OUT / 'figures' / (name + '.pdf')) == sha(FINAL / 'figures' / (name + '.pdf')))
    for r in rows(FINAL / 'figures' / (name + '_data.csv')):
        k = tuple(r[f] for f in key_fields)
        ref = stat_index[k + (r['metric'],)]
        close('plot y:' + str(k) + ':' + r['metric'], float(r['y']), float(ref['mean']))

def value(figure, parameter, method, metric, penalty=None):
    found = [r for r in stats if r['figure'] == str(figure) and
             float(r['parameter_value']) == parameter and r['method'] == method and r['metric'] == metric
             and (penalty is None or float(r['lambda_bits_per_use']) == penalty)]
    check('unique finding:' + str((figure, parameter, method, metric, penalty)), len(found) == 1)
    return float(found[0]['mean'])

j_gain = 100 * (value(1, 100, 'DP', 'U') / value(1, 10, 'DP', 'U') - 1)
unavailability = {m: value(2, .8, m, 'unavailability_percent') for m in ('Stationary', 'Greedy', 'DP')}
rho_distance = [value(3, rho, 'DP', 'D') for rho in (0, .98)]
ref_penalty = 9.468026677248516e-6
trade = [r for r in stats if r['figure'] == '4' and r['method'] == 'DP']
def trade_value(penalty, metric):
    return float(next(r['mean'] for r in trade if float(r['lambda_bits_per_use']) == penalty and r['metric'] == metric))
distance_reduction = 100 * (1 - trade_value(ref_penalty, 'D') / trade_value(0, 'D'))
skr_reduction = 100 * (1 - trade_value(ref_penalty, 'K') / trade_value(0, 'K'))
for name, actual, expected in [('J gain', j_gain, 11.41), ('distance reduction', distance_reduction, 88.37),
                                ('SKR reduction', skr_reduction, .515)]:
    check('manuscript rounded number:' + name, abs(actual - expected) < .0051)
close('p .8 Stationary unavailable', unavailability['Stationary'], 24.6)
check('p .8 Greedy unavailable rounding', round(unavailability['Greedy'], 2) == 16.53)
check('p .8 DP unavailable rounding', round(unavailability['DP'], 2) == 4.07)
check('rho endpoint rounding', [round(x, 2) for x in rho_distance] == [1038.25, 31.84])
matched = defaultdict(dict)
for r in missions:
    matched[(r['figure'], r['case_id'], r['lambda_index'], r['realization_id'])][r['method']] = r
for key, records in matched.items():
    for method in ('Stationary', 'Greedy'):
        check('saved DP objective dominance:' + str(key) + ':' + method,
              float(records['DP']['U']) + 1e-12 >= float(records[method]['U']))

main = (OUT / 'main.tex').read_text(encoding='utf-8')
original = (OUT / 'original/HAP_UAV_Availability_Mobility_Overleaf.tex').read_text(encoding='utf-8')
encoding_fix = '% Load before IEEEtran to avoid XeTeX TU/Times font substitutions.\n' + r'\RequirePackage[T1]{fontenc}' + '\n'
check('original package preamble plus documented T1 fix', main.replace(encoding_fix, '').startswith(original.split(r'\title{TBD}')[0]))
check('original author block', original[original.index(r'\author{'):original.index(r'\begin{document}')] in main)
all_tex = '\n'.join((OUT / name).read_text(encoding='utf-8') for name in ('main.tex', 'system_and_method.tex', 'numerical_results.tex'))
labels = re.findall(r'\\label\{([^}]+)\}', all_tex)
refs = re.findall(r'\\(?:ref|eqref)\{([^}]+)\}', all_tex)
check('unique labels', len(labels) == len(set(labels)))
check('all label references resolve', set(refs) <= set(labels))
aux = (OUT / 'main.aux').read_text(encoding='utf-8')
numbered = ['raw', 'p1', 'p2', 'p3', 'source_choice', 'greedy_init', 'greedy',
            'neighbors', 'dp_init', 'dp', 'backpointer', 'terminal', 'mean_skr', 'distance', 'utility']
for number, label in enumerate(numbered, 1):
    check('equation number:' + label, r'\newlabel{eq:' + label + '}{{' + str(number) + '}' in aux)
bib = (OUT / 'manuscript_refs.bib').read_text(encoding='utf-8')
cites = {key.strip() for group in re.findall(r'\\cite(?:\[[^]]*\])?\{([^}]+)\}', all_tex) for key in group.split(',')}
check('all bibliography keys resolve', cites == set(re.findall(r'@article\{([^,]+),', bib)))
check('4 integrated PDF figures', re.findall(r'\\includegraphics\[[^]]*\]\{([^}]+)\}', all_tex) == ['figures/' + x + '.pdf' for x in figures])
check('six numerical subsections', re.findall(r'\\subsection\{([^}]+)\}', (OUT / 'numerical_results.tex').read_text()) == [
    'Simulation Setup', 'Impact of Candidate UAV Positions', 'Impact of Cloud Blockage Probability',
    'Impact of Temporal Cloud Correlation', 'SKR--Mobility Tradeoff', 'Discussion and Limitations'])
log = (OUT / 'main.log').read_text(encoding='utf-8', errors='replace')
for name, pattern in [('undefined reference', r'(?:Reference|Citation) .+ undefined'),
                       ('undefined labels', r'There were undefined'), ('latex errors', r'^!'),
                       ('overfull boxes', r'Overfull \\[hv]box')]:
    check('build has no ' + name, not re.search(pattern, log, re.M))
check('compiled PDF exists', (OUT / 'main.pdf').is_file())
inspection = read_json(OUT / 'validation/pdf_inspection.json')
check('rendered current PDF', inspection['pdf_sha256'] == sha(OUT / 'main.pdf'))
check('A4 PDF pages', len(inspection['pages']) == 6 and all(
    abs(p['width_pt'] - 595.28) < .02 and abs(p['height_pt'] - 841.89) < .02 for p in inspection['pages']))
for p in inspection['pages']:
    check('rendered page:' + str(p['page']), sha(OUT / 'validation' / p['png']) == p['sha256'])
visual = read_json(OUT / 'validation/visual_review.json')
check('visual review current PDF', visual['pdf_sha256'] == sha(OUT / 'main.pdf') and
      visual['reviewed_pages'] == [dict(page=p['page'], png=p['png'], sha256=p['sha256'],
                                      status='VISUALLY_REVIEWED') for p in inspection['pages']])
check('frozen spec discrepancy preserved', sha(ROOT / 'docs/FINAL_MODEL_SPEC.md') ==
      'df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15')
check('git diff --check', subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True).returncode == 0)

findings = dict(J_objective_gain_percent=j_gain, p08_unavailability_percent=unavailability,
                rho0_to_098_DP_distance_m=rho_distance, DP_distance_reduction_percent=distance_reduction,
                DP_SKR_reduction_percent=skr_reduction)
result = dict(status='CURRENTLY_VERIFIED_PASS', named_checks=len(CHECKS),
              protected_files=len(startup['protected_sha256']), historical_receipts=receipt_manifest,
              saved_mission_records=len(missions), statistical_rows=len(stats),
              optimizer_calls=0, quantum_evaluator_calls=0, cloud_generator_calls=0, new_RNG_draws=0,
              security_verdict='INCONSISTENT_MEASUREMENT_PAIRING', security_status='UNVALIDATED_SECURITY_MODEL',
              lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS', findings=findings)
for filename, payload in [('numerical_crosschecks.json', findings), ('checks.json', CHECKS), ('verification.json', result)]:
    path = OUT / 'validation' / filename
    if completed:
        assert read_json(path) == payload, 'Completed verification changed: ' + filename
    else:
        path.write_text(json.dumps(payload, indent=2) + '\n')
print(json.dumps(result, indent=2))
