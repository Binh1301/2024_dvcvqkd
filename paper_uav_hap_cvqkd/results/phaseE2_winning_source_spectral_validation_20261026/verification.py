"""Read-only E2 saved-evidence check; never evaluates source moments or SKR."""
import csv
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

import mpmath as mp
import numpy as np
import checkpoint_wrapper as cw


def verify():
    startup = cw.read(cw.OUT / 'startup_manifest.json')
    for name, value in startup['protected'].items():
        assert cw.sha(cw.ROOT.parent / name) == value, name
    assert len(startup['protected']) == 10166
    assert cw.sha(cw.ROOT / 'docs/FINAL_MODEL_SPEC.md') == startup['frozen_actual_sha256']
    source = cw.read(cw.OUT / 'input_provenance.json')['source']
    payload = cw.read(cw.ROOT / source['source_path'])
    assert cw.sha(cw.ROOT / source['source_path']) == source['source_sha256']
    for key, expected in [('ensemble_hash', source['ensemble_hash']), ('V_A_hex', source['VA_hex']),
                          ('nu_mb_raw_hex', source['nu_raw_hex']), ('nu_mb_repo_hex', source['nu_repo_hex'])]:
        assert payload[key] == expected, key
    assert float(payload['C']).hex() == source['C_hex']
    assert float(payload['w']).hex() == source['w_hex']
    p, alpha, groups = cw.input_source(cw.PRIOR / 'inputs/Winner_MB.npz')
    original_digests = json.loads(source['input_digests_json'])
    assert hashlib.sha256(p.tobytes()).hexdigest() == original_digests['pmf_sha256']
    assert hashlib.sha256(alpha.tobytes()).hexdigest() == original_digests['amplitude_sha256']
    assert len(p) == len(alpha) == 256 and len(groups) == 64
    assert len(set(alpha)) == 256 and all(p > 0)
    assert sum(map(Fraction.from_float, map(float, p))) < 2
    assert abs(2 * p @ abs(alpha)**2 - float(source['VA'])) < 1e-12
    canonical = cw.identity(cw.PRIOR / 'inputs/Winner_MB.npz', 400, 0)
    assert canonical['canonical_ensemble_hash'] == source['ensemble_hash']

    tests = cw.read(cw.OUT / 'checkpoint_test_results.json')
    assert tests['status'] == 'CURRENTLY_VERIFIED_PASS' and tests['tests_run'] == 14
    assert tests['wrapper_sha256'] == cw.sha(cw.__file__)
    assert tests['producer_sha256'] == cw.sha(cw.OUT / 'test_checkpoint.py')
    first = cw.read(cw.OUT / 'development_evidence/round1_checkpoint_test_results.json')
    assert first['wrapper_sha256'] == cw.sha(cw.OUT / 'development_evidence/round1_checkpoint_wrapper.py')
    assert first['tests_run'] == 14 and first['status'] == 'CURRENTLY_VERIFIED_PASS'
    # Only the four valid scientific round2 sector sets are revalidated.
    small_directory = cw.OUT / 'stub_checkpoints/round2/test_small_scientific_equivalence'
    for name in ['Uniform_4', 'MB_16']:
        for digits in [50, 70]:
            directory = small_directory / f'{name}_{digits}'
            input_path = cw.PRIOR / 'inputs' / (name + '.npz')
            for s in range(4):
                cw.load_checkpoint(directory / f'sector_{s}.json', cw.identity(input_path, digits, s))
            moments = cw.read(directory / 'moments.json')
            assert moments['effective_rank'] == len(cw.input_source(input_path)[0])
            assert moments['result_sha256'] == cw.digest({k:v for k,v in moments.items() if k!='result_sha256'})

    with (cw.OUT / 'sector_spectrum_diagnostics.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 32
    fock = [x for x in rows if x['method']=='Fock' and x['NF']=='256']
    gram = [x for x in rows if x['method']=='Gram' and x['digits']=='180']
    assert sum(int(x['effective_rank']) for x in fock) == 231
    assert sum(int(x['effective_rank']) for x in gram) == 186
    assert len([x for x in rows if 'NO_NUMERICAL_CHECKPOINT' in x['status']]) == 4
    for spectrum in cw.read(cw.OUT / 'historical_spectrum_slices.json'):
        name, interval = spectrum['provenance'].split(' spectrum[')
        begin, end = map(int, interval[:-1].split(':'))
        assert cw.sha(cw.PRIOR / name) == spectrum['payload_sha256']
        original = cw.read(cw.PRIOR / name)['spectrum'][begin:end]
        with mp.workdps(90):
            assert all(mp.mpf(x)==mp.mpf(y) for x,y in zip(original,spectrum['eigenvalues']))
    paired = cw.read(cw.OUT / 'cross_method_spectral_comparison.json')
    assert sum(x['matched_retained_modes'] for x in paired) == 186
    assert all(x['Fock_photon_sector'] == (-x['Gram_sector']) % 4 for x in paired)
    assert max(float(x['maximum_relative_difference']) for x in paired) < 3e-27

    spec = importlib.util.spec_from_file_location('floor_certificate', cw.OUT / 'certify_spectral_floor.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    certificate = cw.read(cw.OUT / 'spectral_lower_bound_certificate.json')
    assert certificate['producer_sha256'] == cw.sha(cw.OUT / 'certify_spectral_floor.py')
    assert certificate['sectors'] == module.lower_bound(p, alpha, groups)
    assert certificate['certified_Fock_Gram_tail'] == module.fock_tail_upper(p, alpha, groups)
    assert [x['certified_lambda_min_lower_bound'] for x in certificate['sectors']] == \
        ['1e-302','1e-305','1e-308','1e-312']
    assert not certificate['full_support_Cw_certified']
    assert certificate['new_eigendecompositions'] == certificate['new_Cw_computations'] == 0

    status = cw.read(cw.OUT / 'source_convergence_status.json')
    assert status['analysis_producer_sha256'] == cw.sha(cw.OUT / 'diagnose_spectrum.py')
    assert status['checkpoint_producer_sha256'] == cw.sha(cw.__file__)
    assert status['conclusion'] == 'INCONCLUSIVE' and status['result_scope'] == 'DIAGNOSTIC_ONLY'
    assert not status['PHASE_B_STRICT_READY'] and not status['full_support_certified']
    assert not status['truncation_error_certified'] and not status['controlled_run_executed']
    assert status['rigorous_Cw_error_bound'] is None and status['certified_Cw_uncertainty'] is None
    assert status['evidence_class_current'] == status['evidence_class_original'] == 'INSUFFICIENT_EVIDENCE'
    assert status['new_target_source_Cw_computations'] == status['target_AP_jobs_started'] == 0
    assert status['new_small_source_moment_checks_total']['total'] == 20
    assert status['spectral_certificate_sha256'] == cw.sha(cw.OUT / 'spectral_lower_bound_certificate.json')
    plan = cw.read(cw.OUT / 'controlled_run_plan.json')
    assert cw.sha(cw.OUT / 'controlled_run_plan.json') == status['controlled_run_plan_sha256']
    assert plan['producer_sha256'] == cw.sha(cw.__file__) and plan['precision_levels'] == [400,500]
    assert plan['status'] == 'PREPARED_NOT_AUTHORIZED'
    assert plan['maximum_total_wall_seconds'] == 3600 and plan['maximum_worker_working_set_MiB'] == 1024
    assert not (cw.ROOT / plan['future_result_namespace']).exists()
    assert not (cw.ROOT / plan['authorization_receipt_planned_path']).exists()
    downstream = cw.read(cw.OUT / 'downstream_error_requirements.json')
    assert all(downstream[x] is None for x in ['certified_C_interval','certified_w_interval',
                                              'certified_Z_interval','certified_SKR_interval'])
    assert downstream['new_MI_Holevo_SKR_evaluations'] == downstream['new_channel_integrations'] == 0
    required = ['full_support_spectral_audit.md','sector_spectrum_diagnostics.csv','checkpoint_wrapper.py',
                'checkpoint_stub_tests.md','precision_feasibility.md','unresolved_spectrum_error_analysis.md',
                'source_convergence_status.json','controlled_run_authorization_plan.md','validation_report_vi.md',
                'artifact_integrity_report.md']
    assert all((cw.OUT / name).is_file() for name in required)
    manifest = cw.read(cw.OUT / 'artifact_manifest.json')
    for name, value in manifest['artifacts'].items():
        assert cw.sha(cw.OUT / name) == value, name
    return dict(verification_status='CURRENTLY_VERIFIED_PASS', scientific_conclusion='INCONCLUSIVE',
        protected_historical_files=len(startup['protected']), latest_unique_focused_tests=14,
        mathematical_positive_modes=256, Fock_retained_modes=231, unresolved_Fock_modes=25,
        Gram_retained_modes=186, cross_method_compared_modes=186,
        spectral_positivity_lower_bound='1e-312', full_support_Cw_certified=False,
        source_evidence='INSUFFICIENT_EVIDENCE', new_target_Cw_computations=0,
        small_source_test_moment_calls_across_two_batches=20, new_target_AP_jobs=0,
        new_channel_MI_Holevo_SKR_sweeps=0, PHASE_B_STRICT_READY=False,
        controlled_run='PREPARED_NOT_AUTHORIZED_NOT_RUN', sealed_artifacts=len(manifest['artifacts']))


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2, ensure_ascii=False))
