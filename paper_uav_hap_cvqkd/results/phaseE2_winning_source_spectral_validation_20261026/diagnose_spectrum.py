"""Read Phase E spectra; cheap matrix checks and analytic-bound feasibility only."""
import csv
import math
import time

import mpmath as mp
import numpy as np
import scipy.linalg as la
import checkpoint_wrapper as cw


def spectrum_summary(values, floor):
    retained = [x for x in values if x > floor]
    descending = sorted(retained, reverse=True)
    relative_gaps = [(descending[i] - descending[i + 1]) / descending[i]
                     for i in range(len(descending) - 1)]
    predictions = []
    if len(values) == 64 and len(descending) >= 12:
        for count in [6, 8, 10, 12]:
            indices = np.arange(len(descending) - count + 1, len(descending) + 1)
            logs = np.array([float(mp.log10(x)) for x in descending[-count:]])
            # This extrapolation is a planning estimate, not an eigenvalue bound.
            predictions.append(float(np.polyval(np.polyfit(indices, logs, 1), 64)))
    st = lambda x: mp.nstr(x, 35)
    return dict(minimum_raw_eigenvalue=st(min(values)), maximum_eigenvalue=st(max(values)),
                positive_count=sum(x > 0 for x in values), effective_rank=len(retained),
                unresolved_below_floor=len(values) - len(retained), floor=st(floor),
                minimum_retained_eigenvalue=st(min(retained)),
                retained_condition=st(max(retained) / min(retained)),
                minimum_retained_relative_gap=st(min(relative_gaps)) if relative_gaps else '',
                extrapolated_log10_lambda64_min=min(predictions) if predictions else '',
                extrapolated_log10_lambda64_max=max(predictions) if predictions else '')


def historical_spectra():
    rows, spectra = [], []
    for receipt in cw.read(cw.PRIOR / 'job_receipts.json'):
        if receipt['source'] != 'Winner_MB' or receipt['digits'] == 16:
            continue
        if receipt['status'] != 'COMPLETED':
            for sector in range(4):
                rows.append(dict(method='Gram', sector=sector, Fock_photon_sector=(-sector) % 4,
                    digits=receipt['digits'], NF='', matrix_dimension=64, effective_rank='',
                    status=receipt['status'] + '_NO_NUMERICAL_CHECKPOINT', job=receipt['job'],
                    source_ensemble_hash=SOURCE['ensemble_hash'],
                    provenance='Phase E log only: retained counts are not saved eigenpairs'))
            continue
        saved = cw.read(cw.PRIOR / receipt['output'])
        size = receipt['NF'] // 4 if receipt['method'] == 'A' else 64
        values = [mp.mpf(x) for x in saved['spectrum']]
        assert len(values) == 4 * size
        floor = mp.power(10, -receipt['digits'] + 20)
        for sector in range(4):
            block = values[sector * size:(sector + 1) * size]
            summary = spectrum_summary(block, floor)
            row = dict(method='Fock' if receipt['method'] == 'A' else 'Gram', sector=sector,
                       Fock_photon_sector=sector if receipt['method'] == 'A' else (-sector) % 4,
                       digits=receipt['digits'], NF=receipt['NF'] or '', matrix_dimension=size,
                       **summary, job=receipt['job'], status='HISTORICAL_PARTIAL_SUPPORT_DIAGNOSTIC',
                       source_ensemble_hash=SOURCE['ensemble_hash'],
                       eigensolver_relative_residual=saved['rows'][0]['eigensolver_relative_residual'],
                       eigenvector_reconstruction_error='',
                       eigenpair_residual_status='NOT_SAVED_PER_PAIR; historical maximum aggregate only',
                       C_contribution='', w_contribution='',
                       provenance=f"{receipt['output']} spectrum[{sector * size}:{(sector + 1) * size}]",
                       payload_sha256=cw.sha(cw.PRIOR / receipt['output']))
            rows.append(row)
            spectra.append(dict(**{k: row[k] for k in ['method', 'sector', 'digits', 'NF', 'job', 'provenance', 'payload_sha256']},
                                eigenvalues=[mp.nstr(x, 55) for x in block]))
    return rows, spectra


def float_C4(p, alpha, groups):
    H = np.sqrt(p[:, None] * p[None, :]) * np.exp(
        -(abs(alpha[:, None])**2 + abs(alpha[None, :])**2) / 2 + alpha[:, None].conj() * alpha[None, :])
    transforms = []
    for sector in range(4):
        F = np.zeros((256, 64), complex)
        for k, group in enumerate(groups):
            for rotation, index in enumerate(group):
                F[index, k] = (1j)**(sector * rotation) / 2
        transforms.append(F)
    Q = np.concatenate(transforms, axis=1)
    error = la.norm(Q.conj().T @ Q - np.eye(256))
    diagonal = np.zeros_like(H); rows = []; saved = []
    for sector, F in enumerate(transforms):
        B = F.conj().T @ H @ F
        fast = np.array([[np.sqrt(p[g[0]] * p[h[0]]) * sum(
            (1j)**(sector * r) * np.exp(-(abs(alpha[g[0]])**2 + abs(alpha[h[0]])**2) / 2 +
                                      alpha[g[0]].conjugate() * alpha[h[r]]) for r in range(4))
                         for h in groups] for g in groups])
        values, U = la.eigh(B)
        residual = la.norm(B @ U - U * values) / la.norm(B)
        reconstruction = la.norm(B - (U * values) @ U.conj().T) / la.norm(B)
        diagonal[sector * 64:(sector + 1) * 64, sector * 64:(sector + 1) * 64] = B
        summary = spectrum_summary([mp.mpf(float(x)) for x in values], mp.mpf('1e-16'))
        rows.append(dict(method='Gram_E2_float64', sector=sector, Fock_photon_sector=(-sector) % 4,
                         digits=16, NF='', matrix_dimension=64, **summary,
                         status='FLOAT64_DIAGNOSTIC_NOT_FULL_SUPPORT', job='E2_lightweight_matrix_check',
                         source_ensemble_hash=SOURCE['ensemble_hash'],
                         eigensolver_relative_residual=residual, eigenvector_reconstruction_error=reconstruction,
                         eigenpair_residual_status='MEASURED_FLOAT64; NOT_OUTWARD_ROUNDED',
                         C_contribution='', w_contribution='', provenance='float_sector_checks.json'))
        saved.append(dict(sector=sector, eigenvalues=values.tolist(),
                          eigenpair_residuals=la.norm(B @ U - U * values, axis=0).tolist(),
                          reconstruction_relative_error=reconstruction,
                          relative_residual=residual, fast_vs_explicit_DFT_error=float(la.norm(fast - B) / la.norm(B))))
    off_block = la.norm(Q.conj().T @ H @ Q - diagonal) / la.norm(H)
    full_difference = np.max(abs(np.sort(np.concatenate([x['eigenvalues'] for x in saved])) - la.eigvalsh(H)))
    assert error < 1e-13 and off_block < 1e-13 and full_difference < 1e-13
    assert max(x['fast_vs_explicit_DFT_error'] for x in saved) < 1e-13
    cw.atomic_json(cw.OUT / 'float_sector_checks.json', dict(
        unitary_error=float(error), off_block_relative_error=float(off_block),
        full_vs_sector_spectrum_absolute_error=float(full_difference), sectors=saved,
        new_target_Cw_computations=0, eigenvector_storage='Not required for this disposable float64 check'))
    return rows


def cross_method(spectra):
    fock = {x['sector']: x for x in spectra if x['method'] == 'Fock' and x['NF'] == 256}
    gram = {x['sector']: x for x in spectra if x['method'] == 'Gram' and x['digits'] == 180}
    comparisons = []
    for s, row in gram.items():
        a = [mp.mpf(x) for x in row['eigenvalues']]
        b = [mp.mpf(x) for x in fock[(-s) % 4]['eigenvalues']]
        matched = [(x, y) for x, y in zip(a, b) if x > mp.mpf('1e-160') and y > mp.mpf('1e-240')]
        comparisons.append(dict(Gram_sector=s, Fock_photon_sector=(-s) % 4,
                                matched_retained_modes=len(matched),
                                maximum_relative_difference=mp.nstr(max(abs(x-y)/abs(y) for x,y in matched), 40),
                                certification=False, limitation='Different Fock cutoff/precision; no saved historical eigenvectors'))
    cw.atomic_json(cw.OUT / 'cross_method_spectral_comparison.json', comparisons)
    return comparisons


def inverse_vandermonde_feasibility(p, alpha, groups):
    """Exact analytic inequality; its ordinary-mpf decimal evaluation is NOT an enclosure."""
    weights = [mp.mpf(float(p[g[0]])) for g in groups]
    z = [mp.mpc(float(alpha[g[0]].real), float(alpha[g[0]].imag)) for g in groups]
    nodes = [x**4 for x in z]; count = len(nodes)
    assert len(set(nodes)) == count and all(x != 0 for x in z)
    upper = [mp.mpf(0) for _ in range(4)]
    for k in range(count):
        majorant = [mp.mpf(1)]; denominator = mp.mpf(1)
        for j in range(count):
            if j == k:
                continue
            # Coefficients of product(x+|t_j|) bound absolute Lagrange numerator coefficients.
            new = [mp.mpf(0)] * (len(majorant) + 1)
            for degree, coefficient in enumerate(majorant):
                new[degree] += abs(nodes[j]) * coefficient
                new[degree + 1] += coefficient
            majorant = new
            denominator *= abs(nodes[k] - nodes[j])**2
        for r in range(4):
            upper[r] += mp.exp(abs(z[k])**2) / (4 * weights[k] * abs(z[k])**(2*r) * denominator) * \
                mp.fsum(majorant[n]**2 * mp.factorial(r + 4*n) for n in range(count))
    return [dict(Fock_photon_sector=r, Gram_sector=(-r) % 4,
                 log10_inverse_Frobenius_upper_expression=mp.nstr(mp.log10(upper[r]), 40),
                 log10_lambda_lower_expression_estimate=mp.nstr(-mp.log10(upper[r]), 40),
                 status='ANALYTIC_INEQUALITY; DECIMAL_VALUE_NOT_OUTWARD_ROUNDED',
                 full_support_Cw_certificate=False) for r in range(4)]


def tail_feasibility(p, alpha):
    rows = []
    for N in [24, 32, 48, 64, 96, 128, 256]:
        upper = []
        for value in alpha:
            z = mp.mpc(float(value.real), float(value.imag)); t = abs(z)**2
            assert t < N+1
            upper.append(mp.exp(-t)*t**N/mp.factorial(N)/(1-t/(N+1)))
        trace_upper = mp.fsum(mp.mpf(float(p[k]))*upper[k] for k in range(len(p)))
        rows.append(dict(Fock_cutoff=N, maximum_coherent_Poisson_tail_upper_expression=mp.nstr(max(upper),40),
                         weighted_Gram_tail_trace_upper_expression=mp.nstr(trace_upper,40),
                         enclosure_status='ANALYTIC_FORMULA; MPF_DECIMAL_EVALUATION_NOT_CERTIFIED'))
    return rows


def downstream():
    with (cw.PRIOR / 'Z_SKR_sensitivity.csv').open(encoding='utf-8', newline='') as stream:
        context = next(csv.DictReader(stream))
    eta, xi = mp.mpf(float(context['eta_f'])), mp.mpf(float(context['xi_f']))
    C, w = mp.mpf(float(SOURCE['C'])), mp.mpf(float(SOURCE['w']))
    coefficient_C = 2*mp.sqrt(eta)
    coefficient_w = -mp.sqrt(2*eta*xi)/(2*mp.sqrt(w))
    return dict(zenith_deg=context['zenith_deg'], eta_f=context['eta_f'], xi_f=context['xi_f'],
                dZ_dC=mp.nstr(coefficient_C,45), dZ_dw=mp.nstr(coefficient_w,45),
                interval_rule='[2sqrt(eta)*C_lo-sqrt(2eta*xi*w_hi), 2sqrt(eta)*C_hi-sqrt(2eta*xi*w_lo)]',
                interval_assumptions='eta,xi fixed >=0; 0<=w_lo<=w_hi; defensible joint C,w enclosure required',
                sensitivity_not_uncertainty=True, certified_C_interval=None, certified_w_interval=None,
                certified_Z_interval=None, certified_SKR_interval=None,
                new_channel_integrations=0, new_MI_Holevo_SKR_evaluations=0)


SOURCE = cw.read(cw.PRIOR / 'inputs/source_metadata.json')[0]


def main():
    wall, cpu = time.perf_counter(), time.process_time()
    p, alpha, groups = cw.input_source(cw.PRIOR / 'inputs/Winner_MB.npz')
    assert cw.sha(cw.ROOT / SOURCE['source_path']) == SOURCE['source_sha256']
    digests = __import__('json').loads(SOURCE['input_digests_json'])
    assert __import__('hashlib').sha256(p.tobytes()).hexdigest() == digests['pmf_sha256']
    assert __import__('hashlib').sha256(alpha.tobytes()).hexdigest() == digests['amplitude_sha256']
    with mp.workdps(90):
        summaries, spectra = historical_spectra()
        summaries += float_C4(p, alpha, groups)
        comparisons = cross_method(spectra)
        bounds = inverse_vandermonde_feasibility(p, alpha, groups)
        tails = tail_feasibility(p, alpha)
        sensitivity = downstream()
    cw.atomic_json(cw.OUT / 'historical_spectrum_slices.json', spectra)
    cw.atomic_json(cw.OUT / 'analytic_bound_feasibility.json', dict(sectors=bounds, Fock_tail=tails,
        rigorous_decimal_enclosure=False, error_bound_for_w=None,
        limitation='Finite analytic lambda lower bound is possible; inverse sensitivity makes mass-only w bounds insufficient'))
    cw.atomic_json(cw.OUT / 'downstream_error_requirements.json', sensitivity)
    keys = list(dict.fromkeys(k for row in summaries for k in row))
    with (cw.OUT / 'sector_spectrum_diagnostics.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=keys); writer.writeheader(); writer.writerows(summaries)
    receipts = [x for x in cw.read(cw.PRIOR / 'job_receipts.json') if x['source']=='Winner_MB']
    tests = cw.read(cw.OUT / 'checkpoint_test_results.json')
    result = dict(conclusion='INCONCLUSIVE', result_scope='DIAGNOSTIC_ONLY', PHASE_B_STRICT_READY=False,
        source_identity=SOURCE, mathematical_support_rank=256,
        mathematical_rank_reason='positive weights; distinct coherent amplitudes; nonsingular finite Vandermonde projection',
        largest_completed_Fock_effective_rank=231, largest_completed_Gram_effective_rank=186,
        unresolved_at_best_completed_Fock_floor=25,
        cross_method_compared_modes=sum(x['matched_retained_modes'] for x in comparisons),
        cross_method_maximum_relative_eigenvalue_difference=max(float(x['maximum_relative_difference']) for x in comparisons),
        full_support_certified=False, truncation_error_certified=False,
        evidence_class_original='INSUFFICIENT_EVIDENCE', evidence_class_current='INSUFFICIENT_EVIDENCE',
        rigorous_Cw_error_bound=None, checkpoints_operational=tests['status']=='CURRENTLY_VERIFIED_PASS',
        focused_tests=tests['tests_run'], new_target_source_Cw_computations=0,
        new_small_source_moment_checks=dict(checkpointed_Gram=4, original_Gram=4, original_Fock=2, maximum_M=16),
        target_AP_jobs_started=0, new_channel_MI_Holevo_SKR_evaluations=0,
        eigenvalue_summary_rows=len(summaries), old_receipts=receipts,
        limiting_factors=['spectral conditioning and precision floor',
                         'lost Gram260 numerical checkpoints after timeout',
                         'finite Fock subspace cannot certify full tiny-eigenvalue spectrum from tail mass alone',
                         'no outward-rounded source-functional error enclosure'],
        authorization_plan_status='PREPARED_NOT_EXECUTED',
        numerical_analysis_wall_seconds=time.perf_counter()-wall,
        numerical_analysis_CPU_seconds=time.process_time()-cpu,
        analysis_producer_sha256=cw.sha(__file__), checkpoint_producer_sha256=cw.sha(cw.__file__))
    cw.atomic_json(cw.OUT / 'source_convergence_status.json', result)
    print(__import__('json').dumps({k: result[k] for k in ['conclusion','cross_method_compared_modes',
        'cross_method_maximum_relative_eigenvalue_difference','eigenvalue_summary_rows','numerical_analysis_wall_seconds']}))


if __name__ == '__main__':
    main()
